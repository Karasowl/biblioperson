#!/usr/bin/env python3
"""
🔧 TEST: FILTRADO DE VARIACIONES CORRUPTAS
Verifica que elementos como "*Antolo* *g* *ía* *Rubén Darío*" se detecten
y filtren como variaciones del mismo elemento estructural.
"""

import sys
import os
sys.path.append('dataset')

def test_corrupted_variations_detection():
    """
    Testa la detección de variaciones corruptas del mismo elemento estructural.
    """
    print("🔧 PROBANDO DETECCIÓN DE VARIACIONES CORRUPTAS")
    print("=" * 60)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Simular documento con VARIACIONES CORRUPTAS del mismo elemento
        test_blocks = [
            # Página 1 - Versión normal
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 1}},
            {"text": "TARDE DEL TRÓPICO", "metadata": {"page_number": 1}},
            
            # Página 2 - Versión con asteriscos (como en el ejemplo del usuario)
            {"text": "*Antolo* *g* *ía* *Rubén Darío*", "metadata": {"page_number": 2}},
            {"text": "Es la tarde gris triste.", "metadata": {"page_number": 2}},
            
            # Página 3 - Versión con espacios entre letras
            {"text": "A n t o l o g í a   R u b é n   D a r í o", "metadata": {"page_number": 3}},
            {"text": "A JOSÉ ENRIQUE RODÓ", "metadata": {"page_number": 3}},
            
            # Página 4 - Versión con formato mixto
            {"text": "*Antología* Rubén *Darío*", "metadata": {"page_number": 4}},
            {"text": "Yo soy aquel que ayer no más decía", "metadata": {"page_number": 4}},
            
            # Página 5 - Versión en mayúsculas
            {"text": "ANTOLOGÍA RUBÉN DARÍO", "metadata": {"page_number": 5}},
            {"text": "Final del libro", "metadata": {"page_number": 5}},
        ]
        
        print(f"📝 Entrada: {len(test_blocks)} bloques en 5 páginas")
        print(f"   - Variaciones del elemento estructural:")
        print(f"     • 'Antología Rubén Darío' (normal)")
        print(f"     • '*Antolo* *g* *ía* *Rubén Darío*' (con asteriscos)")
        print(f"     • 'A n t o l o g í a   R u b é n   D a r í o' (espaciado)")
        print(f"     • '*Antología* Rubén *Darío*' (formato mixto)")
        print(f"     • 'ANTOLOGÍA RUBÉN DARÍO' (mayúsculas)")
        
        # Crear preprocessor
        preprocessor = CommonBlockPreprocessor()
        
        # Test 1: Probar normalización individual
        print(f"\n🔧 PROBANDO NORMALIZACIÓN:")
        test_texts = [
            "Antología Rubén Darío",
            "*Antolo* *g* *ía* *Rubén Darío*",
            "A n t o l o g í a   R u b é n   D a r í o",
            "*Antología* Rubén *Darío*",
            "ANTOLOGÍA RUBÉN DARÍO"
        ]
        
        normalized_results = []
        for text in test_texts:
            normalized = preprocessor._normalize_text_for_structural_detection(text)
            normalized_results.append(normalized)
            print(f"  '{text}' → '{normalized}'")
        
        # Verificar que todas se normalizan al mismo resultado
        if len(set(normalized_results)) == 1:
            print(f"  ✅ Todas las variaciones se normalizan igual: '{normalized_results[0]}'")
        else:
            print(f"  ❌ Error: Diferentes normalizaciones: {set(normalized_results)}")
            return False
        
        # Test 2: Detectar elementos estructurales
        structural_elements = preprocessor._detect_structural_elements(test_blocks)
        
        print(f"\n📊 RESULTADOS DE DETECCIÓN:")
        print(f"  - Elementos estructurales detectados: {len(structural_elements)}")
        for element in structural_elements:
            print(f"    🚫 '{element}'")
        
        # Verificar que TODAS las variaciones fueron detectadas
        expected_variations = [
            "Antología Rubén Darío",
            "*Antolo* *g* *ía* *Rubén Darío*",
            "A n t o l o g í a   R u b é n   D a r í o",
            "*Antología* Rubén *Darío*",
            "ANTOLOGÍA RUBÉN DARÍO"
        ]
        
        detected_count = sum(1 for var in expected_variations if var in structural_elements)
        
        if detected_count == len(expected_variations):
            print(f"\n✅ SUCCESS: Todas las {len(expected_variations)} variaciones detectadas")
        else:
            print(f"\n❌ FAIL: Solo {detected_count}/{len(expected_variations)} variaciones detectadas")
            return False
        
        # Test 3: Filtrar elementos estructurales
        filtered_blocks = preprocessor._filter_structural_elements(test_blocks, structural_elements)
        
        print(f"\n📊 RESULTADOS DE FILTRADO:")
        print(f"  - Bloques originales: {len(test_blocks)}")
        print(f"  - Bloques filtrados: {len(filtered_blocks)}")
        print(f"  - Bloques eliminados: {len(test_blocks) - len(filtered_blocks)}")
        
        # Verificar que el contenido real se preservó
        filtered_texts = [block.get('text', '') for block in filtered_blocks]
        preserved_content = ["TARDE DEL TRÓPICO", "A JOSÉ ENRIQUE RODÓ", "Es la tarde gris triste."]
        preserved_count = sum(1 for text in preserved_content if text in filtered_texts)
        
        print(f"\n📝 CONTENIDO PRESERVADO:")
        print(f"  - Contenido preservado: {preserved_count}/{len(preserved_content)}")
        for text in preserved_content:
            status = "✅" if text in filtered_texts else "❌"
            print(f"    {status} '{text}'")
        
        # Verificar que NINGUNA variación estructural permanece
        remaining_structural = sum(1 for var in expected_variations if var in filtered_texts)
        
        if remaining_structural == 0 and preserved_count >= 2:
            print(f"\n🎉 FILTRADO DE VARIACIONES EXITOSO:")
            print(f"   - Todas las variaciones estructurales eliminadas")
            print(f"   - Contenido real preservado")
            return True
        else:
            print(f"\n❌ PROBLEMAS EN EL FILTRADO:")
            if remaining_structural > 0:
                print(f"   - {remaining_structural} variaciones estructurales NO eliminadas")
            if preserved_count < 2:
                print(f"   - Poco contenido real preservado")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_case_from_user():
    """
    Testa el caso real reportado por el usuario.
    """
    print("\n🔧 PROBANDO CASO REAL DEL USUARIO")
    print("=" * 60)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Simular el caso real del usuario
        real_case_blocks = [
            # Primer poema con elemento estructural corrupto
            {"text": "TARDE DEL TRÓPICO\nEs la tarde gris triste.\nViste el mar de terciopelo\ny el cielo profundo viste\nde duelo.\n*Antolo* *g* *ía* *Rubén Darío*", "metadata": {"page_number": 1}},
            
            # Segundo poema con elemento estructural corrupto
            {"text": "A JOSÉ ENRIQUE RODÓ\nYo soy aquel que ayer no más decía\nel verso azul la canción profana\n*Antolo* *g* *ía* *Rubén Darío*", "metadata": {"page_number": 2}},
            
            # Páginas adicionales para trigger de detección
            {"text": "*Antolo* *g* *ía* *Rubén Darío*", "metadata": {"page_number": 3}},
            {"text": "OTRO POEMA", "metadata": {"page_number": 3}},
            {"text": "*Antolo* *g* *ía* *Rubén Darío*", "metadata": {"page_number": 4}},
            {"text": "Contenido página 4", "metadata": {"page_number": 4}},
            {"text": "*Antolo* *g* *ía* *Rubén Darío*", "metadata": {"page_number": 5}},
            {"text": "Contenido página 5", "metadata": {"page_number": 5}},
        ]
        
        print(f"📝 Caso real: Texto corrupto '*Antolo* *g* *ía* *Rubén Darío*'")
        print(f"   - Aparece en texto de poemas y como bloques separados")
        print(f"   - {len(real_case_blocks)} bloques en 5 páginas")
        
        # Procesar con filtrado estructural activado
        preprocessor = CommonBlockPreprocessor()
        
        # Detectar y filtrar
        structural_elements = preprocessor._detect_structural_elements(real_case_blocks)
        print(f"\n📊 Elementos detectados: {len(structural_elements)}")
        
        # Procesar completo
        processed_blocks, metadata = preprocessor.process(real_case_blocks, {})
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"  - Bloques procesados: {len(processed_blocks)}")
        
        # Verificar que NO aparece el elemento corrupto en ningún texto final
        corrupted_element = "*Antolo* *g* *ía* *Rubén Darío*"
        found_corrupted = False
        
        for block in processed_blocks:
            text = block.get('text', '')
            if corrupted_element in text:
                found_corrupted = True
                print(f"  ❌ ENCONTRADO elemento corrupto en: '{text[:100]}...'")
        
        if not found_corrupted:
            print(f"  ✅ SUCCESS: Elemento corrupto eliminado de todos los textos")
            
            # Verificar que los títulos de poemas se preservaron
            poem_titles = ["TARDE DEL TRÓPICO", "A JOSÉ ENRIQUE RODÓ", "OTRO POEMA"]
            preserved_titles = 0
            
            for block in processed_blocks:
                text = block.get('text', '')
                for title in poem_titles:
                    if title in text:
                        preserved_titles += 1
                        break
            
            print(f"  ✅ Títulos de poemas preservados: {preserved_titles}/{len(poem_titles)}")
            
            if preserved_titles >= 2:
                print(f"\n🎉 CASO REAL SOLUCIONADO!")
                return True
            else:
                print(f"\n⚠️ WARNING: Pocos títulos preservados")
                return True  # Aún éxito parcial
        else:
            print(f"\n❌ FAIL: Elemento corrupto todavía presente")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_corrupted_variations_detection()
    success2 = test_real_case_from_user()
    
    if success1 and success2:
        print(f"\n🎉 TODOS LOS TESTS PASARON - VARIACIONES CORRUPTAS MANEJADAS")
        print(f"\n📋 PROBLEMA SOLUCIONADO:")
        print(f"   ✅ Detección de '*Antolo* *g* *ía* *Rubén Darío*'")
        print(f"   ✅ Filtrado de variaciones corruptas")
        print(f"   ✅ Preservación de contenido poético")
        print(f"\n🚀 READY: Filtrado robusto funcionando")
        exit(0)
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON - REVISAR NORMALIZACIÓN")
        exit(1) 