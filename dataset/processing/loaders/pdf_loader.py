from datetime import datetime, timezone, timedelta
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
# import PyPDF2 # Eliminado PyPDF2
import fitz  # Importación de PyMuPDF
import logging

from .base_loader import BaseLoader

def _calculate_sha256(file_path: Path) -> str:
    """Calcula el hash SHA256 de un archivo."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

logger = logging.getLogger(__name__)

class PDFLoader(BaseLoader):
    """Loader para archivos PDF (.pdf) usando PyMuPDF (fitz) para mayor rendimiento."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader para archivos PDF.
        
        Args:
            file_path: Ruta al archivo PDF
            tipo: Tipo de contenido (no se usa directamente aquí pero podría ser útil para perfiles)
            encoding: Codificación (no se usa directamente en PDFs pero se mantiene por consistencia)
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        # self.encoding = encoding # Encoding no es tan relevante para fitz de esta manera
        logger.debug(f"PDFLoader (fitz) inicializado para: {self.file_path} con tipo: {self.tipo}")

    @staticmethod
    def _parse_pdf_datetime_str(date_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Parsea una cadena de fecha/hora de metadatos PDF (ej. 'D:YYYYMMDDHHMMSS[Z|+-HH\'MM\']').

        Returns:
            Tuple[Optional[str], Optional[str]]: (fecha YYYY-MM-DD, fecha ISO completa) o (None, None).
        """
        if not date_str or not isinstance(date_str, str) or not date_str.startswith('D:'):
            return None, None
        
        raw_dt_part = date_str[2:] # Remover 'D:'
        
        # Extraer la parte principal de la fecha/hora (YYYYMMDDHHMMSS)
        dt_core = raw_dt_part[:14]
        
        try:
            parsed_dt = datetime.strptime(dt_core, '%Y%m%d%H%M%S')
            
            # Manejar la información de la zona horaria si existe
            tz_part = raw_dt_part[14:]
            if tz_part:
                if tz_part == 'Z':
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                elif tz_part.startswith(('+', '-')) and len(tz_part) >= 3:
                    try:
                        offset_hours = int(tz_part[1:3])
                        offset_minutes = int(tz_part[4:6]) if len(tz_part) >= 6 and tz_part[3] == "'" else 0
                        delta = timezone(timedelta(hours=offset_hours, minutes=offset_minutes) * (1 if tz_part[0] == '+' else -1))
                        parsed_dt = parsed_dt.replace(tzinfo=delta)
                    except ValueError:
                        # Si la zona horaria es inválida, mantener como naive pero loguear
                        logger.debug(f"No se pudo parsear la zona horaria de PDF: {tz_part} para fecha {date_str}")
                        # Devolver la fecha parseada sin tzinfo explícito, pero sí como ISO
                        return parsed_dt.strftime('%Y-%m-%d'), parsed_dt.isoformat() 
            
            return parsed_dt.strftime('%Y-%m-%d'), parsed_dt.isoformat()
        
        except ValueError as e:
            logger.warning(f"No se pudo parsear la parte central de la fecha PDF '{dt_core}' de '{date_str}': {e}")
            return None, date_str # Devolver la cadena original como fecha ISO si falla el parseo

    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo PDF.
        
        Returns:
            Dict[str, Any]: Un diccionario con 'blocks' y 'document_metadata'.
        """
        logger.info(f"Iniciando carga de archivo PDF con fitz: {self.file_path}")
        
        # 1. Inicialización correcta de document_metadata con información independiente del PDF
        calculated_hash = _calculate_sha256(self.file_path)
        logger.debug(f"Hash calculado para {self.file_path.name}: '{calculated_hash}' (tipo: {type(calculated_hash)})")
        
        document_metadata: Dict[str, Any] = {
            'ruta_archivo_original': str(self.file_path.resolve()),
            'file_format': 'pdf',
            'hash_documento_original': calculated_hash,
            'idioma_documento': 'und',
            'metadatos_adicionales_fuente': {
                'loader_used': 'PDFLoader',
                'loader_config': {'tipo': self.tipo},
                'original_fuente': 'pdf_file',
                'original_contexto': 'document_processing',
                'blocks_are_fitz_native': True
            },
            'error': None,
            'warning': None
        }
        
        # Inicializar variables
        blocks = []
        doc = None
        
        # 2. Procesamiento del PDF dentro de try/except/finally
        try:
            # Abrir el documento PDF
            doc = fitz.open(self.file_path)
            
            # Extraer todos los metadatos del objeto doc de PyMuPDF/fitz
            pdf_meta_fitz = doc.metadata
            num_pages_fitz = doc.page_count
            
            # Parsear las fechas de creación y modificación
            creation_date_str = pdf_meta_fitz.get('creationDate') if pdf_meta_fitz else None
            mod_date_str = pdf_meta_fitz.get('modDate') if pdf_meta_fitz else None

            parsed_creation_date_simple, parsed_creation_date_iso = self._parse_pdf_datetime_str(creation_date_str)
            parsed_mod_date_simple, parsed_mod_date_iso = self._parse_pdf_datetime_str(mod_date_str)

            # Actualizar el diccionario document_metadata usando las variables recién extraídas
            document_metadata['titulo_documento'] = (
                pdf_meta_fitz.get('title') if pdf_meta_fitz and pdf_meta_fitz.get('title') 
                else self.file_path.stem
            )
            document_metadata['autor_documento'] = (
                pdf_meta_fitz.get('author') if pdf_meta_fitz and pdf_meta_fitz.get('author') 
                else None
            )
            
            # Priorizar fecha de creación sobre modificación para fecha_publicacion_documento
            document_metadata['fecha_publicacion_documento'] = parsed_creation_date_simple or parsed_mod_date_simple
            
            # Actualizar metadatos_adicionales_fuente con información del PDF
            additional_meta = document_metadata['metadatos_adicionales_fuente']
            if pdf_meta_fitz:
                additional_meta['pdf_subject'] = pdf_meta_fitz.get('subject')
                additional_meta['pdf_keywords'] = pdf_meta_fitz.get('keywords')
                additional_meta['pdf_creator'] = pdf_meta_fitz.get('creator')
                additional_meta['pdf_producer'] = pdf_meta_fitz.get('producer')
                additional_meta['pdf_creation_date_iso'] = parsed_creation_date_iso
                additional_meta['pdf_modified_date_iso'] = parsed_mod_date_iso

            additional_meta['pdf_page_count'] = num_pages_fitz
            
            # Manejo de archivos vacíos/sin páginas
            if num_pages_fitz == 0:
                warning_message = f"El archivo PDF '{self.file_path.name}' no contiene páginas o está vacío."
                logger.warning(warning_message)
                document_metadata['warning'] = warning_message
                # Continuar al bloque finally (no extraer bloques de texto)
            else:
                # Extracción de bloques de texto
                current_order = 0
                
                for page_num in range(num_pages_fitz):
                    page = doc.load_page(page_num)
                    page_blocks = page.get_text("blocks", sort=True) 
                    logger.debug(f"Página {page_num + 1}/{num_pages_fitz} - get_text(\"blocks\") devolvió {len(page_blocks)} bloques.")

                    for i, b in enumerate(page_blocks):
                        x0, y0, x1, y1, block_text, block_no, block_type = b
                        
                        # Solo procesar bloques de texto (block_type == 0) que no estén vacíos
                        if block_type == 0 and block_text and block_text.strip():
                            blocks.append({
                                'type': 'text_block',
                                'text': block_text.strip(),
                                'order_in_document': current_order,
                                'source_page_number': page_num + 1,
                                'source_block_number': block_no,
                                'coordinates': {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}
                            })
                            current_order += 1
            
                logger.info(f"Archivo PDF cargado exitosamente: {self.file_path}. Bloques de texto extraídos: {len(blocks)}")

        except FileNotFoundError:
            error_message = f"Archivo no encontrado: {self.file_path}"
            logger.error(error_message)
            document_metadata['error'] = error_message
        except RuntimeError as e_fitz_open_error:
            error_message = f"Error al abrir el archivo PDF (PyMuPDF RuntimeError) '{self.file_path.name}': {e_fitz_open_error}"
            logger.error(error_message)
            document_metadata['error'] = error_message
        except Exception as e:
            error_message = f"Error general al procesar PDF '{self.file_path.name}': {e}"
            logger.error(error_message)
            document_metadata['error'] = error_message
            logger.exception(f"Detalles de la excepción en PDFLoader para {self.file_path.name}:")
        finally:
            # Asegurar que doc.close() se llame si doc fue abierto
            if doc is not None:
                try:
                    doc.close()
                except Exception as e:
                    logger.error(f"Error al cerrar el documento PDF {self.file_path.name}: {e}")

        return {
            'blocks': blocks,
            'document_metadata': document_metadata
        }