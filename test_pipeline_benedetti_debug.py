#!/usr/bin/env python3
"""
Test DEBUG COMPLETO del pipeline con PDF de Benedetti
Analiza cada paso para encontrar dónde se pierde la información
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def debug_pipeline_benedetti():
    print("🔍 DEBUG COMPLETO: Pipeline con PDF de Benedetti")
    
    # Ruta del archivo PDF
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n📄 ARCHIVO: {archivo_pdf.name}")
    
    # PASO 1: CARGAR PDF
    print(f"\n1️⃣ PASO 1: Cargar PDF con PDFLoader")
    try:
        loader = PDFLoader(str(archivo_pdf))
        raw_blocks = loader.load()
        print(f"   ✅ Bloques cargados: {len(raw_blocks)}")
        
        # Analizar tipos de datos devueltos
        if raw_blocks:
            first_block = raw_blocks[0]
            print(f"   🔍 Tipo del primer bloque: {type(first_block)}")
            
            if isinstance(first_block, dict):
                print(f"   📋 Keys del primer bloque: {list(first_block.keys())}")
                print(f"   📝 Texto (primeros 50 chars): '{first_block.get('text', '')[:50]}...'")
                print(f"   🏷️  Metadata: página={first_block.get('page')}, is_heading={first_block.get('is_heading')}")
            else:
                print(f"   ⚠️  PROBLEMA: Primer bloque es {type(first_block)}, no dict")
                print(f"   📝 Contenido (primeros 50 chars): '{str(first_block)[:50]}...'")
        
        # Contar bloques con potencial de título
        potential_titles = 0
        for i, block in enumerate(raw_blocks[:100]):  # Solo los primeros 100
            if isinstance(block, dict):
                text = block.get('text', '').strip()
                if text and len(text) < 80:
                    # Aplicar algunos patrones simples
                    if (text.startswith('"') and text.endswith('"')) or \
                       text.isupper() or \
                       block.get('is_heading', False):
                        potential_titles += 1
                        if potential_titles <= 5:  # Mostrar solo los primeros 5
                            print(f"   📍 Título potencial {potential_titles}: '{text}'")
        
        print(f"   🎯 Títulos potenciales detectados en primeros 100 bloques: {potential_titles}")
        
    except Exception as e:
        print(f"   ❌ ERROR en PDFLoader: {e}")
        return
    
    # PASO 2: PREPROCESSAR
    print(f"\n2️⃣ PASO 2: Preprocessar con CommonBlockPreprocessor")
    try:
        preprocessor = CommonBlockPreprocessor()
        processed_blocks = preprocessor.process(raw_blocks, {})
        print(f"   ✅ Bloques procesados: {len(processed_blocks)}")
        
        # Verificar formato después del preprocessor
        if processed_blocks:
            first_processed = processed_blocks[0]
            print(f"   🔍 Tipo después de preprocessor: {type(first_processed)}")
            
            if isinstance(first_processed, dict):
                print(f"   📋 Keys después de preprocessor: {list(first_processed.keys())}")
            else:
                print(f"   ⚠️  PROBLEMA: Bloque procesado es {type(first_processed)}, no dict")
        
        # Verificar cuántos títulos potenciales quedan
        processed_titles = 0
        for block in processed_blocks[:100]:
            if isinstance(block, dict):
                text = block.get('text', '').strip()
                if text and len(text) < 80:
                    if (text.startswith('"') and text.endswith('"')) or \
                       text.isupper() or \
                       block.get('is_heading', False):
                        processed_titles += 1
        
        print(f"   🎯 Títulos potenciales tras preprocessor: {processed_titles}")
        
    except Exception as e:
        print(f"   ❌ ERROR en Preprocessor: {e}")
        return
    
    # PASO 3: SEGMENTAR
    print(f"\n3️⃣ PASO 3: Segmentar con VerseSegmenter MEJORADO")
    try:
        segmenter = VerseSegmenter({})
        segments = segmenter.segment(processed_blocks)
        print(f"   ✅ Poemas detectados: {len(segments)}")
        
        # Analizar los poemas encontrados
        if segments:
            print(f"   📝 POEMAS DETECTADOS:")
            for i, segment in enumerate(segments[:10]):  # Solo los primeros 10
                title = segment.get('title', 'Sin título')
                text_lines = len(segment.get('text', '').split('\n'))
                print(f"      [{i+1}] '{title}' ({text_lines} líneas)")
                
            # Verificar formato
            first_segment = segments[0]
            print(f"   🔍 Formato del primer segmento:")
            print(f"      📋 Keys: {list(first_segment.keys())}")
            print(f"      🏷️  type: '{first_segment.get('type')}'")
            print(f"      📝 title: '{first_segment.get('title')}'")
            print(f"      📄 text length: {len(first_segment.get('text', ''))}")
        else:
            print(f"   ❌ NO se detectaron poemas")
            
            # DEBUG: Verificar manualmente los primeros bloques
            print(f"   🔍 ANÁLISIS MANUAL de primeros 20 bloques:")
            for i, block in enumerate(processed_blocks[:20]):
                if isinstance(block, dict):
                    text = block.get('text', '').strip()
                    if text:
                        is_title = segmenter._is_main_title(block, i, processed_blocks)
                        status = "📍 TÍTULO" if is_title else "📝 Contenido"
                        print(f"      [{i}] {status}: '{text[:40]}{'...' if len(text) > 40 else ''}'")
        
    except Exception as e:
        print(f"   ❌ ERROR en VerseSegmenter: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # RESUMEN
    print(f"\n🏁 RESUMEN DEL DIAGNÓSTICO:")
    print(f"   📦 Bloques originales: {len(raw_blocks)}")
    print(f"   🔧 Bloques procesados: {len(processed_blocks)}")
    print(f"   🎭 Poemas detectados: {len(segments)}")
    print(f"   🎯 Objetivo del usuario: ~140 poemas")
    
    detection_rate = (len(segments) / 140) * 100
    print(f"   📈 Tasa de detección: {detection_rate:.1f}%")
    
    if len(segments) < 10:
        print(f"   🚨 PROBLEMA CRÍTICO: Muy pocos poemas detectados")
        print(f"   🔍 Revisar: Compatibilidad PDFLoader <-> VerseSegmenter")
    elif len(segments) < 50:
        print(f"   ⚠️  PROBLEMA MODERADO: Detección insuficiente")
        print(f"   🔧 Revisar: Patrones de detección en VerseSegmenter")
    else:
        print(f"   ✅ DETECCIÓN ACEPTABLE: Se acerca al objetivo")

if __name__ == "__main__":
    debug_pipeline_benedetti() 