#!/usr/bin/env python3
"""
Script para probar el nuevo sistema MarkdownPDFLoader + MarkdownSegmenter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.profile_manager import ProfileManager
import logging
import json
import yaml

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_markdown_segmentation():
    """Probar el nuevo sistema de segmentación basado en estructura visual"""
    
    # Archivo de prueba
    test_file = r"C:\Users\adven\Downloads\Obras literarias-20250531T221115Z-1-001\Obras literarias\Último_planeta_en_pie.pdf"
    output_file = r"C:\Users\adven\Downloads\test_markdown_segmentation.json"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🔄 Probando nuevo sistema MarkdownPDFLoader + MarkdownSegmenter")
    print(f"   📄 Archivo: {test_file}")
    print(f"   📤 Salida: {output_file}")
    
    # Deshabilitar deduplicación temporalmente
    config_path = "dataset/config/deduplication_config.yaml"
    original_enabled = True
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            original_enabled = config.get('deduplication', {}).get('enabled', True)
            config['deduplication']['enabled'] = False
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            print(f"🔄 Deduplicación deshabilitada temporalmente")
        
        # Crear ProfileManager
        manager = ProfileManager()
        
        # Procesar archivo con perfil prosa (debería auto-detectar MarkdownSegmenter)
        print(f"\n🎯 Procesando con perfil 'prosa'...")
        
        processed_items, stats, metadata = manager.process_file(
            file_path=test_file,
            profile_name='prosa',
            output_file=output_file,
            output_format='json'
        )
        
        print(f"\n📊 Resultados:")
        print(f"   - Segmentos generados: {len(processed_items)}")
        print(f"   - Archivo de salida: {output_file}")
        
        if processed_items:
            # Analizar distribución de longitudes
            lengths = [len(item.text) for item in processed_items]
            lengths.sort()
            
            print(f"\n📈 Distribución de longitudes:")
            print(f"   - Longitud promedio: {sum(lengths) / len(lengths):.1f} caracteres")
            print(f"   - Longitud mínima: {min(lengths)} caracteres")
            print(f"   - Longitud máxima: {max(lengths)} caracteres")
            
            # Contar por rangos
            short = len([l for l in lengths if l < 100])
            medium = len([l for l in lengths if 100 <= l < 300])
            long_segs = len([l for l in lengths if l >= 300])
            
            print(f"   - Segmentos cortos (<100 chars): {short}")
            print(f"   - Segmentos medianos (100-300 chars): {medium}")
            print(f"   - Segmentos largos (≥300 chars): {long_segs}")
            
            # Buscar el texto problemático específico
            target_text = "Mi profesor de Periodismo Investigativo"
            found_segments = []
            
            for i, item in enumerate(processed_items):
                if target_text in item.text:
                    found_segments.append((i, item))
            
            print(f"\n🎯 Texto problemático encontrado en {len(found_segments)} segmento(s):")
            for i, (seg_idx, item) in enumerate(found_segments):
                print(f"   Segmento {seg_idx + 1}: {len(item.text)} caracteres")
                print(f"   Tipo: {item.segment_type}")
                print(f"   Texto: {item.text[:200]}...")
                if i < len(found_segments) - 1:
                    print()
            
            # Mostrar primeros 3 segmentos como muestra
            print(f"\n📄 Primeros 3 segmentos como muestra:")
            for i, item in enumerate(processed_items[:3]):
                print(f"   Segmento {i + 1}: {len(item.text)} chars, tipo='{item.segment_type}'")
                print(f"              texto: {item.text[:100]}...")
        
        print(f"\n✅ Procesamiento completado exitosamente")
        
        # Verificar que se usó MarkdownSegmenter
        if 'segmenter_used' in metadata:
            print(f"🔍 Segmentador usado: {metadata['segmenter_used']}")
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restaurar configuración original
        if os.path.exists(config_path):
            config['deduplication']['enabled'] = original_enabled
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            print(f"🔄 Configuración de deduplicación restaurada: {original_enabled}")

if __name__ == "__main__":
    test_markdown_segmentation() 