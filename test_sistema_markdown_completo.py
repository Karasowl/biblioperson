#!/usr/bin/env python3
"""
Prueba del Sistema Completo: MarkdownPDFLoader + MarkdownVerseSegmenter

Sistema optimizado para procesamiento de PDFs de poesía:
1. MarkdownPDFLoader: Extracción limpia con pymupdf4llm
2. MarkdownVerseSegmenter: Segmentación específica para markdown
"""

import sys
from pathlib import Path

# Agregar la ruta del dataset al path
sys.path.append(str(Path(__file__).parent / "dataset"))

from dataset.processing.loaders.markdown_pdf_loader import MarkdownPDFLoader
from dataset.processing.segmenters.markdown_verse_segmenter import MarkdownVerseSegmenter

def test_sistema_completo():
    """Probar el sistema completo optimizado para markdown"""
    
    pdf_path = r"C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return
        
    print("🚀 SISTEMA COMPLETO: MARKDOWNPDFLOADER + MARKDOWNVERSESEGMENTER")
    print("=" * 80)
    
    # PASO 1: EXTRACCIÓN CON MARKDOWNPDFLOADER
    print("📋 PASO 1: EXTRACCIÓN PDF → MARKDOWN ESTRUCTURADO")
    print("-" * 50)
    
    try:
        loader = MarkdownPDFLoader(pdf_path)
        result = loader.load()
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        source_info = result.get('source_info', {})
        
        print(f"✅ Extracción exitosa:")
        print(f"   📦 Bloques extraídos: {len(blocks)}")
        print(f"   📊 Caracteres: {metadata.get('char_count', 0)}")
        print(f"   🎭 Poemas detectados en metadata: {metadata.get('detected_poems', 0)}")
        print(f"   🔧 Método: {source_info.get('extraction_method', 'unknown')}")
        
        # Mostrar estructura de bloques
        print(f"\n📚 ESTRUCTURA DE BLOQUES (primeros 10):")
        poem_titles = 0
        content_blocks = 0
        
        for i, block in enumerate(blocks[:10]):
            block_type = block.get('metadata', {}).get('type', 'unknown')
            text_preview = block.get('text', '')[:50].replace('\n', ' ')
            level = block.get('metadata', {}).get('level', 0)
            indent = "  " * level
            
            print(f"   {i+1:2d}. {indent}[{block_type:12}] {text_preview}...")
            
            if block_type == 'poem_title':
                poem_titles += 1
            elif block_type == 'content':
                content_blocks += 1
        
        if len(blocks) > 10:
            # Contar todos los tipos
            for block in blocks[10:]:
                block_type = block.get('metadata', {}).get('type', 'unknown')
                if block_type == 'poem_title':
                    poem_titles += 1
                elif block_type == 'content':
                    content_blocks += 1
            
            print(f"   ... y {len(blocks) - 10} bloques más")
        
        print(f"\n📊 RESUMEN DE BLOQUES:")
        print(f"   🎭 Títulos de poemas: {poem_titles}")
        print(f"   📝 Bloques de contenido: {content_blocks}")
        print(f"   📄 Otros: {len(blocks) - poem_titles - content_blocks}")
        
    except Exception as e:
        print(f"❌ Error en extracción: {e}")
        return
    
    # PASO 2: SEGMENTACIÓN CON MARKDOWNVERSESEGMENTER
    print(f"\n📋 PASO 2: SEGMENTACIÓN MARKDOWN → POEMAS")
    print("-" * 50)
    
    try:
        segmenter = MarkdownVerseSegmenter()
        segments = segmenter.segment(blocks)
        
        print(f"✅ Segmentación exitosa:")
        print(f"   🎭 Poemas detectados: {len(segments)}")
        
        # Mostrar estadísticas
        stats = segmenter.get_stats(segments)
        print(f"   📊 Total versos: {stats.get('total_verses', 0)}")
        print(f"   📊 Promedio versos/poema: {stats.get('avg_verses_per_poem', 0):.1f}")
        print(f"   📊 Total caracteres: {stats.get('total_chars', 0)}")
        
        # Mostrar primeros poemas
        print(f"\n📋 PRIMEROS POEMAS DETECTADOS:")
        for i, segment in enumerate(segments[:8], 1):
            title = segment.get('metadata', {}).get('title', 'Sin título')
            verse_lines = segment.get('metadata', {}).get('verse_lines', 0)
            char_count = segment.get('metadata', {}).get('char_count', 0)
            
            print(f"   {i:2d}. {title[:50]:<50} ({verse_lines:2d} versos, {char_count:3d} chars)")
        
        if len(segments) > 8:
            print(f"   ... y {len(segments) - 8} poemas más")
        
        # Mostrar contenido de un poema ejemplo
        if segments:
            print(f"\n📝 EJEMPLO - CONTENIDO DEL PRIMER POEMA:")
            first_poem = segments[0]
            content = first_poem.get('content', '')
            lines = content.split('\n')
            
            for i, line in enumerate(lines[:8], 1):
                print(f"   {i:2d}: {line}")
            
            if len(lines) > 8:
                print(f"   ... y {len(lines) - 8} líneas más")
        
    except Exception as e:
        print(f"❌ Error en segmentación: {e}")
        return
    
    # PASO 3: ANÁLISIS FINAL
    print(f"\n📊 ANÁLISIS FINAL DEL SISTEMA")
    print("-" * 50)
    
    expected_poems = 20  # "20 Poemas de Amor"
    detected_poems = len(segments)
    
    print(f"🎯 EFECTIVIDAD:")
    print(f"   📚 Poemas esperados: {expected_poems}")
    print(f"   🎭 Poemas detectados: {detected_poems}")
    print(f"   📊 Tasa de detección: {detected_poems/expected_poems*100:.1f}%")
    
    if detected_poems >= expected_poems * 0.9:  # 90%+
        print(f"   ✅ EXCELENTE: Sistema detecta ≥90% de poemas")
    elif detected_poems >= expected_poems * 0.75:  # 75%+
        print(f"   ✅ BUENO: Sistema detecta ≥75% de poemas")
    elif detected_poems >= expected_poems * 0.5:  # 50%+
        print(f"   ⚠️  ACEPTABLE: Sistema detecta ≥50% de poemas")
    else:
        print(f"   ❌ MEJORABLE: Sistema detecta <50% de poemas")
    
    print(f"\n🔍 CALIDAD DE EXTRACCIÓN:")
    if metadata.get('char_count', 0) > 20000:
        print(f"   ✅ Contenido completo extraído ({metadata.get('char_count', 0)} chars)")
    else:
        print(f"   ⚠️  Contenido parcial ({metadata.get('char_count', 0)} chars)")
    
    print(f"\n💡 RECOMENDACIONES:")
    if detected_poems < expected_poems:
        missing = expected_poems - detected_poems
        print(f"   🔧 Faltan {missing} poemas por detectar")
        print(f"   📝 Revisar patrones de títulos no detectados")
        print(f"   🎯 Analizar estructura de poemas sin título claro")
    else:
        print(f"   ✅ Sistema funcionando óptimamente")
        print(f"   🚀 Listo para producción")
    
    return {
        'blocks_extracted': len(blocks),
        'poems_detected': detected_poems,
        'detection_rate': detected_poems/expected_poems*100,
        'extraction_method': source_info.get('extraction_method', 'unknown'),
        'total_chars': metadata.get('char_count', 0)
    }

if __name__ == "__main__":
    result = test_sistema_completo()
    print(f"\n🎯 RESULTADO FINAL: {result}") 