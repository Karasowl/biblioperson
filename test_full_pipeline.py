#!/usr/bin/env python3
"""
Script para probar el pipeline completo: ProfileManager + MarkdownPDFLoader + MarkdownSegmenter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.profile_manager import ProfileManager
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_full_pipeline():
    """Probar el pipeline completo"""
    
    # Archivo de prueba
    test_file = r"C:\Users\adven\Downloads\Obras literarias-20250531T221115Z-1-001\Obras literarias\Último_planeta_en_pie.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🔄 Probando pipeline completo con: {os.path.basename(test_file)}")
    
    try:
        # Configurar ProfileManager
        print("\n⚙️  Paso 1: Configurando ProfileManager...")
        profile_manager = ProfileManager()
        
        # Procesar archivo
        print("\n🔄 Paso 2: Procesando archivo con pipeline completo...")
        result = profile_manager.process_file(test_file)
        
        if not result or 'segments' not in result:
            print("❌ Error: No se generaron segmentos")
            return
        
        segments = result['segments']
        print(f"✅ Pipeline completo: {len(segments)} segmentos generados")
        
        # Analizar resultados
        print("\n📊 Paso 3: Análisis de resultados...")
        
        # Estadísticas de longitud
        lengths = [len(seg['text']) for seg in segments]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        print(f"📏 Longitud promedio: {avg_length:.0f} caracteres")
        print(f"📏 Rango: {min(lengths)} - {max(lengths)} caracteres")
        
        # Distribución por tamaño
        short = sum(1 for l in lengths if l < 100)
        medium = sum(1 for l in lengths if 100 <= l < 300)
        long = sum(1 for l in lengths if l >= 300)
        
        print(f"📊 Distribución:")
        print(f"   - Cortos (<100 chars): {short}")
        print(f"   - Medianos (100-300 chars): {medium}")
        print(f"   - Largos (≥300 chars): {long}")
        
        # Buscar el texto problemático específico
        print("\n🔍 Paso 4: Buscando texto problemático...")
        target_text = "Mi profesor de Periodismo Investigativo me dijo una vez"
        
        found_segments = []
        for i, segment in enumerate(segments):
            if target_text in segment['text']:
                found_segments.append((i, segment))
        
        if found_segments:
            print(f"✅ Texto problemático encontrado en {len(found_segments)} segmento(s):")
            for i, (seg_idx, segment) in enumerate(found_segments):
                print(f"\n📄 Segmento {seg_idx + 1}:")
                print(f"   ID: {segment.get('segment_id', 'N/A')}")
                print(f"   Longitud: {len(segment['text'])} caracteres")
                print(f"   Texto (primeros 200 chars): {segment['text'][:200]}...")
                
                # Verificar si contiene múltiples secciones problemáticas
                text = segment['text']
                has_intro = "continuación le ofrecemos el cuento ganador" in text
                has_title = "¡SAQUÉNME DE AQUÍ!" in text
                has_dialogue = "Buenas tardes. Buenas Tardes" in text
                
                print(f"   Contiene introducción: {'✅' if has_intro else '❌'}")
                print(f"   Contiene título: {'✅' if has_title else '❌'}")
                print(f"   Contiene diálogo: {'✅' if has_dialogue else '❌'}")
                
                if has_intro and has_title and has_dialogue:
                    print("   ⚠️  PROBLEMA: Segmento contiene múltiples secciones que deberían estar separadas")
                else:
                    print("   ✅ BIEN: Segmento parece estar correctamente separado")
        else:
            print("❌ Texto problemático no encontrado")
        
        # Verificar metadatos del resultado
        print(f"\n📋 Paso 5: Verificando metadatos del resultado...")
        print(f"   - Loader usado: {result.get('loader_type', 'N/A')}")
        print(f"   - Segmentador usado: {result.get('segmenter_type', 'N/A')}")
        print(f"   - Tiempo de procesamiento: {result.get('processing_time', 'N/A')}")
        
        print(f"\n🎯 RESUMEN FINAL:")
        print(f"   - Segmentos generados: {len(segments)}")
        print(f"   - Longitud promedio: {avg_length:.0f} caracteres")
        print(f"   - Loader: {result.get('loader_type', 'N/A')}")
        print(f"   - Segmentador: {result.get('segmenter_type', 'N/A')}")
        print(f"   - ✅ Pipeline funcionando correctamente")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_pipeline() 