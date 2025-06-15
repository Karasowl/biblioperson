"""
Módulo de deduplicación para el sistema de procesamiento de documentos.
Implementa hash SHA-256 y gestión de duplicados usando SQLite.
"""

import hashlib
import sqlite3
import pathlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Ruta por defecto para la base de datos de deduplicación
DEFAULT_DEDUP_DB_PATH = pathlib.Path("dataset/.cache/dedup_registry.sqlite")

class DeduplicationManager:
    """Gestor de deduplicación de documentos basado en hash SHA-256."""
    
    def __init__(self, db_path: Optional[str | pathlib.Path] = None):
        """
        Inicializa el gestor de deduplicación.
        
        Args:
            db_path: Ruta a la base de datos SQLite. Si es None, usa la ruta por defecto.
        """
        if db_path is None:
            self.db_path = DEFAULT_DEDUP_DB_PATH
        else:
            self.db_path = pathlib.Path(db_path)
        self._ensure_db_exists()
    
    def _ensure_db_exists(self) -> None:
        """Crea la base de datos y tabla si no existen."""
        # Crear directorio padre si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS docs (
                    hash        TEXT PRIMARY KEY,
                    file_path   TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    first_seen  TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_first_seen 
                ON docs(first_seen)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_title 
                ON docs(title)
            """)
            conn.commit()
    
    def compute_sha256(self, file_path: str | pathlib.Path) -> str:
        """
        Calcula el hash SHA-256 de un archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Hash SHA-256 en formato hexadecimal
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            IOError: Si hay problemas leyendo el archivo
        """
        file_path = pathlib.Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")
        
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Leer en chunks de 8192 bytes para eficiencia de memoria
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
        except IOError as e:
            logger.error(f"Error leyendo archivo {file_path}: {e}")
            raise
        
        return hash_sha256.hexdigest()
    
    def is_duplicate(self, file_hash: str) -> bool:
        """
        Verifica si un hash ya existe en la base de datos.
        
        Args:
            file_hash: Hash SHA-256 del archivo
            
        Returns:
            True si el hash ya existe, False en caso contrario
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM docs WHERE hash = ? LIMIT 1",
                (file_hash,)
            )
            return cursor.fetchone() is not None
    
    def register_document(self, file_hash: str, file_path: str | pathlib.Path, title: Optional[str] = None) -> bool:
        """
        Registra un documento en la base de datos de deduplicación.
        
        Args:
            file_hash: Hash SHA-256 del archivo
            file_path: Ruta al archivo
            title: Título del documento (opcional, se deriva del nombre del archivo si no se proporciona)
            
        Returns:
            True si se registró exitosamente, False si ya existía
        """
        file_path = pathlib.Path(file_path)
        if title is None:
            title = file_path.stem  # Nombre sin extensión
        first_seen = datetime.utcnow().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO docs (hash, file_path, title, first_seen) VALUES (?, ?, ?, ?)",
                    (file_hash, str(file_path), title, first_seen)
                )
                conn.commit()
                logger.info(f"Documento registrado: {title} ({file_hash[:8]}...)")
                return True
        except sqlite3.IntegrityError:
            # El hash ya existe
            logger.debug(f"Hash ya existe en la base de datos: {file_hash[:8]}...")
            return False
    
    def check_and_register(self, file_path: str | pathlib.Path, title: Optional[str] = None) -> tuple[str, bool]:
        """
        Verifica si un archivo es duplicado y lo registra si no lo es.
        
        Args:
            file_path: Ruta al archivo
            title: Título opcional del documento
            
        Returns:
            tuple[str, bool]: (hash, is_new)
            - hash: Hash SHA-256 del archivo
            - is_new: True si es un archivo nuevo, False si es duplicado
        """
        file_hash = self.compute_sha256(file_path)
        
        if self.is_duplicate(file_hash):
            logger.warning(f"Documento duplicado detectado: {pathlib.Path(file_path).name}")
            return file_hash, False
        
        self.register_document(file_hash, file_path, title)
        return file_hash, True
    
    def get_duplicate_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información sobre un documento duplicado.
        
        Args:
            file_hash: Hash SHA-256 del archivo
            
        Returns:
            Diccionario con información del documento o None si no existe
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM docs WHERE hash = ?",
                (file_hash,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def list_documents(self, 
                      search: Optional[str] = None,
                      before: Optional[str] = None,
                      after: Optional[str] = None,
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Lista documentos en la base de datos con filtros opcionales.
        
        Args:
            search: Texto a buscar en título o ruta
            before: Fecha límite superior (ISO format)
            after: Fecha límite inferior (ISO format)
            limit: Número máximo de resultados
            
        Returns:
            Lista de diccionarios con información de documentos
        """
        query = "SELECT * FROM docs WHERE 1=1"
        params = []
        
        if search:
            query += " AND (title LIKE ? OR file_path LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        if before:
            query += " AND first_seen < ?"
            params.append(before)
        
        if after:
            query += " AND first_seen > ?"
            params.append(after)
        
        query += " ORDER BY first_seen DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def remove_document(self, file_hash: str) -> bool:
        """
        Elimina un documento de la base de datos.
        
        Args:
            file_hash: Hash SHA-256 del documento
            
        Returns:
            True si se eliminó, False si no existía
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM docs WHERE hash = ?", (file_hash,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Documento eliminado del registro: {file_hash[:8]}...")
                return True
            return False
    
    def remove_by_hash(self, file_hash: str) -> bool:
        """
        Alias para remove_document para compatibilidad con CLI.
        
        Args:
            file_hash: Hash SHA-256 del documento
            
        Returns:
            True si se eliminó, False si no existía
        """
        return self.remove_document(file_hash)
    
    def remove_by_path(self, file_path: str) -> bool:
        """
        Elimina un documento por su ruta.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            True si se eliminó, False si no existía
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM docs WHERE file_path = ?", (str(file_path),))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Documento eliminado del registro: {file_path}")
                return True
            return False
    
    def clear_all(self) -> int:
        """
        Elimina todos los documentos de la base de datos.
        
        Returns:
            Número de documentos eliminados
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM docs")
            conn.commit()
            
            count = cursor.rowcount
            logger.info(f"Registro de deduplicación limpiado: {count} documentos eliminados")
            return count
    
    def prune_before(self, before_date: str) -> int:
        """
        Elimina documentos registrados antes de una fecha específica.
        
        Args:
            before_date: Fecha límite en formato ISO
            
        Returns:
            Número de documentos eliminados
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM docs WHERE first_seen < ?",
                (before_date,)
            )
            conn.commit()
            
            count = cursor.rowcount
            logger.info(f"Documentos eliminados antes de {before_date}: {count}")
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos.
        
        Returns:
            Diccionario con estadísticas
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Contar total de documentos
            total_cursor = conn.execute("SELECT COUNT(*) as total FROM docs")
            total = total_cursor.fetchone()["total"]
            
            # Obtener fecha más antigua y más reciente
            date_cursor = conn.execute("""
                SELECT 
                    MIN(first_seen) as oldest,
                    MAX(first_seen) as newest
                FROM docs
            """)
            dates = date_cursor.fetchone()
            
            return {
                "total_documents": total,
                "oldest_entry": dates["oldest"],
                "newest_entry": dates["newest"],
                "database_path": str(self.db_path)
            }


# Instancia global para uso conveniente
_global_dedup_manager = None

def get_dedup_manager(db_path: Optional[str | pathlib.Path] = None) -> DeduplicationManager:
    """
    Obtiene la instancia global del gestor de deduplicación.
    
    Args:
        db_path: Ruta personalizada para la base de datos (solo en primera llamada)
        
    Returns:
        Instancia del DeduplicationManager
    """
    global _global_dedup_manager
    
    if _global_dedup_manager is None:
        # Si no se especifica db_path, usar la configuración
        if db_path is None:
            try:
                from .dedup_config import DedupConfigManager
                config_manager = DedupConfigManager()
                db_path = config_manager.get_database_path()
            except ImportError:
                # Fallback a la ruta por defecto si no hay configuración
                pass
        
        _global_dedup_manager = DeduplicationManager(db_path)
    
    return _global_dedup_manager 