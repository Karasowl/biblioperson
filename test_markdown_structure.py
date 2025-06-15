#!/usr/bin/env python3
"""
Script para probar la conversión PDF → Markdown y analizar la estructura visual
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.loaders.markdown_pdf_loader import MarkdownPDFLoader
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_markdown_structure():
    """Probar la conversión a Markdown y analizar estructura"""
    
    # Archivo de prueba
    test_file = r"C:\Users\adven\Downloads\Obras literarias-20250531T221115Z-1-001\Obras literarias\Último_planeta_en_pie.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🔄 Probando conversión Markdown: {test_file}")
    
    # Cargar con MarkdownPDFLoader
    loader = MarkdownPDFLoader(test_file)
    result = loader.load()
    
    if not result or 'raw_markdown' not in result:
        print("❌ Error: No se pudo generar Markdown")
        return
    
    raw_markdown = result['raw_markdown']
    blocks = result.get('blocks', [])
    
    print(f"\n📊 Estadísticas:")
    print(f"   - Caracteres en Markdown: {len(raw_markdown)}")
    print(f"   - Bloques generados: {len(blocks)}")
    
    # Guardar Markdown completo para análisis
    markdown_file = r"C:\Users\adven\Downloads\test_markdown_output.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(raw_markdown)
    print(f"📄 Markdown guardado en: {markdown_file}")
    
    # Analizar estructura de párrafos en las primeras líneas
    print(f"\n🔍 Análisis de estructura (primeras 50 líneas):")
    lines = raw_markdown.split('\n')
    
    for i, line in enumerate(lines[:50]):
        # Analizar indentación y estructura
        if line.strip():  # Solo líneas no vacías
            leading_spaces = len(line) - len(line.lstrip())
            line_preview = line[:80] + "..." if len(line) > 80 else line
            
            # Marcar líneas con indentación
            indent_marker = f"[{leading_spaces}sp]" if leading_spaces > 0 else "[0sp]"
            print(f"   {i+1:2d}: {indent_marker} {line_preview}")
        else:
            print(f"   {i+1:2d}: [VACÍA]")
    
    # Buscar el texto problemático específico
    print(f"\n🎯 Buscando texto problemático:")
    target_text = "Mi profesor de Periodismo Investigativo"
    
    if target_text in raw_markdown:
        # Encontrar la posición y mostrar contexto
        pos = raw_markdown.find(target_text)
        context_start = max(0, pos - 200)
        context_end = min(len(raw_markdown), pos + 500)
        context = raw_markdown[context_start:context_end]
        
        print(f"✅ Texto encontrado en posición {pos}")
        print(f"📄 Contexto:")
        print("=" * 60)
        print(context)
        print("=" * 60)
        
        # Analizar líneas alrededor del texto problemático
        lines_around = context.split('\n')
        print(f"\n🔍 Análisis línea por línea del contexto:")
        for i, line in enumerate(lines_around):
            if line.strip():
                leading_spaces = len(line) - len(line.lstrip())
                indent_marker = f"[{leading_spaces}sp]"
                print(f"   {i+1:2d}: {indent_marker} {line}")
            else:
                print(f"   {i+1:2d}: [VACÍA]")
    else:
        print(f"❌ Texto problemático no encontrado en Markdown")
    
    # Analizar bloques generados
    print(f"\n📦 Primeros 5 bloques generados:")
    for i, block in enumerate(blocks[:5]):
        text_preview = block.get('text', '')[:100] + "..." if len(block.get('text', '')) > 100 else block.get('text', '')
        print(f"   Bloque {i+1}: tipo='{block.get('type', 'unknown')}', chars={len(block.get('text', ''))}")
        print(f"              texto: {text_preview}")

if __name__ == "__main__":
    test_markdown_structure() 