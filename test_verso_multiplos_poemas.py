#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para múltiples poemas en un archivo (como el caso real del usuario)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
import logging

# Configurar logging solo para errores críticos
logging.basicConfig(level=logging.ERROR)

def test_multiplos_poemas():
    print("=== TEST: MÚLTIPLES POEMAS EN UN ARCHIVO ===")
    
    # Simular un archivo con múltiples poemas como los que tendría el usuario
    test_blocks = [
        # PRIMER POEMA
        {
            "text": "Adiós",
            "page": 1,
            "is_heading": True,
            "font_size": 16,
            "font_weight": "bold"
        },
        {
            "text": "Tierna melancolía que en noches de consuelo",
            "page": 1,
            "font_size": 12
        },
        {
            "text": "Esconde el alma rota pidiéndose perdón",
            "page": 1,
            "font_size": 12
        },
        {
            "text": "",  # Línea vacía
            "page": 1
        },
        {
            "text": "Si acaso por ternura nos expias el cielo",
            "page": 1,
            "font_size": 12
        },
        {
            "text": "De sombras mis acciones de mal el corazón",
            "page": 1,
            "font_size": 12
        },
        
        # SEPARACIÓN ENTRE POEMAS (varias líneas vacías)
        {
            "text": "",
            "page": 1
        },
        {
            "text": "",
            "page": 1
        },
        {
            "text": "",
            "page": 1
        },
        
        # SEGUNDO POEMA
        {
            "text": "Esperanza",
            "page": 2,
            "is_heading": True,
            "font_size": 16,
            "font_weight": "bold"
        },
        {
            "text": "Brilla la luz en el horizonte",
            "page": 2,
            "font_size": 12
        },
        {
            "text": "Como promesa de un nuevo día",
            "page": 2,
            "font_size": 12
        },
        {
            "text": "",  # Línea vacía dentro del poema
            "page": 2
        },
        {
            "text": "Que trae consigo dulce esperanza",
            "page": 2,
            "font_size": 12
        },
        {
            "text": "Y borra las penas del ayer",
            "page": 2,
            "font_size": 12
        }
    ]
    
    document_metadata = {
        'filename': 'mis_poemas.docx',
        'source_type': 'docx'
    }
    
    print(f"📄 Simulando archivo con {len(test_blocks)} bloques")
    
    # Usar el perfil verso actualizado
    profile_manager = ProfileManager()
    verso_config = profile_manager.get_profile("verso")
    print(f"📋 Configuración verso cargada (umbral confianza: {verso_config.get('segmenter_config', {}).get('thresholds', {}).get('confidence_threshold', 'N/A')})")
    
    # Preprocessor 
    preprocessor_config = verso_config.get('pre_processor_config', {})
    preprocessor = CommonBlockPreprocessor(preprocessor_config)
    processed_blocks, processed_metadata = preprocessor.process(test_blocks, document_metadata)
    print(f"🔧 Preprocessor: {len(test_blocks)} → {len(processed_blocks)} bloques")
    
    # Segmentador 
    segmenter_config = verso_config.get('segmenter_config', {})
    segmenter = VerseSegmenter(segmenter_config)
    result = segmenter.segment(processed_blocks, processed_metadata)
    
    print(f"\n✂️ Segmentador: {len(processed_blocks)} → {len(result)} segmentos")
    
    print("\n📊 RESULTADOS:")
    poems_found = 0
    
    for i, segment in enumerate(result, 1):
        segment_type = segment.get('type', 'unknown')
        
        if segment_type == 'poem':
            poems_found += 1
            title = segment.get('title', 'Sin título')
            verses_count = segment.get('verses_count', 0)
            stanzas = segment.get('stanzas', 0)
            confidence = segment.get('confidence', 0.0)
            print(f"   [{i}] POEMA #{poems_found}: {title}")
            print(f"       📈 Versos: {verses_count}, Estrofas: {stanzas}, Confianza: {confidence:.2f}")
            
            # Mostrar primeros versos
            numbered_verses = segment.get('numbered_verses', [])
            for j, verse in enumerate(numbered_verses[:3]):  # Solo los primeros 3
                verse_text = verse.get('text', '')
                if verse_text:
                    print(f"          {verse.get('verse_number', j+1)}. {verse_text}")
        else:
            text_content = segment.get('text', segment.get('texto_segmento', ''))
            text = text_content[:40] + "..." if len(text_content) > 40 else text_content
            print(f"   [{i}] {segment_type.upper()}: {text}")
    
    print(f"\n🎯 VERIFICACIÓN:")
    expected_poems = 2
    if poems_found == expected_poems:
        print(f"   ✅ {poems_found} poema(s) detectado(s) (esperado: {expected_poems})")
        return True
    else:
        print(f"   ❌ {poems_found} poema(s) detectado(s), esperado: {expected_poems}")
        return False

