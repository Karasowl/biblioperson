#!/usr/bin/env python3
"""Script para verificar las configuraciones guardadas en QSettings"""

from PySide6.QtCore import QSettings

def main():
    settings = QSettings()
    
    print("=== Todas las configuraciones guardadas ===")
    all_keys = settings.allKeys()
    
    if not all_keys:
        print("No hay configuraciones guardadas")
        return
    
    for key in sorted(all_keys):
        value = settings.value(key)
        print(f"{key}: {value}")
    
    print(f"\nTotal de configuraciones: {len(all_keys)}")
    
    # Verificar específicamente las nuevas configuraciones
    print("\n=== Configuraciones de formato y unificación ===")
    output_format = settings.value("output_format", "NO ENCONTRADO")
    unify_output = settings.value("unify_output", "NO ENCONTRADO")
    
    print(f"output_format: {output_format}")
    print(f"unify_output: {unify_output}")

if __name__ == "__main__":
    main() 