#!/usr/bin/env python3
"""Script para probar la lógica exacta del CLI."""

import sys
from pathlib import Path

# Usar la misma lógica de importación que el CLI
try:
    from processing.deduplication import get_dedup_manager
    from processing.dedup_config import get_config_manager
    print("Importación relativa exitosa")
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(Path(__file__).parent))
    from deduplication import get_dedup_manager
    from dedup_config import get_config_manager
    print("Importación fallback exitosa")

def main():
    print("Probando la lógica exacta del CLI...")
    
    # Obtener el manager exactamente como lo hace el CLI
    dedup_manager = get_dedup_manager()
    print(f"Manager obtenido con ruta: {dedup_manager.db_path}")
    
    # Listar documentos exactamente como lo hace el CLI
    documents = dedup_manager.list_documents(
        search=None,
        before=None,
        after=None
    )
    
    print(f"Documentos encontrados: {len(documents)}")
    for doc in documents:
        print(f"  - {doc['title']} ({doc['hash'][:12]}...)")

if __name__ == "__main__":
    main() 