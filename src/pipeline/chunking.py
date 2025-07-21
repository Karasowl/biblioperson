"""
Módulo de chunking usando LangChain
Divide documentos en chunks optimizados para embeddings
"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# LangChain imports
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    LatexTextSplitter
)
from langchain.schema import Document

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuración para chunking"""
    chunk_size: int
    chunk_overlap: int
    separators: List[str]
    keep_separator: bool = True
    add_start_index: bool = True


class DocumentChunker:
    """
    Clase para dividir documentos en chunks usando LangChain
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el chunker con configuración
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config = self._load_config(config_path)
        self.splitters = self._initialize_splitters()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Carga la configuración desde archivo YAML"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # Configuración por defecto
            return {
                "chunking": {
                    "default_chunk_size": 750,
                    "default_overlap": 200,
                    "profiles": {
                        "narrative": {"chunk_size": 750, "overlap": 200},
                        "poetry": {"chunk_size": 500, "overlap": 150},
                        "technical": {"chunk_size": 1000, "overlap": 250},
                        "dialogue": {"chunk_size": 600, "overlap": 150},
                        "biblical": {"chunk_size": 500, "overlap": 100}
                    }
                },
                "text_splitter": {
                    "type": "recursive",
                    "separators": ["\n\n", "\n", ". ", ", ", " ", ""],
                    "keep_separator": True,
                    "add_start_index": True
                },
                "limits": {
                    "max_chunk_size": 2000,
                    "min_chunk_size": 100,
                    "max_chunks_per_document": 10000
                }
            }
    
    def _initialize_splitters(self) -> Dict[str, Any]:
        """Inicializa diferentes tipos de splitters"""
        splitters = {}
        
        # Configuración base
        base_config = {
            "separators": self.config["text_splitter"]["separators"],
            "keep_separator": self.config["text_splitter"]["keep_separator"],
            "add_start_index": self.config["text_splitter"]["add_start_index"]
        }
        
        # Splitter recursivo (principal)
        for profile_name, profile_config in self.config["chunking"]["profiles"].items():
            splitters[profile_name] = RecursiveCharacterTextSplitter(
                chunk_size=profile_config["chunk_size"],
                chunk_overlap=profile_config["overlap"],
                **base_config
            )
        
        # Splitters especializados
        splitters["markdown"] = MarkdownTextSplitter(
            chunk_size=self.config["chunking"]["default_chunk_size"],
            chunk_overlap=self.config["chunking"]["default_overlap"]
        )
        
        splitters["code"] = PythonCodeTextSplitter(
            chunk_size=self.config["chunking"]["default_chunk_size"],
            chunk_overlap=self.config["chunking"]["default_overlap"]
        )
        
        splitters["latex"] = LatexTextSplitter(
            chunk_size=self.config["chunking"]["default_chunk_size"],
            chunk_overlap=self.config["chunking"]["default_overlap"]
        )
        
        # Splitter por defecto
        splitters["default"] = RecursiveCharacterTextSplitter(
            chunk_size=self.config["chunking"]["default_chunk_size"],
            chunk_overlap=self.config["chunking"]["default_overlap"],
            **base_config
        )
        
        return splitters
    
    def chunk_text(self, 
                   text: str, 
                   profile: str = "default",
                   metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Divide un texto en chunks según el perfil especificado
        
        Args:
            text: Texto a dividir
            profile: Perfil de chunking a usar
            metadata: Metadatos adicionales para los chunks
            
        Returns:
            Lista de Documents de LangChain
        """
        # Seleccionar splitter
        splitter = self.splitters.get(profile, self.splitters["default"])
        
        # Crear documento base
        base_metadata = metadata or {}
        base_metadata["profile"] = profile
        
        # Dividir texto
        if self.config["text_splitter"]["add_start_index"]:
            # Crear documentos con índices de inicio
            chunks = splitter.create_documents(
                texts=[text],
                metadatas=[base_metadata]
            )
        else:
            # División simple
            texts = splitter.split_text(text)
            chunks = [
                Document(
                    page_content=chunk_text,
                    metadata={**base_metadata, "chunk_index": i}
                )
                for i, chunk_text in enumerate(texts)
            ]
        
        # Validar tamaños
        chunks = self._validate_chunk_sizes(chunks)
        
        # Agregar metadatos adicionales
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{profile}_{i}"
            chunk.metadata["chunk_size"] = len(chunk.page_content)
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks
    
    def chunk_documents(self,
                       documents: List[Document],
                       profile: str = "default") -> List[Document]:
        """
        Divide una lista de documentos LangChain en chunks
        
        Args:
            documents: Lista de Documents
            profile: Perfil de chunking
            
        Returns:
            Lista de Documents divididos
        """
        splitter = self.splitters.get(profile, self.splitters["default"])
        
        # Dividir documentos preservando metadatos
        all_chunks = []
        for doc_idx, doc in enumerate(documents):
            # Preservar metadatos del documento original
            doc_metadata = doc.metadata.copy()
            doc_metadata["source_doc_index"] = doc_idx
            
            # Dividir
            chunks = splitter.split_documents([doc])
            
            # Actualizar metadatos
            for chunk_idx, chunk in enumerate(chunks):
                chunk.metadata.update(doc_metadata)
                chunk.metadata["chunk_index"] = chunk_idx
                chunk.metadata["profile"] = profile
            
            all_chunks.extend(chunks)
        
        return self._validate_chunk_sizes(all_chunks)
    
    def chunk_markdown(self, markdown_text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Especializado para dividir Markdown preservando estructura
        """
        splitter = self.splitters["markdown"]
        
        # Crear documento
        doc = Document(
            page_content=markdown_text,
            metadata=metadata or {}
        )
        
        # Dividir
        chunks = splitter.split_documents([doc])
        
        # Agregar metadatos
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"markdown_{i}"
            chunk.metadata["chunk_size"] = len(chunk.page_content)
            chunk.metadata["format"] = "markdown"
        
        return chunks
    
    def chunk_by_elements(self,
                         elements: List[Dict[str, Any]],
                         profile: str = "default") -> List[Document]:
        """
        Divide elementos estructurales en chunks
        
        Args:
            elements: Lista de elementos de unstructured
            profile: Perfil de chunking
            
        Returns:
            Lista de Documents
        """
        # Agrupar elementos por tipo y proximidad
        grouped_elements = self._group_elements(elements)
        
        # Convertir grupos a chunks
        chunks = []
        for group_idx, group in enumerate(grouped_elements):
            # Concatenar texto del grupo
            text_parts = []
            element_types = set()
            
            for elem in group:
                text_parts.append(elem.get("text", ""))
                element_types.add(elem.get("type", "Unknown"))
            
            combined_text = "\n\n".join(text_parts)
            
            # Determinar perfil basado en tipos de elementos
            if "Title" in element_types:
                current_profile = "narrative"
            elif "ListItem" in element_types:
                current_profile = "technical"
            else:
                current_profile = profile
            
            # Crear documento
            doc = Document(
                page_content=combined_text,
                metadata={
                    "group_index": group_idx,
                    "element_types": list(element_types),
                    "element_count": len(group),
                    "profile": current_profile
                }
            )
            
            # Si el grupo es pequeño, agregarlo directamente
            if len(combined_text) < self.config["chunking"]["default_chunk_size"]:
                chunks.append(doc)
            else:
                # Dividir grupos grandes
                sub_chunks = self.chunk_text(combined_text, current_profile, doc.metadata)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _group_elements(self, elements: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Agrupa elementos estructurales por proximidad y tipo
        """
        if not elements:
            return []
        
        groups = []
        current_group = [elements[0]]
        current_size = len(elements[0].get("text", ""))
        
        for elem in elements[1:]:
            elem_text = elem.get("text", "")
            elem_size = len(elem_text)
            
            # Decidir si agregar al grupo actual o crear uno nuevo
            if (current_size + elem_size < self.config["chunking"]["default_chunk_size"] and
                elem.get("type") not in ["Title", "PageBreak"]):
                # Agregar al grupo actual
                current_group.append(elem)
                current_size += elem_size
            else:
                # Crear nuevo grupo
                groups.append(current_group)
                current_group = [elem]
                current_size = elem_size
        
        # Agregar último grupo
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _validate_chunk_sizes(self, chunks: List[Document]) -> List[Document]:
        """
        Valida y ajusta tamaños de chunks según límites configurados
        """
        validated_chunks = []
        min_size = self.config["limits"]["min_chunk_size"]
        max_size = self.config["limits"]["max_chunk_size"]
        
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            chunk_size = len(chunk.page_content)
            
            if chunk_size < min_size and i < len(chunks) - 1:
                # Fusionar con el siguiente chunk si es muy pequeño
                next_chunk = chunks[i + 1]
                combined_content = chunk.page_content + "\n\n" + next_chunk.page_content
                
                if len(combined_content) <= max_size:
                    # Crear chunk combinado
                    combined_chunk = Document(
                        page_content=combined_content,
                        metadata={
                            **chunk.metadata,
                            "merged": True,
                            "original_chunks": [chunk.metadata, next_chunk.metadata]
                        }
                    )
                    validated_chunks.append(combined_chunk)
                    i += 2  # Saltar ambos chunks
                    continue
            
            elif chunk_size > max_size:
                # Dividir chunk muy grande
                sub_splitter = CharacterTextSplitter(
                    chunk_size=max_size,
                    chunk_overlap=self.config["chunking"]["default_overlap"],
                    separator=" "
                )
                sub_chunks = sub_splitter.split_documents([chunk])
                
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata["split_from_large"] = True
                    sub_chunk.metadata["sub_chunk_index"] = j
                
                validated_chunks.extend(sub_chunks)
                i += 1
                continue
            
            # Chunk de tamaño válido
            validated_chunks.append(chunk)
            i += 1
        
        # Verificar límite total de chunks
        max_chunks = self.config["limits"]["max_chunks_per_document"]
        if len(validated_chunks) > max_chunks:
            logger.warning(f"Documento excede límite de chunks ({len(validated_chunks)} > {max_chunks})")
            # Opcionalmente, truncar o combinar chunks
        
        return validated_chunks
    
    def detect_content_type(self, text: str) -> str:
        """
        Detecta el tipo de contenido para seleccionar el perfil adecuado
        
        Returns:
            Nombre del perfil recomendado
        """
        # Heurísticas simples
        lines = text.split('\n')
        
        # Detectar poesía (líneas cortas, posible rima)
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        if avg_line_length < 50 and len(lines) > 5:
            short_lines = sum(1 for line in lines if 10 < len(line) < 60)
            if short_lines / len(lines) > 0.7:
                return "poetry"
        
        # Detectar diálogo (guiones, comillas)
        dialogue_markers = sum(1 for line in lines if line.strip().startswith(('—', '-', '"', '«')))
        if dialogue_markers / max(len(lines), 1) > 0.3:
            return "dialogue"
        
        # Detectar contenido técnico (muchos números, código)
        technical_indicators = sum(1 for line in lines if any(char.isdigit() for char in line))
        if technical_indicators / max(len(lines), 1) > 0.4:
            return "technical"
        
        # Detectar contenido bíblico (referencias a libros, capítulos, versículos)
        biblical_keywords = ["génesis", "éxodo", "salmos", "mateo", "juan", "apocalipsis", 
                           "versículo", "capítulo", "libro"]
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in biblical_keywords):
            return "biblical"
        
        # Por defecto, narrativa
        return "narrative"


