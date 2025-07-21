"""
Módulo de persistencia para la base de datos de Biblioperson
Maneja el guardado de documentos, bloques estructurales y chunks
"""

import sqlite3
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestor de base de datos para Biblioperson
    """
    
    def __init__(self, db_path: str = "data/biblioperson.db"):
        """
        Inicializa el gestor de base de datos
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos con el esquema v2"""
        schema_path = Path("database/schema_v2.sql")
        
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                # Ejecutar el esquema
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Base de datos inicializada con esquema v2")
        else:
            logger.warning(f"No se encontró el archivo de esquema: {schema_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a la base de datos"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        try:
            yield conn
        finally:
            conn.close()
    
    def save_document(self, 
                     file_path: str,
                     title: str,
                     author: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Guarda un documento en la base de datos
        
        Returns:
            ID del documento guardado
        """
        file_path = Path(file_path)
        
        # Calcular hash del archivo
        file_hash = self._calculate_file_hash(file_path)
        
        # Preparar metadatos
        doc_metadata = metadata or {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si el documento ya existe
            cursor.execute(
                "SELECT id FROM documents WHERE file_hash = ?",
                (file_hash,)
            )
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"Documento ya existe con ID: {existing['id']}")
                return existing['id']
            
            # Insertar nuevo documento
            cursor.execute("""
                INSERT INTO documents (
                    title, author, file_path, file_hash, file_type, file_size,
                    language, metadata, used_ocr, page_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title,
                author,
                str(file_path),
                file_hash,
                file_path.suffix.lower(),
                file_path.stat().st_size,
                doc_metadata.get('language', 'es'),
                json.dumps(doc_metadata),
                doc_metadata.get('used_ocr', False),
                doc_metadata.get('page_count')
            ))
            
            conn.commit()
            document_id = cursor.lastrowid
            
            logger.info(f"Documento guardado con ID: {document_id}")
            return document_id
    
    def save_structural_blocks(self,
                              document_id: int,
                              elements: List[Dict[str, Any]],
                              batch_size: int = 1000) -> int:
        """
        Guarda bloques estructurales en lotes
        
        Args:
            document_id: ID del documento
            elements: Lista de elementos estructurales
            batch_size: Tamaño del lote para inserción
            
        Returns:
            Número de bloques guardados
        """
        if not elements:
            return 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Preparar datos para inserción
            blocks_data = []
            for element in elements:
                block_data = (
                    document_id,
                    element.get('order', len(blocks_data)),
                    None,  # parent_block_id (por ahora no manejamos anidación)
                    0,     # depth_level
                    element.get('type', 'Text'),
                    element.get('text', ''),
                    json.dumps(element.get('style_info', {})),
                    json.dumps(element.get('position_info', {})),
                    element.get('image_path'),
                    json.dumps(element.get('table_data')) if element.get('table_data') else None,
                    element.get('link_url'),
                    json.dumps(element.get('metadata', {}))
                )
                blocks_data.append(block_data)
            
            # Insertar en lotes
            total_inserted = 0
            for i in range(0, len(blocks_data), batch_size):
                batch = blocks_data[i:i + batch_size]
                cursor.executemany("""
                    INSERT INTO structural_blocks (
                        document_id, order_index, parent_block_id, depth_level,
                        block_type, text_content, style_info, position_info,
                        image_path, table_data, link_url, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                total_inserted += len(batch)
                
                if total_inserted % 5000 == 0:
                    logger.info(f"Insertados {total_inserted} bloques...")
            
            conn.commit()
            logger.info(f"Total de bloques guardados: {total_inserted}")
            return total_inserted
    
    def save_semantic_chunks(self,
                           document_id: int,
                           chunks: List[Dict[str, Any]],
                           batch_size: int = 500) -> int:
        """
        Guarda chunks semánticos con sus embeddings
        
        Args:
            document_id: ID del documento
            chunks: Lista de chunks con sus embeddings
            batch_size: Tamaño del lote
            
        Returns:
            Número de chunks guardados
        """
        if not chunks:
            return 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener bloques estructurales para mapear
            cursor.execute(
                "SELECT id, order_index FROM structural_blocks WHERE document_id = ? ORDER BY order_index",
                (document_id,)
            )
            blocks = cursor.fetchall()
            block_map = {b['order_index']: b['id'] for b in blocks}
            
            # Preparar datos
            chunks_data = []
            for i, chunk in enumerate(chunks):
                # Serializar embedding si existe
                embedding_blob = None
                if 'embedding' in chunk and chunk['embedding'] is not None:
                    if isinstance(chunk['embedding'], np.ndarray):
                        embedding_blob = chunk['embedding'].tobytes()
                    elif isinstance(chunk['embedding'], list):
                        embedding_blob = np.array(chunk['embedding'], dtype=np.float32).tobytes()
                
                # Mapear bloques de inicio y fin
                start_block = chunk.get('start_block_index', 0)
                end_block = chunk.get('end_block_index', start_block)
                
                chunk_data = (
                    document_id,
                    i,  # chunk_index
                    f"doc_{document_id}_chunk_{i}",  # chunk_id único
                    chunk.get('text', ''),
                    len(chunk.get('text', '')),
                    block_map.get(start_block),
                    block_map.get(end_block),
                    chunk.get('profile', 'default'),
                    None,  # previous_chunk_id (se actualiza después)
                    None,  # next_chunk_id (se actualiza después)
                    embedding_blob,
                    chunk.get('embedding_model'),
                    chunk.get('embedding_dimensions'),
                    json.dumps(chunk.get('metadata', {})),
                    datetime.now() if embedding_blob else None  # indexed_at
                )
                chunks_data.append(chunk_data)
            
            # Insertar en lotes
            total_inserted = 0
            chunk_ids = []
            
            for i in range(0, len(chunks_data), batch_size):
                batch = chunks_data[i:i + batch_size]
                cursor.executemany("""
                    INSERT INTO semantic_chunks (
                        document_id, chunk_index, chunk_id, text_content, chunk_size,
                        start_block_id, end_block_id, chunk_profile,
                        previous_chunk_id, next_chunk_id,
                        embedding, embedding_model, embedding_dimensions,
                        metadata, indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                
                # Obtener IDs insertados
                for j in range(len(batch)):
                    chunk_ids.append(cursor.lastrowid - len(batch) + j + 1)
                
                total_inserted += len(batch)
            
            # Actualizar enlaces previous/next
            for i in range(len(chunk_ids)):
                prev_id = chunk_ids[i-1] if i > 0 else None
                next_id = chunk_ids[i+1] if i < len(chunk_ids)-1 else None
                
                cursor.execute("""
                    UPDATE semantic_chunks 
                    SET previous_chunk_id = ?, next_chunk_id = ?
                    WHERE id = ?
                """, (prev_id, next_id, chunk_ids[i]))
            
            conn.commit()
            logger.info(f"Total de chunks guardados: {total_inserted}")
            return total_inserted
    
    def get_document_blocks(self, document_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los bloques estructurales de un documento para reconstrucción
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM structural_blocks 
                WHERE document_id = ? 
                ORDER BY order_index
            """, (document_id,))
            
            blocks = []
            for row in cursor.fetchall():
                block = dict(row)
                # Parsear JSON fields
                if block['style_info']:
                    block['style_info'] = json.loads(block['style_info'])
                if block['position_info']:
                    block['position_info'] = json.loads(block['position_info'])
                if block['metadata']:
                    block['metadata'] = json.loads(block['metadata'])
                if block['table_data']:
                    block['table_data'] = json.loads(block['table_data'])
                blocks.append(block)
            
            return blocks
    
    def search_chunks(self, 
                     query_embedding: np.ndarray,
                     limit: int = 20,
                     document_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Busca chunks similares usando embeddings
        
        Args:
            query_embedding: Embedding de la consulta
            limit: Número máximo de resultados
            document_ids: Filtrar por documentos específicos
            
        Returns:
            Lista de chunks ordenados por similitud
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construir query base
            query = """
                SELECT 
                    sc.*,
                    d.title as document_title,
                    d.author as document_author,
                    d.file_type
                FROM semantic_chunks sc
                JOIN documents d ON sc.document_id = d.id
                WHERE sc.embedding IS NOT NULL
            """
            
            params = []
            if document_ids:
                placeholders = ','.join('?' * len(document_ids))
                query += f" AND sc.document_id IN ({placeholders})"
                params.extend(document_ids)
            
            cursor.execute(query, params)
            
            # Calcular similitudes
            results = []
            for row in cursor.fetchall():
                chunk = dict(row)
                
                # Deserializar embedding
                if chunk['embedding']:
                    stored_embedding = np.frombuffer(chunk['embedding'], dtype=np.float32)
                    
                    # Calcular similitud coseno
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )
                    
                    chunk['similarity'] = float(similarity)
                    chunk['embedding'] = None  # No devolver el embedding completo
                    
                    # Parsear metadata
                    if chunk['metadata']:
                        chunk['metadata'] = json.loads(chunk['metadata'])
                    
                    results.append(chunk)
            
            # Ordenar por similitud descendente
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:limit]
    
    def update_chunk_embeddings(self,
                              chunk_embeddings: List[Tuple[int, np.ndarray, str]]):
        """
        Actualiza embeddings de chunks existentes
        
        Args:
            chunk_embeddings: Lista de tuplas (chunk_id, embedding, model_name)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for chunk_id, embedding, model_name in chunk_embeddings:
                embedding_blob = embedding.tobytes() if isinstance(embedding, np.ndarray) else None
                
                cursor.execute("""
                    UPDATE semantic_chunks
                    SET embedding = ?, 
                        embedding_model = ?,
                        embedding_dimensions = ?,
                        indexed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    embedding_blob,
                    model_name,
                    len(embedding) if embedding is not None else None,
                    chunk_id
                ))
            
            conn.commit()
            logger.info(f"Actualizados {len(chunk_embeddings)} embeddings")
    
    def get_chunks_without_embeddings(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Obtiene chunks que no tienen embeddings generados
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, document_id, chunk_id, text_content, chunk_profile
                FROM semantic_chunks
                WHERE embedding IS NULL
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_biblical_version(self, 
                            version_code: str,
                            version_name: str,
                            language: str = 'es') -> int:
        """
        Guarda una versión bíblica
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO biblical_versions 
                (version_code, version_name, language)
                VALUES (?, ?, ?)
            """, (version_code, version_name, language))
            
            conn.commit()
            
            # Obtener ID
            cursor.execute(
                "SELECT id FROM biblical_versions WHERE version_code = ?",
                (version_code,)
            )
            return cursor.fetchone()['id']
    
    def save_biblical_content(self,
                            version_id: int,
                            books_data: List[Dict[str, Any]]):
        """
        Guarda libros, capítulos y versículos bíblicos
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for book in books_data:
                # Insertar libro
                cursor.execute("""
                    INSERT INTO biblical_books
                    (version_id, book_number, book_name, book_abbrev, testament,
                     chapter_count, verse_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    version_id,
                    book['number'],
                    book['name'],
                    book['abbrev'],
                    book['testament'],
                    book['chapter_count'],
                    book['verse_count']
                ))
                
                book_id = cursor.lastrowid
                
                # Insertar versículos
                verses_data = []
                for verse in book.get('verses', []):
                    verses_data.append((
                        book_id,
                        verse['chapter'],
                        verse['verse'],
                        verse['text'],
                        json.dumps(verse.get('cross_references', []))
                    ))
                
                if verses_data:
                    cursor.executemany("""
                        INSERT INTO biblical_verses
                        (book_id, chapter_number, verse_number, verse_text, cross_references)
                        VALUES (?, ?, ?, ?, ?)
                    """, verses_data)
            
            conn.commit()
    
    def get_user_config(self, user_id: str = 'default') -> Dict[str, Any]:
        """
        Obtiene la configuración del usuario
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_config WHERE user_id = ?",
                (user_id,)
            )
            
            row = cursor.fetchone()
            if row:
                config = dict(row)
                if config['config_json']:
                    config['config_json'] = json.loads(config['config_json'])
                return config
            else:
                # Crear configuración por defecto
                cursor.execute("""
                    INSERT INTO user_config (user_id) VALUES (?)
                """, (user_id,))
                conn.commit()
                return self.get_user_config(user_id)
    
    def update_user_config(self, user_id: str, config: Dict[str, Any]):
        """
        Actualiza la configuración del usuario
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Extraer campos conocidos
            known_fields = {
                'preferred_chunk_size': config.get('preferred_chunk_size'),
                'preferred_overlap': config.get('preferred_overlap'),
                'search_result_limit': config.get('search_result_limit'),
                'rerank_results': config.get('rerank_results'),
                'preferred_font_size': config.get('preferred_font_size'),
                'preferred_theme': config.get('preferred_theme'),
                'embedding_backend': config.get('embedding_backend')
            }
            
            # Resto en config_json
            extra_config = {k: v for k, v in config.items() if k not in known_fields}
            
            # Construir update dinámico
            set_clauses = []
            values = []
            for field, value in known_fields.items():
                if value is not None:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if extra_config:
                set_clauses.append("config_json = ?")
                values.append(json.dumps(extra_config))
            
            if set_clauses:
                values.append(user_id)
                cursor.execute(f"""
                    UPDATE user_config 
                    SET {', '.join(set_clauses)}
                    WHERE user_id = ?
                """, values)
                conn.commit()
    
    def log_search(self,
                  query_text: str,
                  query_embedding: Optional[np.ndarray],
                  results: List[str],
                  search_duration_ms: int,
                  rerank_duration_ms: Optional[int] = None):
        """
        Registra una búsqueda para analytics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            embedding_blob = query_embedding.tobytes() if query_embedding is not None else None
            
            cursor.execute("""
                INSERT INTO search_history
                (query_text, query_embedding, result_count, top_results,
                 search_duration_ms, rerank_duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                query_text,
                embedding_blob,
                len(results),
                json.dumps(results[:10]),  # Top 10 IDs
                search_duration_ms,
                rerank_duration_ms
            ))
            conn.commit()
    
    def get_document_stats(self) -> List[Dict[str, Any]]:
        """
        Obtiene estadísticas de documentos
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_stats")
            return [dict(row) for row in cursor.fetchall()]
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula el hash SHA256 de un archivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def cleanup_old_data(self, days: int = 30):
        """
        Limpia datos antiguos de la base de datos
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Limpiar historial de búsquedas antiguo
            cursor.execute("""
                DELETE FROM search_history
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            
            logger.info(f"Eliminadas {deleted} búsquedas antiguas")
    
    def vacuum(self):
        """Optimiza la base de datos"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("Base de datos optimizada")


# Singleton para uso global
_db_manager = None

def get_db_manager(db_path: str = "data/biblioperson.db") -> DatabaseManager:
    """Obtiene la instancia singleton del gestor de BD"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


if __name__ == "__main__":
    # Prueba básica
    db = DatabaseManager()
    
    # Guardar un documento de prueba
    doc_id = db.save_document(
        file_path="test.pdf",
        title="Documento de Prueba",
        author="Autor Prueba",
        metadata={"language": "es", "used_ocr": False}
    )
    
    print(f"Documento guardado con ID: {doc_id}")
    
    # Guardar bloques de prueba
    blocks = [
        {"order": 0, "type": "Title", "text": "Título Principal"},
        {"order": 1, "type": "NarrativeText", "text": "Este es el contenido del documento."}
    ]
    
    num_blocks = db.save_structural_blocks(doc_id, blocks)
    print(f"Bloques guardados: {num_blocks}")
    
    # Obtener estadísticas
    stats = db.get_document_stats()
    print(f"Estadísticas: {stats}") 