#!/usr/bin/env python3
"""
Análisis detallado de la estructura real del PDF de Benedetti
Para identificar todos los patrones de separación entre poemas
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from pathlib import Path
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def analyze_benedetti_structure():
    print("🔍 ANÁLISIS DETALLADO: Estructura real del PDF de Benedetti")
    
    # Ruta del archivo PDF
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n1️⃣ PASO 1: Cargar y pre-procesar PDF")
    
    # Cargar PDF
    loader = PDFLoader(str(archivo_pdf))
    raw_blocks = loader.load()
    print(f"   📄 Bloques cargados del PDF: {len(raw_blocks)}")
    
    # Pre-procesar
    preprocessor = CommonBlockPreprocessor({'clean_unicode_corruption': True})
    processed_blocks, metadata = preprocessor.process(raw_blocks, {})
    print(f"   🧹 Bloques después de limpieza: {len(processed_blocks)}")
    
    print(f"\n2️⃣ PASO 2: Analizar patrones de separación")
    
    # Categorizar todos los bloques
    categorias = {
        'titulos_explícitos': [],
        'posibles_titulos': [],
        'texto_poético': [],
        'separadores_visuales': [],
        'listas_títulos': [],
        'números_página': [],
        'otros': []
    }
    
    for i, block in enumerate(processed_blocks):
        text = block.get('text', '').strip()
        if not text:
            continue
            
        # Analizar patrones específicos
        analyze_block_patterns(text, i, categorias)
    
    # Mostrar estadísticas
    print(f"\n📊 ESTADÍSTICAS DE CATEGORIZACIÓN:")
    for categoria, items in categorias.items():
        print(f"   {categoria}: {len(items)} bloques")
        
        # Mostrar ejemplos de cada categoría
        if items and len(items) <= 10:
            print(f"      Ejemplos:")
            for item in items[:5]:  # Solo primeros 5
                texto = item['text'][:60] + '...' if len(item['text']) > 60 else item['text']
                print(f"         [{item['index']}] {repr(texto)}")
        elif items:
            print(f"      Primeros ejemplos:")
            for item in items[:3]:
                texto = item['text'][:60] + '...' if len(item['text']) > 60 else item['text']
                print(f"         [{item['index']}] {repr(texto)}")
    
    print(f"\n3️⃣ PASO 3: Detectar patrones de inicio de poema")
    
    # Buscar todos los posibles inicios de poema
    posibles_inicios = detect_poem_starts(processed_blocks)
    
    print(f"   🎯 POSIBLES INICIOS DE POEMA DETECTADOS: {len(posibles_inicios)}")
    
    # Mostrar primeros 20 inicios detectados
    print(f"\n   📝 PRIMEROS 20 INICIOS DETECTADOS:")
    for i, inicio in enumerate(posibles_inicios[:20]):
        bloque_idx = inicio['block_index']
        motivo = inicio['reason']
        texto = inicio['text'][:80] + '...' if len(inicio['text']) > 80 else inicio['text']
        print(f"      [{bloque_idx:3d}] {motivo}: {repr(texto)}")
    
    print(f"\n4️⃣ PASO 4: Proponer mejoras al algoritmo")
    
    # Analizar qué porcentaje de inicios detectamos vs lo que el usuario encontró
    inicios_detectados = len(posibles_inicios)
    inicios_esperados = 140  # Según análisis del usuario
    
    cobertura = (inicios_detectados / inicios_esperados) * 100
    
    print(f"   📈 ANÁLISIS DE COBERTURA:")
    print(f"      Inicios detectados: {inicios_detectados}")
    print(f"      Inicios esperados: {inicios_esperados}")
    print(f"      Cobertura actual: {cobertura:.1f}%")
    
    if cobertura < 80:
        print(f"   ⚠️  COBERTURA INSUFICIENTE - Necesitamos detectar más patrones")
    elif cobertura > 120:
        print(f"   ⚠️  SOBREDETECCIÓN - Necesitamos ser más selectivos")
    else:
        print(f"   ✅ COBERTURA ADECUADA - Algoritmo funcionando bien")
    
    return {
        'categorias': categorias,
        'posibles_inicios': posibles_inicios,
        'cobertura': cobertura
    }

def analyze_block_patterns(text, index, categorias):
    """Analiza un bloque y lo categoriza según sus patrones"""
    
    # 1. Títulos explícitos (entre comillas)
    if re.match(r'^["""].*["""]$', text.strip()) and len(text) < 100:
        categorias['titulos_explícitos'].append({'index': index, 'text': text})
        return
    
    # 2. Posibles títulos (cortos, sin puntuación final, mayúscula inicial)
    if (len(text) < 50 and 
        text[0].isupper() and 
        not text.endswith(('.', '!', '?')) and
        len(text.split()) <= 6 and
        not text.isdigit()):
        categorias['posibles_titulos'].append({'index': index, 'text': text})
        return
    
    # 3. Números de página
    if re.match(r'^\d+$', text) or re.match(r'^Página \d+$', text, re.IGNORECASE):
        categorias['números_página'].append({'index': index, 'text': text})
        return
    
    # 4. Separadores visuales (líneas, asteriscos, etc.)
    if re.match(r'^[\*\-_=]{3,}$', text) or text in ['***', '---', '___']:
        categorias['separadores_visuales'].append({'index': index, 'text': text})
        return
    
    # 5. Listas de títulos (patrones como "1. Título", "- Título")
    if re.match(r'^\d+[\.\)]\s+\w+', text) or re.match(r'^[-•]\s+\w+', text):
        categorias['listas_títulos'].append({'index': index, 'text': text})
        return
    
    # 6. Texto poético (más de 20 caracteres, contiene saltos de línea o versos)
    if len(text) > 20 and ('\n' in text or has_poetic_structure(text)):
        categorias['texto_poético'].append({'index': index, 'text': text})
        return
    
    # 7. Otros
    categorias['otros'].append({'index': index, 'text': text})

def has_poetic_structure(text):
    """Detecta si un texto tiene estructura poética"""
    lines = text.split('\n')
    
    # Características poéticas:
    # - Líneas cortas (menos de 80 caracteres promedio)
    # - Variación en longitud de líneas
    # - No termina todas las líneas con punto
    
    if len(lines) < 2:
        return False
    
    avg_line_length = sum(len(line) for line in lines) / len(lines)
    lines_without_period = sum(1 for line in lines if not line.strip().endswith('.'))
    
    return (avg_line_length < 80 and 
            lines_without_period > len(lines) * 0.6)

def detect_poem_starts(blocks):
    """Detecta todos los posibles inicios de poema usando múltiples heurísticas"""
    
    inicios = []
    
    for i, block in enumerate(blocks):
        text = block.get('text', '').strip()
        if not text:
            continue
        
        motivos = []
        
        # 1. Títulos explícitos entre comillas
        if re.match(r'^["""].*["""]$', text.strip()) and len(text) < 100:
            motivos.append("TÍTULO_EXPLÍCITO")
        
        # 2. Texto corto que podría ser título
        if (len(text) < 60 and 
            text[0].isupper() and 
            not text.endswith(('.', '!', '?')) and
            len(text.split()) <= 8 and
            not text.isdigit()):
            motivos.append("POSIBLE_TÍTULO")
        
        # 3. Después de separador visual
        if i > 0:
            prev_text = blocks[i-1].get('text', '').strip()
            if (re.match(r'^[\*\-_=]{3,}$', prev_text) or 
                prev_text in ['***', '---', '___', '']):
                motivos.append("DESPUÉS_SEPARADOR")
        
        # 4. Cambio de página (posible nuevo poema)
        if i > 0:
            prev_page = blocks[i-1].get('page', 0)
            curr_page = block.get('page', 0)
            if curr_page > prev_page:
                motivos.append("NUEVA_PÁGINA")
        
        # 5. Después de bloque con mucho texto (fin de poema anterior)
        if i > 0:
            prev_text = blocks[i-1].get('text', '').strip()
            if len(prev_text) > 200:  # Bloque largo anterior
                motivos.append("DESPUÉS_TEXTO_LARGO")
        
        # 6. Estructura de verso clara (líneas cortas, sin puntuación)
        if has_clear_verse_structure(text):
            motivos.append("ESTRUCTURA_VERSO")
        
        # 7. Patrón de lista numerada
        if re.match(r'^\d+[\.\)]\s+', text):
            motivos.append("LISTA_NUMERADA")
        
        # 8. Headings detectados por el PDF
        if block.get('is_heading', False):
            motivos.append("HEADING_PDF")
        
        # Si encontramos algún motivo, es un posible inicio
        if motivos:
            inicios.append({
                'block_index': i,
                'text': text,
                'reason': ' + '.join(motivos),
                'page': block.get('page', 0)
            })
    
    return inicios

def has_clear_verse_structure(text):
    """Detecta estructura clara de verso"""
    lines = text.split('\n')
    
    if len(lines) < 2:
        return False
    
    # Características de verso:
    # - Líneas generalmente cortas (< 60 caracteres)
    # - No todas terminan en punto
    # - Al menos 3 líneas
    
    short_lines = sum(1 for line in lines if len(line.strip()) < 60)
    no_period_lines = sum(1 for line in lines if not line.strip().endswith('.'))
    
    return (len(lines) >= 3 and 
            short_lines > len(lines) * 0.7 and
            no_period_lines > len(lines) * 0.5)

if __name__ == "__main__":
    resultado = analyze_benedetti_structure()
    print(f"\n✅ Análisis completado")
    if resultado:
        print(f"   📊 Cobertura: {resultado['cobertura']:.1f}%")
        print(f"   🎯 Inicios detectados: {len(resultado['posibles_inicios'])}") 