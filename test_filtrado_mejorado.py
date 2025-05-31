#!/usr/bin/env python3
"""
Script de prueba para verificar el filtrado mejorado de bloques insignificantes.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor

def test_filtrado_bloques():
    """Prueba el filtrado de bloques insignificantes."""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== PRUEBA DE FILTRADO DE BLOQUES INSIGNIFICANTES ===\n")
    
    # 1. Probar CommonBlockPreprocessor directamente
    print("1. Probando CommonBlockPreprocessor con filtrado agresivo...")
    
    config_agresivo = {
        'filter_insignificant_blocks': True,
        'min_block_chars_to_keep': 15,  # Reducir para permitir párrafos válidos
        'discard_only_numbers': True,
        'discard_common_pdf_artifacts': True,
        'aggressive_merge_for_pdfs': True,
        'max_vertical_gap_aggressive_pt': 25
    }
    
    preprocessor = CommonBlockPreprocessor(config=config_agresivo)
    
    # Bloques de prueba que simulan artefactos de PDF con coordenadas
    test_blocks = [
        {'text': 'del', 'type': 'text_block', 'order_in_document': 0, 'coordinates': {'x0': 100, 'y0': 100, 'x1': 120, 'y1': 110}, 'source_page_number': 1},
        {'text': '2', 'type': 'text_block', 'order_in_document': 1, 'coordinates': {'x0': 100, 'y0': 120, 'x1': 110, 'y1': 130}, 'source_page_number': 1},
        {'text': '3', 'type': 'text_block', 'order_in_document': 2, 'coordinates': {'x0': 100, 'y0': 140, 'x1': 110, 'y1': 150}, 'source_page_number': 1},
        {'text': 'Este es un párrafo real con suficiente contenido para ser considerado válido.', 'type': 'text_block', 'order_in_document': 3, 'coordinates': {'x0': 100, 'y0': 160, 'x1': 400, 'y1': 180}, 'source_page_number': 1},
        {'text': 'a', 'type': 'text_block', 'order_in_document': 4, 'coordinates': {'x0': 100, 'y0': 200, 'x1': 110, 'y1': 210}, 'source_page_number': 1},
        {'text': 'IV', 'type': 'text_block', 'order_in_document': 5, 'coordinates': {'x0': 100, 'y0': 220, 'x1': 120, 'y1': 230}, 'source_page_number': 1},
        {'text': 'Otro párrafo válido que debería mantenerse en el resultado final.', 'type': 'text_block', 'order_in_document': 6, 'coordinates': {'x0': 100, 'y0': 240, 'x1': 400, 'y1': 260}, 'source_page_number': 1},
        {'text': '15/03/2024', 'type': 'text_block', 'order_in_document': 7, 'coordinates': {'x0': 100, 'y0': 280, 'x1': 180, 'y1': 290}, 'source_page_number': 1},
        {'text': 'para', 'type': 'text_block', 'order_in_document': 8, 'coordinates': {'x0': 100, 'y0': 300, 'x1': 130, 'y1': 310}, 'source_page_number': 1},
    ]
    
    metadata = {'source_file_path': 'test.pdf', 'blocks_are_fitz_native': True}
    
    processed_blocks, processed_metadata = preprocessor.process(test_blocks, metadata)
    
    print(f"Bloques originales: {len(test_blocks)}")
    print(f"Bloques después del filtrado: {len(processed_blocks)}")
    print("\nBloques que pasaron el filtro:")
    for i, block in enumerate(processed_blocks):
        text = block.get('text', '')
        print(f"  {i+1}. '{text[:50]}{'...' if len(text) > 50 else ''}' (longitud: {len(text)})")
    
    # 2. Probar HeadingSegmenter con filtrado
    print("\n2. Probando HeadingSegmenter con filtrado...")
    
    try:
        manager = ProfileManager()
        profile = manager.get_profile('book_structure')
        
        if profile:
            print(f"Perfil book_structure cargado correctamente")
            
            # Crear segmentador con la configuración del perfil
            segmenter = manager.create_segmenter('book_structure')
            if segmenter:
                print(f"Segmentador creado: {type(segmenter).__name__}")
                print(f"Filtrado de segmentos pequeños habilitado: {getattr(segmenter, 'filter_small_segments', 'No configurado')}")
                print(f"Longitud mínima de segmento: {getattr(segmenter, 'min_segment_length', 'No configurado')}")
                
                # Probar segmentación con bloques que incluyen fragmentos pequeños
                test_blocks_segmenter = [
                    {'text': 'del', 'type': 'text_block'},
                    {'text': '2', 'type': 'text_block'},
                    {'text': 'CAPÍTULO 1: INTRODUCCIÓN', 'type': 'text_block'},
                    {'text': 'Este es el contenido del primer capítulo con información relevante.', 'type': 'text_block'},
                    {'text': 'a', 'type': 'text_block'},
                    {'text': 'Más contenido del capítulo que debería mantenerse.', 'type': 'text_block'},
                ]
                
                segments = segmenter.segment(test_blocks_segmenter)
                print(f"\nSegmentos generados: {len(segments)}")
                for i, segment in enumerate(segments):
                    if isinstance(segment, dict):
                        seg_type = segment.get('type', 'unknown')
                        if seg_type == 'section':
                            print(f"  {i+1}. Sección: '{segment.get('title', 'Sin título')}'")
                            if segment.get('content'):
                                print(f"      Contenido: {len(segment['content'])} elementos")
                        elif seg_type == 'paragraph':
                            text = segment.get('text', '')
                            print(f"  {i+1}. Párrafo: '{text[:50]}{'...' if len(text) > 50 else ''}' (longitud: {len(text)})")
                        else:
                            print(f"  {i+1}. {seg_type}: {segment}")
                    else:
                        print(f"  {i+1}. {type(segment)}: {segment}")
                        
            else:
                print("Error: No se pudo crear el segmentador")
        else:
            print("Error: No se pudo cargar el perfil book_structure")
            
    except Exception as e:
        print(f"Error al probar el perfil: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== FIN DE LA PRUEBA ===")

if __name__ == "__main__":
    test_filtrado_bloques() 