from datetime import datetime
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
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
            'source_file_path': str(self.file_path.absolute()),
            'file_format': 'pdf',
            'loader_used': self.__class__.__name__,
            'loader_config': {'tipo': self.tipo},
            'original_fuente': original_fuente,
            'original_contexto': original_contexto,
            'blocks_are_fitz_native': True,
            'error': None,
            'warning': None
        }

        doc = None # Definir doc aquí para que esté en el scope del finally
        try:
            doc = fitz.open(self.file_path)
            
            # Restaurar extracción de metadatos del PDF
            pdf_meta = doc.metadata
            if pdf_meta:
                document_metadata['pdf_title'] = pdf_meta.get('title')
                document_metadata['pdf_author'] = pdf_meta.get('author')
                document_metadata['pdf_subject'] = pdf_meta.get('subject')
                document_metadata['pdf_creator'] = pdf_meta.get('creator')
                document_metadata['pdf_producer'] = pdf_meta.get('producer')
                creation_date_str = pdf_meta.get('creationDate')
                if creation_date_str and isinstance(creation_date_str, str) and creation_date_str.startswith('D:'):
                    try:
                        dt_part = creation_date_str[2:16]
                        document_metadata['pdf_creation_date'] = datetime.strptime(dt_part, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        logger.warning(f"No se pudo parsear creationDate de PDF: {creation_date_str}")
                        document_metadata['pdf_creation_date_raw'] = creation_date_str
                
                mod_date_str = pdf_meta.get('modDate')
                if mod_date_str and isinstance(mod_date_str, str) and mod_date_str.startswith('D:'):
                    try:
                        dt_part = mod_date_str[2:16]
                        document_metadata['pdf_modification_date'] = datetime.strptime(dt_part, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        logger.warning(f"No se pudo parsear modDate de PDF: {mod_date_str}")
                        document_metadata['pdf_modification_date_raw'] = mod_date_str

            document_metadata['pdf_page_count'] = doc.page_count
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