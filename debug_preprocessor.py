#!/usr/bin/env python3
"""
Script de debug para entender el comportamiento del CommonBlockPreprocessor.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor

def debug_preprocessor():
    """Debug detallado del preprocessor."""
    
    # Configurar logging detallado
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== DEBUG DETALLADO DEL PREPROCESSOR ===\n")
    
    # Configuración de prueba
    config_debug = {
        'filter_insignificant_blocks': True,
        'min_block_chars_to_keep': 15,
        'discard_only_numbers': True,
        'discard_common_pdf_artifacts': True,
        'aggressive_merge_for_pdfs': True,
        'max_vertical_gap_aggressive_pt': 25,
        'min_chars_for_paragraph_split': 50,
        'try_single_newline_split_if_block_longer_than': 300,
        'min_chars_for_single_newline_paragraph': 30
    }
    
    preprocessor = CommonBlockPreprocessor(config=config_debug)
    
    # Bloques de prueba más realistas
    test_blocks = [
        {'text': 'del', 'type': 'text_block', 'order_in_document': 0, 'coordinates': {'x0': 100, 'y0': 100, 'x1': 120, 'y1': 110}, 'source_page_number': 1},
        {'text': '2', 'type': 'text_block', 'order_in_document': 1, 'coordinates': {'x0': 100, 'y0': 120, 'x1': 110, 'y1': 130}, 'source_page_number': 1},
        {'text': 'Este es un párrafo real con suficiente contenido para ser considerado válido y debería mantenerse.', 'type': 'text_block', 'order_in_document': 2, 'coordinates': {'x0': 100, 'y0': 160, 'x1': 400, 'y1': 180}, 'source_page_number': 1},
        {'text': 'Otro párrafo válido que también debería mantenerse en el resultado final porque tiene suficiente contenido.', 'type': 'text_block', 'order_in_document': 3, 'coordinates': {'x0': 100, 'y0': 240, 'x1': 400, 'y1': 260}, 'source_page_number': 1},
    ]
    
    metadata = {'source_file_path': 'test.pdf', 'blocks_are_fitz_native': True}
    
    print("Bloques de entrada:")
    for i, block in enumerate(test_blocks):
        text = block.get('text', '')
        print(f"  {i+1}. '{text}' (longitud: {len(text)})")
    
    print(f"\nConfiguración del preprocessor:")
    for key, value in config_debug.items():
        print(f"  {key}: {value}")
    
    print("\n--- PROCESANDO ---")
    processed_blocks, processed_metadata = preprocessor.process(test_blocks, metadata)
    
    print(f"\nBloques de salida: {len(processed_blocks)}")
    for i, block in enumerate(processed_blocks):
        text = block.get('text', '')
        print(f"  {i+1}. '{text[:100]}{'...' if len(text) > 100 else ''}' (longitud: {len(text)})")
        print(f"      Tipo: {block.get('type', 'N/A')}")
        print(f"      Orden: {block.get('order_in_document', 'N/A')}")
    
    # Probar también sin fusión para comparar
    print("\n=== PRUEBA SIN FUSIÓN ===")
    config_sin_fusion = config_debug.copy()
    config_sin_fusion['split_blocks_into_paragraphs'] = False
    
    preprocessor_sin_fusion = CommonBlockPreprocessor(config=config_sin_fusion)
    processed_blocks_sin_fusion, _ = preprocessor_sin_fusion.process(test_blocks, metadata)
    
    print(f"\nBloques sin fusión: {len(processed_blocks_sin_fusion)}")
    for i, block in enumerate(processed_blocks_sin_fusion):
        text = block.get('text', '')
        print(f"  {i+1}. '{text}' (longitud: {len(text)})")
    
    print("\n=== FIN DEL DEBUG ===")

if __name__ == "__main__":
    debug_preprocessor() 