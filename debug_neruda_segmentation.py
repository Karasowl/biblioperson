#!/usr/bin/env python3
"""
Debug específico para PDF de Neruda - Analizar por qué está detectando solo 12 segmentos
en lugar de los ~20+ poemas esperados.
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

def analyze_neruda_segmentation():
    """Analiza por qué el PDF de Neruda detecta menos segmentos de los esperados"""
    
    pdf_path = r"C:\Users\adven\Downloads\Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        print("📝 Nota: Ajusta la ruta del archivo según tu sistema")
        return
    
    print("🔍 ANÁLISIS DETALLADO DE SEGMENTACIÓN - NERUDA")
    print(f"📄 Archivo: {pdf_path}")
    print("📊 Expectativa: ~20+ poemas | Detectado: 12 segmentos")
    print("=" * 80)
    
    # PASO 1: Cargar documento con PDFLoader V7.2
    print("📋 PASO 1: ANÁLISIS DEL PDFLOADER V7.2")
    print("-" * 50)
    
    try:
        loader = PDFLoader(pdf_path)
        result = loader.load()
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        
        print(f"✅ PDFLoader completado")
        print(f"📦 Bloques generados: {len(blocks)}")
        print(f"📄 Páginas del PDF: {metadata.get('page_count', 'N/A')}")
        print(f"📊 Ratio bloques/páginas: {len(blocks) / metadata.get('page_count', 1):.2f}")
        print()
        
        # Analizar calidad del texto
        total_text = ""
        readable_blocks = 0
        
        for i, block in enumerate(blocks):
            text = block.get('text', '')
            total_text += text
            
            # Verificar si el bloque tiene texto legible
            import re
            readable_chars = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', text))
            if readable_chars > len(text) * 0.5:  # 50% legible
                readable_blocks += 1
            
            # Mostrar primeros bloques para diagnóstico
            if i < 5:
                print(f"  📄 Bloque {i+1}:")
                print(f"    📏 Longitud: {len(text)} caracteres")
                print(f"    📊 Legibilidad: {readable_chars}/{len(text)} ({readable_chars/len(text)*100:.1f}%)")
                print(f"    📝 Preview: {repr(text[:100])}...")
                print()
        
        print(f"📊 CALIDAD GENERAL:")
        print(f"  📝 Texto total: {len(total_text)} caracteres")
        print(f"  ✅ Bloques legibles: {readable_blocks}/{len(blocks)} ({readable_blocks/len(blocks)*100:.1f}%)")
        
        # Calcular ratio de corrupción general
        import re
        total_readable = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡()"\'-]', total_text))
        corruption_ratio = 1.0 - (total_readable / len(total_text)) if total_text else 1.0
        print(f"  🔍 Corrupción detectada: {corruption_ratio*100:.1f}%")
        print()
        
    except Exception as e:
        print(f"❌ Error en PDFLoader: {e}")
        return
    
    # PASO 2: Análisis detallado del VerseSegmenter
    print("📋 PASO 2: ANÁLISIS DETALLADO DEL VERSESEGMENTER")
    print("-" * 50)
    
    try:
        segmenter = VerseSegmenter()
        
        # Habilitar logging detallado
        import logging
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        
        print("🔄 Ejecutando segmentación con logging detallado...")
        segments = segmenter.segment(blocks)
        
        print(f"\n✅ Segmentación completada")
        print(f"🎭 Segmentos detectados: {len(segments)}")
        print(f"📊 Ratio segmentos/páginas: {len(segments) / metadata.get('page_count', 1):.2f}")
        print()
        
        # Analizar cada segmento
        print("🔍 ANÁLISIS DETALLADO DE SEGMENTOS:")
        for i, segment in enumerate(segments):
            title = segment.get('title', 'Sin título')
            text = segment.get('text', '')
            method = segment.get('detection_method', 'principal')
            
            print(f"  🎭 Segmento {i+1}:")
            print(f"    🎯 Título: '{title}'")
            print(f"    📏 Longitud: {len(text)} caracteres")
            print(f"    📊 Versos: {segment.get('verse_count', 0)}")
            print(f"    🔧 Método: {method}")
            print(f"    📝 Preview: {repr(text[:150])}...")
            
            # Contar posibles títulos internos en segmentos largos
            if len(text) > 1000:  # Segmento potencialmente largo
                lines = text.split('\n')
                potential_internal_titles = []
                
                for line in lines:
                    line = line.strip()
                    if line and len(line) < 100:
                        # Buscar patrones de títulos de poemas
                        if (line.isupper() and len(line) < 60) or \
                           (line.isdigit() and int(line) <= 50) or \
                           (len(line.split()) <= 6 and not line.endswith('.') and not line.endswith(',')) or \
                           (line.startswith('"') and line.endswith('"')):
                            potential_internal_titles.append(line)
                
                if potential_internal_titles:
                    print(f"    ⚠️ POSIBLES TÍTULOS INTERNOS: {len(potential_internal_titles)}")
                    for j, internal_title in enumerate(potential_internal_titles[:5]):
                        print(f"      📍 '{internal_title}'")
                    if len(potential_internal_titles) > 5:
                        print(f"      📍 ... y {len(potential_internal_titles)-5} más")
            
            print()
        
    except Exception as e:
        print(f"❌ Error en VerseSegmenter: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # PASO 3: Cálculo de expectativas vs realidad
    print("📋 PASO 3: ANÁLISIS DE EXPECTATIVAS VS REALIDAD")
    print("-" * 50)
    
    expected_poems = 20  # "20 Poemas de Amor"
    detected_segments = len(segments)
    pages = metadata.get('page_count', 1)
    
    print(f"📊 MÉTRICAS:")
    print(f"  📖 Poemas esperados: ~{expected_poems}")
    print(f"  🎭 Segmentos detectados: {detected_segments}")
    print(f"  📄 Páginas del PDF: {pages}")
    print(f"  📉 Déficit: {expected_poems - detected_segments} poemas no detectados")
    print()
    
    # Algoritmo para determinar si necesita OCR
    ratio_segments_per_page = detected_segments / pages
    expected_ratio = expected_poems / pages
    
    print(f"📊 RATIOS:")
    print(f"  📊 Segmentos/página detectado: {ratio_segments_per_page:.2f}")
    print(f"  📊 Segmentos/página esperado: {expected_ratio:.2f}")
    print()
    
    # Determinar si necesita OCR
    needs_ocr = False
    ocr_reasons = []
    
    if corruption_ratio > 0.2:  # Más del 20% corrupto
        needs_ocr = True
        ocr_reasons.append(f"Alta corrupción: {corruption_ratio*100:.1f}%")
    
    if ratio_segments_per_page < 0.5:  # Menos de 0.5 segmentos por página
        needs_ocr = True
        ocr_reasons.append(f"Muy pocos segmentos por página: {ratio_segments_per_page:.2f}")
    
    if detected_segments < expected_poems * 0.6:  # Menos del 60% de poemas esperados
        needs_ocr = True
        ocr_reasons.append(f"Poemas insuficientes: {detected_segments}/{expected_poems}")
    
    if readable_blocks < len(blocks) * 0.8:  # Menos del 80% de bloques legibles
        needs_ocr = True
        ocr_reasons.append(f"Bloques ilegibles: {readable_blocks}/{len(blocks)}")
    
    print("🎯 DIAGNÓSTICO FINAL:")
    if needs_ocr:
        print("❌ REQUIERE OCR - Razones:")
        for reason in ocr_reasons:
            print(f"  • {reason}")
        print()
        print("💡 RECOMENDACIÓN: Implementar OCR automático como fallback")
    else:
        print("✅ NO REQUIERE OCR - Calidad de extracción aceptable")
        print("💡 RECOMENDACIÓN: Mejorar algoritmo de segmentación de títulos")
    
    print("\n" + "=" * 80)
    print("🏁 ANÁLISIS COMPLETADO")

if __name__ == "__main__":
    analyze_neruda_segmentation() 