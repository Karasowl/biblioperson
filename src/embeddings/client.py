"""
Cliente de embeddings intercambiable para Biblioperson
Soporta embeddings locales (HuggingFace) y cloud (OpenAI)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Union, Optional, Dict, Any
import numpy as np
from functools import lru_cache
import torch
from pathlib import Path

# Imports condicionales
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logging.warning("sentence-transformers no instalado. Embeddings locales no disponibles.")

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logging.warning("openai no instalado. Embeddings de OpenAI no disponibles.")

logger = logging.getLogger(__name__)


class EmbeddingClient(ABC):
    """Clase base abstracta para clientes de embeddings"""
    
    @abstractmethod
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """Genera embeddings para texto(s)"""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Genera embeddings en lotes"""
        pass
    
    @property
    @abstractmethod
    def embedding_dimensions(self) -> int:
        """Retorna las dimensiones del embedding"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Retorna el nombre del modelo"""
        pass
    
    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Retorna el máximo de tokens soportados"""
        pass


class LocalEmbeddingClient(EmbeddingClient):
    """
    Cliente de embeddings locales usando Sentence Transformers
    """
    
    def __init__(self, 
                 model_name: str = "BAAI/bge-large-es-v1.5",
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None):
        """
        Inicializa el cliente de embeddings locales
        
        Args:
            model_name: Nombre del modelo de HuggingFace
            device: Dispositivo a usar ('cuda', 'cpu', o None para auto-detectar)
            cache_dir: Directorio para caché de modelos
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("sentence-transformers no está instalado")
        
        self.model_name_str = model_name
        self.cache_dir = cache_dir or "models/embeddings"
        
        # Auto-detectar dispositivo si no se especifica
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Inicializando modelo {model_name} en dispositivo: {self.device}")
        
        # Cargar modelo
        self.model = SentenceTransformer(
            model_name,
            device=self.device,
            cache_folder=self.cache_dir
        )
        
        # Obtener información del modelo
        self._embedding_dim = self.model.get_sentence_embedding_dimension()
        self._max_seq_length = self.model.max_seq_length
        
        logger.info(f"Modelo cargado: {self._embedding_dim} dimensiones, max {self._max_seq_length} tokens")
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Genera embeddings para texto(s)
        
        Args:
            text: Texto o lista de textos
            
        Returns:
            Array de embeddings
        """
        if isinstance(text, str):
            text = [text]
        
        # Generar embeddings
        embeddings = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,  # Normalizar para similitud coseno
            show_progress_bar=len(text) > 100
        )
        
        # Si era un solo texto, devolver un solo embedding
        if len(text) == 1:
            return embeddings[0]
        
        return embeddings
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Genera embeddings en lotes optimizados
        
        Args:
            texts: Lista de textos
            batch_size: Tamaño del lote
            
        Returns:
            Lista de embeddings
        """
        all_embeddings = []
        
        # Procesar en lotes
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Generar embeddings del lote
            batch_embeddings = self.model.encode(
                batch,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            all_embeddings.extend(batch_embeddings)
            
            # Log de progreso
            if (i + batch_size) % (batch_size * 10) == 0:
                logger.info(f"Procesados {i + batch_size}/{len(texts)} textos")
        
        return all_embeddings
    
    @property
    def embedding_dimensions(self) -> int:
        return self._embedding_dim
    
    @property
    def model_name(self) -> str:
        return self.model_name_str
    
    @property
    def max_tokens(self) -> int:
        return self._max_seq_length
    
    def save_model(self, path: str):
        """Guarda el modelo localmente"""
        self.model.save(path)
        logger.info(f"Modelo guardado en: {path}")
    
    @staticmethod
    def list_available_models() -> List[Dict[str, Any]]:
        """Lista modelos recomendados para español"""
        return [
            {
                "name": "BAAI/bge-large-es-v1.5",
                "dimensions": 1024,
                "description": "Mejor modelo para español, 1024 dimensiones",
                "size": "1.3GB"
            },
            {
                "name": "BAAI/bge-base-es-v1.5",
                "dimensions": 768,
                "description": "Modelo equilibrado para español",
                "size": "440MB"
            },
            {
                "name": "BAAI/bge-small-es-v1.5",
                "dimensions": 384,
                "description": "Modelo ligero para español",
                "size": "134MB"
            },
            {
                "name": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
                "dimensions": 768,
                "description": "Modelo multilingüe general",
                "size": "1GB"
            },
            {
                "name": "sentence-transformers/distiluse-base-multilingual-cased-v2",
                "dimensions": 512,
                "description": "Modelo multilingüe rápido",
                "size": "500MB"
            }
        ]


class OpenAIEmbeddingClient(EmbeddingClient):
    """
    Cliente de embeddings usando OpenAI API
    """
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 model_name: str = "text-embedding-3-small",
                 dimensions: Optional[int] = None):
        """
        Inicializa el cliente de OpenAI
        
        Args:
            api_key: API key de OpenAI
            model_name: Modelo a usar
            dimensions: Dimensiones del embedding (solo para ada v3)
        """
        if not HAS_OPENAI:
            raise ImportError("openai no está instalado")
        
        # Configurar API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key de OpenAI no encontrada")
        
        openai.api_key = self.api_key
        self.model_name_str = model_name
        self.custom_dimensions = dimensions
        
        # Configuración por modelo
        self.model_config = {
            "text-embedding-3-small": {
                "dimensions": dimensions or 1536,
                "max_tokens": 8191,
                "supports_dimensions": True
            },
            "text-embedding-3-large": {
                "dimensions": dimensions or 3072,
                "max_tokens": 8191,
                "supports_dimensions": True
            },
            "text-embedding-ada-002": {
                "dimensions": 1536,
                "max_tokens": 8191,
                "supports_dimensions": False
            }
        }
        
        if model_name not in self.model_config:
            raise ValueError(f"Modelo no soportado: {model_name}")
        
        self.config = self.model_config[model_name]
        logger.info(f"Cliente OpenAI inicializado: {model_name} ({self.config['dimensions']} dims)")
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Genera embeddings usando OpenAI API
        """
        if isinstance(text, str):
            text = [text]
            single_text = True
        else:
            single_text = False
        
        try:
            # Preparar parámetros
            params = {
                "model": self.model_name_str,
                "input": text
            }
            
            # Agregar dimensiones si el modelo lo soporta
            if self.config["supports_dimensions"] and self.custom_dimensions:
                params["dimensions"] = self.custom_dimensions
            
            # Llamar a la API
            response = openai.embeddings.create(**params)
            
            # Extraer embeddings
            embeddings = [np.array(item.embedding) for item in response.data]
            
            if single_text:
                return embeddings[0]
            
            return np.array(embeddings)
            
        except Exception as e:
            logger.error(f"Error generando embeddings con OpenAI: {e}")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[np.ndarray]:
        """
        Genera embeddings en lotes (OpenAI soporta hasta 2048 inputs por request)
        """
        all_embeddings = []
        
        # OpenAI permite hasta 2048 inputs por request
        api_batch_size = min(batch_size, 2048)
        
        for i in range(0, len(texts), api_batch_size):
            batch = texts[i:i + api_batch_size]
            
            try:
                embeddings = self.embed_text(batch)
                all_embeddings.extend(embeddings)
                
                if (i + api_batch_size) % 1000 == 0:
                    logger.info(f"Procesados {i + api_batch_size}/{len(texts)} textos")
                    
            except Exception as e:
                logger.error(f"Error en lote {i}-{i+api_batch_size}: {e}")
                # Intentar procesar uno por uno en caso de error
                for text in batch:
                    try:
                        emb = self.embed_text(text)
                        all_embeddings.append(emb)
                    except Exception as e2:
                        logger.error(f"Error en texto individual: {e2}")
                        # Agregar embedding vacío para mantener alineación
                        all_embeddings.append(np.zeros(self.embedding_dimensions))
        
        return all_embeddings
    
    @property
    def embedding_dimensions(self) -> int:
        return self.config["dimensions"]
    
    @property
    def model_name(self) -> str:
        return self.model_name_str
    
    @property
    def max_tokens(self) -> int:
        return self.config["max_tokens"]
    
    @staticmethod
    def estimate_cost(num_tokens: int, model: str = "text-embedding-3-small") -> float:
        """
        Estima el costo de generar embeddings
        
        Args:
            num_tokens: Número total de tokens
            model: Modelo a usar
            
        Returns:
            Costo estimado en USD
        """
        # Precios por millón de tokens (a dic 2024)
        pricing = {
            "text-embedding-3-small": 0.02,  # $0.02 per 1M tokens
            "text-embedding-3-large": 0.13,  # $0.13 per 1M tokens
            "text-embedding-ada-002": 0.10   # $0.10 per 1M tokens
        }
        
        price_per_million = pricing.get(model, 0.02)
        return (num_tokens / 1_000_000) * price_per_million


class HybridEmbeddingClient(EmbeddingClient):
    """
    Cliente híbrido que usa embeddings locales con fallback a cloud
    """
    
    def __init__(self,
                 primary_client: EmbeddingClient,
                 fallback_client: Optional[EmbeddingClient] = None):
        """
        Inicializa cliente híbrido
        
        Args:
            primary_client: Cliente principal (generalmente local)
            fallback_client: Cliente de respaldo (generalmente cloud)
        """
        self.primary = primary_client
        self.fallback = fallback_client
        self._last_used = "primary"
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """Intenta con primario, usa fallback si falla"""
        try:
            self._last_used = "primary"
            return self.primary.embed_text(text)
        except Exception as e:
            logger.warning(f"Error en cliente primario: {e}")
            if self.fallback:
                logger.info("Usando cliente de respaldo")
                self._last_used = "fallback"
                return self.fallback.embed_text(text)
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Procesa en lotes con fallback"""
        try:
            self._last_used = "primary"
            return self.primary.embed_batch(texts, batch_size)
        except Exception as e:
            logger.warning(f"Error en cliente primario: {e}")
            if self.fallback:
                logger.info("Usando cliente de respaldo para lote")
                self._last_used = "fallback"
                return self.fallback.embed_batch(texts, batch_size)
            raise
    
    @property
    def embedding_dimensions(self) -> int:
        if self._last_used == "primary":
            return self.primary.embedding_dimensions
        return self.fallback.embedding_dimensions if self.fallback else self.primary.embedding_dimensions
    
    @property
    def model_name(self) -> str:
        if self._last_used == "primary":
            return f"{self.primary.model_name} (primary)"
        return f"{self.fallback.model_name} (fallback)" if self.fallback else self.primary.model_name
    
    @property
    def max_tokens(self) -> int:
        return min(self.primary.max_tokens, 
                  self.fallback.max_tokens if self.fallback else float('inf'))


