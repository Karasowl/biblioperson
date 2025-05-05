#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Procesador semántico para la Biblioteca de Conocimiento Personal
"""

import os
import sqlite3
import time
from pathlib import Path
from embedding_service import EmbeddingService
from tqdm import tqdm

# Configuración
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'biblioteca.db'

def procesar_embeddings():
    print("Iniciando generación de embeddings...")
    
    # Verificar que existe la base de datos
    if not DB_PATH.exists():
        print(f"Error: La base de datos no existe en {DB_PATH}")
        return False
    
    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Verificar que existen las tablas necesarias
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contenidos'")
    if not cursor.fetchone():
        print("Error: La tabla 'contenidos' no existe")
        conn.close()
        return False
    
    # Verificar que existe la tabla de embeddings
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contenido_embeddings'")
    if not cursor.fetchone():
        print("Error: La tabla 'contenido_embeddings' no existe. Ejecute primero 'inicializar_semantica.py'")
        conn.close()
        return False
    
    # Obtener contenidos sin embeddings
    cursor.execute('''
        SELECT c.id, c.contenido_texto 
        FROM contenidos c
        LEFT JOIN contenido_embeddings ce ON c.id = ce.contenido_id
        WHERE ce.contenido_id IS NULL
    ''')
    
    contenidos = cursor.fetchall()
    total = len(contenidos)
    
    if total == 0:
        print("No hay nuevos contenidos para procesar")
        conn.close()
        return True
    
    print(f"Procesando {total} contenidos...")
    
    # Inicializar servicio de embeddings
    embedding_service = EmbeddingService()
    
    # Procesar cada contenido
    procesados = 0
    inicio = time.time()
    
    for contenido in tqdm(contenidos):
        contenido_id = contenido['id']
        contenido_texto = contenido['contenido_texto']
        
        # Generar y guardar embedding
        embedding = embedding_service.generar_embedding(contenido_texto)
        if embedding:
            embedding_service.guardar_embedding(conn, contenido_id, embedding)
            procesados += 1
            
            # Commit cada 100 documentos
            if procesados % 100 == 0:
                conn.commit()
                tiempo_transcurrido = time.time() - inicio
                tiempo_por_doc = tiempo_transcurrido / procesados
                tiempo_restante = tiempo_por_doc * (total - procesados)
                print(f"Procesados {procesados}/{total} - Tiempo restante estimado: {int(tiempo_restante/60)} minutos")
    
    # Commit final
    conn.commit()
    conn.close()
    
    tiempo_total = time.time() - inicio
    print(f"Procesamiento completado. {procesados} documentos procesados en {int(tiempo_total/60)} minutos")
    return True

if __name__ == "__main__":
    procesar_embeddings() 