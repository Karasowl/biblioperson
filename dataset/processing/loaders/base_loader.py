from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Dict, Any, List, Optional

class BaseLoader(ABC):
    """Clase base abstracta para todos los loaders de documentos."""
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el archivo, devolviendo los bloques de contenido y metadatos del documento.
        
        Returns:
            Dict[str, Any]: Un diccionario con las siguientes claves:
                'blocks': List[Dict[str, Any]], donde cada diccionario de bloque tiene:
                    'text': str, # El contenido textual del bloque.
                    'order_in_document': int, # El índice secuencial del bloque.
                    # ... (otros metadatos específicos del bloque pueden incluirse aquí)
                'document_metadata': Dict[str, Any], con información como:
                    'source_file_path': str,
                    'file_format': str, # ej. 'txt', 'docx'
                    'detected_date': Optional[str], # YYYY-MM-DD
                    'original_fuente': str, # Carpeta principal (de get_source_info)
                    'original_contexto': str # Ruta completa (de get_source_info)
                    # ... (otros metadatos a nivel de documento)
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