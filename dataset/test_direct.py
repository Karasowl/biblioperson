#!/usr/bin/env python3
"""Script para probar directamente el DeduplicationManager."""

from processing.dedup_config import DedupConfigManager
from processing.deduplication import DeduplicationManager

def main():
    # Usar la configuración
    config = DedupConfigManager()
    db_path = config.get_database_path()
    print(f"Ruta de la base de datos: {db_path}")
    
    # Crear manager
    manager = DeduplicationManager(str(db_path))
    
    # Obtener estadísticas
    stats = manager.get_stats()
    print(f"Estadísticas: {stats}")
    
    # Listar documentos
    docs = manager.list_documents()
    print(f"Documentos encontrados: {len(docs)}")
    
    for i, doc in enumerate(docs):
        print(f"  {i+1}. {doc['title']} - {doc['hash'][:12]}...")

if __name__ == "__main__":
    main() 