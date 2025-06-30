#!/usr/bin/env python3
import sqlite3
import os

# Verificar base de datos del dataset
db_path = 'dataset/data/biblioperson.db'
print(f"BD dataset existe: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tablas en dataset: {tables}")
    
    if 'embeddings' in tables:
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        print(f"Embeddings en dataset: {count}")
        
        cursor.execute("SELECT model FROM embeddings LIMIT 1")
        model = cursor.fetchone()
        print(f"Modelo usado: {model[0] if model else 'Desconocido'}")
    else:
        print("No hay tabla embeddings en dataset")
    
    conn.close()

# Verificar base de datos principal
main_db = 'data.ms/documents.db'
print(f"\nBD principal existe: {os.path.exists(main_db)}")

if os.path.exists(main_db):
    conn = sqlite3.connect(main_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tablas en principal: {tables}")
    
    if 'embeddings' in tables:
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        print(f"Embeddings en principal: {count}")
    else:
        print("No hay tabla embeddings en principal")
    
    conn.close() 