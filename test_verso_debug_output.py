#!/usr/bin/env python3
"""
Test para verificar exactamente qué devuelve el VerseSegmenter
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

def test_verse_output():
    print("🔍 TEST: Verificar output exacto del VerseSegmenter")
    
    # Ruta del archivo PDF
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n1️⃣ PASO 1: Cargar PDF")
    loader = PDFLoader(str(archivo_pdf))
    raw_blocks = loader.load()
    print(f"   📄 Bloques cargados: {len(raw_blocks)}")
    
    print(f"\n2️⃣ PASO 2: Preprocessar bloques")
    preprocessor = CommonBlockPreprocessor()
    processed_blocks = preprocessor.process(raw_blocks, {})  # Agregar parámetro document_metadata vacío
    print(f"   📦 Bloques procesados: {len(processed_blocks)}")
    
    print(f"\n3️⃣ PASO 3: Segmentar con VerseSegmenter")
    segmenter = VerseSegmenter()
    segments = segmenter.segment(processed_blocks)
    
    print(f"\n✅ RESULTADO:")
    print(f"   🎯 Segmentos devueltos: {len(segments)}")
    print(f"   📊 Tipo de resultado: {type(segments)}")
    
    if segments:
        print(f"\n📝 ANÁLISIS DE PRIMEROS 3 SEGMENTOS:")
        for i, segment in enumerate(segments[:3]):
            print(f"\n   --- SEGMENTO {i+1} ---")
            print(f"   📋 Tipo: {type(segment)}")
            print(f"   🗂️  Keys: {list(segment.keys()) if isinstance(segment, dict) else 'No es dict'}")
            
            if isinstance(segment, dict):
                # Revisar cada campo importante
                print(f"   🏷️  type: '{segment.get('type', 'NO_ENCONTRADO')}'")
                print(f"   📄 text length: {len(segment.get('text', '')) if segment.get('text') else 'NO_ENCONTRADO/NONE'}")
                print(f"   📝 title: '{segment.get('title', 'NO_ENCONTRADO')}'")
                
                # Mostrar contenido del texto (primeros 100 chars)
                text_content = segment.get('text', '')
                if text_content:
                    preview = text_content[:100].replace('\n', '\\n')
                    print(f"   📖 text preview: '{preview}...'")
                else:
                    print(f"   ❌ text está VACÍO o es None")
            
            print(f"   📄 Representación completa:")
            print(f"      {segment}")
    
    else:
        print(f"   ❌ NO HAY SEGMENTOS")

if __name__ == "__main__":
    test_verse_output() 