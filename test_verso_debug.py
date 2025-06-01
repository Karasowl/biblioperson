#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test debug específico para el perfil verso
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.loaders.docx_loader import DocxLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
import logging

# Configurar logging para ver los debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_verso_debug():
    print("=== TEST DEBUG: PERFIL VERSO ===")
    
    # Crear datos de prueba que simulan un poema simple
    test_blocks = [
        {
            "text": "Adiós",
            "page": 1,
            "bbox": [72, 720, 300, 750],
            "font_size": 16,
            "font_weight": "bold",
            "is_heading": True
        },
        {
            "text": "Tierna melancolía que en noches de consuelo",
            "page": 1,
            "bbox": [72, 680, 400, 700],
            "font_size": 12,
            "font_weight": "normal"
        },
        {
            "text": "Esconde el alma rota pidiéndose perdón",
            "page": 1,
            "bbox": [72, 660, 400, 680],
            "font_size": 12,
            "font_weight": "normal"
        },
        {
            "text": "Si acaso por ternura nos expias el cielo",
            "page": 1,
            "bbox": [72, 640, 400, 660],
            "font_size": 12,
            "font_weight": "normal"
        },
        {
            "text": "De sombras mis acciones de mal el corazón",
            "page": 1,
            "bbox": [72, 620, 400, 640],
            "font_size": 12,
            "font_weight": "normal"
        },
        {
            "text": "",  # Línea vacía
            "page": 1,
            "bbox": [72, 600, 400, 620],
            "font_size": 12,
            "font_weight": "normal"
        },
        {
            "text": "Cuan fascinante velo y abrumadora holgura",
            "page": 1,
            "bbox": [72, 580, 400, 600],
            "font_size": 12,
            "font_weight": "normal"
        },
        {
            "text": "El vals de los quehaceres, de la conversación,",
            "page": 1,
            "bbox": [72, 560, 400, 580],
            "font_size": 12,
            "font_weight": "normal"
        }
    ]
    
    document_metadata = {
        'filename': 'test_poema.docx',
        'source_type': 'docx'
    }
    
    # Simular el pipeline completo manualmente
    print("📤 Procesando bloques con perfil VERSO...")
    
    # 1. Cargar configuración del perfil verso
    profile_manager = ProfileManager()
    verso_config = profile_manager.get_profile("verso")
    print(f"📋 Configuración del perfil verso cargada")
    print(f"📋 Config completa: {verso_config}")
    
    # 2. Preprocessor 
    preprocessor_config = verso_config.get('pre_processor_config', {})
    preprocessor = CommonBlockPreprocessor(preprocessor_config)
    processed_blocks, processed_metadata = preprocessor.process(test_blocks, document_metadata)
    print(f"🔧 Preprocessor: {len(test_blocks)} → {len(processed_blocks)} bloques")
    
    # 3. Segmentador 
    segmenter_config = verso_config.get('segmenter_config', {})
    print(f"🎵 Config del segmentador: {segmenter_config}")
    
    # Crear segmentador con debug
    segmenter = VerseSegmenter(segmenter_config)
    print(f"🎵 Segmentador de verso creado")
    print(f"🎵 Umbral de confianza: {segmenter.confidence_threshold}")
    print(f"🎵 Max verse length: {segmenter.max_verse_length}")
    
    # Probar funciones individuales primero
    print("\n=== ANÁLISIS DE BLOQUES INDIVIDUALES ===")
    for i, block in enumerate(processed_blocks):
        text = block.get('text', '').strip()
        if text:
            is_verse = segmenter.is_verse(text)
            has_title = segmenter.has_title_format(block)
            print(f"Bloque {i}: '{text[:50]}...' -> verso={is_verse}, título={has_title}")
    
    # Ahora segmentar
    result = segmenter.segment(processed_blocks, processed_metadata)
    print(f"\n✂️ Segmentador: {len(processed_blocks)} → {len(result)} segmentos")
    
    print("\n📊 RESULTADOS:")
    print(f"   Total segmentos: {len(result)}")
    
    for i, segment in enumerate(result, 1):
        segment_type = segment.get('type', 'unknown')
        
        if segment_type == 'poem':
            title = segment.get('title', 'Sin título')
            verses_count = segment.get('verses_count', 0)
            stanzas = segment.get('stanzas', 0)
            confidence = segment.get('confidence', 0.0)
            print(f"   [{i}] POEMA: {title}")
            print(f"       📈 Versos: {verses_count}, Estrofas: {stanzas}, Confianza: {confidence:.2f}")
            
            # Mostrar algunos versos
            numbered_verses = segment.get('numbered_verses', [])
            print(f"       🎵 Versos numerados ({len(numbered_verses)}):")
            for j, verse in enumerate(numbered_verses[:5]):  # Solo los primeros 5
                verse_text = verse.get('text', '')
                verse_num = verse.get('verse_number')
                if verse_text:
                    print(f"          {verse_num}. {verse_text}")
        else:
            # Probar diferentes campos de texto posibles
            text_content = segment.get('text', segment.get('texto_segmento', ''))
            text = text_content[:60] + "..." if len(text_content) > 60 else text_content
            print(f"   [{i}] {segment_type.upper()}: {text}")
    
    print(f"\n🎯 VERIFICACIÓN:")
    
    # Verificar que se detectaron versos
    poem_segments = [s for s in result if s.get('type') == 'poem']
    if poem_segments:
        print(f"   ✅ {len(poem_segments)} poema(s) detectado(s)")
        for poem in poem_segments:
            print(f"   ✅ Título: {poem.get('title')}")
            print(f"   ✅ Versos: {poem.get('verses_count')}")
    else:
        print(f"   ❌ NO se detectaron poemas")
    
    return len(poem_segments) > 0

