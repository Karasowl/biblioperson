from datetime import datetime, timezone
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
# import PyPDF2 # Eliminado PyPDF2
import fitz  # Importación de PyMuPDF
import logging

from .base_loader import BaseLoader

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
                        delta = timezone(datetime.timedelta(hours=offset_hours, minutes=offset_minutes) * (1 if tz_part[0] == '+' else -1))
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
        blocks = []
        
        # Construir document_metadata desde cero aquí
        original_fuente, original_contexto = self.get_source_info()
        document_metadata: Dict[str, Any] = {
            'ruta_archivo_original': str(self.file_path.resolve()),
            'file_format': 'pdf',
            'titulo_documento': None,
            'autor_documento': None,
            'fecha_publicacion_documento': None, # Se llenará más abajo
            'idioma_documento': None, # Generalmente no disponible en metadatos PDF estándar
            'metadatos_adicionales_fuente': {
                'loader_used': self.__class__.__name__,
                'loader_config': {'tipo': self.tipo},
                'original_fuente': original_fuente,
                'original_contexto': original_contexto,
                'blocks_are_fitz_native': True, # Indica que los bloques son nativos de fitz
                # Otros campos específicos del PDF se añadirán aquí
            },
            'error': None,
            'warning': None
        }

        doc = None # Definir doc aquí para que esté en el scope del finally
        try:
            doc = fitz.open(self.file_path)
            
            # Restaurar extracción de metadatos del PDF
            pdf_meta = doc.metadata
            if pdf_meta:
                document_metadata['titulo_documento'] = pdf_meta.get('title') if pdf_meta.get('title') else None
                document_metadata['autor_documento'] = pdf_meta.get('author') if pdf_meta.get('author') else None
                additional_meta = document_metadata['metadatos_adicionales_fuente']
                additional_meta['pdf_subject'] = pdf_meta.get('subject') if pdf_meta.get('subject') else None
                additional_meta['pdf_keywords'] = pdf_meta.get('keywords') if pdf_meta.get('keywords') else None
                additional_meta['pdf_creator'] = pdf_meta.get('creator') if pdf_meta.get('creator') else None
                additional_meta['pdf_producer'] = pdf_meta.get('producer') if pdf_meta.get('producer') else None
                
                creation_date_str = pdf_meta.get('creationDate')
                mod_date_str = pdf_meta.get('modDate')

                parsed_creation_date_simple, parsed_creation_date_iso = self._parse_pdf_datetime_str(creation_date_str)
                parsed_mod_date_simple, parsed_mod_date_iso = self._parse_pdf_datetime_str(mod_date_str)

                additional_meta['pdf_creation_date_iso'] = parsed_creation_date_iso
                additional_meta['pdf_modified_date_iso'] = parsed_mod_date_iso

                # Priorizar fecha de creación, luego modificación para 'fecha_publicacion_documento'
                document_metadata['fecha_publicacion_documento'] = parsed_creation_date_simple or parsed_mod_date_simple
            
            additional_meta['pdf_page_count'] = doc.page_count
            current_order = 0

            if doc.page_count == 0:
                warning_message = f"El archivo PDF '{self.file_path.name}' (fitz) no contiene páginas o está vacío."
                logger.warning(warning_message)
                document_metadata['warning'] = warning_message
                # No es necesario retornar aquí explícitamente si el bucle de páginas no se ejecuta.
                # doc.close() se llamará en el finally.
            else:
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    page_blocks = page.get_text("blocks", sort=True) 
                    logger.debug(f"Página {page_num + 1}/{doc.page_count} - get_text(\"blocks\") devolvió {len(page_blocks)} bloques.")

                    for i, b in enumerate(page_blocks):
                        x0, y0, x1, y1, block_text, block_no, block_type = b
                        # Descomentar para depuración muy detallada:
                        # logger.debug(f"  Bloque {i} (fitz_block_no {block_no}) en pág {page_num+1}: Type={block_type}, Pos=({x0:.2f},{y0:.2f}-{x1:.2f},{y1:.2f}), Texto (primeros 50): '{block_text[:50].replace('\\n', ' ')}'")
                        if block_type == 0: # Solo procesar bloques de texto
                            if block_text and block_text.strip():
                                blocks.append({
                                    'type': 'text_block',
                                    'text': block_text.strip(),
                                    'order_in_document': current_order,
                                    'source_page_number': page_num + 1,
                                    'source_block_number': block_no,
                                    'coordinates': {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}
                                })
                                current_order += 1
            
            logger.info(f"Archivo PDF cargado con fitz: {self.file_path}. Bloques de texto extraídos: {len(blocks)}")

        except FileNotFoundError:
            error_message = f"Archivo no encontrado: {self.file_path}"
            logger.error(error_message)
            document_metadata['error'] = error_message
        except fitz.FitzUnableToOpenError: # Corregido: FitzUnableToOpenError dentro del try/except
            error_message = f"Error al abrir el archivo PDF (fitz FitzUnableToOpenError) '{self.file_path.name}': El archivo no se puede abrir."
            logger.error(error_message)
            document_metadata['error'] = error_message
        except Exception as e:
            error_message = f"Error general al abrir o procesar PDF '{self.file_path.name}' (fitz): {e}"
            logger.error(error_message)
            document_metadata['error'] = error_message
            logger.exception(f"Detalles de la excepción en PDFLoader para {self.file_path.name}:") # Loguear stacktrace
        finally:
            if 'doc' in locals() and doc: # Asegurarse de que doc exista y no sea None
                try:
                    doc.close()
                except Exception as e:
                    logger.error(f"Error al cerrar el documento PDF {self.file_path.name}: {e}")

        return {
            'blocks': blocks,
            'document_metadata': document_metadata
        } 