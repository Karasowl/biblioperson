import re
import logging
from typing import Dict, Any, List, Optional
from .base import BaseSegmenter

# Importar el detector de autores
try:
    from ..author_detection import detect_author_in_segments, get_author_detection_config
except ImportError:
    # Fallback si no está disponible
    detect_author_in_segments = None
    get_author_detection_config = None

logger = logging.getLogger(__name__)

class VerseSegmenter(BaseSegmenter):
    """
    Segmentador para contenido poético.
    Identifica títulos de poemas y los versos que les siguen.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # PREPROCESSOR VERSION LOCK LOG
        self.logger.warning("🔒 VERSE SEGMENTER V2.3 - LIMPIEZA DIRECTA DE ELEMENTOS ESTRUCTURALES")
        self.logger.warning("🧹 NUEVA FUNCIONALIDAD: Filtrado de '*Antolo* *g* *ía* *Rubén Darío*' en texto final")
        
        # Configuraciones por defecto
        default_config = {
            'min_verse_lines': 3,
            'max_title_length': 100,
            'max_verse_line_length': 120
        }
        
        if config:
            default_config.update(config)
        self.config = default_config

    def _pre_split_large_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔧 NUEVA FUNCIONALIDAD - PRE-DIVISIÓN DE BLOQUES GRANDES
        
        Antes de la segmentación principal, divide bloques grandes que contienen
        múltiples poemas en bloques más pequeños basándose en patrones de títulos.
        
        Args:
            blocks: Lista de bloques originales
            
        Returns:
            List[Dict]: Lista expandida de bloques más granulares
        """
        self.logger.info("🔧 Pre-dividiendo bloques grandes...")
        
        new_blocks = []
        blocks_split = 0
        
        for block in blocks:
            text = block.get('text', '').strip()
            if not text:
                new_blocks.append(block)
                continue
            
            # Solo dividir bloques grandes (más de 1000 caracteres)
            if len(text) < 1000:
                new_blocks.append(block)
                continue
                
            # Buscar patrones de división dentro del bloque
            split_points = self._find_split_points(text)
            
            if len(split_points) <= 1:  # No hay puntos de división
                new_blocks.append(block)
                continue
            
            # Dividir el bloque en sub-bloques
            blocks_split += 1
            self.logger.debug(f"📄 Dividiendo bloque grande en {len(split_points)} partes")
            
            start = 0
            for i, split_point in enumerate(split_points):
                if i == len(split_points) - 1:  # Último fragmento
                    fragment = text[start:].strip()
                else:
                    fragment = text[start:split_point].strip()
                
                if fragment:
                    # Crear nuevo bloque con metadata similar
                    new_block = {
                        'text': fragment,
                        'metadata': dict(block.get('metadata', {}))
                    }
                    new_block['metadata']['split_from_large'] = True
                    new_block['metadata']['original_order'] = block.get('metadata', {}).get('order', 0)
                    new_block['metadata']['split_index'] = i
                    new_blocks.append(new_block)
                
                start = split_point
        
        self.logger.info(f"🔧 Pre-división completada: {blocks_split} bloques divididos, {len(new_blocks)} bloques totales")
        return new_blocks

    def _find_split_points(self, text: str) -> List[int]:
        """
        Encuentra puntos donde dividir un bloque grande basándose en patrones de títulos.
        
        Args:
            text: Texto del bloque grande
            
        Returns:
            List[int]: Posiciones donde dividir el texto
        """
        lines = text.split('\n')
        split_points = [0]  # Siempre empezar desde el inicio
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Buscar patrones que indican inicio de nuevo poema
            is_title_pattern = False
            
            # PATRÓN 1: "Poema" seguido de número
            if re.match(r'^(POEMA|Poema)\s+\d+', line, re.IGNORECASE):
                is_title_pattern = True
                self.logger.debug(f"🎯 Patrón 'Poema N' detectado: '{line}'")
            
            # PATRÓN 2: Números romanos o arábigos solos (I, II, III, 1, 2, 3)
            elif re.match(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|\d+)\.?$', line):
                is_title_pattern = True
                self.logger.debug(f"🎯 Patrón numérico detectado: '{line}'")
            
            # PATRÓN 3: Líneas en mayúsculas cortas (posibles títulos)
            elif line.isupper() and 3 <= len(line) <= 60 and not line.endswith('.'):
                is_title_pattern = True
                self.logger.debug(f"🎯 Patrón mayúsculas detectado: '{line}'")
            
            # PATRÓN 4: Títulos entre comillas
            elif line.startswith('"') and line.endswith('"') and len(line) < 80:
                is_title_pattern = True
                self.logger.debug(f"🎯 Patrón comillas detectado: '{line}'")
            
            # PATRÓN 5: Títulos descriptivos comunes
            elif re.match(r'^(Canción|Soneto|Elegía|Oda|Balada)\s+', line, re.IGNORECASE):
                is_title_pattern = True
                self.logger.debug(f"🎯 Patrón tipo poético detectado: '{line}'")
            
            # PATRÓN 6: Patrones específicos de títulos poéticos
            elif self._looks_like_poem_title(line):
                is_title_pattern = True
                self.logger.debug(f"🎯 Patrón título poético detectado: '{line}'")
            
            if is_title_pattern and i > 0:  # No dividir en la primera línea
                # Calcular posición en el texto original
                text_position = sum(len(lines[j]) + 1 for j in range(i))  # +1 por \n
                split_points.append(text_position)
        
        return split_points

    def _is_main_title(self, block: Dict[str, Any], block_index: int = 0, all_blocks: List = None) -> bool:
        """
        🔧 MEJORADO - Detecta si un bloque es un título PRINCIPAL de poema.
        """
        text = block.get('text', '').strip()
        if not text:
            return False

        # CONDICIÓN 1: Debe ser un título válido pero NO subtítulo interno
        if not self._is_title_block(block):
            return False
        
        # CONDICIÓN EXTRA: Para títulos en mayúsculas, dar prioridad absoluta
        if (text.isupper() and 
            3 <= len(text) <= 80 and 
            len(text.split()) <= 8):
            self.logger.debug(f"🏆 Título PRINCIPAL en mayúsculas (prioridad máxima): '{text}'")
            return True
        
        # Detectar subtítulos internos que NO deben iniciar poemas nuevos
        internal_patterns = [
            r'^[A-Z][a-z]+:$',          # "Asere:", "Hombre:", "Mujer:", etc.
            r'^[A-Z][a-z]+\.\.\..*$',   # "Asere...algo"
            r'\.\.\..*$',               # Líneas que contienen "..."
            r'^[IVX]+\.$',              # Numeración romana "I.", "II.", etc.
            r'^\d+\.$',                 # Numeración "1.", "2.", etc.
            r'^Página\s+\d+',           # "Página N de M" 
        ]
        
        is_internal = any(re.match(pattern, text) for pattern in internal_patterns)
        
        if is_internal:
            self.logger.debug(f"❌ Subtítulo INTERNO detectado: '{text}' - no inicia poema nuevo")
            return False

        # CONDICIÓN 2: Le siguen 0-3 líneas vacías (más flexible)
        empty_lines_after = 0
        next_content_index = None
        
        for j in range(block_index + 1, min(block_index + 5, len(all_blocks or []))):
            if j >= len(all_blocks):
                break
            next_block = all_blocks[j]
            next_text = next_block.get('text', '').strip()
            
            if not next_text:
                empty_lines_after += 1
            else:
                next_content_index = j
                break
        
        # Ser más flexible: permitir 0 líneas vacías también
        if empty_lines_after > 3:
            return False
        
        # Si no hay contenido después, no puede ser un título válido
        if next_content_index is None:
            return False
        
        # CONDICIÓN 3: Después aparece un bloque de ≥ 1 línea corta (MENOS RESTRICTIVO)
        verse_lines_count = 0
        consecutive_empty = 0
        
        for j in range(next_content_index, min(next_content_index + 10, len(all_blocks))):
            if j >= len(all_blocks):
                break
            verse_block = all_blocks[j]
            verse_text = verse_block.get('text', '').strip()
            
            if not verse_text:
                consecutive_empty += 1
                if consecutive_empty > 2:  # Más de 2 líneas vacías rompe el bloque poético
                    break
                continue
            else:
                consecutive_empty = 0
                        
            # Verificar si es un subtítulo interno que NO debe interrumpir el conteo
            is_internal_subtitle = any(re.match(pattern, verse_text) for pattern in [
                r'^[A-Z][a-z]+:$',  # Patrones como "Asere:", "Hombre:", "Mujer:" etc
                r'^[A-Z][a-z]+\.\.\..*$',  # Patrones como "Asere...algo"
                r'\.\.\..*$',  # Líneas que empiezan o contienen "..." 
            ])
            
            # La línea debe ser corta y sin estilo (verso plano) O ser subtítulo interno
            if (len(verse_text) <= 120 and 
                (not verse_block.get('is_heading', False) or is_internal_subtitle) and
                not verse_block.get('is_bold', False)):
                verse_lines_count += 1
            else:
                # Solo interrumpir si es una línea larga o con estilo que NO es subtítulo interno
                if not is_internal_subtitle:
                    break  # Línea larga o con estilo interrumpe el bloque poético
        
        # MENOS RESTRICTIVO: Solo necesitamos 1 línea de verso para confirmar que es un poema
        is_valid_poem = verse_lines_count >= 1
        
        if is_valid_poem:
            self.logger.debug(f"✅ Título válido (algoritmo mejorado): '{text}' - {verse_lines_count} versos detectados")
        else:
            self.logger.debug(f"❌ Título rechazado: '{text}' - solo {verse_lines_count} versos detectados")
        
        return is_valid_poem
    
    def _is_title_block(self, block: Dict[str, Any]) -> bool:
        """
        🔧 MEJORADO - Detecta si un bloque es cualquier tipo de título.
        RESTRICTIVO: Solo detecta títulos reales, no versos normales.
        """
        text = block.get('text', '').strip()
        if not text:
            return False
            
        # Información estructural del DocxLoader
        if block.get('is_heading', False):
            self.logger.debug(f"🎭 Título detectado por estructura: '{text}'")
            return True
        
        # PATRÓN 1: Títulos entre comillas
        if (text.startswith('"') and text.endswith('"')) and len(text) < 80:
            self.logger.debug(f"🎭 Título detectado por comillas: '{text}'")
            return True
        
        # PATRÓN 2: "Poema" + número (MUY ESPECÍFICO)
        if re.match(r'^(POEMA|Poema)\s+\d+\s*$', text, re.IGNORECASE):
            self.logger.debug(f"🎭 Título 'Poema N' detectado: '{text}'")
            return True
        
        # PATRÓN 3: Números romanos o arábigos solos (EXACTOS)
        if re.match(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|\d+)\.?\s*$', text):
            self.logger.debug(f"🎭 Título numérico detectado: '{text}'")
            return True
        
        # PATRÓN 4 (PRIORITARIO): Texto en mayúsculas - TIENE PRIORIDAD SOBRE PATRONES DE VERSO
        if (text.isupper() and 
            3 <= len(text) <= 80 and 
            not text.endswith('.') and 
            not text.endswith(',') and
            not text.endswith(';') and
            not text.endswith('!') and
            not text.endswith('?') and
            # Permitir títulos con preposiciones si están en mayúsculas
            len(text.split()) <= 8):  # Máximo 8 palabras para ser considerado título
            self.logger.debug(f"🎭 Título en MAYÚSCULAS detectado (prioritario): '{text}'")
            return True
        
        # PATRÓN 5: Títulos con formato especial
        if (block.get('is_bold', False) and len(text) < 80) or \
           (block.get('is_centered', False) and len(text) < 80):
            self.logger.debug(f"🎭 Título detectado por formato: '{text}'")
            return True
        
        # PATRÓN 6: Títulos específicos de poesía (EXACTOS)
        if re.match(r'^(Canción|Soneto|Elegía|Oda|Balada)\s+', text, re.IGNORECASE):
            self.logger.debug(f"🎭 Título tipo poético detectado: '{text}'")
            return True
        
        # PATRÓN 7: ULTRA AGRESIVO - Rechazar cualquier cosa que se parezca a verso
        obvious_verse_patterns = [
            # Puntuación típica de versos
            r'[,;]\s+\w+',        # Coma seguida de palabra 
            r'\.\s*$',            # Termina en punto
            r'!\s*$',             # Termina en exclamación
            r'\?\s*$',            # Termina en interrogación
            r';\s*$',             # Termina en punto y coma
            
            # Artículos + sustantivos (típico de versos descriptivos)
            r'^(La\s+\w+|El\s+\w+|Los\s+\w+|Las\s+\w+)',  # "La espada", "El viento", etc.
            r'^(Una\s+\w+|Un\s+\w+|Unos\s+\w+|Unas\s+\w+)',  # "Una rosa", "Un día", etc.
            
            # Verbos conjugados al inicio (típico de acción poética) 
            r'^\w+\s+(se\s+)?\w+',  # "viene", "se anuncia", "corren", etc.
            
            # Preposiciones al inicio
            r'^(Con\s+|Sin\s+|Por\s+|Para\s+|Desde\s+|Hasta\s+|Sobre\s+|Bajo\s+)',
            
            # Construcciones reflexivas y pronominales
            r'\b(se\s+\w+|me\s+\w+|te\s+\w+|le\s+\w+|nos\s+\w+)',  # "se anuncia", "me duele"
            
            # Adjetivos descriptivos con artículo
            r'^(La\s+\w+\s+\w+|El\s+\w+\s+\w+)',  # "La dulce brisa", "El fuerte viento"
            
            # Construcciones verbales específicas
            r'\b(anuncia|viene|pasa|llega|corre|vuela|suena|brilla)\b',  # Verbos típicos de verso
            
            # Patrones de rima o metro
            r'\b\w+or\b|\b\w+ar\b|\b\w+er\b',  # Palabras que terminan en sonidos comunes de rima
            
            # Si contiene más de 2 verbos conjugados (típico de narración poética)
            # Se revisará por separado
        ]
        
        # Solo rechazar si contiene patrones OBVIAMENTE de versos
        for pattern in obvious_verse_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.logger.debug(f"❌ Rechazado como título (patrón obvio de verso): '{text}'")
                return False
        
        # PATRÓN 8: Patrones avanzados de títulos poéticos (ULTRA RESTRICTIVOS - solo títulos obvios)
        if self._looks_like_poem_title(text):
            self.logger.debug(f"🎭 Título poético avanzado detectado: '{text}'")
            return True
        
        # RECHAZAR todo lo demás que no cumple criterios específicos de títulos
        self.logger.debug(f"❌ Texto rechazado como título (no cumple criterios específicos): '{text}'")        
        return False
    
    def _is_verse_line(self, block: Dict[str, Any]) -> bool:
        """
        Detecta si un bloque es una línea de verso.
        """
        text = block.get('text', '').strip()
        if not text:
            return False
        
        # Los versos típicamente son líneas cortas o medianas
        if len(text) <= 120:
            return True
        
        return False
    
    def _is_empty_block(self, block: Dict[str, Any]) -> bool:
        """
        Detecta si un bloque está vacío.
        """
        text = block.get('text', '').strip()
        return not text
    
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔧 MEJORADO - Segmenta bloques en poemas individuales con pre-procesamiento.
        """
        if not blocks:
            return []
        
        self.logger.info(f"VerseSegmenter V2.1: Procesando {len(blocks)} bloques")
        
        # PASO 1: Pre-dividir bloques grandes
        processed_blocks = self._pre_split_large_blocks(blocks)
        self.logger.info(f"📄 Después de pre-división: {len(processed_blocks)} bloques")
        
        segments = []
        current_poem_blocks = []
        current_title = None
        
        i = 0
        while i < len(processed_blocks):
            block = processed_blocks[i]
            text = block.get('text', '').strip()
            
            # Detectar título PRINCIPAL de poema
            if self._is_main_title(block, i, processed_blocks):
                # Si ya tenemos un poema acumulado, crearlo
                if current_poem_blocks and current_title:
                    poem_text = self._create_poem_text(current_title, current_poem_blocks)
                    if poem_text.strip():
                        segments.append({
                            'type': 'poem',
                            'text': poem_text.strip(),
                            'title': current_title,
                            'verse_count': len([b for b in current_poem_blocks if self._is_verse_line(b)]),
                            'source_blocks': len(current_poem_blocks)
                        })
                        self.logger.info(f"✅ Poema creado: '{current_title}' ({len(current_poem_blocks)} bloques)")
                
                # Iniciar nuevo poema
                current_title = text
                current_poem_blocks = []
                self.logger.debug(f"🎭 Nuevo título PRINCIPAL: '{current_title}'")
            
            # Agregar bloque al poema actual (títulos internos y versos)
            elif current_title is not None:
                current_poem_blocks.append(block)
                
                # Log subtítulos internos
                if self._is_title_block(block):
                    self.logger.debug(f"🔹 Subtítulo interno agregado: '{text}'")
            
            i += 1
        
        # Procesar último poema si existe
        if current_poem_blocks and current_title:
            poem_text = self._create_poem_text(current_title, current_poem_blocks)
            if poem_text.strip():
                segments.append({
                    'type': 'poem',
                    'text': poem_text.strip(),
                    'title': current_title,
                    'verse_count': len([b for b in current_poem_blocks if self._is_verse_line(b)]),
                    'source_blocks': len(current_poem_blocks)
                })
                self.logger.info(f"✅ Último poema creado: '{current_title}' ({len(current_poem_blocks)} bloques)")
        
        self.logger.info(f"🎭 VerseSegmenter V2.1: {len(segments)} poemas detectados")
        
        # ALGORITMO DE FALLBACK según reglas del usuario
        # MODIFICADO: Solo activar cuando se detectan 0 segmentos, no ≤3
        # Si ya tenemos 1+ segmentos, significa que el algoritmo principal funcionó
        if len(segments) == 0:
            self.logger.warning(f"⚠️ No se detectaron segmentos, activando algoritmo de fallback")
            fallback_segments = self._fallback_segmentation(processed_blocks)
            if len(fallback_segments) > 0:
                self.logger.info(f"✅ Fallback creó {len(fallback_segments)} segmentos donde no había ninguno")
                segments = fallback_segments
            else:
                return segments
        elif len(segments) <= 3:
            self.logger.info(f"ℹ️ Detectados {len(segments)} segmentos (suficiente), omitiendo fallback")
            # No aplicar fallback si ya tenemos segmentos válidos
        
        # === DETECCIÓN AUTOMÁTICA DE AUTORES ===
        segments = self._apply_author_detection(segments)
        
        return segments
    
    def _create_poem_text(self, title: str, blocks: List[Dict[str, Any]]) -> str:
        """
        Crea el texto completo del poema combinando título y versos.
        MEJORADO: Preserva saltos de línea internos de los bloques.
        🆕 LIMPIEZA: Remueve elementos estructurales corruptos del texto final.
        """
        lines = [title]  # Empezar con el título
        
        for block in blocks:
            text = block.get('text', '').strip()
            if text:  # Solo agregar líneas no vacías
                # 🧹 LIMPIEZA DIRECTA: Remover elementos estructurales corruptos
                text = self._clean_structural_corruption(text)
                
                # Si el bloque ya contiene saltos de línea, preservarlos
                if '\n' in text:
                    # Agregar una línea vacía antes del bloque si tiene múltiples líneas
                    lines.append('')
                    lines.append(text)
                else:
                    lines.append(text)
        
        # Limpiar líneas vacías excesivas al final
        result = '\n'.join(lines)
        # Eliminar más de 2 líneas vacías consecutivas
        import re
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # 🧹 LIMPIEZA FINAL: Aplicar una vez más al texto completo
        result = self._clean_structural_corruption(result)
        
        return result
    
    def _clean_structural_corruption(self, text: str) -> str:
        """
        🧹 LIMPIEZA DIRECTA DE ELEMENTOS ESTRUCTURALES CORRUPTOS
        
        Limpia elementos estructurales conocidos que aparecen en medio de los poemas.
        Específicamente diseñado para manejar: "*Antolo* *g* *ía* *Rubén Darío*"
        y otras variaciones corruptas.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio sin elementos estructurales
        """
        if not text:
            return text
        
        # 🎯 PATRONES ESPECÍFICOS para "*Antolo* *g* *ía* *Rubén Darío*"
        corrupted_patterns = [
            # Patrón exacto del usuario
            r'\*Antolo\*\s*\*g\*\s*\*ía\*\s*\*Rubén\s+Darío\*',
            
            # Variaciones con espacios
            r'\*\s*Antolo\s*\*\s*\*\s*g\s*\*\s*\*\s*ía\s*\*\s*\*\s*Rubén\s+Darío\s*\*',
            
            # Variación sin asteriscos en nombres
            r'\*Antolo\*\s*\*g\*\s*\*ía\*\s*Rubén\s+Darío',
            
            # Variaciones de formato más flexibles
            r'\*Antol[oó]\*.*\*[gí]\*.*\*[íi]a\*.*Rub[eé]n.*Dar[íi]o',
        ]
        
        cleaned_text = text
        
        # Aplicar cada patrón
        for pattern in corrupted_patterns:
            if re.search(pattern, cleaned_text, re.IGNORECASE):
                self.logger.info(f"🧹 REMOVIENDO elemento corrupto: '{pattern[:30]}...'")
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # 🎯 PATRONES GENERALES para otros elementos estructurales
        general_patterns = [
            # Títulos de antología normales
            r'Antología\s+Rubén\s+Darío',
            r'ANTOLOGÍA\s+RUBÉN\s+DARÍO',
            
            # Números de página
            r'Página\s+\d+',
            r'\b\d+\s+de\s+\d+\b',
            
            # Headers/footers comunes
            r'^Libros\s+Tauro.*$',
            r'http://www\.librostauro\.com\.ar',
        ]
        
        for pattern in general_patterns:
            if re.search(pattern, cleaned_text, re.IGNORECASE):
                self.logger.debug(f"🧹 Removiendo elemento general: patrón '{pattern[:20]}...'")
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # 🧼 LIMPIEZA FINAL
        # Remover líneas vacías excesivas
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        
        # Remover espacios al inicio y final de líneas
        lines = cleaned_text.split('\n')
        lines = [line.strip() for line in lines]
        cleaned_text = '\n'.join(lines)
        
        # Remover líneas completamente vacías al inicio y final
        cleaned_text = cleaned_text.strip()
        
        # Si el texto cambió, logear la limpieza
        if cleaned_text != text:
            original_preview = text[:50].replace('\n', '\\n')
            cleaned_preview = cleaned_text[:50].replace('\n', '\\n')
            self.logger.warning(f"🧹 TEXTO LIMPIADO:")
            self.logger.warning(f"   ANTES: '{original_preview}{'...' if len(text) > 50 else ''}'")
            self.logger.warning(f"   DESPUÉS: '{cleaned_preview}{'...' if len(cleaned_text) > 50 else ''}'")
        
        return cleaned_text
    
    def _fallback_segmentation(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔧 MEJORADO - Algoritmo de fallback más inteligente.
        """
        if not blocks:
            return []
        
        self.logger.info("🔄 Ejecutando algoritmo de fallback V2.1 más inteligente")
        
        segments = []
        current_poem_blocks = []
        current_title = None
        
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # FALLBACK: Criterios muy flexibles para títulos
            is_potential_title = (
                # Títulos específicos de poesía
                re.match(r'^(POEMA|Poema)\s+\d+', text, re.IGNORECASE) or
                # Números solos (I, II, 1, 2, etc.)
                re.match(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|\d+)\.?$', text) or
                # Títulos cortos sin punto final
                (len(text) < 80 and not text.endswith('.') and not text.endswith(',') and len(text.split()) <= 6) or
                # Texto en mayúsculas
                (text.isupper() and 3 <= len(text) <= 60) or
                # Entre comillas
                (text.startswith('"') and text.endswith('"')) or
                # Con formato especial
                block.get('is_heading', False) or
                block.get('is_bold', False) or
                block.get('is_centered', False) or
                # Títulos que parecen nombres de poemas
                self._looks_like_poem_title(text)
            )
            
            # Excluir patrones que NO son títulos de poemas
            is_not_title = (
                re.match(r'^Página\s+\d+', text) or  # "Página N de M"
                text.endswith(' de ' + str(len(blocks))) or  # Footer de página
                len(text) > 150 or  # Muy largo para ser título
                text.count('.') > 3  # Demasiada puntuación (párrafo)
            )
            
            if is_potential_title and not is_not_title:
                # Verificar si hay al menos 1 línea de verso después
                has_verses_after = False
                verse_count = 0
                
                for j in range(i + 1, min(i + 8, len(blocks))):
                    if j >= len(blocks):
                        break
                    next_block = blocks[j]
                    next_text = next_block.get('text', '').strip()
                    
                    if next_text and len(next_text) <= 150:  # Más permisivo en longitud
                        verse_count += 1
                        has_verses_after = True
                        if verse_count >= 1:  # Solo necesita 1 verso
                            break
                
                # Si encontramos un título válido
                if has_verses_after:
                    # Guardar poema anterior si existe
                    if current_poem_blocks and current_title:
                        poem_text = self._create_poem_text(current_title, current_poem_blocks)
                        if poem_text.strip():
                            segments.append({
                                'type': 'poem',
                                'text': poem_text.strip(),
                                'title': current_title,
                                'verse_count': len([b for b in current_poem_blocks if self._is_verse_line(b)]),
                                'source_blocks': len(current_poem_blocks),
                                'detection_method': 'fallback_v2.1'
                            })
                            self.logger.debug(f"✅ Poema fallback: '{current_title}' ({len(current_poem_blocks)} bloques)")
                    
                    # Iniciar nuevo poema
                    current_title = text
                    current_poem_blocks = []
                    self.logger.debug(f"🎭 Título fallback: '{current_title}'")
                    continue
            
            # Agregar bloque al poema actual
            if current_title is not None:
                current_poem_blocks.append(block)
        
        # Procesar último poema
        if current_poem_blocks and current_title:
            poem_text = self._create_poem_text(current_title, current_poem_blocks)
            if poem_text.strip():
                segments.append({
                    'type': 'poem',
                    'text': poem_text.strip(),
                    'title': current_title,
                    'verse_count': len([b for b in current_poem_blocks if self._is_verse_line(b)]),
                    'source_blocks': len(current_poem_blocks),
                    'detection_method': 'fallback_v2.1'
                })
                self.logger.debug(f"✅ Último poema fallback: '{current_title}' ({len(current_poem_blocks)} bloques)")
        
        self.logger.info(f"🔄 Fallback V2.1 completado: {len(segments)} poemas detectados")
        return segments
    
    def _looks_like_poem_title(self, text: str) -> bool:
        """
        🔧 INTELIGENTE - Detecta títulos poéticos sin rechazar preposiciones válidas.
        """
        if not text or len(text) > 80:  # Más permisivo en longitud
            return False
        
        # Patrones de títulos poéticos específicos
        title_patterns = [
            # Títulos poéticos específicos
            r'^(Canción|Soneto|Elegía|Oda|Balada|Poema|Verso)\s+',
            # Nombres propios como títulos (capitalizados)
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # "María José", "Don Juan", etc.
            # Títulos con números romanos al final
            r'^.+\s+(I|II|III|IV|V|VI|VII|VIII|IX|X)$',
            # Títulos con preposiciones comunes PERO que son claramente títulos
            r'^(Del|El|La|Los|Las|De la|De los|En el|En la)\s+[A-Z]',  # "Del árbol", "El cantar", etc.
        ]
        
        # Solo rechazar si tiene patrones OBVIAMENTE de versos
        obvious_verse_indicators = [
            r'[,;]\s+\w+',        # Coma seguida de más texto (verso continuo)
            r'[\.!?]\s*$',        # Terminaciones de oración completa
            r'^(He\s+|Yo\s+|Tú\s+)',  # Pronombres al inicio típicos de versos
            r'\b(forjé|sobrevivirme)\b',  # Verbos muy específicos de versos
        ]
        
        # Solo rechazar si contiene indicadores OBVIOS de verso
        for pattern in obvious_verse_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return any(re.match(pattern, text, re.IGNORECASE) for pattern in title_patterns)
    
    def _apply_author_detection(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔍 DETECCIÓN AUTOMÁTICA DE AUTORES PARA VERSO
        
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
        
        self.logger.info("🔍 INICIANDO DETECCIÓN AUTOMÁTICA DE AUTORES PARA VERSO")
        
        try:
            # Obtener configuración específica para verso
            detection_config = get_author_detection_config('verso')
            
            # Aplicar configuración del perfil si está disponible
            if 'confidence_threshold' in author_config:
                detection_config['confidence_threshold'] = author_config['confidence_threshold']
            if 'debug' in author_config:
                detection_config['debug'] = author_config['debug']
            
            # Detectar autor en todos los segmentos
            detected_author = detect_author_in_segments(segments, 'verso', detection_config)
            
            if detected_author:
                self.logger.info(f"✅ AUTOR DETECTADO AUTOMÁTICAMENTE: '{detected_author['name']}' "
                               f"(confianza: {detected_author['confidence']:.2f})")
                
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
                
                self.logger.info(f"📝 Información de autor añadida a {len(segments)} segmentos de verso")
                
            else:
                self.logger.info("❌ No se pudo detectar autor automáticamente")
                
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