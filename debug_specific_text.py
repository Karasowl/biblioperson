#!/usr/bin/env python3
"""
Debug específico para rastrear el texto "atractivo de esta idea"
a través de todo el pipeline de procesamiento.
"""

import os
import sys
import importlib

# Limpiar cache de Python
def clear_python_cache():
    """Eliminar archivos .pyc para forzar recarga"""
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    print(f"Eliminado cache: {file}")
                except:
                    pass
    
    # Limpiar __pycache__
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            import shutil
            try:
                shutil.rmtree(os.path.join(root, '__pycache__'))
                print(f"Eliminado __pycache__ en {root}")
            except:
                pass

def reload_all_modules():
    """Forzar recarga de módulos críticos"""
    modules_to_reload = [
        'dataset.processing.loaders.pdf_loader',
        'dataset.processing.pre_processors.common_block_preprocessor',
        'dataset.processing.segmenters.heading_segmenter'
    ]
    
    for module_name in modules_to_reload:
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                print(f"Recargado: {module_name}")
        except Exception as e:
            print(f"Error recargando {module_name}: {e}")

def test_specific_text_tracking():
    """Rastrear específicamente el texto problemático"""
    
    # Limpiar cache primero
    clear_python_cache()
    reload_all_modules()
    
    target_text = "atractivo de esta idea"
    search_parts = ["atractivo", "de esta idea", "dominar colectivamente"]
    
    print(f"\n=== RASTREANDO TEXTO ESPECÍFICO ===")
    print(f"Texto objetivo: '{target_text}'")
    print(f"Partes a buscar: {search_parts}")
    
    # 1. Probar PDFLoader
    print(f"\n1. TESTING PDFLoader:")
    try:
        from dataset.processing.loaders.pdf_loader import PDFLoader
        
        pdf_path = r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf"
        
        if os.path.exists(pdf_path):
            loader = PDFLoader(pdf_path)
            raw_data = loader.load()
            
            print(f"PDFLoader extrajo {len(raw_data['blocks'])} bloques")
            
            # Buscar bloques que contienen las partes del texto
            found_blocks = []
            for i, block in enumerate(raw_data['blocks']):
                text = block.get('text', '').lower()
                for part in search_parts:
                    if part.lower() in text:
                        found_blocks.append((i, part, text[:200]))
                        print(f"  Bloque {i} contiene '{part}': {text[:100]}...")
            
            print(f"  Total bloques encontrados: {len(found_blocks)}")
            
            # Buscar si hay bloques consecutivos con las partes
            for i in range(len(found_blocks) - 1):
                curr_idx, curr_part, curr_text = found_blocks[i]
                next_idx, next_part, next_text = found_blocks[i + 1]
                
                if next_idx == curr_idx + 1:
                    print(f"  ⚠️ POSIBLE DIVISIÓN: Bloques {curr_idx}-{next_idx}")
                    print(f"    Bloque {curr_idx}: ...{curr_text[-50:]}")
                    print(f"    Bloque {next_idx}: {next_text[:50]}...")
        else:
            print(f"  ❌ PDF no encontrado: {pdf_path}")
            
    except Exception as e:
        print(f"  ❌ Error en PDFLoader: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Probar CommonBlockPreprocessor
    print(f"\n2. TESTING CommonBlockPreprocessor:")
    try:
        if 'raw_data' in locals():
            from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
            
            preprocessor = CommonBlockPreprocessor()
            processed_blocks = preprocessor.process(raw_data['blocks'], raw_data.get('metadata', {}))
            
            print(f"CommonBlockPreprocessor procesó {len(processed_blocks)} bloques")
            
            # Buscar el texto en bloques procesados
            found_processed = []
            for i, block in enumerate(processed_blocks):
                text = block.get('text', '').lower()
                for part in search_parts:
                    if part.lower() in text:
                        found_processed.append((i, part, text[:200]))
                        print(f"  Bloque procesado {i} contiene '{part}': {text[:100]}...")
            
            print(f"  Total bloques procesados encontrados: {len(found_processed)}")
            
    except Exception as e:
        print(f"  ❌ Error en CommonBlockPreprocessor: {e}")
    
    # 3. Probar HeadingSegmenter
    print(f"\n3. TESTING HeadingSegmenter:")
    try:
        if 'processed_blocks' in locals():
            from dataset.processing.segmenters.heading_segmenter import HeadingSegmenter
            
            # Cargar configuración del perfil prosa
            config = {
                "preserve_individual_paragraphs": True,
                "min_segment_length": 10,
                "max_segment_length": 5000
            }
            
            segmenter = HeadingSegmenter(config)
            segments = segmenter.segment(processed_blocks)
            
            print(f"HeadingSegmenter creó {len(segments)} segmentos")
            
            # Buscar segmentos que contienen las partes del texto
            found_segments = []
            for i, segment in enumerate(segments):
                text = segment.get('text', '').lower()
                for part in search_parts:
                    if part.lower() in text:
                        found_segments.append((i, part, text[:200]))
                        print(f"  Segmento {i} contiene '{part}': {text[:100]}...")
            
            print(f"  Total segmentos encontrados: {len(found_segments)}")
            
            # Verificar si hay división del texto objetivo
            for i in range(len(found_segments) - 1):
                curr_idx, curr_part, curr_text = found_segments[i]
                next_idx, next_part, next_text = found_segments[i + 1]
                
                if "atractivo" in curr_text and "de esta idea" in next_text:
                    print(f"  🔥 PROBLEMA ENCONTRADO:")
                    print(f"     Segmento {curr_idx}: ...{curr_text[-100:]}")
                    print(f"     Segmento {next_idx}: {next_text[:100]}...")
                    
    except Exception as e:
        print(f"  ❌ Error en HeadingSegmenter: {e}")

if __name__ == "__main__":
    test_specific_text_tracking() 