#!/usr/bin/env python3
"""
Script para verificar que TODOS los perfiles que usan el segmentador "heading" 
tienen las mejoras de fusión inteligente aplicadas.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.profile_manager import ProfileManager

def test_todos_perfiles():
    """Prueba todos los perfiles que usan el segmentador heading."""
    
    # Configurar logging
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=== VERIFICANDO TODOS LOS PERFILES CON SEGMENTADOR HEADING ===\n")
    
    # Crear ProfileManager
    profile_manager = ProfileManager()
    
    # Lista de perfiles que deberían usar heading
    perfiles_heading = [
        'prosa',
        'book_structure', 
        'chapter_heading',
        'perfil_docx_heading'
    ]
    
    # Bloques de prueba con el problema específico
    test_blocks_problema = [
        {
            'text': 'económicamente inestables, los analfabetas, los poco sofisticados y las personalidades',
            'type': 'text_block',
            'order_in_document': 0,
            'coordinates': {'x0': 72, 'y0': 100, 'x1': 523, 'y1': 115},
            'source_page_number': 1
        },
        {
            'text': 'autoritarias".22 Los blancos inmediatos de estos teóricos sociales fueron el macartismo y la John',
            'type': 'text_block',
            'order_in_document': 1,
            'coordinates': {'x0': 72, 'y0': 118, 'x1': 500, 'y1': 133},  # Gap: 3pt (PEQUEÑO)
            'source_page_number': 1
        },
        {
            'text': 'Birch Society, pero sus diagnósticos a menudo se extendían a la originaria revuelta populista en los',
            'type': 'text_block',
            'order_in_document': 2,
            'coordinates': {'x0': 72, 'y0': 121, 'x1': 520, 'y1': 136},  # Gap: 3pt (PEQUEÑO)
            'source_page_number': 1
        }
    ]
    
    metadata = {
        'source_file_path': 'populismo.pdf',
        'blocks_are_fitz_native': True,
        'author': 'Jan-Werner Müller'
    }
    
    for perfil_nombre in perfiles_heading:
        print(f"🔍 PROBANDO PERFIL: {perfil_nombre}")
        
        # Cargar perfil
        profile = profile_manager.get_profile(perfil_nombre)
        if not profile:
            print(f"   ❌ ERROR: No se pudo cargar el perfil '{perfil_nombre}'")
            continue
            
        print(f"   ✅ Perfil cargado: {profile['name']}")
        
        # Verificar que use el segmentador heading
        segmenter_type = profile.get('segmenter')
        if segmenter_type != 'heading':
            print(f"   ⚠️  AVISO: Perfil usa segmentador '{segmenter_type}', no 'heading'")
            continue
            
        # Verificar configuración del preprocessor
        preprocessor_config = profile.get('pre_processor_config')
        if not preprocessor_config:
            print(f"   ❌ ERROR: No tiene configuración de pre-procesador")
            continue
            
        # Verificar configuraciones clave
        tiene_fusion = preprocessor_config.get('aggressive_merge_for_pdfs', False)
        tiene_filtrado = preprocessor_config.get('filter_insignificant_blocks', False)
        
        if not tiene_fusion:
            print(f"   ❌ ERROR: No tiene fusión agresiva habilitada")
            continue
            
        if not tiene_filtrado:
            print(f"   ❌ ERROR: No tiene filtrado de bloques insignificantes")
            continue
            
        print(f"   ✅ Configuración OK: fusión={tiene_fusion}, filtrado={tiene_filtrado}")
        
        # Crear preprocessor y probar
        try:
            from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
            preprocessor = CommonBlockPreprocessor(config=preprocessor_config)
            
            # Probar fusión específica
            should_merge = preprocessor._should_merge_blocks(
                test_blocks_problema[0]['text'],
                test_blocks_problema[1]['text'],
                test_blocks_problema[0]['source_page_number'],
                test_blocks_problema[1]['source_page_number'],
                3,  # gap pequeño
                25  # max_gap
            )
            
            if should_merge:
                print(f"   ✅ FUSIÓN OK: Detecta correctamente que debe fusionar oraciones cortadas")
            else:
                print(f"   ❌ FUSIÓN FALLA: No detecta que debe fusionar oraciones cortadas")
                
            # Probar procesamiento completo
            processed_blocks, _ = preprocessor.process(test_blocks_problema, metadata)
            
            # Verificar resultado
            fusion_correcta = False
            for block in processed_blocks:
                text = block.get('text', '')
                if 'personalidades autoritarias' in text:
                    fusion_correcta = True
                    break
                    
            if fusion_correcta:
                print(f"   ✅ RESULTADO OK: Las palabras cortadas se fusionaron correctamente")
            else:
                print(f"   ❌ RESULTADO FALLA: Las palabras cortadas NO se fusionaron")
                print(f"      Bloques resultantes: {len(processed_blocks)}")
                for i, block in enumerate(processed_blocks):
                    text = block.get('text', '')[:80]
                    print(f"        {i+1}. '{text}...'")
                
        except Exception as e:
            print(f"   ❌ ERROR al procesar: {e}")
            
        print()  # Línea en blanco entre perfiles
    
    print("=== RESUMEN ===")
    print("Si TODOS los perfiles muestran '✅ RESULTADO OK', entonces las mejoras están aplicadas correctamente.")
    print("Si algún perfil muestra '❌ RESULTADO FALLA', ese perfil necesita corrección.")
    print("\n⚠️  IMPORTANTE: Usa el perfil que muestre '✅ RESULTADO OK' en tu UI.")

if __name__ == "__main__":
    test_todos_perfiles() 