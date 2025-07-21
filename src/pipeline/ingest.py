"""
Módulo de ingesta unificado para Biblioperson
Usa unstructured para procesar todos los tipos de documentos
COMPATIBLE con el sistema de configuración existente
"""

import os
import json
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator
import hashlib
from datetime import datetime

# Unstructured imports
try:
    from unstructured.partition.auto import partition
    # Importar partition_pdf solo si es necesario
    try:
        from unstructured.partition.pdf import partition_pdf
        HAS_PDF_PARTITION = True
    except ImportError:
        HAS_PDF_PARTITION = False
        logging.warning("partition_pdf no disponible, usando partition auto")
    
    from unstructured.documents.elements import (
        Title, NarrativeText, ListItem, Table, PageBreak,
        Header, Footer, Image, FigureCaption, Address,
        EmailAddress, Link, Text, Element
    )
    from unstructured.staging.base import convert_to_dict, elements_to_json
    HAS_UNSTRUCTURED = True
except ImportError as e:
    HAS_UNSTRUCTURED = False
    HAS_PDF_PARTITION = False
    logging.warning(f"unstructured no instalado. Error: {e}")

# OCR imports
try:
    import pytesseract
    from PIL import Image as PILImage
    from pdf2image import convert_from_path
    import cv2
    import numpy as np
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    logging.warning("Dependencias OCR no instaladas. OCR no disponible.")

# Markdown conversion
try:
    import pymupdf4llm
    import fitz  # PyMuPDF
    from markdownify import markdownify
    HAS_MARKDOWN_TOOLS = True
except ImportError:
    HAS_MARKDOWN_TOOLS = False
    logging.warning("Herramientas de Markdown no instaladas.")

logger = logging.getLogger(__name__)


