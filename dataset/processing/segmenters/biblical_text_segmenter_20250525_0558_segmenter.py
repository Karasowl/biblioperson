from typing import Dict, List, Any, Optional
import logging
import re

# Import absoluto para evitar problemas con carga dinámica
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataset.processing.segmenters.base import BaseSegmenter

class BiblicalTextSegmenter202505250558Segmenter(BaseSegmenter):
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Patrones robustos para texto bíblico
        self.verse_patterns = [
            r'(\d+)\s+([A-Z][^\n]*?)(?=\s*\d+\s+[A-Z]|$)',
            r'(\d+)\s*[:\.\-]\s*(\d+)\s+([^\n]*?)(?=\s*\d+\s*[:\.\-]\s*\d+|$)',
            r'^(\d+)\s+(.+?)$'
        ]
        
        self.book_patterns = [
            r'^([A-Z][A-Za-z\s]+)\s+(\d+)$',
            r'^([A-Z][A-Z\s]+)$'
        ]
    
    def segment(self, blocks, document_metadata_from_loader=None):
        segments = []
        current_book = "Libro Desconocido"
        current_chapter = 1
        
        try:
            for block_idx, block in enumerate(blocks):
                if isinstance(block, dict):
                    text = block.get('content', '') or block.get('text', '')
                else:
                    text = str(block)
                
                if not text.strip():
                    continue
                
                lines = text.split('\n')
                
                for line_idx, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    book_match = self._detect_book_chapter(line)
                    if book_match:
                        current_book = book_match.get('book', current_book)
                        current_chapter = book_match.get('chapter', current_chapter)
                        continue
                    
                    verse_match = self._detect_verse(line)
                    if verse_match:
                        segments.append({
                            'content': verse_match['text'],
                            'type': 'verse',
                            'index': len(segments),
                            'metadata': {
                                'book': current_book,
                                'chapter': current_chapter,
                                'verse': verse_match['verse'],
                                'block_index': block_idx,
                                'line_index': line_idx,
                                'segmentation_method': 'biblical_text_segmenter_20250525_0558'
                            }
                        })
                    else:
                        if len(line) > 10:
                            segments.append({
                                'content': line,
                                'type': 'text',
                                'index': len(segments),
                                'metadata': {
                                    'book': current_book,
                                    'chapter': current_chapter,
                                    'block_index': block_idx,
                                    'line_index': line_idx,
                                    'segmentation_method': 'biblical_text_segmenter_20250525_0558'
                                }
                            })
            
            self.logger.info(f"Segmentación completada: {len(segments)} segmentos")
            
        except Exception as e:
            self.logger.error(f"Error en segmentación: {str(e)}")
            for i, block in enumerate(blocks):
                if isinstance(block, dict):
                    text = block.get('content', '') or block.get('text', '')
                else:
                    text = str(block)
                
                if text.strip():
                    segments.append({
                        'content': text.strip(),
                        'type': 'fallback_segment',
                        'index': i,
                        'metadata': {
                            'error': str(e),
                            'segmentation_method': 'fallback'
                        }
                    })
        
        return segments
    
    def _detect_book_chapter(self, line: str) -> Optional[Dict[str, Any]]:
        for pattern in self.book_patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    return {'book': groups[0].strip(), 'chapter': int(groups[1])}
                else:
                    return {'book': groups[0].strip()}
        return None
    
    def _detect_verse(self, line: str) -> Optional[Dict[str, Any]]:
        for pattern in self.verse_patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    try:
                        verse_num = int(groups[0])
                        text = groups[-1].strip()
                        return {'verse': verse_num, 'text': text}
                    except ValueError:
                        continue
        return None
