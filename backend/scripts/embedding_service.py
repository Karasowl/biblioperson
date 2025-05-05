#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de embeddings para la Biblioteca de Conocimiento Personal
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import json
import sqlite3
from pathlib import Path
from tqdm import tqdm

class EmbeddingService:
    def __init__(self, model_name='paraphrase-multilingual-mpnet-base-v2'):
        print(f"Inicializando servicio de embeddings con modelo: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            print(f"Modelo cargado correctamente: {model_name}")
        except Exception as e:
            print(f"ERROR al cargar el modelo {model_name}: {str(e)}")
            # Intentar con un modelo alternativo más básico
            try:
                backup_model = 'distiluse-base-multilingual-cased-v1'
                print(f"Intentando con modelo alternativo: {backup_model}")
                self.model = SentenceTransformer(backup_model)
                print(f"Modelo alternativo cargado correctamente")
            except Exception as e2:
                print(f"ERROR crítico al cargar modelos de embedding: {str(e2)}")
                raise RuntimeError(f"No se pudo inicializar ningún modelo de embedding: {str(e2)}")
        
    def generar_embedding(self, contenido_texto):
        """Genera el vector de embedding para un contenido_texto"""
        try:
            if not contenido_texto:
                print(f"Error: contenido_texto vacío")
                return None
            if len(contenido_texto) < 3:
                print(f"Error: contenido_texto demasiado corto ({len(contenido_texto)} caracteres): {contenido_texto}")
                return None
            return self.model.encode(contenido_texto).tolist()
        except Exception as e:
            print(f"Error al generar embedding: {str(e)}")
            print(f"Texto problemático: '{contenido_texto}'")
            return None
        
    def guardar_embedding(self, conn, contenido_id, embedding):
        """Guarda el embedding en la base de datos"""
        if not embedding:
            return False
            
        cursor = conn.cursor()
        embedding_json = json.dumps(embedding)
        
        # Verificar si ya existe
        cursor.execute('SELECT contenido_id FROM contenido_embeddings WHERE contenido_id = ?', (contenido_id,))
        if cursor.fetchone():
            cursor.execute('UPDATE contenido_embeddings SET embedding = ? WHERE contenido_id = ?',
                          (embedding_json, contenido_id))
        else:
            cursor.execute('INSERT INTO contenido_embeddings (contenido_id, embedding) VALUES (?, ?)',
                          (contenido_id, embedding_json))
        
        return True
        
    def calcular_similitud(self, vec1, vec2):
        """Calcula la similitud coseno entre dos vectores"""
        np_vec1 = np.array(vec1)
        np_vec2 = np.array(vec2)
        return np.dot(np_vec1, np_vec2) / (np.linalg.norm(np_vec1) * np.linalg.norm(np_vec2)) 