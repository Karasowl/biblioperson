"""
Módulo de modos de salida para el sistema de procesamiento de documentos.
Define los modos 'generic' y 'biblioperson' con diferentes niveles de metadatos.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class OutputMode(Enum):
    """Modos de salida disponibles para el procesamiento de documentos."""
    GENERIC = "generic"
    BIBLIOPERSON = "biblioperson"

class OutputModeSerializer:
    """Serializador que maneja los diferentes modos de salida."""
    
    def __init__(self, mode: OutputMode):
        """
        Inicializa el serializador con un modo específico.
        
        Args:
            mode: Modo de salida a usar
        """
        self.mode = mode
        self.logger = logging.getLogger(__name__)
    
    def serialize_segment(self, segment: Any, document_metadata: Optional[Dict[str, Any]] = None, 
                         segment_index: int = 0) -> Dict[str, Any]:
        """
        Serializa un segmento según el modo de salida configurado.
        
        Args:
            segment: Segmento a serializar (ProcessedContentItem o dict)
            document_metadata: Metadatos del documento
            segment_index: Índice del segmento
            
        Returns:
            Diccionario con el segmento serializado
        """
        if self.mode == OutputMode.GENERIC:
            return self._serialize_generic(segment, document_metadata, segment_index)
        elif self.mode == OutputMode.BIBLIOPERSON:
            return self._serialize_biblioperson(segment, document_metadata, segment_index)
        else:
            raise ValueError(f"Modo de salida no soportado: {self.mode}")
    
    def _serialize_generic(self, segment: Any, document_metadata: Optional[Dict[str, Any]] = None, 
                          segment_index: int = 0) -> Dict[str, Any]:
        """
        Serialización en modo genérico: solo campos esenciales para IA.
        
        Campos incluidos:
        - text: Contenido del segmento
        - type: Tipo de segmento (opcional)
        - order: Orden en el documento (opcional)
        - title: Título del documento (opcional)
        - author: Autor del documento (opcional)
        """
        # Extraer texto del segmento
        if hasattr(segment, 'text'):
            # ProcessedContentItem nuevo
            text = segment.text
            segment_type = getattr(segment, 'segment_type', None)
            segment_order = getattr(segment, 'segment_order', segment_index + 1)
            document_title = getattr(segment, 'document_title', None)
            document_author = getattr(segment, 'document_author', None)
        elif hasattr(segment, 'texto_segmento'):
            # ProcessedContentItem viejo
            text = segment.texto_segmento
            segment_type = getattr(segment, 'tipo_segmento', None)
            segment_order = getattr(segment, 'orden_segmento_documento', segment_index + 1)
            document_title = getattr(segment, 'titulo_documento', None)
            document_author = getattr(segment, 'autor_documento', None)
        else:
            # Diccionario
            text = segment.get('text', '')
            segment_type = segment.get('type', None)
            segment_order = segment.get('order', segment_index + 1)
            document_title = segment.get('title', None)
            document_author = segment.get('author', None)
        
        # Usar metadatos del documento si no están en el segmento
        if not document_title and document_metadata:
            document_title = document_metadata.get('title', None)
        if not document_author and document_metadata:
            document_author = document_metadata.get('author', None)
        
        # Estructura mínima para modo genérico
        result = {
            "text": text
        }
        
        # Añadir campos opcionales solo si tienen valor
        if segment_type:
            result["type"] = segment_type
        if segment_order:
            result["order"] = segment_order
        if document_title:
            result["title"] = document_title
        if document_author:
            result["author"] = document_author
        
        return result
    
    def _serialize_biblioperson(self, segment: Any, document_metadata: Optional[Dict[str, Any]] = None, 
                               segment_index: int = 0) -> Dict[str, Any]:
        """
        Serialización en modo Biblioperson: estructura completa con todos los metadatos.
        
        Incluye todos los campos necesarios para el sistema Biblioperson:
        - Identificadores únicos
        - Metadatos completos del documento
        - Información de procesamiento
        - Hash de deduplicación
        - Estructura de carpetas
        """
        import uuid
        
        # Extraer datos del segmento
        if hasattr(segment, 'text'):
            # ProcessedContentItem nuevo (estructura en inglés)
            segment_data = {
                "segment_id": segment.segment_id,
                "document_id": segment.document_id,
                "document_language": segment.document_language,
                "text": segment.text,
                "segment_type": segment.segment_type,
                "segment_order": segment.segment_order,
                "text_length": segment.text_length,
                "processing_timestamp": segment.processing_timestamp,
                "source_file_path": segment.source_file_path,
                "document_hash": segment.document_hash,
                "document_title": segment.document_title,
                "document_author": segment.document_author,
                "publication_date": segment.publication_date,
                "publisher": segment.publisher,
                "isbn": segment.isbn,
                "additional_metadata": segment.additional_metadata or {},
                "pipeline_version": segment.pipeline_version,
                "segmenter_used": segment.segmenter_used
            }
        elif hasattr(segment, 'texto_segmento'):
            # ProcessedContentItem viejo (compatibilidad hacia atrás)
            segment_metadata = segment.metadatos_adicionales_fuente or {}
            segment_hierarchy = segment.jerarquia_contextual or {}
            
            segment_data = {
                "segment_id": segment.id_segmento,
                "document_id": segment.id_documento_fuente,
                "document_language": segment.idioma_documento,
                "text": segment.texto_segmento,
                "segment_type": segment.tipo_segmento,
                "segment_order": segment.orden_segmento_documento,
                "text_length": segment.longitud_caracteres_segmento,
                "processing_timestamp": segment.timestamp_procesamiento,
                "source_file_path": segment.ruta_archivo_original,
                "document_hash": segment.hash_documento_original,
                "document_title": segment.titulo_documento,
                "document_author": segment.autor_documento,
                "publication_date": segment.fecha_publicacion_documento,
                "publisher": segment.editorial_documento,
                "isbn": segment.isbn_documento,
                "additional_metadata": segment_metadata,
                "pipeline_version": segment.version_pipeline_etl,
                "segmenter_used": segment.nombre_segmentador_usado,
                # Campos legacy para compatibilidad temporal
                "_legacy_hierarchy": segment_hierarchy,
                "_legacy_processing_notes": segment.notas_procesamiento_segmento
            }
        else:
            # Diccionario (compatibilidad hacia atrás)
            timestamp = datetime.now(timezone.utc).isoformat()
            segment_data = {
                "segment_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "document_language": document_metadata.get('language', 'es') if document_metadata else 'es',
                "text": segment.get('text', ''),
                "segment_type": segment.get('type', 'unknown'),
                "segment_order": segment.get('order', segment_index + 1),
                "text_length": len(segment.get('text', '')),
                "processing_timestamp": timestamp,
                "source_file_path": document_metadata.get('source_file_path', '') if document_metadata else '',
                "document_hash": document_metadata.get('document_hash', None) if document_metadata else None,
                "document_title": document_metadata.get('title', '') if document_metadata else '',
                "document_author": document_metadata.get('author', None) if document_metadata else None,
                "publication_date": document_metadata.get('publication_date', None) if document_metadata else None,
                "publisher": document_metadata.get('publisher', None) if document_metadata else None,
                "isbn": document_metadata.get('isbn', None) if document_metadata else None,
                "additional_metadata": segment.get('metadata', {}),
                "pipeline_version": "profile_manager_v4.0_english_clean",
                "segmenter_used": document_metadata.get('segmenter_name', 'unknown') if document_metadata else 'unknown',
                "_legacy_processing_notes": segment.get('notes', None)
            }
        
        # Limpiar campos None/vacíos
        cleaned_data = {k: v for k, v in segment_data.items() if v is not None}
        
        return cleaned_data
    
    def export_segments(self, segments: List[Any], output_file: str, 
                       document_metadata: Optional[Dict[str, Any]] = None,
                       output_format: str = "ndjson") -> None:
        """
        Exporta una lista de segmentos al archivo especificado.
        
        Args:
            segments: Lista de segmentos a exportar
            output_file: Ruta del archivo de salida
            document_metadata: Metadatos del documento
            output_format: Formato de salida ("ndjson" o "json")
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serializar todos los segmentos
        results = []
        for i, segment in enumerate(segments):
            serialized = self.serialize_segment(segment, document_metadata, i)
            results.append(serialized)
        
        # Exportar según el formato
        if output_format.lower() == "json":
            if self.mode == OutputMode.BIBLIOPERSON:
                # En modo Biblioperson, incluir metadatos del documento
                output_data = {
                    "document_metadata": self._clean_document_metadata(document_metadata),
                    "segments": results
                }
            else:
                # En modo genérico, solo los segmentos
                output_data = results
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
        else:
            # Formato NDJSON: una línea por segmento
            with open(output_path, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        self.logger.info(f"Segmentos exportados en modo {self.mode.value} formato {output_format.upper()}: {output_path}")
    
    def _clean_document_metadata(self, document_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Limpia y prepara los metadatos del documento para exportación.
        
        Args:
            document_metadata: Metadatos originales
            
        Returns:
            Metadatos limpios
        """
        if not document_metadata:
            return {}
        
        if self.mode == OutputMode.GENERIC:
            # En modo genérico, solo campos básicos
            return {
                k: v for k, v in document_metadata.items() 
                if k in ['title', 'author', 'language', 'source_file_path'] and v is not None
            }
        else:
            # En modo Biblioperson, todos los metadatos
            return {k: v for k, v in document_metadata.items() if v is not None}


def get_output_mode_from_string(mode_str: str) -> OutputMode:
    """
    Convierte una cadena a OutputMode.
    
    Args:
        mode_str: Cadena con el modo ("generic" o "biblioperson")
        
    Returns:
        OutputMode correspondiente
        
    Raises:
        ValueError: Si el modo no es válido
    """
    mode_str = mode_str.lower().strip()
    
    if mode_str == "generic":
        return OutputMode.GENERIC
    elif mode_str == "biblioperson":
        return OutputMode.BIBLIOPERSON
    else:
        raise ValueError(f"Modo de salida no válido: {mode_str}. Debe ser 'generic' o 'biblioperson'")


def create_serializer(mode: str) -> OutputModeSerializer:
    """
    Crea un serializador para el modo especificado.
    
    Args:
        mode: Modo de salida ("generic" o "biblioperson")
        
    Returns:
        OutputModeSerializer configurado
    """
    output_mode = get_output_mode_from_string(mode)
    return OutputModeSerializer(output_mode) 