def test_multiple_poems():
    print("🎯 TEST: VerseSegmenter MEJORADO - Detección de múltiples poemas")
    
    # Simular bloques con los 8 patrones que agregamos
    test_blocks = [
        # 1. Título explícito entre comillas
        {'text': '"Cementerio"', 'page': 1},
        {'text': 'Aquí yacen los sueños', 'page': 1},
        {'text': 'en tierras de olvido', 'page': 1},
        
        # 2. Número romano como título
        {'text': 'XV', 'page': 2},
        {'text': 'La luna se esconde', 'page': 2},
        {'text': 'tras las nubes', 'page': 2},
        
        # 3. Lista numerada
        {'text': '23. Mi táctica', 'page': 3},
        {'text': 'Mi táctica es mirarte', 'page': 3},
        
        # 4. Separador visual
        {'text': '***', 'page': 4},
        {'text': 'Un nuevo amanecer', 'page': 4},
        
        # 5. Título capitalizado sin comillas
        {'text': 'Esperanza', 'page': 5},
        {'text': 'Brilla la esperanza', 'page': 5},
        
        # 6. Título después de texto largo (contexto)
        {'text': 'Esta es una línea muy larga que simula el final de un poema anterior con muchas palabras para alcanzar el límite de 300 caracteres que define un texto largo según nuestro algoritmo de detección contextual mejorado', 'page': 6},
        {'text': 'País Verde', 'page': 6},
        {'text': 'Verde como la hierba', 'page': 6},
        
        # 7. Título en nueva página
        {'text': 'Responso', 'page': 7},  # página nueva
        {'text': 'Por los que se fueron', 'page': 7},
        
        # 8. Heading de PDF
        {'text': 'Mar', 'is_heading': True, 'page': 8},
        {'text': 'El mar susurra secretos', 'page': 8},
    ]
    
    print(f"   📦 Bloques de prueba: {len(test_blocks)}")
    print(f"   🎭 Patrones de títulos incluidos: 8")
    
    # Segmentar
    segmenter = VerseSegmenter({})
    segments = segmenter.segment(test_blocks)
    
    print(f"\n✅ RESULTADOS:")
    print(f"   🎯 Poemas detectados: {len(segments)}")
    print(f"   🎯 Esperados: 8 poemas")
    
    success_rate = (len(segments) / 8) * 100
    
    print(f"   📈 Tasa de éxito: {success_rate:.1f}%")
    
    # Mostrar títulos detectados
    print(f"\n📝 TÍTULOS DETECTADOS:")
    for i, segment in enumerate(segments):
        title = segment.get('title', 'Sin título')
        print(f"   [{i+1:2d}] '{title}'")
    
    # Verificar formato
    if segments:
        first = segments[0]
        format_ok = (first.get('type') == 'poem' and 
                    'title' in first and 
                    'text' in first)
        
        if format_ok:
            print(f"\n✅ FORMATO: Compatible con ProfileManager")
        else:
            print(f"\n❌ FORMATO: Incompatible con ProfileManager")
            print(f"   Keys encontradas: {list(first.keys())}")
    
    return len(segments), success_rate

if __name__ == "__main__":
    success = test_multiplos_poemas()
    if success:
        print("\n🎉 TEST EXITOSO: Múltiples poemas detectados correctamente")
    else:
        print("\n❌ TEST FALLIDO: No se detectaron múltiples poemas correctamente")

    detected, rate = test_multiple_poems()
    
    print(f"\n🏁 RESULTADO FINAL:")
    if rate >= 87.5:  # 7/8 o mejor
        print(f"   🎉 EXCELENTE: {detected}/8 poemas detectados ({rate:.1f}%)")
        print(f"   ✅ VerseSegmenter MEJORADO funcionando correctamente")
    elif rate >= 75:  # 6/8 o mejor  
        print(f"   👍 BUENO: {detected}/8 poemas detectados ({rate:.1f}%)")
        print(f"   📈 Mejora significativa confirmada")
    elif rate >= 50:  # 4/8 o mejor
        print(f"   ⚠️  REGULAR: {detected}/8 poemas detectados ({rate:.1f}%)")
        print(f"   🔧 Necesita algunos ajustes")
    else:
        print(f"   ❌ INSUFICIENTE: {detected}/8 poemas detectados ({rate:.1f}%)")
        print(f"   🔨 Requiere revisión completa") 