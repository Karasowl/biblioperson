#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpiar la base de datos y recrearla desde cero.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'biblioteca.db'
SCHEMA_PATH = BASE_DIR / 'data' / 'db_schema.sql'

def limpiar_base_datos():
    """Elimina la base de datos existente y la recrea con el esquema definido."""
    
    # Verificar si existe la base de datos
    if DB_PATH.exists():
        print(f"Eliminando base de datos existente: {DB_PATH}")
        try:
            os.remove(DB_PATH)
            print("Base de datos eliminada correctamente.")
        except Exception as e:
            print(f"Error al eliminar la base de datos: {e}")
            return False
    else:
        print("No existe una base de datos previa.")
    
    # Verificar si existe el esquema
    if not SCHEMA_PATH.exists():
        print(f"Error: No se encontró el archivo de esquema: {SCHEMA_PATH}")
        return False
    
    # Crear directorio de datos si no existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Crear nueva base de datos con el esquema
    try:
        # Leer el archivo de esquema
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Conectar a la nueva base de datos y ejecutar el esquema
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        print(f"Base de datos recreada correctamente: {DB_PATH}")
        return True
    except Exception as e:
        print(f"Error al recrear la base de datos: {e}")
        return False

def main():
    """Función principal."""
    print("=== Iniciando limpieza de base de datos ===")
    resultado = limpiar_base_datos()
    
    if resultado:
        print("=== Limpieza completada con éxito ===")
        return 0
    else:
        print("=== ERROR: La limpieza falló ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 