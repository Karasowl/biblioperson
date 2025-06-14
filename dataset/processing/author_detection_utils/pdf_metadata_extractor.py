"""
Extractor de metadatos de autor desde archivos PDF.
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfpage import PDFPage
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

class PDFMetadataExtractor:
    """
    Extrae metadatos de autor desde archivos PDF usando PyMuPDF o PDFMiner.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backend = self._select_backend()
        
    def _select_backend(self) -> str:
        """Selecciona el backend disponible para extracción."""
        if PYMUPDF_AVAILABLE:
            self.logger.info("Usando PyMuPDF para extracción de metadatos")
            return "pymupdf"
        elif PDFMINER_AVAILABLE:
            self.logger.info("Usando PDFMiner para extracción de metadatos")
            return "pdfminer"
        else:
            self.logger.warning("No hay backend PDF disponible. Instale pymupdf o pdfminer.six")
            return "none"
    
    def extract_author_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extrae metadatos de autor desde un archivo PDF.
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con información del autor o None
        """
        if self.backend == "none":
            return None
            
        try:
            path = Path(file_path)
            if not path.exists() or path.suffix.lower() != '.pdf':
                return None
                
            if self.backend == "pymupdf":
                return self._extract_with_pymupdf(str(path))
            elif self.backend == "pdfminer":
                return self._extract_with_pdfminer(str(path))
                
        except Exception as e:
            self.logger.error(f"Error extrayendo metadatos de {file_path}: {e}")
            return None
    
    def _extract_with_pymupdf(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extrae metadatos usando PyMuPDF."""
        try:
            doc = pymupdf.open(file_path)
            metadata = doc.metadata
            doc.close()
            
            # Buscar campos de autor
            author_fields = ['author', 'creator', 'producer']
            authors_found = []
            
            for field in author_fields:
                value = metadata.get(field, '').strip()
                if value and self._is_valid_author(value):
                    authors_found.append({
                        'name': self._clean_author_name(value),
                        'source': f'pdf_metadata_{field}',
                        'confidence': 0.9 if field == 'author' else 0.8
                    })
            
            if authors_found:
                # Retornar el autor con mayor confianza
                best_author = max(authors_found, key=lambda x: x['confidence'])
                return {
                    'name': best_author['name'],
                    'confidence': best_author['confidence'],
                    'method': 'pdf_metadata',
                    'details': {
                        'source_field': best_author['source'],
                        'all_metadata': metadata,
                        'all_authors_found': authors_found
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error con PyMuPDF: {e}")
            
        return None
    
    def _extract_with_pdfminer(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extrae metadatos usando PDFMiner."""
        try:
            with open(file_path, 'rb') as fp:
                parser = PDFParser(fp)
                doc = PDFDocument(parser)
                
                if not doc.info:
                    return None
                    
                # PDFMiner puede tener múltiples diccionarios de info
                all_metadata = {}
                for info in doc.info:
                    all_metadata.update(info)
                
                # Buscar campos de autor
                author_fields = ['Author', 'Creator', 'Producer']
                authors_found = []
                
                for field in author_fields:
                    value = all_metadata.get(field, b'')
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore').strip()
                        except:
                            continue
                    
                    if value and self._is_valid_author(value):
                        authors_found.append({
                            'name': self._clean_author_name(value),
                            'source': f'pdf_metadata_{field.lower()}',
                            'confidence': 0.9 if field == 'Author' else 0.8
                        })
                
                if authors_found:
                    best_author = max(authors_found, key=lambda x: x['confidence'])
                    return {
                        'name': best_author['name'],
                        'confidence': best_author['confidence'],
                        'method': 'pdf_metadata',
                        'details': {
                            'source_field': best_author['source'],
                            'all_authors_found': authors_found
                        }
                    }
                    
        except Exception as e:
            self.logger.error(f"Error con PDFMiner: {e}")
            
        return None
    
    def _is_valid_author(self, value: str) -> bool:
        """Valida si un valor parece ser un nombre de autor válido."""
        if not value or len(value) < 3:
            return False
            
        # Rechazar valores que parecen ser software o URLs
        invalid_patterns = [
            r'^https?://',
            r'^www\.',
            r'\.(com|org|net|pdf)$',
            r'^(Microsoft|Adobe|PDF|Writer|Creator|Producer)',
            r'^(Word|Excel|PowerPoint|Acrobat)',
            r'^\d+$',  # Solo números
            r'^[^a-zA-Z]+$'  # Sin letras
        ]
        
        import re
        for pattern in invalid_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
                
        # Debe tener al menos una letra
        if not re.search(r'[a-zA-Z]', value):
            return False
            
        return True
    
    def _clean_author_name(self, name: str) -> str:
        """Limpia y normaliza el nombre del autor."""
        import re
        
        # Remover caracteres especiales comunes en metadatos
        name = re.sub(r'[_\-\.\,]+', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        # Capitalizar palabras
        words = name.split()
        cleaned_words = []
        
        for word in words:
            if len(word) > 2:
                cleaned_words.append(word.capitalize())
            elif word.lower() in ['de', 'del', 'la', 'el', 'y', 'e']:
                cleaned_words.append(word.lower())
            else:
                cleaned_words.append(word)
        
        return ' '.join(cleaned_words) 