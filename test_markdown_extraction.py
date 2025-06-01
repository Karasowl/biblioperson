#!/usr/bin/env python3
"""
Prueba: PDF → Markdown Estructurado

Probar diferentes métodos de extracción que mantengan la estructura
del PDF sin corromper el texto.
"""

import sys
from pathlib import Path
import fitz
import re

def test_extraction_methods():
    """Probar diferentes métodos de extracción PDF → MD"""
    
    pdf_path = r"C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return
        
    print("🔍 PRUEBA: DIFERENTES MÉTODOS DE EXTRACCIÓN")
    print("=" * 60)
    
    # MÉTODO 1: PyMuPDF con get_text() simple
    print("📋 MÉTODO 1: PyMuPDF get_text() Simple")
    print("-" * 40)
    
    try:
        doc = fitz.open(pdf_path)
        method1_text = ""
        
        for page_num in range(min(3, len(doc))):  # Solo primeras 3 páginas
            page = doc[page_num]
            page_text = page.get_text()
            method1_text += f"\n=== PÁGINA {page_num + 1} ===\n"
            method1_text += page_text
        
        print(f"✅ Extraído - Primeras 300 chars:")
        print(f"'{method1_text[:300]}...'")
        
        # Verificar corrupción
        corrupted_chars = sum(1 for char in method1_text[:1000] if ord(char) < 32 and char not in '\n\r\t')
        corruption_rate = corrupted_chars / min(1000, len(method1_text)) * 100
        print(f"📊 Corrupción detectada: {corruption_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # MÉTODO 2: PyMuPDF con get_text("blocks")
    print(f"\n📋 MÉTODO 2: PyMuPDF get_text('blocks')")
    print("-" * 40)
    
    try:
        method2_text = ""
        
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            
            method2_text += f"\n=== PÁGINA {page_num + 1} ===\n"
            
            for block in blocks:
                if len(block) >= 5:  # block[4] contiene el texto
                    block_text = block[4].strip()
                    if block_text:
                        method2_text += block_text + "\n\n"
        
        print(f"✅ Extraído - Primeras 300 chars:")
        print(f"'{method2_text[:300]}...'")
        
        # Verificar corrupción
        corrupted_chars = sum(1 for char in method2_text[:1000] if ord(char) < 32 and char not in '\n\r\t')
        corruption_rate = corrupted_chars / min(1000, len(method2_text)) * 100
        print(f"📊 Corrupción detectada: {corruption_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # MÉTODO 3: PyMuPDF con get_text("dict") más detallado
    print(f"\n📋 MÉTODO 3: PyMuPDF get_text('dict') Detallado")
    print("-" * 40)
    
    try:
        method3_text = ""
        
        for page_num in range(min(2, len(doc))):  # Solo 2 páginas para dict
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            method3_text += f"\n=== PÁGINA {page_num + 1} ===\n"
            
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    block_text = ""
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                        if line_text.strip():
                            block_text += line_text + "\n"
                    
                    if block_text.strip():
                        # Detectar si parece título
                        first_line = block_text.strip().split('\n')[0]
                        if len(first_line) < 80 and any(word in first_line.lower() for word in ['poema', 'canción']):
                            method3_text += f"## {first_line}\n\n"
                        else:
                            method3_text += block_text + "\n"
        
        print(f"✅ Extraído - Primeras 300 chars:")
        print(f"'{method3_text[:300]}...'")
        
        # Verificar corrupción
        corrupted_chars = sum(1 for char in method3_text[:1000] if ord(char) < 32 and char not in '\n\r\t')
        corruption_rate = corrupted_chars / min(1000, len(method3_text)) * 100
        print(f"📊 Corrupción detectada: {corruption_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # MÉTODO 4: Intentar con pymupdf4llm (si está disponible)
    print(f"\n📋 MÉTODO 4: pymupdf4llm (si disponible)")
    print("-" * 40)
    
    try:
        import pymupdf4llm
        
        # Convertir solo primeras páginas
        md_text = pymupdf4llm.to_markdown(pdf_path, pages=[0, 1, 2])
        
        print(f"✅ Extraído - Primeras 300 chars:")
        print(f"'{md_text[:300]}...'")
        
        # Verificar corrupción
        corrupted_chars = sum(1 for char in md_text[:1000] if ord(char) < 32 and char not in '\n\r\t')
        corruption_rate = corrupted_chars / min(1000, len(md_text)) * 100
        print(f"📊 Corrupción detectada: {corruption_rate:.1f}%")
        
        # Contar poemas detectados
        poem_patterns = [
            r'^#+ Poema \d+',
            r'^Poema \d+',
            r'^\d+\.',
        ]
        
        poem_count = 0
        for line in md_text.split('\n'):
            line = line.strip()
            for pattern in poem_patterns:
                if re.match(pattern, line):
                    poem_count += 1
                    break
        
        print(f"🎭 Poemas detectados: {poem_count}")
        
    except ImportError:
        print("⚠️ pymupdf4llm no disponible - instalando...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf4llm"])
            print("✅ Instalado - ejecuta el script de nuevo")
        except:
            print("❌ No se pudo instalar pymupdf4llm")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    doc.close()
    
    # COMPARACIÓN Y RECOMENDACIONES
    print(f"\n📊 COMPARACIÓN Y RECOMENDACIONES")
    print("-" * 40)
    
    print(f"🎯 RESULTADOS:")
    print(f"   Método 1 (simple): Rápido pero puede perder estructura")
    print(f"   Método 2 (blocks): Mejor estructura, bloques definidos")
    print(f"   Método 3 (dict): Máximo detalle, estructura jerárquica")
    print(f"   Método 4 (pymupdf4llm): Conversión directa a markdown")
    
    print(f"\n💡 RECOMENDACIÓN:")
    print(f"   • Si hay corrupción en todos los métodos → PDF realmente corrupto")
    print(f"   • Si solo Método 1 tiene corrupción → Usar Método 2 o 3")
    print(f"   • Si Método 4 funciona bien → Usar pymupdf4llm")
    print(f"   • Si ninguno funciona → Usar OCR como backup")

def test_markdown_to_blocks():
    """Probar conversión de markdown estructurado a bloques"""
    
    print(f"\n🔧 PRUEBA: MARKDOWN → BLOQUES ESTRUCTURADOS")
    print("-" * 40)
    
    # Ejemplo de markdown bien estructurado
    sample_md = """
# Veinte Poemas de Amor y Una Canción Desesperada

## Poema 1

Cuerpo de mujer, blancas colinas, muslos blancos,
te pareces al mundo en tu actitud de entrega.
Mi cuerpo de labriego salvaje te socava
y hace saltar el hijo del fondo de la tierra.

Fui solo como un túnel. De mí huían los pájaros
y en mí la noche entraba su invasión poderosa.

## Poema 2

En su llama mortal la luz te envuelve.
Absorta, pálida doliente, así situada
contra las viejas hélices del crepúsculo
que en torno a ti da vueltas.

## Canción Desesperada

Emerge tu recuerdo de la noche en que estoy.
El río anuda al mar su lamento obstinado.
"""
    
    # Convertir MD a bloques estructurados
    blocks = []
    current_poem = None
    current_content = []
    
    for line in sample_md.split('\n'):
        line = line.strip()
        
        if line.startswith('## '):  # Título de poema
            # Guardar poema anterior si existe
            if current_poem and current_content:
                blocks.append({
                    'type': 'poem',
                    'title': current_poem,
                    'content': '\n'.join(current_content).strip(),
                    'lines': len(current_content)
                })
            
            # Iniciar nuevo poema
            current_poem = line[3:].strip()
            current_content = []
            
        elif line.startswith('# '):  # Título principal
            blocks.append({
                'type': 'title',
                'content': line[2:].strip()
            })
            
        elif line and current_poem:  # Contenido del poema
            current_content.append(line)
    
    # Guardar último poema
    if current_poem and current_content:
        blocks.append({
            'type': 'poem',
            'title': current_poem,
            'content': '\n'.join(current_content).strip(),
            'lines': len(current_content)
        })
    
    print(f"✅ Bloques estructurados creados: {len(blocks)}")
    for i, block in enumerate(blocks, 1):
        if block['type'] == 'poem':
            print(f"   {i}. [POEMA] {block['title']} ({block['lines']} líneas)")
        else:
            print(f"   {i}. [TÍTULO] {block['content']}")
    
    return blocks

if __name__ == "__main__":
    test_extraction_methods()
    test_markdown_to_blocks() 