# Factory function para crear clientes
def create_embedding_client(backend: str = "local", **kwargs) -> EmbeddingClient:
    """
    Factory para crear clientes de embeddings
    
    Args:
        backend: Tipo de backend ('local', 'openai', 'hybrid')
        **kwargs: Argumentos específicos del backend
        
    Returns:
        Cliente de embeddings configurado
    """
    if backend == "local":
        return LocalEmbeddingClient(**kwargs)
    
    elif backend == "openai":
        return OpenAIEmbeddingClient(**kwargs)
    
    elif backend == "hybrid":
        # Crear cliente local primario
        local_kwargs = {k: v for k, v in kwargs.items() 
                       if k in ['model_name', 'device', 'cache_dir']}
        primary = LocalEmbeddingClient(**local_kwargs)
        
        # Crear cliente OpenAI como fallback si hay API key
        fallback = None
        if 'api_key' in kwargs or os.getenv("OPENAI_API_KEY"):
            openai_kwargs = {k: v for k, v in kwargs.items() 
                           if k in ['api_key', 'model_name', 'dimensions']}
            # Ajustar nombre de modelo para OpenAI
            if 'model_name' not in openai_kwargs:
                openai_kwargs['model_name'] = 'text-embedding-3-small'
            
            try:
                fallback = OpenAIEmbeddingClient(**openai_kwargs)
            except Exception as e:
                logger.warning(f"No se pudo crear cliente OpenAI de respaldo: {e}")
        
        return HybridEmbeddingClient(primary, fallback)
    
    else:
        raise ValueError(f"Backend no soportado: {backend}")


