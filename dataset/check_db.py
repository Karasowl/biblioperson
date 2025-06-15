#!/usr/bin/env python3
"""Script para verificar la base de datos de deduplicación."""

import sqlite3

def main():
    db_path = 'data/deduplication.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tablas en la base de datos: {tables}")
        
        # Contar documentos
        cursor.execute("SELECT COUNT(*) FROM docs")
        count = cursor.fetchone()[0]
        print(f"Total de documentos: {count}")
        
        # Mostrar algunos documentos
        if count > 0:
            cursor.execute("SELECT hash, title, file_path, first_seen FROM docs LIMIT 5")
            docs = cursor.fetchall()
            print("\nPrimeros documentos:")
            for doc in docs:
                print(f"  Hash: {doc[0][:12]}... | Título: {doc[1]} | Ruta: {doc[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 