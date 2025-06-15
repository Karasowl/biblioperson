#!/usr/bin/env python3
"""
Markdown Segmenter - Segmentación CONSERVADORA basada en estructura visual

Respeta la estructura del MarkdownPDFLoader siendo MUY conservador en la fusión.
Principio: Cuando hay duda, mantener separado.
"""

import logging
import re
from typing import List, Dict, Any
import uuid

logger = logging.getLogger(__name__)

class MarkdownSegmenter:
    """
    Segmentador CONSERVADOR que respeta la estructura del MarkdownPDFLoader
    """
    
    def __init__(self, config=None, **kwargs):
        """
        Inicializar el segmentador conservador
        
        Args:
            config: Diccionario de configuración
            **kwargs: Argumentos de configuración adicionales
        """
        self.config = config or {}
        
        # Configuración CONSERVADORA
        self.min_segment_length = self.config.get('min_segment_length', 50)
        self.max_segment_length = self.config.get('max_segment_length', 8000)
        
        # Umbrales ESTRICTOS para fusión
        self.max_fusion_gap = 10.0  # Gap vertical máximo para fusión (muy estricto)
        self.min_continuation_length = 20  # Longitud mínima para considerar continuación
        
        logger.info("MarkdownSegmenter inicializado en modo CONSERVADOR")
    
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segmentar bloques de manera CONSERVADORA
        
        Args:
            blocks: Lista de bloques del MarkdownPDFLoader
            
        Returns:
            Lista de segmentos conservadores
        """
        if not blocks:
            return []
        
        logger.info(f"🔄 Iniciando segmentación CONSERVADORA de {len(blocks)} bloques")
        
        # Filtrar bloques válidos
        valid_blocks = self._filter_valid_blocks(blocks)
        logger.info(f"📋 Bloques válidos después del filtrado: {len(valid_blocks)}")
        
        # Aplicar fusión CONSERVADORA
        merged_blocks = self._conservative_merge(valid_blocks)
        logger.info(f"🔗 Bloques después de fusión conservadora: {len(merged_blocks)}")
        
        # Convertir a segmentos finales
        segments = self._blocks_to_segments(merged_blocks)
        logger.info(f"✅ Segmentos finales generados: {len(segments)}")
        
        return segments
    
    def _filter_valid_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtrar bloques válidos (eliminar vacíos, muy cortos, etc.)
        """
        valid_blocks = []
        
        for block in blocks:
            text = block.get('text', '').strip()
            
            # Saltar bloques vacíos
            if not text:
                continue
            
            # Saltar bloques muy cortos (probablemente ruido)
            if len(text) < 10:
                continue
            
            # Saltar números de página aislados
            if re.match(r'^\d+$', text):
                continue
            
            # Saltar líneas de solo puntuación
            if re.match(r'^[^\w\s]*$', text):
                continue
            
            valid_blocks.append(block)
        
        return valid_blocks
    
    def _conservative_merge(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fusión CONSERVADORA de bloques - solo fusiona cuando es OBVIO
        """
        if not blocks:
            return []
        
        # PASO 1: Subdividir bloques largos ANTES de fusionar
        subdivided_blocks = []
        for block in blocks:
            sub_blocks = self._subdivide_long_block(block)
            subdivided_blocks.extend(sub_blocks)
        
        logger.info(f"📋 Subdivisión: {len(blocks)} → {len(subdivided_blocks)} bloques")
        
        # PASO 2: Aplicar fusión conservadora a los bloques subdivididos
        merged = []
        current_group = [subdivided_blocks[0]]
        
        for i in range(1, len(subdivided_blocks)):
            current_block = subdivided_blocks[i]
            previous_block = subdivided_blocks[i-1]
            
            # Decidir si fusionar con el grupo actual
            if self._should_merge_conservative(previous_block, current_block):
                current_group.append(current_block)
            else:
                # Finalizar grupo actual y empezar uno nuevo
                merged.append(self._merge_block_group(current_group))
                current_group = [current_block]
        
        # Agregar el último grupo
        if current_group:
            merged.append(self._merge_block_group(current_group))
        
        return merged
    
    def _subdivide_long_block(self, block: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Subdivide bloques largos que contienen múltiples elementos semánticos
        """
        text = block.get('text', '').strip()
        
        # Si es corto, no subdividir
        if len(text) < 600:
            return [block]
        
        # Buscar puntos de división naturales
        split_points = []
        lines = text.split('\n')
        
        current_pos = 0
        accumulated_text = ""
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Detectar puntos de división naturales
            is_split_point = (
                # Títulos en negrita
                (line_stripped.startswith('**') and line_stripped.endswith('**') and len(line_stripped) > 4) or
                # Líneas que parecen diálogos
                (line_stripped.startswith('"') or line_stripped.startswith('—') or line_stripped.startswith('-')) or
                # Cambios de párrafo con indentación
                (line_stripped and not line_stripped[0].islower() and len(accumulated_text) > 200) or
                # Líneas que empiezan con mayúscula después de acumulación significativa
                (line_stripped and line_stripped[0].isupper() and len(accumulated_text) > 300 and 
                 not accumulated_text.strip().endswith(','))
            )
            
            if is_split_point and accumulated_text.strip():
                # Guardar punto de división
                split_points.append(len(accumulated_text.strip()))
                accumulated_text = line + '\n'
            else:
                accumulated_text += line + '\n'
        
        # Si no hay puntos de división naturales, no subdividir
        if not split_points:
            logger.debug(f"🔍 Bloque largo ({len(text)} chars) sin puntos de división naturales")
            return [block]
        
        # Crear sub-bloques
        sub_blocks = []
        start_pos = 0
        
        for split_pos in split_points:
            if split_pos > start_pos:
                sub_text = text[start_pos:split_pos].strip()
                if sub_text:
                    sub_block = block.copy()
                    sub_block['text'] = sub_text
                    sub_blocks.append(sub_block)
                start_pos = split_pos
        
        # Agregar el último fragmento
        remaining_text = text[start_pos:].strip()
        if remaining_text:
            sub_block = block.copy()
            sub_block['text'] = remaining_text
            sub_blocks.append(sub_block)
        
        logger.info(f"🔪 Subdividido bloque de {len(text)} chars → {len(sub_blocks)} sub-bloques")
        return sub_blocks
    
    def _should_merge_conservative(self, block1: Dict[str, Any], block2: Dict[str, Any]) -> bool:
        """
        Criterios BALANCEADOS para fusión - conservador pero no excesivo
        """
        text1 = block1.get('text', '').strip()
        text2 = block2.get('text', '').strip()
        
        # NO fusionar si alguno está vacío
        if not text1 or not text2:
            return False
        
        # NO fusionar si hay títulos o encabezados
        if self._is_title_or_header(text1) or self._is_title_or_header(text2):
            return False
        
        # NO fusionar si hay cambio de estilo narrativo
        if self._has_style_change(text1, text2):
            return False
        
        # NO fusionar si el gap vertical es MUY grande
        gap = self._get_vertical_gap(block1, block2)
        if gap > self.max_fusion_gap:
            return False
        
        # SÍ fusionar si es claramente continuación de la misma oración
        if self._is_clear_continuation(text1, text2):
            return True
        
        # SÍ fusionar si ambos son texto normal (no títulos) y están cerca
        if self._are_normal_text_blocks(text1, text2) and gap <= 5.0:
            return True
        
        # NO fusionar en otros casos
        return False
    
    def _is_title_or_header(self, text: str) -> bool:
        """
        Detectar títulos o encabezados usando estructura markdown y patrones semánticos
        """
        text_stripped = text.strip()
        
        # 1. ENCABEZADOS MARKDOWN (###, ####, etc.)
        if re.match(r'^#{1,6}\s+', text_stripped):
            return True
        
        # 2. TEXTO EN NEGRITA QUE PARECE TÍTULO/SECCIÓN
        # Detectar **TEXTO** que parece encabezado de sección
        bold_pattern = r'^\*\*([^*]+)\*\*$'
        bold_match = re.match(bold_pattern, text_stripped)
        if bold_match:
            bold_content = bold_match.group(1).strip()
            # Si está en mayúsculas o parece título de sección
            if (bold_content.isupper() or 
                len(bold_content) < 100 or
                any(indicator in bold_content.lower() for indicator in 
                    ['radio', 'capítulo', 'parte', 'sección', 'prólogo', 'epílogo', 'miércoles', 'lunes', 'martes', 'jueves', 'viernes', 'sábado', 'domingo'])):
                return True
        
        # 3. TEXTO TODO EN MAYÚSCULAS (probable título)
        if text_stripped.isupper() and len(text_stripped) > 5:
            return True
        
        # 4. PATRONES DE TÍTULOS TRADICIONALES
        if len(text_stripped) < 100 and not text_stripped.endswith('.'):
            title_indicators = ['capítulo', 'parte', 'sección', 'prólogo', 'epílogo']
            if any(indicator in text_stripped.lower() for indicator in title_indicators):
                return True
        
        # 5. PATRONES DE FECHA/LUGAR QUE INDICAN NUEVA SECCIÓN
        # Ej: "RADIO EXTERIOR DE ESPAÑA. MIÉRCOLES 13 MARZO"
        date_place_patterns = [
            r'[A-Z\s]+\.\s+(LUNES|MARTES|MIÉRCOLES|JUEVES|VIERNES|SÁBADO|DOMINGO)',
            r'[A-Z\s]+\s+\d{1,2}\s+(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)',
            r'^[A-Z\s]{10,}\.$'  # Texto largo en mayúsculas terminado en punto
        ]
        
        for pattern in date_place_patterns:
            if re.search(pattern, text_stripped, re.IGNORECASE):
                return True
        
        return False
    
    def _has_style_change(self, text1: str, text2: str) -> bool:
        """
        Detectar cambios de estilo narrativo
        """
        # Cambio de narrativa a diálogo
        if not text1.startswith('—') and text2.startswith('—'):
            return True
        
        # Cambio de diálogo a narrativa
        if text1.startswith('—') and not text2.startswith('—'):
            return True
        
        # Cambio de descripción a diálogo directo
        dialogue_patterns = [r'^[A-Z][^.]*[?!]$', r'^¿.*\?$', r'^¡.*!$']
        is_dialogue1 = any(re.match(pattern, text1) for pattern in dialogue_patterns)
        is_dialogue2 = any(re.match(pattern, text2) for pattern in dialogue_patterns)
        
        if is_dialogue1 != is_dialogue2:
            return True
        
        return False
    
    def _get_vertical_gap(self, block1: Dict[str, Any], block2: Dict[str, Any]) -> float:
        """
        Calcular gap vertical entre bloques
        """
        meta1 = block1.get('metadata', {})
        meta2 = block2.get('metadata', {})
        
        # Si no hay metadatos de posición, asumir gap pequeño
        if 'bbox' not in meta1 or 'bbox' not in meta2:
            return 5.0
        
        bbox1 = meta1['bbox']
        bbox2 = meta2['bbox']
        
        # Calcular gap vertical
        gap = bbox2[1] - bbox1[3]  # top del segundo - bottom del primero
        return max(0, gap)
    
    def _is_clear_continuation(self, text1: str, text2: str) -> bool:
        """
        Verificar si text2 es claramente continuación de text1
        """
        # El primer texto debe terminar sin punto (oración incompleta)
        if text1.endswith('.'):
            return False
        
        # El segundo texto debe ser suficientemente largo
        if len(text2) < self.min_continuation_length:
            return False
        
        # El segundo texto no debe empezar con mayúscula (no es nueva oración)
        if text2[0].isupper():
            return False
        
        # Verificar palabras de continuación
        continuation_words = ['y', 'o', 'pero', 'sin embargo', 'además', 'también', 'que', 'de', 'en', 'con']
        first_word = text2.split()[0].lower()
        
        return first_word in continuation_words
    
    def _are_normal_text_blocks(self, text1: str, text2: str) -> bool:
        """
        Verificar si ambos bloques son texto normal (no títulos, no diálogos especiales)
        """
        # No son títulos
        if self._is_title_or_header(text1) or self._is_title_or_header(text2):
            return False
        
        # No son diálogos con guiones
        if text1.startswith('—') or text2.startswith('—'):
            return False
        
        # No son preguntas/exclamaciones aisladas
        if (text1.endswith('?') or text1.endswith('!')) and len(text1) < 50:
            return False
        
        if (text2.endswith('?') or text2.endswith('!')) and len(text2) < 50:
            return False
        
        # Ambos son texto normal
        return True
    
    def _merge_block_group(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fusionar un grupo de bloques en uno solo
        """
        if not blocks:
            return {}
        
        if len(blocks) == 1:
            return blocks[0]
        
        # Combinar textos
        combined_text = ' '.join(block.get('text', '').strip() for block in blocks)
        
        # Usar metadatos del primer bloque
        base_block = blocks[0].copy()
        base_block['text'] = combined_text
        
        # Actualizar metadatos si es necesario
        if 'metadata' in base_block:
            base_block['metadata']['merged_blocks'] = len(blocks)
        
        return base_block
    
    def _blocks_to_segments(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convertir bloques finales a segmentos
        """
        segments = []
        
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            
            # Saltar bloques vacíos
            if not text:
                continue
            
            # Crear segmento
            segment = {
                'segment_id': str(uuid.uuid4()),
                'text': text,
                'segment_order': i + 1,
                'text_length': len(text),
                'segment_type': 'paragraph',
                'metadata': block.get('metadata', {}),
                'processing_notes': f"MarkdownSegmenter CONSERVADOR - bloque {i+1}"
            }
            
            segments.append(segment)
        
        return segments 