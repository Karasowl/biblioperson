#!/usr/bin/env python3
"""
Script principal de importación para Biblioperson.

Este script integra todo el flujo de procesamiento:
1. Procesamiento con Task Master para generar NDJSON
2. Generación de embeddings para búsqueda semántica
3. Indexación en Meilisearch
4. Almacenamiento en SQLite local
5. Sincronización de metadatos con Supabase (opcional)

Uso:
    python scripts/process_and_import.py <archivo_o_directorio> [opciones]

Ejemplos:
    # Procesar un archivo PDF
    python scripts/process_and_import.py ~/documentos/libro.pdf
    
    # Procesar un directorio completo
    python scripts/process_and_import.py ~/biblioteca --recursive
    
    # Procesar con perfil específico
    python scripts/process_and_import.py ~/libro.pdf --profile verso
    
    # Procesar y generar embeddings
    python scripts/process_and_import.py ~/libro.pdf --embeddings
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
from datetime import datetime
import hashlib
import subprocess

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar módulos del dataset
from dataset.processing.profile_manager import ProfileManager
from dataset.scripts.process_file import core_process

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BibliopersonImporter:
    """Clase principal para importar documentos a Biblioperson."""
    
    def __init__(self, db_path: str = "data.ms/documents.db"):
        """
        Inicializa el importador.
        
        Args:
            db_path: Ruta a la base de datos SQLite local
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar ProfileManager
        self.profile_manager = ProfileManager()
        
        # Crear conexión a la base de datos
        self._init_database()
        
        # Configuración de Meilisearch
        self.meilisearch_url = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        self.meilisearch_key = os.getenv("MEILISEARCH_MASTER_KEY", "")
        
    def _init_database(self):
        """Inicializa la base de datos SQLite con el esquema necesario."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de documentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT,
                language TEXT,
                file_path TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                total_segments INTEGER DEFAULT 0,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON
            )
        """)
        
        # Crear índices para documents
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON documents(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_author ON documents(author)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_at ON documents(processed_at)")
        
        # Tabla de segmentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                segment_order INTEGER NOT NULL,
                segment_type TEXT,
                text TEXT NOT NULL,
                text_length INTEGER,
                original_page INTEGER,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Crear índices para segments
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_id ON segments(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_segment_order ON segments(segment_order)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_segment_type ON segments(segment_type)")
        
        # Tabla de embeddings (opcional)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                segment_id TEXT PRIMARY KEY,
                embedding BLOB,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (segment_id) REFERENCES segments(id)
            )
        """)
        
        # Crear índice para embeddings
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_created_at ON embeddings(created_at)")
        
        # Tabla de trabajos de procesamiento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                segments_processed INTEGER DEFAULT 0,
                profile_used TEXT
            )
        """)
        
        # Crear índices para processing_jobs
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON processing_jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_started_at ON processing_jobs(started_at)")
        
        conn.commit()
        conn.close()
        
    def process_file(self, file_path: Path, profile: str = "automático", 
                    generate_embeddings: bool = False) -> Tuple[bool, str]:
        """
        Procesa un archivo individual.
        
        Args:
            file_path: Ruta al archivo
            profile: Perfil de procesamiento a usar
            generate_embeddings: Si generar embeddings para búsqueda semántica
            
        Returns:
            Tuple de (éxito, mensaje)
        """
        logger.info(f"Procesando archivo: {file_path}")
        
        # Verificar si el archivo ya fue procesado
        file_hash = self._calculate_file_hash(file_path)
        if self._is_file_processed(file_hash):
            logger.warning(f"Archivo ya procesado: {file_path}")
            return False, "Archivo ya procesado anteriormente"
        
        # Crear trabajo de procesamiento
        job_id = self._create_processing_job(file_path, profile)
        
        try:
            # 1. Procesar con Task Master
            output_path = Path("temp") / f"{file_path.stem}.ndjson"
            output_path.parent.mkdir(exist_ok=True)
            
            # Crear argumentos simulados
            args = argparse.Namespace()
            args.input_path = str(file_path)
            args.profile = profile
            args.verbose = True
            args.encoding = "utf-8"
            args.force_type = None
            args.confidence_threshold = 0.5
            args.language_override = None
            args.author_override = None
            args.json_filter_config = None
            
            # Procesar archivo
            result_code, message, document_metadata, segments, segmenter_stats = core_process(
                manager=self.profile_manager,
                input_path=file_path,
                profile_name_override=None if profile == "automático" else profile,
                output_spec=str(output_path),
                cli_args=args,
                output_format="ndjson"
            )
            
            if not result_code.startswith('SUCCESS'):
                raise Exception(f"Error en procesamiento: {message}")
            
            # 2. Importar a SQLite
            document_id = self._import_to_sqlite(
                file_path, file_hash, output_path, 
                document_metadata, segments
            )
            
            # 3. Generar embeddings (opcional)
            if generate_embeddings and segments:
                self._generate_embeddings(document_id, segments)
            
            # 4. Indexar en Meilisearch
            if segments:
                self._index_in_meilisearch(document_id, document_metadata, segments)
            
            # 5. Sincronizar metadatos con Supabase (opcional)
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
                self._sync_to_supabase(document_id, document_metadata)
            
            # Actualizar trabajo como completado
            self._update_processing_job(job_id, "completed", len(segments))
            
            # Limpiar archivo temporal
            if output_path.exists():
                output_path.unlink()
            
            logger.info(f"✅ Archivo procesado exitosamente: {len(segments)} segmentos")
            return True, f"Procesado exitosamente: {len(segments)} segmentos"
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            self._update_processing_job(job_id, "failed", error_message=str(e))
            return False, f"Error: {str(e)}"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula el hash SHA-256 de un archivo."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _is_file_processed(self, file_hash: str) -> bool:
        """Verifica si un archivo ya fue procesado."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def _create_processing_job(self, file_path: Path, profile: str) -> int:
        """Crea un registro de trabajo de procesamiento."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO processing_jobs (file_path, profile_used, started_at, status)
            VALUES (?, ?, datetime('now'), 'processing')
        """, (str(file_path), profile))
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
    
    def _update_processing_job(self, job_id: int, status: str, 
                             segments_processed: int = 0, error_message: str = None):
        """Actualiza el estado de un trabajo de procesamiento."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == "completed":
            cursor.execute("""
                UPDATE processing_jobs 
                SET status = ?, completed_at = datetime('now'), segments_processed = ?
                WHERE id = ?
            """, (status, segments_processed, job_id))
        else:
            cursor.execute("""
                UPDATE processing_jobs 
                SET status = ?, completed_at = datetime('now'), error_message = ?
                WHERE id = ?
            """, (status, error_message, job_id))
        
        conn.commit()
        conn.close()
    
    def _import_to_sqlite(self, file_path: Path, file_hash: str, 
                         ndjson_path: Path, document_metadata: Dict,
                         segments: List[Any]) -> str:
        """Importa los segmentos procesados a SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear documento
        document_id = document_metadata.get('document_id', str(file_hash))
        cursor.execute("""
            INSERT INTO documents (id, title, author, language, file_path, 
                                 file_hash, total_segments, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            document_metadata.get('document_title', file_path.stem),
            document_metadata.get('author'),
            document_metadata.get('language', 'unknown'),
            str(file_path),
            file_hash,
            len(segments),
            json.dumps(document_metadata)
        ))
        
        # Insertar segmentos
        for segment in segments:
            # Extraer datos del segmento
            if hasattr(segment, '__dict__'):
                seg_data = segment.__dict__
            else:
                seg_data = segment
            
            # Extraer página original de metadata
            original_page = None
            if isinstance(seg_data.get('additional_metadata'), dict):
                original_page = seg_data['additional_metadata'].get('originalPage')
            
            cursor.execute("""
                INSERT INTO segments (id, document_id, segment_order, segment_type,
                                    text, text_length, original_page, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                seg_data.get('segment_id'),
                document_id,
                seg_data.get('segment_order', 0),
                seg_data.get('segment_type', 'text'),
                seg_data.get('text', ''),
                seg_data.get('text_length', 0),
                original_page,
                json.dumps(seg_data.get('additional_metadata', {}))
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Importados {len(segments)} segmentos a SQLite")
        return document_id
    
    def _generate_embeddings(self, document_id: str, segments: List[Any]):
        """Genera embeddings para los segmentos."""
        try:
            # Importar el generador de embeddings
            from backend.generate_embeddings import EmbeddingGenerator
            
            # Configurar el generador (usar sentence-transformers por defecto)
            generator = EmbeddingGenerator(
                provider="sentence-transformers",
                model_name="hiiamsid/sentence_similarity_spanish_es"
            )
            
            # Procesar el documento
            processed, skipped = generator.process_document(document_id)
            
            if processed > 0:
                logger.info(f"✅ Generados {processed} embeddings para el documento")
            else:
                logger.info("ℹ️ No se generaron embeddings nuevos (ya existían)")
                
        except ImportError:
            logger.warning("⚠️ No se pudo importar sentence-transformers. Instala con: pip install sentence-transformers")
        except Exception as e:
            logger.warning(f"⚠️ Error generando embeddings: {str(e)}")
            # No fallar el procesamiento por errores de embeddings
    
    def _index_in_meilisearch(self, document_id: str, document_metadata: Dict,
                             segments: List[Any]):
        """Indexa los segmentos en Meilisearch."""
        try:
            import requests
            
            # Asegurar que Meilisearch esté corriendo
            from dataset.processing.meilisearch_manager import ensure_meilisearch_running
            if not ensure_meilisearch_running():
                logger.warning("⚠️ No se pudo iniciar Meilisearch, saltando indexación")
                return
            
            # Preparar documentos para Meilisearch
            docs = []
            for segment in segments:
                if hasattr(segment, '__dict__'):
                    seg_data = segment.__dict__
                else:
                    seg_data = segment
                
                # Extraer página original
                original_page = None
                if isinstance(seg_data.get('additional_metadata'), dict):
                    original_page = seg_data['additional_metadata'].get('originalPage')
                
                doc = {
                    "id": seg_data.get('segment_id'),
                    "document_id": document_id,
                    "document_title": document_metadata.get('document_title'),
                    "document_author": document_metadata.get('author'),
                    "text": seg_data.get('text', ''),
                    "segment_type": seg_data.get('segment_type', 'text'),
                    "segment_order": seg_data.get('segment_order', 0),
                    "original_page": original_page,
                    "language": seg_data.get('document_language', 'unknown')
                }
                docs.append(doc)
            
            # Enviar a Meilisearch
            headers = {}
            if self.meilisearch_key:
                headers['Authorization'] = f'Bearer {self.meilisearch_key}'
            
            response = requests.post(
                f"{self.meilisearch_url}/indexes/biblioperson/documents",
                json=docs,
                headers=headers
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Indexados {len(docs)} documentos en Meilisearch")
            else:
                logger.warning(f"⚠️ Error indexando en Meilisearch: {response.text}")
                
        except Exception as e:
            logger.warning(f"⚠️ No se pudo indexar en Meilisearch: {str(e)}")
    
    def _sync_to_supabase(self, document_id: str, document_metadata: Dict):
        """Sincroniza metadatos con Supabase (placeholder)."""
        logger.info("🔄 Sincronización con Supabase no implementada aún")
        # TODO: Implementar sincronización con Supabase
    
    def process_directory(self, directory: Path, recursive: bool = False,
                         profile: str = "automático", 
                         generate_embeddings: bool = False) -> Dict[str, Any]:
        """
        Procesa todos los archivos en un directorio.
        
        Args:
            directory: Directorio a procesar
            recursive: Si procesar subdirectorios
            profile: Perfil de procesamiento
            generate_embeddings: Si generar embeddings
            
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        stats = {
            "total_files": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        # Obtener archivos
        pattern = "**/*" if recursive else "*"
        files = [f for f in directory.glob(pattern) if f.is_file()]
        stats["total_files"] = len(files)
        
        logger.info(f"Encontrados {len(files)} archivos para procesar")
        
        for file_path in files:
            try:
                success, message = self.process_file(
                    file_path, profile, generate_embeddings
                )
                
                if success:
                    stats["processed"] += 1
                elif "ya procesado" in message:
                    stats["skipped"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"].append(f"{file_path}: {message}")
                    
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{file_path}: {str(e)}")
                logger.error(f"Error procesando {file_path}: {str(e)}")
        
        return stats


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Importar documentos a Biblioperson",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "input",
        type=str,
        help="Archivo o directorio a procesar"
    )
    
    parser.add_argument(
        "--profile", "-p",
        type=str,
        default="automático",
        help="Perfil de procesamiento (default: automático)"
    )
    
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Procesar subdirectorios recursivamente"
    )
    
    parser.add_argument(
        "--embeddings", "-e",
        action="store_true",
        help="Generar embeddings para búsqueda semántica"
    )
    
    parser.add_argument(
        "--db-path",
        type=str,
        default="data.ms/documents.db",
        help="Ruta a la base de datos SQLite (default: data.ms/documents.db)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar información detallada"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear importador
    importer = BibliopersonImporter(args.db_path)
    
    # Procesar entrada
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"No existe: {input_path}")
        sys.exit(1)
    
    if input_path.is_file():
        # Procesar archivo individual
        success, message = importer.process_file(
            input_path, args.profile, args.embeddings
        )
        
        if success:
            logger.info(f"✅ {message}")
        else:
            logger.error(f"❌ {message}")
            sys.exit(1)
            
    elif input_path.is_dir():
        # Procesar directorio
        stats = importer.process_directory(
            input_path, args.recursive, args.profile, args.embeddings
        )
        
        # Mostrar resumen
        logger.info("\n=== RESUMEN DE PROCESAMIENTO ===")
        logger.info(f"Total archivos: {stats['total_files']}")
        logger.info(f"Procesados: {stats['processed']}")
        logger.info(f"Omitidos (ya procesados): {stats['skipped']}")
        logger.info(f"Fallidos: {stats['failed']}")
        
        if stats['errors']:
            logger.error("\nErrores encontrados:")
            for error in stats['errors']:
                logger.error(f"  - {error}")
        
        if stats['failed'] > 0:
            sys.exit(1)
    else:
        logger.error(f"Tipo de entrada no válido: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main() 