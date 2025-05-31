#!/usr/bin/env python3
"""Script para limpiar configuraciones corruptas"""

from PySide6.QtCore import QSettings, QCoreApplication
import sys

def main():
    app = QCoreApplication(sys.argv)
    settings = QSettings("Biblioperson", "DatasetProcessor")
    
    print("=== Limpiando configuraciones corruptas ===")
    
    # Leer todas las configuraciones
    all_keys = settings.allKeys()
    print(f"Configuraciones encontradas: {len(all_keys)}")
    
    corrupted_keys = []
    
    for key in all_keys:
        try:
            value = settings.value(key)
            # Verificar si el valor contiene datos binarios extraños
            if isinstance(value, str) and ('\x00' in value or len(value) > 1000):
                corrupted_keys.append(key)
                print(f"Configuración corrupta encontrada: {key}")
        except Exception as e:
            corrupted_keys.append(key)
            print(f"Error al leer {key}: {e}")
    
    # Eliminar configuraciones corruptas
    if corrupted_keys:
        print(f"\nEliminando {len(corrupted_keys)} configuraciones corruptas...")
        for key in corrupted_keys:
            settings.remove(key)
            print(f"  Eliminado: {key}")
        
        settings.sync()
        print("Configuraciones corruptas eliminadas y sincronizadas")
    else:
        print("No se encontraron configuraciones corruptas")
    
    # Mostrar configuraciones limpias
    print("\n=== Configuraciones después de la limpieza ===")
    clean_keys = settings.allKeys()
    print(f"Total: {len(clean_keys)}")
    
    for key in sorted(clean_keys):
        value = settings.value(key)
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 