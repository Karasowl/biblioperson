import re
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import logging
from collections import defaultdict, Counter
from datetime import datetime

from .base import BaseSegmenter

# Importar el detector de autores
try:
    from ..author_detection import detect_author_in_segments, get_author_detection_config
except ImportError:
    # Fallback si no está disponible
    detect_author_in_segments = None
    get_author_detection_config = None

class HeadingState(Enum):
    """Estados posibles durante el procesamiento de estructura jerárquica."""
    INITIAL = 1           # Estado inicial, buscando cualquier contenido
    HEADING_FOUND = 2     # Encabezado encontrado, procesando sección
    COLLECTING_CONTENT = 3 # Recolectando contenido de la sección
    SECTION_END = 4       # Finalizando sección actual
    OUTSIDE_SECTION = 5   # Fuera de sección estructurada

class TitleDetector:
    """
    Detector inteligente de títulos que combina análisis visual y textual.
    """
    
    def __init__(self):
        self.title_keywords = {
            'spanish': [
                'introducción', 'conclusión', 'resumen', 'abstract', 'prefacio', 'prólogo', 'epílogo',
                'índice', 'bibliografía', 'referencias', 'apéndice', 'anexo', 'glosario',
                'capítulo', 'sección', 'parte', 'libro', 'título', 'subtítulo'
            ],
            'english': [
                'introduction', 'conclusion', 'summary', 'abstract', 'preface', 'prologue', 'epilogue',
                'index', 'bibliography', 'references', 'appendix', 'glossary', 'contents',
                'chapter', 'section', 'part', 'book', 'title', 'subtitle'
            ]
        }
        
        self.numbering_patterns = [
            r'^[IVXLCDM]+\.?\s+',  # Números romanos
            r'^\d+\.?\s+',  # Números arábigos
            r'^[A-Z]\.?\s+',  # Letras mayúsculas
            r'^[a-z][\.\)]\s+',  # Letras minúsculas
            r'^\d+\.\d+\.?\s+',  # Numeración decimal (1.1, 1.2)
            r'^\d+\.\d+\.\d+\.?\s+',  # Numeración triple (1.1.1)
        ]
    
    def analyze_visual_characteristics(self, blocks: List[Dict]) -> Dict[str, Any]:
        """
        Analiza las características visuales de todos los bloques para establecer baselines.
        """
        font_sizes = []
        text_lengths = []
        
        for block in blocks:
            visual_meta = block.get('visual_metadata', {})
            if visual_meta.get('avg_font_size'):
                font_sizes.append(visual_meta['avg_font_size'])
            if visual_meta.get('text_length'):
                text_lengths.append(visual_meta['text_length'])
        
        if font_sizes:
            avg_font_size = sum(font_sizes) / len(font_sizes)
            max_font_size = max(font_sizes)
            font_size_std = (sum((x - avg_font_size) ** 2 for x in font_sizes) / len(font_sizes)) ** 0.5
        else:
            avg_font_size = max_font_size = font_size_std = 12
            
        if text_lengths:
            avg_text_length = sum(text_lengths) / len(text_lengths)
        else:
            avg_text_length = 200
        
        return {
            'avg_font_size': avg_font_size,
            'max_font_size': max_font_size,
            'font_size_std': font_size_std,
            'avg_text_length': avg_text_length
        }
    
    def calculate_title_score(self, block: Dict, baseline_stats: Dict[str, Any]) -> float:
        """
        Calcula un score de 0-10 indicando qué tan probable es que el bloque sea un título.
        """
        text = block.get('text', '').strip()
        visual_meta = block.get('visual_metadata', {})
        
        if not text:
            return 0.0
        
        score = 0.0
        
        # === ANÁLISIS VISUAL === (peso: 40%)
        font_size = visual_meta.get('avg_font_size', 12)
        is_bold = visual_meta.get('is_bold', False)
        alignment = visual_meta.get('alignment', 'left')
        text_length = visual_meta.get('text_length', 0)
        
        # Tamaño de fuente mayor al promedio
        if font_size > baseline_stats['avg_font_size'] * 1.2:
            score += 2.0
        elif font_size > baseline_stats['avg_font_size'] * 1.1:
            score += 1.0
            
        # Texto en negrita
        if is_bold:
            score += 1.5
            
        # Alineación centrada
        if alignment == 'center':
            score += 1.0
        elif alignment == 'indented':
            score += 0.5
            
        # === ANÁLISIS TEXTUAL === (peso: 60%)
        text_lower = text.lower()
        
        # Patrones de numeración
        for pattern in self.numbering_patterns:
            if re.match(pattern, text):
                score += 2.0
                break
        
        # Palabras clave de títulos
        for lang_keywords in self.title_keywords.values():
            if any(keyword in text_lower for keyword in lang_keywords):
                score += 1.5
                break
        
        # Longitud del texto (títulos suelen ser más cortos)
        if text_length < 100:
            score += 1.0
        elif text_length < 50:
            score += 1.5
        elif text_length > 300:
            score -= 1.0
            
        # Uso de mayúsculas
        if text.isupper():
            score += 1.0
        elif text.istitle():
            score += 0.5
            
        # Terminación sin puntuación final (títulos no suelen terminar en punto)
        if not re.search(r'[.!?]$', text.strip()):
            score += 0.5
            
        # Contiene símbolos especiales típicos de títulos
        if '|' in text or '–' in text or '—' in text:
            score += 0.5
            
        # Penalizar texto muy largo para ser título
        if text_length > baseline_stats['avg_text_length'] * 2:
            score -= 1.0
            
        return min(10.0, max(0.0, score))
    
    def determine_hierarchy_level(self, title_blocks: List[Tuple[Dict, float]]) -> List[int]:
        """
        Determina los niveles jerárquicos de los títulos detectados.
        """
        if not title_blocks:
            return []
            
        # Ordenar por score descendente para identificar títulos principales
        sorted_titles = sorted(title_blocks, key=lambda x: x[1], reverse=True)
        
        # Extraer características para clustering por nivel
        font_sizes = []
        scores = []
        
        for block, score in sorted_titles:
            visual_meta = block.get('visual_metadata', {})
            font_sizes.append(visual_meta.get('avg_font_size', 12))
            scores.append(score)
        
        # Asignar niveles basándose en font size y score
        levels = []
        unique_sizes = sorted(set(font_sizes), reverse=True)
        
        for block, score in sorted_titles:
            visual_meta = block.get('visual_metadata', {})
            font_size = visual_meta.get('avg_font_size', 12)
            
            # Determinar nivel basándose en tamaño de fuente
            level = 1
            for i, size_threshold in enumerate(unique_sizes):
                if font_size >= size_threshold:
                    level = i + 1
                    break
            
            # Ajustar nivel basándose en score
            if score >= 8.0:
                level = max(1, level - 1)  # Promover títulos de alto score
            elif score < 5.0:
                level = min(6, level + 1)  # Degradar títulos de bajo score
                
            levels.append(min(6, level))  # Máximo 6 niveles
            
        return levels

