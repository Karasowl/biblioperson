#!/usr/bin/env python3
"""
Test para detectar y limpiar texto corrupto con caracteres Unicode
"""

import sys
sys.path.append('.')

import re
from pathlib import Path
from dataset.processing.loaders.pdf_loader import PDFLoader

def detect_unicode_corruption(text):
    """
    Detecta patrones de corrupción Unicode en el texto.
    """
    if not text:
        return False, []
    
    # Patrones de caracteres problemáticos
    corruption_patterns = [
        r'\\u[0-9a-fA-F]{4}',  # Secuencias \u0001, \u001a, etc.
        r'[\x00-\x1F\x7F-\x9F]+',  # Caracteres de control ASCII/Unicode
        r'[^\x20-\x7E\u00A0-\uFFFF]+',  # Caracteres fuera del rango imprimible normal
    ]
    
    issues = []
    is_corrupted = False
    
    for pattern in corruption_patterns:
        matches = re.findall(pattern, text)
        if matches:
            is_corrupted = True
            issues.extend(matches)
    
    return is_corrupted, issues

def clean_unicode_corruption(text):
    """
    Limpia texto corrupto con caracteres Unicode de escape.
    """
    if not text:
        return text
    
    # 1. Remover secuencias \u seguidas de 4 caracteres hex
    text = re.sub(r'\\u[0-9a-fA-F]{4}', ' ', text)
    
    # 2. Remover caracteres de control (0x00-0x1F excepto \n, \r, \t)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', ' ', text)
    
    # 3. Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    # 4. Limpiar líneas vacías excesivas
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

def test_benedetti_corruption():
    print("🔍 TEST: Detección de corrupción Unicode en PDF Benedetti")
    
    # Ruta del archivo PDF del usuario
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n📁 Archivo: {archivo_pdf.name}")
    
    # PASO 1: Cargar PDF con PDFLoader
    print(f"\n1️⃣ PASO 1: Cargar PDF y analizar corrupción")
    loader = PDFLoader(archivo_pdf, tipo='poemas')
    resultado_loader = loader.load()
    
    bloques_originales = resultado_loader.get('blocks', [])
    print(f"   ✅ Bloques cargados: {len(bloques_originales)}")
    
    # PASO 2: Analizar corrupción en los primeros bloques
    print(f"\n2️⃣ PASO 2: Detectar texto corrupto")
    
    corrupted_count = 0
    clean_count = 0
    corruption_examples = []
    
    for i, bloque in enumerate(bloques_originales[:200], 1):  # Analizar primeros 200 bloques
        texto = bloque.get('text', '')
        
        is_corrupted, issues = detect_unicode_corruption(texto)
        
        if is_corrupted:
            corrupted_count += 1
            if len(corruption_examples) < 5:  # Guardar ejemplos
                corruption_examples.append({
                    'block_num': i,
                    'original': texto[:200] + '...' if len(texto) > 200 else texto,
                    'issues': issues[:10]  # Primeros 10 problemas
                })
        else:
            clean_count += 1
    
    print(f"   📊 Análisis de {len(bloques_originales[:200])} bloques:")
    print(f"      ✅ Bloques limpios: {clean_count}")
    print(f"      ❌ Bloques corruptos: {corrupted_count}")
    print(f"      📈 Porcentaje corrupto: {(corrupted_count/(clean_count+corrupted_count)*100):.1f}%")
    
    # PASO 3: Mostrar ejemplos de corrupción
    if corruption_examples:
        print(f"\n3️⃣ PASO 3: Ejemplos de texto corrupto detectado")
        for i, ejemplo in enumerate(corruption_examples, 1):
            print(f"\n   Ejemplo {i} (Bloque {ejemplo['block_num']}):")
            print(f"   Original: {ejemplo['original']}")
            print(f"   Problemas: {ejemplo['issues']}")
            
            # Mostrar versión limpia
            texto_limpio = clean_unicode_corruption(ejemplo['original'])
            print(f"   Limpio: {texto_limpio}")
    
    # PASO 4: Test de limpieza completa
    print(f"\n4️⃣ PASO 4: Test de limpieza en todos los bloques")
    
    bloques_limpios = []
    total_cleaned = 0
    
    for bloque in bloques_originales:
        texto_original = bloque.get('text', '')
        texto_limpio = clean_unicode_corruption(texto_original)
        
        if texto_original != texto_limpio:
            total_cleaned += 1
        
        # Crear bloque limpio
        bloque_limpio = bloque.copy()
        bloque_limpio['text'] = texto_limpio
        bloques_limpios.append(bloque_limpio)
    
    print(f"   ✅ Bloques procesados: {len(bloques_limpios)}")
    print(f"   🧹 Bloques limpiados: {total_cleaned}")
    print(f"   📈 Porcentaje limpiado: {(total_cleaned/len(bloques_originales)*100):.1f}%")
    
    return bloques_limpios

if __name__ == "__main__":
    test_benedetti_corruption() 