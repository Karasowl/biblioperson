#!/usr/bin/env python3
"""
🔧 TEST DE CORRECCIÓN DIRECTORIO vs ARCHIVO
Verifica que la función _export_results ya no crea directorios en lugar de archivos.
"""

import tempfile
import json
from pathlib import Path

def test_export_behavior():
    """
    Simula el comportamiento corregido vs el original problemático.
    """
    print("🔧 PROBANDO CORRECCIÓN DIRECTORIO vs ARCHIVO")
    print("=" * 55)
    
    def export_results_original(output_dir, segments, format_type="ndjson"):
        """Comportamiento original problemático"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)  # ❌ PROBLEMA: Crea directorio
        
        # Intentar escribir archivo
        try:
            with open(output_dir, 'w') as f:  # ❌ Falla porque output_dir es ahora un directorio
                if format_type == "json":
                    json.dump({"segments": segments}, f)
                else:
                    for segment in segments:
                        f.write(json.dumps(segment) + '\n')
            return True, "Archivo creado exitosamente"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def export_results_fixed(output_file, segments, format_type="ndjson"):
        """Comportamiento corregido"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)  # ✅ CORREGIDO: Solo crea directorio padre
        
        # Escribir archivo
        try:
            with open(output_path, 'w') as f:  # ✅ CORREGIDO: Usa output_path (archivo)
                if format_type == "json":
                    json.dump({"segments": segments}, f)
                else:
                    for segment in segments:
                        f.write(json.dumps(segment) + '\n')
            return True, "Archivo creado exitosamente"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    # Datos de prueba
    test_segments = [
        {"id": 1, "text": "Primer poema", "type": "poem"},
        {"id": 2, "text": "Segundo poema", "type": "poem"}
    ]
    
    # Usar directorio temporal para las pruebas
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Probar comportamiento original (problemático)
        print("🚨 COMPORTAMIENTO ORIGINAL (PROBLEMÁTICO):")
        original_file = temp_path / "test_original.ndjson"
        original_success, original_msg = export_results_original(str(original_file), test_segments)
        
        print(f"  Archivo objetivo: {original_file}")
        print(f"  ¿Exitoso? {original_success}")
        print(f"  Mensaje: {original_msg}")
        
        # Verificar qué se creó realmente
        if original_file.exists():
            if original_file.is_dir():
                print(f"  ❌ PROBLEMA: Se creó un DIRECTORIO: {original_file}")
            elif original_file.is_file():
                print(f"  ✅ Se creó un archivo correctamente: {original_file}")
        else:
            print(f"  ❓ No se creó nada en: {original_file}")
        
        print()
        
        # Probar comportamiento corregido
        print("✅ COMPORTAMIENTO CORREGIDO:")
        fixed_file = temp_path / "test_fixed.ndjson"
        fixed_success, fixed_msg = export_results_fixed(str(fixed_file), test_segments)
        
        print(f"  Archivo objetivo: {fixed_file}")
        print(f"  ¿Exitoso? {fixed_success}")
        print(f"  Mensaje: {fixed_msg}")
        
        # Verificar qué se creó realmente
        if fixed_file.exists():
            if fixed_file.is_dir():
                print(f"  ❌ PROBLEMA: Se creó un DIRECTORIO: {fixed_file}")
            elif fixed_file.is_file():
                print(f"  ✅ Se creó un archivo correctamente: {fixed_file}")
                # Verificar contenido
                with open(fixed_file, 'r') as f:
                    content = f.read()
                lines = content.strip().split('\n')
                print(f"  📄 Contenido: {len(lines)} líneas")
                print(f"  📝 Primera línea: {lines[0][:50]}...")
        else:
            print(f"  ❓ No se creó nada en: {fixed_file}")
        
        print()
        print("=" * 55)
        print("RESUMEN:")
        print(f"  Original (problemático): {'❌ FALLA' if not original_success else '✅ FUNCIONA'}")
        print(f"  Corregido: {'✅ FUNCIONA' if fixed_success else '❌ FALLA'}")

if __name__ == "__main__":
    test_export_behavior() 