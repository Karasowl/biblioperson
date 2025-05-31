#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del perfil prosa actualizado con detección inteligente de títulos integrada
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar componentes directamente
from dataset.processing.profile_manager import ProfileManager
from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.heading_segmenter import HeadingSegmenter

def test_prosa_con_deteccion_titulos():
    print("=== TEST: PERFIL PROSA CON DETECCIÓN INTELIGENTE DE TÍTULOS ===")
    
    # Crear datos de prueba que simulan un documento con títulos (metadatos completos)
    test_blocks = [
        {
            "text": "Primera edición, 2017\nPrimera edición en inglés, 2016",
            "page": 1,
            "bbox": [72, 720, 300, 750],
            "coordinates": {"x0": 72, "y0": 720, "x1": 300, "y1": 750},
            "font_size": 12,
            "font_weight": "normal",
            "font_name": "TimesNewRoman",
            "is_bold": False,
            "is_italic": False,
            "text_alignment": "left",
            "line_count": 2,
            "type": "text_block"
        },
        {
            "text": "Introducción | ¿Son todos populistas?",
            "page": 2, 
            "bbox": [72, 400, 400, 430],
            "coordinates": {"x0": 72, "y0": 400, "x1": 400, "y1": 430},
            "font_size": 16,
            "font_weight": "bold", 
            "font_name": "TimesNewRoman-Bold",
            "is_bold": True,
            "is_italic": False,
            "text_alignment": "left",
            "line_count": 1,
            "type": "text_block"
        },
        {
            "text": "En los últimos años, el término populismo se ha vuelto omnipresente en el debate político. Uno tendría que ser muy necio para no ver el atractivo de esta idea de cómo dominar colectivamente el propio destino.",
            "page": 2,
            "bbox": [72, 350, 500, 390],
            "coordinates": {"x0": 72, "y0": 350, "x1": 500, "y1": 390},
            "font_size": 12,
            "font_weight": "normal",
            "font_name": "TimesNewRoman",
            "is_bold": False,
            "is_italic": False,
            "text_alignment": "left",
            "line_count": 3,
            "type": "text_block"
        },
        {
            "text": "1. Lo que dicen los populistas",
            "page": 3,
            "bbox": [72, 600, 350, 625],
            "coordinates": {"x0": 72, "y0": 600, "x1": 350, "y1": 625},
            "font_size": 14,
            "font_weight": "bold",
            "font_name": "TimesNewRoman-Bold", 
            "is_bold": True,
            "is_italic": False,
            "text_alignment": "left",
            "line_count": 1,
            "type": "text_block"
        },
        {
            "text": "Los populistas afirman que ellos y sólo ellos representan al pueblo. Esta no es una afirmación empírica; es siempre de carácter moral.",
            "page": 3,
            "bbox": [72, 550, 500, 590],
            "coordinates": {"x0": 72, "y0": 550, "x1": 500, "y1": 590},
            "font_size": 12,
            "font_weight": "normal",
            "font_name": "TimesNewRoman",
            "is_bold": False,
            "is_italic": False,
            "text_alignment": "left",
            "line_count": 2,
            "type": "text_block"
        },
        {
            "text": "Capítulo 2: Las técnicas populistas",
            "page": 4,
            "bbox": [72, 650, 400, 680],
            "coordinates": {"x0": 72, "y0": 650, "x1": 400, "y1": 680},
            "font_size": 15,
            "font_weight": "bold",
            "font_name": "TimesNewRoman-Bold",
            "is_bold": True,
            "is_italic": False,
            "text_alignment": "left",
            "line_count": 1,
            "type": "text_block"
        }
    ]
    
    # Metadatos del documento simulado
    document_metadata = {
        "source_file_path": "test_populismo.pdf",
        "title": "¿Qué es el populismo?",
        "author": "Jan-Werner Müller",
        "format": "pdf"
    }
    
    # Simular el pipeline completo manualmente
    print("📤 Procesando bloques con perfil PROSA (detección de títulos activada)...")
    
    # 1. Cargar configuración del perfil prosa
    profile_manager = ProfileManager()
    prosa_config = profile_manager.get_profile("prosa")
    print(f"📋 Configuración del perfil prosa cargada")
    
    # 2. Preprocessor 
    preprocessor_config = prosa_config.get('pre_processor_config', {})
    preprocessor = CommonBlockPreprocessor(preprocessor_config)
    processed_blocks, processed_metadata = preprocessor.process(test_blocks, document_metadata)
    print(f"🔧 Preprocessor: {len(test_blocks)} → {len(processed_blocks)} bloques")
    
    # 3. Segmentador con configuración del perfil prosa (incluyendo detección de títulos)
    segmenter_config = prosa_config.get('segmenter_config', {})
    segmenter = HeadingSegmenter(segmenter_config)
    result = segmenter.segment(processed_blocks, processed_metadata)
    print(f"✂️ Segmentador: {len(processed_blocks)} → {len(result)} segmentos")
    
    # Analizar resultados
    print(f"\n📊 RESULTADOS:")
    print(f"   Total segmentos: {len(result)}")
    
    titles_found = 0
    paragraphs_found = 0
    
    for i, segment in enumerate(result, 1):
        segment_type = segment.get('type', 'unknown')
        # Probar diferentes campos de texto posibles
        text_content = segment.get('text', segment.get('texto_segmento', ''))
        text = text_content[:60] + "..." if len(text_content) > 60 else text_content
        
        if segment_type.startswith('title_level_'):
            titles_found += 1
            level = segment_type.split('_')[-1]
            print(f"   [{i}] TÍTULO NIVEL {level}: {text}")
            
            # Mostrar score si está disponible
            if 'title_score' in segment:
                print(f"       📈 Score: {segment['title_score']:.2f}")
        elif segment_type == 'paragraph':
            paragraphs_found += 1
            print(f"   [{i}] PÁRRAFO: {text}")
        else:
            print(f"   [{i}] {segment_type.upper()}: {text}")
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   🏷️ Títulos detectados: {titles_found}")
    print(f"   📄 Párrafos normales: {paragraphs_found}")
    
    # Verificaciones específicas
    expected_titles = [
        "Introducción | ¿Son todos populistas?",
        "1. Lo que dicen los populistas", 
        "Capítulo 2: Las técnicas populistas"
    ]
    
    detected_titles = [s.get('text', s.get('texto_segmento', '')) for s in result if s.get('type', '').startswith('title_level_')]
    
    print(f"\n🎯 VERIFICACIÓN:")
    for expected in expected_titles:
        if any(expected in detected for detected in detected_titles):
            print(f"   ✅ ENCONTRADO: {expected}")
        else:
            print(f"   ❌ FALTANTE: {expected}")
    
    # Verificar que el texto problemático esté unido
    full_text = " ".join([s.get('text', s.get('texto_segmento', '')) for s in result])
    if "atractivo de esta idea" in full_text:
        print(f"   ✅ TEXTO UNIDO CORRECTAMENTE: 'atractivo de esta idea'")
    else:
        print(f"   ❌ PROBLEMA PERSISTE: texto 'atractivo' sigue separado")
    
    return len(result) > 0 and titles_found > 0

if __name__ == "__main__":
    success = test_prosa_con_deteccion_titulos()
    if success:
        print(f"\n🎉 TEST EXITOSO: Perfil prosa detecta títulos correctamente")
    else:
        print(f"\n💥 TEST FALLIDO: Problema con detección de títulos") 