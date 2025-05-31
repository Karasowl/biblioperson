#!/usr/bin/env python3
"""
Script específico para analizar la extracción RAW de PyMuPDF
y ver exactamente dónde se divide "atractivo de esta idea"
"""

import fitz
import re

def analyze_pdf_extraction():
    pdf_path = r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf"
    
    print("🔍 ANÁLISIS EXTRACCIÓN RAW DE PyMuPDF")
    print("=" * 60)
    
    # Abrir PDF
    doc = fitz.open(pdf_path)
    
    found_blocks = []
    target_phrases = ["atractivo", "de esta idea", "dominar colectivamente"]
    
    # Analizar cada página
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        print(f"\n📄 PÁGINA {page_num + 1}:")
        
        # 1. Extraer texto simple
        page_text = page.get_text()
        for phrase in target_phrases:
            if phrase in page_text.lower():
                print(f"   ✓ Contiene '{phrase}' en texto simple")
        
        # 2. Extraer bloques con get_text("dict")
        text_dict = page.get_text("dict")
        
        for block_idx, block in enumerate(text_dict.get("blocks", [])):
            if "lines" in block:  # Es un bloque de texto
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                
                # Verificar si contiene nuestras frases objetivo
                for phrase in target_phrases:
                    if phrase in block_text.lower():
                        print(f"\n🎯 BLOQUE {block_idx} (PÁGINA {page_num + 1}) CONTIENE '{phrase}':")
                        print(f"   Texto completo: '{block_text}'")
                        print(f"   Bbox: {block.get('bbox', 'N/A')}")
                        
                        found_blocks.append({
                            'page': page_num + 1,
                            'block_idx': block_idx,
                            'text': block_text,
                            'phrase': phrase,
                            'bbox': block.get('bbox', None)
                        })
        
        # 3. También probar get_text("blocks") para comparar
        blocks_method = page.get_text("blocks")
        print(f"   Método 'blocks': {len(blocks_method)} bloques")
        
        for block_idx, block in enumerate(blocks_method):
            # block es una tupla: (x0, y0, x1, y1, text, block_no, block_type)
            if len(block) >= 5:
                block_text = block[4]
                for phrase in target_phrases:
                    if phrase in block_text.lower():
                        print(f"\n🎯 BLOCKS METHOD - BLOQUE {block_idx} CONTIENE '{phrase}':")
                        print(f"   Texto: '{block_text[:100]}...'")
                        print(f"   Bbox: ({block[0]}, {block[1]}, {block[2]}, {block[3]})")
    
    doc.close()
    
    print(f"\n📊 RESUMEN:")
    print(f"   Total bloques encontrados con frases objetivo: {len(found_blocks)}")
    
    # Buscar específicamente el patrón "atractivo" -> "de esta idea"
    atractivo_blocks = [b for b in found_blocks if "atractivo" in b["text"].lower()]
    idea_blocks = [b for b in found_blocks if "de esta idea" in b["text"].lower()]
    
    print(f"\n🔍 ANÁLISIS ESPECÍFICO:")
    print(f"   Bloques con 'atractivo': {len(atractivo_blocks)}")
    print(f"   Bloques con 'de esta idea': {len(idea_blocks)}")
    
    if atractivo_blocks and idea_blocks:
        print(f"\n🚨 DIVISIÓN DETECTADA:")
        for atractivo_block in atractivo_blocks:
            if not any("de esta idea" in b["text"].lower() for b in atractivo_blocks):
                print(f"   BLOQUE ATRACTIVO (PÁGINA {atractivo_block['page']}):")
                print(f"     '{atractivo_block['text']}'")
        
        for idea_block in idea_blocks:
            if not any("atractivo" in b["text"].lower() for b in idea_blocks):
                print(f"   BLOQUE DE ESTA IDEA (PÁGINA {idea_block['page']}):")
                print(f"     '{idea_block['text']}'")
    
    # Analizar bloques consecutivos que podrían estar divididos
    print(f"\n🔗 BUSCAR BLOQUES CONSECUTIVOS DIVIDIDOS:")
    for i, block1 in enumerate(found_blocks):
        for j, block2 in enumerate(found_blocks):
            if (block1['page'] == block2['page'] and 
                abs(block1['block_idx'] - block2['block_idx']) <= 2 and
                i != j):
                
                text1 = block1['text'].strip()
                text2 = block2['text'].strip()
                
                # Verificar patrones de división
                if (text1.lower().endswith('atractivo') and 
                    text2.lower().startswith('de esta idea')):
                    print(f"   🎯 DIVISIÓN ENCONTRADA:")
                    print(f"     Bloque {block1['block_idx']}: '{text1}'")
                    print(f"     Bloque {block2['block_idx']}: '{text2}'")
                    print(f"     Página: {block1['page']}")

if __name__ == "__main__":
    analyze_pdf_extraction() 