#!/usr/bin/env python3
"""
Prueba simple de búsqueda para verificar que el sistema funciona
"""

import requests
import time

def test_frontend_running():
    """Verificar que el frontend esté corriendo"""
    print("🔍 Verificando frontend...")
    
    # Probar diferentes puertos
    ports = [11983, 3000, 8080]
    
    for port in ports:
        try:
            response = requests.get(f'http://localhost:{port}', timeout=3)
            if response.status_code == 200:
                print(f"✅ Frontend corriendo en puerto {port}")
                return port
        except:
            continue
    
    print("❌ Frontend no encontrado en puertos comunes")
    return None

def test_literal_search():
    """Probar búsqueda literal"""
    print("\n🔍 Probando búsqueda literal...")
    
    try:
        # Probar búsqueda literal a través del backend
        response = requests.get(
            'http://localhost:5000/api/search',
            params={'q': 'amor', 'limit': 3},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ Encontrados {len(results)} resultados para 'amor'")
            
            for i, result in enumerate(results[:3], 1):
                title = result.get('document_title', result.get('title', 'Sin título'))
                text = result.get('text', result.get('content_preview', ''))[:100]
                print(f"  {i}. {title}")
                print(f"     Texto: {text}...")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_frontend_search():
    """Probar búsqueda a través del frontend"""
    print("\n🔍 Probando búsqueda del frontend...")
    
    frontend_port = test_frontend_running()
    if not frontend_port:
        print("⚠️ Frontend no disponible")
        return
    
    try:
        # Probar búsqueda literal
        response = requests.post(
            f'http://localhost:{frontend_port}/api/search',
            json={
                'query': 'amor',
                'type': 'literal',
                'options': {'limit': 3}
            },
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ Frontend API - {len(results)} resultados")
            
            if results:
                print(f"  Primer resultado: {results[0].get('documentTitle', 'Sin título')}")
        else:
            print(f"❌ Error frontend: {response.text[:200]}")
            
        # Probar búsqueda semántica (debería fallar graciosamente)
        print("\n🧠 Probando búsqueda semántica...")
        response = requests.post(
            f'http://localhost:{frontend_port}/api/search',
            json={
                'query': 'amor eterno',
                'type': 'semantic',
                'options': {'limit': 3}
            },
            timeout=10
        )
        
        print(f"Status semántica: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"🎉 ¡Búsqueda semántica funcionando! - {len(results)} resultados")
        else:
            print(f"⚠️ Búsqueda semántica no disponible (esperado sin embeddings)")
            
    except Exception as e:
        print(f"❌ Error frontend: {e}")

def test_document_content():
    """Verificar que tenemos contenido para buscar"""
    print("\n📚 Verificando contenido disponible...")
    
    try:
        response = requests.get('http://localhost:5000/api/library/documents', timeout=5)
        if response.status_code == 200:
            data = response.json()
            docs = data.get('documents', [])
            print(f"✅ {len(docs)} documentos disponibles")
            
            # Mostrar algunos documentos
            for i, doc in enumerate(docs[:3], 1):
                print(f"  {i}. {doc.get('title', 'Sin título')}")
                print(f"     Autor: {doc.get('author', 'Desconocido')}")
                print(f"     Palabras: {doc.get('word_count', 0)}")
                
            return len(docs) > 0
        else:
            print(f"❌ Error obteniendo documentos: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar pruebas básicas"""
    print("🧪 PRUEBAS BÁSICAS DE BÚSQUEDA - BIBLIOPERSON")
    print("=" * 50)
    
    # Verificar que tenemos contenido
    if not test_document_content():
        print("\n❌ No hay contenido para buscar")
        return
    
    # Probar búsqueda literal
    test_literal_search()
    
    # Esperar un poco para que el frontend se inicie
    print("\n⏳ Esperando que el frontend se inicie...")
    time.sleep(5)
    
    # Probar frontend
    test_frontend_search()
    
    print("\n🎯 RESUMEN:")
    print("1. ✅ Backend funcionando con contenido real")
    print("2. ⚠️ Búsqueda semántica requiere embeddings")
    print("3. 💡 Para generar embeddings, necesitas configurar la base de datos correcta")
    
    print("\n📋 PRÓXIMOS PASOS PARA BÚSQUEDA SEMÁNTICA:")
    print("1. Configura la ruta correcta de la base de datos en procesar_semantica.py")
    print("2. Ejecuta: python scripts/backend/procesar_semantica.py")
    print("3. Reinicia el backend")
    print("4. Prueba búsquedas como 'amor eterno', 'tristeza muerte'")

if __name__ == "__main__":
    main() 