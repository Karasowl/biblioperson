from datetime import datetime
import re
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
import PyPDF2

from .base_loader import BaseLoader

class PDFLoader(BaseLoader):
    """Loader para archivos PDF (.pdf)."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader para archivos PDF.
        
        Args:
            file_path: Ruta al archivo PDF
            tipo: Tipo de contenido ('escritos', 'poemas', 'canciones')
            encoding: Codificación (no se usa directamente en PDFs pero se mantiene por consistencia)
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
        
    def _extract_date_from_filename(self) -> Optional[str]:
        """Intenta extraer una fecha del nombre del archivo."""
        # Patrones comunes de fecha en nombres de archivo
        patterns = [
            r'(\d{4})[_-](\d{1,2})[_-](\d{1,2})',  # YYYY-MM-DD o YYYY_MM_DD
            r'(\d{1,2})[_-](\d{1,2})[_-](\d{4})',  # DD-MM-YYYY o DD_MM_YYYY
            r'(\d{4})(\d{2})(\d{2})'              # YYYYMMDD
        ]
        
        filename = self.file_path.stem
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                # Asegurar que sea una fecha válida
                try:
                    if len(match.groups()) == 3:
                        if pattern == patterns[0]:  # YYYY-MM-DD
                            year, month, day = match.groups()
                        elif pattern == patterns[1]:  # DD-MM-YYYY
                            day, month, year = match.groups()
                        else:  # YYYYMMDD
                            year, month, day = match.groups()
                            
                        # Asegurar que los valores son numéricos
                        year, month, day = int(year), int(month), int(day)
                        
                        # Validar rango
                        if 1900 <= year <= datetime.now().year and 1 <= month <= 12 and 1 <= day <= 31:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                except (ValueError, IndexError):
                    continue
                    
        return None
        
    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Carga y procesa el archivo PDF.
        
        Returns:
            Iterator[Dict[str, Any]]: Documentos procesados como bloques de texto
        """
        fuente, contexto = self.get_source_info()
        fecha = self._extract_date_from_filename()
        
        try:
            # Abrir el archivo PDF
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extraer metadatos si existen
                metadata = pdf_reader.metadata
                title = None
                
                if metadata and "/Title" in metadata:
                    title = metadata["/Title"]
                
                # Si hay título, pasar primero
                if title:
                    yield {
                        'text': title,
                        'is_heading': True,
                        'heading_level': 1,
                        'fuente': fuente,
                        'contexto': contexto,
                        'fecha': fecha
                    }
                
                # Procesar cada página
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        
                        if not text:
                            continue
                            
                        # Separar por párrafos
                        paragraphs = text.split('\n\n')
                        
                        for para in paragraphs:
                            if para.strip():
                                yield {
                                    'text': para.strip(),
                                    'is_heading': False,
                                    'page_number': page_num + 1,
                                    'fuente': fuente,
                                    'contexto': contexto,
                                    'fecha': fecha
                                }
                                
                    except Exception as e:
                        print(f"Error al procesar página {page_num + 1} del PDF: {e}")
                
        except Exception as e:
            print(f"Error al abrir el PDF {self.file_path}: {e}")
            raise 