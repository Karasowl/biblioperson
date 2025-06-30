#!/usr/bin/env python3
"""
Script para probar la búsqueda semántica POTENTE
"""

import requests
import time
import json

def test_powerful_semantic_search():
    """Probar la búsqueda semántica potente con Platón"""
    print("🚀 PROBANDO BÚSQUEDA SEMÁNTICA POTENTE")
    print("=" * 50)
    
    # Esperar a que el backend cargue el modelo potente
    print("⏳ Esperando a que cargue el modelo potente...")
    time.sleep(10)
    
    # Consultas de prueba para encontrar Platón
    test_queries = [
        "sociedad justa filosofía política",
        "república ideal gobierno",
        "justicia virtud estado",
        "filosofía política antigua",
        "Platón república"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Prueba {i}: '{query}'")
        try:
            response = requests.post(
                'http://localhost:5000/api/search/semantic',
                json={'query': query, 'limit': 5},
                timeout=45
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ {len(results)} resultados encontrados")
                
                for j, result in enumerate(results, 1):
                    title = result.get('document_title', 'Sin título')
                    author = result.get('document_author', 'Desconocido')
                    similarity = result.get('similarity', 0)
                    text_preview = result.get('text', '')[:100] + "..."
                    
                    print(f"  {j}. 📖 {title}")
                    print(f"     👤 Autor: {author}")
                    print(f"     🎯 Similitud: {similarity:.4f}")
                    print(f"     📝 Texto: {text_preview}")
                    
                    # ¡Buscar específicamente Platón!
                    if 'plat' in title.lower() or 'plat' in author.lower() or 'república' in title.lower():
                        print(f"     🎉 ¡ENCONTRADO PLATÓN!")
                        
            else:
                error_text = response.text
                print(f"❌ Error: {error_text}")
                
        except Exception as e:
            print(f"❌ Error en request: {e}")
        
        print("-" * 40)
    
    print(f"\n🎯 PRUEBA COMPLETADA")
    print("Si no encontró Platón, el backend puede estar usando una BD diferente")

if __name__ == "__main__":
    test_powerful_semantic_search() 