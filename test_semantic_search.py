#!/usr/bin/env python3
"""
Script para probar la búsqueda semántica en Biblioperson
"""

import requests
import json
import sqlite3
import sys
import os

def test_backend_health():
    """Verificar que el backend esté funcionando"""
    print("🔍 1. Verificando backend...")
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend funcionando correctamente")
            return True
        else:
            print(f"❌ Backend responde con código {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        return False

def check_database():
    """Verificar datos en la base de datos"""
    print("\n🔍 2. Verificando base de datos...")
    try:
        db_path = 'data.ms/documents.db'
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Tablas disponibles: {tables}")
        
        # Contar documentos y segmentos
        if 'documents' in tables:
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            print(f"📚 Documentos: {doc_count}")
        
        if 'segments' in tables:
            cursor.execute("SELECT COUNT(*) FROM segments")
            seg_count = cursor.fetchone()[0]
            print(f"📄 Segmentos: {seg_count}")
        
        # Verificar embeddings
        if 'embeddings' in tables:
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            emb_count = cursor.fetchone()[0]
            print(f"🧠 Embeddings: {emb_count}")
            
            if emb_count > 0:
                cursor.execute("SELECT model FROM embeddings LIMIT 1")
                model = cursor.fetchone()[0]
                print(f"🤖 Modelo usado: {model}")
                print("✅ Embeddings disponibles para búsqueda semántica")
                return True
            else:
                print("⚠️ No hay embeddings generados")
                return False
        else:
            print("⚠️ Tabla de embeddings no encontrada")
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def test_semantic_search():
    """Probar búsqueda semántica"""
    print("\n🔍 3. Probando búsqueda semántica...")
    
    test_queries = [
        "amor eterno",
        "muerte tristeza",
        "democracia política",
        "ciencia física"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Probando query: '{query}'")
        try:
            response = requests.post(
                'http://localhost:5000/api/search/semantic',
                json={'query': query, 'limit': 3},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Encontrados {len(results)} resultados")
                
                for i, result in enumerate(results[:2], 1):
                    print(f"  {i}. {result.get('document_title', 'Sin título')}")
                    print(f"     Autor: {result.get('document_author', 'Desconocido')}")
                    print(f"     Similitud: {result.get('similarity', 0):.3f}")
                    print(f"     Texto: {result.get('text', '')[:100]}...")
                    
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")

def test_literal_search():
    """Probar búsqueda literal para comparar"""
    print("\n🔍 4. Probando búsqueda literal (para comparar)...")
    
    try:
        response = requests.get(
            'http://localhost:5000/api/search',
            params={'q': 'amor', 'limit': 3},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ Búsqueda literal encontró {len(results)} resultados para 'amor'")
            
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. {result.get('document_title', 'Sin título')}")
                print(f"     Texto: {result.get('text', '')[:100]}...")
        else:
            print(f"❌ Error en búsqueda literal: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en búsqueda literal: {e}")

def test_frontend_api():
    """Probar la API del frontend"""
    print("\n🔍 5. Probando API del frontend...")
    
    try:
        # Probar búsqueda semántica a través del frontend
        response = requests.post(
            'http://localhost:11983/api/search',
            json={
                'query': 'amor eterno',
                'type': 'semantic',
                'options': {'limit': 3}
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ Frontend API funcionando - {len(results)} resultados")
            
            if results:
                print(f"  Primer resultado: {results[0].get('documentTitle', 'Sin título')}")
                print(f"  Score: {results[0].get('score', 0)}")
        else:
            print(f"❌ Error en frontend API: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error probando frontend: {e}")

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 PRUEBAS DE BÚSQUEDA SEMÁNTICA EN BIBLIOPERSON")
    print("=" * 50)
    
    # Ejecutar pruebas en orden
    if not test_backend_health():
        print("\n❌ Backend no disponible. Asegúrate de que esté corriendo.")
        sys.exit(1)
    
    if not check_database():
        print("\n⚠️ Base de datos sin embeddings. Ejecuta:")
        print("python scripts/backend/procesar_semantica.py")
        print("para generar embeddings.")
    
    test_semantic_search()
    test_literal_search()
    test_frontend_api()
    
    print("\n🎉 PRUEBAS COMPLETADAS")
    print("\n💡 Para probar en el navegador:")
    print("1. Ve a http://localhost:11983")
    print("2. Abre la biblioteca")
    print("3. Usa búsqueda avanzada")
    print("4. Selecciona 'Semantic' o 'Both'")
    print("5. Busca: 'amor eterno', 'tristeza muerte', etc.")

if __name__ == "__main__":
    main() 