class HeadingSegmenter(BaseSegmenter):
    """
    Segmentador para estructuras jerárquicas como libros y documentos con capítulos/secciones.
    
    Este segmentador implementa las reglas descritas en ALGORITMOS_PROPUESTOS.md
    para la detección de encabezados y estructura jerárquica en documentos.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el segmentador con configuración específica.
        
        Args:
            config: Configuración del segmentador con opciones como:
                   - preserve_paragraphs: Preservar párrafos individuales
                   - disable_grouping: No agrupar bajo títulos 
                   - enable_headings: Habilitar detección de títulos
                   - smart_titles: Usar detección inteligente de títulos
        """
        super().__init__(config)
        
        # Configuración por defecto
        default_config = {
            'preserve_paragraphs': True,
            'disable_grouping': True,
            'enable_headings': True,
            'smart_titles': True,
            'split_paragraphs_internally': True,  # Nueva opción
            'min_paragraph_length': 50,          # Mínimo para ser párrafo válido
            'max_segment_length': 500           # Máximo antes de dividir internamente
        }
        
        # Combinar configuración
        if config:
            default_config.update(config)
        self.config = default_config
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Log de configuración
        self.logger.warning(f"🔧 HEADINGSEGMENTER CONFIG: preserve_paragraphs={self.config['preserve_paragraphs']}, disable_grouping={self.config['disable_grouping']}, enable_headings={self.config['enable_headings']}, smart_titles={self.config['smart_titles']}")
        if not self.config['disable_grouping']:
            self.logger.warning("⚠️ disable_grouping=False - riesgo de fusión masiva")
        
        # Configurar thresholds con valores por defecto si no están en config
        self.thresholds = self.config.get('thresholds', {})
        self.max_heading_length = self.thresholds.get('max_heading_length', 150)
        self.max_section_depth = self.thresholds.get('max_section_depth', 3)
        self.min_heading_content = self.thresholds.get('min_heading_content', 2)
        self.max_empty_after_heading = self.thresholds.get('max_empty_after_heading', 3)
        
        # Configuración adicional para filtrado de segmentos
        self.min_segment_length = self.config.get('min_segment_length', 25)  # Longitud mínima para crear un segmento
        self.filter_small_segments = self.config.get('filter_small_segments', True)
        
        # Configuración de detección de encabezados desde el config
        heading_config = self.config.get('heading_detection', {})
        self.enable_heading_detection = heading_config.get('enable_heading_detection', True)
        
        # 🆕 INICIALIZAR DETECTOR DE TÍTULOS INTELIGENTE
        self.title_detector = TitleDetector()
        self.smart_title_detection = heading_config.get('smart_title_detection', False)
        self.title_score_threshold = heading_config.get('title_score_threshold', 4.0)
        
        # Si está desactivada la detección de encabezados, ajustar configuración
        if not self.enable_heading_detection:
            self.max_heading_length = 0  # Desactivar completamente
            
        # Patrones para detectar numeración
        self.number_pattern = re.compile(r'^(\d+)(\.\d+)*\.?\s+')
        
        # Configuración extra para debug
        self.debug_mode = self.config.get('debug', False)
        
        # Contador para estadísticas
        self.stats = {
            "blocks_total": 0,
            "headings_detected": 0,
            "headings_by_pattern": {},
            "headings_by_format": 0,
            "headings_by_heuristic": 0,
            "small_blocks_filtered": 0,
            "smart_titles_detected": 0,
        }
        
        # === PARCHE_ANTI_FUSION_MASIVA V1.0 ===
        # Prevenir fusión masiva de segmentos
        self.max_segment_length = 1000  # Máximo 1000 caracteres por segmento
        self.force_split_large_segments = True
        disable_grouping = self.config.get('disable_grouping', False)
        if disable_grouping:
            self.logger.info('🛡️ ANTI-FUSIÓN: disable_grouping activado')
        else:
            self.logger.warning('⚠️ disable_grouping=False - riesgo de fusión masiva')
    
    def _is_too_small_for_segment(self, text: str) -> bool:
        """
        Determina si un texto es demasiado pequeño para formar un segmento independiente.
        
        Args:
            text: Texto a evaluar
            
        Returns:
            True si es demasiado pequeño, False en caso contrario
        """
        if not self.filter_small_segments:
            return False
            
        # Filtrar por longitud mínima
        if len(text.strip()) < self.min_segment_length:
            return True
            
        # Filtrar artefactos comunes que pueden haber pasado el preprocessor
        text_lower = text.lower().strip()
        
        # Preposiciones y artículos sueltos que no deberían ser segmentos
        if text_lower in ['del', 'de', 'la', 'el', 'los', 'las', 'un', 'una', 'y', 'o', 'a', 'en', 'con', 'por', 'para', 'que', 'se', 'es', 'al', 'este', 'esta']:
            return True
            
        # Solo números o combinaciones de números y puntos
        if re.match(r'^[\d\.\-\s]+$', text.strip()):
            return True
            
        # Letras solas o muy cortas
        if len(text.strip()) <= 3:
            return True
            
        return False
    
    def is_heading(self, block: Dict[str, Any]) -> bool:
        """
        Determina si un bloque es un encabezado SOLO usando señales estructurales.
        
        Args:
            block: Bloque de texto con metadatos
        Returns:
            True si parece un encabezado, False en caso contrario
        """
        self.stats["blocks_total"] += 1
        
        # NUEVA LÓGICA: Si está desactivada la detección de encabezados, nunca es encabezado
        if not self.enable_heading_detection:
            return False
        
        # Si ya viene marcado como heading desde el loader, es encabezado
        if block.get('is_heading', False):
            self.stats["headings_by_format"] += 1
            return True
        
        text = block.get('text', '').strip()
        if not text:
            return False
        
        # Señal estructural: longitud máxima
        if len(text) > self.max_heading_length:
            if self.debug_mode:
                self.logger.debug(f"Rechazado por longitud: {text[:50]}...")
            return False
        
        # Señal estructural: formato visual
        if block.get('is_bold', False) or block.get('is_centered', False):
            self.stats["headings_by_format"] += 1
            self.logger.debug(f"Encabezado detectado por formato visual: {text[:80]}...")
            return True
        
        # Señal estructural: todo en mayúsculas y corto
        if text.isupper() and len(text) < 100:
            self.stats["headings_detected"] += 1
            self.stats["headings_by_heuristic"] += 1
            self.logger.debug(f"Encabezado detectado por mayúsculas: {text}")
            return True
        
        # Señal estructural: líneas cortas sin punto final
        if len(text) < 80 and not text.endswith('.') and not text.endswith(','):
            words = text.split()
            if 2 <= len(words) <= 8 and words[0][0].isupper():
                # Todas las palabras capitalizadas
                all_capitalized = all(w[0].isupper() for w in words if len(w) > 2)
                if all_capitalized:
                    self.stats["headings_detected"] += 1
                    self.stats["headings_by_heuristic"] += 1
                    self.logger.debug(f"Encabezado detectado por capitalización: {text}")
                    return True
                # Formato "Tema - Explicación"
                if " - " in text and text.index(" - ") < 40:
                    self.stats["headings_detected"] += 1
                    self.stats["headings_by_heuristic"] += 1
                    self.logger.debug(f"Encabezado detectado por guion: {text}")
                    return True
                # Termina con dos puntos y es corto
                if text.endswith(':') and len(text) < 40:
                    self.stats["headings_detected"] += 1
                    self.stats["headings_by_heuristic"] += 1
                    self.logger.debug(f"Encabezado detectado por dos puntos: {text}")
                    return True
        return False
    
    def get_heading_level(self, block: Dict[str, Any]) -> int:
        """
        Determina el nivel jerárquico de un encabezado.
        
        Args:
            block: Bloque de texto con metadatos
            
        Returns:
            Nivel jerárquico (1-6, donde 1 es el nivel superior)
        """
        # Si el loader ya determinó el nivel, usarlo
        if 'heading_level' in block and block['heading_level'] > 0:
            return min(block['heading_level'], 6)
            
        text = block.get('text', '').strip()
        
        # Contar '#' para headings de Markdown
        if text.startswith('#'):
            level = 0
            for char in text:
                if char == '#':
                    level += 1
                else:
                    break
            return min(level, 6)
        
        # Contar niveles en numeración decimal
        match = self.number_pattern.match(text)
        if match:
            # Contar número de puntos en la numeración
            numbering = match.group(0)
            level = numbering.count('.') + 1
            return min(level, 6)
        
        # Todo en mayúsculas suele ser de nivel superior
        if text.isupper() or (text == text.upper() and len(text) > 3):
            return 1
        
        # Si empieza con artículos en mayúsculas (LA, EL, LOS, LAS)
        if re.match(r'^(LA|EL|LOS|LAS)\s', text):
            return 1
            
        # Títulos más cortos suelen ser de mayor nivel
        if len(text) < 30:
            return 1
        elif len(text) < 50:
            return 2
        else:
            return 3
        
        # Por defecto, nivel 1 (título principal)
        return 1
    
    def extract_title(self, block: Dict[str, Any]) -> str:
        """
        Extrae el título limpio de un bloque de encabezado.
        
        Args:
            block: Bloque de texto con metadatos
            
        Returns:
            Texto del título sin marcadores ni numeración
        """
        text = block.get('text', '').strip()
        
        # Eliminar marcadores de Markdown
        if text.startswith('#'):
            # Contar '#' y eliminarlos
            count = 0
            for char in text:
                if char == '#':
                    count += 1
                else:
                    break
            text = text[count:].lstrip()
        
        # Eliminar numeración
        match = self.number_pattern.match(text)
        if match:
            text = text[len(match.group(0)):].lstrip()
        
        # Eliminar puntos suspensivos al final (comunes en el documento de ejemplo)
        if text.endswith('...'):
            text = text[:-3].rstrip()
            
        return text
    
    def segment(self, blocks: List[Dict[str, Any]], document_metadata_from_loader: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Segmenta bloques en estructura jerárquica usando una máquina de estados.
        
        Args:
            blocks: Lista de bloques de texto con metadatos
            
        Returns:
            Lista de unidades semánticas (secciones, subsecciones, párrafos)
        """
        self.logger.info(f"HeadingSegmenter.segment received {len(blocks)} blocks to process.") # Log added for debugging
        
        # ===== IDENTIFICADOR ÚNICO DE VERSIÓN =====
        self.logger.warning("🚨🚨🚨 HEADINGSEGMENTER V10.0 - DETECCIÓN INTELIGENTE DE TÍTULOS 🚨🚨🚨")
        self.logger.warning("🔄 VERSIÓN ACTIVA: 31-MAY-2025 03:40 - TITLEDETECTOR INTEGRADO + JERARQUÍA AUTOMÁTICA")
        print("🚨🚨🚨 HEADINGSEGMENTER V10.0 - DETECCIÓN INTELIGENTE DE TÍTULOS 🚨🚨🚨")
        print("🔄 VERSIÓN ACTIVA: 31-MAY-2025 03:40 - TITLEDETECTOR INTEGRADO + JERARQUÍA AUTOMÁTICA")
        
        # 🆕 DETECCIÓN INTELIGENTE DE TÍTULOS
        if self.smart_title_detection and blocks:
            self.logger.info("🧠 ACTIVANDO DETECCIÓN INTELIGENTE DE TÍTULOS")
            
            # Analizar características visuales globales
            baseline_stats = self.title_detector.analyze_visual_characteristics(blocks)
            self.logger.info(f"📊 Estadísticas visuales: font_size_avg={baseline_stats['avg_font_size']:.1f}, text_length_avg={baseline_stats['avg_text_length']:.0f}")
            
            # Detectar títulos candidatos
            title_candidates = []
            for i, block in enumerate(blocks):
                score = self.title_detector.calculate_title_score(block, baseline_stats)
                self.logger.info(f"🔍 Análisis título bloque {i}: score={score:.1f} - '{block.get('text', '')[:50]}...'")
                if score >= self.title_score_threshold:  # Umbral configurable para considerar como título
                    title_candidates.append((i, block, score))
                    self.logger.warning(f"🎯 TÍTULO DETECTADO (score={score:.1f}): {block.get('text', '')[:80]}...")
            
            # Determinar niveles jerárquicos
            if title_candidates:
                title_blocks = [(block, score) for _, block, score in title_candidates]
                hierarchy_levels = self.title_detector.determine_hierarchy_level(title_blocks)
                
                # Marcar bloques como títulos con sus niveles
                for (idx, block, score), level in zip(title_candidates, hierarchy_levels):
                    blocks[idx]['is_smart_title'] = True
                    blocks[idx]['title_score'] = score  
                    blocks[idx]['smart_hierarchy_level'] = level
                    blocks[idx]['is_heading'] = True  # Marcar para el sistema existente
                    blocks[idx]['heading_level'] = level
                    self.stats["smart_titles_detected"] += 1
                    
                self.logger.info(f"✅ Detección inteligente: {len(title_candidates)} títulos encontrados con niveles {hierarchy_levels}")
        
        # NUEVA LÓGICA: Modo de preservación de párrafos individuales
        if self.config.get('disable_grouping', True):
            self.logger.warning("🚨 MODO PÁRRAFOS INDIVIDUALES ACTIVADO - NO AGRUPANDO EN SECCIONES")
            
            # DEBUG: Ver qué bloques estamos procesando
            self.logger.warning(f"📊 DEBUG HeadingSegmenter - Bloques a procesar: {len(blocks)}")
            for i, block in enumerate(blocks[:5]):  # Primeros 5 bloques
                text = block.get('text', '')
                self.logger.warning(f"   Bloque {i}: {len(text)} chars, inicio: {repr(text[:80])}")
            
            segments = []
            for i, block in enumerate(blocks):
                text = block.get('text', '').strip()
                # EN MODO PÁRRAFOS INDIVIDUALES: NO APLICAR FILTROS DE TAMAÑO
                # Solo verificar que no esté vacío
                if text:
                    # 🆕 DETERMINAR TIPO DE SEGMENTO BASÁNDOSE EN DETECCIÓN INTELIGENTE
                    if block.get('is_smart_title', False):
                        segment_type = f"title_level_{block.get('smart_hierarchy_level', 1)}"
                        self.logger.info(f"📄 Segmento {segment_type}: {text[:50]}...")
                        
                        # Los títulos no se dividen internamente
                        segments.append({
                            "type": segment_type,
                            "text": text,
                            "order": len(segments),
                            "hierarchy_level": block.get('smart_hierarchy_level'),
                            "title_score": block.get('title_score'),
                            "block_index": i,
                            "processing_timestamp": datetime.now().isoformat(),
                            "metadata": {
                                'original_block_index': i,
                                'font_size': block.get('font_size'),
                                'bbox': block.get('bbox'),
                                'page_number': block.get('page_number')
                            }
                        })
                    else:
                        segment_type = "paragraph"
                        
                        # 🆕 DIVISIÓN INTERNA POR PÁRRAFOS
                        # Si el segmento es largo y tenemos división interna habilitada
                        if (self.config.get('split_paragraphs_internally', True) and 
                            len(text) > self.config.get('max_segment_length', 500)):
                            
                            # Dividir en párrafos
                            paragraphs = self._split_text_into_paragraphs(
                                text, 
                                self.config.get('min_paragraph_length', 50)
                            )
                            
                            self.logger.warning(f"📝 DIVIDIENDO SEGMENTO LARGO en {len(paragraphs)} párrafos (original: {len(text)} chars)")
                            
                            # Crear un segmento por cada párrafo
                            for j, paragraph in enumerate(paragraphs):
                                segments.append({
                                    "type": f"{segment_type}_split" if len(paragraphs) > 1 else segment_type,
                                    "text": paragraph,
                                    "order": len(segments),
                                    "hierarchy_level": None,
                                    "title_score": None,
                                    "block_index": f"{i}.{j}" if len(paragraphs) > 1 else i,
                                    "processing_timestamp": datetime.now().isoformat(),
                                    "metadata": {
                                        'original_block_index': i,
                                        'paragraph_index': j if len(paragraphs) > 1 else None,
                                        'total_paragraphs': len(paragraphs) if len(paragraphs) > 1 else None,
                                        'font_size': block.get('font_size'),
                                        'bbox': block.get('bbox'),
                                        'page_number': block.get('page_number')
                                    }
                                })
                        else:
                            # Crear segmento único sin división
                            segments.append({
                                "type": segment_type,
                                "text": text,
                                "order": len(segments),
                                "hierarchy_level": None,
                                "title_score": None,
                                "block_index": i,
                                "processing_timestamp": datetime.now().isoformat(),
                                "metadata": {
                                    'original_block_index': i,
                                    'font_size': block.get('font_size'),
                                    'bbox': block.get('bbox'),
                                    'page_number': block.get('page_number')
                                }
                            })
                else:
                    self.logger.debug(f"Filtrado bloque vacío en modo párrafos individuales")
            
            self.logger.warning(f"✅ PÁRRAFOS INDIVIDUALES CON DIVISIÓN INTERNA: {len(segments)} segmentos creados")
            return self._post_process_segments(segments)
        
        # Reiniciar estadísticas para este procesamiento
        self.stats = {
            "blocks_total": 0,
            "headings_detected": 0,
            "headings_by_pattern": {},
            "headings_by_format": 0,
            "headings_by_heuristic": 0,
            "small_blocks_filtered": 0,
            "smart_titles_detected": 0,
        }
        
        # Imprimir información de bloques para debug
        if self.debug_mode:
            self.logger.debug(f"Procesando {len(blocks)} bloques")
            for i, block in enumerate(blocks[:20]):  # Sólo imprimir los primeros 20 para no saturar
                text = block.get('text', '').strip()
                self.logger.debug(f"Bloque {i+1}: {text[:100]}...")
        
        segments = []
        
        # Variables para la sección actual
        current_section = None
        current_content = []
        section_stack = []  # Para mantener jerarquía
        consecutive_empty = 0
        
        # NUEVA: Configuración para documentos largos
        max_consecutive_empty = self.config.get('max_consecutive_empty_lines', 5)
        continue_after_gaps = self.config.get('continue_after_large_gaps', False)
        
        # Estado inicial
        state = HeadingState.INITIAL
        
        # Procesamiento basado en estados
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            is_empty = not text
            
            # Actualizar contador de líneas vacías
            if is_empty:
                consecutive_empty += 1
                # NUEVA LÓGICA: Solo parar si excede el límite Y no está configurado para continuar
                if consecutive_empty > max_consecutive_empty and not continue_after_gaps:
                    self.logger.warning(f"🛑 Deteniendo procesamiento: {consecutive_empty} líneas vacías consecutivas exceden límite {max_consecutive_empty}")
                    break
                # No procesar más lógica para líneas vacías, solo actualizar contador
                continue
            else:
                # NUEVA LÓGICA: Log cuando reanudamos después de muchas líneas vacías
                if consecutive_empty > 5:
                    self.logger.info(f"📄 Reanudando procesamiento después de {consecutive_empty} líneas vacías")
                consecutive_empty = 0  # Resetear contador de líneas vacías
                
                # Filtrar bloques demasiado pequeños antes de procesarlos
                if self._is_too_small_for_segment(text):
                    self.stats["small_blocks_filtered"] += 1
                    if self.debug_mode:
                        self.logger.debug(f"Filtrado bloque muy pequeño: '{text}'")
                    continue
                
                is_heading = self.is_heading(block)
                
                # Depuración
                self.logger.debug(f"Procesando bloque {i}: {'HEADING' if is_heading else 'CONTENT'} - {text[:80]}")
                
                # Transiciones de estado y acciones
                if state == HeadingState.INITIAL:
                    if is_heading:
                        # Encabezado encontrado, iniciar nueva sección
                        level = self.get_heading_level(block)
                        title = self.extract_title(block)
                        
                        current_section = {
                            "type": "section",
                            "title": title,
                            "level": level,
                            "content": [],
                            "subsections": []
                        }
                        state = HeadingState.HEADING_FOUND
                    else:
                        # Texto normal fuera de sección estructurada
                        # Aplicar filtro adicional antes de crear segmento
                        if not self._is_too_small_for_segment(text):
                            segments.append({
                                "type": "paragraph",
                                "text": text
                            })
                        else:
                            self.stats["small_blocks_filtered"] += 1
                
                elif state == HeadingState.HEADING_FOUND:
                    if is_heading:
                        # Otro encabezado justo después de un encabezado (sin contenido)
                        level = self.get_heading_level(block)
                        prev_level = current_section["level"]
                        
                        if level > prev_level:
                            # Es una subsección del encabezado anterior
                            section_stack.append(current_section)
                            
                            # Crear nueva subsección
                            title = self.extract_title(block)
                            current_section = {
                                "type": "section",
                                "title": title,
                                "level": level,
                                "content": [],
                                "subsections": []
                            }
                        else:
                            # Es un encabezado al mismo nivel o superior
                            # El anterior era solo un título sin contenido
                            if section_stack:
                                # Verificar y ajustar la jerarquía
                                while section_stack and level <= section_stack[-1]["level"]:
                                    parent = section_stack.pop()
                                    if not parent["content"] and not parent["subsections"]:
                                        # Sección vacía, añadir como párrafo
                                        segments.append({
                                            "type": "heading",
                                            "text": parent["title"],
                                            "level": parent["level"]
                                        })
                                    else:
                                        # Añadir sección completa
                                        parent["subsections"].append(current_section)
                                        current_section = parent
                                
                                if section_stack:
                                    # Si queda un padre válido, añadir sección actual
                                    parent = section_stack[-1]
                                    parent["subsections"].append(current_section)
                                else:
                                    # No hay padre, añadir a segmentos principales
                                    segments.append(current_section)
                            else:
                                # No hay jerarquía, añadir como encabezado simple
                                segments.append({
                                    "type": "heading",
                                    "text": current_section["title"],
                                    "level": current_section["level"]
                                })
                            
                            # Crear nueva sección con el encabezado actual
                            title = self.extract_title(block)
                            level = self.get_heading_level(block)
                            current_section = {
                                "type": "section",
                                "title": title,
                                "level": level,
                                "content": [],
                                "subsections": []
                            }
                    else:
                        # Contenido después de un encabezado, comenzar a recolectar
                        current_section["content"].append(text)
                        state = HeadingState.COLLECTING_CONTENT
                
                elif state == HeadingState.COLLECTING_CONTENT:
                    if is_heading:
                        # Nuevo encabezado encontrado mientras recolectábamos contenido
                        level = self.get_heading_level(block)
                        prev_level = current_section["level"]
                        
                        # Finalizar sección actual
                        min_content_required = max(1, self.min_heading_content)  # Usar al menos 1
                        if len(current_section["content"]) >= min_content_required or current_section["subsections"]:
                            # La sección tiene suficiente contenido, procesarla normalmente
                            if level > prev_level:
                                # Es una subsección
                                section_stack.append(current_section)
                                title = self.extract_title(block)
                                current_section = {
                                    "type": "section",
                                    "title": title,
                                    "level": level,
                                    "content": [],
                                    "subsections": []
                                }
                            else:
                                # Mismo nivel o superior, cerrar secciones según sea necesario
                                while section_stack and level <= section_stack[-1]["level"]:
                                    parent = section_stack.pop()
                                    parent["subsections"].append(current_section)
                                    current_section = parent
                                
                                # Añadir la sección actual a donde corresponda
                                if section_stack:
                                    parent = section_stack[-1]
                                    parent["subsections"].append(current_section)
                                    
                                    # Crear nueva sección con el encabezado actual
                                    title = self.extract_title(block)
                                    current_section = {
                                        "type": "section",
                                        "title": title,
                                        "level": level,
                                        "content": [],
                                        "subsections": []
                                    }
                                else:
                                    # No hay padre, añadir a segmentos principales
                                    segments.append(current_section)
                                    
                                    # Crear nueva sección con el encabezado actual
                                    title = self.extract_title(block)
                                    current_section = {
                                        "type": "section",
                                        "title": title,
                                        "level": level,
                                        "content": [],
                                        "subsections": []
                                    }
                        else:
                            # Sección con poco contenido, tratar el contenido como párrafos independientes
                            for content in current_section["content"]:
                                segments.append({
                                    "type": "paragraph",
                                    "text": content
                                })
                            
                            # Crear nueva sección con el encabezado actual
                            title = self.extract_title(block)
                            current_section = {
                                "type": "section",
                                "title": title,
                                "level": level,
                                "content": [],
                                "subsections": []
                            }
                        
                        state = HeadingState.HEADING_FOUND
                    else:
                        # Seguir recolectando contenido
                        current_section["content"].append(text)
        
        # Procesar cualquier sección pendiente
        if current_section:
            # Cerrar todas las secciones abiertas
            while section_stack:
                parent = section_stack.pop()
                parent["subsections"].append(current_section)
                current_section = parent
            
            # Añadir la sección final
            segments.append(current_section)
        
        # Mostrar estadísticas de procesamiento
        self.logger.info(f"Estadísticas de procesamiento:")
        self.logger.info(f"  Total bloques procesados: {self.stats['blocks_total']}")
        self.logger.info(f"  Bloques pequeños filtrados: {self.stats['small_blocks_filtered']}")
        self.logger.info(f"  Encabezados detectados: {self.stats['headings_detected']}")
        self.logger.info(f"  Por formato visual: {self.stats['headings_by_format']}")
        self.logger.info(f"  Por heurísticas: {self.stats['headings_by_heuristic']}")
        
        if self.stats['headings_by_pattern']:
            self.logger.info("  Por patrones:")
            for pattern, count in self.stats['headings_by_pattern'].items():
                if count > 0:
                    pattern_short = pattern[:30] + "..." if len(pattern) > 30 else pattern
                    self.logger.info(f"    - {pattern_short}: {count}")
        
        if not segments:
            self.logger.warning("No se encontraron secciones ni párrafos. Verificar la configuración.")
            # Como fallback, si no hay secciones, tratar cada bloque como párrafo
            if len(blocks) > 0:
                self.logger.info("Aplicando fallback: tratando cada bloque como párrafo")
                for block in blocks:
                    text = block.get('text', '').strip()
                    if text:
                        segments.append({
                            "type": "paragraph",
                            "text": text
                        })
        
        # Procesar las secciones y convertirlas al formato final
        processed_segments = self._post_process_segments(segments)
        
        # === DETECCIÓN AUTOMÁTICA DE AUTORES ===
        processed_segments = self._apply_author_detection(processed_segments)
        
        return processed_segments
    
    def _post_process_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesa las secciones después de la segmentación inicial.
        
        Args:
            segments: Lista de segmentos iniciales
            
        Returns:
            Lista de segmentos procesados
        """
        # Aplanar la estructura si se configuró como flat=True
        if self.config.get("flat", False):
            return self._flatten_sections(segments)
        
        # Convertir contenido en texto
        for segment in segments:
            if segment["type"] == "section":
                if "content" in segment and isinstance(segment["content"], list):
                    segment["content"] = "\n\n".join(segment["content"])
                
                # Procesar subsecciones recursivamente
                if "subsections" in segment:
                    segment["subsections"] = self._post_process_segments(segment["subsections"])
        
        return segments
    
    def _flatten_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aplana la estructura jerárquica de secciones a una lista plana.
        
        Args:
            sections: Lista de secciones
            
        Returns:
            Lista plana de secciones
        """
        flat_sections = []
        section_id = 0
        
        # Función recursiva para procesar secciones
        def process_section(section, parent_id=None):
            nonlocal section_id
            current_id = section_id
            section_id += 1
            
            # Crear entrada plana
            flat_section = {
                "id": current_id,
                "parent_id": parent_id,
                "type": section["type"]
            }
            
            # Copiar atributos relevantes
            for key in ["title", "level", "content", "text"]:
                if key in section:
                    flat_section[key] = section[key]
            
            flat_sections.append(flat_section)
            
            # Procesar subsecciones
            if "subsections" in section:
                for subsection in section["subsections"]:
                    process_section(subsection, current_id)
        
        # Procesar todas las secciones de primer nivel
        for section in sections:
            if section["type"] == "section":
                process_section(section)
            else:
                # Para elementos no-sección (párrafos, etc.), añadirlos directamente
                flat_sections.append(section)
        
        return flat_sections
    
    def _apply_author_detection(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔍 DETECCIÓN AUTOMÁTICA DE AUTORES PARA PROSA
        
        Aplica el algoritmo de detección automática de autores a los segmentos
        generados, utilizando la configuración del perfil.
        
        Args:
            segments: Lista de segmentos procesados
            
        Returns:
            Lista de segmentos con información de autor añadida
        """
        if not segments:
            return segments
        
        # Verificar si la detección automática está habilitada
        author_config = self.config.get('author_detection', {})
        if not author_config.get('enabled', False):
            self.logger.debug("🔍 Detección automática de autores deshabilitada")
            return segments
        
        # Verificar si el detector está disponible
        if detect_author_in_segments is None:
            self.logger.warning("⚠️ Detector de autores no disponible (importación falló)")
            return segments
        
        self.logger.info("🔍 INICIANDO DETECCIÓN AUTOMÁTICA DE AUTORES PARA PROSA")
        
        try:
            # Obtener configuración específica para prosa
            detection_config = get_author_detection_config('prosa')
            
            # Aplicar configuración del perfil si está disponible
            if 'confidence_threshold' in author_config:
                detection_config['confidence_threshold'] = author_config['confidence_threshold']
            if 'debug' in author_config:
                detection_config['debug'] = author_config['debug']
            
            # Detectar autor en todos los segmentos
            detected_author = detect_author_in_segments(segments, 'prosa', detection_config)
            
            if detected_author:
                confidence_pct = detected_author['confidence'] * 100
                self.logger.info(f"✅ AUTOR DETECTADO EN SEGMENTACIÓN (PROSA): '{detected_author['name']}' "
                               f"(confianza: {confidence_pct:.1f}%)")
                
                # Añadir información del autor a todos los segmentos
                for segment in segments:
                    if 'metadata' not in segment:
                        segment['metadata'] = {}
                    
                    # Información principal del autor
                    segment['metadata']['detected_author'] = detected_author['name']
                    segment['metadata']['author_confidence'] = detected_author['confidence']
                    segment['metadata']['author_detection_method'] = detected_author['extraction_method']
                    
                    # Detalles adicionales de la detección
                    segment['metadata']['author_detection_details'] = {
                        'sources': detected_author['sources'],
                        'frequency': detected_author['frequency'],
                        'total_candidates': detected_author['detection_details']['total_candidates'],
                        'threshold_used': detected_author['detection_details']['threshold_used']
                    }
                
                self.logger.info(f"📝 Información de autor añadida a {len(segments)} segmentos de prosa")
                
            else:
                self.logger.info("❌ No se pudo detectar autor en segmentación (PROSA)")
                
                # Si está configurado el fallback al override, usar author_override
                if author_config.get('fallback_to_override', True):
                    # El author_override se manejará en el profile_manager o a nivel superior
                    self.logger.info("🔄 Fallback a author_override configurado en el perfil")
                
        except Exception as e:
            self.logger.error(f"❌ Error en detección automática de autores: {str(e)}")
            if author_config.get('debug', False):
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        return segments

    def _split_text_into_paragraphs(self, text: str, min_length: int = 50) -> List[str]:
        """
        Divide un texto en párrafos usando patrones inteligentes.
        Reutiliza la lógica implementada en CommonBlockPreprocessor.
        
        Args:
            text: Texto a dividir
            min_length: Longitud mínima para considerar como párrafo válido
            
        Returns:
            Lista de párrafos
        """
        self.logger.warning(f"🔍 ANALIZANDO TEXTO PARA DIVISIÓN: {len(text)} chars")
        self.logger.warning(f"   📝 Inicio del texto: {repr(text[:200])}...")
        self.logger.warning(f"   📏 Min length requerido: {min_length}")
        
        if len(text) <= min_length:
            self.logger.warning(f"   ❌ Texto muy corto, devolviendo sin dividir")
            return [text]
        
        # Limpiar el texto
        text = text.strip()
        
        # Detectar si hay saltos de línea
        has_newlines = '\n' in text
        self.logger.warning(f"   📊 Tiene saltos de línea: {has_newlines}")
        
        # Patrón más flexible para división de párrafos
        patterns_to_try = [
            # Patrón principal: punto + espacios/saltos + mayúscula (incluye minúsculas)
            r'([.!?]["»"'']?)\s*\n+\s*([A-Za-zÁÉÍÓÚáéíóúñÑüÜ—])',
            # Patrón simple: punto + espacios + mayúscula sin requerir salto
            r'([.!?]["»"'']?)\s{2,}([A-Za-zÁÉÍÓÚáéíóúñÑüÜ—])',
            # Patrón muy simple: doble salto de línea
            r'\n\s*\n',
        ]
        
        paragraphs = []
        
        for i, pattern in enumerate(patterns_to_try):
            self.logger.warning(f"   🔍 Probando patrón {i+1}: {pattern}")
            
            if i < 2:  # Para los dos primeros patrones más complejos
                # Dividir por el patrón capturando grupos
                parts = re.split(pattern, text)
                self.logger.warning(f"   📊 Patrón dividió en {len(parts)} partes")
                
                if len(parts) > 1:  # Si encontró divisiones
                    temp_paragraphs = []
                    j = 0
                    while j < len(parts):
                        if j == 0:
                            # Primer fragmento
                            current = parts[j]
                        elif j % 3 == 1:
                            # Es un separador (punto, etc.)
                            separator = parts[j]
                            next_char = parts[j + 1] if j + 1 < len(parts) else ""
                            next_text = parts[j + 2] if j + 2 < len(parts) else ""
                            
                            # Reconstruir el párrafo anterior con su terminación
                            current += separator
                            if len(current.strip()) >= min_length:
                                temp_paragraphs.append(current.strip())
                            
                            # Iniciar nuevo párrafo
                            current = next_char + next_text
                            j += 2  # Saltar los siguientes dos elementos
                        else:
                            # Agregar texto restante
                            current += parts[j]
                        j += 1
                    
                    # Agregar último párrafo si existe
                    if current and len(current.strip()) >= min_length:
                        temp_paragraphs.append(current.strip())
                    
                    if len(temp_paragraphs) > 1:
                        paragraphs = temp_paragraphs
                        self.logger.warning(f"   ✅ Patrón {i+1} exitoso: {len(paragraphs)} párrafos")
                        break
            else:  # Para el patrón simple de doble salto
                parts = re.split(pattern, text)
                temp_paragraphs = [p.strip() for p in parts if len(p.strip()) >= min_length]
                if len(temp_paragraphs) > 1:
                    paragraphs = temp_paragraphs
                    self.logger.warning(f"   ✅ Patrón {i+1} exitoso: {len(paragraphs)} párrafos")
                    break
        
        # Si ningún patrón funcionó, usar división más agresiva
        if len(paragraphs) <= 1:
            self.logger.warning(f"   🔄 Ningún patrón funcionó, probando división agresiva")
            
            # Intentar división por frases largas (punto + espacio + mayúscula)
            sentence_pattern = r'([.!?])\s+([A-Za-zÁÉÍÓÚáéíóúñÑüÜ])'
            sentences = re.split(sentence_pattern, text)
            
            if len(sentences) > 3:  # Si hay múltiples frases
                # Agrupar frases en párrafos de tamaño razonable
                temp_paragraphs = []
                current_paragraph = ""
                
                for k in range(0, len(sentences), 3):
                    if k == 0:
                        current_paragraph = sentences[k]
                    else:
                        # Reconstruir con puntuación
                        punct = sentences[k-2] if k-2 >= 0 else ""
                        start_char = sentences[k-1] if k-1 >= 0 else ""
                        text_part = sentences[k] if k < len(sentences) else ""
                        
                        # Si el párrafo actual está getting too long, start new one
                        if len(current_paragraph) > 300:  # ~300 chars per paragraph
                            if len(current_paragraph.strip()) >= min_length:
                                temp_paragraphs.append(current_paragraph.strip())
                            current_paragraph = start_char + text_part
                        else:
                            current_paragraph += punct + " " + start_char + text_part
                
                # Add final paragraph
                if current_paragraph and len(current_paragraph.strip()) >= min_length:
                    temp_paragraphs.append(current_paragraph.strip())
                
                if len(temp_paragraphs) > 1:
                    paragraphs = temp_paragraphs
                    self.logger.warning(f"   ✅ División agresiva exitosa: {len(paragraphs)} párrafos")
        
        # Si aún no hay división, devolver el texto original
        if not paragraphs:
            paragraphs = [text]
            self.logger.warning(f"   ❌ No se pudo dividir, devolviendo texto original")
        
        self.logger.warning(f"   🎯 RESULTADO FINAL: {len(paragraphs)} párrafos generados")
        for i, p in enumerate(paragraphs[:3]):  # Mostrar primeros 3
            self.logger.warning(f"      Párrafo {i+1}: {len(p)} chars - {repr(p[:100])}...")
        
        return paragraphs