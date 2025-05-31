#!/usr/bin/env python3
"""Script para debuggear QSettings"""

from PySide6.QtCore import QSettings, QCoreApplication
import sys

def main():
    # Crear aplicación para QSettings
    app = QCoreApplication(sys.argv)
    
    print("=== Información de QSettings ===")
    
    # Crear QSettings
    settings = QSettings()
    
    print(f"Organización: {settings.organizationName()}")
    print(f"Aplicación: {settings.applicationName()}")
    print(f"Formato: {settings.format()}")
    print(f"Scope: {settings.scope()}")
    print(f"Archivo de configuración: {settings.fileName()}")
    
    # Probar escribir y leer
    print("\n=== Prueba de escritura/lectura ===")
    
    # Escribir valores de prueba
    settings.setValue("test_string", "valor_prueba")
    settings.setValue("test_bool", True)
    settings.setValue("test_int", 42)
    settings.sync()
    
    print("Valores escritos:")
    print(f"  test_string: valor_prueba")
    print(f"  test_bool: True")
    print(f"  test_int: 42")
    
    # Leer valores
    test_string = settings.value("test_string", "NO_ENCONTRADO")
    test_bool = settings.value("test_bool", False, bool)
    test_int = settings.value("test_int", 0, int)
    
    print("\nValores leídos:")
    print(f"  test_string: {test_string}")
    print(f"  test_bool: {test_bool}")
    print(f"  test_int: {test_int}")
    
    # Verificar todas las claves
    all_keys = settings.allKeys()
    print(f"\nTotal de claves: {len(all_keys)}")
    for key in sorted(all_keys):
        value = settings.value(key)
        print(f"  {key}: {value}")
    
    # Limpiar valores de prueba
    settings.remove("test_string")
    settings.remove("test_bool")
    settings.remove("test_int")
    settings.sync()
    
    print("\n=== Valores de prueba eliminados ===")

if __name__ == "__main__":
    main() 