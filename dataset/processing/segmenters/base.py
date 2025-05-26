from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseSegmenter(ABC):
    """
    Clase base para todos los segmentadores.
    
    Los segmentadores implementan algoritmos para dividir bloques de texto
    en unidades semánticas coherentes (poemas, párrafos, capítulos, etc.).
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el segmentador con su configuración.
        
        Args:
            config: Diccionario de configuración con thresholds y otros parámetros
        """
        self.config = config if config is not None else {}
        
    @abstractmethod
    def segment(self, blocks: List[Dict[str, Any]], document_metadata_from_loader: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Segmenta bloques de texto en unidades semánticas.
        
        Este método debe ser implementado por todas las subclases.
        
        Args:
            blocks: Lista de bloques de texto a segmentar.
            document_metadata_from_loader: Metadatos del documento proporcionados por el loader (opcional).
            
        Returns:
            Lista de unidades semánticas (poemas, párrafos, etc.)
        """
        raise NotImplementedError("Las subclases deben implementar segment()")

    def get_stats(self) -> Dict[str, Any]:
        """Devuelve estadísticas de la última operación de segmentación."""
        # Las clases hijas deben sobrescribir esto si tienen estadísticas específicas.
        return {} 