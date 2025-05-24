import re
from enum import Enum
from typing import List, Dict, Any, Optional
import logging

from .base import BaseSegmenter

class HeadingState(Enum):
    """Estados posibles durante el procesamiento de estructura jerárquica."""
    INITIAL = 1           # Estado inicial, buscando cualquier contenido
    HEADING_FOUND = 2     # Encabezado encontrado, procesando sección
    COLLECTING_CONTENT = 3 # Recolectando contenido de la sección
    SECTION_END = 4       # Finalizando sección actual
    OUTSIDE_SECTION = 5   # Fuera de sección estructurada

class HeadingSegmenter(BaseSegmenter):
    """
    Segmentador para estructuras jerárquicas como libros y documentos con capítulos/secciones.
    
    Este segmentador implementa las reglas descritas en ALGORITMOS_PROPUESTOS.md
    para la detección de encabezados y estructura jerárquica en documentos.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        # Configurar thresholds con valores por defecto si no están en config
        self.thresholds = self.config.get('thresholds', {})
        self.max_heading_length = self.thresholds.get('max_heading_length', 150)
        self.max_section_depth = self.thresholds.get('max_section_depth', 3)
        self.min_heading_content = self.thresholds.get('min_heading_content', 2)
        self.max_empty_after_heading = self.thresholds.get('max_empty_after_heading', 3)
        
        # Patrones para detectar numeración
        self.number_pattern = re.compile(r'^(\d+)(\.\d+)*\.?\s+')
        
        # Logger para depuración
        self.logger = logging.getLogger(__name__)
        
        # Configuración extra para debug
        self.debug_mode = self.config.get('debug', False)
        
        # Contador para estadísticas
        self.stats = {
            "blocks_total": 0,
            "headings_detected": 0,
            "headings_by_pattern": {},
            "headings_by_format": 0,
            "headings_by_heuristic": 0
        }
    
    def is_heading(self, block: Dict[str, Any]) -> bool:
        """
        Determina si un bloque es un encabezado SOLO usando señales estructurales.
        
        Args:
            block: Bloque de texto con metadatos
        Returns:
            True si parece un encabezado, False en caso contrario
        """
        self.stats["blocks_total"] += 1
        
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
    
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segmenta bloques en estructura jerárquica usando una máquina de estados.
        
        Args:
            blocks: Lista de bloques de texto con metadatos
            
        Returns:
            Lista de unidades semánticas (secciones, subsecciones, párrafos)
        """
        self.logger.info(f"HeadingSegmenter.segment received {len(blocks)} blocks to process.") # Log added for debugging
        # Reiniciar estadísticas para este procesamiento
        self.stats = {
            "blocks_total": 0,
            "headings_detected": 0,
            "headings_by_pattern": {},
            "headings_by_format": 0,
            "headings_by_heuristic": 0
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
        
        # Estado inicial
        state = HeadingState.INITIAL
        
        # Procesamiento basado en estados
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            is_empty = not text
            
            # Actualizar contador de líneas vacías
            if is_empty:
                consecutive_empty += 1
                # No procesar más lógica para líneas vacías, solo actualizar contador
                continue
            else:
                consecutive_empty = 0  # Resetear contador de líneas vacías
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
                        segments.append({
                            "type": "paragraph",
                            "text": text
                        })
                
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
        return self._post_process_segments(segments)
    
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