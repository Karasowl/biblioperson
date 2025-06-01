#!/usr/bin/env python3
"""
Debug del procesamiento PDF de Benedetti
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

def test_pdf_benedetti():
    print("🔍 DEBUG: PDF Benedetti - análisis de estructura")
    
    # Ruta del archivo PDF del usuario
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n📁 Archivo: {archivo_pdf.name}")
    
    # PASO 1: PDFLoader - ver qué bloques genera
    print(f"\n1️⃣ PASO 1: PDFLoader")
    loader = PDFLoader(archivo_pdf, tipo='poemas')
    resultado_loader = loader.load()
    
    bloques_originales = resultado_loader.get('blocks', [])
    metadata = resultado_loader.get('document_metadata', {})
    
    print(f"   ✅ Bloques cargados: {len(bloques_originales)}")
    print(f"   ✅ Documento: {metadata.get('titulo_documento', 'N/A')}")
    
    # Analizar primeros 50 bloques para ver la estructura
    print(f"\n📝 ANÁLISIS DE PRIMEROS 50 BLOQUES:")
    for i, bloque in enumerate(bloques_originales[:50], 1):
        texto = bloque.get('text', '').strip()
        is_heading = bloque.get('is_heading', False)
        is_bold = bloque.get('is_bold', False)
        is_centered = bloque.get('is_centered', False)
        
        # Solo mostrar bloques con contenido interesante
        if texto and len(texto) < 100:  # Títulos probables
            print(f"   [{i:2d}] {'🎭' if is_heading else '📄'} '{texto[:80]}'")
            print(f"        heading={is_heading}, bold={is_bold}, centered={is_centered}")
            
            # Detectar posibles títulos de poemas por patrones
            if (texto.isupper() and len(texto) < 50) or \
               (is_bold and len(texto) < 80) or \
               (is_centered and len(texto) < 80):
                print(f"        🚨 POSIBLE TÍTULO DE POEMA")
    
    # PASO 2: CommonBlockPreprocessor
    print(f"\n2️⃣ PASO 2: CommonBlockPreprocessor")
    preprocessor_config = {
        'filter_insignificant_blocks': False,
        'min_block_chars_to_keep': 1,
        'aggressive_merge_for_pdfs': False,
        'merge_cross_page_sentences': False
    }
    
    preprocessor = CommonBlockPreprocessor(preprocessor_config)
    bloques_procesados, metadata_procesada = preprocessor.process(bloques_originales, metadata)
    
    print(f"   ✅ Bloques después del preprocessor: {len(bloques_procesados)}")
    
    # PASO 3: VerseSegmenter
    print(f"\n3️⃣ PASO 3: VerseSegmenter")
    segmenter_config = {
        'thresholds': {
            'min_consecutive_verses': 2,
            'min_empty_between_stanzas': 1,
            'confidence_threshold': 0.3
        }
    }
    
    segmenter = VerseSegmenter(segmenter_config)
    segmentos = segmenter.segment(bloques_procesados)
    
    print(f"   ✅ Segmentos generados: {len(segmentos)}")
    
    if len(segmentos) == 0:
        print(f"\n❌ PROBLEMA: No se detectaron poemas en PDF")
        print(f"   🔍 Analizando por qué no se detectan títulos principales...")
        
        # Buscar manualmente títulos potenciales
        titulos_potenciales = []
        for bloque in bloques_procesados[:100]:  # Primeros 100 bloques
            texto = bloque.get('text', '').strip()
            if texto and len(texto) < 80:
                if (texto.isupper() and len(texto) < 50) or \
                   (bloque.get('is_bold', False)) or \
                   (bloque.get('is_centered', False)):
                    titulos_potenciales.append(texto)
        
        print(f"   📝 Títulos potenciales encontrados: {len(titulos_potenciales)}")
        for i, titulo in enumerate(titulos_potenciales[:10], 1):
            print(f"      {i}. {titulo}")
    
    else:
        print(f"\n✅ ÉXITO: Se detectaron {len(segmentos)} poemas")
        for i, segmento in enumerate(segmentos, 1):
            titulo = segmento.get('title', 'Sin título')
            texto = segmento.get('text', '')
            print(f"   [{i}] '{titulo}' ({len(texto)} caracteres)")

if __name__ == "__main__":
    test_pdf_benedetti() 