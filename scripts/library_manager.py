# -*- coding: utf-8 -*-
"""
Gestor de Biblioteca para Biblioperson

Este módulo maneja la persistencia de documentos procesados en una base de datos SQLite
para que puedan ser mostrados en la biblioteca del frontend.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class LibraryManager:
    """Gestor de la base de datos de biblioteca."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Inicializa el gestor de biblioteca.
        
        Args:
            db_path: Ruta a la base de datos SQLite. Si no se especifica,
                    usa una ruta por defecto en el directorio del usuario.
        """
        if db_path is None:
            # Crear directorio de datos si no existe
            data_dir = os.path.expanduser('~/AppData/Roaming/Biblioperson/data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'library.db')
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos con las tablas necesarias."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT,
                    content_preview TEXT,
                    full_content TEXT,
                    source_file TEXT,
                    file_type TEXT,
                    processed_date TEXT,
                    word_count INTEGER,
                    language TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_documents_author ON documents(author)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_documents_processed_date ON documents(processed_date)
            ''')
    
    def save_documents_from_ndjson(self, ndjson_file: str, job_id: str) -> int:
        """Guarda documentos desde un archivo NDJSON en la biblioteca.
        
        Args:
            ndjson_file: Ruta al archivo NDJSON con los documentos procesados
            job_id: ID del trabajo de procesamiento
            
        Returns:
            Número de documentos guardados
        """
        if not os.path.exists(ndjson_file):
            raise FileNotFoundError(f"Archivo NDJSON no encontrado: {ndjson_file}")
        
        documents_saved = 0
        processed_date = datetime.now().isoformat()
        
        # Variables para acumular el contenido completo del documento
        full_text_parts = []
        document_metadata = None
        
        with sqlite3.connect(self.db_path) as conn:
            with open(ndjson_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        doc = json.loads(line)
                        
                        # Si es la primera línea, capturamos los metadatos del documento
                        if document_metadata is None:
                            document_metadata = {
                                'title': (doc.get('title') or doc.get('document_title') or doc.get('content_title')
                                         or f'Documento sin título'),
                                'author': (doc.get('author') or doc.get('document_author') or doc.get('content_author')
                                          or 'Desconocido'),
                                'source_file': doc.get('source_file_path') or doc.get('source_file') or '',
                                'language': doc.get('document_language') or doc.get('language') or 'unknown',
                                'original_metadata': doc
                            }
                        
                        # Acumular el texto de cada segmento
                        segment_text = doc.get('text') or doc.get('content') or ''
                        if segment_text:
                            full_text_parts.append(segment_text)
                        
                    except json.JSONDecodeError as e:
                        print(f"Error al parsear línea {line_num} del NDJSON: {e}")
                        continue
                    except Exception as e:
                        print(f"Error procesando línea {line_num}: {e}")
                        continue
            
            # Al final, guardar el documento completo con todo el texto acumulado
            if document_metadata and full_text_parts:
                # Unir todos los segmentos de texto con saltos de línea dobles
                full_content = '\n\n'.join(full_text_parts)
                
                # Crear preview del contenido
                content_preview = full_content[:200] + '...' if len(full_content) > 200 else full_content
                
                # Contar palabras
                word_count = len(full_content.split())
                
                # Detectar tipo de archivo
                file_type = 'unknown'
                source_file = document_metadata['source_file']
                if source_file:
                    ext = Path(source_file).suffix.lower()
                    if ext in ['.txt', '.md']:
                        file_type = 'text'
                    elif ext in ['.pdf']:
                        file_type = 'pdf'
                    elif ext in ['.json']:
                        file_type = 'json'
                    elif ext in ['.docx', '.doc']:
                        file_type = 'document'
                
                # Guardar metadatos adicionales
                metadata = {
                    'job_id': job_id,
                    'total_segments': len(full_text_parts),
                    'original_metadata': document_metadata['original_metadata']
                }
                
                # Insertar en la base de datos
                conn.execute('''
                    INSERT INTO documents (
                        title, author, content_preview, full_content, 
                        source_file, file_type, processed_date, 
                        word_count, language, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_metadata['title'], 
                    document_metadata['author'], 
                    content_preview, 
                    full_content,
                    source_file, 
                    file_type, 
                    processed_date,
                    word_count, 
                    document_metadata['language'],
                    json.dumps(metadata)
                ))
                
                documents_saved = 1
                print(f"Documento guardado: {document_metadata['title']} ({len(full_text_parts)} segmentos, {word_count} palabras)")
        
        return documents_saved
    
    def get_documents(self, limit: int = 50, offset: int = 0, 
                     search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene documentos de la biblioteca.
        
        Args:
            limit: Número máximo de documentos a devolver
            offset: Número de documentos a omitir (para paginación)
            search: Término de búsqueda en título, autor o contenido
            
        Returns:
            Lista de documentos
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT id, title, author, content_preview, source_file, 
                       file_type, processed_date, word_count, language,
                       created_at
                FROM documents
            '''
            params = []
            
            if search:
                query += ''' WHERE (title LIKE ? OR author LIKE ? OR content_preview LIKE ?)'''
                search_term = f'%{search}%'
                params.extend([search_term, search_term, search_term])
            
            query += ''' ORDER BY created_at DESC LIMIT ? OFFSET ?'''
            params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            documents = []
            for row in rows:
                doc = {
                    'id': row['id'],
                    'title': row['title'],
                    'author': row['author'],
                    'content_preview': row['content_preview'],
                    'source_file': row['source_file'],
                    'file_type': row['file_type'],
                    'processed_date': row['processed_date'],
                    'word_count': row['word_count'],
                    'language': row['language'],
                    'created_at': row['created_at']
                }
                documents.append(doc)
            
            return documents
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un documento específico por su ID.
        
        Args:
            doc_id: ID del documento
            
        Returns:
            Documento completo o None si no se encuentra
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute('''
                SELECT * FROM documents WHERE id = ?
            ''', (doc_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            doc = dict(row)
            # Parsear metadatos JSON
            if doc['metadata']:
                try:
                    doc['metadata'] = json.loads(doc['metadata'])
                except json.JSONDecodeError:
                    doc['metadata'] = {}
            
            return doc
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la biblioteca.
        
        Returns:
            Diccionario con estadísticas
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) as total FROM documents')
            total_docs = cursor.fetchone()[0]
            
            cursor = conn.execute('''
                SELECT file_type, COUNT(*) as count 
                FROM documents 
                GROUP BY file_type
            ''')
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor = conn.execute('''
                SELECT author, COUNT(*) as count 
                FROM documents 
                WHERE author != 'Desconocido'
                GROUP BY author 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_authors = [{'author': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            cursor = conn.execute('SELECT SUM(word_count) as total_words FROM documents')
            total_words = cursor.fetchone()[0] or 0
            
            return {
                'total_documents': total_docs,
                'total_words': total_words,
                'documents_by_type': by_type,
                'top_authors': top_authors
            }
    
    def delete_document(self, doc_id: int) -> bool:
        """Elimina un documento de la biblioteca.
        
        Args:
            doc_id: ID del documento a eliminar
            
        Returns:
            True si se eliminó, False si no se encontró
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
            return cursor.rowcount > 0
    
    def clear_library(self) -> int:
        """Elimina todos los documentos de la biblioteca.
        
        Returns:
            Número de documentos eliminados
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('DELETE FROM documents')
            return cursor.rowcount


if __name__ == '__main__':
    # Prueba básica del módulo
    manager = LibraryManager()
    stats = manager.get_library_stats()
    print(f"Estadísticas de la biblioteca: {stats}")
    
    docs = manager.get_documents(limit=5)
    print(f"Documentos en la biblioteca: {len(docs)}")
    for doc in docs:
        print(f"- {doc['title']} por {doc['author']}")