# Funciones de utilidad
def chunk_document(text: str, 
                  chunk_size: int = 750,
                  overlap: int = 200,
                  profile: Optional[str] = None) -> List[Document]:
    """
    Función de conveniencia para chunking rápido
    """
    chunker = DocumentChunker()
    
    # Auto-detectar perfil si no se especifica
    if profile is None:
        profile = chunker.detect_content_type(text)
        logger.info(f"Perfil detectado: {profile}")
    
    return chunker.chunk_text(text, profile)


def chunk_markdown(markdown_text: str) -> List[Document]:
    """
    Función de conveniencia para chunking de Markdown
    """
    chunker = DocumentChunker()
    return chunker.chunk_markdown(markdown_text)


def create_chunker(content_type: str = "narrative", 
                  chunk_size: int = 750, 
                  chunk_overlap: int = 200) -> RecursiveCharacterTextSplitter:
    """
    Crea un chunker específico para un tipo de contenido
    """
    if content_type == "poetry":
        chunk_size = 500
        chunk_overlap = 150
    elif content_type == "technical":
        chunk_size = 1000
        chunk_overlap = 250
    elif content_type == "biblical":
        chunk_size = 500
        chunk_overlap = 100
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        keep_separator=True,
        add_start_index=True
    )


if __name__ == "__main__":
    # Ejemplo de uso
    sample_text = """
    # Capítulo 1: Introducción
    
    Este es un texto de ejemplo para demostrar el funcionamiento del chunking.
    Contiene varios párrafos y secciones que serán divididas inteligentemente.
    
    ## Sección 1.1: Conceptos básicos
    
    El chunking es el proceso de dividir textos largos en fragmentos más pequeños
    y manejables. Esto es especialmente útil para:
    
    - Procesamiento con modelos de lenguaje
    - Búsqueda semántica
    - Indexación eficiente
    
    ## Sección 1.2: Implementación
    
    La implementación utiliza LangChain para proporcionar diferentes estrategias
    de división según el tipo de contenido.
    """
    
    # Crear chunker
    chunker = DocumentChunker()
    
    # Detectar tipo de contenido
    content_type = chunker.detect_content_type(sample_text)
    print(f"Tipo de contenido detectado: {content_type}")
    
    # Crear chunks
    chunks = chunker.chunk_text(sample_text, profile=content_type)
    
    # Mostrar resultados
    print(f"\nNúmero de chunks creados: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Tamaño: {chunk.metadata['chunk_size']} caracteres")
        print(f"Contenido: {chunk.page_content[:100]}...")
        print(f"Metadatos: {chunk.metadata}") 