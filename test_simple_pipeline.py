#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple para probar el pipeline completo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.segmenters.markdown_segmenter import MarkdownSegmenter
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_header_detection():
    """Test específico para verificar detección de encabezados"""
    
    print("🧪 === TEST DE DETECCIÓN DE ENCABEZADOS ===")
    
    # Crear instancia del segmentador
    segmenter = MarkdownSegmenter()
    
    # Textos de prueba basados en el markdown real
    test_texts = [
        "**RADIO EXTERIOR DE ESPAÑA. MIÉRCOLES 13 MARZO**",
        "### **La Luna**",
        "#### **Salgo de noche porque soy mayor de edad.**",
        "**En cualquier lugar del espacio**",
        "Mi profesor de Periodismo Investigativo me dijo una vez",
        "Miguel es condenado a cinco años de privación de libertad",
        "# **El Ultimo Planeta en Pie**",
        "## **Por** **Grafitti**"
    ]
    
    print("🔍 Probando detección de títulos/encabezados:")
    for i, text in enumerate(test_texts, 1):
        is_header = segmenter._is_title_or_header(text)
        status = "✅ SÍ" if is_header else "❌ NO"
        print(f"   {i}. {status} - {text[:50]}...")
    
    print("\n🔍 Probando fusión conservadora:")
    
    # Simular bloques como los que genera el MarkdownPDFLoader
    test_blocks = [
        {"text": "Mi profesor de Periodismo Investigativo me dijo una vez: El cubano es como el sol"},
        {"text": "**RADIO EXTERIOR DE ESPAÑA. MIÉRCOLES 13 MARZO**"},
        {"text": "Miguel es condenado a cinco años de privación de libertad en Cien Aldabós"}
    ]
    
    for i in range(len(test_blocks) - 1):
        block1 = test_blocks[i]
        block2 = test_blocks[i + 1]
        should_merge = segmenter._should_merge_conservative(block1, block2)
        status = "🔗 FUSIONAR" if should_merge else "✂️ SEPARAR"
        print(f"   {status}: '{block1['text'][:30]}...' + '{block2['text'][:30]}...'")

def test_header_detection_detailed():
    """Test detallado de detección de encabezados en bloques reales"""
    
    print("🧪 === TEST DETALLADO DE DETECCIÓN DE ENCABEZADOS ===")
    
    # Crear instancia del segmentador
    segmenter = MarkdownSegmenter()
    
    # Simular bloques como los que genera el CommonBlockPreprocessor
    test_blocks = [
        {"text": "**El Ultimo Planeta en Pie**"},
        {"text": "**Por** **Grafitti**"},
        {"text": "#### **Salgo de noche porque soy mayor de edad.**"},
        {"text": "### **La Luna**"},
        {"text": "**En cualquier lugar del espacio**"},
        {"text": "Mi profesor de Periodismo Investigativo me dijo una vez: El cubano es como el sol"},
        {"text": "**RADIO EXTERIOR DE ESPAÑA. MIÉRCOLES 13 MARZO**"},
        {"text": "Miguel es condenado a cinco años de privación de libertad en Cien Aldabós"}
    ]
    
    print("🔍 Probando detección individual de encabezados:")
    for i, block in enumerate(test_blocks, 1):
        text = block['text']
        is_header = segmenter._is_title_or_header(text)
        status = "✅ ENCABEZADO" if is_header else "❌ TEXTO NORMAL"
        print(f"   {i}. {status}: '{text}'")
    
    print("\n🔍 Probando fusión entre bloques consecutivos:")
    for i in range(len(test_blocks) - 1):
        block1 = test_blocks[i]
        block2 = test_blocks[i + 1]
        should_merge = segmenter._should_merge_conservative(block1, block2)
        status = "🔗 FUSIONAR" if should_merge else "✂️ SEPARAR"
        print(f"   {status}: '{block1['text'][:30]}...' + '{block2['text'][:30]}...'")
    
    print("\n🔍 Simulando fusión conservadora completa:")
    merged_blocks = segmenter._conservative_merge(test_blocks)
    print(f"   📊 Resultado: {len(test_blocks)} bloques → {len(merged_blocks)} bloques fusionados")
    
    for i, block in enumerate(merged_blocks, 1):
        text = block.get('text', '')
        print(f"   📄 Bloque fusionado {i}: {len(text)} caracteres")
        print(f"      Inicio: {text[:100]}...")

