from typing import Dict, List, Any, Optional
import logging
import re

# Import absoluto para evitar problemas con carga dinámica
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataset.processing.segmenters.base import BaseSegmenter

class BiblicalVerseSegmentationSegmenter(BaseSegmenter):
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    def segment(self, blocks, document_metadata_from_loader=None):
        segments = []
        
        try:
            for i, block in enumerate(blocks):
                if isinstance(block, dict):
                    text = block.get('content', '') or block.get('text', '')
                else:
                    text = str(block)
                
                if not text.strip():
                    continue
                
                # Segmentación básica por párrafos
                paragraphs = text.split('\n\n')
                for j, paragraph in enumerate(paragraphs):
                    if paragraph.strip():
                        segments.append({
                            'content': paragraph.strip(),
                            'type': 'segment',
                            'index': len(segments),
                            'metadata': {
                                'block_index': i,
                                'paragraph_index': j
                            }
                        })
            
            self.logger.info(f"Segmentación completada: {len(segments)} segmentos")
            
        except Exception as e:
            self.logger.error(f"Error en segmentación: {str(e)}")
            # Fallback básico
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
                        'metadata': {'error': str(e)}
                    })
        
        return segments
