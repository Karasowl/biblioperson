#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar duplicados exactos por texto en la tabla 'contenidos' de la base de datos.
Uso:
    python limpiar_duplicados.py --db-path <ruta_a_biblioteca.db>
"""
import sqlite3
import argparse
from pathlib import Path

def eliminar_duplicados_por_texto(conn):
    cursor = conn.cursor()
    print("Buscando duplicados exactos por texto en la tabla 'contenidos'...")
    # Buscar duplicados
    cursor.execute('''
        SELECT contenido_texto, COUNT(*) as cantidad, GROUP_CONCAT(id) as ids
        FROM contenidos
        GROUP BY contenido_texto
        HAVING cantidad > 1
    ''')
    duplicados = cursor.fetchall()
    if not duplicados:
        print("No se encontraron duplicados. No se eliminará nada.")
        return
    print(f"Se encontraron {len(duplicados)} textos duplicados.")
    total_entradas_eliminadas = 0
    for dup in duplicados:
        contenido_texto = dup[0]
        ids = [int(x) for x in dup[2].split(',')]
        ids.sort()
        ids_a_borrar = ids[1:]  # Mantener el de menor id
        total_entradas_eliminadas += len(ids_a_borrar)
        primeras_palabras = ' '.join(contenido_texto.strip().split()[:3])
        print(f"DUPLICADO: '{primeras_palabras}...' | IDs eliminados: {ids_a_borrar}")
        # Eliminar los duplicados (excepto el primero)
        cursor.executemany('DELETE FROM contenidos WHERE id = ?', [(i,) for i in ids_a_borrar])
    conn.commit()
    print(f"Total de entradas eliminadas: {total_entradas_eliminadas}")

def main():
    parser = argparse.ArgumentParser(description='Eliminar duplicados exactos por texto en la tabla contenidos')
    parser.add_argument('--db-path', required=True, help='Ruta a la base de datos SQLite (biblioteca.db)')
    args = parser.parse_args()
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"Error: No se encontró la base de datos en {db_path}")
        return
    conn = sqlite3.connect(str(db_path))
    try:
        eliminar_duplicados_por_texto(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()