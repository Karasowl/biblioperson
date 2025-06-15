#!/usr/bin/env python3
"""Script para agregar datos de prueba a la base de datos de deduplicación."""

from processing.deduplication import DeduplicationManager
from processing.dedup_config import DedupConfigManager
import hashlib
from datetime import datetime

def main():
    config = DedupConfigManager()
    db_path = config.get_database_path()
    manager = DeduplicationManager(str(db_path))

    # Agregar documentos de prueba
    test_docs = [
        {'title': 'El Quijote - Capítulo 1', 'file_path': '/docs/quijote_cap1.txt', 'size': 15420},
        {'title': 'Cien Años de Soledad', 'file_path': '/docs/cien_anos.pdf', 'size': 89234},
        {'title': 'La Casa de Bernarda Alba', 'file_path': '/docs/bernarda_alba.docx', 'size': 34567},
        {'title': 'Romancero Gitano', 'file_path': '/docs/romancero.txt', 'size': 12890}
    ]

    for i, doc in enumerate(test_docs):
        content = f'Contenido de prueba {i}: {doc["title"]}'
        hash_val = hashlib.sha256(content.encode()).hexdigest()
        success = manager.register_document(hash_val, doc['file_path'], doc['title'])
        if success:
            print(f'Agregado: {doc["title"]}')
        else:
            print(f'Ya existe: {doc["title"]}')

    print('Documentos de prueba agregados exitosamente')

if __name__ == "__main__":
    main() 