import re
from enum import Enum
from typing import List, Dict, Any, Optional
import math
import logging

from .base import BaseSegmenter

class VerseState(Enum):
    """Estados posibles durante el procesamiento de poemas."""
    SEARCH_TITLE = 1      # Buscando título de poema
    TITLE_FOUND = 2       # Título encontrado, esperando versos iniciales
    COLLECTING_VERSE = 3  # Recolectando versos de un poema
    STANZA_GAP = 4        # En hueco entre estrofas
    END_POEM = 5          # Finalizando poema actual
    OUTSIDE_POEM = 6      # Fuera de poema (procesando otro tipo de contenido)

class VerseSegmenter(BaseSegmenter):
    """
    Segmentador para poemas y canciones basado en una máquina de estados.
    
    Este segmentador implementa las reglas descritas en ALGORITMOS_PROPUESTOS.md
    para la detección de poemas, versos y estrofas.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        # Configurar logger
        self.logger = logging.getLogger(__name__)
        
        # Configurar thresholds con valores por defecto si no están en config
        self.thresholds = self.config.get('thresholds', {})
        self.max_verse_length = self.thresholds.get('max_verse_length', 120)
        self.max_title_length = self.thresholds.get('max_title_length', 80)
        self.min_consecutive_verses = self.thresholds.get('min_consecutive_verses', 3)
        self.min_stanza_verses = self.thresholds.get('min_stanza_verses', 2)
        self.max_empty_in_stanza = self.thresholds.get('max_empty_in_stanza', 2)
        self.min_empty_between_stanzas = self.thresholds.get('min_empty_between_stanzas', 2)
        self.max_empty_between_stanzas = self.thresholds.get('max_empty_between_stanzas', 3)
        self.max_empty_end_poem = self.thresholds.get('max_empty_end_poem', 3)
        self.max_space_ratio = self.thresholds.get('max_space_ratio', 0.35)
        
        # Umbral de confianza para poemas
        self.confidence_threshold = self.thresholds.get('confidence_threshold', 0.5)
        
        # Patrones para detección de título y estilos
        self.title_patterns = self.config.get('title_patterns', [
            r'^# ',                 # Markdown H1
            r'^\* ',                # Asterisco inicial
            r'^> ',                 # Cita
            r'^[A-Z ]{4,}:$'        # TÍTULO: (todo mayúsculas seguido de dos puntos)
        ])
        self.title_regex = re.compile('|'.join(self.title_patterns))
        
        # Patrón para acordes
        self.chord_pattern = re.compile(r'^\s*\[[A-G][#b]?m?[0-9]?(\([0-9]\))?\]\s*$')
    
    def set_confidence_threshold(self, threshold: float):
        """
        Establece el umbral de confianza para detección de poemas.
        
        Args:
            threshold: Valor entre 0.0 y 1.0
        """
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        self.logger.debug(f"Umbral de confianza establecido a: {self.confidence_threshold}")
    
    def is_verse(self, text: str) -> bool:
        """
        Determina si una línea es un verso según heurísticas.
        
        Args:
            text: Texto de la línea
            
        Returns:
            True si parece un verso, False en caso contrario
        """
        stripped = text.strip()
        if not stripped:
            return False
            
        # Chequear longitud
        if len(stripped) <= self.max_verse_length:
            # Si es una línea de acordes, no es un verso
            if self.chord_pattern.match(stripped):
                return False
                
            # Si termina en puntuación final, podría ser diálogo, no verso
            if stripped[-1] in '.!?' and not self._is_verse_by_context(stripped):
                return False
                
            return True
            
        # Chequear ratio de espacios (para versos con formato especial)
        space_count = stripped.count(' ')
        if space_count / len(stripped) >= self.max_space_ratio:
            return True
            
        return False
    
    def _is_verse_by_context(self, text: str) -> bool:
        """
        Análisis adicional para líneas que podrían ser diálogo.
        (Implementación simplificada, se expandiría con análisis de contexto)
        """
        # Si empieza con guión de diálogo y termina en puntuación, probablemente es diálogo
        if text.startswith('—') and text[-1] in '.!?':
            return False
        return True
        
    def has_title_format(self, block: Dict[str, Any]) -> bool:
        """
        Determina si un bloque tiene formato de título.
        
        Args:
            block: Bloque de texto con metadatos
            
        Returns:
            True si parece un título, False en caso contrario
        """
        # Si ya viene marcado como heading desde el loader, es título
        if block.get('is_heading', False):
            return True
            
        text = block.get('text', '').strip()
        if not text:
            return False
            
        # Verificar longitud máxima
        if len(text) > self.max_title_length:
            return False
            
        # Verificar patrones de formato
        if self.title_regex.search(text):
            return True
            
        # Verificar mayúsculas (para títulos en mayúsculas)
        if len(text) >= 4:  # Solo para textos no muy cortos
            uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if uppercase_ratio > 0.7:  # >70% mayúsculas
                return True
            
        # Verificar si está en negrita o centrado (si hay metadatos disponibles)
        if block.get('is_bold', False) or block.get('is_centered', False):
            return True
            
        return False
    
    def count_stanzas(self, verses: List[str]) -> int:
        """
        Cuenta el número de estrofas en un conjunto de versos.
        
        Args:
            verses: Lista de versos incluyendo líneas vacías
            
        Returns:
            Número de estrofas detectadas
        """
        stanzas = 1
        empty_count = 0
        
        for verse in verses:
            if not verse.strip():
                empty_count += 1
                if empty_count >= self.min_empty_between_stanzas:
                    stanzas += 1
                    empty_count = 0
            else:
                empty_count = 0
                
        return stanzas
    
    def _create_numbered_verses(self, verses: List[str]) -> List[Dict[str, Any]]:
        """
        Convierte una lista de versos a una lista de objetos con numeración.
        
        Args:
            verses: Lista de versos incluyendo líneas vacías
            
        Returns:
            Lista de objetos con numeración para cada verso
        """
        numbered_verses = []
        verse_number = 1
        
        for i, verse in enumerate(verses):
            if not verse.strip():
                # Para líneas vacías, no incrementar número pero mantener en estructura
                numbered_verses.append({
                    "text": "",
                    "line_number": i + 1,  # Número de línea en el poema
                    "verse_number": None   # No es un verso numerado
                })
            else:
                # Para versos con contenido, incrementar numeración
                numbered_verses.append({
                    "text": verse,
                    "line_number": i + 1,
                    "verse_number": verse_number
                })
                verse_number += 1
                
        return numbered_verses
    
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segmenta bloques en poemas usando una máquina de estados.
        
        Args:
            blocks: Lista de bloques de texto con metadatos
            
        Returns:
            Lista de unidades semánticas (poemas, párrafos, etc.)
        """
        segments = []
        
        # Primero procesamos bloques que ya vienen marcados como poemas
        for block in blocks:
            # Si el loader ya detectó que es un poema (DocxLoader por ejemplo)
            if block.get('is_poem', False):
                text = block.get('texto', '')
                title = block.get('titulo')
                verses = text.split('\n') if text else []
                
                # Calculamos algunos metadatos adicionales
                stanzas = self.count_stanzas(verses)
                confidence = self._calculate_confidence(verses)
                verses_count = block.get('verse_count', len([v for v in verses if v.strip()]))
                
                # Solo incluir poemas que superen el umbral de confianza
                if confidence >= self.confidence_threshold:
                    # Crear segmento de poema con versos numerados
                    numbered_verses = self._create_numbered_verses(verses)
                    
                    poem = {
                        "type": "poem",
                        "title": title or "Sin título",
                        "numbered_verses": numbered_verses,
                        "verses_count": verses_count,
                        "stanzas": stanzas,
                        "confidence": confidence,
                        # Copiar metadatos adicionales
                        "fuente": block.get('fuente'),
                        "contexto": block.get('contexto'),
                        "fecha": block.get('fecha')
                    }
                    segments.append(poem)
                else:
                    self.logger.debug(f"Poema descartado por baja confianza: {confidence} < {self.confidence_threshold}")
                continue
                
        # Variables para el algoritmo de detección de poemas
        current_title = None
        current_verses = []
        consecutive_empty = 0
        consecutive_verses = 0
        
        # Estado inicial
        state = VerseState.SEARCH_TITLE
        
        # Procesamiento basado en estados para bloques sin marcar
        for i, block in enumerate(blocks):
            # Skip bloques que ya se procesaron como poemas
            if block.get('is_poem', False):
                continue
                
            text = block.get('text', '').strip()
            is_empty = not text
            
            # Actualizar contador de líneas vacías
            if is_empty:
                consecutive_empty += 1
                # No procesar más lógica para líneas vacías, solo actualizar contador
                continue
            else:
                # Línea no vacía, evaluar según estado actual
                is_potential_title = self.has_title_format(block)
                is_verse = self.is_verse(text)
                
                # Transiciones de estado y acciones
                if state == VerseState.SEARCH_TITLE:
                    if is_potential_title:
                        # Posible título encontrado, cambiar estado y verificar lo que sigue
                        current_title = text
                        consecutive_empty = 0
                        state = VerseState.TITLE_FOUND
                    elif is_verse:
                        # Verso sin título previo, podría ser poema sin título
                        consecutive_verses = 1
                        current_verses.append(text)
                        if self._peek_ahead_for_verses(blocks, i, 2):
                            # Si vienen más versos, tratarlo como inicio de poema sin título
                            state = VerseState.COLLECTING_VERSE
                        else:
                            # Línea suelta, no es poema
                            segments.append({
                                "type": "paragraph",
                                "text": text
                            })
                            current_verses = []
                            consecutive_verses = 0
                    else:
                        # Texto normal, no poema
                        segments.append({
                            "type": "paragraph", 
                            "text": text
                        })
                
                elif state == VerseState.TITLE_FOUND:
                    # Después de un título, esperamos versos
                    if is_verse:
                        current_verses.append(text)
                        consecutive_verses = 1
                        consecutive_empty = 0
                        
                        # Si vienen más versos, confirmar poema
                        if self._peek_ahead_for_verses(blocks, i, self.min_consecutive_verses - 1):
                            state = VerseState.COLLECTING_VERSE
                        
                    elif is_potential_title:
                        # Otro título después de un título, sin versos intermedios
                        # El título anterior era falso positivo
                        segments.append({
                            "type": "heading",
                            "text": current_title,
                            "level": block.get('heading_level', 1)
                        })
                        current_title = text
                        consecutive_empty = 0
                        # Seguimos en estado TITLE_FOUND con el nuevo título
                        
                    else:
                        # Texto normal después de título, no es poema
                        segments.append({
                            "type": "heading",
                            "text": current_title,
                            "level": block.get('heading_level', 1)
                        })
                        segments.append({
                            "type": "paragraph",
                            "text": text
                        })
                        current_title = None
                        state = VerseState.SEARCH_TITLE
                
                elif state == VerseState.COLLECTING_VERSE:
                    if is_verse:
                        # Continuar recogiendo versos
                        current_verses.append(text)
                        consecutive_verses += 1
                        consecutive_empty = 0
                        
                    elif is_potential_title:
                        # Título después de recoger algunos versos = fin de poema
                        state = VerseState.END_POEM
                        # Procesaremos el título en la siguiente iteración, tras añadir el poema
                        i -= 1  # Retroceder para reprocesar este bloque
                        
                    else:
                        # Texto normal después de versos = fin de poema
                        state = VerseState.END_POEM
                        # Retroceder para procesar este bloque después
                        i -= 1
                
                elif state == VerseState.STANZA_GAP:
                    if is_verse:
                        # Verso después de hueco = nueva estrofa del mismo poema
                        current_verses.append("")  # Añadir marcador de separación de estrofa
                        current_verses.append(text)
                        consecutive_verses += 1
                        consecutive_empty = 0
                        state = VerseState.COLLECTING_VERSE
                        
                    elif is_potential_title:
                        # Título después de hueco = fin del poema anterior
                        state = VerseState.END_POEM
                        # Retroceder para procesar título en siguiente iteración
                        i -= 1
                        
                    else:
                        # Texto normal después de hueco = fin de poema
                        state = VerseState.END_POEM
                        # Retroceder para procesar texto en siguiente iteración
                        i -= 1
                
                elif state == VerseState.END_POEM:
                    # Finalizar poema actual
                    if current_verses:
                        if consecutive_verses >= self.min_consecutive_verses:
                            # Calcular confianza
                            confidence = self._calculate_confidence(current_verses)
                            
                            # Solo agregar como poema si supera el umbral de confianza
                            if confidence >= self.confidence_threshold:
                                # Agregar versos numerados
                                numbered_verses = self._create_numbered_verses(current_verses)
                                
                                segments.append({
                                    "type": "poem",
                                    "title": current_title or "Sin título",
                                    "numbered_verses": numbered_verses,
                                    "verses_count": len([v for v in current_verses if v.strip()]),
                                    "stanzas": self.count_stanzas(current_verses),
                                    "confidence": confidence
                                })
                            else:
                                self.logger.debug(f"Poema final descartado por baja confianza: {confidence} < {self.confidence_threshold}")
                                # Tratar como párrafos normales
                                if current_title:
                                    segments.append({
                                        "type": "heading", 
                                        "text": current_title,
                                        "level": 1
                                    })
                                
                                for verse in current_verses:
                                    if verse.strip():
                                        segments.append({
                                            "type": "paragraph",
                                            "text": verse
                                        })
                        else:
                            # Pocos versos, tratar como párrafos normales
                            if current_title:
                                segments.append({
                                    "type": "heading", 
                                    "text": current_title,
                                    "level": 1
                                })
                            
                            for verse in current_verses:
                                if verse.strip():
                                    segments.append({
                                        "type": "paragraph",
                                        "text": verse
                                    })
                    
                    # Reiniciar variables para siguiente poema
                    current_title = None
                    current_verses = []
                    consecutive_verses = 0
                    consecutive_empty = 0
                    
                    # Volver a estado inicial y reprocesar el bloque actual
                    state = VerseState.SEARCH_TITLE
                    i -= 1  # Retroceder para procesar este bloque desde inicio
            
            # Transiciones basadas en contador de líneas vacías
            if consecutive_empty > 0:
                if state == VerseState.COLLECTING_VERSE:
                    if consecutive_empty <= self.max_empty_in_stanza:
                        # Pocas vacías: sigue siendo misma estrofa
                        pass
                    elif consecutive_empty <= self.max_empty_between_stanzas:
                        # Vacías intermedias: posible separación de estrofas
                        state = VerseState.STANZA_GAP
                    else:
                        # Demasiadas vacías: fin de poema
                        state = VerseState.END_POEM
                
                elif state == VerseState.TITLE_FOUND:
                    if consecutive_empty > self.max_empty_in_stanza:
                        # Demasiadas vacías tras título, no parece inicio de poema
                        segments.append({
                            "type": "heading",
                            "text": current_title,
                            "level": block.get('heading_level', 1)
                        })
                        current_title = None
                        state = VerseState.SEARCH_TITLE
        
        # Procesar estado final - si quedó un poema sin cerrar
        if state in (VerseState.COLLECTING_VERSE, VerseState.STANZA_GAP) and current_verses:
            if consecutive_verses >= self.min_consecutive_verses:
                # Calcular confianza
                confidence = self._calculate_confidence(current_verses)
                
                # Solo agregar como poema si supera el umbral de confianza
                if confidence >= self.confidence_threshold:
                    # Agregar versos numerados
                    numbered_verses = self._create_numbered_verses(current_verses)
                    
                    segments.append({
                        "type": "poem",
                        "title": current_title or "Sin título",
                        "numbered_verses": numbered_verses,
                        "verses_count": len([v for v in current_verses if v.strip()]),
                        "stanzas": self.count_stanzas(current_verses),
                        "confidence": confidence
                    })
                else:
                    self.logger.debug(f"Poema final descartado por baja confianza: {confidence} < {self.confidence_threshold}")
                    # Tratar como párrafos normales
                    if current_title:
                        segments.append({
                            "type": "heading", 
                            "text": current_title,
                            "level": 1
                        })
                    
                    for verse in current_verses:
                        if verse.strip():
                            segments.append({
                                "type": "paragraph",
                                "text": verse
                            })
            else:
                # Pocos versos, tratar como párrafos normales
                if current_title:
                    segments.append({
                        "type": "heading", 
                        "text": current_title,
                        "level": 1
                    })
                
                for verse in current_verses:
                    if verse.strip():
                        segments.append({
                            "type": "paragraph",
                            "text": verse
                        })
        
        return segments
    
    def _peek_ahead_for_verses(self, blocks: List[Dict[str, Any]], 
                              current_idx: int, count: int) -> bool:
        """
        Mira adelante en los bloques para verificar si hay suficientes versos.
        
        Args:
            blocks: Lista completa de bloques
            current_idx: Índice actual
            count: Número de versos a buscar
            
        Returns:
            True si hay al menos 'count' versos en los bloques siguientes
        """
        if current_idx >= len(blocks) - 1:
            return False
            
        verse_count = 0
        empty_count = 0
        
        for i in range(current_idx + 1, min(len(blocks), current_idx + count*2 + 5)):
            text = blocks[i].get('text', '').strip()
            
            if not text:
                empty_count += 1
                if empty_count > self.max_empty_in_stanza:
                    # Demasiadas líneas vacías, corta la búsqueda
                    break
                continue
                
            # Reiniciar contador de vacías si encontramos texto
            empty_count = 0
            
            # Si es verso, incrementar contador
            if self.is_verse(text):
                verse_count += 1
                if verse_count >= count:
                    return True
            else:
                # Si encontramos algo que no es verso, cortar búsqueda
                break
                
        return False
    
    def _calculate_confidence(self, verses: List[str]) -> float:
        """
        Calcula un valor de confianza para el poema detectado con análisis avanzado.
        
        Args:
            verses: Lista de versos incluyendo líneas vacías
            
        Returns:
            Valor de confianza de 0.0 a 1.0
        """
        if not verses:
            return 0.0
            
        # Filtrar versos no vacíos
        non_empty = [v for v in verses if v.strip()]
        if not non_empty:
            return 0.0
            
        # Factores que aumentan la confianza
        factors = {
            "min_verses": 0.2,      # Base por tener versos suficientes
            "verse_regularity": 0.0, # Consistencia en longitud de versos
            "stanza_structure": 0.0, # Estructura clara de estrofas
            "rhyme_patterns": 0.0,   # Patrones de rima (análisis avanzado)
            "line_brevity": 0.0,     # Versos cortos (característica poética)
            "metric_patterns": 0.0,  # Patrones métricos
            "linguistic_features": 0.0, # Características lingüísticas poéticas
        }
        
        # 1. Calcular regularidad de versos (longitudes similares)
        if len(non_empty) >= self.min_consecutive_verses:
            lengths = [len(v) for v in non_empty]
            
            if lengths:
                avg_len = sum(lengths) / len(lengths)
                # Desviación estándar simplificada
                variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
                std_dev = variance ** 0.5
                
                # Menor desviación = más regular = más confianza
                if avg_len > 0:
                    regularity = max(0, 1 - min(std_dev / avg_len, 1.0))
                    factors["verse_regularity"] = regularity * 0.2
                    
                # Bonus por versos cortos (poemas suelen tener versos más breves que prosa)
                if avg_len < 50:
                    # Menor longitud promedio = más probable que sea poema
                    brevity_score = max(0, 1 - (avg_len / 100))
                    factors["line_brevity"] = brevity_score * 0.1
        
        # 2. Estructura de estrofas
        stanzas = self.count_stanzas(verses)
        if stanzas > 1:
            # Calculamos el tamaño promedio de estrofas
            stanza_sizes = []
            current_size = 0
            
            for verse in verses:
                if verse.strip():
                    current_size += 1
                elif current_size > 0:
                    stanza_sizes.append(current_size)
                    current_size = 0
            
            if current_size > 0:
                stanza_sizes.append(current_size)
                
            # Regularidad de tamaño de estrofas
            if stanza_sizes and len(stanza_sizes) > 1:
                avg_stanza = sum(stanza_sizes) / len(stanza_sizes)
                stanza_variance = sum((s - avg_stanza) ** 2 for s in stanza_sizes) / len(stanza_sizes)
                stanza_regularity = max(0, 1 - min(math.sqrt(stanza_variance) / avg_stanza, 1.0))
                
                # Más estrofas y más regulares = estructura más clara = más confianza
                stanza_factor = min(0.15, (stanzas * 0.03) * (1 + stanza_regularity))
                factors["stanza_structure"] = stanza_factor
        
        # 3. Análisis de patrones de rima
        if len(non_empty) >= 4:
            # Extraer últimas palabras y finales fonéticos estimados
            endings = []
            
            for verse in non_empty:
                words = verse.strip().split()
                if words:
                    # Tomar última palabra y sus últimos 2-3 caracteres como aproximación fonética
                    last_word = words[-1].lower().rstrip(',.;:!?')
                    if len(last_word) >= 3:
                        endings.append(last_word[-3:])
                    elif last_word:
                        endings.append(last_word)
            
            # Contar repeticiones de terminaciones
            if endings:
                ending_counts = {}
                for e in endings:
                    ending_counts[e] = ending_counts.get(e, 0) + 1
                
                # Calcular frecuencia de repeticiones
                repeated = sum(count - 1 for count in ending_counts.values() if count > 1)
                
                # Normalizar por número total de finales
                rhyme_score = min(repeated / len(endings), 1.0)
                
                # Identificar patrones de rima potenciales
                rhyme_patterns = self._identify_rhyme_patterns(endings)
                if rhyme_patterns:
                    rhyme_score = max(rhyme_score, 0.7)  # Si hay patrón evidente, aumentar score
                
                factors["rhyme_patterns"] = rhyme_score * 0.25
        
        # 4. Análisis de características lingüísticas poéticas
        poetic_expressions = self._analyze_poetic_expressions(non_empty)
        factors["linguistic_features"] = poetic_expressions * 0.1
        
        # 5. Patrones métricos (simplificado)
        if len(non_empty) >= 3:
            metric_score = self._analyze_metric_patterns(non_empty)
            factors["metric_patterns"] = metric_score * 0.15
        
        # Calcular confianza total
        confidence = sum(factors.values())
        
        # Normalizar a rango 0.0-1.0
        return min(1.0, max(0.0, confidence))
    
    def _identify_rhyme_patterns(self, endings: List[str]) -> bool:
        """
        Identifica patrones potenciales de rima (ABAB, AABB, etc.).
        
        Args:
            endings: Lista de terminaciones fonéticas
            
        Returns:
            True si se identifica un patrón, False en caso contrario
        """
        if len(endings) < 4:
            return False
            
        # Convertir terminaciones a patrones (A, B, C, etc.)
        pattern = []
        ending_to_letter = {}
        next_letter = 'A'
        
        for ending in endings:
            if ending not in ending_to_letter:
                ending_to_letter[ending] = next_letter
                next_letter = chr(ord(next_letter) + 1)
            pattern.append(ending_to_letter[ending])
        
        # Buscar patrones comunes de rima
        pattern_str = ''.join(pattern)
        common_patterns = [
            'ABAB', 'AABB', 'ABBA', 'AAAA',
            'ABCB', 'AABCCB'
        ]
        
        # Verificar si existe alguno de los patrones comunes en segmentos
        for i in range(len(pattern_str) - 3):
            segment = pattern_str[i:i+4]
            for p in common_patterns:
                if segment in p:
                    return True
        
        return False
    
    def _analyze_poetic_expressions(self, verses: List[str]) -> float:
        """
        Analiza el texto buscando expresiones típicas de poesía.
        
        Args:
            verses: Lista de versos no vacíos
            
        Returns:
            Puntuación de 0.0 a 1.0
        """
        text = ' '.join(verses).lower()
        
        # Palabras y expresiones comunes en poesía
        poetic_words = [
            'alma', 'amor', 'corazón', 'sueño', 'cielo', 'estrella', 'noche', 
            'mar', 'sol', 'luna', 'luz', 'sombra', 'silencio', 'tiempo',
            'suspiro', 'lágrima', 'rosa', 'flor', 'vida', 'muerte'
        ]
        
        # Figuras retóricas comunes 
        rhetorical_patterns = [
            r'como si', r'cual', r'semejante a', r'parece',  # símiles
            r'oh!', r'ah!', r'!', r'\?',  # exclamaciones e interrogaciones retóricas
            r'ni', r'no',  # negaciones repetidas (frecuentes en poesía)
            r'siempre', r'nunca', r'jamás',  # absolutos (comunes en poesía)
            r'tan', r'qué',  # intensificadores
        ]
        
        # Contar palabras poéticas
        word_matches = sum(1 for word in poetic_words if word in text)
        max_possible_words = min(len(poetic_words), len(verses) * 2)
        word_score = min(word_matches / max_possible_words, 1.0) if max_possible_words > 0 else 0
        
        # Buscar patrones retóricos
        pattern_matches = sum(len(re.findall(pattern, text)) for pattern in rhetorical_patterns)
        max_possible_patterns = len(verses) * 2
        pattern_score = min(pattern_matches / max_possible_patterns, 1.0) if max_possible_patterns > 0 else 0
        
        # Combinar scores
        return (word_score * 0.6) + (pattern_score * 0.4)
    
    def _analyze_metric_patterns(self, verses: List[str]) -> float:
        """
        Analiza patrones métricos simplificados (basados en sílabas aproximadas).
        
        Args:
            verses: Lista de versos no vacíos
            
        Returns:
            Puntuación de 0.0 a 1.0
        """
        # Función simplificada para estimar sílabas en español
        def estimate_syllables(text):
            # Contar vocales como aproximación básica
            vowels = 'aeiouáéíóúü'
            count = sum(1 for c in text.lower() if c in vowels)
            
            # Ajustar por diptongos comunes (aproximación)
            diphthongs = ['ia', 'ie', 'io', 'iu', 'ua', 'ue', 'ui', 'uo', 'ai', 'ei', 'oi', 'ui']
            for d in diphthongs:
                count -= text.lower().count(d)
                
            return max(count, 1)
        
        # Calcular sílabas estimadas por verso
        syllables = [estimate_syllables(verse) for verse in verses]
        
        if not syllables:
            return 0.0
            
        # Analizar regularidad en número de sílabas
        avg_syllables = sum(syllables) / len(syllables)
        variance = sum((s - avg_syllables) ** 2 for s in syllables) / len(syllables)
        std_dev = math.sqrt(variance)
        
        # Si hay poca variación, hay un patrón métrico fuerte
        regularity = max(0, 1 - (std_dev / avg_syllables))
        
        # Para versos con longitud común en poesía española (7-11 sílabas), dar bonus
        common_length_verses = sum(1 for s in syllables if 7 <= s <= 14)
        common_ratio = common_length_verses / len(syllables)
        
        # Combinar ambos factores
        return (regularity * 0.7) + (common_ratio * 0.3)
    
    def get_full_text_from_numbered_verses(self, numbered_verses: List[Dict[str, Any]]) -> str:
        """
        Reconstruye el texto completo a partir de los versos numerados.
        
        Args:
            numbered_verses: Lista de versos numerados
            
        Returns:
            Texto completo del poema
        """
        return "\n".join(verse["text"] for verse in numbered_verses) 