"""
Módulo de indexación y búsqueda vectorial con FAISS
Optimizado para GPU cuando está disponible
"""

import os
import logging
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from dataclasses import dataclass
import time

# FAISS imports
try:
    import faiss
    HAS_FAISS = True
    
    # Intentar importar versión GPU
    try:
        import faiss.swigfaiss_gpu as swigfaiss_gpu
        HAS_GPU = True
    except ImportError:
        HAS_GPU = False
except ImportError:
    HAS_FAISS = False
    logging.error("FAISS no está instalado. Instala faiss-cpu o faiss-gpu")

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Resultado de búsqueda"""
    chunk_id: str
    document_id: int
    text: str
    score: float
    metadata: Dict[str, Any]
    chunk_index: int


class FAISSIndex:
    """
    Gestor de índices FAISS para búsqueda vectorial
    """
    
    def __init__(self,
                 dimension: int,
                 index_type: str = "Flat",
                 use_gpu: bool = True,
                 gpu_device: int = 0):
        """
        Inicializa el índice FAISS
        
        Args:
            dimension: Dimensión de los embeddings
            index_type: Tipo de índice ("Flat", "IVF", "HNSW")
            use_gpu: Intentar usar GPU si está disponible
            gpu_device: ID del dispositivo GPU
        """
        if not HAS_FAISS:
            raise ImportError("FAISS no está instalado")
        
        self.dimension = dimension
        self.index_type = index_type
        self.use_gpu = use_gpu and HAS_GPU
        self.gpu_device = gpu_device
        
        # Metadatos de los vectores
        self.metadata = {}
        self.id_to_index = {}  # Mapeo de chunk_id a índice en FAISS
        self.index_to_id = {}  # Mapeo inverso
        
        # Crear índice
        self.index = self._create_index()
        
        logger.info(f"Índice FAISS creado: {index_type}, dim={dimension}, GPU={self.use_gpu}")
    
    def _create_index(self) -> faiss.Index:
        """Crea el índice FAISS según el tipo especificado"""
        
        if self.index_type == "Flat":
            # Índice plano - búsqueda exacta
            index = faiss.IndexFlatL2(self.dimension)
            
        elif self.index_type == "IVF":
            # Índice IVF - más rápido para datasets grandes
            nlist = 100  # Número de clusters
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            
        elif self.index_type == "HNSW":
            # Índice HNSW - buen balance velocidad/precisión
            M = 32  # Número de conexiones
            index = faiss.IndexHNSWFlat(self.dimension, M)
            
        else:
            raise ValueError(f"Tipo de índice no soportado: {self.index_type}")
        
        # Mover a GPU si está disponible y solicitado
        if self.use_gpu:
            try:
                res = faiss.StandardGpuResources()
                index = faiss.index_cpu_to_gpu(res, self.gpu_device, index)
                logger.info(f"Índice movido a GPU {self.gpu_device}")
            except Exception as e:
                logger.warning(f"No se pudo mover índice a GPU: {e}")
                self.use_gpu = False
        
        return index
    
    def add_embeddings(self,
                      embeddings: np.ndarray,
                      chunk_ids: List[str],
                      metadata: List[Dict[str, Any]]):
        """
        Agrega embeddings al índice
        
        Args:
            embeddings: Array de embeddings (n_samples, dimension)
            chunk_ids: IDs únicos de los chunks
            metadata: Metadatos asociados a cada chunk
        """
        if len(embeddings) != len(chunk_ids) != len(metadata):
            raise ValueError("embeddings, chunk_ids y metadata deben tener la misma longitud")
        
        # Normalizar embeddings para búsqueda por similitud coseno
        embeddings = embeddings.astype(np.float32)
        faiss.normalize_L2(embeddings)
        
        # Si es IVF, entrenar si es necesario
        if self.index_type == "IVF" and not self.index.is_trained:
            logger.info("Entrenando índice IVF...")
            self.index.train(embeddings)
        
        # Obtener índices actuales
        start_idx = self.index.ntotal
        
        # Agregar al índice
        self.index.add(embeddings)
        
        # Actualizar metadatos
        for i, (chunk_id, meta) in enumerate(zip(chunk_ids, metadata)):
            idx = start_idx + i
            self.metadata[idx] = meta
            self.id_to_index[chunk_id] = idx
            self.index_to_id[idx] = chunk_id
        
        logger.info(f"Agregados {len(embeddings)} embeddings. Total: {self.index.ntotal}")
    
    def search(self,
              query_embedding: np.ndarray,
              k: int = 20,
              filter_fn: Optional[callable] = None) -> List[SearchResult]:
        """
        Busca los k vecinos más cercanos
        
        Args:
            query_embedding: Embedding de la consulta
            k: Número de resultados
            filter_fn: Función opcional para filtrar resultados
            
        Returns:
            Lista de SearchResult ordenados por similitud
        """
        # Normalizar query
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Buscar más resultados si hay filtro
        search_k = k * 3 if filter_fn else k
        search_k = min(search_k, self.index.ntotal)
        
        # Realizar búsqueda
        start_time = time.time()
        distances, indices = self.index.search(query_embedding, search_k)
        search_time = (time.time() - start_time) * 1000  # ms
        
        logger.debug(f"Búsqueda FAISS completada en {search_time:.2f}ms")
        
        # Procesar resultados
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS devuelve -1 para resultados no válidos
                continue
            
            # Obtener metadatos
            meta = self.metadata.get(idx, {})
            chunk_id = self.index_to_id.get(idx, f"unknown_{idx}")
            
            # Aplicar filtro si existe
            if filter_fn and not filter_fn(meta):
                continue
            
            # Convertir distancia L2 a similitud coseno
            # Para vectores normalizados: cos_sim = 1 - (L2_dist^2 / 2)
            similarity = 1 - (dist / 2)
            
            result = SearchResult(
                chunk_id=chunk_id,
                document_id=meta.get('document_id', -1),
                text=meta.get('text', ''),
                score=float(similarity),
                metadata=meta,
                chunk_index=meta.get('chunk_index', -1)
            )
            
            results.append(result)
            
            if len(results) >= k:
                break
        
        return results
    
    def batch_search(self,
                    query_embeddings: np.ndarray,
                    k: int = 20) -> List[List[SearchResult]]:
        """
        Búsqueda en lote para múltiples queries
        
        Args:
            query_embeddings: Array de embeddings (n_queries, dimension)
            k: Número de resultados por query
            
        Returns:
            Lista de listas de SearchResult
        """
        # Normalizar queries
        query_embeddings = query_embeddings.astype(np.float32)
        faiss.normalize_L2(query_embeddings)
        
        # Realizar búsqueda
        distances, indices = self.index.search(query_embeddings, k)
        
        # Procesar resultados para cada query
        all_results = []
        for query_idx in range(len(query_embeddings)):
            query_results = []
            
            for dist, idx in zip(distances[query_idx], indices[query_idx]):
                if idx == -1:
                    continue
                
                meta = self.metadata.get(idx, {})
                chunk_id = self.index_to_id.get(idx, f"unknown_{idx}")
                similarity = 1 - (dist / 2)
                
                result = SearchResult(
                    chunk_id=chunk_id,
                    document_id=meta.get('document_id', -1),
                    text=meta.get('text', ''),
                    score=float(similarity),
                    metadata=meta,
                    chunk_index=meta.get('chunk_index', -1)
                )
                
                query_results.append(result)
            
            all_results.append(query_results)
        
        return all_results
    
    def remove_document(self, document_id: int):
        """
        Elimina todos los chunks de un documento del índice
        
        Nota: FAISS no soporta eliminación directa, se debe reconstruir
        """
        # Encontrar índices a eliminar
        indices_to_remove = []
        for idx, meta in self.metadata.items():
            if meta.get('document_id') == document_id:
                indices_to_remove.append(idx)
        
        if not indices_to_remove:
            return
        
        logger.info(f"Eliminando {len(indices_to_remove)} chunks del documento {document_id}")
        
        # Reconstruir índice sin los elementos eliminados
        self._rebuild_without_indices(indices_to_remove)
    
    def _rebuild_without_indices(self, indices_to_remove: List[int]):
        """Reconstruye el índice excluyendo ciertos índices"""
        # Obtener todos los vectores
        vectors = []
        new_metadata = {}
        new_id_to_index = {}
        new_index_to_id = {}
        
        # Reconstruir datos excluyendo índices a eliminar
        new_idx = 0
        for old_idx in range(self.index.ntotal):
            if old_idx not in indices_to_remove:
                # Obtener vector
                vector = self.index.reconstruct(old_idx)
                vectors.append(vector)
                
                # Actualizar mapeos
                chunk_id = self.index_to_id.get(old_idx)
                if chunk_id:
                    new_id_to_index[chunk_id] = new_idx
                    new_index_to_id[new_idx] = chunk_id
                
                # Copiar metadata
                if old_idx in self.metadata:
                    new_metadata[new_idx] = self.metadata[old_idx]
                
                new_idx += 1
        
        # Crear nuevo índice
        self.index = self._create_index()
        
        # Re-agregar vectores
        if vectors:
            vectors_array = np.array(vectors).astype(np.float32)
            
            if self.index_type == "IVF":
                self.index.train(vectors_array)
            
            self.index.add(vectors_array)
        
        # Actualizar metadatos
        self.metadata = new_metadata
        self.id_to_index = new_id_to_index
        self.index_to_id = new_index_to_id
        
        logger.info(f"Índice reconstruido. Nuevo total: {self.index.ntotal}")
    
    def save(self, index_path: str, metadata_path: str):
        """
        Guarda el índice y metadatos a disco
        
        Args:
            index_path: Ruta para guardar el índice FAISS
            metadata_path: Ruta para guardar los metadatos
        """
        # Crear directorios si no existen
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar índice FAISS
        if self.use_gpu:
            # Transferir a CPU antes de guardar
            cpu_index = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(cpu_index, index_path)
        else:
            faiss.write_index(self.index, index_path)
        
        # Guardar metadatos
        metadata_dict = {
            'metadata': self.metadata,
            'id_to_index': self.id_to_index,
            'index_to_id': self.index_to_id,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'total_vectors': self.index.ntotal
        }
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata_dict, f)
        
        logger.info(f"Índice guardado: {index_path}, metadatos: {metadata_path}")
    
    def load(self, index_path: str, metadata_path: str):
        """
        Carga el índice y metadatos desde disco
        
        Args:
            index_path: Ruta del índice FAISS
            metadata_path: Ruta de los metadatos
        """
        # Cargar índice FAISS
        self.index = faiss.read_index(index_path)
        
        # Mover a GPU si corresponde
        if self.use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, self.gpu_device, self.index)
            except Exception as e:
                logger.warning(f"No se pudo mover índice a GPU: {e}")
                self.use_gpu = False
        
        # Cargar metadatos
        with open(metadata_path, 'rb') as f:
            metadata_dict = pickle.load(f)
        
        self.metadata = metadata_dict['metadata']
        self.id_to_index = metadata_dict['id_to_index']
        self.index_to_id = metadata_dict['index_to_id']
        self.dimension = metadata_dict['dimension']
        self.index_type = metadata_dict['index_type']
        
        logger.info(f"Índice cargado: {self.index.ntotal} vectores")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del índice"""
        stats = {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'use_gpu': self.use_gpu,
            'memory_usage_mb': self._estimate_memory_usage()
        }
        
        # Estadísticas por documento
        doc_counts = {}
        for meta in self.metadata.values():
            doc_id = meta.get('document_id', 'unknown')
            doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
        
        stats['documents'] = len(doc_counts)
        stats['avg_chunks_per_doc'] = np.mean(list(doc_counts.values())) if doc_counts else 0
        
        return stats
    
    def _estimate_memory_usage(self) -> float:
        """Estima el uso de memoria en MB"""
        # Tamaño aproximado: vectores + overhead
        vector_size = self.index.ntotal * self.dimension * 4  # float32
        metadata_size = len(str(self.metadata).encode('utf-8'))
        
        total_bytes = vector_size + metadata_size
        return total_bytes / (1024 * 1024)
    
    def optimize(self):
        """Optimiza el índice para búsquedas más rápidas"""
        if self.index_type == "IVF":
            # Ajustar nprobe para balance velocidad/precisión
            self.index.nprobe = 10
            logger.info("Índice IVF optimizado: nprobe=10")
        
        elif self.index_type == "HNSW":
            # HNSW se optimiza durante la construcción
            logger.info("Índice HNSW ya está optimizado")
        
        else:
            logger.info("No hay optimizaciones disponibles para índice Flat")


