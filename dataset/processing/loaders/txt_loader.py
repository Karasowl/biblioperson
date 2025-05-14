from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_loader import BaseLoader
import logging

logger = logging.getLogger(__name__)

class TxtLoader(BaseLoader):
    """Loader para archivos de texto plano (.txt)."""

    def __init__(self, file_path: str | Path, encoding: str = 'utf-8'):
        super().__init__(file_path)
        self.encoding = encoding
        logger.debug(f"Inicializando TxtLoader para archivo: {self.file_path} con encoding {self.encoding}")

    def load(self) -> Dict[str, Any]:
        logger.info(f"Iniciando carga de archivo TXT: {self.file_path}")
        blocks: List[Dict[str, Any]] = []
        
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Dividir por párrafos (uno o más saltos de línea consecutivos)
            # Normalizar saltos de línea a \n
            normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            order_idx = 0
            current_paragraph_lines = []
            for line in normalized_content.split('\n'):
                stripped_line = line.strip()
                if not stripped_line: # Línea vacía o solo espacios
                    if current_paragraph_lines: # Si teníamos líneas acumuladas, forman un párrafo
                        blocks.append({
                            'text': "\n".join(current_paragraph_lines).strip(),
                            'order_in_document': order_idx
                        })
                        order_idx += 1
                        current_paragraph_lines = []
                else:
                    current_paragraph_lines.append(stripped_line) # Usar stripped_line para evitar espacios indeseados al reconstruir
            
            # Añadir el último párrafo si existe
            if current_paragraph_lines:
                blocks.append({
                    'text': "\n".join(current_paragraph_lines).strip(),
                    'order_in_document': order_idx
                })

            original_fuente, original_contexto = self.get_source_info()
            
            document_metadata = {
                'source_file_path': str(self.file_path.absolute()),
                'file_format': 'txt',
                'original_fuente': original_fuente,
                'original_contexto': original_contexto,
                # 'detected_date': self._extract_date_from_filename(), # Podríamos añadir una función para esto
            }
            
            logger.info(f"Archivo TXT cargado: {self.file_path}. Bloques encontrados: {len(blocks)}")
            return {
                'blocks': blocks,
                'document_metadata': document_metadata
            }

        except FileNotFoundError:
            logger.error(f"Error: Archivo no encontrado en TxtLoader: {self.file_path}")
            raise
        except Exception as e:
            logger.error(f"Error al procesar archivo TXT {self.file_path}: {str(e)}")
            # Devolver estructura vacía o parcial en caso de error no fatal
            return {
                'blocks': [],
                'document_metadata': {
                    'source_file_path': str(self.file_path.absolute()),
                    'file_format': 'txt',
                    'error': str(e)
                }
            } 