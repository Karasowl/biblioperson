"""
Script de inicialización de base de datos para Biblioperson
Crea las tablas con el esquema v2
"""

import sys
import sqlite3
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database(db_path: str = "data/biblioperson.db", force: bool = False):
    """
    Inicializa la base de datos con el esquema v2
    
    Args:
        db_path: Ruta a la base de datos
        force: Si True, elimina la BD existente
    """
    db_path = Path(db_path)
    
    # Crear directorio si no existe
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Si existe y force=True, eliminar
    if db_path.exists() and force:
        logger.warning(f"Eliminando base de datos existente: {db_path}")
        db_path.unlink()
    
    # Leer esquema
    schema_path = Path("database/schema_v2.sql")
    if not schema_path.exists():
        logger.error(f"No se encontró el archivo de esquema: {schema_path}")
        return False
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Crear base de datos
    try:
        conn = sqlite3.connect(str(db_path))
        
        # Ejecutar esquema
        conn.executescript(schema_sql)
        
        # Verificar tablas creadas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Base de datos creada con {len(tables)} tablas:")
        for table in tables:
            logger.info(f"  - {table}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Base de datos inicializada correctamente en: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando base de datos: {e}")
        return False


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inicializar base de datos de Biblioperson")
    parser.add_argument("--db", default="data/biblioperson.db", help="Ruta a la base de datos")
    parser.add_argument("--force", action="store_true", help="Eliminar BD existente")
    
    args = parser.parse_args()
    
    success = init_database(args.db, args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 