#!/usr/bin/env python3
"""
Test del VerseSegmenter mejorado con el PDF real de Benedetti
Para verificar si detectamos ~140 poemas como identificó el usuario
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def test_benedetti_improved():
    print("🎯 TEST: VerseSegmenter MEJORADO con PDF de Benedetti")
    
    # Ruta del archivo PDF
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n1️⃣ PASO 1: Pipeline completo de procesamiento")
    
    # 1. Cargar PDF
    print(f"   📄 Cargando PDF...")
    loader = PDFLoader(str(archivo_pdf))
    raw_blocks = loader.load()
    print(f"   ✅ Bloques cargados: {len(raw_blocks)}")
    
    # 2. Pre-procesar (limpiar Unicode corrupto)
    print(f"   🧹 Pre-procesando...")
    preprocessor = CommonBlockPreprocessor({'clean_unicode_corruption': True})
    processed_blocks, metadata = preprocessor.process(raw_blocks, {})
    print(f"   ✅ Bloques después de limpieza: {len(processed_blocks)}")
    
    # 3. Segmentar con VerseSegmenter MEJORADO
    print(f"   🎭 Segmentando poemas...")
    segmenter = VerseSegmenter({})
    segments = segmenter.segment(processed_blocks)
    
    print(f"\n2️⃣ PASO 2: Resultados de segmentación")
    print(f"   🎯 POEMAS DETECTADOS: {len(segments)}")
    print(f"   🎯 OBJETIVO USUARIO: 140 poemas")
    
    if len(segments) >= 120:
        print(f"   ✅ EXCELENTE: Cobertura muy buena ({len(segments)}/140 = {len(segments)/140*100:.1f}%)")
    elif len(segments) >= 100:
        print(f"   ✅ BUENA: Cobertura aceptable ({len(segments)}/140 = {len(segments)/140*100:.1f}%)")
    elif len(segments) >= 80:
        print(f"   ⚠️  MEJORABLE: Progreso pero insuficiente ({len(segments)}/140 = {len(segments)/140*100:.1f}%)")
    else:
        print(f"   ❌ INSUFICIENTE: Necesitamos más mejoras ({len(segments)}/140 = {len(segments)/140*100:.1f}%)")
    
    print(f"\n3️⃣ PASO 3: Análisis de primeros poemas detectados")
    
    # Mostrar primeros 20 poemas detectados
    print(f"   📝 PRIMEROS 20 POEMAS DETECTADOS:")
    for i, segment in enumerate(segments[:20]):
        title = segment.get('title', 'Sin título')[:50]
        verse_count = segment.get('verse_count', 0)
        source_blocks = segment.get('source_blocks', 0)
        
        print(f"      [{i+1:2d}] '{title}' ({verse_count} versos, {source_blocks} bloques)")
    
    print(f"\n4️⃣ PASO 4: Comparación con versión anterior")
    
    # Para comparar, vamos a contar qué tipos de patrones detectamos
    pattern_counts = analyze_detection_patterns(segments)
    
    print(f"   📊 PATRONES DETECTADOS:")
    for pattern, count in pattern_counts.items():
        print(f"      • {pattern}: {count} poemas")
    
    return {
        'total_poems': len(segments),
        'target_poems': 140,
        'coverage': len(segments) / 140 * 100,
        'pattern_counts': pattern_counts,
        'first_poems': segments[:10]  # Primeros 10 para análisis
    }

def analyze_detection_patterns(segments):
    """Analiza qué tipos de patrones fueron detectados"""
    patterns = {
        'Títulos entre comillas': 0,
        'Títulos sin comillas': 0,
        'Números romanos': 0,
        'Listas numeradas': 0,
        'Separadores visuales': 0,
        'Otros patrones': 0
    }
    
    for segment in segments:
        title = segment.get('title', '')
        
        if title.startswith('"') and title.endswith('"'):
            patterns['Títulos entre comillas'] += 1
        elif title.upper() in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
                              'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX',
                              'XXI', 'XXII', 'XXIII', 'XXIV', 'XXV', 'XXVI', 'XXVII', 'XXVIII', 'XXIX', 'XXX']:
            patterns['Números romanos'] += 1
        elif title.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
            patterns['Listas numeradas'] += 1
        elif title in ['***', '---', '___', '...']:
            patterns['Separadores visuales'] += 1
        elif len(title) <= 50 and title[0].isupper():
            patterns['Títulos sin comillas'] += 1
        else:
            patterns['Otros patrones'] += 1
    
    return patterns

if __name__ == "__main__":
    resultado = test_benedetti_improved()
    
    if resultado:
        print(f"\n✅ TEST COMPLETADO")
        print(f"   🎯 Resultado: {resultado['total_poems']} poemas detectados")
        print(f"   📈 Cobertura: {resultado['coverage']:.1f}%")
        
        if resultado['coverage'] >= 85:
            print(f"   🎉 ¡OBJETIVO ALCANZADO! Excelente mejora")
        elif resultado['coverage'] >= 70:
            print(f"   👍 PROGRESO SIGNIFICATIVO - Casi llegamos")
        else:
            print(f"   🔧 NECESITAMOS MÁS AJUSTES") 