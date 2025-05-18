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
        
        # Patrones para detección de encabezados
        self.heading_patterns = self.config.get('heading_patterns', [
            r'^#{1,6} ',           # Markdown headings
            r'^Capítulo \d+',      # Capítulos numerados
            r'^\d+\.\d*\s+',       # Numeración tipo "1.2 Título"
            r'^[A-Z][A-ZÁ-Ú ]{3,}$',  # TÍTULO EN MAYÚSCULAS
            r'^[A-Z][A-ZÁ-Ú ]{3,}\.+', # TÍTULO EN MAYÚSCULAS seguido de puntos
            r'^[A-Z][A-Z ]{0,2}[A-ZÁ-Ú ]{3,}\.{0,3}', # Más flexible para títulos en mayúsculas con o sin puntos
            r'^[A-ZÁ-Ú][\w ]{0,30}:' # Títulos con formato "Palabra: texto"
        ])
        
        # Añadir patrones adicionales específicos para documentos religiosos/doctrinales
        self.heading_patterns.extend([
            r'^LA\s+[A-ZÁ-Ú\s]{2,}',   # LA PERMANENCIA, LA SANTIDAD, etc.
            r'^EL\s+[A-ZÁ-Ú\s]{2,}',   # EL SEÑOR, EL PROPÓSITO, etc.
            r'^LOS\s+[A-ZÁ-Ú\s]{2,}',  # LOS TESTIGOS, LOS MANDAMIENTOS, etc.
            r'^LAS\s+[A-ZÁ-Ú\s]{2,}',  # LAS PROMESAS, LAS ESCRITURAS, etc.
            r'^[A-ZÁ-Ú]{4,}(\s+[A-ZÁ-Ú]+){0,5}',  # Palabras completas en mayúsculas
            r'^[A-ZÁ-Ú][a-zá-ú]+(\s+[A-ZÁ-Ú][a-zá-ú]+){1,7}$', # Títulos con cada palabra capitalizada
            r'^[A-ZÁ-Ú][a-zá-ú\'\-]+\s*:',  # Formato "Palabra: texto continuación"
        ])
        
        self.heading_regex = re.compile('|'.join(self.heading_patterns))
        
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
            "headings_by_heuristic": 0,
            "total_paragraphs_extracted": 0,
            "total_structural_nodes_identified": 0
        }
    
    def is_heading(self, block: Dict[str, Any]) -> bool:
        """
        Determina si un bloque es un encabezado según heurísticas.
        
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
            
        # Verificar longitud máxima
        if len(text) > self.max_heading_length:
            if self.debug_mode:
                self.logger.debug(f"Rechazado por longitud: {text[:50]}...")
            return False
            
        # Verificar patrones de formato
        if self.heading_regex.search(text):
            for pattern in self.heading_patterns:
                if re.search(pattern, text):
                    self.stats["headings_by_pattern"][pattern] = self.stats["headings_by_pattern"].get(pattern, 0) + 1
                    break
            
            self.stats["headings_detected"] += 1
            self.logger.debug(f"Encabezado detectado por regex: {text[:80]}...")
            return True
            
        # Verificar formatos visuales (negrita, centrado) si hay metadatos
        if block.get('is_bold', False) or block.get('is_centered', False):
            self.stats["headings_by_format"] += 1
            self.logger.debug(f"Encabezado detectado por formato visual: {text[:80]}...")
            return True
        
        # Verificar si el texto termina con puntos suspensivos (común en algunos documentos)
        if text.endswith('...') and len(text) < 100:
            self.stats["headings_detected"] += 1
            self.stats["headings_by_heuristic"] += 1
            self.logger.debug(f"Encabezado detectado por puntos suspensivos: {text}")
            return True
            
        # Heurística adicional: líneas cortas que terminan sin punto
        if len(text) < 80 and not text.endswith('.') and not text.endswith(','):
            words = text.split()
            # Si tiene pocas palabras y la primera empieza con mayúscula
            if 2 <= len(words) <= 8 and words[0][0].isupper():
                # Y no es una frase típica
                if not any(word in text.lower() for word in ['que', 'cuando', 'aunque', 'porque', 'sino']):
                    # Verificar si todas las palabras están capitalizadas
                    all_capitalized = all(w[0].isupper() for w in words if len(w) > 2)
                    if all_capitalized:
                        self.stats["headings_detected"] += 1
                        self.stats["headings_by_heuristic"] += 1
                        self.logger.debug(f"Encabezado detectado por heurística de capitalización: {text}")
                        return True
                        
                    # Verificar si el texto tiene formato de tema "Tema - Explicación"
                    if " - " in text and text.index(" - ") < 40:
                        self.stats["headings_detected"] += 1
                        self.stats["headings_by_heuristic"] += 1
                        self.logger.debug(f"Encabezado detectado por formato tema-explicación: {text}")
                        return True
                    
                    # Si hay poco texto y termina con dos puntos, probablemente es un subtítulo
                    if text.endswith(':') and len(text) < 40:
                        self.stats["headings_detected"] += 1
                        self.stats["headings_by_heuristic"] += 1
                        self.logger.debug(f"Encabezado detectado por formato con dos puntos: {text}")
                        return True
                        
                    # Si es corto pero no cumple con otras heurísticas, verificar palabras clave
                    heading_keywords = ['introducción', 'conclusión', 'resumen', 'prólogo', 'epílogo', 
                                       'prefacio', 'notas', 'apéndice', 'glosario', 'bibliografía']
                    if text.lower() in heading_keywords or any(text.lower().startswith(kw) for kw in heading_keywords):
                        self.stats["headings_detected"] += 1
                        self.stats["headings_by_heuristic"] += 1
                        self.logger.debug(f"Encabezado detectado por palabra clave: {text}")
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Devuelve las estadísticas de la última operación de segmentación."""
        return self.stats
    
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        segments: List[Dict[str, Any]] = []
        
        current_section: Optional[Dict[str, Any]] = None
        current_content_blocks: List[Dict[str, Any]] = []
        section_stack: List[Dict[str, Any]] = [] # Para manejar subsecciones anidadas
        
        # Para la heurística de líneas vacías después de un encabezado
        empty_lines_after_heading_count = 0

        # Reiniciar estadísticas para cada ejecución de segment()
        self.stats = {
            "blocks_total": 0,
            "headings_detected": 0,
            "headings_by_pattern": {},
            "headings_by_format": 0,
            "headings_by_heuristic": 0,
            "total_paragraphs_extracted": 0,
            "total_structural_nodes_identified": 0
        }

        self.logger.debug(f"Iniciando segmentación con {len(blocks)} bloques.")

        for i, block in enumerate(blocks):
            self.stats["blocks_total"] += 1 # Contar cada bloque procesado aquí también.
            block_text = block.get('text', '').strip()
            
            is_block_heading = self.is_heading(block)
            
            if self.debug_mode:
                self.logger.debug(f"Procesando bloque {i}: '{block_text[:100]}...' - Es encabezado: {is_block_heading}")

            if is_block_heading:
                heading_level = self.get_heading_level(block)
                heading_title = self.extract_title(block)
                
                if self.debug_mode:
                    self.logger.debug(f"Encabezado detectado: '{heading_title}' (Nivel: {heading_level})")

                # Heurística: si el título es muy corto y no hay contenido mínimo después, podría no ser un encabezado real.
                # Esto se maneja mejor al final de la sección si el contenido es escaso.

                if current_section:
                    # Finalizar la sección anterior antes de empezar una nueva
                    # si la nueva no es una subsección de la actual o es de nivel superior/igual.
                    if heading_level <= current_section['level'] or not section_stack:
                        # Unir el contenido acumulado para la sección anterior
                        if current_content_blocks:
                            processed_block_texts = []
                            for block_content in current_content_blocks:
                                text = block_content['text'].strip()
                                if text:
                                    # Normalizar todos los tipos de saltos de línea a \\n
                                    text = text.replace('\\r\\n', '\\n').replace('\\r', '\\n')
                                    text = text.replace('\\u2028', '\\n').replace('\\u2029', '\\n')
                                    processed_block_texts.append(text)
                            
                            complete_section_text = "\\n".join(processed_block_texts).strip()
                            if complete_section_text:
                                self.logger.debug(f"--- Analizando sección para párrafos ---")
                                self.logger.debug(f"Texto completo de la sección (primeros 500 chars): {complete_section_text[:500]}")
                                lines = complete_section_text.split('\\n')
                                final_paragraphs = []
                                current_paragraph_lines = []
                                for i, line in enumerate(lines):
                                    line_original_para_log = line # Para logging de la línea original
                                    line_stripped = line.strip()
                                    self.logger.debug(f"  Línea {i+1}/{len(lines)}: '{line_original_para_log}' (stripped: '{line_stripped}')")

                                    if not line_stripped:
                                        self.logger.debug(f"    Línea vacía. Fin de párrafo actual.")
                                        if current_paragraph_lines:
                                            paragraph_to_add = "\\n".join(current_paragraph_lines)
                                            self.logger.debug(f"      AÑADIENDO PÁRRAFO (por línea vacía): '{paragraph_to_add[:200]}...'")
                                            final_paragraphs.append(paragraph_to_add)
                                            current_paragraph_lines = []
                                        continue
                                    
                                    if current_paragraph_lines:
                                        self.logger.debug(f"    Párrafo actual en formación: {current_paragraph_lines}")
                                        should_start_new_paragraph = False
                                        reason_new_paragraph = ""

                                        # Criterio 1: Sangría
                                        is_indented = line.startswith("  ")
                                        if is_indented:
                                            should_start_new_paragraph = True
                                            reason_new_paragraph = "Sangría detectada"
                                            self.logger.debug(f"      Criterio SANGRÍA: SÍ ('{line[:10]}...')")
                                        else:
                                            self.logger.debug(f"      Criterio SANGRÍA: NO")

                                        # Criterio 2: Mayúscula después de fin de oración
                                        if not should_start_new_paragraph and line_stripped and line_stripped[0].isupper():
                                            self.logger.debug(f"      Línea comienza con MAYÚSCULA: SÍ ('{line_stripped[0]}')")
                                            last_accumulated_line = current_paragraph_lines[-1]
                                            ends_with_punctuation = last_accumulated_line.endswith(('.', '!', '?', ':'))
                                            self.logger.debug(f"        Última línea acumulada ('{last_accumulated_line[:50]}...') termina con puntuación: {ends_with_punctuation}")
                                            if ends_with_punctuation:
                                                should_start_new_paragraph = True
                                                reason_new_paragraph = "Mayúscula tras puntuación"
                                            else:
                                                # Heurística adicional: línea anterior corta
                                                is_prev_line_short = len(last_accumulated_line.split()) <= 7 and len(current_paragraph_lines) == 1
                                                self.logger.debug(f"        Última línea acumulada es corta (y única en párr. actual): {is_prev_line_short}")
                                                if is_prev_line_short:
                                                    should_start_new_paragraph = True
                                                    reason_new_paragraph = "Mayúscula tras línea corta"
                                        elif not should_start_new_paragraph:
                                            self.logger.debug(f"      Línea comienza con MAYÚSCULA: NO o ya se decidió nuevo párrafo por sangría")

                                        if should_start_new_paragraph:
                                            paragraph_to_add = "\\n".join(current_paragraph_lines)
                                            self.logger.debug(f"      AÑADIENDO PÁRRAFO (razón: {reason_new_paragraph}): '{paragraph_to_add[:200]}...'")
                                            final_paragraphs.append(paragraph_to_add)
                                            current_paragraph_lines = [line_stripped]
                                            self.logger.debug(f"      Nuevo párrafo iniciado con: ['{line_stripped[:50]}...']")
                                        else:
                                            current_paragraph_lines.append(line_stripped)
                                            self.logger.debug(f"      Línea AÑADIDA a párrafo actual. Párrafo ahora: {current_paragraph_lines}")
                                    else:
                                        current_paragraph_lines.append(line_stripped)
                                        self.logger.debug(f"    INICIANDO NUEVO PÁRRAFO con: ['{line_stripped[:50]}...']")
                                
                                if current_paragraph_lines:
                                    paragraph_to_add = "\\n".join(current_paragraph_lines)
                                    self.logger.debug(f"  --- Fin de análisis de sección ---")
                                    self.logger.debug(f"    AÑADIENDO ÚLTIMO PÁRRAFO: '{paragraph_to_add[:200]}...'")

                                # Filtrar párrafos vacíos que podrían haberse colado
                                final_paragraphs = [p for p in final_paragraphs if p]

                                current_section['content'] = final_paragraphs if final_paragraphs else []
                                self.stats["total_paragraphs_extracted"] += len(final_paragraphs)
                            else:
                                current_section['content'] = []
                            current_content_blocks = []

                        # Volver al nivel superior en la pila si es necesario
                        while section_stack and heading_level <= section_stack[-1]['level']:
                            closed_section = section_stack.pop()
                            if section_stack: # Si hay un padre, la sección cerrada es una subsección
                                if 'subsections' not in section_stack[-1]:
                                    section_stack[-1]['subsections'] = []
                                section_stack[-1]['subsections'].append(closed_section)
                            else: # Si no hay padre, es una sección de nivel superior
                                segments.append(closed_section)
                        
                        current_section = None # Forzar la creación de una nueva sección
                
                # Crear la nueva sección
                new_section = {
                    "type": "section",
                    "title": heading_title,
                    "level": heading_level,
                    "content": [], # Inicializar contenido como lista vacía (de párrafos)
                    "subsections": [] # Inicializar subsecciones
                }
                
                # Manejo de la pila de secciones para la anidación
                if current_section: # Implica que new_section es una subsección
                    if 'subsections' not in current_section:
                        current_section['subsections'] = []
                    # Antes de añadir new_section como subsección de current_section,
                    # current_section debe estar en el stack si no es la raíz.
                    # Esta lógica de apilamiento es compleja y depende de cómo se manejen los niveles.
                    # La lógica simplificada es: si la nueva sección es más profunda, es subsección.
                    if new_section['level'] > current_section['level']:
                         # No se añade directamente a current_section.subsections aquí,
                         # sino que se apila current_section y new_section se vuelve current_section.
                         pass # La lógica de cierre anterior y apilamiento ya maneja esto.


                if section_stack and new_section['level'] > section_stack[-1]['level']:
                    # Nueva sección es subsección de la cima de la pila
                    if 'subsections' not in section_stack[-1]:
                        section_stack[-1]['subsections'] = []
                    # No la agregamos aún, new_section se convierte en la activa y se apilará
                elif section_stack and new_section['level'] <= section_stack[-1]['level']:
                    # Se gestionó arriba con el cierre de secciones
                    pass

                section_stack.append(new_section)
                current_section = new_section
                current_content_blocks = []
                empty_lines_after_heading_count = 0
                self.stats["total_structural_nodes_identified"] += 1
                
            else: # No es un encabezado, es contenido
                if current_section:
                    if block_text: # Solo añadir si no está vacío
                        current_content_blocks.append(block)
                        empty_lines_after_heading_count = 0 # Resetear contador de líneas vacías
                    elif current_content_blocks: # Es una línea vacía después de contenido
                        # Permitir un número limitado de líneas vacías para separar párrafos visualmente
                        # pero no acumular demasiadas si son errores de formato del PDF.
                        # La lógica de split('\n\n') ya maneja múltiples saltos de línea.
                        # Simplemente añadir el bloque vacío si se quiere preservar.
                        # Por ahora, los bloques de texto vacíos (después de strip) se ignoran.
                        # Si se quiere mantener saltos de línea dobles intencionados,
                        # se podría añadir el bloque original si block['text'] == '' (sin strip).
                        # current_content_blocks.append({'text': ''}) # Para mantener un separador
                        pass

                    # Heurística: si hay demasiadas líneas vacías después de un encabezado,
                    # podría significar que el encabezado no tenía contenido y era falso.
                    # Esta heurística es compleja y propensa a errores, mejor confiar en min_heading_content.
                    # if not current_content_blocks: # Aún no hay contenido para la sección actual
                    #     empty_lines_after_heading_count += 1
                    #     if empty_lines_after_heading_count > self.max_empty_after_heading:
                    #         # Considerar el encabezado anterior como texto normal si no tuvo contenido
                    #         # Esto requiere revertir la creación de current_section
                    #         self.logger.debug(f"Revirtiendo encabezado '{current_section['title']}' por falta de contenido.")
                    #         # Convertir current_section de nuevo a un bloque de contenido y añadirlo a la sección anterior o a segments
                    #         # Esta lógica es compleja, por ahora la omitimos.
                    #         pass

                else: # Contenido fuera de cualquier sección (ej. al inicio del documento)
                    if block_text: # Solo si hay texto real
                        # Tratar como un segmento de tipo "paragraph" o "text"
                        # Esto puede ocurrir si el documento no empieza con un encabezado.
                        orphan_paragraph_node = {
                            "type": "paragraph", # O "text_block"
                            "content": [block_text], # Mantener formato de lista de párrafos
                            "level": 0 # Nivel especial para contenido no estructurado
                        }
                        segments.append(orphan_paragraph_node)
                        self.stats["total_paragraphs_extracted"] += 1
                        self.stats["total_structural_nodes_identified"] += 1
                        if self.debug_mode:
                            self.logger.debug(f"Contenido huérfano añadido: {block_text[:100]}...")


        # Finalizar la última sección abierta (si existe)
        if current_section:
            if current_content_blocks:
                processed_block_texts = []
                for block_content in current_content_blocks:
                    text = block_content['text'].strip()
                    if text:
                        # Normalizar todos los tipos de saltos de línea a \\n
                        text = text.replace('\\r\\n', '\\n').replace('\\r', '\\n')
                        text = text.replace('\\u2028', '\\n').replace('\\u2029', '\\n')
                        processed_block_texts.append(text)
                
                complete_section_text = "\\n".join(processed_block_texts).strip()
                if complete_section_text:
                    self.logger.debug(f"--- Analizando sección final para párrafos ---")
                    self.logger.debug(f"Texto completo de la sección (primeros 500 chars): {complete_section_text[:500]}")
                    lines = complete_section_text.split('\\n')
                    final_paragraphs = []
                    current_paragraph_lines = []
                    for i, line in enumerate(lines):
                        line_original_para_log = line # Para logging de la línea original
                        line_stripped = line.strip()
                        self.logger.debug(f"  Línea {i+1}/{len(lines)}: '{line_original_para_log}' (stripped: '{line_stripped}')")

                        if not line_stripped:
                            self.logger.debug(f"    Línea vacía. Fin de párrafo actual.")
                            if current_paragraph_lines:
                                paragraph_to_add = "\\n".join(current_paragraph_lines)
                                self.logger.debug(f"      AÑADIENDO PÁRRAFO (por línea vacía): '{paragraph_to_add[:200]}...'")
                                final_paragraphs.append(paragraph_to_add)
                                current_paragraph_lines = []
                            continue
                        
                        if current_paragraph_lines:
                            self.logger.debug(f"    Párrafo actual en formación: {current_paragraph_lines}")
                            should_start_new_paragraph = False
                            reason_new_paragraph = ""

                            # Criterio 1: Sangría
                            is_indented = line.startswith("  ")
                            if is_indented:
                                should_start_new_paragraph = True
                                reason_new_paragraph = "Sangría detectada"
                                self.logger.debug(f"      Criterio SANGRÍA: SÍ ('{line[:10]}...')")
                            else:
                                self.logger.debug(f"      Criterio SANGRÍA: NO")
                            
                            # Criterio 2: Mayúscula después de fin de oración
                            if not should_start_new_paragraph and line_stripped and line_stripped[0].isupper():
                                self.logger.debug(f"      Línea comienza con MAYÚSCULA: SÍ ('{line_stripped[0]}')")
                                last_accumulated_line = current_paragraph_lines[-1]
                                ends_with_punctuation = last_accumulated_line.endswith(('.', '!', '?', ':'))
                                self.logger.debug(f"        Última línea acumulada ('{last_accumulated_line[:50]}...') termina con puntuación: {ends_with_punctuation}")
                                if ends_with_punctuation:
                                    should_start_new_paragraph = True
                                    reason_new_paragraph = "Mayúscula tras puntuación"
                                else:
                                    # Heurística adicional: línea anterior corta
                                    is_prev_line_short = len(last_accumulated_line.split()) <= 7 and len(current_paragraph_lines) == 1
                                    self.logger.debug(f"        Última línea acumulada es corta (y única en párr. actual): {is_prev_line_short}")
                                    if is_prev_line_short:
                                        should_start_new_paragraph = True
                                        reason_new_paragraph = "Mayúscula tras línea corta"
                            elif not should_start_new_paragraph:
                                self.logger.debug(f"      Línea comienza con MAYÚSCULA: NO o ya se decidió nuevo párrafo por sangría")

                            if should_start_new_paragraph:
                                paragraph_to_add = "\\n".join(current_paragraph_lines)
                                self.logger.debug(f"      AÑADIENDO PÁRRAFO (razón: {reason_new_paragraph}): '{paragraph_to_add[:200]}...'")
                                final_paragraphs.append(paragraph_to_add)
                                current_paragraph_lines = [line_stripped]
                                self.logger.debug(f"      Nuevo párrafo iniciado con: ['{line_stripped[:50]}...']")
                            else:
                                current_paragraph_lines.append(line_stripped)
                                self.logger.debug(f"      Línea AÑADIDA a párrafo actual. Párrafo ahora: {current_paragraph_lines}")
                        else:
                            current_paragraph_lines.append(line_stripped)
                            self.logger.debug(f"    INICIANDO NUEVO PÁRRAFO con: ['{line_stripped[:50]}...']")
                    
                    if current_paragraph_lines:
                        paragraph_to_add = "\\n".join(current_paragraph_lines)
                        self.logger.debug(f"  --- Fin de análisis de sección (final) ---")
                        self.logger.debug(f"    AÑADIENDO ÚLTIMO PÁRRAFO: '{paragraph_to_add[:200]}...'")

                    # Filtrar párrafos vacíos que podrían haberse colado
                    final_paragraphs = [p for p in final_paragraphs if p]
                    
                    current_section['content'] = final_paragraphs if final_paragraphs else []
                    self.stats["total_paragraphs_extracted"] += len(final_paragraphs)
                else:
                    current_section['content'] = []
            
            # Vaciar la pila restante
            while section_stack:
                closed_section = section_stack.pop()
                # Validar contenido mínimo para la sección
                # if len(closed_section.get('content', '')) < self.min_heading_content and not closed_section.get('subsections'):
                #     self.logger.debug(f"Sección '{closed_section['title']}' descartada por contenido insuficiente.")
                #     # Aquí se podría convertir el título en un párrafo de la sección padre o segmento
                #     # if section_stack: # si tiene padre
                #     #     # ... lógica para añadir el título como texto al padre ...
                #     # else: # si es de nivel superior
                #     #     segments.append({"type": "paragraph", "content": closed_section['title'], "level": 0})
                #     continue # Saltar la adición de esta sección

                if section_stack: # La sección cerrada es una subsección de la cima de la pila
                    if 'subsections' not in section_stack[-1]:
                        section_stack[-1]['subsections'] = []
                    section_stack[-1]['subsections'].insert(0, closed_section) # Insertar al principio para mantener orden
                else: # Es una sección de nivel superior
                    segments.append(closed_section)

        # Post-procesamiento (opcional, para limpiar o reestructurar)
        segments = self._post_process_segments(segments)
        
        self.logger.info(f"Segmentación completada. Total segmentos: {len(segments)}")
        self.logger.info(f"Estadísticas de procesamiento: {self.get_stats()}")
        
        # Devolver una copia aplanada si es necesario para el formato ndjson final,
        # o la estructura jerárquica si el consumidor la maneja.
        # Por ahora, devolvemos la estructura jerárquica (segments puede contener secciones anidadas).
        # El consumidor (ej. ProfileManager) se encargará de aplanar si es necesario.
        return segments

    def _post_process_segments(self, segments_input: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesa las secciones después de la segmentación inicial.
        Si self.config.get("flat", False) es True, aplana la estructura.
        De lo contrario, procesa recursivamente las subsecciones (content ya es lista de párrafos).
        """
        if self.config.get("flat", False):
            # Aplanar usando el formato id/parent_id. content se mantiene como lista de párrafos.
            return self._flatten_sections(segments_input)
        else:
            # Procesar para formato anidado.
            # 'content' ya es una lista de párrafos desde segment(), no necesita ser modificado aquí.
            # Solo necesitamos procesar recursivamente las subsecciones.
            processed_segments = []
            for segment in segments_input:
                segment_copy = dict(segment) # Trabajar con una copia
                if segment_copy.get("type") == "section": # Verificar type
                    if "subsections" in segment_copy and segment_copy["subsections"]:
                        # Llamada recursiva para procesar las subsecciones
                        segment_copy["subsections"] = self._post_process_segments(segment_copy["subsections"])
                processed_segments.append(segment_copy)
            return processed_segments
    
    def _flatten_sections(self, sections_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aplana la estructura jerárquica de secciones a una lista plana con id/parent_id.
        El campo 'content' de cada sección se mantiene como una lista de párrafos.
        No actualiza self.stats directamente, eso se hace en segment() o antes.
        """
        flat_sections_output: List[Dict[str, Any]] = []
        current_id_counter = 0

        def process_section_recursive(section_node: Dict[str, Any], parent_id_val: Optional[int] = None) -> None:
            nonlocal current_id_counter
            
            node_id = current_id_counter
            current_id_counter += 1

            flat_representation = {
                "id": node_id,
                "parent_id": parent_id_val,
                "type": section_node.get("type", "section"),
                "title": section_node.get("title", ""),
                "level": section_node.get("level", 0),
                "content": section_node.get("content", []) # content es lista de párrafos
            }
            # Eliminar 'subsections' de la representación plana principal, 
            # ya que la jerarquía se maneja con parent_id.
            # flat_representation.pop("subsections", None) # No necesario si solo copiamos claves específicas

            flat_sections_output.append(flat_representation)

            if "subsections" in section_node and section_node["subsections"]:
                for sub_section_node in section_node["subsections"]:
                    process_section_recursive(sub_section_node, node_id)

        for top_level_section in sections_list:
            if top_level_section.get("type") == "section":
                process_section_recursive(top_level_section)
            else:
                # Manejar elementos no-sección (p.ej., párrafos huérfanos)
                orphan_id = current_id_counter
                current_id_counter += 1
                
                # Crear una copia para no modificar el objeto original si viene de fuera
                top_level_item_copy = dict(top_level_section)
                top_level_item_copy["id"] = orphan_id
                top_level_item_copy["parent_id"] = None 
                # Asegurar que las claves esperadas estén presentes
                if "type" not in top_level_item_copy:
                    top_level_item_copy["type"] = "paragraph" # O un tipo por defecto
                if "content" not in top_level_item_copy:
                     # Si es un bloque de texto simple, content podría ser el texto mismo en una lista
                    top_level_item_copy["content"] = [top_level_item_copy.get("text", "")] if "text" in top_level_item_copy else []
                # No contamos párrafos aquí, ya que se cuentan cuando se añaden al 'content' de una sección
                # o como 'orphan_paragraph_node'. Aquí solo estamos aplanando.
                # Los nodos estructurales se cuentan cuando se identifican como sección o párrafo huérfano en segment().


                flat_sections_output.append(top_level_item_copy)
                
        return flat_sections_output 