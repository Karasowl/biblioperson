#!/usr/bin/env python3
"""
Test específico para el NUEVO PDF de Benedetti
"Mario Benedetti Antologia Poética.pdf"
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from pathlib import Path
import logging

# Configurar logging para ver detalles
logging.basicConfig(level=logging.INFO)

def test_nuevo_benedetti():
    print("🔍 TEST: Nuevo PDF de Benedetti sin corrupción")
    
    # Ruta del NUEVO archivo PDF
    archivo_pdf = Path("C:/Users/adven/Downloads/Mario Benedetti Antologia Poética.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n📄 ARCHIVO: {archivo_pdf.name}")
    
    # PASO 1: CARGAR PDF
    print(f"\n1️⃣ PASO 1: Cargar PDF")
    try:
        loader = PDFLoader(str(archivo_pdf))
        raw_blocks = loader.load()
        print(f"   ✅ Bloques cargados: {len(raw_blocks)}")
        
        # Analizar primeros bloques para ver el contenido real
        if raw_blocks:
            print(f"\n   📝 PRIMEROS 10 BLOQUES:")
            for i, block in enumerate(raw_blocks[:10]):
                if isinstance(block, dict):
                    text = block.get('text', '').strip()
                    page = block.get('page', 'N/A')
                    print(f"      [{i}] P.{page}: '{text[:70]}{'...' if len(text) > 70 else ''}'")
                else:
                    print(f"      [{i}] TIPO INCORRECTO: {type(block)}")
        
        # Buscar títulos potenciales en primeros 50 bloques
        potential_titles = []
        for i, block in enumerate(raw_blocks[:50]):
            if isinstance(block, dict):
                text = block.get('text', '').strip()
                if text and len(text) < 100:
                    # Patrones de títulos de poemas
                    if (text.startswith('"') and text.endswith('"')) or \
                       (len(text.split()) <= 5 and text[0].isupper() and not text.endswith('.')) or \
                       text.isupper():
                        potential_titles.append((i, text))
        
        print(f"\n   📍 TÍTULOS POTENCIALES EN PRIMEROS 50 BLOQUES ({len(potential_titles)}):")
        for i, (idx, title) in enumerate(potential_titles[:10]):
            print(f"      [{idx}] '{title}'")
        
    except Exception as e:
        print(f"   ❌ ERROR en PDFLoader: {e}")
        return
    
    # PASO 2: PREPROCESSAR
    print(f"\n2️⃣ PASO 2: Preprocessar")
    try:
        preprocessor = CommonBlockPreprocessor()
        processed_blocks = preprocessor.process(raw_blocks, {})
        print(f"   ✅ Bloques procesados: {len(processed_blocks)} (filtrado: {len(raw_blocks) - len(processed_blocks)} bloques)")
        
        # Verificar qué queda después del filtrado
        if processed_blocks:
            print(f"\n   📝 PRIMEROS 10 BLOQUES PROCESADOS:")
            for i, block in enumerate(processed_blocks[:10]):
                if isinstance(block, dict):
                    text = block.get('text', '').strip()
                    page = block.get('page', 'N/A')
                    print(f"      [{i}] P.{page}: '{text[:70]}{'...' if len(text) > 70 else ''}'")
        
        # Buscar títulos potenciales después del preprocessor
        processed_titles = []
        for i, block in enumerate(processed_blocks[:50]):
            if isinstance(block, dict):
                text = block.get('text', '').strip()
                if text and len(text) < 100:
                    if (text.startswith('"') and text.endswith('"')) or \
                       (len(text.split()) <= 5 and text[0].isupper() and not text.endswith('.')) or \
                       text.isupper():
                        processed_titles.append((i, text))
        
        print(f"\n   📍 TÍTULOS TRAS PREPROCESSOR ({len(processed_titles)}):")
        for i, (idx, title) in enumerate(processed_titles[:10]):
            print(f"      [{idx}] '{title}'")
        
    except Exception as e:
        print(f"   ❌ ERROR en Preprocessor: {e}")
        return
    
    # PASO 3: SEGMENTAR CON DEBUG
    print(f"\n3️⃣ PASO 3: Segmentar con VerseSegmenter MEJORADO")
    try:
        segmenter = VerseSegmenter({})
        
        # TEST MANUAL: Ver si al menos los primeros bloques son detectados como títulos
        print(f"\n   🔍 TEST MANUAL de detección:")
        manual_titles = 0
        for i, block in enumerate(processed_blocks[:20]):
            if isinstance(block, dict):
                is_title = segmenter._is_main_title(block, i, processed_blocks)
                text = block.get('text', '').strip()
                if is_title:
                    manual_titles += 1
                    print(f"      ✅ TÍTULO {manual_titles}: '{text[:50]}...'")
                else:
                    if text and len(text) < 60:  # Solo mostrar texto corto
                        print(f"      ❌ No título: '{text[:50]}...'")
        
        print(f"\n   📊 Títulos detectados manualmente: {manual_titles}")
        
        # Ahora hacer la segmentación real
        segments = segmenter.segment(processed_blocks)
        print(f"   ✅ Poemas detectados por segmentador: {len(segments)}")
        
        if segments:
            print(f"\n   📝 POEMAS DETECTADOS:")
            for i, segment in enumerate(segments[:10]):
                title = segment.get('title', 'Sin título')
                text_lines = len(segment.get('text', '').split('\n'))
                print(f"      [{i+1}] '{title}' ({text_lines} líneas)")
        else:
            print(f"   ❌ NO se detectaron poemas por el segmentador")
        
    except Exception as e:
        print(f"   ❌ ERROR en VerseSegmenter: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # RESUMEN
    print(f"\n🏁 DIAGNÓSTICO:")
    print(f"   📦 Bloques originales: {len(raw_blocks)}")
    print(f"   🔧 Bloques procesados: {len(processed_blocks)}")
    print(f"   📍 Títulos potenciales antes: {len(potential_titles)}")
    print(f"   📍 Títulos potenciales después: {len(processed_titles)}")
    print(f"   🎭 Poemas detectados: {len(segments)}")
    print(f"   🎯 Objetivo: ~140 poemas")
    
    if len(raw_blocks) > 100:
        print(f"   ✅ PDF válido cargado correctamente")
        if len(processed_blocks) < 50:
            print(f"   ⚠️  Preprocessor filtró demasiado contenido")
        elif len(segments) == 0:
            print(f"   🚨 PROBLEMA: VerseSegmenter no funciona con este formato")
            print(f"   💡 REVISAR: Patrones de detección o formato de datos")
        else:
            print(f"   🎉 Sistema funcionando")
    else:
        print(f"   ❌ PDF tiene muy poco contenido")

if __name__ == "__main__":
    test_nuevo_benedetti() 