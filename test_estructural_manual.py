#!/usr/bin/env python3
"""
🔧 TEST MANUAL: SIMULACIÓN FILTRADO ESTRUCTURAL
Simula el comportamiento que tendría con un documento real tipo "Antología Rubén Darío".
"""

import sys
import os
sys.path.append('dataset')

def test_simulated_anthology():
    print("🔧 TEST: SIMULACIÓN ANTOLOGÍA CON ELEMENTOS ESTRUCTURALES")
    print("=" * 70)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Simular un documento típico con headers/footers repetitivos
        # Basado en el ejemplo del usuario: "Antología Rubén Darío" en cada página
        simulated_blocks = []
        
        # Simular 50 páginas de un libro de poesía
        for page in range(1, 51):
            # Header repetitivo en cada página
            simulated_blocks.append({
                "text": "Antología Rubén Darío",
                "metadata": {"page_number": page, "type": "header"}
            })
            
            # Footer ocasional (70% de páginas) - debajo del umbral
            if page % 10 <= 7:  # 70% de páginas
                simulated_blocks.append({
                    "text": f"Página {page}",
                    "metadata": {"page_number": page, "type": "footer"}
                })
            
            # Contenido real variado por página
            if page <= 10:  # Primeras páginas - MARCHA TRIUNFAL
                simulated_blocks.extend([
                    {"text": "MARCHA TRIUNFAL", "metadata": {"page_number": page}},
                    {"text": "Ya viene el cortejo!", "metadata": {"page_number": page}},
                    {"text": "La espada se anuncia con vivo reflejo;", "metadata": {"page_number": page}},
                ])
            elif page <= 20:  # Páginas 11-20 - SOUVENIR
                simulated_blocks.extend([
                    {"text": "SOUVENIR", "metadata": {"page_number": page}},
                    {"text": "En el agua clara", "metadata": {"page_number": page}},
                    {"text": "que brota de la fuente", "metadata": {"page_number": page}},
                ])
            elif page <= 30:  # Páginas 21-30 - CANTARES
                simulated_blocks.extend([
                    {"text": "CANTARES DEL CARDÓN", "metadata": {"page_number": page}},
                    {"text": "Del desierto vengo", "metadata": {"page_number": page}},
                    {"text": "cantando mis penas", "metadata": {"page_number": page}},
                ])
            else:  # Páginas 31-50 - Contenido variado
                poem_num = page - 30
                simulated_blocks.extend([
                    {"text": f"POEMA {poem_num}", "metadata": {"page_number": page}},
                    {"text": f"Verso {poem_num} línea 1", "metadata": {"page_number": page}},
                    {"text": f"Verso {poem_num} línea 2", "metadata": {"page_number": page}},
                ])
        
        print(f"📚 Documento simulado: {len(simulated_blocks)} bloques en 50 páginas")
        print(f"   - 'Antología Rubén Darío' aparece en 50/50 páginas (100%)")
        print(f"   - 'Página N' aparece en ~35/50 páginas (70%)")
        
        # Configurar filtrado estructural
        config = {
            'filter_structural_elements': True,
            'structural_frequency_threshold': 0.9,  # 90% de páginas
            'min_pages_for_structural_detection': 5,
        }
        
        preprocessor = CommonBlockPreprocessor(config=config)
        
        # Detectar elementos estructurales
        structural_elements = preprocessor._detect_structural_elements(simulated_blocks)
        
        print(f"\n📊 DETECCIÓN DE ELEMENTOS ESTRUCTURALES:")
        print(f"  - Elementos detectados: {len(structural_elements)}")
        
        for elem in structural_elements:
            # Calcular frecuencia real
            count = sum(1 for b in simulated_blocks if b.get('text', '').strip() == elem)
            frequency = (count / 50) * 100  # 50 páginas total
            print(f"    🚫 '{elem}' ({count} apariciones, {frequency:.1f}%)")
        
        # Verificar detección esperada
        expected_structural = "Antología Rubén Darío"
        unexpected_structural = "Página"  # No debería detectarse (solo 70%)
        
        success = True
        
        if expected_structural in structural_elements:
            print(f"\n✅ CORRECTO: '{expected_structural}' detectado como estructural")
        else:
            print(f"\n❌ ERROR: '{expected_structural}' NO detectado como estructural")
            success = False
        
        # Verificar que elementos con frecuencia menor no se detecten
        has_page_elements = any("Página" in elem for elem in structural_elements)
        if not has_page_elements:
            print(f"✅ CORRECTO: Elementos 'Página N' NO detectados (frecuencia 70% < umbral 90%)")
        else:
            print(f"⚠️ ATENCIÓN: Algunos elementos 'Página N' fueron detectados")
        
        # Filtrar elementos estructurales
        filtered_blocks = preprocessor._filter_structural_elements(simulated_blocks, structural_elements)
        
        print(f"\n📊 FILTRADO:")
        print(f"  - Bloques originales: {len(simulated_blocks)}")
        print(f"  - Bloques filtrados: {len(filtered_blocks)}")
        print(f"  - Bloques eliminados: {len(simulated_blocks) - len(filtered_blocks)}")
        
        # Verificar que el contenido poético se preservó
        filtered_texts = [b.get('text', '') for b in filtered_blocks]
        preserved_poems = ["MARCHA TRIUNFAL", "SOUVENIR", "CANTARES DEL CARDÓN", "POEMA 1"]
        preserved_count = sum(1 for poem in preserved_poems if poem in filtered_texts)
        
        print(f"\n📝 CONTENIDO PRESERVADO:")
        print(f"  - Poemas preservados: {preserved_count}/{len(preserved_poems)}")
        for poem in preserved_poems:
            status = "✅" if poem in filtered_texts else "❌"
            print(f"    {status} '{poem}'")
        
        # Verificar que elementos estructurales fueron eliminados
        structural_removed = expected_structural not in filtered_texts
        
        if structural_removed and preserved_count >= 3:
            print(f"\n🎉 FILTRADO ESTRUCTURAL EXITOSO:")
            print(f"   - Elementos estructurales eliminados")
            print(f"   - Contenido poético preservado")
            return True
        else:
            print(f"\n❌ PROBLEMAS EN EL FILTRADO:")
            if not structural_removed:
                print(f"   - Elementos estructurales NO eliminados")
            if preserved_count < 3:
                print(f"   - Demasiado contenido poético eliminado")
            return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_case_thresholds():
    """
    Testa diferentes umbrales de detección.
    """
    print("\n🔧 TEST: UMBRALES DE DETECCIÓN")
    print("=" * 50)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Documento con elemento que aparece en 85% de páginas
        test_blocks = []
        for page in range(1, 21):  # 20 páginas
            # Elemento que aparece en 17/20 páginas (85%)
            if page <= 17:
                test_blocks.append({
                    "text": "Header 85%",
                    "metadata": {"page_number": page}
                })
            
            # Contenido normal
            test_blocks.append({
                "text": f"Contenido página {page}",
                "metadata": {"page_number": page}
            })
        
        # Test con umbral 90% (NO debería detectar)
        config_90 = {
            'filter_structural_elements': True,
            'structural_frequency_threshold': 0.9,  # 90%
            'min_pages_for_structural_detection': 5,
        }
        
        preprocessor_90 = CommonBlockPreprocessor(config=config_90)
        structural_90 = preprocessor_90._detect_structural_elements(test_blocks)
        
        # Test con umbral 80% (SÍ debería detectar)
        config_80 = {
            'filter_structural_elements': True,
            'structural_frequency_threshold': 0.8,  # 80%
            'min_pages_for_structural_detection': 5,
        }
        
        preprocessor_80 = CommonBlockPreprocessor(config=config_80)
        structural_80 = preprocessor_80._detect_structural_elements(test_blocks)
        
        print(f"📊 RESULTADOS UMBRALES:")
        print(f"  - Elemento aparece en 17/20 páginas (85%)")
        print(f"  - Umbral 90%: {len(structural_90)} elementos detectados")
        print(f"  - Umbral 80%: {len(structural_80)} elementos detectados")
        
        # Verificar comportamiento esperado
        success = True
        
        if len(structural_90) == 0:
            print(f"  ✅ Umbral 90%: Correcto (85% < 90%, no detecta)")
        else:
            print(f"  ❌ Umbral 90%: Error (detectó elemento debajo del umbral)")
            success = False
        
        if len(structural_80) > 0 and "Header 85%" in structural_80:
            print(f"  ✅ Umbral 80%: Correcto (85% > 80%, sí detecta)")
        else:
            print(f"  ❌ Umbral 80%: Error (no detectó elemento arriba del umbral)")
            success = False
        
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_simulated_anthology()
    success2 = test_edge_case_thresholds()
    
    if success1 and success2:
        print(f"\n🎉 TODOS LOS TESTS PASARON - FILTRADO ESTRUCTURAL PERFECTO")
        print(f"\n📋 RESUMEN:")
        print(f"   ✅ Detección de elementos estructurales (>90% páginas)")
        print(f"   ✅ Filtrado correcto de headers/footers repetitivos")
        print(f"   ✅ Preservación de contenido poético")
        print(f"   ✅ Umbrales de frecuencia funcionando")
        print(f"\n🚀 READY: La funcionalidad está lista para uso en producción")
        exit(0)
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON")
        exit(1) 