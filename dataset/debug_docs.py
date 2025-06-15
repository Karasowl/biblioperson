#!/usr/bin/env python3
"""Script para debuggear la estructura de documentos."""

from processing.deduplication import get_dedup_manager

def main():
    manager = get_dedup_manager()
    docs = manager.list_documents()
    
    print(f"Total documentos encontrados: {len(docs)}")
    
    if docs:
        print('\nEstructura del primer documento:')
        for key, value in docs[0].items():
            print(f'  {key}: {value} (tipo: {type(value).__name__})')
        
        print('\nTodos los documentos:')
        for i, doc in enumerate(docs):
            print(f"  {i+1}. {doc.get('title', 'Sin título')} - {doc.get('hash', 'Sin hash')[:12]}...")
    else:
        print('No hay documentos')

if __name__ == "__main__":
    main() 