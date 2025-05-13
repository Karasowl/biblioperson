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
    
    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Carga y procesa el archivo Markdown.
        
        Returns:
            Iterator[Dict[str, Any]]: Documentos procesados
        """
        # Obtiene información de fuente y contexto
        fuente, contexto = self.get_source_info()
        
        # Extrae fecha del nombre de archivo o metadata
        fecha = self._extract_date_from_filename()
        
        # Lee y procesa el contenido
        content = self.file_path.read_text(encoding=self.encoding)
        
        # Segmenta el contenido según el tipo
        for texto in self._segment_content(content):
            yield {
                'texto': texto,
                'fecha': fecha,
                'fuente': fuente,
                'contexto': contexto
            } 