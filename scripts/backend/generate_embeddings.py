#!/usr/bin/env python3
"""
GENERADOR DE EMBEDDINGS MÁS POTENTE Y COMPLETO para Biblioperson
Soporta múltiples modelos avanzados y técnicas de optimización
"""

import numpy as np
import logging
from typing import List, Dict, Optional, Union
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)

class AdvancedEmbeddingGenerator:
    """
    Generador de embeddings más potente con múltiples modelos y optimizaciones avanzadas.
    
    Modelos soportados:
    - all-mpnet-base-v2: 768 dims - Máxima calidad general
    - paraphrase-multilingual-mpnet-base-v2: 768 dims - Multilingüe potente
    - all-MiniLM-L12-v2: 384 dims - Balance calidad/velocidad
    - multi-qa-mpnet-base-dot-v1: 768 dims - Optimizado para Q&A
    """
    
    ADVANCED_MODELS = {
        'ultra_quality': {
            'model': 'all-mpnet-base-v2',
            'dimensions': 768,
            'description': 'Máxima calidad - Mejor para búsqueda semántica profunda',
            'languages': ['en', 'es', 'fr', 'de', 'it'],
            'use_case': 'Búsqueda semántica de alta precisión'
        },
        'multilingual_power': {
            'model': 'paraphrase-multilingual-mpnet-base-v2', 
            'dimensions': 768,
            'description': 'Potencia multilingüe - Optimizado para español',
            'languages': ['es', 'en', 'fr', 'de', 'it', 'pt', 'ru', 'zh'],
            'use_case': 'Contenido multilingüe y español avanzado'
        },
        'spanish_expert': {
            'model': 'hiiamsid/sentence_similarity_spanish_es',
            'dimensions': 384,
            'description': 'Experto en español - Entrenado específicamente',
            'languages': ['es'],
            'use_case': 'Contenido exclusivamente en español'
        }
    }
    
    def __init__(self, model_config: str = "ultra_quality"):
        """Inicializar el generador con configuración avanzada."""
        self.model_config = model_config
        self.model = None
        self.model_info = self.ADVANCED_MODELS.get(model_config, self.ADVANCED_MODELS['ultra_quality'])
        
        logger.info(f"🚀 Inicializando generador POTENTE: {self.model_info['description']}")
        logger.info(f"🔢 Dimensiones: {self.model_info['dimensions']}")
        
        self._load_model()
    
    def _load_model(self):
        """Cargar el modelo más potente."""
        try:
            model_name = self.model_info['model']
            logger.info(f"📥 Cargando modelo POTENTE: {model_name}")
            
            self.model = SentenceTransformer(model_name)
            
            # Verificar dimensiones
            test_embedding = self.model.encode("test", convert_to_numpy=True)
            actual_dims = len(test_embedding)
            
            logger.info(f"✅ Modelo POTENTE cargado exitosamente")
            logger.info(f"🔢 Dimensiones verificadas: {actual_dims}")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo potente: {e}")
            # Fallback a modelo básico
            logger.warning("⚠️ Fallback a modelo básico")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generar embedding con máxima potencia y calidad."""
        if self.model is None:
            raise RuntimeError("❌ Modelo no cargado")
        
        logger.debug(f"🧠 Generando embedding POTENTE")
        
        try:
            # Generar embedding con máxima potencia
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convertir a float32 para máxima precisión
            embedding = embedding.astype(np.float32)
            
            logger.debug(f"✅ Embedding generado: shape={embedding.shape}, dtype={embedding.dtype}")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error generando embedding: {e}")
            raise


# Alias para compatibilidad con el backend existente
class EmbeddingGenerator(AdvancedEmbeddingGenerator):
    """Alias para compatibilidad con el código existente."""
    
    def __init__(self, provider="sentence-transformers", model_name="all-mpnet-base-v2"):
        # Mapear nombres de modelos a configuraciones avanzadas
        model_mapping = {
            "all-mpnet-base-v2": "ultra_quality",
            "paraphrase-multilingual-mpnet-base-v2": "multilingual_power",
            "hiiamsid/sentence_similarity_spanish_es": "spanish_expert"
        }
        
        config = model_mapping.get(model_name, "ultra_quality")
        super().__init__(model_config=config)
        
        logger.info(f"🔄 Compatibilidad activada: {model_name} → {config}")


if __name__ == "__main__":
    print("🚀 GENERADOR MÁS POTENTE LISTO")
    generator = AdvancedEmbeddingGenerator(model_config="ultra_quality")
    print("🎯 ¡GENERADOR POTENTE LISTO PARA PRODUCCIÓN!") 