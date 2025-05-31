#!/usr/bin/env python3
"""Script de prueba para los perfiles simplificados."""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.profile_manager import ProfileManager

def test_simplified_profiles():
    """Prueba los nuevos perfiles simplificados."""
    
    # Inicializar ProfileManager
    manager = ProfileManager()
    
    print("=== PERFILES DISPONIBLES (SIMPLIFICADOS) ===")
    profiles = manager.list_profiles()
    
    # Separar por categoría
    core_profiles = []
    special_profiles = []
    other_profiles = []
    
    for profile in profiles:
        profile_data = manager.get_profile(profile['name'])
        category = profile_data.get('_category', 'other')
        
        if category == 'core':
            core_profiles.append(profile)
        elif category == 'special':
            special_profiles.append(profile)
        else:
            other_profiles.append(profile)
    
    print("\n📋 PERFILES CORE (básicos):")
    for profile in core_profiles:
        print(f"  ✅ {profile['name']}: {profile['description']}")
    
    print("\n🔧 PERFILES ESPECIALES:")
    for profile in special_profiles:
        print(f"  ⚙️ {profile['name']}: {profile['description']}")
    
    if other_profiles:
        print("\n📁 OTROS PERFILES (compatibilidad):")
        for profile in other_profiles:
            print(f"  📄 {profile['name']}: {profile['description']}")
    
    print(f"\n📊 RESUMEN: {len(core_profiles)} core, {len(special_profiles)} especiales, {len(other_profiles)} otros")
    
    # Probar perfil JSON simplificado
    print("\n=== PROBANDO PERFIL JSON SIMPLIFICADO ===")
    try:
        result = manager.process_file(
            file_path='test_json_example.json',
            profile_name='json',
            encoding='utf-8'
        )
        
        segments, stats, metadata = result
        print(f"✅ Segmentos procesados: {len(segments)}")
        print(f"✅ Archivo: {metadata.get('source_file_path', 'N/A')}")
        
        if segments:
            segment = segments[0]
            print(f"✅ Primer segmento: {segment.texto_segmento[:50]}...")
            print(f"✅ Tipo: {segment.tipo_segmento}")
            print(f"✅ Idioma: {segment.idioma_documento}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simplified_profiles() 