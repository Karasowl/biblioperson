#!/usr/bin/env python3
"""
🔧 TEST: VERIFICAR MARCHA TRIUNFAL
Verifica que el poema "MARCHA TRIUNFAL" se detecta como una sola unidad.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

def test_marcha_triunfal():
    """
    Testa que el texto "MARCHA TRIUNFAL" se segmente correctamente.
    """
    print("🔧 PROBANDO SEGMENTACIÓN DE 'MARCHA TRIUNFAL'")
    print("=" * 60)
    
    try:
        from processing.segmenters.verse_segmenter import VerseSegmenter
        
        # Texto de prueba basado en el ejemplo del usuario
        test_blocks = [
            {"text": "MARCHA TRIUNFAL"},
            {"text": "Ya viene el cortejo!"},
            {"text": "Ya viene el cortejo! Ya se oyen los claros clarines."},
            {"text": "La espada se anuncia con vivo reflejo;"},
            {"text": "ya viene, oro y hierro, el cortejo de los paladines."},
            {"text": "Ya pasa debajo los arcos ornados de blancas"},
            {"text": "Minervas y Martes,"},
            {"text": "los arcos triunfales en donde las Famas erigen sus"},
            {"text": "largas trompetas,"},
            {"text": "la gloria solemne de los estandartes"},
            {"text": "llevados por manos robustas de heroicos atletas."},
        ]
        
        print(f"📝 Entrada: {len(test_blocks)} bloques")
        for i, block in enumerate(test_blocks):
            print(f"  [{i+1}] {block['text'][:50]}{'...' if len(block['text']) > 50 else ''}")
        
        # Crear segmentador
        segmenter = VerseSegmenter()
        
        # Segmentar
        segments = segmenter.segment(test_blocks)
        
        print(f"\n📊 RESULTADOS:")
        print(f"  - Segmentos detectados: {len(segments)}")
        
        for i, segment in enumerate(segments):
            segment_text = segment.get('text', '')
            segment_type = segment.get('type', 'unknown')
            print(f"  [{i+1}] {segment_type}: {segment_text[:100]}{'...' if len(segment_text) > 100 else ''}")
        
        # Verificación
        if len(segments) == 1:
            first_segment = segments[0]
            if first_segment.get('type') == 'poem' and 'MARCHA TRIUNFAL' in first_segment.get('text', ''):
                print("\n✅ SUCCESS: 'MARCHA TRIUNFAL' detectado como UN SOLO POEMA")
                return True
            else:
                print(f"\n❌ FAIL: Tipo incorrecto o título faltante")
                print(f"    - Tipo: {first_segment.get('type')}")
                print(f"    - Contiene título: {'MARCHA TRIUNFAL' in first_segment.get('text', '')}")
                return False
        else:
            print(f"\n❌ FAIL: Se detectaron {len(segments)} segmentos en lugar de 1")
            print("    - Esto indica que el poema se está dividiendo incorrectamente")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_problematic_lines():
    """
    Testa líneas específicas que estaban causando problemas.
    """
    print("\n🔧 PROBANDO LÍNEAS PROBLEMÁTICAS INDIVIDUALES")
    print("=" * 60)
    
    try:
        from processing.segmenters.verse_segmenter import VerseSegmenter
        
        # Crear instancia para acceder a métodos internos
        segmenter = VerseSegmenter()
        
        # Líneas que NO deberían ser detectadas como títulos
        problematic_lines = [
            "La espada se anuncia con vivo reflejo;",
            "ya viene, oro y hierro, el cortejo de los paladines.",
            "los arcos triunfales en donde las Famas erigen sus",
            "la gloria solemne de los estandartes",
            "llevados por manos robustas de heroicos atletas.",
        ]
        
        # Líneas que SÍ deberían ser detectadas como títulos
        valid_titles = [
            "MARCHA TRIUNFAL",
            "SOUVENIR", 
            "CANTARES DE EL CARDÓN",
            "Poema 1",
            "Poema 15"
        ]
        
        print("🚫 Verificando que VERSOS NO se detecten como títulos:")
        all_good = True
        for line in problematic_lines:
            block = {"text": line}
            is_title = segmenter._is_title_block(block)
            status = "❌ DETECTADO COMO TÍTULO" if is_title else "✅ Rechazado correctamente"
            print(f"  {status}: '{line}'")
            if is_title:
                all_good = False
        
        print("\n✅ Verificando que TÍTULOS SÍ se detecten como títulos:")
        for line in valid_titles:
            block = {"text": line}
            is_title = segmenter._is_title_block(block)
            status = "✅ DETECTADO COMO TÍTULO" if is_title else "❌ Rechazado incorrectamente"
            print(f"  {status}: '{line}'")
            if not is_title:
                all_good = False
        
        if all_good:
            print("\n🎉 TODOS LOS TESTS DE LÍNEAS INDIVIDUALES PASARON")
            return True
        else:
            print("\n❌ ALGUNOS TESTS DE LÍNEAS INDIVIDUALES FALLARON")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_marcha_triunfal()
    success2 = test_problematic_lines()
    
    if success1 and success2:
        print(f"\n🎉 TODOS LOS TESTS PASARON - PROBLEMA SOLUCIONADO")
        exit(0)
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON - REVISAR IMPLEMENTACIÓN")
        exit(1) 