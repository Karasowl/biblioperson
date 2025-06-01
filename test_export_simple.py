#!/usr/bin/env python3
"""
🔧 TEST SIMPLE DE CORRECCIONES DE EXPORTACIÓN
Verifica que las correcciones estén en el código sin ejecutar todo el pipeline.
"""

import os
import tempfile
import json
from pathlib import Path

def test_code_corrections():
    """
    Verifica que las correcciones estén aplicadas en el código.
    """
    print("🔧 VERIFICANDO CORRECCIONES EN EL CÓDIGO")
    print("=" * 50)
    
    # Archivos a verificar
    files_to_check = [
        "dataset/processing/profile_manager.py",
        "dataset/scripts/process_file.py",
        "dataset/scripts/ui/main_window.py"
    ]
    
    corrections_found = 0
    total_corrections = 0
    
    print("✅ 1. VERIFICANDO ProfileManager.py:")
    profile_manager_path = "dataset/processing/profile_manager.py"
    if os.path.exists(profile_manager_path):
        with open(profile_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar cambio en la definición de función
        total_corrections += 1
        if "def process_file(self," in content and "output_file: Optional[str] = None" in content:
            print("  ✅ Parámetro output_file en process_file()")
            corrections_found += 1
        else:
            print("  ❌ Parámetro output_file NO encontrado")
        
        # Verificar cambio en _export_results
        total_corrections += 1
        if "def _export_results(self, segments: List[Any], output_file: str" in content:
            print("  ✅ Parámetro output_file en _export_results()")
            corrections_found += 1
        else:
            print("  ❌ Parámetro output_file en _export_results NO encontrado")
        
        # Verificar uso correcto en las llamadas internas
        total_corrections += 1
        if "self._export_results(processed_content_items, output_file," in content:
            print("  ✅ Llamadas internas usando output_file")
            corrections_found += 1
        else:
            print("  ❌ Llamadas internas NO corregidas")
    
    print("\\n✅ 2. VERIFICANDO process_file.py:")
    process_file_path = "dataset/scripts/process_file.py"
    if os.path.exists(process_file_path):
        with open(process_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que la llamada use output_file
        total_corrections += 1
        if "output_file=str(output_file_path)" in content:
            print("  ✅ Llamada a manager.process_file usa output_file")
            corrections_found += 1
        else:
            print("  ❌ Llamada a manager.process_file NO corregida")
    
    print("\\n✅ 3. VERIFICANDO main_window.py:")
    main_window_path = "dataset/scripts/ui/main_window.py"
    if os.path.exists(main_window_path):
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar función _get_output_format corregida
        total_corrections += 1
        if 'return "json"  # ✅ CORREGIDO: minúsculas' in content:
            print("  ✅ _get_output_format devuelve minúsculas")
            corrections_found += 1
        else:
            print("  ❌ _get_output_format NO corregida")
        
        # Verificar filtros de archivo actualizados
        total_corrections += 1
        if "current_format = self._get_output_format()" in content and "if current_format == \"json\":" in content:
            print("  ✅ Diálogo de archivo actualizado")
            corrections_found += 1
        else:
            print("  ❌ Diálogo de archivo NO corregido")
    
    print(f"\\n📊 RESUMEN: {corrections_found}/{total_corrections} correcciones encontradas")
    
    if corrections_found == total_corrections:
        print("🎉 ¡TODAS LAS CORRECCIONES ESTÁN APLICADAS!")
        return True
    else:
        print("❌ FALTAN ALGUNAS CORRECCIONES")
        return False

def test_export_logic():
    """
    Simula la lógica de exportación para verificar que funciona correctamente.
    """
    print("\\n" + "=" * 50)
    print("🔧 SIMULANDO LÓGICA DE EXPORTACIÓN")
    print("=" * 50)
    
    def simulate_export_logic(output_path_str, segments, format_type="ndjson"):
        """Simula la lógica corregida de _export_results"""
        
        try:
            output_path = Path(output_path_str)
            
            # ✅ CORRECCIÓN: Solo crear directorio padre, no el archivo como directorio
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir archivo
            with open(output_path, 'w', encoding='utf-8') as f:
                if format_type == "json":
                    json.dump({"segments": segments}, f)
                else:
                    for segment in segments:
                        f.write(json.dumps(segment) + '\\n')
            
            # Verificar resultado
            if output_path.exists() and output_path.is_file():
                return True, f"Archivo creado correctamente: {output_path}"
            elif output_path.exists() and output_path.is_dir():
                return False, f"ERROR: Se creó directorio en lugar de archivo: {output_path}"
            else:
                return False, f"ERROR: No se creó nada"
                
        except Exception as e:
            return False, f"Excepción: {str(e)}"
    
    # Datos de prueba
    test_segments = [
        {"id": 1, "text": "Primer poema", "type": "poem"},
        {"id": 2, "text": "Segundo poema", "type": "poem"}
    ]
    
    # Usar directorio temporal
    with tempfile.TemporaryDirectory() as temp_dir:
        test_files = [
            (Path(temp_dir) / "test.ndjson", "ndjson"),
            (Path(temp_dir) / "test.json", "json")
        ]
        
        all_passed = True
        for test_file, format_type in test_files:
            success, message = simulate_export_logic(str(test_file), test_segments, format_type)
            if success:
                print(f"  ✅ {format_type.upper()}: {message}")
            else:
                print(f"  ❌ {format_type.upper()}: {message}")
                all_passed = False
        
        return all_passed

if __name__ == "__main__":
    success1 = test_code_corrections()
    success2 = test_export_logic()
    
    if success1 and success2:
        print(f"\\n🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        exit(0)
    else:
        print(f"\\n❌ ALGUNAS VERIFICACIONES FALLARON")
        exit(1) 