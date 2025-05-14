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
    """Loader para archivos DOCX (Microsoft Word). Devuelve bloques de párrafos."""
    
    def __init__(self, file_path: str | Path, encoding: str = 'utf-8'):
        """
        Inicializa el loader de DOCX.
        
        Args:
            file_path: Ruta al archivo DOCX
            encoding: Codificación para leer el texto (por defecto utf-8)
        """
        super().__init__(file_path)
        self.encoding = encoding
        logger.debug(f"Inicializando DocxLoader para archivo: {file_path}")
        
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
    
    def _extract_date_from_filename(self) -> Optional[str]:
        """Intenta extraer una fecha del nombre del archivo."""
        # Patrones comunes de fecha en nombres de archivo
        patterns = [
            r'(\d{4})[_-](\d{2})[_-](\d{2})',  # 2024-01-30, 2024_01_30
            r'(\d{2})[_-](\d{2})[_-](\d{4})',  # 30-01-2024, 30_01_2024
            r'(\d{4})(\d{2})(\d{2})'           # 20240130
        ]
        
        filename = self.file_path.stem
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    if len(match.group(1)) == 4:  # Año primero
                        year, month, day = match.groups()
                    else:  # Día primero
                        day, month, year = match.groups()
                    
                    # Validar fecha
                    date = datetime(int(year), int(month), int(day))
                    return date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Limpia el texto de caracteres no deseados y espacios extra."""
        try:
            # Intenta decodificar si es bytes
            if isinstance(text, bytes):
                text = text.decode(self.encoding, errors='replace')
            
            # Elimina caracteres de control excepto saltos de línea
            text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
            # Normaliza saltos de línea
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            # Elimina espacios múltiples y al inicio/final
            text = re.sub(r' +', ' ', text).strip()
            
            return text
        except Exception as e:
            logger.warning(f"Error al limpiar texto: {str(e)}")
            # Retorna una versión segura del texto
            return str(text).encode('ascii', errors='replace').decode('ascii')
    
    def _process_paragraph(self, paragraph) -> Optional[Dict[str, Any]]:
        """
        Procesa un párrafo del documento.
        Devuelve None si el párrafo está vacío después de limpiar.
        """
        raw_text = paragraph.text
        cleaned_text = self._clean_text(raw_text) # Limpiar primero

        if not cleaned_text: # Si el párrafo está vacío después de limpiar
            return None
            
        is_heading = False
        heading_level = 0
        style_name = "Normal"
        try:
            if paragraph.style and paragraph.style.name:
                style_name = paragraph.style.name
                style_name_lower = style_name.lower()
                is_heading = style_name_lower.startswith('heading') or 'título' in style_name_lower
                if is_heading:
                    level_match = re.search(r'\d+', style_name)
                    if level_match:
                        heading_level = int(level_match.group())
                    else: # Estilo 'Heading' sin número o 'Título'
                        heading_level = 1 
                elif 'title' in style_name_lower or 'subtitle' in style_name_lower or 'caption' in style_name_lower:
                    is_heading = True
                    heading_level = 1 if 'title' in style_name_lower else 2
        except Exception as e:
            logger.debug(f"Error al procesar estilo para texto '{cleaned_text[:30]}...': {str(e)}")
        
        alignment_str = None
        is_centered = False
        try:
            if paragraph.alignment is not None: # WD_ALIGN_PARAGRAPH puede ser 0 (izquierda)
                alignment_str = str(docx.enum.text.WD_ALIGN_PARAGRAPH(paragraph.alignment))
                is_centered = paragraph.alignment == docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e:
            logger.debug(f"Error al procesar alineación para texto '{cleaned_text[:30]}...': {str(e)}")
        
        is_bold = False
        is_italic = False
        is_caps = False
        fonts = []
        try:
            runs_with_text = [run for run in paragraph.runs if run.text.strip()]
            if runs_with_text: # Solo si hay runs con texto real
                is_bold = all(run.bold for run in runs_with_text) if runs_with_text else False
                is_italic = all(run.italic for run in runs_with_text) if runs_with_text else False
                is_caps = cleaned_text.isupper() and len(cleaned_text) > 3 # Basado en el texto limpio del párrafo
                for run in runs_with_text:
                    if run.font and run.font.name:
                        fonts.append(run.font.name)
        except Exception as e:
            logger.debug(f"Error al procesar formato de runs para texto '{cleaned_text[:30]}...': {str(e)}")
        
        # Heurísticas adicionales para detectar encabezados, solo si no se detectó por estilo
        if not is_heading:
            if is_caps and len(cleaned_text) < 100:
                is_heading = True; heading_level = 1
            elif is_bold and len(cleaned_text) < 80:
                is_heading = True; heading_level = 2
            elif is_centered and len(cleaned_text) < 80: # Menos fiable, puede ser poesía
                is_heading = True; heading_level = 2
            elif cleaned_text.endswith('...') and len(cleaned_text) < 80:
                 is_heading = True; heading_level = 2
        
        # Patrones comunes de títulos (esta lógica podría mejorarse o hacerse configurable)
        # heading_patterns = [r'^(La|El|Los|Las|Un|Una) [A-ZÁ-Ú][a-zá-ú]+(\.{3})?$', r'^[A-ZÁ-Ú]{4,}$', r'^Capítulo \d+', r'^[A-ZÁ-Ú][a-zá-ú]+(:|\.{3})']
        # if not is_heading and any(re.match(pattern, cleaned_text) for pattern in heading_patterns):
        #     is_heading = True; heading_level = 2

        return {
            'text': cleaned_text,
            'is_heading': is_heading,
            'heading_level': heading_level,
            'is_bold': is_bold,
            'is_italic': is_italic,
            'is_caps': is_caps,
            'is_centered': is_centered,
            'style': style_name,
            'alignment': alignment_str,
            'fonts': list(set(fonts)) if fonts else [] # Lista de fuentes únicas
        }
    
    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo DOCX.
        
        Returns:
            Dict[str, Any]: Documento procesado
        """
        logger.info(f"Iniciando carga de archivo DOCX: {self.file_path}")
        processed_blocks: List[Dict[str, Any]] = []

        try:
            # Abre el documento
            doc = docx.Document(self.file_path)
            
            # Obtiene información de fuente y contexto
            original_fuente, original_contexto = self.get_source_info()
            logger.debug(f"Fuente: {original_fuente}, Contexto: {original_contexto}")
            
            # Extrae fecha de las propiedades del documento
            detected_date = self._extract_date_from_core_properties(doc) or self._extract_date_from_filename()
            logger.debug(f"Fecha extraída: {detected_date}")
            
            core_props = doc.core_properties
            document_metadata = {
                'source_file_path': str(self.file_path.absolute()),
                'file_format': 'docx',
                'original_fuente': original_fuente,
                'original_contexto': original_contexto,
                'detected_date': detected_date,
                'author': core_props.author,
                'title': core_props.title, # Título del documento si existe en propiedades
                'subject': core_props.subject,
                'keywords': core_props.keywords,
                'category': core_props.category,
                'comments': core_props.comments,
                'last_modified_by': core_props.last_modified_by,
                'created_date_prop': core_props.created.strftime('%Y-%m-%d %H:%M:%S') if core_props.created else None,
                'modified_date_prop': core_props.modified.strftime('%Y-%m-%d %H:%M:%S') if core_props.modified else None,
                'revision': core_props.revision,
                'version': core_props.version,
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
            logger.error(f"Error al abrir archivo: {self.file_path} (PackageNotFoundError). Asegúrese de que es un archivo DOCX válido.")
            return {
                'blocks': [],
                'document_metadata': {
                    'source_file_path': str(self.file_path.absolute()),
                    'file_format': 'docx',
                    'error': f"No se pudo abrir el archivo (PackageNotFoundError): {self.file_path}. No es un archivo DOCX válido o está corrupto."
                }
            }
        except Exception as e:
            logger.error(f"Error general al procesar documento DOCX {self.file_path}: {str(e)}", exc_info=True)
            return {
                'blocks': [],
                'document_metadata': {
                    'source_file_path': str(self.file_path.absolute()),
                    'file_format': 'docx',
                    'error': str(e)
                }
            }