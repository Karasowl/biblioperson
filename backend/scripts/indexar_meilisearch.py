import sqlite3
import meilisearch

# Configuración
DB_PATH = '../../backend/data/biblioteca.db'  # Ajusta si es necesario
MEILI_URL = 'http://127.0.0.1:7700'
MEILI_INDEX = 'contenidos'
MEILI_KEY = None  # Si usas master key, ponla aquí como string

# Conexión a la base de datos
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT id, contenido_texto, fecha_creacion, autor FROM contenidos")
docs = [
    {
        "id": row[0],
        "contenido_texto": row[1],
        "fecha_creacion": row[2],
        "autor": row[3]
    }
    for row in cursor.fetchall()
]

# Conexión a Meilisearch
client = meilisearch.Client(MEILI_URL, MEILI_KEY)
index = client.index(MEILI_INDEX)

# Crear el índice si no existe
try:
    client.create_index(MEILI_INDEX, {'primaryKey': 'id'})
except Exception:
    pass  # Ya existe

# Indexar documentos en lotes
BATCH_SIZE = 1000  # Puedes ajustar este valor

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

print(f"Indexando {len(docs)} documentos en Meilisearch en lotes de {BATCH_SIZE}...")
for i, doc_batch in enumerate(batch(docs, BATCH_SIZE), 1):
    print(f"Lote {i}: indexando {len(doc_batch)} documentos...")
    res = index.add_documents(doc_batch)
    index.wait_for_task(res.task_uid, 60000)  # Espera hasta 60 segundos por lote
print("¡Indexación completada!")

def indexar_nuevos_en_meilisearch():
    """
    Indexa en Meilisearch solo los contenidos que no están en el índice.
    Requiere que Meilisearch esté corriendo en http://127.0.0.1:7700.
    """
    DB_PATH = '../../backend/data/biblioteca.db'
    MEILI_URL = 'http://127.0.0.1:7700'
    MEILI_INDEX = 'contenidos'
    MEILI_KEY = None  # Si usas master key, ponla aquí

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    client = meilisearch.Client(MEILI_URL, MEILI_KEY)
    index = client.index(MEILI_INDEX)

    # Obtener IDs ya indexados
    try:
        existing_ids = set()
        offset = 0
        limit = 10000
        while True:
            docs = index.get_documents({'fields': ['id'], 'limit': limit, 'offset': offset})
            if not docs:
                break
            for doc in docs:
                existing_ids.add(doc['id'])
            if len(docs) < limit:
                break
            offset += limit
    except Exception:
        existing_ids = set()

    # Buscar en la base de datos los que no están indexados
    cursor.execute("SELECT id, contenido_texto, fecha_creacion, autor FROM contenidos")
    nuevos = []
    for row in cursor.fetchall():
        if row['id'] not in existing_ids:
            nuevos.append({
                'id': row['id'],
                'contenido_texto': row['contenido_texto'],
                'fecha_creacion': row['fecha_creacion'],
                'autor': row['autor']
            })
    if not nuevos:
        print("No hay nuevos contenidos para indexar en Meilisearch.")
        return
    print(f"Indexando {len(nuevos)} nuevos documentos en Meilisearch...")
    BATCH_SIZE = 1000
    def batch(iterable, n=1):
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]
    for i, doc_batch in enumerate(batch(nuevos, BATCH_SIZE), 1):
        print(f"Lote {i}: indexando {len(doc_batch)} documentos...")
        res = index.add_documents(doc_batch)
        index.wait_for_task(res.task_uid, 60000)  # Espera hasta 60 segundos por lote
    print("¡Indexación incremental completada!")

if __name__ == "__main__":
    import sys
    if '--indexar-nuevos' in sys.argv:
        indexar_nuevos_en_meilisearch()
        sys.exit(0)

    print(f"Indexando {len(docs)} documentos en Meilisearch en lotes de {BATCH_SIZE}...")
    for i, doc_batch in enumerate(batch(docs, BATCH_SIZE), 1):
        print(f"Lote {i}: indexando {len(doc_batch)} documentos...")
        res = index.add_documents(doc_batch)
        index.wait_for_task(res.task_uid, 60000)  # Espera hasta 60 segundos por lote
    print("¡Indexación completada!")