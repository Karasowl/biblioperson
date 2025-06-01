#!/usr/bin/env python3
"""
Debug específico para PDFLoader - Investigar por qué marca como corrupto 
un PDF que visualmente está bien y anteriormente producía 60 poemas.
"""

import sys
import os
import re
import fitz
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_pdf_extraction_methods():
    """Analiza diferentes métodos de extracción de texto del PDF"""
    
    pdf_path = r"C:\Users\adven\Downloads\Mario Benedetti Antologia Poética.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        return
    
    print("🔍 ANÁLISIS DETALLADO DE EXTRACCIÓN PDF")
    print(f"📄 Archivo: {pdf_path}")
    print("=" * 80)
    
    # Abrir el PDF
    try:
        doc = fitz.open(pdf_path)
        print(f"✅ PDF abierto exitosamente")
        print(f"📊 Páginas: {len(doc)}")
        print()
    except Exception as e:
        print(f"❌ Error abriendo PDF: {e}")
        return
    
    # Analizar primera página con diferentes métodos
    page = doc[0]
    
    print("🧪 MÉTODO 1: get_text() - TEXTO PLANO")
    print("-" * 50)
    try:
        text_plain = page.get_text()
        print(f"📏 Longitud: {len(text_plain)} caracteres")
        print(f"📝 Primeros 300 chars: {repr(text_plain[:300])}")
        print(f"🔤 Texto real: {text_plain[:200]}")
        print()
        
        # Analizar caracteres
        analyze_character_composition(text_plain, "TEXTO PLANO")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🧪 MÉTODO 2: get_text('blocks') - BLOQUES")
    print("-" * 50)
    try:
        blocks = page.get_text("blocks")
        print(f"📦 Bloques encontrados: {len(blocks)}")
        
        all_block_text = ""
        for i, block in enumerate(blocks[:5]):  # Primeros 5 bloques
            if len(block) >= 5:
                block_text = str(block[4])
                all_block_text += block_text + "\n"
                print(f"  📄 Bloque {i+1}: {repr(block_text[:100])}")
                print(f"    🔤 Texto: {block_text[:100]}")
        
        analyze_character_composition(all_block_text, "BLOQUES")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🧪 MÉTODO 3: get_text('dict') - DICCIONARIO CON FORMATO")
    print("-" * 50)
    try:
        page_dict = page.get_text("dict")
        
        all_dict_text = ""
        block_count = 0
        
        for block in page_dict.get("blocks", []):
            if "lines" not in block:
                continue
                
            block_count += 1
            block_text = ""
            
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    block_text += text + " "
            
            if block_text.strip():
                all_dict_text += block_text + "\n"
                if block_count <= 3:  # Mostrar primeros 3 bloques
                    print(f"  📄 Bloque {block_count}: {repr(block_text[:100])}")
                    print(f"    🔤 Texto: {block_text[:100]}")
        
        print(f"📦 Bloques procesados: {block_count}")
        analyze_character_composition(all_dict_text, "DICCIONARIO")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🧪 MÉTODO 4: get_text('html') - HTML")
    print("-" * 50)
    try:
        html_text = page.get_text("html")
        # Extraer solo texto sin tags HTML
        import re
        clean_html = re.sub(r'<[^>]+>', ' ', html_text)
        clean_html = re.sub(r'\s+', ' ', clean_html).strip()
        
        print(f"📏 Longitud HTML: {len(html_text)} chars, limpio: {len(clean_html)} chars")
        print(f"🔤 Texto HTML limpio: {clean_html[:200]}")
        
        analyze_character_composition(clean_html, "HTML")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    doc.close()
    
    print("\n" + "=" * 80)
    print("🏁 ANÁLISIS COMPLETADO")
    print("\n💡 RECOMENDACIONES:")
    print("1. Si algún método muestra texto legible, el PDF NO está corrupto")
    print("2. Si todos muestran caracteres extraños, el problema está en el PDF")
    print("3. Si hay texto legible, el algoritmo de limpieza es demasiado agresivo")

def analyze_character_composition(text, method_name):
    """Analiza la composición de caracteres del texto extraído"""
    if not text:
        print(f"❌ {method_name}: Sin texto extraído")
        return
    
    # Contadores
    total_chars = len(text)
    ascii_letters = len(re.findall(r'[a-zA-Z]', text))
    spanish_chars = len(re.findall(r'[áéíóúüñÁÉÍÓÚÜÑ]', text))
    numbers = len(re.findall(r'[0-9]', text))
    punctuation = len(re.findall(r'[.,;:!?¿¡()"\'-]', text))
    spaces = len(re.findall(r'\s', text))
    
    # Caracteres "legibles" según el algoritmo actual
    current_algo_readable = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡()"\'-]', text))
    
    # Otros caracteres
    other_chars = total_chars - (ascii_letters + spanish_chars + numbers + punctuation + spaces)
    
    print(f"📊 COMPOSICIÓN DE CARACTERES - {method_name}:")
    print(f"  📏 Total: {total_chars}")
    print(f"  🔤 Letras ASCII: {ascii_letters} ({ascii_letters/total_chars*100:.1f}%)")
    print(f"  🇪🇸 Letras españolas: {spanish_chars} ({spanish_chars/total_chars*100:.1f}%)")
    print(f"  🔢 Números: {numbers} ({numbers/total_chars*100:.1f}%)")
    print(f"  📝 Puntuación: {punctuation} ({punctuation/total_chars*100:.1f}%)")
    print(f"  ⭐ Espacios: {spaces} ({spaces/total_chars*100:.1f}%)")
    print(f"  ❓ Otros: {other_chars} ({other_chars/total_chars*100:.1f}%)")
    print(f"  ✅ Legibles (algoritmo actual): {current_algo_readable} ({current_algo_readable/total_chars*100:.1f}%)")
    
    if other_chars > 0:
        # Mostrar algunos de los "otros" caracteres
        other_char_examples = []
        for char in text:
            if not re.match(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡()"\'-]', char):
                other_char_examples.append(f"'{char}'({ord(char)})")
                if len(other_char_examples) >= 10:
                    break
        
        if other_char_examples:
            print(f"  🔍 Ejemplos de 'otros': {', '.join(other_char_examples[:5])}")
    
    # Determinar si es "corrupto" según algoritmo actual
    corruption_ratio = 1.0 - (current_algo_readable / total_chars)
    print(f"  🚨 Corrupción detectada: {corruption_ratio*100:.1f}%")
    
    if corruption_ratio > 0.2:
        print(f"  ⚠️ ALGORITMO ACTUAL MARCARIA COMO CORRUPTO")
    else:
        print(f"  ✅ ALGORITMO ACTUAL LO ACEPTARÍA")
    
    print()

if __name__ == "__main__":
    analyze_pdf_extraction_methods() 