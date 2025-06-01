#!/usr/bin/env python3
"""
Prueba del nuevo MarkdownPDFLoader

Comparar resultados entre:
1. PDFLoader tradicional (PyMuPDF)
2. MarkdownPDFLoader (pymupdf4llm)
"""

import sys
from pathlib import Path

# Agregar la ruta del dataset al path
sys.path.append(str(Path(__file__).parent / "dataset"))

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.loaders.markdown_pdf_loader import MarkdownPDFLoader
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def test_markdown_loader():
    """Probar el nuevo MarkdownPDFLoader"""
    
    pdf_path = r"C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return
        
    print("🚀 PRUEBA: MARKDOWNPDFLOADER vs PDFLOADER TRADICIONAL")
    print("=" * 70)
    
    # 1. PRUEBA LOADER TRADICIONAL
    print("📋 MÉTODO TRADICIONAL: PDFLoader")
    print("-" * 40)
    
    try:
        traditional_loader = PDFLoader(pdf_path)
        traditional_result = traditional_loader.load()
        
        traditional_blocks = traditional_result.get('blocks', [])
        traditional_metadata = traditional_result.get('metadata', {})
        
        print(f"✅ Bloques extraídos: {len(traditional_blocks)}")
        print(f"📊 Caracteres: {traditional_metadata.get('char_count', 0)}")
        print(f"🔧 Método: {traditional_result.get('source_info', {}).get('extraction_method', 'unknown')}")
        
        # Muestra de texto
        if traditional_blocks:
            sample_text = traditional_blocks[0].get('text', '')[:100]
            print(f"📝 Muestra: '{sample_text}...'")
        
        # Segmentación tradicional
        segmenter = VerseSegmenter()
        traditional_segments = segmenter.segment(traditional_blocks)
        print(f"🎭 Segmentos detectados: {len(traditional_segments)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traditional_segments = []
    
    # 2. PRUEBA NUEVO MARKDOWN LOADER
    print(f"\n📋 MÉTODO NUEVO: MarkdownPDFLoader")
    print("-" * 40)
    
    try:
        markdown_loader = MarkdownPDFLoader(pdf_path)
        markdown_result = markdown_loader.load()
        
        markdown_blocks = markdown_result.get('blocks', [])
        markdown_metadata = markdown_result.get('metadata', {})
        
        print(f"✅ Bloques extraídos: {len(markdown_blocks)}")
        print(f"📊 Caracteres: {markdown_metadata.get('char_count', 0)}")
        print(f"🎭 Poemas detectados: {markdown_metadata.get('detected_poems', 0)}")
        print(f"🔧 Método: {markdown_result.get('source_info', {}).get('extraction_method', 'unknown')}")
        
        # Muestra de texto
        if markdown_blocks:
            sample_block = markdown_blocks[0]
            sample_text = sample_block.get('text', '')[:100]
            block_type = sample_block.get('metadata', {}).get('type', 'unknown')
            print(f"📝 Muestra [{block_type}]: '{sample_text}...'")
        
        # Mostrar estructura de bloques
        print(f"\n📚 ESTRUCTURA DE BLOQUES:")
        for i, block in enumerate(markdown_blocks[:10]):  # Primeros 10
            block_type = block.get('metadata', {}).get('type', 'unknown')
            text_preview = block.get('text', '')[:50].replace('\n', ' ')
            level = block.get('metadata', {}).get('level', 0)
            indent = "  " * level
            print(f"   {i+1:2d}. {indent}[{block_type}] {text_preview}...")
        
        if len(markdown_blocks) > 10:
            print(f"   ... y {len(markdown_blocks) - 10} bloques más")
        
        # Segmentación con VerseSegmenter
        markdown_segments = segmenter.segment(markdown_blocks)
        print(f"\n🎭 Segmentos VerseSegmenter: {len(markdown_segments)}")
        
        # Mostrar comparación de segmentos
        print(f"\n📋 PRIMEROS SEGMENTOS DETECTADOS:")
        for i, segment in enumerate(markdown_segments[:5], 1):
            content = segment.get('content', '').strip()
            first_line = content.split('\n')[0] if content else 'Vacío'
            print(f"   {i}. {first_line[:60]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        markdown_segments = []
    
    # 3. COMPARACIÓN FINAL
    print(f"\n📊 COMPARACIÓN FINAL")
    print("-" * 40)
    
    print(f"🎯 BLOQUES EXTRAÍDOS:")
    print(f"   Tradicional: {len(traditional_blocks) if 'traditional_blocks' in locals() else 0}")
    print(f"   Markdown:    {len(markdown_blocks) if 'markdown_blocks' in locals() else 0}")
    
    print(f"\n🎭 SEGMENTOS DETECTADOS:")
    print(f"   Tradicional: {len(traditional_segments)}")
    print(f"   Markdown:    {len(markdown_segments)}")
    
    if markdown_segments and traditional_segments:
        improvement = len(markdown_segments) / len(traditional_segments) * 100 - 100
        print(f"   Mejora:      {improvement:+.1f}%")
    
    # Calidad del texto
    if 'markdown_metadata' in locals() and 'traditional_metadata' in locals():
        print(f"\n📝 CALIDAD DEL TEXTO:")
        print(f"   Tradicional: {traditional_metadata.get('char_count', 0)} chars")
        print(f"   Markdown:    {markdown_metadata.get('char_count', 0)} chars")
    
    print(f"\n💡 RECOMENDACIÓN:")
    if len(markdown_segments) > len(traditional_segments):
        print(f"   ✅ MarkdownPDFLoader es SUPERIOR")
        print(f"   • Mejor extracción de estructura")
        print(f"   • Más segmentos detectados")
        print(f"   • Preserva jerarquía del documento")
    elif len(markdown_segments) == len(traditional_segments):
        print(f"   ⚖️  Resultados SIMILARES")
        print(f"   • Considerar usar MarkdownPDFLoader por estructura")
    else:
        print(f"   ⚠️  Método tradicional detectó más")
        print(f"   • Revisar configuración de MarkdownPDFLoader")

def test_with_verse_segmenter_original():
    """Probar también con VerseSegmenter usando markdown directo"""
    
    print(f"\n🔬 PRUEBA ADICIONAL: MARKDOWN DIRECTO → VERSE SEGMENTER")
    print("-" * 50)
    
    pdf_path = r"C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    try:
        # Obtener markdown limpio
        markdown_loader = MarkdownPDFLoader(pdf_path)
        result = markdown_loader.load()
        
        raw_markdown = result.get('raw_markdown', '')
        
        if raw_markdown:
            print(f"📄 Markdown extraído: {len(raw_markdown)} caracteres")
            
            # Contar poemas en markdown crudo
            lines = raw_markdown.split('\n')
            poem_lines = [line for line in lines if 'Poema' in line or line.startswith('##')]
            
            print(f"🎭 Líneas con 'Poema': {len(poem_lines)}")
            print(f"📋 Primeras líneas de poemas:")
            for i, line in enumerate(poem_lines[:8], 1):
                print(f"   {i}. {line.strip()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_markdown_loader()
    test_with_verse_segmenter_original() 