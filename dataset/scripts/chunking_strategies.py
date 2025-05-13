import logging
import re # Para CustomEGWSplitterStrategy
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class ChunkingStrategy(ABC):
    """
    Clase base abstracta para diferentes estrategias de división de contenido (chunking).
    """
    def __init__(self, chunking_config: Optional[Dict[str, Any]] = None):
        """
        Inicializa la estrategia con su configuración específica.

        Args:
            chunking_config: Diccionario de configuración para la estrategia de chunking
                             (ej. min_size, regex, etc.), proveniente del perfil de contenido.
        """
        self.config = chunking_config or {}
        # Ejemplo de un parámetro común que podría estar en chunking_config
        self.min_chunk_size = self.config.get("min_chunk_size", 50) 

    @abstractmethod
    def chunk(self, content: Union[str, Dict[str, Any]], file_path: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """
        Divide el contenido (texto o un objeto JSON) en chunks.

        Cada chunk se devuelve como un diccionario.
        - Para estrategias basadas en texto, el diccionario podría ser {'text_content': str_chunk}.
        - Para estrategias basadas en objetos (como JsonObjectAsItemStrategy), el diccionario
          devuelto es el objeto JSON en sí mismo.

        Args:
            content: El contenido a dividir. Puede ser una cadena de texto completa (ej. Markdown)
                     o un único objeto JSON (si la fuente es json_like).
            file_path: Ruta opcional al archivo original, para logging o contexto.

        Yields:
            Iterador de diccionarios, donde cada diccionario representa un chunk.
        """
        pass

class ParagraphChunkerStrategy(ChunkingStrategy):
    """Divide el texto en párrafos (separados por líneas en blanco)."""
    def chunk(self, content: Union[str, Dict[str, Any]], file_path: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        if not isinstance(content, str):
            logger.error(f"ParagraphChunkerStrategy expects string content, but received {type(content)} for file {file_path}. Skipping chunking for this content.")
            return
        
        lines = content.splitlines()
        current_paragraph_lines = []
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line: 
                if current_paragraph_lines:
                    paragraph_text = "\n".join(current_paragraph_lines).strip()
                    if len(paragraph_text) >= self.min_chunk_size:
                        yield {"text_content": paragraph_text}
                    elif paragraph_text: 
                        logger.debug(f"Short paragraph (len {len(paragraph_text)}) found in {file_path}, smaller than min_chunk_size {self.min_chunk_size}.")
                        yield {"text_content": paragraph_text}
                    current_paragraph_lines = []
            else:
                current_paragraph_lines.append(line)
        
        if current_paragraph_lines:
            paragraph_text = "\n".join(current_paragraph_lines).strip()
            if len(paragraph_text) >= self.min_chunk_size:
                yield {"text_content": paragraph_text}
            elif paragraph_text:
                logger.debug(f"Short paragraph (len {len(paragraph_text)}) at end of file {file_path}, smaller than min_chunk_size {self.min_chunk_size}.")
                yield {"text_content": paragraph_text}

class WholeDocumentAsItemStrategy(ChunkingStrategy):
    """Trata todo el contenido del documento (texto) como un único chunk."""
    def chunk(self, content: Union[str, Dict[str, Any]], file_path: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        if not isinstance(content, str):
            logger.error(f"WholeDocumentAsItemStrategy expects string content, but received {type(content)} for file {file_path}. Skipping.")
            return
        
        trimmed_content = content.strip()
        if trimmed_content: 
            yield {"text_content": trimmed_content}
        else:
            logger.info(f"WholeDocumentAsItemStrategy found no content after stripping for file {file_path}.")

class JsonObjectAsItemStrategy(ChunkingStrategy):
    """
    Trata un objeto JSON (ya parseado) como un único item/chunk.
    Esta estrategia no divide texto, sino que pasa el objeto JSON.
    """
    def chunk(self, content: Union[str, Dict[str, Any]], file_path: Optional[str] = None, profile_cfg: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        if not isinstance(content, dict):
            logger.error(f"JsonObjectAsItemStrategy expects a dictionary (JSON object), but received {type(content)} for file {file_path}. Skipping.")
            return
        yield content

class CustomEGWSplitterStrategy(ChunkingStrategy):
    """
    Divide un texto de Ellen G. White en secciones basadas en referencias
    tipo {PVGM 12.3}.  Cada referencia se detecta con un regex configurable.

    chunking_config opcional:
        {
            "reference_regex": r"{\([A-Z]{2,5})\\\\s+(\\\\d{1,3}\\\\. \\\\d{1,3})}\",
            "keep_reference_in_text": true
        }
    """

    DEFAULT_REGEX = r"{\\\\s*([A-Z]{2,5})\\\\s+(\\\\d{1,3}\\\\. \\\\d{1,3})\\\\s*}"

    def __init__(self, chunking_config: Optional[Dict[str, Any]] = None):
        super().__init__(chunking_config)
        pattern = self.config.get("reference_regex", self.DEFAULT_REGEX)
        self.keep_reference = self.config.get("keep_reference_in_text", True)
        try:
            self._ref_re = re.compile(pattern, re.MULTILINE)
            logger.info(f"CustomEGWSplitterStrategy initialized with regex: {pattern}")
        except re.error as e:
            logger.error(f"Invalid regex pattern for CustomEGWSplitterStrategy: {pattern}. Error: {e}. Using default regex.")
            self._ref_re = re.compile(self.DEFAULT_REGEX, re.MULTILINE)

    def chunk(self, content: Union[str, Dict[str, Any]], file_path: Optional[str] = None, profile_cfg: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """
        Devuelve dicts con:
          • text_content
          • source_document_pointer_hint  (p.ej. PVGM 12.3)
        """
        if not isinstance(content, str):
            logger.error(f"CustomEGWSplitterStrategy expects string content, but received {type(content)} for file {file_path}. Skipping.")
            return

        if not content.strip():
            logger.debug(f"CustomEGWSplitterStrategy received empty content for {file_path}. No chunks produced.")
            return

        matches = list(self._ref_re.finditer(content))
        if not matches:
            # sin referencias → todo el documento como un chunk
            logger.debug(f"No EGW references found in {file_path} with regex. Yielding whole content as one chunk.")
            yield {"text_content": content.strip()}
            return

        # Recorremos las coincidencias y cortamos de ref a ref
        logger.debug(f"Found {len(matches)} EGW references in {file_path}.")
        for idx, match in enumerate(matches):
            ref_code = f"{match.group(1)} {match.group(2)}"  # ej. PVGM 12.3
            
            # Determinar el inicio del texto del chunk
            # Si keep_reference es True, el chunk comienza CON la referencia.
            # Si es False, comienza DESPUÉS de la referencia.
            chunk_start_pos = match.start() if self.keep_reference else match.end()

            # Determinar el final del texto del chunk
            # Es el inicio de la SIGUIENTE referencia, o el final del contenido si es la última ref.
            chunk_end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            
            chunk_text = content[chunk_start_pos:chunk_end_pos].strip()

            if not chunk_text:
                logger.debug(f"Empty chunk generated for reference '{ref_code}' in {file_path}. Skipping.")
                continue

            yield {
                "text_content": chunk_text,
                "source_document_pointer_hint": ref_code,
            }

# --- Registro y Factory para Estrategias ---
STRATEGY_REGISTRY: Dict[str, type[ChunkingStrategy]] = {
    "ParagraphChunkerStrategy": ParagraphChunkerStrategy,
    "WholeDocumentAsItemStrategy": WholeDocumentAsItemStrategy,
    "JsonObjectAsItemStrategy": JsonObjectAsItemStrategy,
    "CustomEGWSplitterStrategy": CustomEGWSplitterStrategy,
}

def get_chunking_strategy(strategy_name: str, chunking_config: Optional[Dict[str, Any]] = None) -> ChunkingStrategy:
    """
    Factory function para obtener una instancia de una ChunkingStrategy.
    """
    strategy_class = STRATEGY_REGISTRY.get(strategy_name)
    if not strategy_class:
        logger.error(f"Unknown chunking strategy name: '{strategy_name}'. Available strategies: {list(STRATEGY_REGISTRY.keys())}")
        raise ValueError(f"Unknown chunking strategy: {strategy_name}")
    
    logger.info(f"Instantiating chunking strategy: {strategy_name}")
    return strategy_class(chunking_config)
