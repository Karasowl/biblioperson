#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Inicialización de tablas para análisis semántico - Biblioteca de Conocimiento Personal
"""

import os
import sqlite3
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'biblioteca.db'

def inicializar_tablas_semanticas():
    print(f"Inicializando tablas semánticas en {DB_PATH}...")
    
    # Verificar que existe la base de datos
    if not DB_PATH.exists():
        print(f"Error: La base de datos no existe en {DB_PATH}")
        return False
    
    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla para embeddings
    print("Creando tabla de embeddings...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contenido_embeddings (
        contenido_id INTEGER PRIMARY KEY,
        embedding TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contenido_id) REFERENCES contenidos(id)
    )
    ''')
    
    # Tabla para entidades nombradas
    print("Creando tabla de entidades...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entidades (
        id INTEGER PRIMARY KEY,
        contenido_id INTEGER,
        tipo TEXT,
        texto TEXT,
        FOREIGN KEY (contenido_id) REFERENCES contenidos(id)
    )
    ''')
    
    # Crear índices para optimizar consultas
    print("Creando índices...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contenido_id ON contenido_embeddings (contenido_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entidades_contenido ON entidades (contenido_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entidades_tipo ON entidades (tipo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entidades_texto ON entidades (texto)')
    
    conn.commit()
    conn.close()
    
    print("Tablas semánticas inicializadas correctamente.")
    return True

if __name__ == "__main__":
    inicializar_tablas_semanticas() 