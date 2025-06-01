#!/usr/bin/env python3
"""
🔧 TEST SIMPLE: FILTRADO ESTRUCTURAL
Test simplificado para verificar que funciona el filtrado de elementos estructurales.
"""

import sys
import os
sys.path.append('dataset')

def test_simple():
    print("🔧 TEST SIMPLE - FILTRADO ESTRUCTURAL")
    print("=" * 50)
    
    try:
        from processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        # Crear documento de prueba con elemento repetitivo
        test_blocks = [
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 1}},
            {"text": "MARCHA TRIUNFAL", "metadata": {"page_number": 1}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 2}},
            {"text": "Contenido página 2", "metadata": {"page_number": 2}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 3}},
            {"text": "Contenido página 3", "metadata": {"page_number": 3}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 4}},
            {"text": "Contenido página 4", "metadata": {"page_number": 4}},
            {"text": "Antología Rubén Darío", "metadata": {"page_number": 5}},
            {"text": "Contenido página 5", "metadata": {"page_number": 5}},
        ]
        
        print(f"📝 {len(test_blocks)} bloques, 'Antología Rubén Darío' en 5/5 páginas (100%)")
        
        # Crear preprocessor
        preprocessor = CommonBlockPreprocessor()
        
        # Test 1: Detectar elementos estructurales
        structural = preprocessor._detect_structural_elements(test_blocks)
        print(f"\n📊 Elementos estructurales detectados: {len(structural)}")
        for elem in structural:
            print(f"  🚫 '{elem}'")
        
        # Test 2: Filtrar elementos
        filtered = preprocessor._filter_structural_elements(test_blocks, structural)
        print(f"\n📊 Filtrado: {len(test_blocks)} → {len(filtered)} bloques")
        
        # Test 3: Process completo
        processed, metadata = preprocessor.process(test_blocks, {})
        print(f"\n📊 Process completo: {len(test_blocks)} → {len(processed)} bloques")
        
        # Verificar resultado
        processed_texts = [block.get('text', '') for block in processed]
        if "Antología Rubén Darío" not in processed_texts:
            print("\n✅ SUCCESS: Elemento estructural eliminado correctamente")
            return True
        else:
            print("\n❌ FAIL: Elemento estructural NO eliminado")
            return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    if success:
        print("\n🎉 TEST EXITOSO")
        exit(0)
    else:
        print("\n❌ TEST FALLIDO")
        exit(1) 