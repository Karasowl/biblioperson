from datetime import datetime
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .base_loader import BaseLoader

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

        document_metadata = {
            'source_file_path': str(self.file_path.absolute()),
            'file_format': 'txt', # o el sufijo real Path(self.file_path).suffix.lower().lstrip('.')
            'loader_used': self.__class__.__name__,
            'loader_config': {
                'tipo': self.tipo,
                'encoding': self.encoding
            },
            'original_fuente': original_fuente,
            'original_contexto': original_contexto,
            'error': None,
            'warning': None
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