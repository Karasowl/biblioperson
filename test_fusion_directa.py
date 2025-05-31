#!/usr/bin/env python3
"""
Test DIRECTO para verificar si la fusión de páginas funciona
específicamente para el caso "atractivo" + "de esta idea"
"""

import sys
import os

# Agregar el path del proyecto
sys.path.insert(0, os.path.abspath('.'))

def test_fusion_directa():
    """Test directo de la fusión sin usar el pipeline completo"""
    
    print("🧪 TEST DIRECTO DE FUSIÓN")
    print("=" * 50)
    
    # Simular bloques exactos como los que produce PyMuPDF
    bloques_simulados = [
        {
            'text': 'La promesa principal, por ponerlo simple, es que el pueblo puede gobernar. Al menos en teoría, los populistas aseveran que el pueblo como un todo no sólo tiene una voluntad común y coherente, sino que también puede gobernar, en el sentido de que los representantes correctos pueden instrumentar lo que el pueblo ha demandado en forma de un mandato imperativo. Muchas intuiciones iniciales sobre la democracia pueden acomodarse en un cuadro similar: la democracia es autogobierno y quien puede gobernar idealmente no es sólo una minoría sino el todo. Incluso en la Atenas democrática esta historia no era toda la historia, pero Atenas se acercó a la democracia tanto como es imaginable, en el sentido de cultivar un sentido de la capacidad colectiva y de, en los hechos, involucrarse en una acción colectiva (pero, fundamentalmente, bajo el entendido de que los ciudadanos gobernarían y serían gobernados sucesivamente: no hay democracia sin una rotación adecuada hacia y desde la función pública).2 Uno tendría que ser muy necio para no ver el atractivo',
            'page': 45,
            'bbox': [100, 100, 500, 700]
        },
        {
            'text': 'de esta idea de cómo dominar colectivamente el propio destino, y se nos debe excusar por sentir nostalgia ante esta pérdida en la práctica.',
            'page': 46,
            'bbox': [100, 50, 500, 150]
        }
    ]
    
    print("📋 BLOQUES ORIGINALES:")
    for i, bloque in enumerate(bloques_simulados):
        print(f"  {i+1}. Página {bloque['page']}: {bloque['text'][:50]}...")
    
    # Test 1: Verificar función de detección
    print(f"\n🔍 TEST 1: Función _should_merge_cross_page")
    try:
        from dataset.processing.loaders.pdf_loader import PDFLoader
        
        # Crear una instancia dummy para usar el método
        loader = PDFLoader("dummy.pdf")
        
        texto1 = bloques_simulados[0]['text']
        texto2 = bloques_simulados[1]['text']
        
        resultado = loader._should_merge_cross_page(texto1, texto2)
        print(f"  ¿Debería fusionar?: {resultado}")
        
        if resultado:
            print("  ✅ DETECTÓ que debe fusionar")
        else:
            print("  ❌ NO detectó que debe fusionar")
            
    except Exception as e:
        print(f"  💥 ERROR en _should_merge_cross_page: {e}")
    
    # Test 2: Verificar fusión completa
    print(f"\n🔧 TEST 2: Función _merge_cross_page_sentences completa")
    try:
        resultado_fusion = loader._merge_cross_page_sentences(bloques_simulados)
        
        print(f"📊 RESULTADO DE FUSIÓN:")
        print(f"  Bloques originales: {len(bloques_simulados)}")
        print(f"  Bloques después de fusión: {len(resultado_fusion)}")
        
        if len(resultado_fusion) == 1:
            print("  ✅ FUSIONÓ correctamente en 1 bloque")
            texto_fusionado = resultado_fusion[0]['text']
            if "atractivo de esta idea" in texto_fusionado:
                print("  ✅ El texto 'atractivo de esta idea' está UNIDO")
                print(f"  📝 Fragmento: ...{texto_fusionado[texto_fusionado.find('atractivo')-20:texto_fusionado.find('idea')+20]}...")
            else:
                print("  ❌ El texto 'atractivo de esta idea' NO está unido")
        else:
            print("  ❌ NO fusionó correctamente")
            for i, bloque in enumerate(resultado_fusion):
                print(f"    Bloque {i+1}: {bloque['text'][:100]}...")
                
    except Exception as e:
        print(f"  💥 ERROR en _merge_cross_page_sentences: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: ¿Por qué no funciona en el pipeline real?
    print(f"\n🚨 TEST 3: Comparación con pipeline real")
    print("   Esto nos ayudará a entender por qué el pipeline real no funciona")
    
    try:
        # Ejecutar el loader real
        pdf_path = r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf"
        
        if os.path.exists(pdf_path):
            loader_real = PDFLoader(pdf_path)
            raw_data = loader_real.load()
            
            # Buscar bloques que contienen "atractivo" y "de esta idea"
            bloques_atractivo = []
            for i, block in enumerate(raw_data['blocks']):
                text = block.get('text', '')
                if 'atractivo' in text or 'de esta idea' in text:
                    bloques_atractivo.append((i, text[:100] + "..."))
            
            print(f"   📋 Bloques del loader real que contienen 'atractivo' o 'de esta idea':")
            for i, texto in bloques_atractivo:
                print(f"     Bloque {i}: {texto}")
                
            if len(bloques_atractivo) == 1:
                print("   ✅ El loader real SÍ fusiona correctamente")
            else:
                print("   ❌ El loader real NO está fusionando")
        
    except Exception as e:
        print(f"   💥 ERROR ejecutando loader real: {e}")

if __name__ == "__main__":
    test_fusion_directa() 