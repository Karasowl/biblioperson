"""
Utilidades avanzadas para detección de autores.
"""

from .header_footer_filter import HeaderFooterFilter
from .pdf_metadata_extractor import PDFMetadataExtractor
from .spacy_ner_validator import SpacyNERValidator
from .known_authors_validator import KnownAuthorsValidator

__all__ = [
    'HeaderFooterFilter',
    'PDFMetadataExtractor', 
    'SpacyNERValidator',
    'KnownAuthorsValidator'
] 