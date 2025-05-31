#!/usr/bin/env python3
"""
Script de debug para analizar saltos de página vs párrafos en PDFLoader
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.loaders.pdf_loader import PDFLoader
import fitz
import re

def debug_page_breaks():
    """Analiza cómo se manejan los saltos de página en el PDF"""
    
    # Archivo de prueba
    pdf_path = r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ Archivo no encontrado:", pdf_path)
        return
        
    print("🔍 ANALIZANDO SALTOS DE PÁGINA EN PDF...")
    print(f"📄 Archivo: {os.path.basename(pdf_path)}")
    print("=" * 80)
    
    # Abrir PDF directamente con fitz para análisis detallado
    doc = fitz.open(pdf_path)
    
    print(f"📊 Total de páginas: {doc.page_count}")
    print()
    
    # Analizar las primeras 3 páginas en detalle
    for page_num in range(min(3, doc.page_count)):
        print(f"📄 === PÁGINA {page_num + 1} ===")
        page = doc.load_page(page_num)
        
        # Extraer con dict para ver estructura
        page_dict = page.get_text("dict", sort=True)
        blocks = page_dict.get('blocks', [])
        
        print(f"🧱 Bloques en página: {len(blocks)}")
        
        # Analizar cada bloque
        for block_idx, block in enumerate(blocks):
            if block.get('type') == 0:  # Bloque de texto
                lines = []
                for line_group in block.get('lines', []):
                    line_text = ""
                    for span in line_group.get('spans', []):
                        line_text += span.get('text', '')
                    if line_text.strip():
                        lines.append(line_text.strip())
                
                if lines:
                    print(f"🧱 Bloque {block_idx} - {len(lines)} líneas:")
                    for i, line in enumerate(lines):
                        # Mostrar solo primeras 60 chars de cada línea
                        preview = line[:60] + "..." if len(line) > 60 else line
                        print(f"  [{i}] {preview}")
                    
                    # Análisis de reconstrucción con PDFLoader
                    loader = PDFLoader(pdf_path)
                    reconstructed = loader._reconstruct_paragraphs(lines)
                    
                    print(f"🔧 Reconstruido ({len(reconstructed)} chars):")
                    # Mostrar párrafos separados
                    paragraphs = reconstructed.split('\n\n')
                    for p_idx, paragraph in enumerate(paragraphs):
                        preview = paragraph[:100] + "..." if len(paragraph) > 100 else paragraph
                        print(f"  PÁRRAFO {p_idx}: {preview}")
                    print()
        
        print("-" * 40)
    
    # Buscar casos específicos de corte de párrafo
    print("🔍 BUSCANDO CASOS PROBLEMÁTICOS...")
    print("=" * 80)
    
    # Extraer todo el texto para buscar patrones problemáticos
    all_text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        all_text += page_text + "\n"
    
    # Buscar frases cortadas típicas
    problematic_patterns = [
        r'atractivo\s*\n.*?de esta idea',
        r'necio para\s*\n.*?no ver',
        r'destino\s*\n.*?y se nos',
        r'práctica\s*\n.*?y el salto'
    ]
    
    for pattern in problematic_patterns:
        matches = re.finditer(pattern, all_text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            context = all_text[max(0, match.start()-50):match.end()+50]
            print(f"🚨 PATRÓN PROBLEMÁTICO ENCONTRADO:")
            print(f"   {repr(context)}")
            print()
    
    doc.close()

if __name__ == "__main__":
    debug_page_breaks() 