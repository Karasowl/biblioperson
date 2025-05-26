from datetime import datetime
import re
import csv
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from .base_loader import BaseLoader
from dataset.scripts.converters import _calculate_sha256

class CSVLoader(BaseLoader):
    """Loader para archivos CSV (.csv)."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8', 
                 delimiter: str = ',', quotechar: str = '"'):
        """
        Inicializa el loader para archivos CSV.
        
        Args:
            file_path: Ruta al archivo CSV
            tipo: Tipo de contenido ('escritos', 'poemas', 'canciones')
            encoding: Codificación del archivo
            delimiter: Separador de campos (por defecto ',')
            quotechar: Carácter para encerrar campos con espacios (por defecto '"')
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
        self.delimiter = delimiter
        self.quotechar = quotechar
        
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
        
    def _detect_delimiter(self) -> str:
        """
        Detecta automáticamente el delimitador del archivo CSV.
        
        Returns:
            Delimitador detectado o el valor por defecto
        """
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                sample = f.read(1024)  # Leer una muestra pequeña
                
                # Contar posibles delimitadores
                counts = {
                    ',': sample.count(','),
                    ';': sample.count(';'),
                    '\t': sample.count('\t'),
                    '|': sample.count('|')
                }
                
                # Elegir el más común
                if max(counts.values()) > 0:
                    return max(counts.items(), key=lambda x: x[1])[0]
        except Exception:
            pass
            
        return self.delimiter  # Usar valor por defecto si falla la detección
        
    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo CSV.
        
        Returns:
            Dict[str, Any]: Un diccionario con bloques de contenido y metadatos del documento.
        """
        fuente, contexto = self.get_source_info()
        fecha = self._extract_date_from_filename()
        delimiter = self._detect_delimiter()
        
        blocks = []
        order_in_document = 0
        
        file_hash = _calculate_sha256(self.file_path)
        # Placeholder for actual metadata extraction if possible from CSV
        document_metadata: DocumentMetadata = {
            "nombre_archivo": self.file_path.name,
            "ruta_archivo": str(self.file_path.resolve()),
            "extension_archivo": self.file_path.suffix,
            "titulo_documento": self.file_path.stem, # Default to filename stem
            "hash_documento_original": file_hash,
            # Add other relevant metadata if extractable
        }

        try:
            with open(self.file_path, 'r', encoding=self.encoding, newline='') as f:
                reader = csv.reader(f, delimiter=delimiter, quotechar=self.quotechar)
                headers = []
                try:
                    headers = next(reader)
                    blocks.append({
                        'text': ', '.join(headers),
                        'order_in_document': order_in_document,
                        'block_type': 'csv_header'
                    })
                    order_in_document += 1
                except StopIteration:
                    document_metadata['csv_has_header'] = False
                    return {'blocks': [], 'document_metadata': document_metadata}
                
                document_metadata['csv_has_header'] = True
                document_metadata['csv_headers'] = headers

                for row_num, row in enumerate(reader, 1):
                    if not any(field.strip() for field in row):
                        continue
                        
                    row_texts = []
                    for i, value in enumerate(row):
                        cell_text = value.strip()
                        if i < len(headers):
                            field_name = headers[i].strip()
                            if field_name and cell_text:
                                row_texts.append(f"{field_name}: {cell_text}")
                            elif cell_text:
                                row_texts.append(cell_text)
                        elif cell_text:
                            row_texts.append(cell_text)
                    
                    if row_texts:
                        blocks.append({
                            'text': '; '.join(row_texts),
                            'order_in_document': order_in_document,
                            'block_type': 'csv_row',
                            'csv_row_number': row_num
                        })
                        order_in_document += 1
                            
        except Exception as e:
            error_message = f"Error al procesar CSV {self.file_path}: {str(e)}"
            document_metadata['loader_error'] = error_message
            return {'blocks': blocks, 'document_metadata': document_metadata}

        return {'blocks': blocks, 'document_metadata': document_metadata}