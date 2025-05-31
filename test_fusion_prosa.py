#!/usr/bin/env python3
"""
Script para probar la fusión con el perfil PROSA (el correcto según nuestro sistema simplificado).
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.profile_manager import ProfileManager

def test_fusion_prosa():
    """Prueba la fusión usando el perfil PROSA (el correcto)."""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== PRUEBA DE FUSIÓN CON PERFIL PROSA (CORRECTO) ===\n")
    
    # Crear ProfileManager
    profile_manager = ProfileManager()
    
    # Cargar el perfil PROSA (el que deberíamos estar usando)
    profile = profile_manager.get_profile('prosa')
    if not profile:
        print("❌ Error: No se pudo cargar el perfil 'prosa'")
        return
        
    print(f"✅ Perfil cargado: {profile['name']}")
    print(f"📄 Descripción: {profile['description']}")
    
    # Obtener configuración del preprocessor del perfil
    preprocessor_config = profile.get('pre_processor_config')
    if preprocessor_config:
        print(f"🔧 Configuración del preprocessor: SÍ PRESENTE")
        print(f"   - filter_insignificant_blocks: {preprocessor_config.get('filter_insignificant_blocks')}")
        print(f"   - aggressive_merge_for_pdfs: {preprocessor_config.get('aggressive_merge_for_pdfs')}")
        print(f"   - max_vertical_gap_aggressive_pt: {preprocessor_config.get('max_vertical_gap_aggressive_pt')}")
    else:
        print("❌ Configuración del preprocessor: NO PRESENTE")
        return
    
    # Crear preprocessor con la configuración del perfil
    from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
    preprocessor = CommonBlockPreprocessor(config=preprocessor_config)
    
    # Simular los bloques problema del usuario
    test_blocks_problema_usuario = [
        # El problema específico del usuario: "...y un" cortado
        {
            'text': 'no sólo creará un Estado PiS o un Estado Fidesz, sino que también buscará crear un pueblo PiS y un',
            'type': 'text_block',
            'order_in_document': 0,
            'coordinates': {'x0': 72, 'y0': 250, 'x1': 523, 'y1': 265},
            'source_page_number': 42
        },
        {
            'text': 'pueblo Fidesz. Los populistas en el poder harán todo lo posible por institucionalizar su interpretación',
            'type': 'text_block', 
            'order_in_document': 1,
            'coordinates': {'x0': 72, 'y0': 268, 'x1': 480, 'y1': 283},
            'source_page_number': 42
        },
        {
            'text': 'de la democracia. Por esta razón, es fundamental entender el populismo.',
            'type': 'text_block',
            'order_in_document': 2, 
            'coordinates': {'x0': 72, 'y0': 286, 'x1': 350, 'y1': 301},
            'source_page_number': 42
        }
    ]
    
    metadata = {
        'source_file_path': 'populismo.pdf',
        'blocks_are_fitz_native': True,
        'author': 'Jan-Werner Müller'
    }
    
    print(f"\n📄 BLOQUES DE ENTRADA (simulando el problema del usuario):")
    for i, block in enumerate(test_blocks_problema_usuario):
        text = block.get('text', '')
        print(f"  {i+1}. '{text}'")
    
    print(f"\n🔄 PROCESANDO CON PERFIL PROSA...")
    
    # Procesar con el preprocessor usando la configuración del perfil PROSA
    try:
        processed_blocks, processed_metadata = preprocessor.process(test_blocks_problema_usuario, metadata)
        
        print(f"\n✅ BLOQUES DESPUÉS DEL PROCESAMIENTO ({len(processed_blocks)}):")
        for i, block in enumerate(processed_blocks):
            text = block.get('text', '')
            print(f"  {i+1}. '{text}'")
            print(f"      📏 Longitud: {len(text)} caracteres")
            
            # Verificar si se resolvió el problema específico del usuario
            if 'pueblo PiS y un' in text and 'pueblo Fidesz' in text:
                print("      ✅ PROBLEMA RESUELTO: El texto cortado se fusionó correctamente")
                print("      🎯 ANTES: '...pueblo PiS y un' | 'pueblo Fidesz...'")
                print("      🎯 AHORA: Texto completo unificado")
            elif 'pueblo PiS y un' in text and 'pueblo Fidesz' not in text:
                print("      ❌ PROBLEMA PERSISTE: El texto sigue cortado")
    
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        logger.exception("Error detallado:")
    
    print(f"\n📋 RESUMEN:")
    print(f"   - Perfil usado: PROSA (el correcto para contenido en prosa)")
    print(f"   - Pre-procesador: CommonBlockPreprocessor con fusión inteligente")
    print(f"   - Segmentador: HeadingSegmenter para detectar estructura")
    print(f"   - Configuración: Optimizada para PDFs problemáticos")
    
    print("\n=== FIN DE LA PRUEBA CON PERFIL PROSA ===")

if __name__ == "__main__":
    test_fusion_prosa() 