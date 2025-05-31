#!/usr/bin/env python3
"""Script de prueba para el JSONLoader."""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.loaders.json_loader import JSONLoader

def test_json_loader():
    """Prueba el JSONLoader con diferentes configuraciones."""
    
    # Configuración básica
    config1 = {
        'text_property_paths': ['content', 'title'],
        'filter_rules': [
            {'field': 'type', 'operator': 'eq', 'value': 'poem'},
            {'field': 'status', 'operator': 'eq', 'value': 'published'}
        ],
        'root_array_path': 'data',
        'pointer_path': 'id',
        'date_path': 'date'
    }
    
    print("=== PRUEBA 1: Filtrar solo poemas publicados ===")
    loader1 = JSONLoader(Path('test_json_example.json'), **config1)
    
    try:
        data1 = loader1.load()
        blocks1 = data1['blocks']
        print(f"Bloques encontrados: {len(blocks1)}")
        
        for i, block in enumerate(blocks1):
            print(f"\n--- Bloque {i+1} ---")
            print(f"Texto: {block['text'][:100]}...")
            print(f"Fecha: {block.get('detected_date', 'N/A')}")
            print(f"Metadata: {block['metadata']}")
            
    except Exception as e:
        print(f"Error en prueba 1: {e}")
    
    # Configuración sin filtros
    config2 = {
        'text_property_paths': ['content'],
        'filter_rules': [],
        'root_array_path': 'data',
        'pointer_path': 'id',
        'date_path': 'date'
    }
    
    print("\n\n=== PRUEBA 2: Sin filtros, todos los elementos ===")
    loader2 = JSONLoader(Path('test_json_example.json'), **config2)
    
    try:
        data2 = loader2.load()
        blocks2 = data2['blocks']
        print(f"Bloques encontrados: {len(blocks2)}")
        
        for i, block in enumerate(blocks2):
            print(f"\n--- Bloque {i+1} ---")
            print(f"Texto: {block['text'][:50]}...")
            print(f"Metadata pointer: {block['metadata'].get('pointer')}")
            
    except Exception as e:
        print(f"Error en prueba 2: {e}")
    
    # Configuración con filtro de idioma
    config3 = {
        'text_property_paths': ['content', 'title'],
        'filter_rules': [
            {'field': 'metadata.language', 'operator': 'eq', 'value': 'es'}
        ],
        'root_array_path': 'data',
        'pointer_path': 'id',
        'date_path': 'date'
    }
    
    print("\n\n=== PRUEBA 3: Filtrar solo contenido en español ===")
    loader3 = JSONLoader(Path('test_json_example.json'), **config3)
    
    try:
        data3 = loader3.load()
        blocks3 = data3['blocks']
        print(f"Bloques encontrados: {len(blocks3)}")
        
        for i, block in enumerate(blocks3):
            print(f"\n--- Bloque {i+1} ---")
            print(f"Texto: {block['text'][:80]}...")
            print(f"Pointer: {block['metadata'].get('pointer')}")
            
    except Exception as e:
        print(f"Error en prueba 3: {e}")

if __name__ == "__main__":
    test_json_loader() 