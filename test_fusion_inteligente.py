#!/usr/bin/env python3
"""
Script para probar la fusión inteligente de bloques que resuelve el problema de cortes en medio de oraciones.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor

def test_fusion_inteligente():
    """Prueba la fusión inteligente con el ejemplo específico del problema."""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== PRUEBA DE FUSIÓN INTELIGENTE ===\n")
    
    # Configuración optimizada
    config_fusion = {
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
    
    preprocessor = CommonBlockPreprocessor(config=config_fusion)
    
    # Simular exactamente el problema que describiste
    test_blocks_problema = [
        # Primer párrafo completo (que debería mantenerse intacto)
        {'text': 'Los populistas, en cambio, persisten en su postulado de representación sin importarles nada más;', 'type': 'text_block', 'order_in_document': 0, 'coordinates': {'x0': 100, 'y0': 100, 'x1': 400, 'y1': 115}, 'source_page_number': 1},
        {'text': 'puesto que este derecho es de una naturaleza moral y simbólica —no empírica—, no puede ser', 'type': 'text_block', 'order_in_document': 1, 'coordinates': {'x0': 100, 'y0': 118, 'x1': 400, 'y1': 133}, 'source_page_number': 1},
        
        # El problema específico: "hablar solamente por una" + "facción"
        {'text': 'Los políticos no populistas no utilizan discursos enardecedores para hablar solamente por una', 'type': 'text_block', 'order_in_document': 2, 'coordinates': {'x0': 100, 'y0': 200, 'x1': 400, 'y1': 215}, 'source_page_number': 1},
        {'text': 'facción (aunque hay quienes lo hacen: al menos en Europa, los nombres de algunos partidos suelen', 'type': 'text_block', 'order_in_document': 3, 'coordinates': {'x0': 100, 'y0': 218, 'x1': 400, 'y1': 233}, 'source_page_number': 1},
        {'text': 'indicar que éstos sólo se proponen representar a una clientela específica, como a los pequeños', 'type': 'text_block', 'order_in_document': 4, 'coordinates': {'x0': 100, 'y0': 236, 'x1': 400, 'y1': 251}, 'source_page_number': 1},
        {'text': 'productores agrícolas o a los cristianos).', 'type': 'text_block', 'order_in_document': 5, 'coordinates': {'x0': 100, 'y0': 254, 'x1': 280, 'y1': 269}, 'source_page_number': 1},
    ]
    
    metadata = {'source_file_path': 'populismo.pdf', 'blocks_are_fitz_native': True}
    
    print("BLOQUES DE ENTRADA (simulando el problema):")
    for i, block in enumerate(test_blocks_problema):
        text = block.get('text', '')
        print(f"  {i+1}. '{text}'")
    
    print(f"\n--- PROCESANDO CON FUSIÓN INTELIGENTE ---")
    processed_blocks, processed_metadata = preprocessor.process(test_blocks_problema, metadata)
    
    print(f"\nBLOQUES DESPUÉS DEL PROCESAMIENTO: {len(processed_blocks)}")
    for i, block in enumerate(processed_blocks):
        text = block.get('text', '')
        print(f"  {i+1}. '{text}'")
        print(f"      Longitud: {len(text)} caracteres")
        
        # Verificar si resolvió el problema específico
        if 'hablar solamente por una' in text and 'facción' in text:
            print("      ✅ PROBLEMA RESUELTO: La oración completa se mantuvo junta")
        elif 'hablar solamente por una' in text and 'facción' not in text:
            print("      ❌ PROBLEMA PERSISTE: La oración sigue cortada")
    
    # Prueba adicional: Casos específicos de fusión
    print(f"\n=== PRUEBAS ESPECÍFICAS DE CRITERIOS DE FUSIÓN ===")
    
    test_cases = [
        # Caso 1: Texto que termina con artículo + texto que empieza con minúscula
        (['Los políticos no populistas no utilizan discursos enardecedores para hablar solamente por una', 
          'facción (aunque hay quienes lo hacen: al menos en Europa'], 
         "Artículo + minúscula"),
        
        # Caso 2: Texto que termina con coma + continuación
        (['En general,', 'los políticos democráticos aceptan que la representación es temporal'], 
         "Coma + continuación"),
        
        # Caso 3: Texto que termina sin puntuación + continuación lógica
        (['Los populistas se ven obligados a sembrar dudas respecto de las instituciones que producen', 
          'los resultados "moralmente incorrectos"'], 
         "Sin puntuación + continuación"),
    ]
    
    for i, (texts, description) in enumerate(test_cases):
        should_merge = preprocessor._should_merge_blocks(
            texts[0], texts[1], 1, 1, 20, 25
        )
        separator = preprocessor._get_merge_separator(texts[0], texts[1])
        merged = texts[0] + separator + texts[1]
        
        print(f"\nCaso {i+1}: {description}")
        print(f"  Texto 1: '{texts[0]}'")
        print(f"  Texto 2: '{texts[1]}'")
        print(f"  ¿Debe fusionarse?: {'SÍ' if should_merge else 'NO'}")
        if should_merge:
            print(f"  Separador: '{separator}'")
            print(f"  Resultado: '{merged}'")
    
    print("\n=== FIN DE LA PRUEBA ===")

if __name__ == "__main__":
    test_fusion_inteligente() 