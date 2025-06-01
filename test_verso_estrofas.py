#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar detección de estrofas
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def test_estrofas():
    print("=== TEST: DETECCIÓN DE ESTROFAS ===")
    
    # Crear segmentador con configuración de prueba
    config = {
        'thresholds': {
            'min_empty_between_stanzas': 2,
            'max_empty_between_stanzas': 3,
            'confidence_threshold': 0.4
        }
    }
    segmenter = VerseSegmenter(config)
    
    # Simular los versos como los procesaría el algoritmo
    # Según ALGORITMOS_PROPUESTOS.md: estrofas se separan con 2-3 líneas vacías
    verses = [
        "Tierna melancolía que en noches de consuelo",
        "Esconde el alma rota pidiéndose perdón", 
        "Si acaso por ternura nos expias el cielo",
        "De sombras mis acciones de mal el corazón",
        "",  # Primera línea vacía
        "",  # Segunda línea vacía - esto separa estrofas según el algoritmo
        "Cuan fascinante velo y abrumadora holgura",
        "El vals de los quehaceres, de la conversación,"
    ]
    
    print(f"📝 Versos de entrada ({len(verses)}):")
    for i, verso in enumerate(verses):
        if verso.strip():
            print(f"   {i+1}. {verso}")
        else:
            print(f"   {i+1}. [LÍNEA VACÍA]")
    
    print(f"\n📏 Configuración del segmentador:")
    print(f"   min_empty_between_stanzas: {segmenter.min_empty_between_stanzas}")
    print(f"   max_empty_between_stanzas: {segmenter.max_empty_between_stanzas}")
    
    # Probar conteo de estrofas
    stanza_count = segmenter.count_stanzas(verses)
    print(f"\n🔢 Estrofas detectadas: {stanza_count}")
    
    # Probar cálculo de confianza
    confidence = segmenter._calculate_confidence(verses)
    print(f"📊 Confianza calculada: {confidence:.2f}")
    
    # Verificar resultado esperado
    expected_stanzas = 2  # Debería detectar 2 estrofas
    if stanza_count == expected_stanzas:
        print(f"✅ CORRECTO: Se detectaron {stanza_count} estrofas (esperado: {expected_stanzas})")
        return True
    else:
        print(f"❌ ERROR: Se detectaron {stanza_count} estrofas, esperado: {expected_stanzas}")
        return False

