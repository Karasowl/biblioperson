#!/usr/bin/env python3
"""
Test de debug completo para investigar por qué el VerseSegmenter 
no detecta nada en PDFs que antes funcionaban.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
import logging

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_pdf_step_by_step():
    """Test paso a paso del procesamiento de PDF"""
    
    # Probar con un PDF que sabemos que tiene contenido
    pdf_path = "C:/Users/adven/Downloads/Dario, Ruben - Antologia.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return False
    
    print(f"📖 Debuggeando paso a paso: {pdf_path}")
    
    # PASO 1: Cargar directamente con PdfLoader
    print(f"\n🔹 PASO 1: Cargando con PdfLoader...")
    try:
        loader = PDFLoader(pdf_path)
        raw_blocks = loader.load()
        
        print(f"   ✅ Bloques cargados: {len(raw_blocks) if isinstance(raw_blocks, list) else 'No es lista'}")
        print(f"   Tipo: {type(raw_blocks)}")
        
        # Si es dict, extraer bloques
        if isinstance(raw_blocks, dict) and 'blocks' in raw_blocks:
            blocks = raw_blocks['blocks']
        else:
            blocks = raw_blocks
            
        print(f"   📋 Bloques extraídos: {len(blocks)}")
        
        # Mostrar primeros bloques
        print(f"\n   📝 Primeros 5 bloques:")
        for i, block in enumerate(blocks[:5]):
            text_preview = block.get('text', '')[:50].replace('\n', ' ')
            is_heading = block.get('is_heading', False)
            print(f"      {i}: {'[H]' if is_heading else '[ ]'} '{text_preview}...'")
            
    except Exception as e:
        print(f"   ❌ Error en PdfLoader: {str(e)}")
        return False
    
    # PASO 2: Preprocessing
    print(f"\n🔹 PASO 2: Aplicando CommonBlockPreprocessor...")
    try:
        config = {
            'filter_insignificant_blocks': True,
            'clean_unicode_corruption': True
        }
        preprocessor = CommonBlockPreprocessor(config)
        # El preprocessor necesita metadata del documento
        document_metadata = {
            'filename': os.path.basename(pdf_path),
            'file_path': pdf_path,
            'file_type': 'pdf'
        }
        result = preprocessor.process(blocks, document_metadata)
        
        # El preprocessor devuelve (blocks, metadata) - extraer solo los bloques
        if isinstance(result, tuple):
            processed_blocks, processed_metadata = result
            print(f"   ✅ Preprocessor devolvió tupla: bloques={len(processed_blocks)}, metadata={type(processed_metadata)}")
        else:
            processed_blocks = result
            print(f"   ✅ Preprocessor devolvió directamente: {len(processed_blocks)} bloques")
        
        print(f"   ✅ Bloques después de preprocessing: {len(processed_blocks)}")
        
        # Debug: verificar estructura de bloques procesados
        print(f"\n   🔍 Tipo de processed_blocks: {type(processed_blocks)}")
        if isinstance(processed_blocks, list) and processed_blocks:
            print(f"   🔍 Tipo del primer elemento: {type(processed_blocks[0])}")
            
            # Mostrar primeros bloques procesados
            print(f"\n   📝 Primeros 5 bloques procesados:")
            for i, block in enumerate(processed_blocks[:5]):
                if isinstance(block, dict):
                    text_preview = block.get('text', '')[:50].replace('\n', ' ')
                    is_heading = block.get('is_heading', False)
                    print(f"      {i}: {'[H]' if is_heading else '[ ]'} '{text_preview}...'")
                else:
                    print(f"      {i}: FORMATO INESPERADO: {type(block)} - {str(block)[:50]}...")
        else:
            print(f"   ❌ processed_blocks vacío o no es lista")
            
    except Exception as e:
        print(f"   ❌ Error en preprocessing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # PASO 3: VerseSegmenter directo
    print(f"\n🔹 PASO 3: Aplicando VerseSegmenter directamente...")
    try:
        segmenter = VerseSegmenter()
        segments = segmenter.segment(processed_blocks)
        
        print(f"   ✅ Segmentos detectados: {len(segments)}")
        
        if segments:
            print(f"\n   📝 Primeros 3 segmentos:")
            for i, segment in enumerate(segments[:3]):
                print(f"      {i+1}. Tipo: {segment.get('type', 'N/A')}")
                title = segment.get('title', 'Sin título')
                print(f"         Título: '{title}'")
                text_preview = segment.get('text', '')[:100].replace('\n', ' ')
                print(f"         Texto: '{text_preview}...'")
                print()
        else:
            print(f"   ❌ No se detectaron segmentos")
            
    except Exception as e:
        print(f"   ❌ Error en VerseSegmenter: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # PASO 4: ProfileManager completo
    print(f"\n🔹 PASO 4: Probando ProfileManager completo...")
    try:
        profile_manager = ProfileManager()
        result = profile_manager.process_file(
            file_path=pdf_path,
            profile_name='verso',
            language_override='es'
        )
        
        if isinstance(result, tuple) and len(result) >= 3:
            content_items, stats, metadata = result[:3]
            print(f"   ✅ Items del ProfileManager: {len(content_items)}")
            print(f"   Stats: {stats}")
        else:
            print(f"   ❌ Resultado inesperado: {type(result)}")
            
    except Exception as e:
        print(f"   ❌ Error en ProfileManager: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("DEBUG: Análisis paso a paso del procesamiento de PDF")
    print("=" * 70)
    
    test_pdf_step_by_step()
    
    print("\n" + "=" * 70)
    print("DEBUG COMPLETADO")
    print("=" * 70) 