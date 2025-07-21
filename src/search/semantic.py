"""
Módulo principal de búsqueda semántica para Biblioperson
Integra embeddings, FAISS y base de datos
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path

# Imports locales
from src.embeddings.client import get_embedding_client, EmbeddingClient
from src.search.faiss_index import FAISSIndex, MultiDocumentIndex, SearchResult
from src.database.persistence import get_db_manager, DatabaseManager
from src.pipeline.chunking import DocumentChunker

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """
    Motor de búsqueda semántica completo
    """
    
    def __init__(self,
                 embedding_backend: str = "local",
                 embedding_model: Optional[str] = None,
                 index_dir: str = "indexes",
                 db_path: str = "data/biblioperson.db",
                 use_multi_index: bool = False,
                 enable_reranking: bool = False):
        """
        Inicializa el motor de búsqueda
        
        Args:
            embedding_backend: Backend para embeddings ('local', 'openai', 'hybrid')
            embedding_model: Modelo específico de embeddings
            index_dir: Directorio para índices FAISS
            db_path: Ruta a la base de datos
            use_multi_index: Usar índices separados por documento
            enable_reranking: Habilitar re-ranking de resultados
        """
        # Configurar cliente de embeddings
        embedding_kwargs = {}
        if embedding_model:
            embedding_kwargs['model_name'] = embedding_model
        
        self.embedding_client = get_embedding_client(embedding_backend, **embedding_kwargs)
        self.embedding_dim = self.embedding_client.embedding_dimensions
        
        # Configurar índice FAISS
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        if use_multi_index:
            self.index = MultiDocumentIndex(self.embedding_dim, str(self.index_dir))
        else:
            self.index = self._load_or_create_index()
        
        # Base de datos
        self.db = get_db_manager(db_path)
        
        # Chunker para procesar nuevos documentos
        self.chunker = DocumentChunker()
        
        # Re-ranking
        self.enable_reranking = enable_reranking
        if enable_reranking:
            self._init_reranker()
        
        logger.info(f"Motor de búsqueda inicializado: {embedding_backend}, dim={self.embedding_dim}")
    
    def _load_or_create_index(self) -> FAISSIndex:
        """Carga o crea el índice FAISS principal"""
        index_path = self.index_dir / "main.index"
        meta_path = self.index_dir / "main.meta"
        
        index = FAISSIndex(
            dimension=self.embedding_dim,
            index_type="IVF" if self.embedding_dim > 512 else "Flat",
            use_gpu=True
        )
        
        if index_path.exists() and meta_path.exists():
            try:
                index.load(str(index_path), str(meta_path))
                logger.info("Índice FAISS cargado desde disco")
            except Exception as e:
                logger.warning(f"Error cargando índice: {e}. Creando nuevo índice.")
        
        return index
    
    def _init_reranker(self):
        """Inicializa el modelo de re-ranking"""
        try:
            # Intentar usar FlashRank (rápido y ligero)
            from flashrank import Ranker, RerankRequest
            self.reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")
            self.rerank_type = "flashrank"
            logger.info("Re-ranker FlashRank inicializado")
        except ImportError:
            try:
                # Fallback a sentence-transformers CrossEncoder
                from sentence_transformers import CrossEncoder
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                self.rerank_type = "cross-encoder"
                logger.info("Re-ranker CrossEncoder inicializado")
            except ImportError:
                logger.warning("No hay modelos de re-ranking disponibles")
                self.enable_reranking = False
    
    def index_document(self,
                      document_id: int,
                      document_text: str,
                      profile: Optional[str] = None) -> int:
        """
        Indexa un documento completo
        
        Args:
            document_id: ID del documento en la BD
            document_text: Texto completo del documento (Markdown)
            profile: Perfil de chunking a usar
            
        Returns:
            Número de chunks indexados
        """
        logger.info(f"Indexando documento {document_id}")
        
        # Detectar perfil si no se especifica
        if profile is None:
            profile = self.chunker.detect_content_type(document_text)
        
        # Crear chunks
        chunks = self.chunker.chunk_text(document_text, profile)
        logger.info(f"Documento dividido en {len(chunks)} chunks con perfil '{profile}'")
        
        # Preparar datos para indexación
        chunk_texts = []
        chunk_ids = []
        chunk_metadata = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"doc_{document_id}_chunk_{i}"
            
            # Metadata del chunk
            metadata = {
                'document_id': document_id,
                'chunk_index': i,
                'text': chunk.page_content,
                'chunk_profile': profile,
                **chunk.metadata
            }
            
            chunk_texts.append(chunk.page_content)
            chunk_ids.append(chunk_id)
            chunk_metadata.append(metadata)
        
        # Generar embeddings en lotes
        logger.info("Generando embeddings...")
        embeddings = self.embedding_client.embed_batch(chunk_texts, batch_size=32)
        embeddings_array = np.array(embeddings)
        
        # Agregar al índice FAISS
        if isinstance(self.index, MultiDocumentIndex):
            self.index.add_document(document_id, embeddings_array, chunk_ids, chunk_metadata)
        else:
            self.index.add_embeddings(embeddings_array, chunk_ids, chunk_metadata)
        
        # Guardar en base de datos
        chunks_data = []
        for i, (chunk_id, text, embedding) in enumerate(zip(chunk_ids, chunk_texts, embeddings)):
            chunks_data.append({
                'chunk_id': chunk_id,
                'text': text,
                'embedding': embedding,
                'embedding_model': self.embedding_client.model_name,
                'embedding_dimensions': len(embedding),
                'profile': profile,
                'metadata': chunk_metadata[i]
            })
        
        self.db.save_semantic_chunks(document_id, chunks_data)
        
        # Guardar índice actualizado
        self._save_index()
        
        logger.info(f"Documento {document_id} indexado con {len(chunks)} chunks")
        return len(chunks)
    
    def search(self,
              query: str,
              k: int = 20,
              document_ids: Optional[List[int]] = None,
              rerank: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda semántica
        
        Args:
            query: Texto de búsqueda
            k: Número de resultados
            document_ids: Filtrar por documentos específicos
            rerank: Forzar re-ranking (None usa configuración por defecto)
            
        Returns:
            Lista de resultados con información completa
        """
        start_time = time.time()
        
        # Generar embedding de la query
        logger.debug(f"Generando embedding para query: '{query[:50]}...'")
        query_embedding = self.embedding_client.embed_text(query)
        embedding_time = (time.time() - start_time) * 1000
        
        # Buscar en índice FAISS
        search_start = time.time()
        
        if isinstance(self.index, MultiDocumentIndex):
            faiss_results = self.index.search_all(query_embedding, k=k*2, document_ids=document_ids)
        else:
            # Crear filtro si hay documentos específicos
            filter_fn = None
            if document_ids:
                filter_fn = lambda meta: meta.get('document_id') in document_ids
            
            faiss_results = self.index.search(query_embedding, k=k*2, filter_fn=filter_fn)
        
        search_time = (time.time() - search_start) * 1000
        logger.debug(f"Búsqueda FAISS: {len(faiss_results)} resultados en {search_time:.2f}ms")
        
        # Re-ranking si está habilitado
        if (rerank if rerank is not None else self.enable_reranking) and faiss_results:
            rerank_start = time.time()
            faiss_results = self._rerank_results(query, faiss_results, k)
            rerank_time = (time.time() - rerank_start) * 1000
        else:
            rerank_time = 0
        
        # Enriquecer resultados con información de la BD
        results = []
        for result in faiss_results[:k]:
            # Obtener información del documento
            doc_info = self.db.get_document_info(result.document_id) if hasattr(result, 'document_id') else {}
            
            enriched_result = {
                'chunk_id': result.chunk_id,
                'document_id': result.document_id,
                'document_title': doc_info.get('title', 'Sin título'),
                'document_author': doc_info.get('author', 'Desconocido'),
                'text': result.text,
                'similarity': result.score,
                'chunk_index': result.chunk_index,
                'metadata': result.metadata,
                'timing': {
                    'embedding_ms': embedding_time,
                    'search_ms': search_time,
                    'rerank_ms': rerank_time
                }
            }
            
            results.append(enriched_result)
        
        # Registrar búsqueda para analytics
        total_time = (time.time() - start_time) * 1000
        self.db.log_search(
            query_text=query,
            query_embedding=query_embedding,
            results=[r['chunk_id'] for r in results],
            search_duration_ms=int(total_time),
            rerank_duration_ms=int(rerank_time) if rerank_time > 0 else None
        )
        
        logger.info(f"Búsqueda completada: {len(results)} resultados en {total_time:.2f}ms")
        return results
    
    def _rerank_results(self, 
                       query: str, 
                       results: List[SearchResult],
                       k: int) -> List[SearchResult]:
        """
        Re-rankea resultados usando un modelo de cross-encoding
        """
        if not self.enable_reranking or not results:
            return results
        
        logger.debug(f"Re-rankeando {len(results)} resultados")
        
        if self.rerank_type == "flashrank":
            # FlashRank
            passages = [{"text": r.text, "meta": {"result": r}} for r in results]
            rerank_request = {"query": query, "passages": passages}
            
            reranked = self.reranker.rerank(rerank_request)
            
            # Extraer resultados re-rankeados
            reranked_results = []
            for item in reranked[:k]:
                original_result = item["meta"]["result"]
                # Actualizar score con el score de re-ranking
                original_result.score = item["score"]
                reranked_results.append(original_result)
            
            return reranked_results
        
        elif self.rerank_type == "cross-encoder":
            # Sentence Transformers CrossEncoder
            pairs = [[query, r.text] for r in results]
            scores = self.reranker.predict(pairs)
            
            # Combinar con resultados originales
            for result, rerank_score in zip(results, scores):
                # Combinar scores (promedio ponderado)
                result.score = 0.7 * result.score + 0.3 * rerank_score
            
            # Re-ordenar por nuevo score
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results[:k]
        
        return results
    
    def get_similar_chunks(self,
                          chunk_id: str,
                          k: int = 10) -> List[Dict[str, Any]]:
        """
        Encuentra chunks similares a uno dado
        
        Args:
            chunk_id: ID del chunk de referencia
            k: Número de resultados similares
            
        Returns:
            Lista de chunks similares
        """
        # Obtener embedding del chunk
        if isinstance(self.index, FAISSIndex):
            if chunk_id not in self.index.id_to_index:
                raise ValueError(f"Chunk {chunk_id} no encontrado en el índice")
            
            idx = self.index.id_to_index[chunk_id]
            chunk_embedding = self.index.index.reconstruct(idx)
        else:
            # Para MultiDocumentIndex, buscar en todos los documentos
            # Esto es menos eficiente, considerar mejoras
            raise NotImplementedError("get_similar_chunks no implementado para MultiDocumentIndex")
        
        # Buscar similares
        results = self.index.search(chunk_embedding, k=k+1)
        
        # Filtrar el chunk original
        results = [r for r in results if r.chunk_id != chunk_id][:k]
        
        # Enriquecer y devolver
        return [
            {
                'chunk_id': r.chunk_id,
                'document_id': r.document_id,
                'text': r.text,
                'similarity': r.score,
                'metadata': r.metadata
            }
            for r in results
        ]
    
    def update_embeddings(self, force: bool = False):
        """
        Actualiza embeddings para chunks sin procesar o con modelo antiguo
        
        Args:
            force: Regenerar todos los embeddings
        """
        logger.info("Actualizando embeddings...")
        
        # Obtener chunks a procesar
        if force:
            chunks = self.db.get_all_chunks()
        else:
            chunks = self.db.get_chunks_without_embeddings(limit=1000)
        
        if not chunks:
            logger.info("No hay chunks para procesar")
            return
        
        logger.info(f"Procesando {len(chunks)} chunks")
        
        # Procesar en lotes
        batch_size = 32
        updated_count = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Extraer textos
            texts = [c['text_content'] for c in batch]
            
            # Generar embeddings
            embeddings = self.embedding_client.embed_batch(texts, batch_size)
            
            # Preparar actualizaciones
            updates = []
            for chunk, embedding in zip(batch, embeddings):
                updates.append((
                    chunk['id'],
                    embedding,
                    self.embedding_client.model_name
                ))
            
            # Actualizar en BD
            self.db.update_chunk_embeddings(updates)
            updated_count += len(updates)
            
            if updated_count % 100 == 0:
                logger.info(f"Actualizados {updated_count} embeddings...")
        
        logger.info(f"Actualización completada: {updated_count} embeddings")
        
        # Reconstruir índice FAISS
        self._rebuild_index_from_db()
    
    def _rebuild_index_from_db(self):
        """Reconstruye el índice FAISS desde la base de datos"""
        logger.info("Reconstruyendo índice FAISS desde BD...")
        
        # Obtener todos los chunks con embeddings
        chunks = self.db.get_chunks_with_embeddings()
        
        if not chunks:
            logger.warning("No hay chunks con embeddings en la BD")
            return
        
        # Preparar datos
        embeddings = []
        chunk_ids = []
        metadata = []
        
        for chunk in chunks:
            if chunk['embedding']:
                # Deserializar embedding
                emb = np.frombuffer(chunk['embedding'], dtype=np.float32)
                embeddings.append(emb)
                chunk_ids.append(chunk['chunk_id'])
                
                meta = {
                    'document_id': chunk['document_id'],
                    'chunk_index': chunk['chunk_index'],
                    'text': chunk['text_content'],
                    'chunk_profile': chunk.get('chunk_profile', 'default')
                }
                metadata.append(meta)
        
        # Crear nuevo índice
        embeddings_array = np.array(embeddings)
        
        if isinstance(self.index, FAISSIndex):
            # Recrear índice
            self.index = FAISSIndex(
                dimension=self.embedding_dim,
                index_type="IVF" if len(embeddings) > 10000 else "Flat"
            )
            self.index.add_embeddings(embeddings_array, chunk_ids, metadata)
        
        # Guardar
        self._save_index()
        
        logger.info(f"Índice reconstruido con {len(embeddings)} vectores")
    
    def _save_index(self):
        """Guarda el índice FAISS a disco"""
        if isinstance(self.index, FAISSIndex):
            index_path = self.index_dir / "main.index"
            meta_path = self.index_dir / "main.meta"
            self.index.save(str(index_path), str(meta_path))
    
    def optimize_index(self):
        """Optimiza el índice para búsquedas más rápidas"""
        if isinstance(self.index, FAISSIndex):
            self.index.optimize()
            self._save_index()
            logger.info("Índice optimizado")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del motor de búsqueda"""
        stats = {
            'embedding_model': self.embedding_client.model_name,
            'embedding_dimensions': self.embedding_dim,
            'reranking_enabled': self.enable_reranking
        }
        
        # Estadísticas del índice
        if isinstance(self.index, FAISSIndex):
            stats['index'] = self.index.get_statistics()
        
        # Estadísticas de la BD
        stats['database'] = self.db.get_document_stats()
        
        return stats


# Funciones de conveniencia para uso directo
def create_search_engine(config: Optional[Dict[str, Any]] = None) -> SemanticSearchEngine:
    """
    Crea un motor de búsqueda con configuración opcional
    
    Args:
        config: Diccionario de configuración
        
    Returns:
        Motor de búsqueda configurado
    """
    default_config = {
        'embedding_backend': 'local',
        'embedding_model': 'BAAI/bge-large-es-v1.5',
        'enable_reranking': True,
        'use_multi_index': False
    }
    
    if config:
        default_config.update(config)
    
    return SemanticSearchEngine(**default_config)


def quick_search(query: str, k: int = 10) -> List[Dict[str, Any]]:
    """
    Búsqueda rápida usando configuración por defecto
    
    Args:
        query: Texto de búsqueda
        k: Número de resultados
        
    Returns:
        Lista de resultados
    """
    engine = create_search_engine()
    return engine.search(query, k=k)


if __name__ == "__main__":
    # Ejemplo de uso
    import json
    
    print("=== Prueba del motor de búsqueda semántica ===")
    
    # Crear motor
    engine = create_search_engine({
        'embedding_backend': 'local',
        'embedding_model': 'BAAI/bge-small-es-v1.5',  # Modelo pequeño para pruebas
        'enable_reranking': False  # Deshabilitado para pruebas rápidas
    })
    
    # Texto de ejemplo
    sample_text = """
    # La República de Platón
    
    La República es el diálogo más conocido e influyente de Platón, y es considerado
    como la piedra angular del pensamiento occidental. El texto trata sobre la justicia
    y examina si el hombre justo es más feliz que el injusto.
    
    ## Libro I: La naturaleza de la justicia
    
    Sócrates visita el Pireo con Glaucón, el hermano de Platón. Allí encuentran a
    Polemarco, quien los invita a su casa. En la casa, Sócrates entabla una conversación
    sobre la vejez con Céfalo, el padre de Polemarco.
    
    La discusión deriva hacia el tema de la justicia. Céfalo sugiere que la justicia
    consiste en decir la verdad y devolver lo que se ha recibido. Sócrates refuta
    esta definición con contraejemplos.
    
    ## Libro II: El desafío de Glaucón
    
    Glaucón no está satisfecho con los argumentos de Sócrates y presenta un desafío:
    demostrar que la justicia es deseable por sí misma, no solo por sus consecuencias.
    Para ilustrar su punto, cuenta la historia del anillo de Giges.
    """
    
    # Simular indexación de documento
    print("Indexando documento de ejemplo...")
    doc_id = 1
    num_chunks = engine.index_document(doc_id, sample_text)
    print(f"Documento indexado en {num_chunks} chunks")
    
    # Realizar búsquedas
    queries = [
        "¿Qué es la justicia según Platón?",
        "Historia del anillo de Giges",
        "Sócrates y la definición de justicia"
    ]
    
    for query in queries:
        print(f"\n🔍 Búsqueda: '{query}'")
        results = engine.search(query, k=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Chunk {result['chunk_id']}")
            print(f"   Similitud: {result['similarity']:.4f}")
            print(f"   Texto: {result['text'][:150]}...")
            print(f"   Tiempos: {json.dumps(result['timing'], indent=2)}")
    
    # Mostrar estadísticas
    stats = engine.get_statistics()
    print(f"\n📊 Estadísticas del motor:")
    print(json.dumps(stats, indent=2)) 