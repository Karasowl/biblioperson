#!/usr/bin/env python3
"""
Script para generar embeddings semánticos para contenido almacenado en SQLite.

Este script:
1. Conecta a la base de datos SQLite
2. Obtiene contenido sin embeddings
3. Genera embeddings usando sentence-transformers
4. Actualiza la base de datos con los embeddings generados

Uso:
    python procesar_semantica.py
    python procesar_semantica.py --batch-size 50
    python procesar_semantica.py --model all-MiniLM-L6-v2
"""

import os
import sys
import sqlite3
import argparse
import logging
import json
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.error("sentence-transformers no está instalado. Instálalo con: pip install sentence-transformers")
    sys.exit(1)

class EmbeddingProcessor:
    """Procesador de embeddings para contenido de Biblioperson."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32, provider: str = "sentence-transformers"):
        self.model_name = model_name
        self.batch_size = batch_size
        self.provider = provider
        self.model = None
        self.db_path = self._find_database_path()
        
    def _find_database_path(self) -> str:
        """Encuentra la ruta de la base de datos SQLite."""
        # Buscar en ubicaciones comunes
        possible_paths = [
            "dataset/data/biblioperson.db",
            "dataset/biblioperson.db",
            "data/biblioperson.db",
            "biblioperson.db"
        ]
        
        project_root = Path(__file__).parent.parent.parent
        
        for path in possible_paths:
            full_path = project_root / path
            if full_path.exists():
                logger.info(f"Base de datos encontrada en: {full_path}")
                return str(full_path)
        
        # Si no se encuentra, usar la ruta por defecto
        default_path = project_root / "dataset" / "data" / "biblioperson.db"
        logger.warning(f"Base de datos no encontrada. Usando ruta por defecto: {default_path}")
        return str(default_path)
    
    def load_model(self):
        """Carga el modelo de embeddings según el proveedor seleccionado."""
        logger.info(f"Cargando modelo de embeddings: {self.model_name} (proveedor: {self.provider})")
        try:
            if self.provider == "sentence-transformers":
                # Usar el modelo más avanzado para Sentence Transformers
                advanced_model = "all-mpnet-base-v2"  # Modelo más potente
                self.model = SentenceTransformer(advanced_model)
                logger.info(f"Modelo Sentence Transformers cargado: {advanced_model}")
            elif self.provider == "novita-ai":
                # Para Novita AI, no cargamos modelo local
                self.model = None
                logger.info("Configurado para usar Novita AI (sin modelo local)")
            elif self.provider == "openai":
                # Para OpenAI, no cargamos modelo local
                self.model = None
                logger.info("Configurado para usar OpenAI (sin modelo local)")
            elif self.provider == "meilisearch-huggingface":
                # Para MeiliSearch + HuggingFace, no cargamos modelo local
                self.model = None
                logger.info("Configurado para usar MeiliSearch + HuggingFace")
            else:
                # Fallback a Sentence Transformers
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Proveedor desconocido, usando Sentence Transformers: {self.model_name}")
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {e}")
            raise
    
    def get_content_without_embeddings(self) -> List[Tuple[int, str]]:
        """Obtiene contenido que no tiene embeddings generados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar tabla de contenido (puede variar según el esquema)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%contenido%'
            """)
            tables = cursor.fetchall()
            
            if not tables:
                logger.error("No se encontraron tablas de contenido en la base de datos")
                return []
            
            # Usar la primera tabla de contenido encontrada
            content_table = tables[0][0]
            logger.info(f"Usando tabla de contenido: {content_table}")
            
            # Obtener contenido sin embeddings
            query = f"""
                SELECT id, texto_segmento 
                FROM {content_table} 
                WHERE embedding_vectorial IS NULL OR embedding_vectorial = ''
                LIMIT 1000
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            conn.close()
            
            logger.info(f"Encontrados {len(results)} elementos sin embeddings")
            return results
            
        except Exception as e:
            logger.error(f"Error al obtener contenido: {e}")
            return []
    
    def generate_embeddings(self, texts: List[str], api_config: dict = None) -> List[List[float]]:
        """Genera embeddings para una lista de textos según el proveedor seleccionado."""
        try:
            logger.info(f"Generando embeddings para {len(texts)} textos usando {self.provider}")
            
            if self.provider == "sentence-transformers":
                if not self.model:
                    self.load_model()
                embeddings = self.model.encode(texts, batch_size=self.batch_size)
                return embeddings.tolist()
            
            elif self.provider == "novita-ai":
                return self._generate_novita_embeddings(texts, api_config)
            
            elif self.provider == "openai":
                return self._generate_openai_embeddings(texts, api_config)
            
            elif self.provider == "meilisearch-huggingface":
                # Para MeiliSearch + HuggingFace, los embeddings se generan automáticamente
                # Retornamos embeddings vacíos ya que MeiliSearch los manejará
                logger.info("MeiliSearch + HuggingFace manejará los embeddings automáticamente")
                return [[0.0] * 384 for _ in texts]  # Placeholder embeddings
            
            else:
                # Fallback a Sentence Transformers
                if not self.model:
                    self.load_model()
                embeddings = self.model.encode(texts, batch_size=self.batch_size)
                return embeddings.tolist()
                
        except Exception as e:
            logger.error(f"Error al generar embeddings: {e}")
            raise
    
    def _generate_novita_embeddings(self, texts: List[str], api_config: dict) -> List[List[float]]:
        """Genera embeddings usando Novita AI."""
        import requests
        
        if not api_config or 'novita' not in api_config:
            raise ValueError("Configuración de API de Novita no encontrada")
        
        api_key = api_config['novita']
        base_url = "https://api.novita.ai/v3/embeddings"
        
        embeddings = []
        
        for text in texts:
            try:
                response = requests.post(
                    base_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "text-embedding-ada-002",  # Modelo por defecto
                        "input": text
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result['data'][0]['embedding']
                    embeddings.append(embedding)
                else:
                    logger.error(f"Error en Novita AI: {response.status_code} - {response.text}")
                    # Usar embedding vacío como fallback
                    embeddings.append([0.0] * 1536)
                    
            except Exception as e:
                logger.error(f"Error al generar embedding con Novita AI: {e}")
                embeddings.append([0.0] * 1536)
        
        return embeddings
    
    def _generate_openai_embeddings(self, texts: List[str], api_config: dict) -> List[List[float]]:
        """Genera embeddings usando OpenAI."""
        try:
            import openai
        except ImportError:
            logger.error("openai no está instalado. Instálalo con: pip install openai")
            raise
        
        if not api_config or 'openai' not in api_config:
            raise ValueError("Configuración de API de OpenAI no encontrada")
        
        openai.api_key = api_config['openai']
        embeddings = []
        
        for text in texts:
            try:
                response = openai.Embedding.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                embedding = response['data'][0]['embedding']
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"Error al generar embedding con OpenAI: {e}")
                embeddings.append([0.0] * 1536)
        
        return embeddings
    
    def update_embeddings_in_db(self, content_data: List[Tuple[int, str, List[float]]]):
        """Actualiza la base de datos con los embeddings generados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar tabla de contenido
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%contenido%'
            """)
            tables = cursor.fetchall()
            
            if not tables:
                logger.error("No se encontraron tablas de contenido")
                return
            
            content_table = tables[0][0]
            
            # Actualizar embeddings
            for content_id, text, embedding in content_data:
                embedding_json = json.dumps(embedding)
                
                update_query = f"""
                    UPDATE {content_table} 
                    SET embedding_vectorial = ? 
                    WHERE id = ?
                """
                
                cursor.execute(update_query, (embedding_json, content_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Actualizados {len(content_data)} embeddings en la base de datos")
            
        except Exception as e:
            logger.error(f"Error al actualizar embeddings: {e}")
            raise
    
    def process_all(self, api_config: dict = None):
        """Procesa todo el contenido sin embeddings."""
        logger.info(f"Iniciando procesamiento de embeddings con proveedor: {self.provider}")
        
        # Obtener contenido sin embeddings
        content_without_embeddings = self.get_content_without_embeddings()
        
        if not content_without_embeddings:
            logger.info("No hay contenido para procesar")
            return
        
        # Procesar en lotes
        total_processed = 0
        
        for i in range(0, len(content_without_embeddings), self.batch_size):
            batch = content_without_embeddings[i:i + self.batch_size]
            
            # Extraer IDs y textos
            ids = [item[0] for item in batch]
            texts = [item[1] for item in batch]
            
            # Generar embeddings con configuración de API
            embeddings = self.generate_embeddings(texts, api_config)
            
            # Preparar datos para actualización
            update_data = [(ids[j], texts[j], embeddings[j]) for j in range(len(batch))]
            
            # Actualizar base de datos
            self.update_embeddings_in_db(update_data)
            
            total_processed += len(batch)
            logger.info(f"Procesados {total_processed}/{len(content_without_embeddings)} elementos")
        
        logger.info("Procesamiento de embeddings completado")

def main():
    parser = argparse.ArgumentParser(description="Generar embeddings para contenido de Biblioperson")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", 
                       help="Modelo de embeddings a usar (default: all-MiniLM-L6-v2)")
    parser.add_argument("--batch-size", type=int, default=32,
                       help="Tamaño del lote para procesamiento (default: 32)")
    parser.add_argument("--provider", default="sentence-transformers",
                       choices=["sentence-transformers", "novita-ai", "openai", "meilisearch-huggingface"],
                       help="Proveedor de embeddings (default: sentence-transformers)")
    parser.add_argument("--api-config", type=str,
                       help="Configuración de API en formato JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Activar logging detallado")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parsear configuración de API si se proporciona
    api_config = None
    if args.api_config:
        try:
            api_config = json.loads(args.api_config)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear configuración de API: {e}")
            sys.exit(1)
    
    try:
        processor = EmbeddingProcessor(
            model_name=args.model, 
            batch_size=args.batch_size,
            provider=args.provider
        )
        processor.process_all(api_config)
    except Exception as e:
        logger.error(f"Error en el procesamiento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()