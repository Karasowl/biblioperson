#!/usr/bin/env python3
"""
Debug específico para VerseSegmenter - Analizar por qué está creando 
segmentos enormes en lugar de separar poemas individuales.
"""

import sys
import os
import json
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def analyze_verse_segmentation():
    """Analiza detalladamente cómo el VerseSegmenter procesa los bloques del PDFLoader"""
    
    pdf_path = r"C:\Users\adven\Downloads\Mario Benedetti Antologia Poética.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        return
    
    print("🔍 ANÁLISIS DETALLADO DE SEGMENTACIÓN DE VERSOS")
    print(f"📄 Archivo: {pdf_path}")
    print("=" * 80)
    
    # PASO 1: Cargar documento con PDFLoader V7.2
    print("📋 PASO 1: CARGANDO CON PDFLOADER V7.2")
    print("-" * 50)
    
    try:
        loader = PDFLoader(pdf_path)
        result = loader.load()
        blocks = result.get('blocks', [])
        
        print(f"✅ PDFLoader completado")
        print(f"📦 Bloques generados: {len(blocks)}")
        print(f"📊 Metadata: {json.dumps(result.get('metadata', {}), indent=2, ensure_ascii=False)}")
        print()
        
        # Analizar estructura de bloques
        print("🔍 ESTRUCTURA DE BLOQUES:")
        for i, block in enumerate(blocks[:10]):  # Primeros 10 bloques
            text = block.get('text', '')
            print(f"  📄 Bloque {i+1}:")
            print(f"    📏 Longitud: {len(text)} caracteres")
            print(f"    📝 Texto: {repr(text[:100])}...")
            print(f"    🏷️ Metadata: {block.get('metadata', {})}")
            print()
            
    except Exception as e:
        print(f"❌ Error en PDFLoader: {e}")
        return
    
    # PASO 2: Analizar con VerseSegmenter
    print("\n📋 PASO 2: PROCESANDO CON VERSESEGMENTER V2.0")
    print("-" * 50)
    
    try:
        segmenter = VerseSegmenter()
        
        # Habilitar logging detallado
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        print("🔄 Iniciando segmentación...")
        segments = segmenter.segment(blocks)
        
        print(f"✅ Segmentación completada")
        print(f"🎭 Segmentos creados: {len(segments)}")
        print()
        
        # Analizar cada segmento
        print("🔍 ANÁLISIS DE SEGMENTOS:")
        for i, segment in enumerate(segments):
            print(f"  🎭 Segmento {i+1}:")
            print(f"    📋 Tipo: {segment.get('type')}")
            print(f"    🎯 Título: {segment.get('title', 'Sin título')}")
            print(f"    📏 Longitud total: {len(segment.get('text', ''))} caracteres")
            print(f"    📊 Versos: {segment.get('verse_count', 0)}")
            print(f"    📦 Bloques origen: {segment.get('source_blocks', 0)}")
            print(f"    🔧 Método: {segment.get('detection_method', 'principal')}")
            print(f"    📝 Texto preview: {repr(segment.get('text', '')[:200])}...")
            print()
            
            # Si es un segmento muy largo, analizar títulos internos
            text = segment.get('text', '')
            if len(text) > 2000:  # Segmento sospechosamente largo
                print(f"    ⚠️ SEGMENTO LARGO DETECTADO - ANALIZANDO TÍTULOS INTERNOS:")
                lines = text.split('\n')
                potential_titles = []
                
                for j, line in enumerate(lines):
                    line = line.strip()
                    if line and len(line) < 100:
                        # Buscar patrones de títulos
                        if (line.isupper() and len(line) < 50) or \
                           (line.startswith('"') and line.endswith('"')) or \
                           (not line.endswith('.') and not line.endswith(',') and len(line) < 80):
                            potential_titles.append((j+1, line))
                
                print(f"    🎯 Posibles títulos internos encontrados: {len(potential_titles)}")
                for line_num, title in potential_titles[:10]:  # Primeros 10
                    print(f"      📍 Línea {line_num}: '{title}'")
                print()
        
    except Exception as e:
        print(f"❌ Error en VerseSegmenter: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # PASO 3: Diagnóstico del problema
    print("\n📋 PASO 3: DIAGNÓSTICO DEL PROBLEMA")
    print("-" * 50)
    
    print("💡 ANÁLISIS:")
    
    if len(blocks) < 10:
        print("⚠️ PROBLEMA POTENCIAL: Muy pocos bloques del PDFLoader")
        print("   El PDFLoader V7.2 está creando bloques demasiado grandes")
        print("   Esto hace que cada bloque contenga múltiples poemas")
        print()
    
    if len(segments) < 10 and len(segments) > 0:
        print("⚠️ PROBLEMA CONFIRMADO: Segmentos muy grandes")
        print("   El VerseSegmenter no está detectando límites entre poemas")
        print("   Cada segmento contiene múltiples poemas concatenados")
        print()
    
    if len(segments) == 0:
        print("❌ PROBLEMA CRÍTICO: Cero segmentos")
        print("   Ni el algoritmo principal ni el fallback funcionaron")
        print()
    
    # PASO 4: Recomendaciones
    print("💡 RECOMENDACIONES:")
    
    if len(blocks) < 10:
        print("1. 🔧 Modificar PDFLoader para crear bloques más granulares")
        print("   - Dividir por párrafos en lugar de páginas/secciones grandes")
        print("   - Detectar saltos de línea significativos")
        print()
    
    if len(segments) > 0 and any(len(s.get('text', '')) > 2000 for s in segments):
        print("2. 🔧 Mejorar VerseSegmenter para detectar títulos internos")
        print("   - Buscar patrones de títulos dentro de bloques grandes")
        print("   - Dividir bloques grandes antes de la segmentación")
        print()
    
    print("3. 🔧 Ajustar coordinación entre PDFLoader y VerseSegmenter")
    print("   - El PDFLoader debe entregar bloques de granularidad adecuada")
    print("   - El VerseSegmenter debe manejar títulos sin formato especial")
    
    print("\n" + "=" * 80)
    print("🏁 ANÁLISIS COMPLETADO")

if __name__ == "__main__":
    analyze_verse_segmentation() 