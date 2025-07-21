#!/usr/bin/env python3
"""
Script para debuggear la extracción de PDF y ver si el problema está en el OCR o en el texto original
"""

import fitz  # PyMuPDF

def test_pdf_extraction(pdf_path):
    """Probar extracción de PDF con diferentes métodos"""
    
    print(f"🔍 Analizando PDF: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        print(f"📄 Páginas en el documento: {len(doc)}")
        
        # Probar extracción tradicional (sin OCR)
        print("\n🔍 MÉTODO 1: Extracción tradicional (sin OCR)")
        for page_num in range(min(2, len(doc))):  # Solo primeras 2 páginas
            page = doc.load_page(page_num)
            text = page.get_text()
            
            print(f"\n📄 Página {page_num + 1}:")
            print(f"   📊 Caracteres extraídos: {len(text)}")
            
            # Mostrar primeras líneas
            lines = text.split('\n')[:10]  # Primeras 10 líneas
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"   {i+1:2d}: '{line.strip()}'")
        
        # Probar extracción con get_text("dict")
        print("\n🔍 MÉTODO 2: Extracción estructurada (dict)")
        page = doc.load_page(0)
        text_dict = page.get_text("dict")
        
        print(f"📊 Bloques encontrados: {len(text_dict.get('blocks', []))}")
        
        for i, block in enumerate(text_dict.get('blocks', [])[:5]):  # Primeros 5 bloques
            if 'lines' in block:
                print(f"\n📦 Bloque {i+1}:")
                for j, line in enumerate(block['lines'][:3]):  # Primeras 3 líneas del bloque
                    line_text = ""
                    for span in line.get('spans', []):
                        line_text += span.get('text', '')
                    if line_text.strip():
                        print(f"   Línea {j+1}: '{line_text.strip()}'")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    pdf_path = r"C:\Users\adven\Downloads\Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    test_pdf_extraction(pdf_path) 