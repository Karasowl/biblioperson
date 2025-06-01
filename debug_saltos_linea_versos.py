#!/usr/bin/env python3
"""
DEBUG SALTOS DE LÍNEA EN VERSOS
===============================

Investigar dónde se están perdiendo los saltos de línea 
en los versos durante el procesamiento del perfil verso.
"""

import sys
import os
import logging
from pathlib import Path

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.profile_manager import ProfileManager
    from dataset.processing.loaders.markdown_pdf_loader import MarkdownPDFLoader
    from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
    
    def debug_line_breaks():
        """Debug de saltos de línea en el pipeline de verso"""
        
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            return False
        
        print("🔍 DEBUG SALTOS DE LÍNEA EN VERSOS")
        print("=" * 50)
        
        # PASO 1: Verificar salida del MarkdownPDFLoader
        print("\n1️⃣ SALIDA DEL MARKDOWNPDFLOADER:")
        print("-" * 40)
        
        loader = MarkdownPDFLoader(test_file)
        loaded_data = loader.load()
        raw_blocks = loaded_data.get('blocks', [])
        
        # Buscar un poema específico (ej. Poema 13)
        for i, block in enumerate(raw_blocks):
            text = block.get('text', '').strip()
            if 'Poema 13' in text:
                print(f"📄 Bloque {i} - MarkdownPDFLoader:")
                print(f"Texto: {repr(text[:200])}...")
                print(f"Saltos de línea detectados: {text.count(chr(10))}")
                print(f"Longitud: {len(text)}")
                break
        
        # PASO 2: Verificar salida del CommonBlockPreprocessor
        print("\n2️⃣ SALIDA DEL COMMONBLOCKPREPROCESSOR:")
        print("-" * 40)
        
        # Configuración del perfil verso
        preprocessor_config = {
            'filter_insignificant_blocks': False,
            'min_block_chars_to_keep': 1,
            'aggressive_merge_for_pdfs': False,
            'merge_cross_page_sentences': False,
            'split_blocks_into_paragraphs': False,
            'discard_common_pdf_artifacts': False,
            'markdown_aware': False
        }
        
        preprocessor = CommonBlockPreprocessor(config=preprocessor_config)
        processed_blocks, processed_metadata = preprocessor.process(
            raw_blocks, loaded_data.get('document_metadata', {})
        )
        
        # Buscar el mismo poema después del preprocessor
        for i, block in enumerate(processed_blocks):
            text = block.get('text', '').strip() if isinstance(block, dict) else str(block).strip()
            if 'Poema 13' in text:
                print(f"📄 Bloque {i} - Después del preprocessor:")
                print(f"Texto: {repr(text[:200])}...")
                print(f"Saltos de línea detectados: {text.count(chr(10))}")
                print(f"Longitud: {len(text)}")
                break
        
        # PASO 3: Verificar salida del VerseSegmenter
        print("\n3️⃣ SALIDA DEL VERSESEGMENTER:")
        print("-" * 40)
        
        manager = ProfileManager()
        segmenter = manager.create_segmenter('verso')
        
        segments = segmenter.segment(blocks=processed_blocks)
        
        # Buscar el Poema 13 en los segmentos
        for i, segment in enumerate(segments):
            if isinstance(segment, dict):
                # Verificar diferentes campos donde podría estar el texto
                text_fields = ['text', 'content', 'full_text']
                segment_text = ""
                
                for field in text_fields:
                    if field in segment and segment[field]:
                        segment_text = segment[field]
                        break
                
                if 'Poema 13' in segment_text:
                    print(f"📄 Segmento {i} - VerseSegmenter:")
                    print(f"Tipo: {segment.get('type', 'unknown')}")
                    print(f"Texto: {repr(segment_text[:200])}...")
                    print(f"Saltos de línea detectados: {segment_text.count(chr(10))}")
                    print(f"Longitud: {len(segment_text)}")
                    
                    # Mostrar la estructura completa del segmento
                    print(f"Estructura del segmento:")
                    for key, value in segment.items():
                        if key != 'text' and key != 'content':
                            print(f"  - {key}: {repr(value)[:50]}...")
                    break
        
        # PASO 4: Análisis del problema
        print("\n4️⃣ ANÁLISIS DEL PROBLEMA:")
        print("-" * 40)
        
        # Verificar si el problema está en el loader
        sample_block_raw = None
        for block in raw_blocks:
            text = block.get('text', '').strip()
            if 'He ido marcando' in text:
                sample_block_raw = text
                break
        
        if sample_block_raw:
            print("🔍 Análisis detallado del Poema 13:")
            print(f"Caracteres especiales encontrados:")
            unique_chars = set(sample_block_raw)
            special_chars = [c for c in unique_chars if ord(c) < 32 or ord(c) > 126]
            for char in special_chars:
                print(f"  - {repr(char)} (ord: {ord(char)})")
            
            # Verificar diferentes tipos de saltos de línea
            print(f"Análisis de saltos de línea:")
            print(f"  - \\n (LF): {sample_block_raw.count(chr(10))}")
            print(f"  - \\r (CR): {sample_block_raw.count(chr(13))}")
            print(f"  - \\r\\n (CRLF): {sample_block_raw.count(chr(13) + chr(10))}")
            
            # Mostrar las primeras líneas separadas
            lines = sample_block_raw.split('\n')[:5]
            print(f"Primeras líneas separadas:")
            for i, line in enumerate(lines):
                print(f"  Línea {i}: {repr(line)}")
        
        return True
    
    if __name__ == "__main__":
        print("🧪 DEBUG SALTOS DE LÍNEA EN VERSOS")
        print("=" * 50)
        
        debug_line_breaks()
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("⚠️ Asegúrate de ejecutar desde el directorio raíz del proyecto") 