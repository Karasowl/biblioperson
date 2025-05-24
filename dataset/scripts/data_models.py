from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class ProcessedContentItem:
    """
    Dataclass representing a single processed content item (segment),
    ready for output to NDJSON. This structure aligns with the fields
    defined in docs/NDJSON_ESPECIFICACION.md.
    """
    # --- Campos Obligatorios sin valor por defecto --- (Deben ir primero)
    id_segmento: str  # UUID string, generado durante el proceso ETL.
    id_documento_fuente: str # Identificador único para el documento original.
    idioma_documento: str # Código ISO 639-1 (ej. "es", "en").
    texto_segmento: str
    tipo_segmento: str # Vocabulario controlado (ej. "parrafo", "titulo_h1").
    orden_segmento_documento: int # Número secuencial global del segmento.
    longitud_caracteres_segmento: int
    timestamp_procesamiento: str # Fecha y hora ISO 8601 del procesamiento.

    # --- Campos Opcionales o con valor por defecto --- 
    # Metadatos del Documento Fuente
    ruta_archivo_original: Optional[str] = None
    hash_documento_original: Optional[str] = None # SHA256 del archivo original.
    titulo_documento: Optional[str] = None
    autor_documento: Optional[str] = None
    fecha_publicacion_documento: Optional[str] = None # Formato YYYY-MM-DD o YYYY.
    editorial_documento: Optional[str] = None
    isbn_documento: Optional[str] = None
    # Para metadatos adicionales del documento fuente.
    metadatos_adicionales_fuente: Dict[str, Any] = field(default_factory=dict)

    # Metadatos del Segmento
    # Objeto JSON que describe la posición del segmento en la estructura.
    jerarquia_contextual: Dict[str, Any] = field(default_factory=dict)
    embedding_vectorial: Optional[List[float]] = None # Podría generarse en un paso posterior.

    # Metadatos del Proceso ETL
    version_pipeline_etl: Optional[str] = None
    nombre_segmentador_usado: Optional[str] = None
    # Notas o advertencias específicas generadas.
    notas_procesamiento_segmento: Optional[str] = None

@dataclass
class BatchContext:
    """
    Contextual information for a batch of files being processed, 
    typically related to a single job defined in jobs_config.json.
    This information is generally constant for all items within that job.
    """
    author_name: str
    language_code: str
    origin_type_name: str # General type for the source of content in this batch (e.g., "Telegram Archive", "EGW Books")
    
    acquisition_date: Optional[str] = None  # Expected format: YYYY-MM-DD
    force_null_publication_date: bool = False # If true, publication_date for all items in this batch will be set to None