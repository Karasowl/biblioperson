from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class ProcessedContentItem:
    """
    Dataclass representing a single processed content item (segment),
    ready for output to NDJSON. Clean structure with English field names.
    """
    # --- Required Fields (no defaults) --- 
    segment_id: str  # UUID string, generated during ETL process
    document_id: str  # Unique identifier for the source document
    document_language: str  # ISO 639-1 code (e.g. "es", "en")
    text: str  # The actual text content of the segment
    segment_type: str  # Controlled vocabulary (e.g. "paragraph", "heading_h1")
    segment_order: int  # Sequential number of this segment in the document
    text_length: int  # Character count of the text
    processing_timestamp: str  # ISO 8601 timestamp when processed

    # --- Optional Fields ---
    # Source Document Metadata
    source_file_path: Optional[str] = None
    document_hash: Optional[str] = None  # SHA256 of original file
    document_title: Optional[str] = None
    document_author: Optional[str] = None
    publication_date: Optional[str] = None  # Format YYYY-MM-DD or YYYY
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    
    # Additional source metadata (consolidated, no duplicates)
    additional_metadata: Dict[str, Any] = field(default_factory=dict)

    # ETL Process Metadata (minimal)
    pipeline_version: Optional[str] = None
    segmenter_used: Optional[str] = None

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