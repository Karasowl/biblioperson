#!/usr/bin/env python3
"""Script para probar QSettings con la misma configuración que la aplicación"""

from PySide6.QtCore import QSettings, QCoreApplication
import sys

def main():
    # Crear aplicación
    app = QCoreApplication(sys.argv)
    
    print("=== Prueba de QSettings con configuración de Biblioperson ===")
    
    # Crear QSettings con la misma configuración que la aplicación
    settings = QSettings("Biblioperson", "DatasetProcessor")
    
    print(f"Organización: {settings.organizationName()}")
    print(f"Aplicación: {settings.applicationName()}")
    print(f"Formato: {settings.format()}")
    print(f"Scope: {settings.scope()}")
    print(f"Archivo de configuración: {settings.fileName()}")
    
    # Verificar configuraciones existentes
    all_keys = settings.allKeys()
    print(f"\nConfiguraciones existentes: {len(all_keys)}")
    for key in sorted(all_keys):
        value = settings.value(key)
        print(f"  {key}: {value}")
    
    # Probar escribir las configuraciones que nos interesan
    print("\n=== Escribiendo configuraciones de prueba ===")
    
    settings.setValue("output_format", "JSON")
    settings.setValue("unify_output", True)
    settings.setValue("test_timestamp", "2025-01-26 17:45:00")
    settings.sync()
    
    print("Configuraciones escritas:")
    print("  output_format: JSON")
    print("  unify_output: True")
    print("  test_timestamp: 2025-01-26 17:45:00")
    
    # Leer las configuraciones
    print("\n=== Leyendo configuraciones ===")
    
    output_format = settings.value("output_format", "NO_ENCONTRADO")
    unify_output = settings.value("unify_output", False, bool)
    test_timestamp = settings.value("test_timestamp", "NO_ENCONTRADO")
    
    print(f"output_format leído: {output_format}")
    print(f"unify_output leído: {unify_output}")
    print(f"test_timestamp leído: {test_timestamp}")
    
    # Verificar todas las claves después de escribir
    all_keys_after = settings.allKeys()
    print(f"\nTotal de configuraciones después de escribir: {len(all_keys_after)}")
    for key in sorted(all_keys_after):
        value = settings.value(key)
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 