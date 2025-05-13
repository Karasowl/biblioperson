import json
from datetime import datetime
import re
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from .base_loader import BaseLoader

class NDJSONLoader(BaseLoader):
    """Loader para archivos NDJSON (JSON por línea)."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader de NDJSON.
        
        Args:
            file_path: Ruta al archivo NDJSON
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
                
        # Si no hay fecha en el nombre, devolver None
        return None
    
    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Carga y procesa el archivo NDJSON.
        
        Returns:
            Iterator[Dict[str, Any]]: Documentos procesados
        """
        fuente, contexto = self.get_source_info()
        fecha_archivo = self._extract_date_from_filename()
        
        with self.file_path.open('r', encoding=self.encoding) as f:
            for line in f:
                if line.strip():
                    try:
                        # Intenta parsear el JSON de la línea
                        data = json.loads(line.strip())
                        
                        # Asegura que tenga los campos requeridos
                        if not isinstance(data, dict):
                            continue
                            
                        # Extrae o establece valores por defecto
                        texto = data.get('texto', data.get('text', data.get('content', '')))
                        fecha = data.get('fecha', data.get('date', fecha_archivo))
                        
                        # Solo procesa si hay texto
                        if texto:
                            yield {
                                'texto': texto,
                                'fecha': fecha,
                                'fuente': fuente,
                                'contexto': contexto
                            }
                            
                    except json.JSONDecodeError:
                        # Ignora líneas que no son JSON válido
                        continue 