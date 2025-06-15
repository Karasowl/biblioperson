#!/usr/bin/env python3
"""Script para debuggear la lógica de la GUI."""

from processing.deduplication import get_dedup_manager
from datetime import datetime
from PySide6.QtCore import QDate

def main():
    manager = get_dedup_manager()
    
    print("=== Probando sin filtros ===")
    docs = manager.list_documents()
    print(f"Sin filtros: {len(docs)} documentos")
    
    print("\n=== Probando con filtros de fecha ===")
    # Simular los filtros de fecha de la GUI
    date_from = QDate.currentDate().addDays(-30).toString("yyyy-MM-dd")
    date_to = QDate.currentDate().toString("yyyy-MM-dd")
    
    print(f"Filtro desde: {date_from}")
    print(f"Filtro hasta: {date_to}")
    
    # Probar con filtros como en la GUI
    docs_filtered = manager.list_documents(
        search=None,
        after=date_from,
        before=date_to,
        limit=100
    )
    print(f"Con filtros de fecha: {len(docs_filtered)} documentos")
    
    print("\n=== Probando filtros individuales ===")
    
    # Probar solo after
    docs_after = manager.list_documents(after=date_from)
    print(f"Solo after {date_from}: {len(docs_after)} documentos")
    
    # Probar solo before
    docs_before = manager.list_documents(before=date_to)
    print(f"Solo before {date_to}: {len(docs_before)} documentos")
    
    print("\n=== Fechas de los documentos ===")
    for doc in docs:
        print(f"  {doc['title']}: {doc['first_seen']}")

if __name__ == "__main__":
    main() 