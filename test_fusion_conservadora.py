#!/usr/bin/env python3
"""
Script para probar la fusión conservadora que respeta gaps visuales grandes.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor

def test_fusion_conservadora():
    """Prueba la fusión conservadora que respeta espaciado visual."""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== PRUEBA DE FUSIÓN CONSERVADORA (RESPETA GAPS GRANDES) ===\n")
    
    # Configuración del perfil prosa
    config_prosa = {
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
    
    preprocessor = CommonBlockPreprocessor(config=config_prosa)
    
    # Simular bloques con diferentes tipos de gaps
    test_blocks_gaps = [
        # CASO 1: Gap pequeño - DEBE fusionarse (oración cortada)
        {
            'text': 'Los políticos no populistas no utilizan discursos enardecedores para hablar solamente por una',
            'type': 'text_block',
            'order_in_document': 0,
            'coordinates': {'x0': 72, 'y0': 100, 'x1': 523, 'y1': 115},
            'source_page_number': 1
        },
        {
            'text': 'facción (aunque hay quienes lo hacen en Europa).',
            'type': 'text_block',
            'order_in_document': 1,
            'coordinates': {'x0': 72, 'y0': 118, 'x1': 300, 'y1': 133},  # Gap: 3pt (MUY PEQUEÑO)
            'source_page_number': 1
        },
        
        # CASO 2: Gap grande - NO debe fusionarse (párrafos separados)
        {
            'text': 'antipluralistas. Por ejemplo, los leninistas y algunas figuras religiosas muy intolerantes no piensan en',
            'type': 'text_block',
            'order_in_document': 2,
            'coordinates': {'x0': 72, 'y0': 160, 'x1': 523, 'y1': 175},  # Gap desde 133: 27pt (GRANDE)
            'source_page_number': 1
        },
        {
            'text': 'el pueblo moralmente puro y de voluntad infalible. No todos los que rechazan el pluralismo son',
            'type': 'text_block',
            'order_in_document': 3,
            'coordinates': {'x0': 72, 'y0': 200, 'x1': 480, 'y1': 215},  # Gap desde 175: 25pt (GRANDE)
            'source_page_number': 1
        },
        
        # CASO 3: Gap mediano con oración obviamente incompleta - DEBE fusionarse
        {
            'text': 'Esto significa que el político debe representar al pueblo de',
            'type': 'text_block',
            'order_in_document': 4,
            'coordinates': {'x0': 72, 'y0': 240, 'x1': 400, 'y1': 255},
            'source_page_number': 1
        },
        {
            'text': 'manera correcta y justa.',
            'type': 'text_block',
            'order_in_document': 5,
            'coordinates': {'x0': 72, 'y0': 258, 'x1': 200, 'y1': 273},  # Gap: 3pt (PEQUEÑO)
            'source_page_number': 1
        }
    ]
    
    metadata = {
        'source_file_path': 'populismo.pdf',
        'blocks_are_fitz_native': True,
        'author': 'Jan-Werner Müller'
    }
    
    print("📄 BLOQUES DE ENTRADA (simulando diferentes tipos de gaps):")
    for i, block in enumerate(test_blocks_gaps):
        text = block.get('text', '')
        coords = block.get('coordinates', {})
        if i > 0:
            prev_coords = test_blocks_gaps[i-1].get('coordinates', {})
            gap = coords.get('y0', 0) - prev_coords.get('y1', 0)
            print(f"  {i+1}. '{text[:60]}...' (Gap: {gap}pt)")
        else:
            print(f"  {i+1}. '{text[:60]}...' (Primer bloque)")
    
    print(f"\n🧪 VERIFICANDO CRITERIOS DE FUSIÓN:")
    
    # Verificar cada par de bloques
    for i in range(len(test_blocks_gaps) - 1):
        prev_block = test_blocks_gaps[i]
        curr_block = test_blocks_gaps[i + 1]
        
        prev_coords = prev_block.get('coordinates', {})
        curr_coords = curr_block.get('coordinates', {})
        gap = curr_coords.get('y0', 0) - prev_coords.get('y1', 0)
        
        should_merge = preprocessor._should_merge_blocks(
            prev_block['text'],
            curr_block['text'],
            prev_block['source_page_number'],
            curr_block['source_page_number'],
            gap,
            25  # max_gap
        )
        
        print(f"  Bloques {i+1}+{i+2}: Gap {gap}pt → {'FUSIONAR' if should_merge else 'NO FUSIONAR'}")
        
        # Explicar la decisión
        if gap > 20:  # 80% de 25pt
            print(f"    🔍 Gap grande ({gap}pt > 20pt) → Párrafos separados")
        elif gap > 15:  # 60% de 25pt
            print(f"    🔍 Gap mediano ({gap}pt) → Solo casos obvios")
        else:
            print(f"    🔍 Gap pequeño ({gap}pt ≤ 15pt) → Aplicar lógica normal")
    
    print(f"\n🔄 PROCESANDO CON LÓGICA CONSERVADORA...")
    
    try:
        processed_blocks, processed_metadata = preprocessor.process(test_blocks_gaps, metadata)
        
        print(f"\n✅ RESULTADO ({len(processed_blocks)} bloques):")
        for i, block in enumerate(processed_blocks):
            text = block.get('text', '')
            print(f"  {i+1}. '{text}'")
            print(f"      📏 {len(text)} caracteres")
            
            # Verificar resultados específicos
            if 'por una facción' in text:
                print("      ✅ CORRECTO: Oración cortada se fusionó")
            
            if 'no piensan en el pueblo moralmente puro' in text:
                print("      ❌ ERROR: Se fusionaron párrafos que debían estar separados")
            elif 'no piensan en' in text and 'el pueblo moralmente puro' not in text:
                print("      ✅ CORRECTO: Párrafos separados se mantuvieron separados")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Error detallado:")
    
    print("\n=== FIN DE LA PRUEBA CONSERVADORA ===")

if __name__ == "__main__":
    test_fusion_conservadora() 