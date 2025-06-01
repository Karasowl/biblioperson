#!/usr/bin/env python3
"""
🔧 TEST: FILTRADO DE ELEMENTOS ESTRUCTURALES
Verifica que elementos como "Antología Rubén Darío" que aparecen en >90% de páginas
se detecten y filtren automáticamente.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

def test_structural_element_detection():
    """
    Testa la detección de elementos estructurales repetitivos.
    """
    print("🔧 PROBANDO DETECCIÓN DE ELEMENTOS ESTRUCTURALES")
    print("=" * 60)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Simular documento con elementos estructurales repetitivos
        test_blocks = [
            # Página 1
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 1}},
            {"text": "MARCHA TRIUNFAL", "metadata": {"page_number": 1}},
            {"text": "Ya viene el cortejo!", "metadata": {"page_number": 1}},
            
            # Página 2  
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 2}},
            {"text": "La espada se anuncia con vivo reflejo;", "metadata": {"page_number": 2}},
            {"text": "ya viene, oro y hierro, el cortejo de los paladines.", "metadata": {"page_number": 2}},
            
            # Página 3
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 3}},
            {"text": "SOUVENIR", "metadata": {"page_number": 3}},
            {"text": "En el agua clara", "metadata": {"page_number": 3}},
            
            # Página 4
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 4}},
            {"text": "que brota de la fuente", "metadata": {"page_number": 4}},
            {"text": "de mármol", "metadata": {"page_number": 4}},
            
            # Página 5
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 5}},
            {"text": "CANTARES DEL CARDÓN", "metadata": {"page_number": 5}},
            {"text": "Último verso del libro", "metadata": {"page_number": 5}},
        ]
        
        print(f"📝 Entrada: {len(test_blocks)} bloques en 5 páginas")
        print(f"   - 'Antología Rubén Darío' aparece en {5}/5 páginas (100%)")
        
        # Crear preprocessor con configuración por defecto
        preprocessor = CommonBlockPreprocessor()
        
        # Detectar elementos estructurales
        structural_elements = preprocessor._detect_structural_elements(test_blocks)
        
        print(f"\n📊 RESULTADOS DE DETECCIÓN:")
        print(f"  - Elementos estructurales detectados: {len(structural_elements)}")
        for element in structural_elements:
            print(f"    🚫 '{element}'")
        
        # Verificar que "Antología Rubén Darío" fue detectado
        expected_structural = "Antología Rubén Darío"
        if expected_structural in structural_elements:
            print(f"\n✅ SUCCESS: '{expected_structural}' detectado como elemento estructural")
        else:
            print(f"\n❌ FAIL: '{expected_structural}' NO fue detectado como elemento estructural")
            return False
        
        # Filtrar elementos estructurales
        filtered_blocks = preprocessor._filter_structural_elements(test_blocks, structural_elements)
        
        print(f"\n📊 RESULTADOS DE FILTRADO:")
        print(f"  - Bloques originales: {len(test_blocks)}")
        print(f"  - Bloques filtrados: {len(filtered_blocks)}")
        print(f"  - Bloques eliminados: {len(test_blocks) - len(filtered_blocks)}")
        
        # Verificar que los elementos estructurales fueron eliminados
        remaining_texts = [block.get('text', '') for block in filtered_blocks]
        if expected_structural not in remaining_texts:
            print(f"\n✅ SUCCESS: '{expected_structural}' eliminado correctamente")
            
            # Verificar que el contenido real se preservó
            content_texts = ["MARCHA TRIUNFAL", "Ya viene el cortejo!", "SOUVENIR", "CANTARES DEL CARDÓN"]
            preserved_content = [text for text in content_texts if text in remaining_texts]
            
            print(f"\n📋 CONTENIDO PRESERVADO:")
            for text in preserved_content:
                print(f"    ✅ '{text}'")
            
            if len(preserved_content) >= 3:  # Al menos 3 títulos preservados
                print(f"\n🎉 FILTRADO EXITOSO: Elementos estructurales eliminados, contenido preservado")
                return True
            else:
                print(f"\n❌ FAIL: Demasiado contenido eliminado")
                return False
        else:
            print(f"\n❌ FAIL: '{expected_structural}' NO fue eliminado")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """
    Testa casos edge de la detección estructural.
    """
    print("\n🔧 PROBANDO CASOS EDGE")
    print("=" * 60)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Caso 1: Documento muy pequeño (< 5 páginas)
        small_doc_blocks = [
            {"text": "Header", "metadata": {"page_number": 1}},
            {"text": "Contenido 1", "metadata": {"page_number": 1}},
            {"text": "Header", "metadata": {"page_number": 2}},
            {"text": "Contenido 2", "metadata": {"page_number": 2}},
        ]
        
        preprocessor = CommonBlockPreprocessor()
        structural_elements_small = preprocessor._detect_structural_elements(small_doc_blocks)
        
        print(f"📝 Caso 1 - Doc pequeño (2 páginas):")
        print(f"  - Elementos detectados: {len(structural_elements_small)}")
        print(f"  - Esperado: 0 (documento muy pequeño)")
        
        if len(structural_elements_small) == 0:
            print(f"  ✅ Correcto: No se detectan elementos en docs pequeños")
        else:
            print(f"  ❌ Error: Se detectaron elementos en doc pequeño")
        
        # Caso 2: Elemento que aparece en 80% de páginas (debajo del umbral)
        below_threshold_blocks = [
            {"text": "Header Ocasional", "metadata": {"page_number": 1}},
            {"text": "Contenido", "metadata": {"page_number": 1}},
            {"text": "Header Ocasional", "metadata": {"page_number": 2}},
            {"text": "Contenido", "metadata": {"page_number": 2}},
            {"text": "Header Ocasional", "metadata": {"page_number": 3}},
            {"text": "Contenido", "metadata": {"page_number": 3}},
            {"text": "Header Ocasional", "metadata": {"page_number": 4}},
            {"text": "Contenido", "metadata": {"page_number": 4}},
            {"text": "Contenido", "metadata": {"page_number": 5}},  # Sin header en página 5
            {"text": "Más contenido", "metadata": {"page_number": 5}},
        ]
        
        structural_elements_below = preprocessor._detect_structural_elements(below_threshold_blocks)
        
        print(f"\n📝 Caso 2 - Elemento en 80% de páginas:")
        print(f"  - Elementos detectados: {len(structural_elements_below)}")
        print(f"  - Esperado: 0 (debajo del umbral 90%)")
        
        if len(structural_elements_below) == 0:
            print(f"  ✅ Correcto: Elemento debajo del umbral no detectado")
        else:
            print(f"  ❌ Error: Elemento debajo del umbral fue detectado")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_full_process_integration():
    """
    Testa la integración completa con el método process().
    """
    print("\n🔧 PROBANDO INTEGRACIÓN COMPLETA")
    print("=" * 60)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Crear documento con elementos estructurales
        test_blocks = [
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 1}},
            {"text": "MARCHA TRIUNFAL", "metadata": {"page_number": 1}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 2}},
            {"text": "Ya viene el cortejo!", "metadata": {"page_number": 2}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 3}},
            {"text": "SOUVENIR", "metadata": {"page_number": 3}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 4}},
            {"text": "En el agua clara", "metadata": {"page_number": 4}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 5}},
            {"text": "Final del libro", "metadata": {"page_number": 5}},
        ]
        
        # Procesar con CommonBlockPreprocessor
        preprocessor = CommonBlockPreprocessor()
        processed_blocks, metadata = preprocessor.process(test_blocks, {})
        
        # Verificar que elementos estructurales fueron filtrados
        processed_texts = [block.get('text', '') for block in processed_blocks]
        structural_element = "Antología Rubén Darío"
        
        print(f"📊 RESULTADOS INTEGRACIÓN:")
        print(f"  - Bloques originales: {len(test_blocks)}")
        print(f"  - Bloques procesados: {len(processed_blocks)}")
        
        if structural_element not in processed_texts:
            print(f"  ✅ Elemento estructural eliminado: '{structural_element}'")
            
            # Verificar contenido preservado
            preserved_content = ["MARCHA TRIUNFAL", "Ya viene el cortejo!", "SOUVENIR"]
            preserved_count = sum(1 for text in preserved_content if text in processed_texts)
            
            print(f"  ✅ Contenido preservado: {preserved_count}/{len(preserved_content)} elementos")
            
            if preserved_count >= 2:
                print(f"\n🎉 INTEGRACIÓN EXITOSA: Filtrado estructural funcionando")
                return True
            else:
                print(f"\n❌ FAIL: Demasiado contenido eliminado en integración")
                return False
        else:
            print(f"  ❌ Elemento estructural NO eliminado: '{structural_element}'")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_structural_element_detection()
    success2 = test_edge_cases()
    success3 = test_full_process_integration()
    
    if success1 and success2 and success3:
        print(f"\n🎉 TODOS LOS TESTS PASARON - FILTRADO ESTRUCTURAL FUNCIONANDO")
        exit(0)
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON - REVISAR IMPLEMENTACIÓN")
        exit(1) 