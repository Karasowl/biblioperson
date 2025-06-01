#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del sistema completo SIN limpieza Unicode
Para ver el contenido real del PDF de Benedetti
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.ERROR)  # Solo errores para reducir ruido

def test_sistema_sin_limpieza():
    print("🔍 TEST: Sistema completo SIN limpieza Unicode")
    
    # Ruta del archivo PDF
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n📄 ARCHIVO: {archivo_pdf.name}")
    
    # PASO 1: CARGAR PDF
    print(f"\n1️⃣ PASO 1: Cargar PDF")
    try:
        loader = PDFLoader(str(archivo_pdf))
        raw_blocks = loader.load()
        print(f"   ✅ Bloques cargados: {len(raw_blocks)}")
        
        # Analizar primeros bloques SIN filtrar
        if raw_blocks:
            print(f"\n   📝 PRIMEROS 10 BLOQUES SIN FILTRAR:")
            for i, block in enumerate(raw_blocks[:10]):
                if isinstance(block, dict):
                    text = block.get('text', '').strip()
                    page = block.get('page', 'N/A')
                    print(f"      [{i}] Página {page}: '{text[:60]}...'")
                else:
                    print(f"      [{i}] Tipo: {type(block)}, Contenido: '{str(block)[:60]}...'")
        
    except Exception as e:
        print(f"   ❌ ERROR en PDFLoader: {e}")
        return
    
    # PASO 2: PREPROCESSAR SIN LIMPIEZA UNICODE
    print(f"\n2️⃣ PASO 2: Preprocessar SIN limpieza Unicode")
    try:
        # Configurar preprocessor SIN limpieza Unicode
        config_sin_limpieza = {
            'clean_unicode_corruption': False  # DESHABILITAR limpieza
        }
        
        preprocessor = CommonBlockPreprocessor(config_sin_limpieza)
        processed_blocks = preprocessor.process(raw_blocks, {})
        print(f"   ✅ Bloques procesados: {len(processed_blocks)}")
        
        # Analizar contenido real
        text_samples = []
        for block in processed_blocks[:50]:  # Primeros 50 bloques
            if isinstance(block, dict):
                text = block.get('text', '').strip()
                if text and len(text) > 10:  # Solo texto significativo
                    text_samples.append(text)
        
        print(f"\n   📝 MUESTRAS DE TEXTO REAL (primeros 10):")
        for i, text in enumerate(text_samples[:10]):
            print(f"      [{i+1}] '{text[:80]}...'")
        
        # Buscar títulos potenciales manualmente
        potential_titles = []
        for block in processed_blocks[:200]:  # Primeros 200 bloques
            if isinstance(block, dict):
                text = block.get('text', '').strip()
                if text:
                    # Patrones típicos de títulos
                    if (text.startswith('"') and text.endswith('"') and len(text) < 80) or \
                       (len(text) < 50 and text[0].isupper() and not text.endswith('.')) or \
                       text.isupper():
                        potential_titles.append(text)
        
        print(f"\n   📍 TÍTULOS POTENCIALES DETECTADOS ({len(potential_titles)}):")
        for i, title in enumerate(potential_titles[:15]):  # Primeros 15
            print(f"      [{i+1}] '{title}'")
        
    except Exception as e:
        print(f"   ❌ ERROR en Preprocessor: {e}")
        return
    
    # PASO 3: SEGMENTAR
    print(f"\n3️⃣ PASO 3: Segmentar con VerseSegmenter")
    try:
        segmenter = VerseSegmenter({})
        segments = segmenter.segment(processed_blocks)
        print(f"   ✅ Poemas detectados: {len(segments)}")
        
        if segments:
            print(f"\n   📝 POEMAS DETECTADOS:")
            for i, segment in enumerate(segments[:20]):  # Primeros 20
                title = segment.get('title', 'Sin título')
                text_lines = len(segment.get('text', '').split('\n'))
                print(f"      [{i+1}] '{title}' ({text_lines} líneas)")
        else:
            print(f"   ❌ NO se detectaron poemas")
        
    except Exception as e:
        print(f"   ❌ ERROR en VerseSegmenter: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # RESUMEN
    print(f"\n🏁 DIAGNÓSTICO FINAL:")
    print(f"   📦 Bloques originales: {len(raw_blocks)}")
    print(f"   🔧 Bloques procesados: {len(processed_blocks)}")
    print(f"   📍 Títulos potenciales: {len(potential_titles)}")
    print(f"   🎭 Poemas detectados: {len(segments)}")
    print(f"   🎯 Objetivo: ~140 poemas")
    
    if len(potential_titles) > 50:
        print(f"   ✅ CONTENIDO DETECTADO: El PDF tiene contenido válido")
        if len(segments) < 50:
            print(f"   🔧 PROBLEMA: VerseSegmenter no detecta suficientes poemas")
            print(f"   💡 SOLUCIÓN: Ajustar patrones de detección")
        else:
            print(f"   🎉 ÉXITO: Sistema funcionando correctamente")
    else:
        print(f"   ❌ PROBLEMA CRÍTICO: PDF corrupto o mal procesado")
        print(f"   🚨 REVISAR: PDFLoader o corrupción del archivo")

if __name__ == "__main__":
    test_sistema_sin_limpieza() 