class MultiDocumentIndex:
    """
    Gestor de múltiples índices FAISS (uno por documento)
    Útil para documentos muy grandes o cuando se necesita eliminar documentos frecuentemente
    """
    
    def __init__(self, dimension: int, index_dir: str = "indexes"):
        """
        Inicializa el gestor multi-índice
        
        Args:
            dimension: Dimensión de los embeddings
            index_dir: Directorio para almacenar índices
        """
        self.dimension = dimension
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Caché de índices cargados
        self.indices = {}
        
        # Índice maestro con información de documentos
        self.master_index = self._load_master_index()
    
    def _load_master_index(self) -> Dict[int, Dict[str, Any]]:
        """Carga o crea el índice maestro"""
        master_path = self.index_dir / "master_index.json"
        
        if master_path.exists():
            with open(master_path, 'r') as f:
                return json.load(f)
        
        return {}
    
    def _save_master_index(self):
        """Guarda el índice maestro"""
        master_path = self.index_dir / "master_index.json"
        with open(master_path, 'w') as f:
            json.dump(self.master_index, f, indent=2)
    
    def add_document(self,
                    document_id: int,
                    embeddings: np.ndarray,
                    chunk_ids: List[str],
                    metadata: List[Dict[str, Any]]):
        """
        Agrega un documento completo con sus embeddings
        """
        # Crear índice para el documento
        doc_index = FAISSIndex(self.dimension, index_type="Flat", use_gpu=False)
        doc_index.add_embeddings(embeddings, chunk_ids, metadata)
        
        # Guardar índice
        index_path = self.index_dir / f"doc_{document_id}.index"
        meta_path = self.index_dir / f"doc_{document_id}.meta"
        doc_index.save(str(index_path), str(meta_path))
        
        # Actualizar índice maestro
        self.master_index[str(document_id)] = {
            'document_id': document_id,
            'num_chunks': len(embeddings),
            'index_path': str(index_path),
            'meta_path': str(meta_path),
            'created_at': time.time()
        }
        self._save_master_index()
        
        # Agregar a caché
        self.indices[document_id] = doc_index
        
        logger.info(f"Documento {document_id} indexado con {len(embeddings)} chunks")
    
    def search_all(self,
                  query_embedding: np.ndarray,
                  k: int = 20,
                  document_ids: Optional[List[int]] = None) -> List[SearchResult]:
        """
        Busca en todos los documentos o en un subconjunto
        """
        all_results = []
        
        # Determinar documentos a buscar
        if document_ids:
            docs_to_search = [str(d) for d in document_ids if str(d) in self.master_index]
        else:
            docs_to_search = list(self.master_index.keys())
        
        # Buscar en cada documento
        for doc_id_str in docs_to_search:
            doc_id = int(doc_id_str)
            
            # Cargar índice si no está en caché
            if doc_id not in self.indices:
                doc_info = self.master_index[doc_id_str]
                doc_index = FAISSIndex(self.dimension)
                doc_index.load(doc_info['index_path'], doc_info['meta_path'])
                self.indices[doc_id] = doc_index
            
            # Buscar en el documento
            doc_results = self.indices[doc_id].search(query_embedding, k)
            all_results.extend(doc_results)
        
        # Ordenar todos los resultados por score
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        return all_results[:k]
    
    def remove_document(self, document_id: int):
        """Elimina un documento completo"""
        doc_id_str = str(document_id)
        
        if doc_id_str not in self.master_index:
            return
        
        # Eliminar archivos
        doc_info = self.master_index[doc_id_str]
        for path in [doc_info['index_path'], doc_info['meta_path']]:
            if os.path.exists(path):
                os.remove(path)
        
        # Eliminar de índice maestro
        del self.master_index[doc_id_str]
        self._save_master_index()
        
        # Eliminar de caché
        if document_id in self.indices:
            del self.indices[document_id]
        
        logger.info(f"Documento {document_id} eliminado del índice")


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Prueba de índice FAISS ===")
    
    # Crear datos de prueba
    dimension = 384  # Dimensión pequeña para pruebas
    num_chunks = 1000
    
    # Generar embeddings aleatorios
    embeddings = np.random.randn(num_chunks, dimension).astype(np.float32)
    chunk_ids = [f"chunk_{i}" for i in range(num_chunks)]
    metadata = [
        {
            'document_id': i // 100,
            'chunk_index': i % 100,
            'text': f"Este es el texto del chunk {i}"
        }
        for i in range(num_chunks)
    ]
    
    # Crear índice
    print("Creando índice...")
    index = FAISSIndex(dimension, index_type="Flat", use_gpu=False)
    
    # Agregar embeddings
    print("Agregando embeddings...")
    index.add_embeddings(embeddings, chunk_ids, metadata)
    
    # Realizar búsqueda
    print("\nRealizando búsqueda...")
    query = np.random.randn(dimension).astype(np.float32)
    results = index.search(query, k=5)
    
    print(f"\nTop 5 resultados:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result.chunk_id} (doc {result.document_id})")
        print(f"   Score: {result.score:.4f}")
        print(f"   Texto: {result.text}")
    
    # Mostrar estadísticas
    stats = index.get_statistics()
    print(f"\nEstadísticas del índice:")
    print(f"- Total vectores: {stats['total_vectors']}")
    print(f"- Documentos: {stats['documents']}")
    print(f"- Memoria estimada: {stats['memory_usage_mb']:.2f} MB") 