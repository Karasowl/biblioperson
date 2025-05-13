from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Dict, Any

class BaseLoader(ABC):
    """Clase base abstracta para todos los loaders de documentos."""
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")
    
    @abstractmethod
    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Carga y procesa el archivo, devolviendo un iterador de documentos.
        
        Returns:
            Iterator[Dict[str, Any]]: Iterador de documentos en formato:
                {
                    'id': int,  # Se asignará posteriormente
                    'texto': str,
                    'fecha': str,  # YYYY-MM-DD, YYYY-MM, o YYYY
                    'fuente': str,  # Carpeta principal
                    'contexto': str  # Ruta completa del archivo
                }
        """
        pass
    
    def get_source_info(self) -> tuple[str, str]:
        """
        Extrae la información de fuente y contexto del archivo.
        
        Returns:
            tuple[str, str]: (fuente, contexto)
        """
        # El contexto es la ruta completa
        contexto = str(self.file_path.absolute())
        
        # La fuente es la carpeta principal (primer nivel después de 'fuentes')
        try:
            # Busca la carpeta 'fuentes' en la ruta
            parts = self.file_path.parts
            fuentes_idx = parts.index('fuentes')
            fuente = parts[fuentes_idx + 1] if fuentes_idx + 1 < len(parts) else 'desconocido'
        except ValueError:
            # Si no encuentra 'fuentes', usa el nombre de la carpeta padre
            fuente = self.file_path.parent.name
            
        return fuente, contexto 