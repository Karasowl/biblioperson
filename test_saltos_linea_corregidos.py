#!/usr/bin/env python3
"""
TEST SALTOS DE LÍNEA CORREGIDOS
===============================

Verificar que los saltos de línea del Poema 13 
se preservan correctamente después de la corrección.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.profile_manager import ProfileManager
    
    def test_line_breaks_fixed():
        """Verificar saltos de línea del Poema 13"""
        
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            return False
        
        print("🔍 VERIFICANDO SALTOS DE LÍNEA CORREGIDOS")
        print("=" * 50)
        
        # Procesar con el perfil verso corregido
        manager = ProfileManager()
        results = manager.process_file(
            file_path=test_file,
            profile_name='verso',
            language_override='es',
            confidence_threshold=0.3
        )
        
        processed_items, segmenter_stats, document_metadata = results
        
        # Buscar el Poema 13
        poema_13 = None
        for item in processed_items:
            if hasattr(item, 'texto_segmento') and 'Poema 13' in item.texto_segmento:
                poema_13 = item.texto_segmento
                break
        
        if not poema_13:
            print("❌ No se encontró el Poema 13")
            return False
        
        print("🎭 ANÁLISIS DEL POEMA 13:")
        print("-" * 40)
        
        # Contar saltos de línea
        line_count = poema_13.count('\n')
        lines = poema_13.split('\n')
        
        print(f"📊 Estadísticas:")
        print(f"   - Saltos de línea: {line_count}")
        print(f"   - Líneas totales: {len(lines)}")
        print(f"   - Longitud total: {len(poema_13)} caracteres")
        
        print(f"\n📝 Primeras 10 líneas del Poema 13:")
        for i, line in enumerate(lines[:10]):
            print(f"   {i+1:2d}: {repr(line)}")
        
        # Verificar estructura esperada
        expected_structure = [
            'Poema 13',  # Título
            '',          # Línea vacía después del título
            'He ido marcando con cruces de fuego',  # Primera línea del poema
            'el atlas blanco de tu cuerpo.',        # Segunda línea
        ]
        
        print(f"\n✅ VERIFICACIÓN DE ESTRUCTURA:")
        structure_ok = True
        
        for i, expected_line in enumerate(expected_structure):
            if i < len(lines):
                actual_line = lines[i].strip()
                expected_line = expected_line.strip()
                
                if actual_line == expected_line or (expected_line == '' and actual_line == ''):
                    status = "✅"
                else:
                    status = "❌"
                    structure_ok = False
                
                print(f"   {status} Línea {i+1}: {repr(actual_line)}")
                if expected_line:
                    print(f"       Esperado: {repr(expected_line)}")
            else:
                print(f"   ❌ Línea {i+1}: FALTANTE")
                structure_ok = False
        
        # Verificar que no hay exceso de líneas vacías
        consecutive_empty = 0
        max_consecutive_empty = 0
        
        for line in lines:
            if line.strip() == '':
                consecutive_empty += 1
                max_consecutive_empty = max(max_consecutive_empty, consecutive_empty)
            else:
                consecutive_empty = 0
        
        print(f"\n📏 VERIFICACIÓN DE FORMATO:")
        print(f"   - Máximo líneas vacías consecutivas: {max_consecutive_empty}")
        print(f"   - ¿Estructura correcta?: {'✅ SÍ' if structure_ok else '❌ NO'}")
        print(f"   - ¿Formato limpio?: {'✅ SÍ' if max_consecutive_empty <= 2 else '❌ NO'}")
        
        # Mostrar comparación antes/después
        print(f"\n🔄 COMPARACIÓN:")
        print("   ANTES (problema reportado):")
        print("   'Poema 13\\nHe ido marcando con cruces de fuego el atlas blanco...'")
        print("   (Todo en una línea)")
        
        print("\n   DESPUÉS (corregido):")
        preview_lines = lines[:5]
        for line in preview_lines:
            print(f"   '{line}'")
        print("   (Estructura poética preservada)")
        
        # Resultado final
        success = structure_ok and max_consecutive_empty <= 2 and line_count > 5
        
        print(f"\n{'🎉 ¡CORRECCIÓN EXITOSA!' if success else '❌ AÚN HAY PROBLEMAS'}")
        
        if success:
            print("   ✅ Los saltos de línea se preservan correctamente")
            print("   ✅ La estructura poética está intacta")
            print("   ✅ El formato es limpio y legible")
        else:
            print("   ❌ Los saltos de línea aún no se preservan adecuadamente")
            
        return success
    
    if __name__ == "__main__":
        print("🧪 TEST SALTOS DE LÍNEA CORREGIDOS")
        print("=" * 50)
        
        success = test_line_breaks_fixed()
        
        print()
        print("=" * 50)
        if success:
            print("🎉 ¡CORRECCIÓN VERIFICADA! Los saltos de línea funcionan correctamente.")
        else:
            print("❌ CORRECCIÓN INCOMPLETA. Revisar implementación.")
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("⚠️ Asegúrate de ejecutar desde el directorio raíz del proyecto") 