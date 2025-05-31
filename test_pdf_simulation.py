#!/usr/bin/env python3
"""
Script para simular el procesamiento de un PDF problemático con el perfil book_structure mejorado.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.profile_manager import ProfileManager

def simulate_pdf_processing():
    """Simula el procesamiento de un PDF problemático."""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== SIMULACIÓN DE PROCESAMIENTO PDF ===\n")
    
    # Simular bloques extraídos de un PDF problemático (como los que se ven en Alfonso Reyes)
    simulated_pdf_blocks = [
        {'text': 'del', 'type': 'text_block', 'order_in_document': 0, 'coordinates': {'x0': 100, 'y0': 100, 'x1': 120, 'y1': 110}, 'source_page_number': 1},
        {'text': '2', 'type': 'text_block', 'order_in_document': 1, 'coordinates': {'x0': 100, 'y0': 120, 'x1': 110, 'y1': 130}, 'source_page_number': 1},
        {'text': '3', 'type': 'text_block', 'order_in_document': 2, 'coordinates': {'x0': 100, 'y0': 140, 'x1': 110, 'y1': 150}, 'source_page_number': 1},
        {'text': 'CAPÍTULO 1', 'type': 'text_block', 'order_in_document': 3, 'coordinates': {'x0': 100, 'y0': 160, 'x1': 200, 'y1': 180}, 'source_page_number': 1},
        {'text': 'INTRODUCCIÓN', 'type': 'text_block', 'order_in_document': 4, 'coordinates': {'x0': 100, 'y0': 190, 'x1': 250, 'y1': 210}, 'source_page_number': 1},
        {'text': 'Este es el primer párrafo del capítulo que contiene información importante sobre el tema que se va a tratar.', 'type': 'text_block', 'order_in_document': 5, 'coordinates': {'x0': 100, 'y0': 220, 'x1': 400, 'y1': 240}, 'source_page_number': 1},
        {'text': 'a', 'type': 'text_block', 'order_in_document': 6, 'coordinates': {'x0': 100, 'y0': 250, 'x1': 110, 'y1': 260}, 'source_page_number': 1},
        {'text': 'IV', 'type': 'text_block', 'order_in_document': 7, 'coordinates': {'x0': 100, 'y0': 270, 'x1': 120, 'y1': 280}, 'source_page_number': 1},
        {'text': 'Continuando con el desarrollo del tema, este segundo párrafo amplía la información presentada anteriormente y proporciona más detalles.', 'type': 'text_block', 'order_in_document': 8, 'coordinates': {'x0': 100, 'y0': 290, 'x1': 400, 'y1': 310}, 'source_page_number': 1},
        {'text': 'para', 'type': 'text_block', 'order_in_document': 9, 'coordinates': {'x0': 100, 'y0': 320, 'x1': 130, 'y1': 330}, 'source_page_number': 1},
        {'text': '15/03/2024', 'type': 'text_block', 'order_in_document': 10, 'coordinates': {'x0': 100, 'y0': 340, 'x1': 180, 'y1': 350}, 'source_page_number': 1},
        {'text': 'CAPÍTULO 2', 'type': 'text_block', 'order_in_document': 11, 'coordinates': {'x0': 100, 'y0': 400, 'x1': 200, 'y1': 420}, 'source_page_number': 2},
        {'text': 'DESARROLLO', 'type': 'text_block', 'order_in_document': 12, 'coordinates': {'x0': 100, 'y0': 430, 'x1': 250, 'y1': 450}, 'source_page_number': 2},
        {'text': 'En este segundo capítulo se desarrollan los conceptos principales que fueron introducidos en el capítulo anterior, proporcionando ejemplos concretos y análisis detallados.', 'type': 'text_block', 'order_in_document': 13, 'coordinates': {'x0': 100, 'y0': 460, 'x1': 400, 'y1': 480}, 'source_page_number': 2},
    ]
    
    # Metadatos simulados del documento
    simulated_metadata = {
        'source_file_path': 'documento_simulado.pdf',
        'blocks_are_fitz_native': True,
        'file_format': '.pdf'
    }
    
    print(f"Bloques simulados del PDF: {len(simulated_pdf_blocks)}")
    print("Fragmentos problemáticos detectados:")
    for i, block in enumerate(simulated_pdf_blocks):
        text = block.get('text', '')
        if len(text) <= 15:  # Mostrar solo los fragmentos pequeños
            print(f"  - '{text}' (longitud: {len(text)})")
    
    # Crear ProfileManager y procesar con el perfil book_structure
    try:
        manager = ProfileManager()
        profile = manager.get_profile('book_structure')
        
        if not profile:
            print("Error: No se pudo cargar el perfil book_structure")
            return
        
        print(f"\nUsando perfil: {profile['name']}")
        print(f"Configuración del pre-procesador:")
        pre_config = profile.get('pre_processor_config', {})
        for key, value in pre_config.items():
            print(f"  {key}: {value}")
        
        # Simular el procesamiento completo
        print("\n--- PROCESANDO CON PERFIL COMPLETO ---")
        
        # 1. Aplicar pre-procesador
        from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        preprocessor = CommonBlockPreprocessor(config=pre_config)
        processed_blocks, processed_metadata = preprocessor.process(simulated_pdf_blocks, simulated_metadata)
        
        print(f"Bloques después del pre-procesador: {len(processed_blocks)}")
        
        # 2. Aplicar segmentador
        segmenter = manager.create_segmenter('book_structure')
        if segmenter:
            segments = segmenter.segment(processed_blocks)
            print(f"Segmentos generados: {len(segments)}")
            
            print("\nSegmentos resultantes:")
            for i, segment in enumerate(segments):
                if isinstance(segment, dict):
                    seg_type = segment.get('type', 'unknown')
                    if seg_type == 'section':
                        title = segment.get('title', 'Sin título')
                        content_count = len(segment.get('content', []))
                        print(f"  {i+1}. Sección: '{title}' ({content_count} elementos de contenido)")
                    elif seg_type == 'paragraph':
                        text = segment.get('text', '')
                        print(f"  {i+1}. Párrafo: '{text[:60]}{'...' if len(text) > 60 else ''}' (longitud: {len(text)})")
                    else:
                        print(f"  {i+1}. {seg_type}: {segment}")
                else:
                    print(f"  {i+1}. {type(segment)}: {segment}")
            
            # Mostrar estadísticas del segmentador si están disponibles
            if hasattr(segmenter, 'get_stats'):
                stats = segmenter.get_stats()
                if stats:
                    print(f"\nEstadísticas del segmentador:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
        else:
            print("Error: No se pudo crear el segmentador")
            
    except Exception as e:
        print(f"Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== FIN DE LA SIMULACIÓN ===")

if __name__ == "__main__":
    simulate_pdf_processing() 