class DocumentIngestor:
    """
    Ingesta unificada de documentos compatible con el sistema de configuración existente
    """
    
    def __init__(self, config_dir: str = "dataset/config"):
        """
        Inicializa el ingestor
        
        Args:
            config_dir: Directorio de configuración existente
        """
        self.config_dir = Path(config_dir)
        self.profiles = self._load_profiles()
        
    def _load_profiles(self) -> Dict[str, Any]:
        """Carga los perfiles de configuración existentes"""
        profiles = {}
        
        # Cargar perfiles core
        core_dir = self.config_dir / "profiles" / "core"
        if core_dir.exists():
            for profile_file in core_dir.glob("*.yaml"):
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        profile_data = yaml.safe_load(f)
                        profiles[profile_data['name']] = profile_data
                except Exception as e:
                    logger.warning(f"Error cargando perfil {profile_file}: {e}")
        
        logger.info(f"Cargados {len(profiles)} perfiles de configuración")
        return profiles
    
    def detect_document_type(self, file_path: Path) -> Dict[str, Any]:
        """
        Detecta el tipo de documento y si requiere OCR
        
        Returns:
            Dict con información del tipo de documento
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        result = {
            'file_type': extension,
            'requires_ocr': False,
            'is_digital': True,
            'recommended_profile': 'auto',
            'source_format_group': 'document'
        }
        
        # Determinar grupo de formato según sistema existente
        if extension in ['.json', '.ndjson']:
            result['source_format_group'] = 'json_like'
            result['recommended_profile'] = 'json'
        elif extension in ['.txt', '.md']:
            result['source_format_group'] = 'text_plain'
            result['recommended_profile'] = 'prosa'
        elif extension in ['.pdf', '.docx', '.epub']:
            result['source_format_group'] = 'document'
            
            # Para PDFs, detectar si es escaneado
            if extension == '.pdf' and HAS_OCR:
                result['requires_ocr'] = self._pdf_requires_ocr(file_path)
                result['is_digital'] = not result['requires_ocr']
        
        return result
    
    def _pdf_requires_ocr(self, pdf_path: Path) -> bool:
        """Detecta si un PDF requiere OCR"""
        if not HAS_MARKDOWN_TOOLS:
            return False
            
        try:
            doc = fitz.open(str(pdf_path))
            
            # Verificar las primeras 3 páginas
            text_found = False
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                text = page.get_text().strip()
                
                if len(text) > 50:  # Si hay texto sustancial
                    text_found = True
                    break
            
            doc.close()
            return not text_found
            
        except Exception as e:
            logger.warning(f"Error detectando OCR para {pdf_path}: {e}")
            return False
    
    def extract_to_markdown(self, 
                          file_path: Path,
                          profile_name: Optional[str] = None,
                          custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extrae contenido a Markdown usando configuración existente
        
        Args:
            file_path: Ruta al archivo
            profile_name: Nombre del perfil a usar
            custom_config: Configuración personalizada
            
        Returns:
            Dict con markdown_text, elements y metadatos
        """
        file_path = Path(file_path)
        
        # Detectar tipo de documento
        doc_info = self.detect_document_type(file_path)
        
        # Determinar perfil a usar
        if not profile_name:
            profile_name = doc_info['recommended_profile']
        
        # Obtener configuración
        config = self._get_effective_config(profile_name, custom_config)
        
        logger.info(f"Procesando {file_path} con perfil '{profile_name}'")
        
        # Procesar según el tipo de archivo
        if doc_info['source_format_group'] == 'json_like':
            return self._process_json_like(file_path, config)
        elif doc_info['source_format_group'] == 'text_plain':
            return self._process_text_plain(file_path, config)
        else:
            return self._process_document(file_path, config, doc_info)
    
    def _get_effective_config(self, 
                            profile_name: str, 
                            custom_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combina configuración de perfil con configuración personalizada"""
        
        # Configuración base del perfil
        base_config = self.profiles.get(profile_name, {})
        
        # Si no hay perfil, usar configuración por defecto
        if not base_config:
            base_config = {
                'json_config': {
                    'text_property_paths': ['content', 'text', 'title', 'message', 'body'],
                    'filter_rules': [],
                    'pointer_path': 'id',
                    'date_path': 'date',
                    'root_array_path': '',
                    'treat_as_single_object': False
                }
            }
        
        # Aplicar configuración personalizada
        if custom_config:
            # Merge profundo de configuraciones
            effective_config = self._deep_merge(base_config.copy(), custom_config)
        else:
            effective_config = base_config
        
        return effective_config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge profundo de diccionarios"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def _process_json_like(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa archivos JSON/NDJSON usando configuración existente
        """
        json_config = config.get('json_config', {})
        text_property_paths = json_config.get('text_property_paths', ['text', 'content'])
        
        markdown_parts = []
        elements = []
        
        try:
            if file_path.suffix.lower() == '.ndjson':
                # Procesar NDJSON línea por línea
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if line.strip():
                            try:
                                obj = json.loads(line)
                                text_content = self._extract_text_from_object(obj, text_property_paths)
                                
                                if text_content:
                                    markdown_parts.append(text_content)
                                    elements.append({
                                        'type': 'NarrativeText',
                                        'text': text_content,
                                        'order': line_num,
                                        'metadata': {
                                            'source_line': line_num,
                                            'original_object': obj
                                        }
                                    })
                            except json.JSONDecodeError as e:
                                logger.warning(f"Error en línea {line_num}: {e}")
            else:
                # Procesar JSON regular
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Manejar root_array_path
                root_array_path = json_config.get('root_array_path', '')
                if root_array_path:
                    data = self._get_nested_value(data, root_array_path.split('.'))
                
                # Si es array, procesar cada elemento
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                        text_content = self._extract_text_from_object(item, text_property_paths)
                        if text_content:
                            markdown_parts.append(text_content)
                            elements.append({
                                'type': 'NarrativeText',
                                'text': text_content,
                                'order': idx,
                                'metadata': {
                                    'source_index': idx,
                                    'original_object': item
                                }
                            })
                else:
                    # Objeto único
                    text_content = self._extract_text_from_object(data, text_property_paths)
                    if text_content:
                        markdown_parts.append(text_content)
                        elements.append({
                            'type': 'NarrativeText',
                            'text': text_content,
                            'order': 0,
                            'metadata': {
                                'original_object': data
                            }
                        })
        
        except Exception as e:
            logger.error(f"Error procesando {file_path}: {e}")
            return {
                'markdown_text': '',
                'elements': [],
                'metadata': {'error': str(e)}
            }
        
        return {
            'markdown_text': '\n\n'.join(markdown_parts),
            'elements': elements,
            'metadata': {
                'total_objects': len(elements),
                'source_file': str(file_path),
                'config_used': json_config
            }
        }
    
    def _extract_text_from_object(self, obj: Dict[str, Any], text_paths: List[str]) -> str:
        """
        Extrae texto de un objeto JSON usando las rutas configuradas
        Compatible con el sistema existente
        """
        for path in text_paths:
            try:
                # Soporte para dot notation
                value = self._get_nested_value(obj, path.split('.'))
                
                if value is not None:
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                    elif isinstance(value, (int, float)):
                        return str(value)
                    elif isinstance(value, list):
                        # Concatenar elementos de lista si son strings
                        text_items = []
                        for item in value:
                            if isinstance(item, str) and item.strip():
                                text_items.append(item.strip())
                            elif isinstance(item, dict):
                                # Si es objeto, intentar extraer texto recursivamente
                                nested_text = self._extract_text_from_object(item, text_paths)
                                if nested_text:
                                    text_items.append(nested_text)
                        
                        if text_items:
                            return ' '.join(text_items)
            
            except (KeyError, TypeError, AttributeError):
                continue
        
        return ''
    
    def _get_nested_value(self, obj: Any, path: List[str]) -> Any:
        """Obtiene valor anidado usando path de keys"""
        current = obj
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                try:
                    current = current[int(key)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
        return current
    
    def _process_text_plain(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa archivos de texto plano"""
        try:
            # Detectar encoding
            encoding = config.get('converter_config', {}).get('text_encoding', 'utf-8')
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Crear elemento único
            elements = [{
                'type': 'NarrativeText',
                'text': content,
                'order': 0,
                'metadata': {
                    'encoding_used': encoding
                }
            }]
            
            return {
                'markdown_text': content,
                'elements': elements,
                'metadata': {
                    'source_file': str(file_path),
                    'encoding': encoding
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando texto plano {file_path}: {e}")
            return {
                'markdown_text': '',
                'elements': [],
                'metadata': {'error': str(e)}
            }
    
    def _process_document(self, 
                         file_path: Path, 
                         config: Dict[str, Any], 
                         doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa documentos usando unstructured"""
        
        if not HAS_UNSTRUCTURED:
            logger.error("unstructured no disponible para procesar documentos")
            return {
                'markdown_text': '',
                'elements': [],
                'metadata': {'error': 'unstructured no instalado'}
            }
        
        try:
            # Configurar estrategia de partición
            partition_kwargs = {
                'filename': str(file_path),
                'include_page_breaks': True,
                'infer_table_structure': True
            }
            
            # Si requiere OCR
            if doc_info.get('requires_ocr', False) and HAS_OCR:
                partition_kwargs['strategy'] = 'ocr_only'
                partition_kwargs['ocr_languages'] = ['spa', 'eng']  # Español e inglés
            else:
                partition_kwargs['strategy'] = 'auto'
            
            # Particionar documento
            logger.info(f"Particionando {file_path} con kwargs: {partition_kwargs}")
            elements = []
            
            try:
                elements = partition(**partition_kwargs)
                logger.info(f"Partición completada: {len(elements)} elementos encontrados")
            except Exception as partition_error:
                error_msg = str(partition_error)
                logger.warning(f"Error en partición con unstructured: {error_msg}")
                
                # Si es error de pdfminer o similar, usar fallback inmediatamente
                if any(keyword in error_msg.lower() for keyword in ['pdfminer', 'psexceptions', 'pdf']):
                    logger.info("Error relacionado con PDF, usando fallback PyMuPDF")
                    elements = []  # Forzar fallback
                else:
                    # Para otros errores, re-lanzar
                    raise partition_error
            
            # Si no se extrajeron elementos y es un PDF, intentar fallback con PyMuPDF
            if len(elements) == 0 and file_path.suffix.lower() == '.pdf' and HAS_MARKDOWN_TOOLS:
                logger.warning(f"Fallback: intentando extraer texto con PyMuPDF para {file_path}")
                try:
                    import fitz
                    doc = fitz.open(str(file_path))
                    fallback_text = ""
                    
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        page_text = page.get_text()
                        if page_text.strip():
                            fallback_text += f"\n\n--- Página {page_num + 1} ---\n\n{page_text}"
                    
                    doc.close()
                    
                    if fallback_text.strip():
                        logger.info(f"Fallback exitoso: {len(fallback_text)} caracteres extraídos")
                        # Crear elemento único con el texto extraído
                        elements = [type('FallbackElement', (), {
                            'text': fallback_text.strip(),
                            '__class__': type('NarrativeText', (), {}),
                            '__str__': lambda: fallback_text.strip(),
                            'metadata': None
                        })()]
                        
                except Exception as fallback_error:
                    logger.error(f"Error en fallback PyMuPDF: {fallback_error}")
            
            # Convertir elementos a formato unificado
            unified_elements = []
            markdown_parts = []
            
            for idx, element in enumerate(elements):
                # Obtener metadatos de forma segura
                element_metadata = getattr(element, 'metadata', None)
                safe_metadata = {}
                
                if element_metadata:
                    # Si es un objeto ElementMetadata, acceder a sus atributos
                    safe_metadata['page_number'] = getattr(element_metadata, 'page_number', None)
                    safe_metadata['coordinates'] = getattr(element_metadata, 'coordinates', None)
                    safe_metadata['filename'] = getattr(element_metadata, 'filename', None)
                
                element_dict = {
                    'type': element.__class__.__name__,
                    'text': str(element).strip(),
                    'order': idx,
                    'metadata': {
                        'element_id': getattr(element, 'id', None),
                        **safe_metadata
                    }
                }
                
                if element_dict['text']:
                    unified_elements.append(element_dict)
                    
                    # Convertir a markdown según el tipo
                    if isinstance(element, Title):
                        markdown_parts.append(f"# {element_dict['text']}")
                    elif isinstance(element, ListItem):
                        markdown_parts.append(f"- {element_dict['text']}")
                    else:
                        markdown_parts.append(element_dict['text'])
            
            return {
                'markdown_text': '\n\n'.join(markdown_parts),
                'elements': unified_elements,
                'metadata': {
                    'source_file': str(file_path),
                    'total_elements': len(unified_elements),
                    'used_ocr': doc_info.get('requires_ocr', False),
                    'unstructured_strategy': partition_kwargs.get('strategy', 'auto')
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando documento {file_path}: {e}")
            return {
                'markdown_text': '',
                'elements': [],
                'metadata': {'error': str(e)}
            }
    
    def process_file(self, 
                    file_path: Union[str, Path],
                    profile_name: Optional[str] = None,
                    custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Método principal para procesar un archivo
        
        Args:
            file_path: Ruta al archivo
            profile_name: Perfil de configuración a usar
            custom_config: Configuración personalizada
            
        Returns:
            Dict con el contenido procesado
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Extraer a markdown
        result = self.extract_to_markdown(file_path, profile_name, custom_config)
        
        # Agregar metadatos del archivo
        file_stats = file_path.stat()
        result['metadata'].update({
            'file_size': file_stats.st_size,
            'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            'file_hash': self._calculate_file_hash(file_path)
        })
        
        return result
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula hash SHA256 del archivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Funciones de conveniencia para mantener compatibilidad
def detect_document_type(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Función de conveniencia para detectar tipo de documento"""
    ingestor = DocumentIngestor()
    return ingestor.detect_document_type(Path(file_path))


def extract_to_markdown(file_path: Union[str, Path], 
                       profile_name: Optional[str] = None,
                       custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Función de conveniencia para extraer a markdown"""
    ingestor = DocumentIngestor()
    return ingestor.extract_to_markdown(Path(file_path), profile_name, custom_config)


def process_file(file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
    """Función de conveniencia para procesar archivo"""
    ingestor = DocumentIngestor()
    return ingestor.process_file(file_path, **kwargs)


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python ingest.py <archivo> [perfil]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = process_file(file_path, profile_name=profile)
        
        print(f"Archivo procesado: {file_path}")
        print(f"Elementos extraídos: {len(result['elements'])}")
        print(f"Longitud del markdown: {len(result['markdown_text'])} caracteres")
        print(f"Metadatos: {result['metadata']}")
        
        # Mostrar primeros elementos
        print("\nPrimeros 3 elementos:")
        for i, element in enumerate(result['elements'][:3]):
            print(f"{i+1}. Tipo: {element['type']}")
            print(f"   Texto: {element['text'][:100]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 