#!/usr/bin/env python3
"""
Análisis: Manual vs Automático - ¿Por qué falla la segmentación?

Investiga por qué la selección manual del PDF funciona bien
pero nuestro algoritmo automático solo detecta 75% de los poemas.
"""

import sys
from pathlib import Path
import fitz
import re

# Agregar la ruta del dataset al path
sys.path.append(str(Path(__file__).parent / "dataset"))

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def analyze_manual_vs_automatic():
    """Compara extracción manual vs automática del PDF Neruda"""
    
    pdf_path = r"C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return
        
    print("🔍 ANÁLISIS: MANUAL vs AUTOMÁTICO")
    print("=" * 60)
    
    # 1. ANÁLISIS MANUAL DEL PDF
    print("📋 PASO 1: ANÁLISIS MANUAL")
    print("-" * 30)
    
    try:
        doc = fitz.open(pdf_path)
        print(f"📄 Páginas totales: {len(doc)}")
        
        # Extraer todo el texto página por página
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            all_text += page_text + "\n\n"
            
            # Mostrar muestra de cada página
            lines = page_text.split('\n')
            significant_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 3]
            
            print(f"   Página {page_num + 1}: {len(significant_lines)} líneas significativas")
            if significant_lines:
                print(f"      Primera: '{significant_lines[0][:60]}...'")
                if len(significant_lines) > 1:
                    print(f"      Última: '{significant_lines[-1][:60]}...'")
        
        doc.close()
        
        # Detectar patrones de poemas manualmente
        manual_poem_patterns = [
            r'^(Poema|POEMA)\s+\d+',  # "Poema 1", "POEMA 2"
            r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)\.?\s*$',  # Números romanos
            r'^\d+\.?\s*$',  # Números arábigos solos
            r'^[A-Z][A-Z\s]{10,50}$',  # Títulos largos en mayúsculas
            r'.*[Cc]anción.*',  # Títulos con "canción"
        ]
        
        manual_titles = []
        for line in all_text.split('\n'):
            line = line.strip()
            if line:
                for pattern in manual_poem_patterns:
                    if re.match(pattern, line):
                        manual_titles.append(line)
                        break
        
        print(f"\n🎯 DETECCIÓN MANUAL:")
        print(f"   Títulos detectados: {len(manual_titles)}")
        for i, title in enumerate(manual_titles[:10], 1):  # Mostrar primeros 10
            print(f"      {i}. {title}")
        if len(manual_titles) > 10:
            print(f"      ... y {len(manual_titles) - 10} más")
        
    except Exception as e:
        print(f"❌ Error en análisis manual: {e}")
        return
    
    # 2. ANÁLISIS AUTOMÁTICO
    print(f"\n📋 PASO 2: ANÁLISIS AUTOMÁTICO")
    print("-" * 30)
    
    try:
        # Usar nuestro PDFLoader
        loader = PDFLoader(pdf_path)
        result = loader.load()
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        
        print(f"📦 Bloques extraídos: {len(blocks)}")
        print(f"📊 Caracteres totales: {metadata.get('char_count', 0)}")
        print(f"🔧 Método extracción: {result.get('source_info', {}).get('extraction_method', 'unknown')}")
        
        # Mostrar muestra de bloques
        print(f"\n📋 MUESTRA DE BLOQUES:")
        for i, block in enumerate(blocks[:5]):
            text = block.get('text', '')[:100].replace('\n', ' ')
            block_type = block.get('metadata', {}).get('type', 'unknown')
            print(f"   {i+1}. [{block_type}] {text}...")
        
        # Usar VerseSegmenter
        segmenter = VerseSegmenter()
        segments = segmenter.segment(blocks)
        
        print(f"\n🎭 SEGMENTACIÓN AUTOMÁTICA:")
        print(f"   Segmentos detectados: {len(segments)}")
        
        # Mostrar títulos detectados automáticamente
        auto_titles = []
        for segment in segments:
            content = segment.get('content', '').strip()
            first_line = content.split('\n')[0].strip() if content else ''
            if first_line:
                auto_titles.append(first_line)
        
        print(f"   Primeros títulos automáticos:")
        for i, title in enumerate(auto_titles[:10], 1):
            print(f"      {i}. {title[:80]}...")
        
    except Exception as e:
        print(f"❌ Error en análisis automático: {e}")
        return
    
    # 3. COMPARACIÓN Y DIAGNÓSTICO
    print(f"\n📊 PASO 3: COMPARACIÓN Y DIAGNÓSTICO")
    print("-" * 30)
    
    print(f"🎯 RESULTADOS:")
    print(f"   Manual: {len(manual_titles)} títulos")
    print(f"   Automático: {len(segments)} segmentos")
    print(f"   Ratio éxito: {len(segments)/len(manual_titles)*100:.1f}%" if manual_titles else "N/A")
    
    # Diagnóstico de problemas
    print(f"\n🔍 DIAGNÓSTICO POTENCIAL:")
    
    if len(segments) < len(manual_titles):
        gap = len(manual_titles) - len(segments)
        print(f"❌ PROBLEMA: Faltan {gap} segmentos")
        print(f"   Posibles causas:")
        print(f"   • Bloques demasiado grandes (combinan varios poemas)")
        print(f"   • Patrones de títulos no detectados")
        print(f"   • Algoritmo de segmentación demasiado conservador")
    
    if len(blocks) < len(doc) * 3:  # Esperamos al menos 3 bloques por página
        print(f"❌ PROBLEMA: Muy pocos bloques extraídos")
        print(f"   • {len(blocks)} bloques para {len(doc)} páginas")
        print(f"   • Ratio: {len(blocks)/len(doc):.1f} bloques/página (esperado: ≥3)")
        print(f"   • Causa: Extracción de texto combina demasiado contenido")
    
    # Análisis de calidad del texto
    sample_text = ' '.join([block.get('text', '') for block in blocks[:3]])
    corruption_chars = sum(1 for char in sample_text if ord(char) < 32 and char not in '\n\r\t')
    corruption_rate = corruption_chars / len(sample_text) * 100 if sample_text else 0
    
    print(f"📝 CALIDAD DEL TEXTO:")
    print(f"   Corrupción: {corruption_rate:.1f}%")
    if corruption_rate > 5:
        print(f"   ⚠️  Alta corrupción detectada - considerar OCR")
    else:
        print(f"   ✅ Texto limpio - problema en segmentación")
    
    print(f"\n🎯 RECOMENDACIONES:")
    if len(segments) < len(manual_titles):
        print(f"   1. 🔧 Mejorar algoritmo de pre-división de bloques")
        print(f"   2. 🎯 Ampliar patrones de detección de títulos")
        print(f"   3. 📏 Reducir umbrales de segmentación")
    
    if len(blocks) < len(doc) * 2:
        print(f"   4. 📦 Mejorar granularidad de extracción de bloques")
        print(f"   5. 🔄 Usar OCR para mejor granularidad")

if __name__ == "__main__":
    analyze_manual_vs_automatic() 