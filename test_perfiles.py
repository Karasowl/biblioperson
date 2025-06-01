#!/usr/bin/env python3
"""
Test para verificar perfiles cargados
"""

import sys
sys.path.append('.')

from dataset.processing.profile_manager import ProfileManager

def test_perfiles():
    print("🔍 Verificando perfiles cargados...")
    
    try:
        pm = ProfileManager()
        profiles_list = pm.list_profiles()
        
        print(f"\n📋 Total perfiles encontrados: {len(profiles_list)}")
        
        for profile_info in profiles_list:
            name = profile_info.get('name', 'Sin nombre')
            description = profile_info.get('description', 'Sin descripción')
            category = profile_info.get('category', 'unknown')
            print(f"  ✅ {name} ({category}): {description}")
        
        # Verificar específicamente verso
        verso_profiles = [p for p in profiles_list if p.get('name') == 'verso']
        if verso_profiles:
            verso = verso_profiles[0]
            print(f"\n🎭 Perfil VERSO encontrado:")
            print(f"   Descripción: {verso.get('description')}")
            print(f"   Categoría: {verso.get('category')}")
            
            # Obtener detalles completos del perfil
            verso_detail = pm.get_profile('verso')
            if verso_detail:
                print(f"   Segmentador: {verso_detail.get('segmenter')}")
        else:
            print(f"\n❌ Perfil VERSO NO encontrado en la lista")
            
    except Exception as e:
        print(f"❌ Error cargando ProfileManager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_perfiles() 