def test_simple_pipeline():
    """Test básico del pipeline completo"""
    
    try:
        # Archivo de prueba - ruta correcta
        test_file = r"C:\Users\adven\Downloads\Obras literarias-20250531T221115Z-1-001\Obras literarias\Último_planeta_en_pie_TEST.pdf"
        
        if not os.path.exists(test_file):
            print(f"ERROR: Archivo no encontrado: {test_file}")
            return
        
        print(f"Archivo encontrado: {test_file}")
        
        # Configurar ProfileManager
        print("Configurando ProfileManager...")
        profile_manager = ProfileManager()
        
        # Procesar archivo (usando modo generic para evitar deduplicación)
        print("Procesando archivo...")
        segments, stats, metadata = profile_manager.process_file(
            test_file,
            profile_name="prosa",  # Especificar perfil
            output_format="generic",  # Usar modo generic para evitar deduplicación
            output_mode="generic"  # IMPORTANTE: Usar modo generic para deshabilitar deduplicación
        )
        
        print(f"EXITO: {len(segments)} segmentos generados")
        
        if segments:
            # Analizar longitudes
            lengths = [len(seg.text if hasattr(seg, 'text') else str(seg)) for seg in segments]
            avg_length = sum(lengths) / len(lengths)
            
            print(f"Longitud promedio: {avg_length:.0f} caracteres")
            print(f"Rango: {min(lengths)} - {max(lengths)} caracteres")
            
            # Distribución por tamaño
            short = sum(1 for l in lengths if l < 100)
            medium = sum(1 for l in lengths if 100 <= l < 300)
            long_segs = sum(1 for l in lengths if l >= 300)
            
            print("Distribucion:")
            print(f"   - Cortos (<100 chars): {short}")
            print(f"   - Medianos (100-300 chars): {medium}")
            print(f"   - Largos (>=300 chars): {long_segs}")
            
            # Buscar el texto problemático específico
            print("Buscando texto problematico...")
            target_text = "Mi profesor de Periodismo Investigativo"
            found_segments = []
            
            for i, segment in enumerate(segments):
                text = segment.text if hasattr(segment, 'text') else str(segment)
                if target_text in text:
                    found_segments.append((i, segment))
            
            if found_segments:
                print(f"ENCONTRADO: Texto problematico en {len(found_segments)} segmento(s)")
                for i, (seg_idx, segment) in enumerate(found_segments):
                    text = segment.text if hasattr(segment, 'text') else str(segment)
                    print(f"Segmento {seg_idx + 1}:")
                    print(f"   ID: {segment.get('segment_id', 'N/A')}")
                    print(f"   Longitud: {len(text)} caracteres")
                    print(f"   Texto (primeros 200 chars): {text[:200]}...")
                    
                    # Verificar si contiene los elementos problemáticos
                    has_intro = "continuación le ofrecemos el cuento ganador" in text
                    has_title = "¡SAQUÉNME DE AQUÍ!" in text
                    has_dialogue = "Buenas tardes" in text
                    
                    print(f"   Contiene introduccion: {'SI' if has_intro else 'NO'}")
                    print(f"   Contiene titulo: {'SI' if has_title else 'NO'}")
                    print(f"   Contiene dialogo: {'SI' if has_dialogue else 'NO'}")
                    
                    if has_intro and has_title and has_dialogue:
                        print(f"   ❌ PROBLEMA: Segmento contiene elementos que deberían estar separados")
                    else:
                        print(f"   ✅ BIEN: Segmento correctamente separado")
            else:
                print("NO ENCONTRADO: Texto problematico no encontrado")
        
        # Mostrar metadatos
        print("Metadatos del resultado:")
        print(f"   - Loader usado: {metadata.get('loader_used', 'N/A')}")
        print(f"   - Segmentador usado: {metadata.get('segmenter_used', 'N/A')}")
        print(f"   - Tiempo de procesamiento: {metadata.get('processing_time', 'N/A')}")
        
        print("RESUMEN FINAL:")
        print(f"   - Segmentos generados: {len(segments)}")
        if segments:
            avg_length = sum(len(seg.text if hasattr(seg, 'text') else str(seg)) for seg in segments) / len(segments)
            print(f"   - Longitud promedio: {avg_length:.0f} caracteres")
        print(f"   - Loader: {metadata.get('loader_used', 'N/A')}")
        print(f"   - Segmentador: {metadata.get('segmenter_used', 'N/A')}")
        print(f"   - Pipeline funcionando correctamente")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_subdivision_logic():
    """Test específico para la lógica de subdivisión"""
    
    print("🧪 === TEST DE SUBDIVISIÓN INTELIGENTE ===")
    
    # Configurar ProfileManager
    profile_manager = ProfileManager()
    
    # Archivo de prueba - NUEVO archivo para evitar deduplicación
    test_file = r"C:\Users\adven\Downloads\test_segmentation_NEW.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"📄 Procesando: {test_file}")
    
    try:
        # Procesar con modo generic para evitar deduplicación
        segments, stats, metadata = profile_manager.process_file(
            test_file,
            profile_name="prosa",  # Especificar perfil
            output_format="generic",
            output_mode="generic"
        )
        
        print(f"\n📊 === RESULTADOS ===")
        print(f"📋 Total de segmentos: {len(segments)}")
        
        if not segments:
            print("❌ No se generaron segmentos")
        else:
            # Analizar cada segmento
            for i, segment in enumerate(segments, 1):
                text = segment.text if hasattr(segment, 'text') else str(segment)
                print(f"\n📄 Segmento {i}:")
                print(f"   📏 Longitud: {len(text)} caracteres")
                print(f"   🔤 Inicio: {text[:100]}...")
                
                # Buscar indicadores de problemas
                if len(text) > 3000:
                    print(f"   ⚠️ LARGO: Segmento muy largo ({len(text)} chars)")
                    
                    # Buscar encabezados dentro del segmento
                    lines = text.split('\n')
                    headers_found = []
                    for line_num, line in enumerate(lines):
                        line_stripped = line.strip()
                        if ('**' in line_stripped and len(line_stripped) < 100) or line_stripped.startswith('#'):
                            headers_found.append((line_num, line_stripped))
                    
                    if headers_found:
                        print(f"   🔍 Encabezados encontrados dentro del segmento:")
                        for line_num, header in headers_found[:5]:  # Mostrar solo los primeros 5
                            print(f"      Línea {line_num}: {header}")
                        if len(headers_found) > 5:
                            print(f"      ... y {len(headers_found) - 5} más")
        
        print(f"\n🎯 === RESUMEN ===")
        if len(segments) == 1 and len(segments[0].text if hasattr(segments[0], 'text') else str(segments[0])) > 10000:
            print("❌ TEST FALLIDO: Un solo segmento muy largo")
        elif len(segments) > 5:
            print("✅ TEST EXITOSO: Múltiples segmentos generados")
        else:
            print("⚠️ TEST PARCIAL: Pocos segmentos generados")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_header_detection()
    print("\n" + "="*60 + "\n")
    test_header_detection_detailed()
    print("\n" + "="*60 + "\n")
    test_subdivision_logic() 