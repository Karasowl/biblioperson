#!/usr/bin/env python3
"""
Sistema de proveedores OCR para Biblioperson Dataset Processor.

Soporta múltiples proveedores para máxima flexibilidad en entornos web:
- Tesseract (local/Docker)
- Google Vision API (cloud)
- AWS Textract (cloud) 
- Azure Cognitive Services (cloud)
- Fallback mejorado
"""

import os
import io
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)

class OCRProvider(ABC):
    """Interfaz base para proveedores OCR"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el proveedor está disponible"""
        pass
    
    @abstractmethod
    def extract_text_from_image(self, image: Image.Image, language: str = 'spa') -> str:
        """Extrae texto de una imagen"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Nombre del proveedor"""
        pass

class TesseractProvider(OCRProvider):
    """Proveedor OCR usando Tesseract local"""
    
    def __init__(self):
        self.tesseract_cmd = os.environ.get('TESSERACT_CMD', 'tesseract')
        
    def is_available(self) -> bool:
        """Verifica si Tesseract está disponible"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.debug(f"Tesseract no disponible: {e}")
            return False
    
    def extract_text_from_image(self, image: Image.Image, language: str = 'spa') -> str:
        """Extrae texto usando Tesseract"""
        try:
            import pytesseract
            
            # Configurar comando si está especificado
            if self.tesseract_cmd != 'tesseract':
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            
            # Configuración OCR optimizada
            ocr_config = '--psm 6 --oem 3 -c preserve_interword_spaces=1'
            
            # Mapear códigos de idioma
            lang_map = {
                'spa': 'spa',
                'es': 'spa', 
                'eng': 'eng',
                'en': 'eng'
            }
            tesseract_lang = lang_map.get(language, 'spa')
            
            try:
                # Intentar con idioma especificado
                text = pytesseract.image_to_string(image, lang=tesseract_lang, config=ocr_config)
            except Exception:
                # Fallback a inglés
                text = pytesseract.image_to_string(image, lang='eng', config=ocr_config)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error en Tesseract OCR: {e}")
            return ""
    
    def get_provider_name(self) -> str:
        return "Tesseract"

class GoogleVisionProvider(OCRProvider):
    """Proveedor OCR usando Google Vision API"""
    
    def is_available(self) -> bool:
        """Verifica si Google Vision está disponible"""
        try:
            from google.cloud import vision
            
            # Verificar credenciales
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path or not os.path.exists(credentials_path):
                logger.debug("Google Vision: credenciales no configuradas")
                return False
            
            return True
        except ImportError:
            logger.debug("Google Vision: librería no instalada")
            return False
        except Exception as e:
            logger.debug(f"Google Vision no disponible: {e}")
            return False
    
    def extract_text_from_image(self, image: Image.Image, language: str = 'spa') -> str:
        """Extrae texto usando Google Vision API"""
        try:
            from google.cloud import vision
            
            client = vision.ImageAnnotatorClient()
            
            # Convertir PIL Image a bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Crear objeto imagen para Vision API
            vision_image = vision.Image(content=img_byte_arr)
            
            # Configurar hints de idioma
            image_context = vision.ImageContext(language_hints=[language])
            
            # Realizar OCR
            response = client.text_detection(image=vision_image, image_context=image_context)
            
            if response.text_annotations:
                return response.text_annotations[0].description.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error en Google Vision OCR: {e}")
            return ""
    
    def get_provider_name(self) -> str:
        return "Google Vision"

class AWSTextractProvider(OCRProvider):
    """Proveedor OCR usando AWS Textract"""
    
    def is_available(self) -> bool:
        """Verifica si AWS Textract está disponible"""
        try:
            import boto3
            
            # Verificar credenciales AWS
            access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            
            if not access_key or not secret_key:
                logger.debug("AWS Textract: credenciales no configuradas")
                return False
            
            return True
        except ImportError:
            logger.debug("AWS Textract: librería boto3 no instalada")
            return False
        except Exception as e:
            logger.debug(f"AWS Textract no disponible: {e}")
            return False
    
    def extract_text_from_image(self, image: Image.Image, language: str = 'spa') -> str:
        """Extrae texto usando AWS Textract"""
        try:
            import boto3
            
            # Convertir PIL Image a bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Cliente Textract
            textract = boto3.client('textract', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
            
            # Detectar texto
            response = textract.detect_document_text(
                Document={'Bytes': img_bytes}
            )
            
            # Extraer texto de la respuesta
            text_blocks = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_blocks.append(block['Text'])
            
            return '\n'.join(text_blocks)
            
        except Exception as e:
            logger.error(f"Error en AWS Textract OCR: {e}")
            return ""
    
    def get_provider_name(self) -> str:
        return "AWS Textract"

class AzureVisionProvider(OCRProvider):
    """Proveedor OCR usando Azure Cognitive Services"""
    
    def is_available(self) -> bool:
        """Verifica si Azure Vision está disponible"""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials
            
            key = os.environ.get('AZURE_VISION_KEY')
            endpoint = os.environ.get('AZURE_VISION_ENDPOINT')
            
            if not key or not endpoint:
                logger.debug("Azure Vision: credenciales no configuradas")
                return False
            
            return True
        except ImportError:
            logger.debug("Azure Vision: librería no instalada")
            return False
        except Exception as e:
            logger.debug(f"Azure Vision no disponible: {e}")
            return False
    
    def extract_text_from_image(self, image: Image.Image, language: str = 'spa') -> str:
        """Extrae texto usando Azure Cognitive Services"""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials
            import time
            
            # Configurar cliente
            key = os.environ.get('AZURE_VISION_KEY')
            endpoint = os.environ.get('AZURE_VISION_ENDPOINT')
            
            credentials = CognitiveServicesCredentials(key)
            client = ComputerVisionClient(endpoint, credentials)
            
            # Convertir PIL Image a bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Iniciar operación OCR
            read_response = client.read_in_stream(img_byte_arr, raw=True)
            operation_id = read_response.headers["Operation-Location"].split("/")[-1]
            
            # Esperar resultados
            while True:
                read_result = client.get_read_result(operation_id)
                if read_result.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)
            
            # Extraer texto
            text_blocks = []
            if read_result.status == 'succeeded':
                for text_result in read_result.analyze_result.read_results:
                    for line in text_result.lines:
                        text_blocks.append(line.text)
            
            return '\n'.join(text_blocks)
            
        except Exception as e:
            logger.error(f"Error en Azure Vision OCR: {e}")
            return ""
    
    def get_provider_name(self) -> str:
        return "Azure Vision"

class OCRManager:
    """Gestor de proveedores OCR con fallback inteligente"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers = self._initialize_providers()
        
    def _initialize_providers(self) -> List[OCRProvider]:
        """Inicializa proveedores según configuración"""
        providers = []
        
        # Obtener orden de proveedores de variable de entorno
        provider_order = os.environ.get('OCR_PROVIDER', 'tesseract,google_vision,aws_textract,azure_vision').split(',')
        
        provider_classes = {
            'tesseract': TesseractProvider,
            'google_vision': GoogleVisionProvider,
            'aws_textract': AWSTextractProvider,
            'azure_vision': AzureVisionProvider
        }
        
        for provider_name in provider_order:
            provider_name = provider_name.strip()
            if provider_name in provider_classes:
                try:
                    provider = provider_classes[provider_name]()
                    if provider.is_available():
                        providers.append(provider)
                        self.logger.info(f"✅ Proveedor OCR disponible: {provider.get_provider_name()}")
                    else:
                        self.logger.debug(f"❌ Proveedor OCR no disponible: {provider_name}")
                except Exception as e:
                    self.logger.warning(f"Error inicializando proveedor {provider_name}: {e}")
        
        return providers
    
    def get_available_providers(self) -> List[str]:
        """Retorna lista de proveedores disponibles"""
        return [provider.get_provider_name() for provider in self.providers]
    
    def extract_text_from_image(self, image: Image.Image, language: str = 'spa') -> tuple[str, str]:
        """
        Extrae texto de imagen usando el mejor proveedor disponible.
        
        Returns:
            tuple: (texto_extraído, proveedor_usado)
        """
        if not self.providers:
            self.logger.warning("⚠️ No hay proveedores OCR disponibles")
            return "", "none"
        
        max_retries = int(os.environ.get('MAX_OCR_RETRIES', '3'))
        
        for provider in self.providers:
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"🔍 Intentando OCR con {provider.get_provider_name()} (intento {attempt + 1})")
                    
                    text = provider.extract_text_from_image(image, language)
                    
                    if text.strip():
                        self.logger.info(f"✅ OCR exitoso con {provider.get_provider_name()}: {len(text)} caracteres")
                        return text, provider.get_provider_name()
                    else:
                        self.logger.warning(f"⚠️ {provider.get_provider_name()} no extrajo texto")
                        
                except Exception as e:
                    self.logger.warning(f"❌ Error en {provider.get_provider_name()} (intento {attempt + 1}): {e}")
                    
                    if attempt < max_retries - 1:
                        continue  # Reintentar
                    else:
                        break  # Probar siguiente proveedor
        
        self.logger.error("❌ Todos los proveedores OCR fallaron")
        return "", "failed"
    
    def has_available_providers(self) -> bool:
        """Verifica si hay al menos un proveedor disponible"""
        return len(self.providers) > 0 