#!/usr/bin/env python3
"""
Debug del DocxLoader - ver exactamente qué bloques genera
"""

import sys
sys.path.append('.')

from dataset.processing.loaders.docx_loader import DocxLoader
from pathlib import Path

def test_docx_loader():
    print("🔍 DEBUGGING: DocxLoader para archivo de poemas")
    
    # Ruta del archivo del usuario
    archivo_poemas = Path("C:/Users/adven/OneDrive/Escritorio/probando biblioperson/Recopilación de Escritos Propios/biblioteca_personal/raw/poesías/Mis Poemas.docx")
    
    if not archivo_poemas.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_poemas}")
        return
    
    # Cargar archivo con DocxLoader
    loader = DocxLoader(archivo_poemas, tipo='poemas')
    resultado = loader.load()
    
    bloques = resultado.get('blocks', [])
    metadata = resultado.get('document_metadata', {})
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Total bloques generados: {len(bloques)}")
    print(f"   Título documento: {metadata.get('titulo_documento', 'N/A')}")
    
    print(f"\n📝 DETALLE DE BLOQUES:")
    for i, bloque in enumerate(bloques, 1):
        texto = bloque.get('text', '')
        is_heading = bloque.get('is_heading', False)
        is_bold = bloque.get('is_bold', False)
        is_centered = bloque.get('is_centered', False)
        style = bloque.get('style', 'N/A')
        
        print(f"\n[{i:2d}] {'🎭 TÍTULO' if is_heading else '📄 TEXTO'} | Longitud: {len(texto):3d}")
        print(f"     Texto: '{texto[:80]}{'...' if len(texto) > 80 else ''}'")
        print(f"     Propiedades: heading={is_heading}, bold={is_bold}, centered={is_centered}")
        print(f"     Estilo: {style}")
        
        # Detectar posibles títulos de poemas
        if texto.startswith('"') and texto.endswith('"'):
            print(f"     🚨 POSIBLE TÍTULO DE POEMA: {texto}")
        
        # Detectar líneas vacías
        if not texto.strip():
            print(f"     🔲 LÍNEA VACÍA")
    
    # Analizar patrones
    print(f"\n🔍 ANÁLISIS DE PATRONES:")
    titulos_comillas = [b for b in bloques if b.get('text', '').startswith('"') and b.get('text', '').endswith('"')]
    lineas_vacias = [b for b in bloques if not b.get('text', '').strip()]
    
    print(f"   Títulos entre comillas detectados: {len(titulos_comillas)}")
    for titulo in titulos_comillas:
        print(f"      - {titulo.get('text', '')}")
    
    print(f"   Líneas vacías: {len(lineas_vacias)}")
    
    # Verificar si los títulos se detectan como headings
    print(f"\n🎯 DETECCIÓN DE HEADINGS:")
    for titulo in titulos_comillas:
        texto = titulo.get('text', '')
        is_heading = titulo.get('is_heading', False)
        print(f"   {texto} -> {'✅ Detectado como heading' if is_heading else '❌ NO detectado como heading'}")

if __name__ == "__main__":
    test_docx_loader() 