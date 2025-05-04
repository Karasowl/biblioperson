#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para preparar la importación copiando el archivo NDJSON unificado 
a la ubicación correcta dentro del proyecto.
"""

import os
import shutil
import argparse
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
IMPORT_DIR = BASE_DIR / 'data' / 'import'

def main():
    """Función principal para copiar el archivo NDJSON."""
    parser = argparse.ArgumentParser(description='Preparar la importación de datos')
    parser.add_argument('archivo_ndjson', 
                       help='Ruta al archivo NDJSON unificado a importar')
    
    args = parser.parse_args()
    archivo_origen = Path(args.archivo_ndjson)
    
    if not archivo_origen.exists():
        print(f"Error: El archivo especificado no existe: {archivo_origen}")
        return False
    
    # Crear directorio si no existe
    os.makedirs(IMPORT_DIR, exist_ok=True)
    
    # Mantener el nombre original del archivo
    archivo_destino = IMPORT_DIR / archivo_origen.name
    
    try:
        # Copiar archivo a la ubicación de importación
        shutil.copy2(archivo_origen, archivo_destino)
        print(f"Archivo copiado con éxito a: {archivo_destino}")
        print("Ahora puede ejecutar 'python importar_datos.py' para comenzar la importación.")
        return True
    except Exception as e:
        print(f"Error al copiar el archivo: {e}")
        return False

if __name__ == "__main__":
    main() 