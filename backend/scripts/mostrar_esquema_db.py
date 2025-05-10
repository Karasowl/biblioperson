#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Ruta a la base de datos SQLite
DB_PATH = "E:\\dev-projects\\biblioperson\\backend\\data\\biblioteca.db"

def print_table_schema(conn, table_name):
    """Muestra el esquema de una tabla"""
    cursor = conn.cursor()
    
    # Obtener información del esquema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\n=== ESQUEMA DE LA TABLA '{table_name}' ===")
    print("ID | Nombre | Tipo | NotNull | Default | PK")
    print("-" * 60)
    for col in columns:
        print(f"{col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]} | {col[5]}")
    
    # Obtener información de índices
    cursor.execute(f"PRAGMA index_list({table_name})")
    indices = cursor.fetchall()
    
    if indices:
        print("\n--- ÍNDICES ---")
        for idx in indices:
            print(f"Índice: {idx[1]}, Único: {idx[2]}")
            
            # Detalles del índice
            cursor.execute(f"PRAGMA index_info({idx[1]})")
            idx_info = cursor.fetchall()
            for info in idx_info:
                print(f"  Columna: {info[2]}")
    
    # Verificar si hay claves foráneas
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = cursor.fetchall()
    
    if fks:
        print("\n--- CLAVES FORÁNEAS ---")
        for fk in fks:
            print(f"ID: {fk[0]}, Tabla: {fk[2]}, Desde: {fk[3]}, Hacia: {fk[4]}")

def show_sample_data(conn, table_name, limit=5):
    """Muestra una muestra de datos de la tabla"""
    cursor = conn.cursor()
    
    try:
        # Obtener columnas
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Obtener datos de muestra
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        print(f"\n=== MUESTRA DE DATOS DE '{table_name}' (Primeros {limit}) ===")
        
        # Imprimir encabezados
        print(" | ".join(columns))
        print("-" * 100)
        
        # Imprimir filas de datos
        for row in rows:
            # Limitar longitud de campos largos para mejor visualización
            formatted_row = []
            for item in row:
                if item is None:
                    formatted_row.append("NULL")
                elif isinstance(item, str) and len(item) > 50:
                    formatted_row.append(f"{item[:47]}...")
                else:
                    formatted_row.append(str(item))
            print(" | ".join(formatted_row))
            
    except sqlite3.Error as e:
        print(f"Error al obtener datos de muestra: {e}")

def export_schema_to_json(conn, output_file="schema.json"):
    """Exporta el esquema completo de la base de datos a un archivo JSON"""
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    schema = {}
    
    for table in tables:
        table_name = table[0]
        schema[table_name] = {
            "columns": [],
            "indices": [],
            "foreign_keys": []
        }
        
        # Obtener columnas
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            schema[table_name]["columns"].append({
                "id": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": bool(col[3]),
                "default": col[4],
                "primary_key": bool(col[5])
            })
            
        # Obtener índices
        cursor.execute(f"PRAGMA index_list({table_name})")
        indices = cursor.fetchall()
        
        for idx in indices:
            index_info = {
                "name": idx[1],
                "unique": bool(idx[2]),
                "columns": []
            }
            
            # Detalles del índice
            cursor.execute(f"PRAGMA index_info({idx[1]})")
            idx_columns = cursor.fetchall()
            
            for info in idx_columns:
                index_info["columns"].append(info[2])
                
            schema[table_name]["indices"].append(index_info)
            
        # Obtener claves foráneas
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()
        
        for fk in fks:
            schema[table_name]["foreign_keys"].append({
                "id": fk[0],
                "seq": fk[1],
                "table": fk[2],
                "from": fk[3],
                "to": fk[4],
                "on_update": fk[5],
                "on_delete": fk[6],
                "match": fk[7]
            })
    
    # Guardar a archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        
    print(f"\nEsquema completo exportado a {output_file}")

def main():
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(DB_PATH)
        
        # Obtener todas las tablas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        print("=== TABLAS EN LA BASE DE DATOS ===")
        for i, table in enumerate(tables):
            print(f"{i+1}. {table[0]}")
            
        # Mostrar esquema de la tabla 'contenidos'
        if ('contenidos',) in tables:
            print_table_schema(conn, 'contenidos')
            show_sample_data(conn, 'contenidos')
        
        # Exportar esquema completo a JSON
        export_schema_to_json(conn)
        
        # Cerrar conexión
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 