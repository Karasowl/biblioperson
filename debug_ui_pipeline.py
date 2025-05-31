#!/usr/bin/env python3
"""
Script de diagnóstico completo para simular exactamente el pipeline de la UI
y identificar dónde se pierde la funcionalidad anti-salto de página.
"""

import sys
import os
import importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def reload_all_modules():
    """Fuerza la recarga de todos los módulos relevantes"""
    print("🔄 FORZANDO RECARGA DE TODOS LOS MÓDULOS...")
    
    # Recargar PDFLoader
    import dataset.processing.loaders.pdf_loader
    importlib.reload(dataset.processing.loaders.pdf_loader)
    print("✅ PDFLoader recargado")
    
    # Recargar CommonBlockPreprocessor
    import dataset.processing.pre_processors.common_block_preprocessor
    importlib.reload(dataset.processing.pre_processors.common_block_preprocessor)
    print("✅ CommonBlockPreprocessor recargado")
    
    # Recargar HeadingSegmenter
    import dataset.processing.segmenters.heading_segmenter
    importlib.reload(dataset.processing.segmenters.heading_segmenter)
    print("✅ HeadingSegmenter recargado")
    
    # Recargar ProfileManager
    import dataset.processing.profile_manager
    importlib.reload(dataset.processing.profile_manager)
    print("✅ ProfileManager recargado")

def test_pdloader_directly():
    """Prueba el PDFLoader directamente"""
    print("\n" + "="*60)
    print("🧪 PASO 1: PROBANDO PDFLoader DIRECTAMENTE")
    print("="*60)
    
    from dataset.processing.loaders.pdf_loader import PDFLoader
    
    pdf_path = r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ Archivo no encontrado")
        return None
        
    print(f"📄 Cargando: {os.path.basename(pdf_path)}")
    
    loader = PDFLoader(pdf_path)
    raw_data = loader.load()
    
    # Buscar bloques que contengan "atractivo"
    atractivo_blocks = []
    for i, block in enumerate(raw_data.get('blocks', [])):
        if 'atractivo' in block.get('text', '').lower():
            atractivo_blocks.append((i, block))
            print(f"\n🎯 BLOQUE {i} CON 'ATRACTIVO':")
            print(f"   Texto: '{block['text']}'")
            print(f"   Orden: {block.get('orden', 'N/A')}")
            
    return raw_data, atractivo_blocks

def test_preprocessor(raw_data):
    """Prueba el CommonBlockPreprocessor"""
    print("\n" + "="*60)
    print("🧪 PASO 2: PROBANDO CommonBlockPreprocessor")
    print("="*60)
    
    from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
    
    config = {
        'filter_insignificant_blocks': True,
        'aggressive_filtering': True,
        'clean_text': True
    }
    
    preprocessor = CommonBlockPreprocessor(config)
    document_metadata = {
        'titulo_documento': '¿Qué es el populismo_ - Jan-Werner Müller',
        'file_format': 'pdf'
    }
    
    print(f"📊 Bloques de entrada: {len(raw_data['blocks'])}")
    processed_blocks = preprocessor.process(raw_data['blocks'], document_metadata)
    print(f"📊 Bloques procesados: {len(processed_blocks)}")
    
    # Buscar bloques con "atractivo" después del preprocesamiento
    atractivo_processed = []
    for i, block in enumerate(processed_blocks):
        if isinstance(block, dict) and 'atractivo' in block.get('text', '').lower():
            atractivo_processed.append((i, block))
            print(f"\n🎯 BLOQUE PROCESADO {i} CON 'ATRACTIVO':")
            print(f"   Texto: '{block['text']}'")
            print(f"   Orden: {block.get('order_in_document', 'N/A')}")
            
    return processed_blocks, atractivo_processed

def test_segmenter(processed_blocks):
    """Prueba el HeadingSegmenter"""
    print("\n" + "="*60)
    print("🧪 PASO 3: PROBANDO HeadingSegmenter")
    print("="*60)
    
    from dataset.processing.segmenters.heading_segmenter import HeadingSegmenter
    
    # Configuración del perfil "prosa"
    profile_config = {
        'preserve_individual_paragraphs': True,
        'disable_section_grouping': True,
        'min_paragraph_length': 5,
        'language': 'es'
    }
    
    segmenter = HeadingSegmenter(profile_config)
    
    document_metadata = {
        'titulo_documento': '¿Qué es el populismo_ - Jan-Werner Müller',
        'file_format': 'pdf',
        'idioma_documento': 'es'
    }
    
    print(f"📊 Bloques para segmentar: {len(processed_blocks)}")
    segments = segmenter.segment(processed_blocks, document_metadata)
    print(f"📊 Segmentos generados: {len(segments)}")
    
    # Buscar segmentos con "atractivo" - revisar qué claves tiene cada segmento
    atractivo_segments = []
    
    print(f"🔍 DEBUG: Primeros 3 segmentos para analizar estructura:")
    for i, segment in enumerate(segments[:3]):
        print(f"   Segmento {i}: {list(segment.keys()) if isinstance(segment, dict) else type(segment)}")
        if isinstance(segment, dict):
            text_field = segment.get('text', segment.get('texto_segmento', ''))
            print(f"   Texto: '{text_field[:100]}...'")
    
    # Buscar segmentos que contengan "atractivo"
    for i, segment in enumerate(segments):
        if isinstance(segment, dict):
            # Probar diferentes campos de texto posibles
            text_field = segment.get('text', segment.get('texto_segmento', ''))
            if text_field and 'atractivo' in text_field.lower():
                atractivo_segments.append((i, segment))
                print(f"\n🎯 SEGMENTO {i} CON 'ATRACTIVO':")
                print(f"   Texto: '{text_field}'")
                print(f"   Campos disponibles: {list(segment.keys())}")
            
    return segments, atractivo_segments

def test_complete_pipeline():
    """Ejecuta el pipeline completo y analiza los resultados"""
    print("\n🚀 INICIANDO DIAGNÓSTICO COMPLETO DEL PIPELINE")
    print("="*80)
    
    # Paso 1: Recarga de módulos
    reload_all_modules()
    
    # Paso 2: Prueba PDFLoader
    raw_data, atractivo_raw = test_pdloader_directly()
    if not raw_data:
        return
    
    # Paso 3: Prueba Preprocessor
    processed_blocks, atractivo_processed = test_preprocessor(raw_data)
    
    # Paso 4: Prueba Segmenter
    segments, atractivo_segments = test_segmenter(processed_blocks)
    
    # Análisis final
    print("\n" + "="*60)
    print("📋 ANÁLISIS FINAL")
    print("="*60)
    
    print(f"🔍 Bloques con 'atractivo' en PDFLoader: {len(atractivo_raw)}")
    print(f"🔍 Bloques con 'atractivo' después de Preprocessor: {len(atractivo_processed)}")
    print(f"🔍 Segmentos con 'atractivo' después de Segmenter: {len(atractivo_segments)}")
    
    if atractivo_segments:
        print("\n🎯 RESULTADO FINAL:")
        for i, (idx, segment) in enumerate(atractivo_segments):
            text = segment['texto_segmento']
            print(f"   Segmento {idx}: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
            # Verificar si el problema persiste
            if text.endswith('atractivo') and not 'de esta idea' in text:
                print("   ❌ PROBLEMA PERSISTE: Texto cortado en 'atractivo'")
            elif 'atractivo de esta idea' in text:
                print("   ✅ PROBLEMA RESUELTO: Texto completo encontrado")
            else:
                print("   ⚠️ RESULTADO INESPERADO")

if __name__ == "__main__":
    test_complete_pipeline() 