#!/usr/bin/env python3
"""
🧹 TEST: LIMPIEZA DIRECTA EN VERSE SEGMENTER
Verifica que el VerseSegmenter remueva elementos estructurales corruptos
del texto final de los poemas usando la nueva función _clean_structural_corruption.
"""

import sys
import os
sys.path.append('dataset')

def test_verse_segmenter_corruption_cleaning():
    """
    Testa que el VerseSegmenter limpia elementos corruptos directamente en _create_poem_text.
    """
    print("🧹 PROBANDO LIMPIEZA DIRECTA EN VERSE SEGMENTER")
    print("=" * 60)
    
    try:
        from processing.segmenters.verse_segmenter import VerseSegmenter
        
        # Crear segmentador
        segmenter = VerseSegmenter()
        
        # Test 1: Probar función de limpieza directamente
        print("\n🔧 TEST 1: Función _clean_structural_corruption")
        
        test_cases = [
            {
                'input': "Es la tarde gris triste.\n*Antolo* *g* *ía* *Rubén Darío*\nViste el mar de terciopelo",
                'expected_removed': "*Antolo* *g* *ía* *Rubén Darío*",
                'description': "Caso exacto del usuario"
            },
            {
                'input': "Yo soy aquel que ayer no más decía\nAntología Rubén Darío\nel verso azul",
                'expected_removed': "Antología Rubén Darío",
                'description': "Versión normal sin asteriscos"
            },
            {
                'input': "Final del poema\nPágina 25\nhttp://www.librostauro.com.ar",
                'expected_removed': "Página 25",
                'description': "Elementos de página"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n   🔧 Caso {i}: {case['description']}")
            
            original = case['input']
            cleaned = segmenter._clean_structural_corruption(original)
            expected_removed = case['expected_removed']
            
            print(f"      📝 ORIGINAL: '{original[:60]}{'...' if len(original) > 60 else ''}'")
            print(f"      🧹 LIMPIADO: '{cleaned[:60]}{'...' if len(cleaned) > 60 else ''}'")
            
            # Verificar que el elemento fue removido
            if expected_removed not in cleaned:
                print(f"      ✅ Elemento '{expected_removed}' removido correctamente")
            else:
                print(f"      ❌ Elemento '{expected_removed}' NO fue removido")
                return False
        
        # Test 2: Probar creación de texto de poema con limpieza
        print(f"\n🔧 TEST 2: Función _create_poem_text con limpieza")
        
        # Simular bloques de un poema con elementos corruptos
        test_blocks = [
            {'text': 'Es la tarde gris y triste.'},
            {'text': 'Viste el mar de terciopelo\n*Antolo* *g* *ía* *Rubén Darío*\ny el cielo profundo viste'},
            {'text': 'de duelo.'},
        ]
        
        title = "TARDE DEL TRÓPICO"
        poem_text = segmenter._create_poem_text(title, test_blocks)
        
        print(f"   📝 TEXTO FINAL DEL POEMA:")
        print(f"   {repr(poem_text)}")
        
        # Verificar que no contiene elementos corruptos
        if "*Antolo* *g* *ía* *Rubén Darío*" in poem_text:
            print(f"   ❌ FAIL: Elemento corrupto todavía presente")
            return False
        else:
            print(f"   ✅ SUCCESS: Elemento corrupto removido del texto final")
        
        # Verificar que el contenido poético se preservó
        expected_content = ["TARDE DEL TRÓPICO", "Es la tarde gris y triste", "Viste el mar de terciopelo", "de duelo"]
        content_preserved = all(content in poem_text for content in expected_content)
        
        if content_preserved:
            print(f"   ✅ SUCCESS: Contenido poético preservado")
        else:
            print(f"   ❌ WARNING: Algún contenido poético perdido")
            for content in expected_content:
                status = "✅" if content in poem_text else "❌"
                print(f"      {status} '{content}'")
        
        # Test 3: Segmentación completa
        print(f"\n🔧 TEST 3: Segmentación completa con limpieza")
        
        # Simular documento con elementos corruptos
        document_blocks = [
            {'text': 'TARDE DEL TRÓPICO', 'metadata': {'type': 'title'}},
            {'text': 'Es la tarde gris y triste.', 'metadata': {'type': 'verse'}},
            {'text': '*Antolo* *g* *ía* *Rubén Darío*', 'metadata': {'type': 'corruption'}},
            {'text': 'Viste el mar de terciopelo', 'metadata': {'type': 'verse'}},
            {'text': 'y el cielo profundo viste', 'metadata': {'type': 'verse'}},
            {'text': 'de duelo.', 'metadata': {'type': 'verse'}},
            {'text': 'A JOSÉ ENRIQUE RODÓ', 'metadata': {'type': 'title'}},
            {'text': 'Yo soy aquel que ayer no más decía', 'metadata': {'type': 'verse'}},
            {'text': '*Antolo* *g* *ía* *Rubén Darío*', 'metadata': {'type': 'corruption'}},
            {'text': 'el verso azul', 'metadata': {'type': 'verse'}},
        ]
        
        segments = segmenter.segment(document_blocks)
        
        print(f"   📊 SEGMENTOS GENERADOS: {len(segments)}")
        
        corrupted_segments = 0
        for i, segment in enumerate(segments):
            text = segment.get('text', '')
            title = segment.get('title', 'Sin título')
            
            print(f"\n   📖 Segmento {i+1}: '{title}'")
            print(f"      Texto: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
            if "*Antolo* *g* *ía* *Rubén Darío*" in text:
                corrupted_segments += 1
                print(f"      ❌ Contiene elemento corrupto")
            else:
                print(f"      ✅ Libre de elementos corruptos")
        
        if corrupted_segments == 0:
            print(f"\n🎉 SUCCESS: Ningún segmento contiene elementos corruptos")
            print(f"   ✅ VERSO SEGMENTER V2.3 limpia correctamente")
            return True
        else:
            print(f"\n❌ FAIL: {corrupted_segments} segmentos contienen elementos corruptos")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_verse_segmenter_corruption_cleaning()
    
    if success:
        print(f"\n🎉 LIMPIEZA DIRECTA FUNCIONANDO")
        print(f"\n📋 SOLUCIÓN IMPLEMENTADA:")
        print(f"   ✅ VerseSegmenter V2.3 con limpieza directa")
        print(f"   ✅ Función _clean_structural_corruption")
        print(f"   ✅ Aplicada en _create_poem_text")
        print(f"   ✅ Elementos corruptos removidos del output final")
        print(f"\n🚀 READY: Problema del usuario solucionado")
        exit(0)
    else:
        print(f"\n❌ LIMPIEZA DIRECTA NO FUNCIONA - REVISAR IMPLEMENTACIÓN")
        exit(1) 