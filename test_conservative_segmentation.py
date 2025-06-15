#!/usr/bin/env python3
"""
Script para probar la segmentación conservadora del MarkdownSegmenter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.loaders.markdown_pdf_loader import MarkdownPDFLoader
from dataset.processing.segmenters.markdown_segmenter import MarkdownSegmenter
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_conservative_segmentation():
    """Probar la segmentación conservadora"""
    
    # Archivo de prueba
    test_file = r"C:\Users\adven\Downloads\Obras literarias-20250531T221115Z-1-001\Obras literarias\Último_planeta_en_pie.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🔄 Probando segmentación conservadora con: {os.path.basename(test_file)}")
    
    try:
        # 1. Cargar con MarkdownPDFLoader
        print("\n📖 Paso 1: Cargando con MarkdownPDFLoader...")
        loader = MarkdownPDFLoader(file_path=test_file)
        loaded_data = loader.load()
        raw_blocks = loaded_data.get('blocks', [])
        
        print(f"✅ MarkdownPDFLoader: {len(raw_blocks)} bloques cargados")
        
        # 2. Segmentar con MarkdownSegmenter conservador
        print("\n🔗 Paso 2: Segmentando con MarkdownSegmenter CONSERVADOR...")
        segmenter = MarkdownSegmenter()
        segments = segmenter.segment(raw_blocks)
        
        print(f"✅ MarkdownSegmenter: {len(segments)} segmentos generados")
        
        # 3. Analizar resultados
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
        
        # 4. Buscar el texto problemático específico
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
                print(f"   ID: {segment['segment_id']}")
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
        
        # 5. Mostrar primeros segmentos para inspección
        print(f"\n📋 Paso 5: Primeros 5 segmentos para inspección:")
        for i, segment in enumerate(segments[:5]):
            print(f"\n--- Segmento {i+1} ---")
            print(f"ID: {segment['segment_id']}")
            print(f"Longitud: {len(segment['text'])} caracteres")
            print(f"Texto: {segment['text'][:150]}...")
        
        print(f"\n🎯 RESUMEN:")
        print(f"   - Bloques originales: {len(raw_blocks)}")
        print(f"   - Segmentos finales: {len(segments)}")
        print(f"   - Reducción: {((len(raw_blocks) - len(segments)) / len(raw_blocks) * 100):.1f}%")
        print(f"   - Longitud promedio: {avg_length:.0f} caracteres")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conservative_segmentation() 