from datetime import datetime
import re
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
import pandas as pd

from .base_loader import BaseLoader
from dataset.scripts.converters import _calculate_sha256

class ExcelLoader(BaseLoader):
    """Loader para archivos Excel (.xlsx, .xls)."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader para archivos Excel.
        
        Args:
            file_path: Ruta al archivo Excel
            tipo: Tipo de contenido ('escritos', 'poemas', 'canciones')
            encoding: Codificación para las cadenas de texto
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
        Carga y procesa el archivo Excel.
        
        Returns:
            Iterator[Dict[str, Any]]: Documentos procesados como bloques de texto
        """
        fuente, contexto = self.get_source_info()
        fecha = self._extract_date_from_filename()
        
        try:
            # Detectar automáticamente si es xls o xlsx
            excel_file = pd.ExcelFile(self.file_path)
            file_hash = _calculate_sha256(self.file_path)
            document_metadata: DocumentMetadata = {
                "nombre_archivo": self.file_path.name,
                "ruta_archivo": str(self.file_path.resolve()),
                "extension_archivo": self.file_path.suffix,
                "titulo_documento": self.file_path.stem, # Default title
                "hash_documento_original": file_hash,
                "metadatos_adicionales_fuente": {
                    "excel_sheets": list(excel_file.sheet_names)
                }
            }
            
            # Procesar cada hoja
            for sheet_name in excel_file.sheet_names:
                # Leer la hoja
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Pasar nombre de la hoja como título
                yield {
                    'text': sheet_name,
                    'is_heading': True,
                    'heading_level': 1,
                    'fuente': fuente,
                    'contexto': contexto,
                    'fecha': fecha
                }
                
                # Procesar las columnas como cabeceras
                headers = df.columns.tolist()
                if headers:
                    yield {
                        'text': ', '.join(str(h) for h in headers),
                        'is_heading': True,
                        'heading_level': 2,
                        'fuente': fuente,
                        'contexto': contexto,
                        'fecha': fecha
                    }
                
                # Procesar cada fila
                for _, row in df.iterrows():
                    # Convertir la fila a texto
                    row_text = ' | '.join(str(v) for v in row.values if pd.notna(v))
                    if row_text:
                        yield {
                            'text': row_text,
                            'is_heading': False,
                            'sheet_name': sheet_name,
                            'fuente': fuente,
                            'contexto': contexto,
                            'fecha': fecha
                        }
                        
        except Exception as e:
            print(f"Error al procesar archivo Excel {self.file_path}: {e}")
            raise
            
    def _process_table_format(self, df: pd.DataFrame) -> Iterator[Dict[str, Any]]:
        """
        Procesa un DataFrame como una tabla estructurada (alternativa).
        
        Args:
            df: DataFrame de pandas con los datos
            
        Returns:
            Iterator con los elementos procesados
        """
        fuente, contexto = self.get_source_info()
        
        # Crear una representación más elaborada de la tabla
        for i, row in df.iterrows():
            row_dict = {
                'row_number': i + 1,
                'is_heading': False,
                'fuente': fuente,
                'contexto': contexto,
                'columns': {}
            }
            
            # Añadir cada columna
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    row_dict['columns'][str(col)] = str(value)
                    
            # Si hay algún contenido, yield
            if row_dict['columns']:
                yield row_dict