# Cache global para modelos
_embedding_clients = {}

def get_embedding_client(backend: str = "local", 
                        force_reload: bool = False,
                        **kwargs) -> EmbeddingClient:
    """
    Obtiene un cliente de embeddings (con caché)
    
    Args:
        backend: Tipo de backend
        force_reload: Forzar recarga del modelo
        **kwargs: Argumentos del cliente
        
    Returns:
        Cliente de embeddings
    """
    cache_key = f"{backend}_{str(kwargs)}"
    
    if force_reload or cache_key not in _embedding_clients:
        _embedding_clients[cache_key] = create_embedding_client(backend, **kwargs)
    
    return _embedding_clients[cache_key]


if __name__ == "__main__":
    # Ejemplo de uso
    import time
    
    # Textos de prueba
    test_texts = [
        "La filosofía de Platón sobre la justicia en La República",
        "Algoritmos de búsqueda en inteligencia artificial",
        "Poema sobre el amor y la naturaleza"
    ]
    
    print("=== Probando embeddings locales ===")
    try:
        local_client = create_embedding_client("local", model_name="BAAI/bge-small-es-v1.5")
        
        # Embedding individual
        start = time.time()
        emb1 = local_client.embed_text(test_texts[0])
        print(f"Embedding individual: {emb1.shape}, tiempo: {time.time()-start:.2f}s")
        
        # Embeddings en lote
        start = time.time()
        embs = local_client.embed_batch(test_texts)
        print(f"Embeddings en lote: {len(embs)} x {embs[0].shape}, tiempo: {time.time()-start:.2f}s")
        
        # Calcular similitudes
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(embs)
        print("\nMatriz de similitudes:")
        for i in range(len(test_texts)):
            for j in range(len(test_texts)):
                print(f"{similarities[i,j]:.3f}", end=" ")
            print()
        
    except Exception as e:
        print(f"Error con embeddings locales: {e}")
    
    print("\n=== Información de modelos disponibles ===")
    for model in LocalEmbeddingClient.list_available_models():
        print(f"- {model['name']}: {model['description']} ({model['size']})") 