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
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
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
        
    def generar_embedding(self, texto):
        """Genera el vector de embedding para un texto"""
        try:
            if not texto:
                print(f"Error: Texto vacío")
                return None
                
            # Reducir el límite mínimo o eliminarlo
            if len(texto) < 3:  # Ahora aceptamos textos de al menos 3 caracteres
                print(f"Error: Texto demasiado corto ({len(texto)} caracteres): {texto}")
                return None
                
            return self.model.encode(texto).tolist()
        except Exception as e:
            print(f"Error al generar embedding: {str(e)}")
            print(f"Texto problemático: '{texto}'")
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