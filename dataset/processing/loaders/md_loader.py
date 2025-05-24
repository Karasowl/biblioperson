from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import os # Para stat

try:
    import frontmatter
    FRONTMATTER_AVAILABLE = True
except ImportError:
    FRONTMATTER_AVAILABLE = False
    logging.warning("python-frontmatter no está instalado. El parsing de Frontmatter en archivos .md se omitirá.")

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)

class MarkdownLoader(BaseLoader):
    """Loader para archivos Markdown (.md)."""

    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader de Markdown.

        Args:
            file_path: Ruta al archivo Markdown.
            tipo: Tipo de contenido (se guarda en metadatos).
            encoding: Codificación del archivo.
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
        logger.debug(f"MarkdownLoader inicializado para: {self.file_path} con tipo: {self.tipo}, encoding: {self.encoding}")

    @staticmethod
    def _parse_frontmatter_date(date_value: Any) -> Optional[str]:
        """Parsea un valor de fecha del frontmatter a YYYY-MM-DD."""
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        if isinstance(date_value, str):
            try:
                # Intentar parsear si es una cadena con formato ISO reconocible por datetime
                parsed_dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return parsed_dt.strftime('%Y-%m-%d')
            except ValueError:
                # Podría ser solo YYYY o YYYY-MM, intentar otros parseos si es necesario
                # Por ahora, si no es ISO completo, se devuelve None o se podría intentar con dateutil
                logger.debug(f"No se pudo parsear la cadena de fecha del frontmatter '{date_value}' directamente a YYYY-MM-DD.")
                return None # O manejar formatos más simples aquí
        return None

    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo Markdown.
        Extrae metadatos del frontmatter y el contenido principal.

        Returns:
            Dict[str, Any]: Un diccionario con 'blocks' y 'document_metadata'.
        """
        logger.info(f"Iniciando carga de archivo Markdown: {self.file_path}")
        blocks: List[Dict[str, Any]] = []
        original_fuente, original_contexto = self.get_source_info()
        
        fm_data = {}
        main_content = ""
        file_content_read_error = None

        try:
            with self.file_path.open('r', encoding=self.encoding) as f:
                file_raw_content = f.read()
            if FRONTMATTER_AVAILABLE:
                post = frontmatter.loads(file_raw_content)
                fm_data = post.metadata
                main_content = post.content
            else:
                main_content = file_raw_content # Sin frontmatter, todo es contenido
        except FileNotFoundError:
            file_content_read_error = f"Archivo MD no encontrado: {self.file_path.name}"
            logger.error(file_content_read_error)
        except UnicodeDecodeError as e:
            file_content_read_error = f"Error de decodificación para el archivo MD '{self.file_path.name}' con encoding '{self.encoding}': {e}"
            logger.error(file_content_read_error)
        except Exception as e:
            file_content_read_error = f"Error general al leer archivo MD {self.file_path.name}: {e}"
            logger.error(file_content_read_error, exc_info=True)

        # --- Obtener Timestamps del Sistema de Archivos ---
        fs_creation_time_iso: Optional[str] = None
        fs_modified_time_iso: Optional[str] = None
        fs_fallback_publication_date: Optional[str] = None
        
        if not file_content_read_error: # Solo si se pudo leer el archivo, o al menos no hubo error fatal al inicio
            try:
                stat_info = self.file_path.stat()
                m_timestamp = stat_info.st_mtime
                fs_modified_time_iso = datetime.fromtimestamp(m_timestamp, timezone.utc).isoformat()
                fs_fallback_publication_date = datetime.fromtimestamp(m_timestamp, timezone.utc).strftime('%Y-%m-%d')
                try:
                    c_timestamp = stat_info.st_birthtime
                except AttributeError:
                    c_timestamp = stat_info.st_ctime
                fs_creation_time_iso = datetime.fromtimestamp(c_timestamp, timezone.utc).isoformat()
            except Exception as e:
                logger.warning(f"No se pudieron obtener las marcas de tiempo del sistema de archivos para {self.file_path}: {e}")

        # --- Determinar metadatos principales ---
        title_from_fm = fm_data.get('title') if isinstance(fm_data.get('title'), str) else None
        author_from_fm = fm_data.get('author') if isinstance(fm_data.get('author'), str) else None
        date_from_fm_val = fm_data.get('date') or fm_data.get('published') or fm_data.get('publish_date')
        parsed_date_from_fm = self._parse_frontmatter_date(date_from_fm_val)
        lang_from_fm = fm_data.get('lang') or fm_data.get('language')
        
        publication_date = parsed_date_from_fm or fs_fallback_publication_date
        publication_date_source = 'frontmatter' if parsed_date_from_fm else ('file_system_modification_time' if fs_fallback_publication_date else None)

        document_metadata = {
            'ruta_archivo_original': str(self.file_path.resolve()),
            'file_format': self.file_path.suffix.lstrip('.').lower() or 'md',
            'titulo_documento': title_from_fm or self.file_path.stem, # Prioridad: FM, luego nombre de archivo
            'autor_documento': author_from_fm,
            'fecha_publicacion_documento': publication_date,
            'idioma_documento': lang_from_fm if isinstance(lang_from_fm, str) else 'und',
            'metadatos_adicionales_fuente': {
                'loader_used': self.__class__.__name__,
                'loader_config': {'tipo': self.tipo, 'encoding': self.encoding},
                'original_fuente': original_fuente,
                'original_contexto': original_contexto,
                'fs_creation_time_iso': fs_creation_time_iso,
                'fs_modified_time_iso': fs_modified_time_iso,
                'publication_date_source': publication_date_source
            },
            'error': file_content_read_error,
            'warning': None
        }

        # Añadir el resto de campos del frontmatter a metadatos_adicionales_fuente
        for key, value in fm_data.items():
            if key not in ['title', 'author', 'date', 'published', 'publish_date', 'lang', 'language']:
                document_metadata['metadatos_adicionales_fuente'][f'fm_{key}'] = value
        
        if file_content_read_error:
            return {
                'blocks': [],
                'document_metadata': document_metadata
            }

        if not main_content.strip():
            warning_message = f"El contenido principal del archivo MD '{self.file_path.name}' está vacío o solo contiene espacios en blanco."
            logger.warning(warning_message)
            document_metadata['warning'] = warning_message
            # No retornar inmediatamente, aún puede haber metadatos útiles

        # Procesar main_content en bloques (similar a TxtLoader)
        normalized_content = main_content.replace('\r\n', '\n').replace('\r', '\n')
        order_idx = 0
        current_paragraph_lines = []
        for line in normalized_content.split('\n'):
            if not line.strip():
                if current_paragraph_lines:
                    paragraph_text = "\n".join(current_paragraph_lines).strip()
                    if paragraph_text:
                        blocks.append({'text': paragraph_text, 'order_in_document': order_idx})
                        order_idx += 1
                    current_paragraph_lines = []
            else:
                current_paragraph_lines.append(line)
        
        if current_paragraph_lines:
            paragraph_text = "\n".join(current_paragraph_lines).strip()
            if paragraph_text:
                blocks.append({'text': paragraph_text, 'order_in_document': order_idx})

        logger.info(f"Archivo MD cargado: {self.file_path}. Bloques encontrados: {len(blocks)}. Metadatos FM: {bool(fm_data)}")
        return {
            'blocks': blocks,
            'document_metadata': document_metadata
        }
