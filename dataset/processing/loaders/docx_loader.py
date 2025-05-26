from pathlib import Path
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import docx
import re
import logging
from docx.opc.exceptions import PackageNotFoundError

from .base_loader import BaseLoader
from dataset.scripts.converters import _calculate_sha256

logger = logging.getLogger(__name__)

class DocxLoader(BaseLoader):
    """Loader para archivos DOCX (Microsoft Word)."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader de DOCX.
        
        Args:
            file_path: Ruta al archivo DOCX
            tipo: Tipo de contenido ('escritos', 'poemas', 'canciones')
            encoding: Codificación para leer el texto (por defecto utf-8)
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
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
    
    def _process_paragraph(self, paragraph) -> Dict[str, Any]:
        """
        Procesa un párrafo del documento.
        
        Args:
            paragraph: Párrafo de python-docx
            
        Returns:
            Dict con la información del párrafo
        """
        # Extraer texto y propiedades
        text = paragraph.text.strip()
        if not text:
            return None
            
        # Detectar si es un encabezado por el estilo
        is_heading = False
        heading_level = 0
        style_name = "Normal"
        try:
            if paragraph.style and paragraph.style.name:
                style_name = paragraph.style.name
                is_heading = paragraph.style.name.lower().startswith('heading') or 'título' in paragraph.style.name.lower()
                if is_heading:
                    # Extraer nivel del nombre del estilo (e.g., 'Heading 1' -> 1)
                    try:
                        level_match = re.search(r'\d+', paragraph.style.name)
                        if level_match:
                            heading_level = int(level_match.group())
                        else:
                            heading_level = 1
                    except (ValueError, IndexError):
                        heading_level = 1
                        
                # Verificar otros estilos que podrían indicar encabezados
                if not is_heading and (
                    'title' in paragraph.style.name.lower() or 
                    'subtitle' in paragraph.style.name.lower() or
                    'caption' in paragraph.style.name.lower()
                ):
                    is_heading = True
                    heading_level = 1 if 'title' in paragraph.style.name.lower() else 2
                    
        except Exception as e:
            logger.debug(f"Error al procesar estilo: {str(e)}")
        
        # Detectar alineación
        alignment = None
        is_centered = False
        try:
            if paragraph.alignment:
                alignment = str(paragraph.alignment)
                is_centered = paragraph.alignment == docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e:
            logger.debug(f"Error al procesar alineación: {str(e)}")
        
        # Analizar formato de los runs
        is_bold = False
        is_italic = False
        is_caps = False
        fonts = []
        try:
            runs_with_text = [run for run in paragraph.runs if run.text.strip()]
            if runs_with_text:
                is_bold = all(run.bold for run in runs_with_text)
                is_italic = all(run.italic for run in runs_with_text)
                # Verificar si todo está en mayúsculas
                is_caps = text.isupper() and len(text) > 3
                # Recopilar información de fuentes
                for run in runs_with_text:
                    if run.font.name:
                        fonts.append(run.font.name)
        except Exception as e:
            logger.debug(f"Error al procesar formato de texto: {str(e)}")
        
        # Verificaciones adicionales para detectar encabezados
        if not is_heading:
            # Los textos en mayúsculas cortos suelen ser títulos
            if is_caps and len(text) < 100:
                is_heading = True
                heading_level = 1
            # Textos en negrita cortos también pueden ser títulos
            elif is_bold and len(text) < 80:
                is_heading = True
                heading_level = 2
            # Textos centrados cortos son candidatos a títulos
            elif is_centered and len(text) < 80:
                is_heading = True
                heading_level = 2
            # Textos que terminan con puntos suspensivos pueden ser títulos
            elif text.endswith('...') and len(text) < 80:
                is_heading = True
                heading_level = 2
        
        # Verificar por patrones comunes de títulos en el texto
        heading_patterns = [
            r'^(La|El|Los|Las|Un|Una) [A-ZÁ-Ú][a-zá-ú]+(\.{3})?$', # La Permanencia...
            r'^[A-ZÁ-Ú]{4,}$',  # INTRODUCCIÓN
            r'^Capítulo \d+',    # Capítulo 1
            r'^[A-ZÁ-Ú][a-zá-ú]+(:|\.{3})' # Naturaleza divina:
        ]
        
        if not is_heading and any(re.match(pattern, text) for pattern in heading_patterns):
            is_heading = True
            heading_level = 2
        
        return {
            'text': text,
            'is_heading': is_heading,
            'heading_level': heading_level,
            'is_bold': is_bold,
            'is_italic': is_italic,
            'is_caps': is_caps,
            'is_centered': is_centered,
            'style': style_name,
            'alignment': alignment,
            'fonts': ','.join(fonts) if fonts else None
        }
    
    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Carga y procesa el archivo DOCX.
        
        Returns:
            Iterator[Dict[str, Any]]: Documentos procesados
        """
        logger.info(f"Iniciando carga de archivo DOCX: {self.file_path}")
        
        try:
            # Abre el documento
            doc = docx.Document(self.file_path)
            
            # Obtiene información de fuente y contexto
            fuente, contexto = self.get_source_info()
            logger.debug(f"Fuente: {fuente}, Contexto: {contexto}")
            
            # Extrae fecha de las propiedades del documento
            fecha = self._extract_date_from_core_properties(doc) or self._extract_date_from_filename()
            logger.debug(f"Fecha extraída: {fecha}")
            file_hash = _calculate_sha256(self.file_path)
            document_metadata: DocumentMetadata = {
                "nombre_archivo": self.file_path.name,
                "ruta_archivo": str(self.file_path.resolve()),
                "extension_archivo": self.file_path.suffix,
                "titulo_documento": title if title else self.file_path.stem,
                "autor_documento": author,
                "fecha_creacion_documento": creation_date.isoformat() if creation_date else None,
                "fecha_modificacion_documento": modification_date.isoformat() if modification_date else None,
                "hash_documento_original": file_hash,
                "metadatos_adicionales_fuente": core_properties_dict
            }
            
            # Procesa el contenido según el tipo
            if self.tipo in ['poemas', 'canciones']:
                # Recorre todos los párrafos y extrae información adicional
                paragraphs_with_metadata = []
                for paragraph in doc.paragraphs:
                    metadata = self._process_paragraph(paragraph)
                    if metadata:
                        paragraphs_with_metadata.append(metadata)
                
                # Detecta secciones o poemas separados por líneas vacías o títulos
                current_poem = []
                poem_groups = []
                
                for i, metadata in enumerate(paragraphs_with_metadata):
                    # Si es un posible título y no es la primera línea, podría ser inicio de nuevo poema
                    if metadata['is_heading'] and i > 0 and current_poem:
                        poem_groups.append(current_poem)
                        current_poem = [metadata]
                    # Línea normal, la agregamos al poema actual
                    else:
                        current_poem.append(metadata)
                
                # Agregamos el último poema si existe
                if current_poem:
                    poem_groups.append(current_poem)
                
                # Procesamos cada grupo como un documento separado
                for poem_group in poem_groups:
                    # Separamos posible título del resto
                    title = None
                    verses = []
                    numbered_verses = []
                    
                    for i, metadata in enumerate(poem_group):
                        if title is None and metadata['is_heading']:
                            title = metadata['text']
                        else:
                            verses.append(metadata['text'])
                            numbered_verses.append({
                                'number': i + 1,
                                'text': metadata['text'],
                                'metadata': metadata
                            })
                    
                    # Generamos el documento final
                    yield {
                        'texto': '\n'.join(verses),
                        'titulo': title,
                        'tipo': self.tipo,
                        'fuente': fuente,
                        'contexto': contexto,
                        'fecha': fecha,
                        'versos': verses,
                        'numbered_verses': numbered_verses,
                    }
            else:
                # Para documentos regulares, extraemos los bloques de texto con metadatos
                blocks = []
                logger.debug(f"Total paragraphs found in DOCX: {len(doc.paragraphs)}")
                for i, paragraph in enumerate(doc.paragraphs):
                    logger.debug(f"Processing paragraph {i+1}/{len(doc.paragraphs)} - Raw text: '{paragraph.text[:100]}...'" ) # Log first 100 chars
                    metadata = self._process_paragraph(paragraph)
                    if metadata:
                        logger.debug(f"Paragraph {i+1} processed. Metadata: {metadata}")
                        blocks.append(metadata)
                    else:
                        logger.debug(f"Paragraph {i+1} skipped (empty or no metadata after processing).")
                
                logger.debug(f"Final _blocks content before yielding: {blocks}")
                # Enviamos todos los bloques con metadatos al segmentador
                yield {
                    'tipo': self.tipo,
                    'fuente': fuente,
                    'contexto': contexto,
                    'fecha': fecha,
                    '_blocks': blocks,  # Para uso del segmentador
                }
        except PackageNotFoundError:
            logger.error(f"Error al abrir archivo: {self.file_path} (no es un archivo DOCX válido)")
            raise ValueError(f"No se pudo abrir el archivo: {self.file_path}")
        except Exception as e:
            logger.error(f"Error al procesar documento DOCX: {str(e)}")
            raise