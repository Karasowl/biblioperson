#!/usr/bin/env python3
"""
🔧 TEST DE CORRECCIÓN DE EXPORTACIÓN
Verifica que los problemas de formato y extensión están corregidos.
"""

def test_format_conversion():
    """
    Simula la función _get_output_format() corregida.
    """
    print("🔧 PROBANDO CORRECCIÓN DE FORMATO")
    print("=" * 50)
    
    def get_output_format_fixed(selected_text):
        """Función corregida que simula _get_output_format()"""
        if selected_text == "JSON":
            return "json"  # ✅ CORREGIDO: minúsculas
        else:  # "NDJSON (líneas JSON)"
            return "ndjson"  # ✅ CORREGIDO: minúsculas
    
    def get_output_format_original(selected_text):
        """Función original que tenía el bug"""
        if selected_text == "JSON":
            return "JSON"  # ❌ PROBLEMA: mayúsculas
        else:  # "NDJSON (líneas JSON)"
            return "NDJSON"  # ❌ PROBLEMA: mayúsculas
    
    test_cases = ["JSON", "NDJSON (líneas JSON)"]
    
    for case in test_cases:
        original = get_output_format_original(case)
        fixed = get_output_format_fixed(case)
        
        print(f"Selección: '{case}'")
        print(f"  Original (problemático): '{original}'")
        print(f"  Corregido: '{fixed}'")
        
        # Simular comparación en ProfileManager
        original_matches = original.lower() == "json"
        fixed_matches = fixed.lower() == "json"
        
        print(f"  ¿Detecta JSON? Original: {original_matches}, Corregido: {fixed_matches}")
        print()

def test_file_extension():
    """
    Simula la corrección de extensiones de archivo.
    """
    print("📁 PROBANDO CORRECCIÓN DE EXTENSIONES")
    print("=" * 50)
    
    def add_extension_if_needed(file_path, format_type):
        """Función que añade extensión si es necesaria"""
        if format_type == "json":
            default_ext = ".json"
        else:
            default_ext = ".ndjson"
            
        if not file_path.lower().endswith(('.json', '.ndjson')):
            return file_path + default_ext, True
        else:
            return file_path, False
    
    test_cases = [
        ("mi_archivo", "json"),
        ("mi_archivo", "ndjson"),
        ("mi_archivo.json", "json"),
        ("mi_archivo.ndjson", "ndjson"),
        ("mi_archivo.txt", "json"),
        ("mi_archivo.pdf", "ndjson"),
    ]
    
    for file_path, format_type in test_cases:
        final_path, extension_added = add_extension_if_needed(file_path, format_type)
        
        print(f"Archivo: '{file_path}' + Formato: '{format_type}'")
        print(f"  Resultado: '{final_path}'")
        print(f"  ¿Extensión añadida? {'Sí' if extension_added else 'No'}")
        print()

if __name__ == "__main__":
    test_format_conversion()
    test_file_extension() 