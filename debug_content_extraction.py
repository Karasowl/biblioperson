#!/usr/bin/env python3
"""
Script de debug para verificar la extracción de contenido del PDF de Neruda
"""

import fitz  # PyMuPDF
from pathlib import Path

def debug_pdf_extraction(pdf_path):
    """Debug de la extracción de contenido del PDF"""
    
    print(f"🔍 DEBUGGING EXTRACCIÓN PDF: {Path(pdf_path).name}")
    print("=" * 60)
    
    try:
        doc = fitz.open(pdf_path)
        text_lines = []
        
        for page_num in range(min(3, len(doc))):  # Solo primeras 3 páginas
            print(f"\n📄 PÁGINA {page_num + 1}:")
            print("-" * 40)
            
            page = doc.load_page(page_num)
            page_text = page.get_text()
            
            # Dividir en líneas y preservar estructura
            lines = page_text.split('\n')
            page_lines = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line:  # Solo agregar líneas no vacías
                    page_lines.append(line)
                    text_lines.append(line)
                    print(f"  {i+1:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
            
            print(f"\n📊 Página {page_num + 1}: {len(page_lines)} líneas extraídas")
        
        doc.close()
        
        # Crear texto estructurado
        content_sample = '\n'.join(text_lines)
        
        print(f"\n📋 RESUMEN TOTAL:")
        print(f"  - Total líneas: {len(text_lines)}")
        print(f"  - Total caracteres: {len(content_sample)}")
        
        # Análisis de estructura
        print(f"\n🔍 ANÁLISIS DE ESTRUCTURA:")
        short_lines = sum(1 for line in text_lines if len(line) <= 180)
        long_lines = len(text_lines) - short_lines
        
        print(f"  - Líneas cortas (≤180 chars): {short_lines} ({short_lines/len(text_lines)*100:.1f}%)")
        print(f"  - Líneas largas (>180 chars): {long_lines} ({long_lines/len(text_lines)*100:.1f}%)")
        
        # Mostrar primeras 10 líneas para análisis
        print(f"\n📝 PRIMERAS 10 LÍNEAS:")
        for i, line in enumerate(text_lines[:10]):
            print(f"  {i+1:2d}: [{len(line):3d}] {line}")
        
        # Guardar contenido para análisis
        with open("debug_extracted_content.txt", "w", encoding="utf-8") as f:
            f.write(content_sample)
        
        print(f"\n💾 Contenido guardado en: debug_extracted_content.txt")
        
        return content_sample
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    pdf_path = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    debug_pdf_extraction(pdf_path) 