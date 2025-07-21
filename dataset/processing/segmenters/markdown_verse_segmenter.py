#!/usr/bin/env python3
"""
Markdown Verse Segmenter - Segmentación específica para markdown estructurado

Diseñado para trabajar con markdown limpio de pymupdf4llm donde
los títulos están marcados con ## y la estructura es jerárquica.
"""

import logging
import re
from typing import Dict, List, Any, Optional

try:
    from .base import BaseSegmenter
except ImportError:
    # Fallback para cuando se ejecuta directamente
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from base import BaseSegmenter

logger = logging.getLogger(__name__)

class MarkdownVerseSegmenter(BaseSegmenter):
    """Segmentador optimizado para markdown estructurado de poemas"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Inicializar el segmentador de markdown"""
        super().__init__(config)
        self.logger = logging.getLogger(f"{__name__}.MarkdownVerseSegmenter")
        self.logger.warning("🎯 MARKDOWN VERSE SEGMENTER - SEGMENTACIÓN OPTIMIZADA PARA MARKDOWN")
    
    def segment(self, blocks: List[Dict[str, Any]], document_metadata_from_loader: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Segmentar bloques de markdown en poemas individuales
        
        Args:
            blocks: Lista de bloques de MarkdownPDFLoader
            
        Returns:
            Lista de segmentos de poemas
        """
        self.logger.info(f"MarkdownVerseSegmenter: Procesando {len(blocks)} bloques de markdown")
        
        segments = []
        current_poem = None
        current_content = []
        poem_id = 0
        
        for block in blocks:
            block_type = block.get('metadata', {}).get('type', 'unknown')
            text = block.get('text', '').strip()
            
            # DETECTAR TÍTULOS DE POEMAS
            if block_type == 'poem_title' or self._is_poem_title_block(block):
                # Guardar poema anterior si existe
                if current_poem and current_content:
                    segments.append(self._create_poem_segment(
                        poem_id, current_poem, current_content
                    ))
                    poem_id += 1
                
                # Iniciar nuevo poema
                current_poem = text
                current_content = []
                self.logger.debug(f"📝 Nuevo poema detectado: '{current_poem[:50]}'")
            
            # CONTENIDO DE POEMA
            elif block_type == 'content' and current_poem:
                if text:  # Solo agregar contenido no vacío
                    current_content.append(text)
            
            # TÍTULOS PRINCIPALES O OTROS ELEMENTOS
            elif block_type in ['title', 'section']:
                # Guardar poema anterior si existe
                if current_poem and current_content:
                    segments.append(self._create_poem_segment(
                        poem_id, current_poem, current_content
                    ))
                    poem_id += 1
                    current_poem = None
                    current_content = []
        
        # Guardar último poema
        if current_poem and current_content:
            segments.append(self._create_poem_segment(
                poem_id, current_poem, current_content
            ))
        
        self.logger.info(f"🎭 MarkdownVerseSegmenter: {len(segments)} poemas detectados")
        
        return segments
    
    def _is_poem_title_block(self, block: Dict[str, Any]) -> bool:
        """
        Verificar si un bloque es un título de poema
        
        Args:
            block: Bloque a verificar
            
        Returns:
            True si es título de poema
        """
        text = block.get('text', '').strip()
        block_type = block.get('metadata', {}).get('type', '')
        
        # Ya marcado como poem_title
        if block_type == 'poem_title':
            return True
        
        # Patrones específicos de títulos
        poem_patterns = [
            r'^Poema\s+\d+',  # "Poema 1", "Poema 20"
            r'^[IVX]+\.?\s*$',  # Números romanos
            r'^\d+\.?\s*$',  # Números arábigos solos
            r'.*[Cc]anción.*[Dd]esesperada.*',  # "Canción Desesperada"
            r'^La\s+Canción\s+Desesperada',  # Título específico
        ]
        
        for pattern in poem_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Heurística adicional: línea corta que parece título
        if (len(text) < 80 and 
            not text.endswith('.') and 
            ('poema' in text.lower() or 'canción' in text.lower())):
            return True
        
        return False
    
    def _create_poem_segment(self, poem_id: int, title: str, 
                           content_blocks: List[str]) -> Dict[str, Any]:
        """
        Crear un segmento de poema
        
        Args:
            poem_id: ID único del poema
            title: Título del poema
            content_blocks: Lista de bloques de contenido
            
        Returns:
            Diccionario del segmento
        """
        # Unir contenido
        full_content = '\n\n'.join(content_blocks).strip()
        
        # Crear contenido completo con título
        if title:
            complete_content = f"{title}\n\n{full_content}" if full_content else title
        else:
            complete_content = full_content
        
        # Estadísticas del contenido
        lines = complete_content.split('\n')
        verse_lines = [line for line in lines if line.strip() and not line.strip() == title]
        
        segment = {
            'id': f"poem_{poem_id + 1}",
            'content': complete_content,
            'metadata': {
                'type': 'poem',
                'title': title,
                'verse_lines': len(verse_lines),
                'total_lines': len(lines),
                'char_count': len(complete_content),
                'content_blocks': len(content_blocks),
                'segmenter': 'markdown_verse_segmenter',
                'extraction_method': 'markdown_structured'
            }
        }
        
        self.logger.debug(f"✅ Poema '{title[:30]}' → {len(verse_lines)} versos, {len(complete_content)} chars")
        
        return segment
    
    def _clean_poem_content(self, content: str) -> str:
        """
        Limpiar contenido de poema
        
        Args:
            content: Contenido crudo
            
        Returns:
            Contenido limpio
        """
        # Remover líneas vacías excesivas
        lines = content.split('\n')
        cleaned_lines = []
        
        prev_empty = False
        for line in lines:
            line = line.strip()
            if not line:
                if not prev_empty:  # Solo una línea vacía consecutiva
                    cleaned_lines.append('')
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        # Remover líneas vacías al inicio y final
        while cleaned_lines and not cleaned_lines[0]:
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def get_stats(self, segments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Obtener estadísticas de los segmentos
        
        Args:
            segments: Lista de segmentos procesados
            
        Returns:
            Diccionario con estadísticas
        """
        if not segments:
            return {
                'total_poems': 0,
                'total_verses': 0,
                'avg_verses_per_poem': 0,
                'total_chars': 0
            }
        
        total_verses = sum(seg.get('metadata', {}).get('verse_lines', 0) for seg in segments)
        total_chars = sum(seg.get('metadata', {}).get('char_count', 0) for seg in segments)
        
        return {
            'total_poems': len(segments),
            'total_verses': total_verses,
            'avg_verses_per_poem': total_verses / len(segments),
            'total_chars': total_chars,
            'segmenter': 'markdown_verse_segmenter'
        } 