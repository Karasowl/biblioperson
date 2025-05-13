from datetime import datetime
import re
import csv
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from .base_loader import BaseLoader

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
        
    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Carga y procesa el archivo CSV.
        
        Returns:
            Iterator[Dict[str, Any]]: Documentos procesados como bloques de texto
        """
        fuente, contexto = self.get_source_info()
        fecha = self._extract_date_from_filename()
        
        # Intentar detectar el delimitador automáticamente
        delimiter = self._detect_delimiter()
        
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                # Leer el CSV
                reader = csv.reader(f, delimiter=delimiter, quotechar=self.quotechar)
                
                # Obtener los encabezados
                try:
                    headers = next(reader)
                    
                    # Generar un bloque para los encabezados
                    yield {
                        'text': ', '.join(headers),
                        'is_heading': True,
                        'heading_level': 1,
                        'fuente': fuente,
                        'contexto': contexto,
                        'fecha': fecha
                    }
                    
                    # Procesar cada fila
                    for row_num, row in enumerate(reader, 1):
                        # Crear texto de la fila
                        row_text = []
                        
                        # Formatear como "campo: valor" si hay encabezados
                        for i, value in enumerate(row):
                            if i < len(headers) and value.strip():
                                field_name = headers[i].strip()
                                if field_name:
                                    row_text.append(f"{field_name}: {value.strip()}")
                                else:
                                    row_text.append(value.strip())
                        
                        if row_text:
                            yield {
                                'text': '; '.join(row_text),
                                'is_heading': False,
                                'row_number': row_num,
                                'fuente': fuente,
                                'contexto': contexto,
                                'fecha': fecha
                            }
                            
                except StopIteration:
                    # Si el archivo está vacío
                    pass
                    
        except Exception as e:
            print(f"Error al procesar CSV {self.file_path}: {e}")
            # Si falla con el encoding especificado, intentar con otros comunes
            if "codec can't decode" in str(e):
                for enc in ['latin1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(self.file_path, 'r', encoding=enc) as f:
                            print(f"Reintentando con encoding {enc}")
                            # Reintentar con nuevo encoding
                            self.encoding = enc
                            # Llamar recursivamente a load() con el nuevo encoding
                            return self.load()
                    except UnicodeDecodeError:
                        continue
            raise 