#!/usr/bin/env python3
"""
Debug para analizar por qué el VerseSegmenter no encuentra segmentos 
en la antología poética de Mario Benedetti.
"""

import sys
import os
import logging
from pathlib import Path

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def debug_benedetti_antologia():
    """Analiza paso a paso el procesamiento de la antología de Benedetti."""
    
    # Ruta del PDF (ajustar según sea necesario)
    pdf_path = r"C:\Users\adven\Downloads\Mario Benedetti Antologia Poética.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        print("Por favor, ajusta la ruta del PDF en el script")
        return
    
    print("🚨 INICIANDO DEBUG DE VERSO SEGMENTER 🚨")
    print(f"📄 Archivo: {pdf_path}")
    print("=" * 60)
    
    # PASO 1: Cargar PDF
    print("\n📦 PASO 1: CARGANDO PDF...")
    loader = PDFLoader(pdf_path)
    try:
        raw_data = loader.load()
        print(f"✅ PDF cargado exitosamente")
        print(f"📊 Datos: {type(raw_data)}")
        print(f"📋 Estructura: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'No es dict'}")
        
        # Examinar estructura detallada
        if isinstance(raw_data, dict):
            for key, value in raw_data.items():
                if isinstance(value, list):
                    print(f"  🔑 {key}: lista con {len(value)} elementos")
                    if value and len(value) > 0:
                        print(f"    📄 Primer elemento: {type(value[0])}")
                        if isinstance(value[0], dict):
                            print(f"    🗝️ Claves: {list(value[0].keys())}")
                else:
                    print(f"  🔑 {key}: {type(value)}")
        print()
    except Exception as e:
        print(f"❌ Error cargando PDF: {e}")
        return
    
    # PASO 2: Preprocesar
    print("⚙️ PASO 2: PREPROCESANDO BLOQUES...")
    preprocessor_config = {
        'filter_insignificant_blocks': False,
        'min_block_chars_to_keep': 1,
        'aggressive_merge_for_pdfs': False,
        'merge_cross_page_sentences': False,
        'split_blocks_into_paragraphs': False,
        'discard_common_pdf_artifacts': False
    }
    
    preprocessor = CommonBlockPreprocessor(preprocessor_config)
    try:
        # Extraer solo los bloques del resultado del PDFLoader
        input_blocks = raw_data.get('blocks', [])
        print(f"📦 Bloques de entrada: {len(input_blocks)}")
        
        # Mostrar contenido de los bloques de entrada
        print("🔍 BLOQUES DE ENTRADA DEL PDF:")
        for i, block in enumerate(input_blocks):
            text = block.get('text', '').strip()
            print(f"  📄 Bloque {i+1}: '{text}'")
            print(f"    📏 Longitud: {len(text)} caracteres")
            print()
        
        # Crear metadatos de documento
        document_metadata = {
            'file_path': pdf_path,
            'content_type': 'poetry'
        }
        result = preprocessor.process(input_blocks, document_metadata)
        print(f"✅ Preprocesamiento exitoso")
        print(f"📦 Resultado: {type(result)}")
        
        # El preprocessor puede devolver una tupla (blocks, metadata)
        if isinstance(result, tuple):
            blocks, metadata = result
            print(f"📦 Bloques extraídos de tupla: {len(blocks)}")
        else:
            blocks = result
            print(f"📦 Bloques directos: {len(blocks)}")
        print()
        
        # Mostrar información detallada de los primeros bloques
        print("🔍 ANÁLISIS DETALLADO DE BLOQUES:")
        if isinstance(blocks, list):
            for i, block in enumerate(blocks[:10]):  # Mostrar primeros 10 bloques
                if isinstance(block, dict):
                    text = block.get('text', '').strip()
                    print(f"  📄 Bloque {i+1}:")
                    print(f"    📝 Texto: '{text[:100]}{'...' if len(text) > 100 else ''}'")
                    print(f"    📏 Longitud: {len(text)} caracteres")
                    print(f"    🎭 Es título (heading): {block.get('is_heading', False)}")
                    print(f"    🔥 Es negrita: {block.get('is_bold', False)}")
                    print(f"    📐 Es centrado: {block.get('is_centered', False)}")
                    print(f"    📊 Metadatos: {dict(block)}")
                    print()
                else:
                    print(f"  📄 Bloque {i+1}: {type(block)} - {block}")
                    print()
                
            if len(blocks) > 10:
                print(f"    ... y {len(blocks) - 10} bloques más")
                print()
        else:
            print(f"❌ Blocks no es una lista: {type(blocks)}")
            print()
    
    except Exception as e:
        print(f"❌ Error en preprocesamiento: {e}")
        return
    
    # PASO 3: Analizar títulos potenciales
    print("🎭 PASO 3: ANÁLISIS DE TÍTULOS POTENCIALES...")
    segmenter = VerseSegmenter()
    
    title_candidates = []
    for i, block in enumerate(blocks):
        if segmenter._is_title_block(block):
            title_candidates.append((i, block))
    
    print(f"🎯 Títulos candidatos encontrados: {len(title_candidates)}")
    for i, (block_idx, block) in enumerate(title_candidates):
        text = block.get('text', '').strip()
        print(f"  🎭 Candidato {i+1} (bloque {block_idx+1}): '{text}'")
        
        # Analizar si es título principal
        is_main = segmenter._is_main_title(block, block_idx, blocks)
        print(f"    ✅ Es título principal: {is_main}")
        
        if not is_main:
            # Analizar por qué no es título principal
            print("    🔍 Análisis detallado:")
            
            # Verificar qué sigue después
            verse_count = 0
            for j in range(block_idx + 1, min(block_idx + 15, len(blocks))):
                next_block = blocks[j]
                next_text = next_block.get('text', '').strip()
                if next_text and len(next_text) <= 120:
                    verse_count += 1
                else:
                    break
            
            print(f"      📝 Versos detectados después: {verse_count}")
            print(f"      ❌ Razón: Necesita mínimo 3 versos, encontrados {verse_count}")
        print()
    
    # PASO 4: Segmentación
    print("✂️ PASO 4: SEGMENTACIÓN VERSO...")
    try:
        segments = segmenter.segment(blocks)
        print(f"✅ Segmentación completada")
        print(f"🎭 Segmentos encontrados: {len(segments)}")
        
        if segments:
            print("\n📚 SEGMENTOS DETECTADOS:")
            for i, segment in enumerate(segments):
                title = segment.get('title', 'Sin título')
                verse_count = segment.get('verse_count', 0)
                text_preview = segment.get('text', '')[:200]
                print(f"  🎭 Segmento {i+1}:")
                print(f"    📖 Título: '{title}'")
                print(f"    📝 Versos: {verse_count}")
                print(f"    📄 Vista previa: '{text_preview}...'")
                print()
        else:
            print("❌ NO SE ENCONTRARON SEGMENTOS")
            print("\n🔧 POSIBLES SOLUCIONES:")
            print("1. Implementar algoritmo de fallback más flexible")
            print("2. Ajustar umbrales de detección de versos")
            print("3. Mejorar limpieza de corrupción del PDF")
            print("4. Revisar patrones de detección de títulos")
            
    except Exception as e:
        print(f"❌ Error en segmentación: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 DEBUG COMPLETADO")

if __name__ == "__main__":
    debug_benedetti_antologia() 