def test_individual_patterns():
    print("🔍 DEBUG: Testeo individual de patrones de VerseSegmenter")
    
    # Crear segmentador
    segmenter = VerseSegmenter({})
    
    # Test cases individuales
    test_cases = [
        # 1. Títulos entre comillas
        {'name': 'Título entre comillas', 'block': {'text': '"Cementerio"', 'page': 1}},
        
        # 2. Números romanos
        {'name': 'Número romano', 'block': {'text': 'XV', 'page': 1}},
        
        # 3. Listas numeradas
        {'name': 'Lista numerada', 'block': {'text': '23. Mi táctica', 'page': 1}},
        
        # 4. Separadores visuales
        {'name': 'Separador visual', 'block': {'text': '***', 'page': 1}},
        
        # 5. Títulos capitalizados
        {'name': 'Título capitalizado', 'block': {'text': 'Esperanza', 'page': 1}},
        
        # 6. Headings PDF
        {'name': 'Heading PDF', 'block': {'text': 'Mar', 'is_heading': True, 'page': 1}},
    ]
    
    print(f"\n📋 PROBANDO {len(test_cases)} PATRONES INDIVIDUALES:\n")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        name = test_case['name']
        block = test_case['block']
        text = block['text']
        
        print(f"   [{i}] {name}: '{text}'")
        
        # Probar detección directa
        try:
            is_main_title = segmenter._is_main_title(block, 0, [block])
            status = "✅ DETECTADO" if is_main_title else "❌ NO DETECTADO"
            
            print(f"       Resultado: {status}")
            results.append({'name': name, 'detected': is_main_title, 'text': text})
            
        except Exception as e:
            print(f"       ❌ ERROR: {e}")
            results.append({'name': name, 'detected': False, 'text': text, 'error': str(e)})
        
        print()
    
    # Resumen
    detected_count = sum(1 for r in results if r['detected'])
    total_count = len(results)
    
    print(f"📊 RESUMEN DE DETECCIÓN INDIVIDUAL:")
    print(f"   🎯 Detectados: {detected_count}/{total_count}")
    print(f"   📈 Tasa: {(detected_count/total_count)*100:.1f}%")
    
    return results, detected_count, total_count

def test_full_segmentation():
    print(f"\n🔄 TEST: Segmentación completa con patrones mezclados")
    
    # Datos mezclados
    mixed_blocks = [
        {'text': '"Cementerio"', 'page': 1},           # Título 1
        {'text': 'Verso del cementerio', 'page': 1},
        
        {'text': 'XV', 'page': 2},                     # Título 2  
        {'text': 'Verso del número romano', 'page': 2},
        
        {'text': '23. Mi táctica', 'page': 3},         # Título 3
        {'text': 'Verso de la táctica', 'page': 3},
        
        {'text': '***', 'page': 4},                    # Título 4
        {'text': 'Verso del separador', 'page': 4},
        
        {'text': 'Esperanza', 'page': 5},              # Título 5
        {'text': 'Verso de la esperanza', 'page': 5},
        
        {'text': 'Mar', 'is_heading': True, 'page': 6}, # Título 6
        {'text': 'Verso del mar', 'page': 6},
    ]
    
    print(f"   📦 Bloques de entrada: {len(mixed_blocks)}")
    print(f"   🎭 Poemas esperados: 6")
    
    # DEBUG: Verificar detección de títulos manualmente
    segmenter = VerseSegmenter({})
    print(f"\n   🔍 ANÁLISIS BLOQUE POR BLOQUE:")
    for i, block in enumerate(mixed_blocks):
        text = block.get('text', '')
        is_title = segmenter._is_main_title(block, i, mixed_blocks)
        print(f"      [{i}] '{text}' → {'📍 TÍTULO' if is_title else '📝 Contenido'}")
    
    print(f"\n   🔄 EJECUTANDO SEGMENTACIÓN:")
    segments = segmenter.segment(mixed_blocks)
    
    print(f"   📊 Poemas detectados: {len(segments)}")
    
    for i, segment in enumerate(segments, 1):
        title = segment.get('title', 'Sin título')
        text_lines = len(segment.get('text', '').split('\n'))
        print(f"   [{i}] '{title}' ({text_lines} líneas)")
    
    success_rate = (len(segments) / 6) * 100
    print(f"   📈 Tasa de éxito: {success_rate:.1f}%")
    
    return len(segments), success_rate

if __name__ == "__main__":
    print("=" * 60)
    
    # Test individual
    individual_results, detected, total = test_individual_patterns()
    
    # Test completo  
    full_detected, full_rate = test_full_segmentation()
    
    print(f"\n🏁 DIAGNÓSTICO FINAL:")
    print(f"   🔍 Detección individual: {detected}/{total} ({(detected/total)*100:.1f}%)")
    print(f"   🔄 Segmentación completa: {full_detected}/6 ({full_rate:.1f}%)")
    
    if detected >= 5 and full_detected >= 5:
        print(f"   ✅ BUEN FUNCIONAMIENTO: Patrones trabajando correctamente")
    elif detected >= 3 or full_detected >= 3:
        print(f"   ⚠️  FUNCIONAMIENTO PARCIAL: Algunos patrones fallan")
        print(f"   🔧 Revisar patrones que no funcionan:")
        for result in individual_results:
            if not result['detected']:
                error_msg = f" (Error: {result.get('error', 'Unknown')})" if 'error' in result else ""
                print(f"      • {result['name']}: '{result['text']}'{error_msg}")
    else:
        print(f"   ❌ FALLO CRÍTICO: La mayoría de patrones no funcionan")
        print(f"   🚨 Se requiere revisión completa del código")
    
    print("=" * 60) 