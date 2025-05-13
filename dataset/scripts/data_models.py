from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ProcessedContentItem:
    """
    Dataclass representing a single processed content item, ready for output to NDJSON.
    This structure aligns with the fields needed for eventual database insertion.
    """
    author_name: str
    origin_type_name: str
    specific_source_name: str # e.g., original filename, or a name derived from a JSON object's ID
    normalized_text_md: str
    language_code: str  # e.g., 'es', 'en'
    
    original_file_path_or_url: Optional[str] = None
    acquisition_date: Optional[str] = None  # Expected format: YYYY-MM-DD
    title: Optional[str] = None
    publication_date: Optional[str] = None  # Expected format: YYYY-MM-DD
    source_document_pointer: Optional[str] = None # e.g., Original ID, bibliographic reference
    additional_metadata_json: Dict[str, Any] = field(default_factory=dict)
    original_content_id: Optional[str] = None # A unique ID from the source data, if available

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