#!/usr/bin/env python3
"""Script de prueba para los nuevos perfiles JSON."""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.profile_manager import ProfileManager

def test_json_profiles():
    """Prueba los nuevos perfiles JSON."""
    
    # Inicializar ProfileManager
    manager = ProfileManager()
    
    print("=== PERFILES DISPONIBLES ===")
    profiles = manager.list_profiles()
    for profile in profiles:
        print(f"- {profile['name']}: {profile['description']}")
        if 'json' in profile['name']:
            print(f"  Segmentador: {profile['segmenter']}")
    
    print("\n=== PROBANDO PERFIL: json_poems_published ===")
    
    # Probar con el archivo de ejemplo
    try:
        result = manager.process_file(
            file_path='test_json_example.json',
            profile_name='json_poems_published',
            encoding='utf-8'
        )
        
        segments, stats, metadata = result
        
        print(f"Segmentos procesados: {len(segments)}")
        print(f"Metadatos del documento: {metadata.get('source_file_path', 'N/A')}")
        print(f"Estadísticas: {stats}")
        
        if segments:
            print("\n=== PRIMEROS 2 SEGMENTOS ===")
            for i, segment in enumerate(segments[:2]):
                print(f"\n--- Segmento {i+1} ---")
                # Los segmentos son objetos ProcessedContentItem
                print(f"Texto: {segment.texto_segmento[:100]}...")
                print(f"Tipo: {segment.tipo_segmento}")
                print(f"ID: {segment.id_segmento}")
                print(f"Idioma: {segment.idioma_documento}")
                print(f"Autor: {segment.autor_documento}")
                print(f"Jerarquía: {segment.jerarquia_contextual}")
        
    except Exception as e:
        print(f"Error al procesar con perfil json_poems_published: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== PROBANDO PERFIL: json_literature_spanish ===")
    
    try:
        result = manager.process_file(
            file_path='test_json_example.json',
            profile_name='json_literature_spanish',
            encoding='utf-8'
        )
        
        segments, stats, metadata = result
        
        print(f"Segmentos procesados: {len(segments)}")
        print(f"Metadatos del documento: {metadata.get('source_file_path', 'N/A')}")
        
        if segments:
            print("\n=== PRIMEROS 2 SEGMENTOS ===")
            for i, segment in enumerate(segments[:2]):
                print(f"\n--- Segmento {i+1} ---")
                # Los segmentos son objetos ProcessedContentItem
                print(f"Texto: {segment.texto_segmento[:100]}...")
                print(f"Tipo: {segment.tipo_segmento}")
                print(f"ID: {segment.id_segmento}")
                print(f"Idioma: {segment.idioma_documento}")
                print(f"Autor: {segment.autor_documento}")
                print(f"Jerarquía: {segment.jerarquia_contextual}")
        
    except Exception as e:
        print(f"Error al procesar con perfil json_literature_spanish: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_profiles() 