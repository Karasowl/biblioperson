#!/usr/bin/env python3
"""
Script para probar la fusión usando el ProfileManager real, simulando el problema específico.
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

def test_fusion_real():
    """Prueba la fusión usando el ProfileManager real."""
    
    # Configurar logging detallado
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== PRUEBA DE FUSIÓN CON PROFILE MANAGER REAL ===\n")
    
    # Crear ProfileManager
    profile_manager = ProfileManager()
    
    # Cargar el perfil book_structure
    profile = profile_manager.get_profile('book_structure')
    if not profile:
        print("❌ Error: No se pudo cargar el perfil 'book_structure'")
        return
        
    print(f"✅ Perfil cargado: {profile['name']}")
    
    # Obtener configuración del preprocessor del perfil
    preprocessor_config = profile.get('pre_processor_config')
    print(f"📋 Configuración del preprocessor: {preprocessor_config}")
    
    # Crear preprocessor con la configuración del perfil
    preprocessor = CommonBlockPreprocessor(config=preprocessor_config)
    print(f"🔧 Preprocessor creado con config: {preprocessor.config}")
    
    # Simular bloques problema más realistas
    test_blocks_real = [
        # Problema específico del usuario: texto que termina con "un"
        {
            'text': 'no sólo creará un Estado PiS o un Estado Fidesz, sino que también buscará crear un pueblo PiS y un',
            'type': 'text_block',
            'order_in_document': 0,
            'coordinates': {'x0': 72, 'y0': 250, 'x1': 523, 'y1': 265},
            'source_page_number': 42
        },
        {
            'text': 'pueblo Fidesz. Los populistas en el poder harán todo lo posible por',
            'type': 'text_block', 
            'order_in_document': 1,
            'coordinates': {'x0': 72, 'y0': 268, 'x1': 340, 'y1': 283},
            'source_page_number': 42
        },
        {
            'text': 'institucionalizar su interpretación de la democracia. Por esta razón,',
            'type': 'text_block',
            'order_in_document': 2, 
            'coordinates': {'x0': 72, 'y0': 286, 'x1': 380, 'y1': 301},
            'source_page_number': 42
        },
        # Otro caso problema: artículo al final
        {
            'text': 'Los políticos no populistas no utilizan discursos enardecedores para hablar solamente por una',
            'type': 'text_block',
            'order_in_document': 3,
            'coordinates': {'x0': 72, 'y0': 320, 'x1': 523, 'y1': 335}, 
            'source_page_number': 42
        },
        {
            'text': 'facción (aunque hay quienes lo hacen: al menos en Europa, los nombres de algunos partidos suelen',
            'type': 'text_block',
            'order_in_document': 4,
            'coordinates': {'x0': 72, 'y0': 338, 'x1': 523, 'y1': 353},
            'source_page_number': 42
        }
    ]
    
    metadata = {
        'source_file_path': 'populismo.pdf',
        'blocks_are_fitz_native': True,
        'author': 'Jan-Werner Müller'
    }
    
    print(f"\n📄 BLOQUES DE ENTRADA ({len(test_blocks_real)}):")
    for i, block in enumerate(test_blocks_real):
        text = block.get('text', '')
        print(f"  {i+1}. '{text}'")
    
    print(f"\n🔄 PROCESANDO CON PROFILE MANAGER...")
    
    # Verificar criterios específicos antes del procesamiento
    print(f"\n🔍 VERIFICACIÓN DE CRITERIOS DE FUSIÓN:")
    
    # Caso 1: "un pueblo PiS y un" + "pueblo Fidesz"
    should_merge_1 = preprocessor._should_merge_blocks(
        test_blocks_real[0]['text'], 
        test_blocks_real[1]['text'],
        test_blocks_real[0]['source_page_number'],
        test_blocks_real[1]['source_page_number'],
        3,  # gap pequeño
        25  # max_gap
    )
    print(f"  ¿Fusionar bloque 1+2?: {'SÍ' if should_merge_1 else 'NO'}")
    
    # Caso 2: "por una" + "facción"  
    should_merge_2 = preprocessor._should_merge_blocks(
        test_blocks_real[3]['text'],
        test_blocks_real[4]['text'], 
        test_blocks_real[3]['source_page_number'],
        test_blocks_real[4]['source_page_number'],
        3,  # gap pequeño
        25  # max_gap
    )
    print(f"  ¿Fusionar bloque 4+5?: {'SÍ' if should_merge_2 else 'NO'}")
    
    # Procesar con el preprocessor usando la configuración del perfil
    try:
        processed_blocks, processed_metadata = preprocessor.process(test_blocks_real, metadata)
        
        print(f"\n✅ BLOQUES DESPUÉS DEL PROCESAMIENTO ({len(processed_blocks)}):")
        for i, block in enumerate(processed_blocks):
            text = block.get('text', '')
            print(f"  {i+1}. '{text}'")
            print(f"      📏 Longitud: {len(text)} caracteres")
            
            # Verificar problemas específicos
            if 'un pueblo PiS y un' in text and 'pueblo Fidesz' in text:
                print("      ✅ RESUELTO: Primer problema fusionado correctamente")
            elif 'un pueblo PiS y un' in text and 'pueblo Fidesz' not in text:
                print("      ❌ PERSISTE: Primer problema no resuelto")
                
            if 'por una' in text and 'facción' in text:
                print("      ✅ RESUELTO: Segundo problema fusionado correctamente")
            elif 'por una' in text and 'facción' not in text:
                print("      ❌ PERSISTE: Segundo problema no resuelto")
    
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        logger.exception("Error detallado:")
    
    print("\n=== FIN DE LA PRUEBA REAL ===")

if __name__ == "__main__":
    test_fusion_real() 