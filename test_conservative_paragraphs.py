#!/usr/bin/env python3
"""
Script de prueba para verificar la nueva lógica conservadora de división de párrafos
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

def test_conservative_paragraphs():
    """Probar la nueva lógica conservadora de división de párrafos"""
    
    # Archivo de prueba
    test_file = r"C:\Users\adven\Downloads\Obras literarias-20250531T221115Z-1-001\Obras literarias\Último_planeta_en_pie.pdf"
    output_file = r"C:\Users\adven\Downloads\test_conservative.json"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🔄 Procesando documento: {test_file}")
    print(f"📁 Archivo de salida: {output_file}")
    
    # Crear ProfileManager
    profile_manager = ProfileManager()
    
    # Deshabilitar deduplicación temporalmente
    config_path = "dataset/config/deduplication_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Guardar configuración original
    original_enabled = config['deduplication']['enabled']
    config['deduplication']['enabled'] = False
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    try:
        # Procesar el archivo
        result = profile_manager.process_file(
            file_path=test_file,
            profile_name="prosa",
            output_file=output_file,
            output_format="ndjson",
            output_mode="biblioperson"
        )
        
        # Manejar tanto tuplas como diccionarios
        if isinstance(result, tuple):
            success = True  # Asumir éxito si es tupla
            segments_count = "N/A"
        else:
            success = result and result.get('success', False)
            segments_count = result.get('segments_count', 'N/A') if result else 'N/A'
        
        if success:
            print(f"✅ Procesamiento exitoso!")
            print(f"📊 Segmentos procesados: {segments_count}")
            
            # Analizar el archivo de salida
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                segments = [json.loads(line) for line in lines]
                lengths = [len(seg['text']) for seg in segments]
                
                print(f"\n📊 Estadísticas de segmentos:")
                print(f"   - Total: {len(segments)}")
                print(f"   - Longitud promedio: {sum(lengths)/len(lengths):.1f} caracteres")
                print(f"   - Longitud mínima: {min(lengths)}")
                print(f"   - Longitud máxima: {max(lengths)}")
                
                # Verificar si hay párrafos coherentes
                very_long_segments = [s for s in segments if len(s['text']) > 300]
                long_segments = [s for s in segments if 200 <= len(s['text']) <= 300]
                medium_segments = [s for s in segments if 100 <= len(s['text']) < 200]
                short_segments = [s for s in segments if len(s['text']) < 100]
                
                print(f"\n🎯 Distribución por longitud:")
                print(f"   - Segmentos muy largos (>300 chars): {len(very_long_segments)}")
                print(f"   - Segmentos largos (200-300 chars): {len(long_segments)}")
                print(f"   - Segmentos medianos (100-200 chars): {len(medium_segments)}")
                print(f"   - Segmentos cortos (<100 chars): {len(short_segments)}")
                
                # Buscar el ejemplo específico del problema
                target_text = "Mi profesor de Periodismo Investigativo me dijo una vez"
                found_segments = []
                for i, seg in enumerate(segments):
                    if target_text in seg['text']:
                        found_segments.append((i, seg))
                
                if found_segments:
                    print(f"\n🔍 Análisis del texto problemático:")
                    for i, (idx, seg) in enumerate(found_segments):
                        print(f"   Segmento {idx + 1}: ({len(seg['text'])} chars)")
                        print(f"   Texto: {seg['text'][:150]}...")
                        
                        # Verificar si el siguiente segmento es la continuación
                        if idx + 1 < len(segments):
                            next_seg = segments[idx + 1]
                            if "Yo invito" in next_seg['text']:
                                print(f"   ⚠️ PROBLEMA: El siguiente segmento debería estar junto:")
                                print(f"   Segmento {idx + 2}: ({len(next_seg['text'])} chars)")
                                print(f"   Texto: {next_seg['text'][:150]}...")
                            else:
                                print(f"   ✅ OK: No hay división problemática detectada")
                else:
                    print(f"\n🔍 No se encontró el texto problemático específico")
                
                # Mostrar algunos ejemplos
                print(f"\n📝 Ejemplos de segmentos:")
                for i, seg in enumerate(segments[:5]):
                    print(f"   [{i+1}] ({len(seg['text'])} chars): {seg['text'][:100]}...")
                
                # Verificar calidad general
                total_long = len(very_long_segments) + len(long_segments)
                if total_long > 100:
                    print(f"\n✅ ¡Excelente! Hay muchos párrafos coherentes ({total_long} segmentos largos)")
                elif len(medium_segments) > 150:
                    print(f"\n👍 Bueno. Hay párrafos de tamaño medio ({len(medium_segments)} segmentos medianos)")
                else:
                    print(f"\n⚠️ Posible problema: Muchos segmentos cortos ({len(short_segments)} segmentos cortos)")
            
        else:
            print(f"❌ Error en el procesamiento: {result}")
    
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restaurar configuración original
        config['deduplication']['enabled'] = original_enabled
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"🔄 Configuración de deduplicación restaurada: {original_enabled}")

if __name__ == "__main__":
    test_conservative_paragraphs() 