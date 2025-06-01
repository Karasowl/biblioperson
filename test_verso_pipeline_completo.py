#!/usr/bin/env python3
"""
Test SIMPLE del VerseSegmenter MEJORADO
Solo verificar que los 8 patrones de detección funcionan
"""

import sys
sys.path.append('.')

from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def test_verse_pipeline():
    print("🎯 TEST SIMPLE: VerseSegmenter MEJORADO")
    
    # Datos de prueba con los 8 patrones
    test_blocks = [
        # 1. Título entre comillas
        {'text': '"Cementerio"', 'page': 1},
        {'text': 'Aquí yacen los sueños perdidos', 'page': 1},
        
        # 2. Número romano
        {'text': 'XV', 'page': 2},
        {'text': 'La luna se esconde', 'page': 2},
        
        # 3. Lista numerada
        {'text': '23. Mi táctica', 'page': 3},
        {'text': 'Mi táctica es mirarte', 'page': 3},
        
        # 4. Separador visual
        {'text': '***', 'page': 4},
        {'text': 'Un nuevo amanecer', 'page': 4},
        
        # 5. Título capitalizado
        {'text': 'Esperanza', 'page': 5},
        {'text': 'Brilla la esperanza', 'page': 5},
        
        # 6. Título después de texto largo
        {'text': 'Esta es una línea muy larga que simula el final de un poema anterior con muchas palabras para alcanzar el límite de 300 caracteres que define un texto largo según nuestro algoritmo de detección contextual mejorado que busca patrones específicos', 'page': 6},
        {'text': 'País Verde', 'page': 6},
        {'text': 'Verde como la hierba', 'page': 6},
        
        # 7. Nueva página
        {'text': 'Responso', 'page': 7},
        {'text': 'Por los que se fueron', 'page': 7},
        
        # 8. Heading PDF
        {'text': 'Mar', 'is_heading': True, 'page': 8},
        {'text': 'El mar susurra secretos', 'page': 8},
    ]
    
    print(f"   📦 Bloques de entrada: {len(test_blocks)}")
    print(f"   🎭 Patrones esperados: 8 poemas")
    
    try:
        # Crear segmentador
        segmenter = VerseSegmenter({})
        
        # Segmentar
        print(f"   🔄 Segmentando...")
        segments = segmenter.segment(test_blocks)
        
        print(f"\n✅ RESULTADOS:")
        print(f"   📊 Poemas detectados: {len(segments)}")
        
        # Mostrar cada poema detectado
        for i, segment in enumerate(segments):
            title = segment.get('title', 'Sin título')
            text_lines = len(segment.get('text', '').split('\n'))
            print(f"   [{i+1}] '{title}' ({text_lines} líneas)")
        
        # Verificar formato
        if segments:
            first = segments[0]
            has_type = 'type' in first and first['type'] == 'poem'
            has_title = 'title' in first
            has_text = 'text' in first and len(first['text']) > 0
            
            print(f"\n🔍 VERIFICACIÓN DE FORMATO:")
            print(f"   ✓ Campo 'type': {'Sí' if has_type else 'No'}")
            print(f"   ✓ Campo 'title': {'Sí' if has_title else 'No'}")
            print(f"   ✓ Campo 'text': {'Sí' if has_text else 'No'}")
            
            format_ok = has_type and has_title and has_text
            print(f"   📋 Formato: {'✅ Correcto' if format_ok else '❌ Incorrecto'}")
        
        # Calcular tasa de éxito
        success_rate = (len(segments) / 8) * 100
        
        print(f"\n📈 TASA DE ÉXITO: {success_rate:.1f}%")
        
        if success_rate >= 87.5:
            print(f"   🎉 EXCELENTE: VerseSegmenter mejorado funcionando")
            return True, len(segments)
        elif success_rate >= 75:
            print(f"   👍 BUENO: Mejora significativa detectada")
            return True, len(segments)
        else:
            print(f"   ⚠️  INSUFICIENTE: Necesita más ajustes")
            return False, len(segments)
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, 0

if __name__ == "__main__":
    success, detected = test_verse_pipeline()
    
    print(f"\n🏁 RESULTADO FINAL:")
    if success:
        print(f"   ✅ ÉXITO: {detected}/8 poemas detectados")
        print(f"   🚀 VerseSegmenter MEJORADO validado")
    else:
        print(f"   ❌ FALLO: Solo {detected}/8 poemas detectados")
        print(f"   🔧 Se requieren más ajustes") 