def test_verse_patterns():
    print("🎯 TEST: VerseSegmenter MEJORADO con datos de prueba")
    
    # Simular bloques de ejemplo con los patrones que agregamos
    test_blocks = [
        # 1. Títulos explícitos entre comillas
        {'text': '"Cementerio"', 'page': 1},
        {'text': 'Aquí yacen los sueños perdidos', 'page': 1},
        {'text': 'en tierras de olvido', 'page': 1},
        
        # 2. Números romanos como títulos
        {'text': 'XV', 'page': 2},
        {'text': 'La luna se esconde', 'page': 2},
        {'text': 'tras las nubes grises', 'page': 2},
        
        # 3. Listas numeradas
        {'text': '23. Mi táctica', 'page': 3},
        {'text': 'Mi táctica es', 'page': 3},
        {'text': 'mirarte', 'page': 3},
        
        # 4. Separadores visuales
        {'text': '***', 'page': 4},
        {'text': 'Un nuevo amanecer', 'page': 4},
        {'text': 'se alza en el horizonte', 'page': 4},
        
        # 5. Títulos sin comillas - capitalizados y cortos
        {'text': 'Esperanza', 'page': 5},
        {'text': 'Brilla la esperanza', 'page': 5},
        {'text': 'como estrella en la noche', 'page': 5},
        
        # 6. Título después de texto muy largo (detección por contexto)
        {'text': 'Esta es una línea muy larga que simula el final de un poema anterior con muchas palabras para alcanzar el límite de 300 caracteres que define un texto largo según nuestro algoritmo de detección contextual mejorado que busca patrones específicos en el texto', 'page': 6},
        {'text': 'País Verde', 'page': 6},
        {'text': 'Verde como la hierba', 'page': 6},
        
        # 7. Título en nueva página
        {'text': 'Responso', 'page': 7},  # página nueva
        {'text': 'Por los que se fueron', 'page': 7},
        {'text': 'sin decir adiós', 'page': 7},
        
        # 8. Headings detectados por PDF
        {'text': 'Mar', 'is_heading': True, 'page': 8},
        {'text': 'El mar susurra secretos', 'page': 8},
        {'text': 'al oído del viento', 'page': 8},
    ]
    
    print(f"\n1️⃣ PASO 1: Datos de prueba")
    print(f"   📦 Bloques de prueba: {len(test_blocks)}")
    print(f"   🎭 Patrones incluidos:")
    print(f"      • Títulos entre comillas")
    print(f"      • Números romanos")  
    print(f"      • Listas numeradas")
    print(f"      • Separadores visuales")
    print(f"      • Títulos capitalizados")
    print(f"      • Detección por contexto")
    print(f"      • Nuevas páginas")
    print(f"      • Headings PDF")
    
    print(f"\n2️⃣ PASO 2: Segmentar con VerseSegmenter MEJORADO")
    
    # Aplicar VerseSegmenter mejorado
    segmenter = VerseSegmenter({})
    segments = segmenter.segment(test_blocks)
    
    print(f"\n✅ RESULTADOS:")
    print(f"   🎯 Poemas detectados: {len(segments)}")
    print(f"   🎯 Esperados: 8 poemas")
    
    if len(segments) == 8:
        print(f"   ✅ PERFECTO: Detectados todos los patrones")
    elif len(segments) >= 6:
        print(f"   ✅ BUENO: Mayoría de patrones detectados")
    elif len(segments) >= 4:
        print(f"   ⚠️  REGULAR: Solo algunos patrones funcionan")
    else:
        print(f"   ❌ PROBLEMA: Muy pocos patrones detectados")
    
    print(f"\n3️⃣ PASO 3: Análisis detallado de cada poema")
    
    for i, segment in enumerate(segments):
        title = segment.get('title', 'Sin título')
        verse_count = segment.get('verse_count', 0)
        text_lines = len(segment.get('text', '').split('\n'))
        
        print(f"   [{i+1}] '{title}' ({verse_count} versos, {text_lines} líneas totales)")
    
    print(f"\n4️⃣ PASO 4: Verificar formato de salida")
    
    if segments:
        first_segment = segments[0]
        print(f"   🔍 Estructura del primer segmento:")
        print(f"      📋 Keys: {list(first_segment.keys())}")
        print(f"      🏷️  type: '{first_segment.get('type', 'NO_ENCONTRADO')}'")
        print(f"      📝 title: '{first_segment.get('title', 'NO_ENCONTRADO')}'")
        print(f"      📄 text length: {len(first_segment.get('text', ''))}")
        
        # Verificar formato correcto
        if (first_segment.get('type') == 'poem' and 
            'title' in first_segment and 
            'text' in first_segment):
            print(f"   ✅ FORMATO CORRECTO: Compatible con ProfileManager")
        else:
            print(f"   ❌ FORMATO INCORRECTO: Incompatible con ProfileManager")
    
    return {
        'total_poems': len(segments),
        'expected_poems': 8,
        'success_rate': len(segments) / 8 * 100,
        'segments': segments
    }

if __name__ == "__main__":
    success = test_estrofas()
    if success:
        print("\n🎉 TEST EXITOSO: Detección de estrofas funciona correctamente")
    else:
        print("\n❌ TEST FALLIDO: Detección de estrofas necesita corrección")

    resultado = test_verse_patterns()
    
    print(f"\n🏁 RESUMEN FINAL:")
    print(f"   🎯 Poemas detectados: {resultado['total_poems']}")
    print(f"   📈 Tasa de éxito: {resultado['success_rate']:.1f}%")
    
    if resultado['success_rate'] >= 87.5:  # 7/8
        print(f"   🎉 EXCELENTE: VerseSegmenter mejorado funcionando")
    elif resultado['success_rate'] >= 75:  # 6/8
        print(f"   👍 BUENO: Mejoras significativas confirmadas")
    else:
        print(f"   🔧 NECESITA AJUSTES: Revisar patrones de detección") 