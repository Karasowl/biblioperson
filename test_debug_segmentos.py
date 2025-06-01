#!/usr/bin/env python3
"""
Test de DEBUG para ver exactamente qué devuelve el VerseSegmenter
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.docx_loader import DocxLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from pathlib import Path
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.ERROR)  # Solo errores

def debug_segmentos():
    print("🔍 DEBUG: ¿Qué devuelve exactamente el VerseSegmenter?")
    
    # Ruta del archivo DOCX
    archivo_docx = Path("C:/Users/adven/OneDrive/Escritorio/probando biblioperson/Recopilación de Escritos Propios/biblioteca_personal/raw/poesías/Mis Poemas.docx")
    
    if not archivo_docx.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_docx}")
        return
    
    print(f"\n📄 ARCHIVO: {archivo_docx.name}")
    
    # PASO 1: CARGAR DOCX
    print(f"\n1️⃣ CARGAR DOCX")
    try:
        loader = DocxLoader(str(archivo_docx))
        loaded_data = loader.load()
        raw_blocks = loaded_data.get('blocks', [])
        print(f"   ✅ Bloques cargados: {len(raw_blocks)}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return
    
    # PASO 2: PREPROCESSAR
    print(f"\n2️⃣ PREPROCESSAR")
    try:
        preprocessor = CommonBlockPreprocessor()
        processed_blocks, processed_metadata = preprocessor.process(raw_blocks, {})
        print(f"   ✅ Bloques procesados: {len(processed_blocks)}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return
    
    # PASO 3: SEGMENTAR Y ANALIZAR
    print(f"\n3️⃣ SEGMENTAR Y ANALIZAR SALIDA")
    try:
        segmenter = VerseSegmenter({})
        segments = segmenter.segment(processed_blocks)
        print(f"   ✅ Segmentos generados: {len(segments)}")
        
        # ANÁLISIS DETALLADO DE LOS PRIMEROS 3 SEGMENTOS
        print(f"\n   🔍 ANÁLISIS DETALLADO (primeros 3 segmentos):")
        for i, segment in enumerate(segments[:3]):
            print(f"\n      📋 SEGMENTO [{i+1}]:")
            print(f"      ├─ Tipo: {type(segment)}")
            
            if isinstance(segment, dict):
                print(f"      ├─ Keys: {list(segment.keys())}")
                
                # Verificar claves específicas
                for key in ['type', 'title', 'text', 'content']:
                    value = segment.get(key)
                    if value:
                        preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        print(f"      ├─ {key}: '{preview}'")
                    else:
                        print(f"      ├─ {key}: [AUSENTE/VACÍO]")
                
                # Mostrar TODAS las claves y sus valores
                print(f"      └─ CONTENIDO COMPLETO:")
                for key, value in segment.items():
                    preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    print(f"          {key}: {preview}")
            else:
                print(f"      └─ Contenido: {str(segment)[:100]}...")
        
        # ANÁLISIS GENERAL
        print(f"\n   📊 ANÁLISIS GENERAL:")
        
        # Verificar tipos de segmentos
        tipos_encontrados = {}
        titulos_encontrados = []
        
        for segment in segments:
            if isinstance(segment, dict):
                tipo = segment.get('type', 'TIPO_AUSENTE')
                tipos_encontrados[tipo] = tipos_encontrados.get(tipo, 0) + 1
                
                titulo = segment.get('title', '')
                if titulo:
                    titulos_encontrados.append(titulo)
        
        print(f"      📋 Tipos de segmento encontrados:")
        for tipo, count in tipos_encontrados.items():
            print(f"          {tipo}: {count} segmentos")
        
        print(f"      📋 Títulos encontrados ({len(titulos_encontrados)}):")
        for i, titulo in enumerate(titulos_encontrados[:10]):
            print(f"          [{i+1}] '{titulo}'")
        
        # VERIFICAR FORMATO EXACTO ESPERADO POR PROFILEMANAGER
        print(f"\n   🎯 VERIFICACIÓN PARA PROFILEMANAGER:")
        tipo_esperado = "poem"
        segmentos_con_tipo_correcto = 0
        segmentos_con_titulo = 0
        
        for segment in segments:
            if isinstance(segment, dict):
                if segment.get('type') == tipo_esperado:
                    segmentos_con_tipo_correcto += 1
                if segment.get('title'):
                    segmentos_con_titulo += 1
        
        print(f"      ├─ Segmentos con type='{tipo_esperado}': {segmentos_con_tipo_correcto}")
        print(f"      ├─ Segmentos con título: {segmentos_con_titulo}")
        print(f"      └─ ¿Problema identificado?: {segmentos_con_tipo_correcto != len(segments) or segmentos_con_titulo == 0}")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # RESUMEN Y DIAGNÓSTICO
    print(f"\n🏁 DIAGNÓSTICO:")
    print(f"   📦 Bloques originales: {len(raw_blocks)}")
    print(f"   🔧 Bloques procesados: {len(processed_blocks)}")
    print(f"   🎭 Segmentos detectados: {len(segments)}")
    
    if segmentos_con_titulo > 0 and segmentos_con_tipo_correcto == len(segments):
        print(f"   ✅ VerseSegmenter funciona correctamente")
        print(f"   💡 ProfileManager debería procesar títulos sin problemas")
    elif segmentos_con_titulo == 0:
        print(f"   ❌ PROBLEMA: VerseSegmenter no está generando títulos")
        print(f"   🔧 Revisar método de generación de títulos en VerseSegmenter")
    elif segmentos_con_tipo_correcto != len(segments):
        print(f"   ❌ PROBLEMA: Tipo de segmento incorrecto")
        print(f"   🔧 ProfileManager espera type='poem', revisar VerseSegmenter")
    else:
        print(f"   ⚠️  PROBLEMA MIXTO: Revisar ambos componentes")

if __name__ == "__main__":
    debug_segmentos() 