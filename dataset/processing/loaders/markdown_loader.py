from datetime import datetime
import re
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from .base_loader import BaseLoader

class MarkdownLoader(BaseLoader):
    """Loader para archivos Markdown."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader de Markdown.
        
        Args:
            file_path: Ruta al archivo Markdown
            tipo: Tipo de contenido ('escritos', 'poemas', 'canciones')
            encoding: Codificación del archivo (por defecto utf-8)
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
        
    def _extract_date_from_filename(self) -> Optional[str]:
        """Intenta extraer una fecha del nombre del archivo."""
        # Patrones comunes de fecha en nombres de archivo
        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{4})-(\d{2})',          # YYYY-MM
            r'(\d{4})',                  # YYYY
        ]
        
        filename = self.file_path.stem
        for pattern in patterns:
            if match := re.search(pattern, filename):
                return match.group(0)
        
        # Si no encuentra fecha en el nombre, usa la fecha de modificación del archivo
        mtime = datetime.fromtimestamp(self.file_path.stat().st_mtime)
        return mtime.strftime('%Y-%m-%d')
    
    def _segment_content(self, content: str) -> Iterator[str]:
        """
        Segmenta el contenido según el tipo de documento.
        
        Para escritos: segmenta por párrafos (doble salto de línea)
        Para poemas/canciones: devuelve el contenido completo
        """
        if self.tipo in ['poemas', 'canciones']:
            yield content.strip()
        else:  # escritos
            # Elimina líneas vacías múltiples y espacios extra
            content = re.sub(r'\n{3,}', '\n\n', content.strip())
            # Segmenta por párrafos
            for parrafo in content.split('\n\n'):
                if parrafo.strip():
                    yield parrafo.strip()
    
    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo Markdown.
        
        Returns:
            Dict[str, Any]: Un diccionario con bloques de contenido y metadatos del documento.
        """
        fuente, contexto = self.get_source_info()
        fecha = self._extract_date_from_filename()
        content = self.file_path.read_text(encoding=self.encoding)
        
        blocks = []
        order_in_document = 0
        for texto_bloque in self._segment_content(content):
            blocks.append({
                'text': texto_bloque,
                'order_in_document': order_in_document
                # Aquí puedes añadir otros metadatos específicos del bloque si los tienes,
                # como 'tipo_bloque': 'parrafo' o similar si _segment_content lo diferencia.
            })
            order_in_document += 1
            
        document_metadata = {
            'source_file_path': str(self.file_path.absolute()),
            'file_format': self.file_path.suffix,
            'detected_date': fecha,
            'original_fuente': fuente,
            'original_contexto': contexto,
            'content_type_provided_to_loader': self.tipo # Para depuración
        }
        
        return {
            'blocks': blocks,
            'document_metadata': document_metadata
        } 