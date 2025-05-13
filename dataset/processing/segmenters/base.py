from typing import Dict, List, Any, Optional

class BaseSegmenter:
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
        self.config = config or {}
        
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segmenta bloques de texto en unidades semánticas.
        
        Este método debe ser implementado por todas las subclases.
        
        Args:
            blocks: Lista de bloques de texto con metadatos
            
        Returns:
            Lista de unidades semánticas (poemas, párrafos, etc.)
        """
        raise NotImplementedError("Las subclases deben implementar segment()") 