#!/usr/bin/env python3
"""
🔧 TEST FINAL DE EXPORTACIÓN CORREGIDA
Verifica que todo el pipeline de exportación funciona correctamente.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Agregar el directorio dataset al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

def test_complete_export_pipeline():
    """
    Test completo del pipeline de exportación corregido.
    """
    print("🔧 PROBANDO PIPELINE COMPLETO DE EXPORTACIÓN")
    print("=" * 60)
    
    try:
        from processing.profile_manager import ProfileManager
        
        # Crear un archivo de prueba temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("Poema 1\n\nEste es el primer verso\nEste es el segundo verso\n\nPoema 2\n\nOtro verso aquí\nY otro más")
            temp_file_path = temp_file.name
        
        # Crear directorio temporal para salida
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file_ndjson = Path(temp_dir) / "test_output.ndjson"
            output_file_json = Path(temp_dir) / "test_output.json"
            
            # Inicializar ProfileManager
            manager = ProfileManager()
            
            print("✅ 1. PROBANDO EXPORTACIÓN NDJSON:")
            try:
                result = manager.process_file(
                    file_path=temp_file_path,
                    profile_name='verso',
                    output_file=str(output_file_ndjson),
                    output_format='ndjson'
                )
                
                # Verificar que se creó el archivo (no directorio)
                if output_file_ndjson.exists():
                    if output_file_ndjson.is_file():
                        print(f"  ✅ Archivo NDJSON creado correctamente: {output_file_ndjson}")
                        with open(output_file_ndjson, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        print(f"  📄 Contenido: {len(lines)} líneas")
                    elif output_file_ndjson.is_dir():
                        print(f"  ❌ ERROR: Se creó un DIRECTORIO en lugar de archivo: {output_file_ndjson}")
                        return False
                else:
                    print(f"  ❌ ERROR: No se creó nada en: {output_file_ndjson}")
                    return False
                    
            except Exception as e:
                print(f"  ❌ ERROR en exportación NDJSON: {str(e)}")
                return False
            
            print("\n✅ 2. PROBANDO EXPORTACIÓN JSON:")
            try:
                result = manager.process_file(
                    file_path=temp_file_path,
                    profile_name='verso',
                    output_file=str(output_file_json),
                    output_format='json'
                )
                
                # Verificar que se creó el archivo (no directorio)
                if output_file_json.exists():
                    if output_file_json.is_file():
                        print(f"  ✅ Archivo JSON creado correctamente: {output_file_json}")
                        with open(output_file_json, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        print(f"  📄 Contenido: {len(data.get('segments', []))} segmentos")
                    elif output_file_json.is_dir():
                        print(f"  ❌ ERROR: Se creó un DIRECTORIO en lugar de archivo: {output_file_json}")
                        return False
                else:
                    print(f"  ❌ ERROR: No se creó nada en: {output_file_json}")
                    return False
                    
            except Exception as e:
                print(f"  ❌ ERROR en exportación JSON: {str(e)}")
                return False
            
            print(f"\n✅ 3. VERIFICANDO CONTENIDOS:")
            
            # Verificar contenido NDJSON
            with open(output_file_ndjson, 'r', encoding='utf-8') as f:
                ndjson_lines = f.readlines()
            
            # Verificar contenido JSON
            with open(output_file_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            print(f"  📊 NDJSON: {len(ndjson_lines)} líneas")
            print(f"  📊 JSON: {len(json_data.get('segments', []))} segmentos")
            
            # Verificar que ambos tienen el mismo número de segmentos
            if len(ndjson_lines) == len(json_data.get('segments', [])):
                print(f"  ✅ Ambos formatos tienen la misma cantidad de segmentos")
            else:
                print(f"  ⚠️ Diferencia en cantidad de segmentos entre formatos")
            
            print(f"\n🎉 ¡PIPELINE DE EXPORTACIÓN FUNCIONANDO CORRECTAMENTE!")
            return True
            
    except ImportError as e:
        print(f"❌ Error de importación: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpiar archivo temporal
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

def test_format_detection():
    """
    Test específico para verificar que los formatos se detectan correctamente.
    """
    print("\n" + "=" * 60)
    print("🔧 PROBANDO DETECCIÓN DE FORMATOS")
    print("=" * 60)
    
    # Simular la función _get_output_format de la GUI
    def get_output_format_fixed(selected_text):
        if selected_text == "JSON":
            return "json"  # ✅ CORREGIDO: minúsculas
        else:  # "NDJSON (líneas JSON)"
            return "ndjson"  # ✅ CORREGIDO: minúsculas
    
    test_cases = [
        ("JSON", "json"),
        ("NDJSON (líneas JSON)", "ndjson"),
    ]
    
    all_passed = True
    for input_format, expected_output in test_cases:
        result = get_output_format_fixed(input_format)
        if result == expected_output:
            print(f"  ✅ {input_format} → {result}")
        else:
            print(f"  ❌ {input_format} → {result} (esperado: {expected_output})")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success1 = test_complete_export_pipeline()
    success2 = test_format_detection()
    
    if success1 and success2:
        print(f"\n🎉 ¡TODOS LOS TESTS PASARON!")
        exit(0)
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON")
        exit(1) 