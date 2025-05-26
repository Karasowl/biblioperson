from datetime import datetime
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone # Asegurar timezone

from .base_loader import BaseLoader
from dataset.scripts.converters import _calculate_sha256

logger = logging.getLogger(__name__)

class txtLoader(BaseLoader):
    """Loader para archivos de texto plano (.txt)."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader de texto plano.
        
        Args:
            file_path: Ruta al archivo de texto
            tipo: Tipo de contenido (se guarda en metadatos pero no afecta la carga)
            encoding: Codificación del archivo
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
        logger.debug(f"txtLoader inicializado para: {self.file_path} con tipo: {self.tipo}, encoding: {self.encoding}")
        
    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo de texto, agrupando líneas en párrafos.
        
        Returns:
            Dict[str, Any]: Un diccionario con 'blocks' y 'document_metadata'.
        """
        logger.info(f"Iniciando carga de archivo TXT (txtLoader): {self.file_path}")
        blocks: List[Dict[str, Any]] = []
        original_fuente, original_contexto = self.get_source_info()

        # --- Obtener Timestamps del Sistema de Archivos ---
        fs_creation_time_iso: Optional[str] = None
        fs_modified_time_iso: Optional[str] = None
        fallback_publication_date: Optional[str] = None
        publication_date_source: Optional[str] = None

        try:
            stat_info = self.file_path.stat()
            
            # Fecha de Modificación (más robusta como fallback para publicación)
            m_timestamp = stat_info.st_mtime
            fs_modified_time_iso = datetime.fromtimestamp(m_timestamp, timezone.utc).isoformat()
            fallback_publication_date = datetime.fromtimestamp(m_timestamp, timezone.utc).strftime('%Y-%m-%d')
            publication_date_source = 'file_system_modification_time'

            # Fecha de Creación (puede variar su disponibilidad/significado por OS)
            try:
                c_timestamp = stat_info.st_birthtime # Idealmente st_birthtime
            except AttributeError:
                c_timestamp = stat_info.st_ctime # Fallback a st_ctime
            fs_creation_time_iso = datetime.fromtimestamp(c_timestamp, timezone.utc).isoformat()
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener las marcas de tiempo del sistema de archivos para {self.file_path}: {e}")

        file_hash = _calculate_sha256(self.file_path)
        document_metadata: DocumentMetadata = {
            "nombre_archivo": self.file_path.name,
            "ruta_archivo": str(self.file_path.resolve()),
            "extension_archivo": self.file_path.suffix,
            "titulo_documento": self.file_path.stem, # Default title
            "hash_documento_original": file_hash,
            # TXT files usually don't have embedded metadata like author or creation date
        }

        try:
            with self.file_path.open('r', encoding=self.encoding) as f:
                content = f.read()

            if not content.strip():
                warning_message = f"El archivo TXT '{self.file_path.name}' (usando txtLoader) está vacío o solo contiene espacios en blanco."
                logger.warning(warning_message)
                document_metadata['warning'] = warning_message
                return {
                    'blocks': [],
                    'document_metadata': document_metadata
                }

            # Lógica de agrupación por párrafos (similar a la de TxtLoader refactorizado)
            normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            order_idx = 0
            current_paragraph_lines = []
            for line in normalized_content.split('\n'):
                if not line.strip(): # Línea efectivamente vacía
                    if current_paragraph_lines:
                        paragraph_text = "\n".join(current_paragraph_lines).strip()
                        if paragraph_text: 
                            blocks.append({
                                'text': paragraph_text,
                                'order_in_document': order_idx
                            })
                            order_idx += 1
                        current_paragraph_lines = []
                else:
                    current_paragraph_lines.append(line) 
            
            # Añadir el último párrafo si existe
            if current_paragraph_lines:
                paragraph_text = "\n".join(current_paragraph_lines).strip()
                if paragraph_text:
                    blocks.append({
                        'text': paragraph_text,
                        'order_in_document': order_idx
                    })
            
            logger.info(f"Archivo TXT cargado con txtLoader: {self.file_path}. Bloques encontrados: {len(blocks)}")

        except FileNotFoundError:
            error_message = f"Archivo TXT no encontrado (txtLoader): {self.file_path.name}"
            logger.error(error_message)
            document_metadata['error'] = error_message
        except UnicodeDecodeError as e:
            error_message = f"Error de decodificación para el archivo TXT '{self.file_path.name}' (txtLoader) con encoding '{self.encoding}': {e}"
            logger.error(error_message)
            document_metadata['error'] = error_message
        except Exception as e:
            error_message = f"Error general al procesar archivo TXT {self.file_path.name} (txtLoader): {e}"
            logger.error(error_message, exc_info=True)
            document_metadata['error'] = error_message
        
        return {
            'blocks': blocks,
            'document_metadata': document_metadata
        }
    
    # _parece_poema ha sido eliminado.