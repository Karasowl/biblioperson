"""Loader para archivos JSON con soporte para filtrado y extracción de contenido."""

import json
import logging
import re
from pathlib import Path
from typing import Iterator, Dict, Any, List, Optional

from .base_loader import BaseLoader
from ...scripts.utils import filter_and_extract_from_json_object

logger = logging.getLogger(__name__)


class JSONLoader(BaseLoader):
    """
    Loader para archivos JSON que soporta:
    - Filtrado de entradas basado en reglas configurables
    - Extracción de texto de propiedades específicas (con dot notation)
    - Manejo de arrays y objetos anidados
    - Concatenación automática de contenido de arrays
    - Limpieza automática de caracteres de control problemáticos
    """
    
    def __init__(self, file_path: Path, encoding: str = 'utf-8', **kwargs):
        super().__init__(file_path)
        self.encoding = encoding
        
        # Configuración para extracción de contenido
        self.text_property_paths = kwargs.get('text_property_paths', ['text', 'content', 'message', 'body'])
        self.filter_rules = kwargs.get('filter_rules', [])
        self.pointer_path = kwargs.get('pointer_path', 'id')
        self.date_path = kwargs.get('date_path', 'date')
        
        # Configuración para manejo de estructura JSON
        self.root_array_path = kwargs.get('root_array_path', None)  # Para JSONs con estructura {"data": [...]}
        self.treat_as_single_object = kwargs.get('treat_as_single_object', False)
        
        # Configuración de filtros de longitud
        self.min_text_length = kwargs.get('min_text_length', None)
        self.max_text_length = kwargs.get('max_text_length', None)
        
        logger.info(f"JSONLoader inicializado para {file_path}")
        logger.debug(f"Configuración: text_paths={self.text_property_paths}, "
                    f"filter_rules={len(self.filter_rules)} reglas, "
                    f"root_array_path={self.root_array_path}")

    def _clean_json_content(self, content: str) -> str:
        """
        LIMPIEZA ULTRA-ROBUSTA de contenido JSON carácter por carácter.
        
        Procesa cada carácter individualmente y mantiene solo aquellos que son
        seguros para JSON, eliminando definitivamente TODOS los caracteres de control.
        """
        logger.info("🧹 INICIANDO LIMPIEZA ULTRA-ROBUSTA carácter por carácter...")
        
        cleaned_chars = []
        total_chars = len(content)
        removed_count = 0
        
        for i, char in enumerate(content):
            char_code = ord(char)
            
            # Mostrar progreso cada 10M caracteres
            if i % 10000000 == 0 and i > 0:
                logger.info(f"🔄 Progreso limpieza: {i:,}/{total_chars:,} caracteres ({i/total_chars*100:.1f}%)")
            
            # CARACTERES VÁLIDOS PARA JSON:
            if (
                # Caracteres imprimibles ASCII (32-126): espacio, letras, números, símbolos
                32 <= char_code <= 126 or
                # Caracteres de control permitidos en JSON: \t(9), \n(10), \r(13)
                char_code in (9, 10, 13) or
                # Caracteres Unicode válidos (> 127)
                char_code > 127
            ):
                cleaned_chars.append(char)
            else:
                # Reemplazar caracteres problemáticos con espacio
                cleaned_chars.append(' ')
                removed_count += 1
        
        cleaned_content = ''.join(cleaned_chars)
        
        logger.info(f"✅ LIMPIEZA ULTRA-ROBUSTA COMPLETADA: {removed_count:,} caracteres problemáticos reemplazados")
        logger.info(f"📊 Tamaño original: {len(content):,} → limpio: {len(cleaned_content):,}")
        
        return cleaned_content

    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo JSON, aplicando filtros y extrayendo contenido.
        
        Returns:
            Dict con 'blocks' y 'document_metadata'
        """
        blocks = []
        document_metadata = {}
        
        try:
            # Leer archivo como texto primero para limpieza
            with self.file_path.open('r', encoding=self.encoding) as f:
                raw_content = f.read()
            
            # Limpiar caracteres de control antes del parsing JSON con método ultra-robusta
            logger.warning(f"🧹 VERSIÓN ULTRA-ROBUSTA v2.0 EJECUTÁNDOSE: {self.file_path}")
            logger.warning(f"🧹 TAMAÑO ARCHIVO ORIGINAL: {len(raw_content):,} caracteres")
            cleaned_content = self._clean_json_content(raw_content)
            
            # Parsear JSON limpio
            # Desactivar modo estricto para permitir caracteres de control residuales dentro de strings
            data = json.loads(cleaned_content, strict=False)
                
            logger.info(f"JSON cargado exitosamente después de limpieza: {self.file_path}")
            
            # Metadatos del documento
            fuente, contexto = self.get_source_info()
            document_metadata = {
                'source_file_path': str(self.file_path.absolute()),
                'file_format': 'json',
                'original_fuente': fuente,
                'original_contexto': contexto,
                'preprocessing_applied': 'control_character_cleaning'
            }
            
            # ✅ LOG: Debugging para fecha
            logger.debug(f"🔍 JSONLoader inicializado para {self.file_path} con date_path='{self.date_path}'")
            
            # Procesar contenido y convertir a bloques
            if self.treat_as_single_object:
                # Tratar todo el JSON como un solo objeto
                processed_items = list(self._process_single_object(data))
            else:
                # Buscar array de objetos para procesar
                processed_items = list(self._process_json_structure(data))
            
            # Convertir items procesados a bloques
            first_date_found = None  # Para agregar a document_metadata
            
            for i, item in enumerate(processed_items):
                block = {
                    'text': item['texto'],
                    'order_in_document': i,
                    'metadata': item['metadata']
                }
                if item.get('fecha'):
                    block['detected_date'] = item['fecha']
                    # ✅ CORRECCIÓN: Guardar la primera fecha para document_metadata
                    if first_date_found is None:
                        first_date_found = item['fecha']
                blocks.append(block)
            
            # ✅ CORRECCIÓN: Agregar fecha a document_metadata si se encontró
            if first_date_found:
                document_metadata['fecha_publicacion_documento'] = first_date_found
                logger.info(f"✅ Fecha agregada a document_metadata: {first_date_found}")
            else:
                logger.debug("❌ No se encontraron fechas en los objetos JSON procesados")
                
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON en {self.file_path}: {e}")
            document_metadata['error'] = f"Error de decodificación JSON: {str(e)}"
        except Exception as e:
            logger.error(f"Error inesperado al cargar {self.file_path}: {e}")
            document_metadata['error'] = f"Error inesperado: {str(e)}"
        
        return {
            'blocks': blocks,
            'document_metadata': document_metadata
        }

    def _process_json_structure(self, data: Any) -> Iterator[Dict[str, Any]]:
        """Procesa la estructura JSON para encontrar objetos a filtrar."""
        
        if isinstance(data, list):
            # El JSON es directamente un array
            logger.debug(f"Procesando array directo con {len(data)} elementos")
            yield from self._process_object_list(data)
            
        elif isinstance(data, dict):
            if self.root_array_path:
                # Buscar array en la ruta especificada
                from ...scripts.utils import get_nested_value
                array_data = get_nested_value(data, self.root_array_path)
                if isinstance(array_data, list):
                    logger.debug(f"Procesando array en '{self.root_array_path}' con {len(array_data)} elementos")
                    yield from self._process_object_list(array_data)
                else:
                    logger.warning(f"No se encontró array en la ruta '{self.root_array_path}'")
            else:
                # Buscar arrays automáticamente en el objeto
                arrays_found = self._find_arrays_in_object(data)
                if arrays_found:
                    largest_array = max(arrays_found, key=lambda x: len(x[1]))
                    logger.debug(f"Procesando array más grande encontrado: '{largest_array[0]}' con {len(largest_array[1])} elementos")
                    yield from self._process_object_list(largest_array[1])
                else:
                    # Tratar el objeto completo como un solo elemento
                    logger.debug("No se encontraron arrays, procesando como objeto único")
                    yield from self._process_single_object(data)
        else:
            logger.warning(f"Estructura JSON no soportada: {type(data)}")

    def _find_arrays_in_object(self, obj: Dict[str, Any]) -> List[tuple]:
        """Encuentra arrays en el objeto JSON."""
        arrays = []
        
        def _search_recursive(current_obj, path=""):
            if isinstance(current_obj, dict):
                for key, value in current_obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, list) and len(value) > 0:
                        # Verificar si es un array de objetos (no de primitivos)
                        if isinstance(value[0], dict):
                            arrays.append((current_path, value))
                    elif isinstance(value, dict):
                        _search_recursive(value, current_path)
        
        _search_recursive(obj)
        return arrays

    def _process_object_list(self, objects: List[Any]) -> Iterator[Dict[str, Any]]:
        """Procesa una lista de objetos JSON aplicando filtros."""
        processed_count = 0
        filtered_count = 0
        
        for i, obj in enumerate(objects):
            if not isinstance(obj, dict):
                logger.debug(f"Saltando elemento {i}: no es un objeto")
                continue
                
            # Convertir reglas de filtro al formato esperado por utils.py
            converted_rules = []
            for rule in self.filter_rules:
                converted_rule = {
                    'path': rule.get('field', ''),
                    'op': rule.get('operator', 'eq'),
                    'value': rule.get('value', ''),
                    'exclude': rule.get('negate', False)
                }
                converted_rules.append(converted_rule)
            
            # Aplicar filtros y extraer contenido
            result = filter_and_extract_from_json_object(
                json_object=obj,
                text_property_paths=self.text_property_paths,
                filter_rules=converted_rules,
                pointer_path=self.pointer_path,
                date_path=self.date_path,
                min_text_length=self.min_text_length,
                max_text_length=self.max_text_length
            )
            
            if result is None:
                filtered_count += 1
                continue
                
            # Convertir al formato esperado por el pipeline
            yield self._format_output(result, i)
            processed_count += 1
        
        logger.info(f"Procesamiento completado: {processed_count} objetos procesados, {filtered_count} filtrados")

    def _process_single_object(self, obj: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Procesa un solo objeto JSON."""
        # Convertir reglas de filtro al formato esperado por utils.py
        converted_rules = []
        for rule in self.filter_rules:
            converted_rule = {
                'path': rule.get('field', ''),
                'op': rule.get('operator', 'eq'),
                'value': rule.get('value', ''),
                'exclude': rule.get('negate', False)
            }
            converted_rules.append(converted_rule)
        
        result = filter_and_extract_from_json_object(
            json_object=obj,
            text_property_paths=self.text_property_paths,
            filter_rules=converted_rules,
            pointer_path=self.pointer_path,
            date_path=self.date_path,
            min_text_length=self.min_text_length,
            max_text_length=self.max_text_length
        )
        
        if result is not None:
            yield self._format_output(result, 0)
        else:
            logger.info("Objeto único filtrado por las reglas configuradas")

    def _format_output(self, result: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Formatea el resultado para el pipeline de procesamiento."""
        date_candidate = result.get('date_candidate')
        
        # ✅ LOG: Debugging detallado para fechas
        if date_candidate:
            logger.debug(f"✅ Fecha extraída del objeto {index}: {date_candidate}")
        else:
            logger.debug(f"❌ No se extrajo fecha del objeto {index}")
            
        return {
            'texto': result['text'],
            'fecha': date_candidate,
            'fuente': str(self.file_path),
            'contexto': f"JSON objeto {index}",
            'metadata': {
                'pointer': result.get('pointer'),
                'raw_data': result.get('raw_data', {}),
                'loader_type': 'json',
                'object_index': index
            }
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Retorna metadatos del archivo JSON."""
        try:
            with self.file_path.open('r', encoding=self.encoding) as f:
                data = json.load(f)
            
            metadata = {
                'file_type': 'json',
                'encoding': self.encoding,
                'file_size': self.file_path.stat().st_size,
            }
            
            # Analizar estructura
            if isinstance(data, list):
                metadata['structure'] = 'array'
                metadata['total_objects'] = len(data)
            elif isinstance(data, dict):
                metadata['structure'] = 'object'
                arrays = self._find_arrays_in_object(data)
                if arrays:
                    metadata['arrays_found'] = [(path, len(arr)) for path, arr in arrays]
                    metadata['largest_array'] = max(arrays, key=lambda x: len(x[1]))[0]
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error obteniendo metadatos de {self.file_path}: {e}")
            return {'file_type': 'json', 'error': str(e)} 