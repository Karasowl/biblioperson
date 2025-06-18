#!/usr/bin/env python3
"""
Script para indexar contenido de SQLite en MeiliSearch con soporte vectorial.

Este script:
1. Conecta a la base de datos SQLite
2. Obtiene contenido con embeddings
3. Configura índices en MeiliSearch
4. Indexa contenido para búsqueda híbrida (texto + vectorial)

Uso:
    python indexar_meilisearch.py
    python indexar_meilisearch.py --indexar-nuevos
    python indexar_meilisearch.py --recrear-indice
"""

import os
import sys
import sqlite3
import argparse
import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import meilisearch
except ImportError:
    logger.error("meilisearch no está instalado. Instálalo con: pip install meilisearch")
    sys.exit(1)

class MeiliSearchIndexer:
    """Indexador de MeiliSearch para contenido de Biblioperson."""
    
    def __init__(self, meilisearch_url: str = "http://localhost:7700", api_key: Optional[str] = None):
        self.meilisearch_url = meilisearch_url
        self.api_key = api_key
        self.client = None
        self.db_path = self._find_database_path()
        self.index_name = "biblioperson_content"
        
    def _find_database_path(self) -> str:
        """Encuentra la ruta de la base de datos SQLite."""
        possible_paths = [
            "dataset/data/biblioperson.db",
            "dataset/biblioperson.db",
            "data/biblioperson.db",
            "biblioperson.db"
        ]
        
        project_root = Path(__file__).parent.parent.parent
        
        for path in possible_paths:
            full_path = project_root / path
            if full_path.exists():
                logger.info(f"Base de datos encontrada en: {full_path}")
                return str(full_path)
        
        default_path = project_root / "dataset" / "data" / "biblioperson.db"
        logger.warning(f"Base de datos no encontrada. Usando ruta por defecto: {default_path}")
        return str(default_path)
    
    def connect_meilisearch(self):
        """Conecta a MeiliSearch."""
        try:
            self.client = meilisearch.Client(self.meilisearch_url, self.api_key)
            # Verificar conexión
            health = self.client.health()
            logger.info(f"Conectado a MeiliSearch: {health}")
        except Exception as e:
            logger.error(f"Error al conectar con MeiliSearch: {e}")
            raise
    
    def setup_index(self, recreate: bool = False):
        """Configura el índice de MeiliSearch."""
        if not self.client:
            self.connect_meilisearch()
        
        try:
            # Eliminar índice si se solicita recrear
            if recreate:
                try:
                    self.client.delete_index(self.index_name)
                    logger.info(f"Índice {self.index_name} eliminado")
                except:
                    pass  # El índice puede no existir
            
            # Crear o obtener índice
            index = self.client.index(self.index_name)
            
            # Configurar atributos de búsqueda
            searchable_attributes = [
                'texto_segmento',
                'titulo_documento',
                'autor_documento',
                'tipo_segmento'
            ]
            
            # Configurar atributos filtrables
            filterable_attributes = [
                'autor_documento',
                'tipo_segmento',
                'idioma_documento',
                'fecha_publicacion_documento'
            ]
            
            # Configurar atributos ordenables
            sortable_attributes = [
                'orden_segmento_documento',
                'fecha_publicacion_documento'
            ]
            
            # Aplicar configuraciones
            index.update_searchable_attributes(searchable_attributes)
            index.update_filterable_attributes(filterable_attributes)
            index.update_sortable_attributes(sortable_attributes)
            
            # Configurar embeddings para búsqueda vectorial
            embedder_settings = {
                "source": "userProvided",
                "dimensions": 384  # Para all-MiniLM-L6-v2
            }
            
            try:
                index.update_embedders({"default": embedder_settings})
                logger.info("Configuración de embeddings aplicada")
            except Exception as e:
                logger.warning(f"No se pudo configurar embeddings vectoriales: {e}")
            
            logger.info(f"Índice {self.index_name} configurado correctamente")
            return index
            
        except Exception as e:
            logger.error(f"Error al configurar índice: {e}")
            raise
    
    def get_content_with_embeddings(self, only_new: bool = False) -> List[Dict[str, Any]]:
        """Obtiene contenido con embeddings de la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar tabla de contenido
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%contenido%'
            """)
            tables = cursor.fetchall()
            
            if not tables:
                logger.error("No se encontraron tablas de contenido")
                return []
            
            content_table = tables[0][0]
            logger.info(f"Usando tabla de contenido: {content_table}")
            
            # Construir query
            base_query = f"""
                SELECT 
                    id,
                    id_unico,
                    texto_segmento,
                    autor_documento,
                    titulo_documento,
                    orden_segmento_documento,
                    tipo_segmento,
                    idioma_documento,
                    fecha_publicacion_documento,
                    jerarquia_contextual,
                    embedding_vectorial
                FROM {content_table}
                WHERE embedding_vectorial IS NOT NULL AND embedding_vectorial != ''
            """
            
            if only_new:
                # Agregar condición para contenido no indexado
                base_query += " AND (indexado_meilisearch IS NULL OR indexado_meilisearch = 0)"
            
            cursor.execute(base_query)
            results = cursor.fetchall()
            
            # Convertir a diccionarios
            content_list = []
            for row in results:
                try:
                    embedding = json.loads(row[10]) if row[10] else None
                    jerarquia = json.loads(row[9]) if row[9] else {}
                    
                    content_item = {
                        'id': row[0],
                        'id_unico': row[1],
                        'texto_segmento': row[2],
                        'autor_documento': row[3],
                        'titulo_documento': row[4],
                        'orden_segmento_documento': row[5],
                        'tipo_segmento': row[6],
                        'idioma_documento': row[7],
                        'fecha_publicacion_documento': row[8],
                        'jerarquia_contextual': jerarquia,
                        '_vectors': {'default': embedding} if embedding else None
                    }
                    
                    content_list.append(content_item)
                    
                except Exception as e:
                    logger.warning(f"Error al procesar fila {row[0]}: {e}")
                    continue
            
            conn.close()
            
            logger.info(f"Obtenidos {len(content_list)} elementos con embeddings")
            return content_list
            
        except Exception as e:
            logger.error(f"Error al obtener contenido: {e}")
            return []
    
    def index_content(self, content_list: List[Dict[str, Any]], batch_size: int = 100):
        """Indexa contenido en MeiliSearch."""
        if not content_list:
            logger.info("No hay contenido para indexar")
            return
        
        index = self.setup_index()
        
        try:
            # Indexar en lotes
            total_indexed = 0
            
            for i in range(0, len(content_list), batch_size):
                batch = content_list[i:i + batch_size]
                
                # Indexar lote
                task = index.add_documents(batch)
                logger.info(f"Lote indexado. Task ID: {task.task_uid}")
                
                # Marcar como indexado en SQLite
                self._mark_as_indexed([item['id'] for item in batch])
                
                total_indexed += len(batch)
                logger.info(f"Indexados {total_indexed}/{len(content_list)} elementos")
            
            logger.info("Indexación completada")
            
        except Exception as e:
            logger.error(f"Error durante la indexación: {e}")
            raise
    
    def _mark_as_indexed(self, content_ids: List[int]):
        """Marca contenido como indexado en la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar tabla de contenido
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%contenido%'
            """)
            tables = cursor.fetchall()
            
            if not tables:
                return
            
            content_table = tables[0][0]
            
            # Verificar si existe la columna indexado_meilisearch
            cursor.execute(f"PRAGMA table_info({content_table})")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'indexado_meilisearch' not in columns:
                # Agregar columna si no existe
                cursor.execute(f"ALTER TABLE {content_table} ADD COLUMN indexado_meilisearch INTEGER DEFAULT 0")
            
            # Marcar como indexado
            placeholders = ','.join(['?' for _ in content_ids])
            update_query = f"""
                UPDATE {content_table} 
                SET indexado_meilisearch = 1 
                WHERE id IN ({placeholders})
            """
            
            cursor.execute(update_query, content_ids)
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"Error al marcar como indexado: {e}")
    
    def process_all(self, only_new: bool = False, recreate_index: bool = False):
        """Procesa todo el contenido para indexación."""
        logger.info("Iniciando indexación en MeiliSearch")
        
        # Configurar índice
        if recreate_index:
            self.setup_index(recreate=True)
        
        # Obtener contenido
        content_list = self.get_content_with_embeddings(only_new=only_new)
        
        if not content_list:
            logger.info("No hay contenido para indexar")
            return
        
        # Indexar contenido
        self.index_content(content_list)
        
        logger.info("Indexación completada")

def main():
    parser = argparse.ArgumentParser(description="Indexar contenido en MeiliSearch")
    parser.add_argument("--url", default="http://localhost:7700",
                       help="URL de MeiliSearch (default: http://localhost:7700)")
    parser.add_argument("--api-key", 
                       help="API key de MeiliSearch")
    parser.add_argument("--indexar-nuevos", action="store_true",
                       help="Indexar solo contenido nuevo")
    parser.add_argument("--recrear-indice", action="store_true",
                       help="Recrear el índice desde cero")
    parser.add_argument("--batch-size", type=int, default=100,
                       help="Tamaño del lote para indexación (default: 100)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Activar logging detallado")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        indexer = MeiliSearchIndexer(meilisearch_url=args.url, api_key=args.api_key)
        indexer.process_all(only_new=args.indexar_nuevos, recreate_index=args.recrear_indice)
    except Exception as e:
        logger.error(f"Error en la indexación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()