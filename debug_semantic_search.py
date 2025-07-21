#!/usr/bin/env python3
import sqlite3
import os
import requests
import json

# Base de datos real
appdata_db = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Biblioperson', 'library.db')

print("🔍 DEBUGGING BÚSQUEDA SEMÁNTICA")
print("=" * 50)

# 1. Verificar embeddings
conn = sqlite3.connect(appdata_db)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM embeddings")
emb_count = cursor.fetchone()[0]
print(f"📊 Embeddings generados: {emb_count}")

# 2. Verificar documentos de Platón
cursor.execute("SELECT id, title, author FROM documents WHERE title LIKE '%Platon%' OR title LIKE '%Republica%' OR author LIKE '%Plat%'")
platon_docs = cursor.fetchall()
print(f"\n📚 Documentos de Platón encontrados: {len(platon_docs)}")
for doc_id, title, author in platon_docs:
    print(f"  - ID: {doc_id}, Título: {title}, Autor: {author}")

# 3. Verificar embeddings de Platón
if platon_docs:
    platon_ids = [str(doc[0]) for doc in platon_docs]
    placeholders = ','.join(['?' for _ in platon_ids])
    cursor.execute(f"SELECT document_id, model FROM embeddings WHERE document_id IN ({placeholders})", platon_ids)
    platon_embeddings = cursor.fetchall()
    print(f"\n🧠 Embeddings de Platón: {len(platon_embeddings)}")
    for doc_id, model in platon_embeddings:
        print(f"  - Doc ID: {doc_id}, Modelo: {model}")

conn.close()

# 4. Probar endpoint semántico directamente
print(f"\n🔍 Probando endpoint semántico...")
try:
    response = requests.post('http://localhost:5000/api/search/semantic', 
                           json={'query': 'sociedad justa', 'limit': 5}, 
                           timeout=10)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Resultados: {len(data.get('results', []))}")
        for i, result in enumerate(data.get('results', [])[:3]):
            print(f"  {i+1}. {result.get('document_title', 'Sin título')} - Score: {result.get('similarity', 0):.3f}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error en request: {e}")

# 5. Verificar si el backend está usando la BD correcta
print(f"\n📍 BD que debería usar el backend: {appdata_db}")
print("💡 Si no encuentra Platón, el backend puede estar usando otra BD.")

print(f"\n🎯 DIAGNÓSTICO:")
print(f"- Embeddings: {'✅' if emb_count > 0 else '❌'}")
print(f"- Platón en BD: {'✅' if platon_docs else '❌'}")
print(f"- Embeddings de Platón: {'✅' if len(platon_embeddings) > 0 else '❌'}") 