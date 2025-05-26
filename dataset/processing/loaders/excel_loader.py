from datetime import datetime
import re
from pathlib import Path
from typing import Dict, Any, Optional, Iterator, List
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
    
    def _detect_header_row(self, df: pd.DataFrame) -> tuple[bool, int]:
        """
        Detecta si hay una fila de cabeceras válida y en qué posición.
        
        Returns:
            tuple[bool, int]: (tiene_cabeceras_validas, fila_de_cabeceras)
        """
        # Verificar si las columnas actuales son mayormente "Unnamed"
        unnamed_count = sum(1 for col in df.columns if str(col).startswith('Unnamed:'))
        total_cols = len(df.columns)
        
        # Si más del 70% son "Unnamed", probablemente no hay cabeceras válidas
        if unnamed_count / total_cols > 0.7:
            # Buscar una fila que pueda servir como cabecera
            for i in range(min(5, len(df))):  # Revisar las primeras 5 filas
                row = df.iloc[i]
                non_null_count = row.notna().sum()
                # Si la fila tiene al menos 50% de valores no nulos, podría ser cabecera
                if non_null_count / len(row) >= 0.5:
                    return True, i
            return False, -1
        else:
            return True, 0  # Las cabeceras actuales son válidas
    
    def _clean_column_names(self, df: pd.DataFrame, header_row: int = -1) -> pd.DataFrame:
        """
        Limpia los nombres de columnas o usa una fila específica como cabecera.
        
        Args:
            df: DataFrame original
            header_row: Fila a usar como cabecera (-1 para usar columnas actuales)
            
        Returns:
            DataFrame con columnas limpias
        """
        if header_row >= 0:
            # Usar una fila específica como cabecera
            new_headers = []
            header_data = df.iloc[header_row]
            
            for i, value in enumerate(header_data):
                if pd.notna(value) and str(value).strip():
                    new_headers.append(str(value).strip())
                else:
                    new_headers.append(f"Columna_{i+1}")
            
            # Crear nuevo DataFrame sin la fila de cabecera
            new_df = df.iloc[header_row+1:].copy()
            new_df.columns = new_headers
            return new_df.reset_index(drop=True)
        else:
            # Limpiar nombres de columnas existentes
            new_columns = []
            for i, col in enumerate(df.columns):
                col_str = str(col)
                if col_str.startswith('Unnamed:'):
                    new_columns.append(f"Columna_{i+1}")
                else:
                    new_columns.append(col_str)
            
            df_copy = df.copy()
            df_copy.columns = new_columns
            return df_copy
    
    def _format_row_data(self, row: pd.Series, use_column_names: bool = True) -> str:
        """
        Formatea una fila de datos de manera más legible.
        
        Args:
            row: Serie de pandas con los datos de la fila
            use_column_names: Si incluir nombres de columnas en el formato
            
        Returns:
            String formateado con los datos de la fila
        """
        if use_column_names:
            # Formato: "Columna: Valor | Columna2: Valor2"
            row_values = []
            for col_name, value in row.items():
                if pd.notna(value) and str(value).strip():
                    clean_value = str(value).strip()
                    if clean_value:  # Solo agregar si no está vacío
                        row_values.append(f"{col_name}: {clean_value}")
            return ' | '.join(row_values)
        else:
            # Formato simple: "Valor1 | Valor2 | Valor3"
            row_values = []
            for value in row.values:
                if pd.notna(value) and str(value).strip():
                    clean_value = str(value).strip()
                    if clean_value:
                        row_values.append(clean_value)
            return ' | '.join(row_values)
    
    def _read_excel_file(self, file_path: Path, sheet_name: str = None) -> pd.ExcelFile:
        """
        Lee un archivo Excel usando el engine apropiado según la extensión.
        
        Args:
            file_path: Ruta al archivo Excel
            sheet_name: Nombre de la hoja (opcional)
            
        Returns:
            pd.ExcelFile: Objeto ExcelFile de pandas
        """
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.xlsx':
                # Usar openpyxl para archivos .xlsx
                return pd.ExcelFile(file_path, engine='openpyxl')
            elif extension == '.xls':
                # Usar xlrd para archivos .xls
                return pd.ExcelFile(file_path, engine='xlrd')
            else:
                # Intentar detección automática
                return pd.ExcelFile(file_path)
        except Exception as e:
            # Si falla, intentar con el engine alternativo
            try:
                if extension == '.xls':
                    return pd.ExcelFile(file_path, engine='openpyxl')
                else:
                    return pd.ExcelFile(file_path, engine='xlrd')
            except Exception as e2:
                raise Exception(f"No se pudo leer el archivo Excel con ningún engine. Error original: {str(e)}, Error alternativo: {str(e2)}")
        
    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo Excel.
        
        Returns:
            Dict[str, Any]: Un diccionario con bloques de contenido y metadatos del documento.
        """
        fuente, contexto = self.get_source_info()
        fecha = self._extract_date_from_filename()
        
        blocks = []
        order_in_document = 0
        
        file_hash = _calculate_sha256(self.file_path)
        document_metadata = {
            "nombre_archivo": self.file_path.name,
            "ruta_archivo": str(self.file_path.resolve()),
            "extension_archivo": self.file_path.suffix,
            "titulo_documento": self.file_path.stem,
            "hash_documento_original": file_hash,
            "original_fuente": fuente,
            "original_contexto": contexto,
            "detected_date": fecha
        }
        
        try:
            # Usar el método mejorado para leer archivos Excel
            excel_file = self._read_excel_file(self.file_path)
            
            # Agregar información de hojas a los metadatos
            document_metadata["metadatos_adicionales_fuente"] = {
                "excel_sheets": list(excel_file.sheet_names),
                "total_sheets": len(excel_file.sheet_names),
                "excel_engine_used": "openpyxl" if self.file_path.suffix.lower() == '.xlsx' else "xlrd"
            }
            
            # Procesar cada hoja
            for sheet_name in excel_file.sheet_names:
                try:
                    # Leer la hoja sin asumir cabeceras
                    if self.file_path.suffix.lower() == '.xlsx':
                        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, engine='openpyxl')
                    else:
                        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, engine='xlrd')
                    
                    # Detectar si hay cabeceras válidas
                    has_headers, header_row = self._detect_header_row(df_raw)
                    
                    # Si detectamos cabeceras, releer con ellas
                    if has_headers and header_row == 0:
                        if self.file_path.suffix.lower() == '.xlsx':
                            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0, engine='openpyxl')
                        else:
                            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0, engine='xlrd')
                        df = self._clean_column_names(df)
                    elif has_headers and header_row > 0:
                        df = self._clean_column_names(df_raw, header_row)
                    else:
                        # No hay cabeceras válidas, usar números de columna
                        df = df_raw.copy()
                        df.columns = [f"Columna_{i+1}" for i in range(len(df.columns))]
                    
                    # Agregar nombre de la hoja como título
                    blocks.append({
                        'text': f"Hoja: {sheet_name}",
                        'order_in_document': order_in_document,
                        'block_type': 'excel_sheet_title',
                        'is_heading': True,
                        'heading_level': 1,
                        'sheet_name': sheet_name
                    })
                    order_in_document += 1
                    
                    # Solo agregar cabeceras si son significativas
                    if has_headers:
                        header_text = ' | '.join(str(col) for col in df.columns)
                        blocks.append({
                            'text': f"Columnas: {header_text}",
                            'order_in_document': order_in_document,
                            'block_type': 'excel_headers',
                            'is_heading': True,
                            'heading_level': 2,
                            'sheet_name': sheet_name,
                            'excel_headers': list(df.columns)
                        })
                        order_in_document += 1
                    
                    # Procesar cada fila con datos
                    for row_idx, row in df.iterrows():
                        # Verificar si la fila tiene contenido significativo
                        non_null_count = row.notna().sum()
                        if non_null_count == 0:
                            continue  # Saltar filas completamente vacías
                        
                        # Formatear la fila
                        row_text = self._format_row_data(row, use_column_names=has_headers)
                        
                        if row_text:  # Solo agregar si hay contenido
                            blocks.append({
                                'text': row_text,
                                'order_in_document': order_in_document,
                                'block_type': 'excel_row',
                                'is_heading': False,
                                'sheet_name': sheet_name,
                                'excel_row_number': row_idx + 1,
                                'has_headers': has_headers
                            })
                            order_in_document += 1
                            
                except Exception as sheet_error:
                    # Error procesando una hoja específica
                    error_block = {
                        'text': f"Error procesando hoja '{sheet_name}': {str(sheet_error)}",
                        'order_in_document': order_in_document,
                        'block_type': 'excel_error',
                        'is_heading': False,
                        'sheet_name': sheet_name,
                        'error_details': str(sheet_error)
                    }
                    blocks.append(error_block)
                    order_in_document += 1
                    continue
                        
        except Exception as e:
            error_message = f"Error al procesar archivo Excel {self.file_path}: {str(e)}"
            document_metadata['loader_error'] = error_message
            return {'blocks': blocks, 'document_metadata': document_metadata}

        return {'blocks': blocks, 'document_metadata': document_metadata}

    def _process_table_format(self, df: pd.DataFrame, start_order: int = 0) -> List[Dict[str, Any]]:
        """
        Procesa un DataFrame como una tabla estructurada (método auxiliar).
        
        Args:
            df: DataFrame de pandas con los datos
            start_order: Orden inicial para los bloques
            
        Returns:
            Lista de bloques procesados
        """
        fuente, contexto = self.get_source_info()
        blocks = []
        order = start_order
        
        # Crear una representación más elaborada de la tabla
        for i, row in df.iterrows():
            row_text = self._format_row_data(row, use_column_names=True)
                    
            # Si hay algún contenido, agregar bloque
            if row_text:
                blocks.append({
                    'text': row_text,
                    'order_in_document': order,
                    'block_type': 'excel_table_row',
                    'is_heading': False,
                    'row_number': i + 1,
                    'excel_columns': {str(col): str(row[col]) for col in df.columns if pd.notna(row[col])}
                })
                order += 1
                
        return blocks