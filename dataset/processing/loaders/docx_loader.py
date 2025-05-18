from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List
from datetime import datetime
import docx
import re
import logging
from docx.opc.exceptions import PackageNotFoundError

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)

class DocxLoader(BaseLoader):
    """Loader para archivos DOCX (Microsoft Word)."""
    
    def __init__(self, file_path: str | Path, encoding: str = 'utf-8'):
        """
        Inicializa el loader de DOCX.
        
        Args:
            file_path: Ruta al archivo DOCX
            encoding: Codificación (generalmente no aplicable para DOCX de esta manera)
        """
        super().__init__(file_path)
        logger.debug(f"Inicializando DocxLoader para archivo: {file_path}")
        
    def _get_publication_date_from_core_props(self, core_props) -> Optional[str]:
        """Intenta extraer la fecha de publicación (creación o modificación) de las propiedades del core.

        Prioriza 'created', luego 'modified'. Formato YYYY-MM-DD.
        """
        try:
            if core_props.created:
                return core_props.created.strftime('%Y-%m-%d')
            if core_props.modified:
                return core_props.modified.strftime('%Y-%m-%d')
        except AttributeError as e: # core_props podría no tener el atributo (aunque raro para python-docx)
            logger.warning(f"Atributo de fecha no encontrado en core_properties: {e}")
        except Exception as e:
            logger.warning(f"Error al extraer fecha de core_properties: {e}")
        return None
    
    def _extract_date_from_core_properties(self, doc) -> Optional[str]:
        """Intenta extraer la fecha de las propiedades del documento."""
        try:
            # Intenta obtener la fecha de creación
            if doc.core_properties.created:
                return doc.core_properties.created.strftime('%Y-%m-%d')
            # Si no hay fecha de creación, intenta la de modificación
            if doc.core_properties.modified:
                return doc.core_properties.modified.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Error al extraer fecha de propiedades: {str(e)}")
        return None
    
    def _process_paragraph(self, paragraph) -> Optional[Dict[str, Any]]:
        """
        Procesa un párrafo del documento, extrayendo texto y metadatos de formato.
        Devuelve None si el párrafo está vacío o solo contiene espacios en blanco.
        """
        text_content = paragraph.text # Obtener texto crudo del párrafo

        if not text_content or not text_content.strip(): # Omitir si está vacío o solo espacios
            return None
            
        is_heading_style = False # Renombrado para claridad, se basa solo en estilo
        heading_level_style = 0  # Renombrado para claridad
        style_name = "Normal"
        try:
            if paragraph.style and paragraph.style.name:
                style_name = paragraph.style.name
                style_name_lower = style_name.lower()
                # Detección de encabezado basada ÚNICAMENTE en el nombre del estilo
                is_heading_style = style_name_lower.startswith('heading') or \
                                   'título' in style_name_lower or \
                                   'title' in style_name_lower or \
                                   'subtitle' in style_name_lower or \
                                   'caption' in style_name_lower
                
                if is_heading_style:
                    level_match = re.search(r'\d+', style_name) # Para estilos como 'Heading 1'
                    if level_match:
                        heading_level_style = int(level_match.group())
                    elif 'title' in style_name_lower or style_name_lower.startswith('heading'): # 'Title', 'Heading' (sin num)
                        heading_level_style = 1 
                    elif 'subtitle' in style_name_lower: # 'Subtitle'
                        heading_level_style = 2
                    elif 'caption' in style_name_lower: # 'Caption' como un nivel bajo de encabezado
                        heading_level_style = 3 # O el nivel que se decida para captions
                    else: # Por si 'título' no encaja en los anteriores pero es heading
                        heading_level_style = 1
        except Exception as e:
            logger.debug(f"Error al procesar estilo para texto '{text_content[:30]}...': {str(e)}")
        
        alignment_str = None
        is_centered_format = False # Renombrado
        try:
            if paragraph.alignment is not None: 
                alignment_str = str(docx.enum.text.WD_ALIGN_PARAGRAPH(paragraph.alignment))
                is_centered_format = paragraph.alignment == docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e:
            logger.debug(f"Error al procesar alineación para texto '{text_content[:30]}...': {str(e)}")
        
        is_bold_format = False # Renombrado
        is_italic_format = False # Renombrado
        is_all_caps_text = False # Renombrado
        fonts_in_paragraph = [] # Renombrado
        try:
            runs_with_text = [run for run in paragraph.runs if run.text.strip()] # Considerar runs con texto real
            if runs_with_text:
                # Si CUALQUIER run con texto tiene el formato, se considera verdadero para el párrafo
                # (Una alternativa sería all(), pero any() es más inclusivo para detectar formato)
                is_bold_format = any(run.bold for run in runs_with_text)
                is_italic_format = any(run.italic for run in runs_with_text)
                for run in runs_with_text:
                    if run.font and run.font.name:
                        fonts_in_paragraph.append(run.font.name)
            # is_all_caps_text se basa en el contenido de texto del párrafo completo
            if text_content: # Asegurarse de que text_content no sea None
                 is_all_caps_text = text_content.isupper() and len(text_content) > 1 # Min 2 chars para ser considerado caps

        except Exception as e:
            logger.debug(f"Error al procesar formato de runs para texto '{text_content[:30]}...': {str(e)}")
        
        # Las heurísticas adicionales para detectar encabezados han sido eliminadas.
        # El segmentador deberá usar los metadatos de estilo y formato extraídos.

        return {
            'text': text_content, # Texto crudo del párrafo
            'docx_style_is_heading': is_heading_style, # Metadato crudo del estilo DOCX
            'docx_style_heading_level': heading_level_style, # Metadato crudo del estilo DOCX
            'format_is_bold': is_bold_format, # Metadato crudo del formato
            'format_is_italic': is_italic_format, # Metadato crudo del formato
            'text_is_all_caps': is_all_caps_text, # Metadato derivado del texto mismo
            'format_is_centered': is_centered_format, # Metadato crudo del formato
            'docx_style_name': style_name, # Metadato crudo del estilo DOCX
            'docx_alignment': alignment_str, # Metadato crudo del formato
            'docx_fonts': list(set(fonts_in_paragraph)) if fonts_in_paragraph else [] # Metadato crudo
        }
    
    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo DOCX.
        
        Returns:
            Dict[str, Any]: Documento procesado
        """
        logger.info(f"Iniciando carga de archivo DOCX: {self.file_path}")
        processed_blocks: List[Dict[str, Any]] = []
        
        base_document_metadata = {
            'ruta_archivo_original': str(self.file_path.resolve()), # Usar resolve() para path absoluto y limpio
            'file_format': 'docx',
            'error': None, 
            'warning': None 
        }

        try:
            doc = docx.Document(self.file_path)
            core_props = doc.core_properties
            
            # Obtener información de fuente y contexto (de BaseLoader)
            original_fuente, original_contexto = self.get_source_info()
            
            # Obtener fecha de publicación
            publication_date = self._get_publication_date_from_core_props(core_props)
            
            # Construir el diccionario de metadatos alineado con ProcessedContentItem
            document_metadata = {
                **base_document_metadata,
                'titulo_documento': core_props.title if core_props.title else None,
                'autor_documento': core_props.author if core_props.author else None,
                'fecha_publicacion_documento': publication_date,
                'idioma_documento': core_props.language if core_props.language else None,
                'metadatos_adicionales_fuente': {
                    'docx_category': core_props.category if core_props.category else None,
                    'docx_comments': core_props.comments if core_props.comments else None,
                    'docx_content_status': core_props.content_status if core_props.content_status else None,
                    'docx_identifier': core_props.identifier if core_props.identifier else None,
                    'docx_keywords': core_props.keywords if core_props.keywords else None,
                    'docx_last_modified_by': core_props.last_modified_by if core_props.last_modified_by else None,
                    'docx_last_printed_raw': core_props.last_printed.isoformat() if core_props.last_printed else None,
                    'docx_revision': core_props.revision if core_props.revision else 0, # revision es int
                    'docx_subject': core_props.subject if core_props.subject else None,
                    'docx_version': core_props.version if core_props.version else None,
                    'docx_created_date_raw': core_props.created.isoformat() if core_props.created else None,
                    'docx_modified_date_raw': core_props.modified.isoformat() if core_props.modified else None,
                    'original_fuente': original_fuente, # Información del BaseLoader
                    'original_contexto': original_contexto # Información del BaseLoader
                }
            }

            if not doc.paragraphs and not doc.tables and not doc.sections:
                warning_message = f"El archivo DOCX '{self.file_path.name}' parece estar vacío o no contiene texto extraíble."
                logger.warning(warning_message)
                document_metadata['warning'] = warning_message
                return {
                    'blocks': [],
                    'document_metadata': document_metadata
                }

            for i, paragraph in enumerate(doc.paragraphs):
                paragraph_data = self._process_paragraph(paragraph)
                if paragraph_data: 
                    paragraph_data['order_in_document'] = i
                    processed_blocks.append(paragraph_data)
            
            logger.info(f"Archivo DOCX cargado: {self.file_path}. Bloques encontrados: {len(processed_blocks)}")
            return {
                'blocks': processed_blocks,
                'document_metadata': document_metadata
            }
        except PackageNotFoundError:
            error_message = f"No se pudo abrir el archivo (PackageNotFoundError): {self.file_path.name}. No es un archivo DOCX válido o está corrupto."
            logger.error(error_message)
            base_document_metadata['error'] = error_message
            return {
                'blocks': [],
                'document_metadata': base_document_metadata
            }
        except Exception as e:
            error_message = f"Error general al procesar documento DOCX {self.file_path.name}: {str(e)}"
            logger.error(error_message, exc_info=True)
            base_document_metadata['error'] = error_message
            return {
                'blocks': [],
                'document_metadata': base_document_metadata
            }