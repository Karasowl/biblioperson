#!/usr/bin/env python3
"""
DEBUG PYMUPDF4LLM RAW OUTPUT
============================

Analizar el texto crudo que genera pymupdf4llm 
para entender por qué no preserva los saltos de línea.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_pymupdf4llm_raw():
    """Analizar la salida cruda de pymupdf4llm"""
    
    test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return False
    
    print("🔍 DEBUG PYMUPDF4LLM RAW OUTPUT")
    print("=" * 50)
    
    try:
        import pymupdf4llm
        print("✅ pymupdf4llm disponible")
    except ImportError:
        print("❌ pymupdf4llm no disponible")
        return False
    
    # 1. EXTRAER MARKDOWN CRUDO
    print("\n1️⃣ EXTRAYENDO MARKDOWN CRUDO:")
    print("-" * 40)
    
    markdown_text = pymupdf4llm.to_markdown(test_file)
    
    print(f"📊 Estadísticas del markdown crudo:")
    print(f"   - Longitud total: {len(markdown_text)} caracteres")
    print(f"   - Saltos de línea: {markdown_text.count(chr(10))}")
    print(f"   - Dobles saltos: {markdown_text.count(chr(10) + chr(10))}")
    
    # 2. BUSCAR EL POEMA 13 EN EL MARKDOWN CRUDO
    print("\n2️⃣ BUSCANDO POEMA 13 EN MARKDOWN CRUDO:")
    print("-" * 40)
    
    lines = markdown_text.split('\n')
    
    # Buscar inicio del Poema 13
    poema_13_start = None
    poema_13_end = None
    
    for i, line in enumerate(lines):
        if 'Poema 13' in line:
            poema_13_start = i
            print(f"📍 Poema 13 encontrado en línea {i}: {repr(line)}")
            break
    
    if poema_13_start is None:
        print("❌ Poema 13 no encontrado")
        return False
    
    # Buscar final del Poema 13 (siguiente título o final)
    for i in range(poema_13_start + 1, len(lines)):
        line = lines[i].strip()
        if (line.startswith('Poema ') or 
            line.startswith('## ') or 
            'Página de' in line or
            i - poema_13_start > 30):  # Máximo 30 líneas
            poema_13_end = i
            break
    
    if poema_13_end is None:
        poema_13_end = min(poema_13_start + 20, len(lines))
    
    # 3. MOSTRAR POEMA 13 COMPLETO
    print(f"\n3️⃣ POEMA 13 COMPLETO ({poema_13_start} a {poema_13_end}):")
    print("-" * 40)
    
    poema_13_lines = lines[poema_13_start:poema_13_end]
    
    for i, line in enumerate(poema_13_lines):
        line_num = poema_13_start + i
        print(f"   {line_num:3d}: {repr(line)}")
    
    # 4. ANALIZAR ESTRUCTURA
    print(f"\n4️⃣ ANÁLISIS DE ESTRUCTURA:")
    print("-" * 40)
    
    poema_13_text = '\n'.join(poema_13_lines)
    
    print(f"📊 Estadísticas del Poema 13:")
    print(f"   - Líneas totales: {len(poema_13_lines)}")
    print(f"   - Líneas no vacías: {sum(1 for line in poema_13_lines if line.strip())}")
    print(f"   - Líneas vacías: {sum(1 for line in poema_13_lines if not line.strip())}")
    print(f"   - Saltos de línea: {poema_13_text.count(chr(10))}")
    print(f"   - Longitud total: {len(poema_13_text)} caracteres")
    
    # 5. DETECTAR VERSOS POTENCIALES
    print(f"\n5️⃣ DETECCIÓN DE VERSOS POTENCIALES:")
    print("-" * 40)
    
    content_lines = [line for line in poema_13_lines if line.strip() and not line.startswith('Poema')]
    
    if content_lines:
        print("📝 Líneas de contenido detectadas:")
        for i, line in enumerate(content_lines):
            line_clean = line.strip()
            if line_clean:
                # Analizar si parece contener múltiples versos
                sentences = line_clean.split('. ')
                print(f"   {i+1}: {repr(line_clean[:100])}{'...' if len(line_clean) > 100 else ''}")
                print(f"       - Oraciones: {len(sentences)}")
                print(f"       - Longitud: {len(line_clean)}")
                
                # Buscar patrones de final de verso
                potential_verse_ends = []
                patterns = [r'\.', r'\!', r'\?', r',']
                for pattern in patterns:
                    import re
                    matches = list(re.finditer(pattern, line_clean))
                    potential_verse_ends.extend([m.start() for m in matches])
                
                print(f"       - Finales potenciales: {len(potential_verse_ends)}")
    
    # 6. COMPARAR CON ESTRUCTURA ESPERADA
    print(f"\n6️⃣ COMPARACIÓN CON ESTRUCTURA ESPERADA:")
    print("-" * 40)
    
    expected_verses = [
        "He ido marcando con cruces de fuego",
        "el atlas blanco de tu cuerpo.",
        "Mi boca era una araña que cruzaba escondiéndose.",
        "En ti, detrás de ti, temerosa, sedienta.",
        "Historias que contarte a la orilla del crepúsculo,",
        "muñeca triste y dulce, para que no estuvieras triste."
    ]
    
    print("✅ Estructura esperada (primeros versos):")
    for i, verse in enumerate(expected_verses):
        print(f"   {i+1}: {repr(verse)}")
    
    print(f"\n❌ Estructura actual (concatenada):")
    if content_lines:
        actual_text = content_lines[0] if content_lines else ""
        print(f"   Todo en línea: {repr(actual_text[:200])}...")
    
    return True

if __name__ == "__main__":
    print("🧪 DEBUG PYMUPDF4LLM RAW OUTPUT")
    print("=" * 50)
    
    debug_pymupdf4llm_raw() 