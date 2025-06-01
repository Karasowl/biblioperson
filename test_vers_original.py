#!/usr/bin/env python3
"""
Test del VerseSegmenter con algoritmo ORIGINAL según ALGORITMOS_PROPUESTOS.md
Verificamos que "Mis Poemas.docx" detecta exactamente 5 poemas como funcionaba antes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.loaders.docx_loader import DocxLoader
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
import logging

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_algoritmo_original():
    """Test del algoritmo original conservador"""
    
    # Archivo que SABEMOS que tiene 5 poemas y funcionaba antes
    docx_path = "C:/Users/adven/OneDrive/Escritorio/probando biblioperson/Recopilación de Escritos Propios/biblioteca_personal/raw/poesías/Mis Poemas.docx"
    
    if not os.path.exists(docx_path):
        print(f"❌ Archivo no encontrado: {docx_path}")
        return
    
    print(f"📖 Cargando: {docx_path}")
    
    # 1. Cargar con DocxLoader
    loader = DocxLoader(docx_path)
    result = loader.load()
    
    print(f"📄 Resultado cargado: {type(result)}")
    print(f"📄 Claves disponibles: {list(result.keys()) if isinstance(result, dict) else 'No es dict'}")
    
    # Extraer los bloques del resultado
    if isinstance(result, dict) and 'blocks' in result:
        blocks = result['blocks']
        print(f"📄 Bloques extraídos: {len(blocks)} elementos")
    else:
        blocks = result
        print(f"📄 Usando resultado directo: {len(blocks) if hasattr(blocks, '__len__') else 'Sin len'}")
    
    # Debug: mostrar estructura de bloques
    print(f"\n📋 Primeros 10 bloques:")
    for i, block in enumerate(blocks[:10]):
        text_preview = block.get('text', '')[:30].replace('\n', ' ')
        is_heading = block.get('is_heading', False)
        is_bold = block.get('is_bold', False)
        print(f"   {i}: {'[H]' if is_heading else '[ ]'} {'[B]' if is_bold else '[ ]'} '{text_preview}...'")
    
    print(f"\n🔍 ACTIVANDO DEBUG LOGGING...")
    logging.getLogger('dataset.processing.segmenters.verse_segmenter').setLevel(logging.DEBUG)
    
    # 🔧 DEBUG MANUAL: Probar _is_main_title() con el primer bloque
    print(f"\n🔧 TEST MANUAL del algoritmo:")
    segmenter = VerseSegmenter()
    first_block = blocks[0]
    print(f"   Primer bloque: '{first_block.get('text', '')}'")
    print(f"   is_heading: {first_block.get('is_heading', False)}")
    print(f"   is_bold: {first_block.get('is_bold', False)}")
    print(f"   is_centered: {first_block.get('is_centered', False)}")
    print(f"   Longitud: {len(first_block.get('text', ''))}")
    
    # Probar manualmente si es título principal
    is_title = segmenter._is_main_title(first_block, 0, blocks)
    print(f"   ¿Es título principal? {is_title}")
    
    # Mostrar algunos bloques siguientes para verificar la estructura
    print(f"\n🔧 Bloques siguientes (para verificar condiciones 2 y 3):")
    for i in range(1, min(15, len(blocks))):
        text = blocks[i].get('text', '').strip()
        if text:
            print(f"   {i}: '{text[:40]}...' (len: {len(text)})")
        else:
            print(f"   {i}: [VACÍO]")
    
    # 🔧 DEBUG ESPECÍFICO: Investigar por qué "El Loco" falla
    print(f"\n🔧 INVESTIGANDO 'El Loco':")
    for i, block in enumerate(blocks):
        text = block.get('text', '').strip()
        if '"El Loco"' in text:
            print(f"   Encontrado 'El Loco' en bloque {i}: '{text}'")
            print(f"   is_heading: {block.get('is_heading', False)}")
            
            # Mostrar bloques siguientes para ver la estructura
            print(f"   Bloques siguientes:")
            for j in range(i+1, min(i+15, len(blocks))):
                next_text = blocks[j].get('text', '').strip()
                if next_text:
                    print(f"      {j}: '{next_text[:40]}...' (len: {len(next_text)})")
                else:
                    print(f"      {j}: [VACÍO]")
            
            # Test manual de _is_main_title para "El Loco"
            is_title = segmenter._is_main_title(block, i, blocks)
            print(f"   ¿Es título principal? {is_title}")
            break
    
    # 2. Segmentar con algoritmo ORIGINAL (conservador)
    poems = segmenter.segment(blocks)
    
    print(f"\n🎭 RESULTADOS - Algoritmo Original:")
    print(f"   📝 Poemas detectados: {len(poems)}")
    
    # 3. Mostrar títulos detectados
    print(f"\n📋 Lista de poemas:")
    for i, poem in enumerate(poems, 1):
        title = poem.get('title', 'Sin título')
        text_preview = poem.get('text', '')[:50].replace('\n', ' ')
        print(f"   {i}. '{title}' - {text_preview}...")
    
    # 4. Verificar que detecta exactamente 5 (como funcionaba antes)
    expected_count = 5
    if len(poems) == expected_count:
        print(f"\n✅ ÉXITO: Detectados {len(poems)} poemas (esperado: {expected_count})")
        print("✅ El algoritmo original funciona correctamente")
    else:
        print(f"\n❌ ERROR: Detectados {len(poems)} poemas (esperado: {expected_count})")
        if len(poems) > expected_count:
            print("❌ SOBRE-DETECCIÓN: Detecta más poemas de los reales")
        else:
            print("❌ SUB-DETECCIÓN: No detecta todos los poemas")
    
    return len(poems) == expected_count

if __name__ == "__main__":
    print("=" * 60)
    print("TEST: VerseSegmenter - Algoritmo Original Conservador")
    print("=" * 60)
    
    success = test_algoritmo_original()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASADO: El algoritmo original funciona correctamente")
    else:
        print("💥 TEST FALLIDO: El algoritmo necesita ajustes")
    print("=" * 60) 