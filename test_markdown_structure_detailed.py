#!/usr/bin/env python3
"""
Script detallado para analizar la estructura exacta que genera MarkdownPDFLoader
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.loaders.markdown_pdf_loader import MarkdownPDFLoader
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_markdown_structure_detailed():
    """Analizar la estructura detallada del Markdown generado"""
    
    # Archivo de prueba
    test_file = r"C:\Users\adven\Downloads\Obras literarias-20250531T221115Z-1-001\Obras literarias\Último_planeta_en_pie.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🔄 Procesando: {test_file}")
    
    # Crear loader con file_path
    loader = MarkdownPDFLoader(test_file)
    
    # Cargar y procesar
    result = loader.load()
    
    print(f"\n📊 Resultados del MarkdownPDFLoader:")
    print(f"   - Tipo de result: {type(result)}")
    print(f"   - Claves en result: {list(result.keys()) if isinstance(result, dict) else 'No es dict'}")
    
    if isinstance(result, dict) and 'blocks' in result:
        blocks = result['blocks']
        print(f"   - Tipo de blocks: {type(blocks)}")
        print(f"   - Longitud de blocks: {len(blocks) if hasattr(blocks, '__len__') else 'No tiene len'}")
        
        # Si blocks es una lista
        if isinstance(blocks, list):
            print(f"   - blocks es una lista con {len(blocks)} elementos")
            
            # Analizar los primeros elementos
            for i in range(min(3, len(blocks))):
                block = blocks[i]
                print(f"\n🔍 BLOQUE {i+1}:")
                print(f"   - Tipo: {type(block)}")
                
                if isinstance(block, dict):
                    print(f"   - Claves: {list(block.keys())}")
                    text = block.get('text', '')
                    print(f"   - Longitud texto: {len(text)}")
                    print(f"   - Primeras 100 chars: {repr(text[:100])}")
                    
                    # Analizar metadata
                    metadata = block.get('metadata', {})
                    if metadata:
                        print(f"   - Metadata: {metadata}")
                else:
                    print(f"   - Contenido: {repr(str(block)[:100])}")
        
        # Si blocks es string (JSON serializado)
        elif isinstance(blocks, str):
            print(f"   - blocks es un string (JSON serializado)")
            print(f"   - Primeras 200 chars: {repr(blocks[:200])}")
            
            # Intentar parsear como JSON
            try:
                parsed_blocks = json.loads(blocks)
                print(f"   - JSON parseado exitosamente")
                print(f"   - Tipo después de parsear: {type(parsed_blocks)}")
                print(f"   - Longitud después de parsear: {len(parsed_blocks) if hasattr(parsed_blocks, '__len__') else 'No tiene len'}")
                
                if isinstance(parsed_blocks, list) and len(parsed_blocks) > 0:
                    first_block = parsed_blocks[0]
                    print(f"   - Primer bloque parseado: {type(first_block)}")
                    if isinstance(first_block, dict):
                        print(f"   - Claves primer bloque: {list(first_block.keys())}")
                        text = first_block.get('text', '')
                        print(f"   - Texto primer bloque: {repr(text[:100])}")
                        
            except json.JSONDecodeError as e:
                print(f"   - Error parseando JSON: {e}")
        
        else:
            print(f"   - blocks es de tipo inesperado: {type(blocks)}")
    
    # Buscar el texto problemático
    target_text = "Mi profesor de Periodismo Investigativo"
    print(f"\n🎯 Buscando texto problemático: '{target_text}'")
    
    # Función recursiva para buscar en cualquier estructura
    def search_in_structure(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                search_in_structure(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_in_structure(item, f"{path}[{i}]")
        elif isinstance(obj, str) and target_text in obj:
            print(f"   - Encontrado en: {path}")
            print(f"   - Contexto: {repr(obj[max(0, obj.find(target_text)-50):obj.find(target_text)+150])}")
    
    search_in_structure(result)

if __name__ == "__main__":
    analyze_markdown_structure_detailed() 