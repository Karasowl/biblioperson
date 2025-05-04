#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script que ejecuta todo el proceso de importación en un solo paso.
Copia el archivo NDJSON y luego lo importa a la base de datos.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

def ejecutar_comando(comando):
    """Ejecuta un comando y muestra la salida en tiempo real."""
    proceso = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Mostrar la salida en tiempo real
    for linea in proceso.stdout:
        print(linea, end='')
    
    # Esperar a que termine
    proceso.wait()
    return proceso.returncode

def main():
    """Función principal que ejecuta todo el proceso de importación."""
    parser = argparse.ArgumentParser(description='Ejecutar todo el proceso de importación en un solo paso')
    parser.add_argument('archivo_ndjson', nargs='?', default=None,
                       help='Ruta al archivo NDJSON unificado a importar (opcional si ya hay archivos en la carpeta de importación)')
    parser.add_argument('--reiniciar-db', action='store_true', 
                       help='Eliminar la base de datos existente y crearla de nuevo')
    parser.add_argument('--solo-importar', action='store_true',
                       help='Solo importar desde los archivos ya existentes en la carpeta de importación')
    
    args = parser.parse_args()
    archivo_ndjson = Path(args.archivo_ndjson) if args.archivo_ndjson else None
    
    # Verificar si se proporcionó un archivo y si existe
    if archivo_ndjson and not archivo_ndjson.exists() and not args.solo_importar:
        print(f"Error: El archivo NDJSON especificado no existe: {archivo_ndjson}")
        return 1
    
    # Si no se especificó archivo y se requiere solo importar, verificar si hay archivos en la carpeta
    if args.solo_importar or not archivo_ndjson:
        import_dir = BASE_DIR / 'data' / 'import'
        archivos_existentes = list(import_dir.glob('*.ndjson'))
        if not archivos_existentes:
            print(f"Error: No se encontraron archivos NDJSON en {import_dir}")
            print("Por favor, especifique un archivo para importar o copie archivos NDJSON a la carpeta de importación.")
            return 1
        else:
            print(f"Se utilizarán los archivos existentes en la carpeta de importación:")
            for i, f in enumerate(archivos_existentes, 1):
                print(f"  {i}. {f.name}")
    
    # Reiniciar base de datos si se solicita
    if args.reiniciar_db:
        print("\n=== PASO 0: Limpiando base de datos ===\n")
        comando_limpiar = [
            sys.executable,
            str(SCRIPTS_DIR / 'limpiar_base_datos.py')
        ]
        if ejecutar_comando(comando_limpiar) != 0:
            print("Error al limpiar la base de datos.")
            return 1
    
    # Paso 1: Copiar el archivo NDJSON (si se proporcionó uno)
    if archivo_ndjson and not args.solo_importar:
        print("\n=== PASO 1: Copiando archivo NDJSON ===\n")
        comando_preparar = [
            sys.executable,
            str(SCRIPTS_DIR / 'preparar_importacion.py'),
            str(archivo_ndjson)
        ]
        
        if ejecutar_comando(comando_preparar) != 0:
            print("Error al copiar el archivo NDJSON.")
            return 1
    else:
        print("\n=== PASO 1: Omitiendo copia de archivo (usando archivos existentes) ===\n")
    
    # Paso 2: Importar datos a la base de datos
    print("\n=== PASO 2: Importando datos a la base de datos ===\n")
    comando_importar = [
        sys.executable,
        str(SCRIPTS_DIR / 'importar_datos.py')
    ]
    
    if ejecutar_comando(comando_importar) != 0:
        print("Error al importar datos a la base de datos.")
        return 1
    
    print("\n¡Importación completada con éxito!")
    if archivo_ndjson and not args.solo_importar:
        print(f"Los datos han sido importados desde: {archivo_ndjson}")
    else:
        print(f"Los datos han sido importados desde los archivos en: {BASE_DIR / 'data' / 'import'}")
    print(f"Base de datos: {BASE_DIR / 'data' / 'biblioteca.db'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 