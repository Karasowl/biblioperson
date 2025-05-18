"""Paquete de loaders para diferentes formatos de archivos."""

from .base_loader import BaseLoader
from .markdown_loader import MarkdownLoader
from .ndjson_loader import NDJSONLoader
from .docx_loader import DocxLoader
from .txt_loader import txtLoader
from .pdf_loader import PDFLoader
from .excel_loader import ExcelLoader
from .csv_loader import CSVLoader

__all__ = [
    'BaseLoader',
    'MarkdownLoader',
    'NDJSONLoader',
    'DocxLoader',
    'txtLoader',
    'PDFLoader',
    'ExcelLoader',
    'CSVLoader'
]

# A medida que se implementen loaders, se importarán y agregarán aquí
# Por ejemplo:
# from .text_loader import txtLoader
# from .docx_loader import DocxLoader
# __all__ = ['txtLoader', 'DocxLoader'] 