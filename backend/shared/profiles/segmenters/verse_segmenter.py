import re
from enum import Enum
from typing import List, Dict, Any, Optional

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
    
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segmenta bloques en poemas usando una máquina de estados.
        
        Args:
            blocks: Lista de bloques de texto con metadatos
            
        Returns:
            Lista de unidades semánticas (poemas, párrafos, etc.)
        """
        segments = []
        
        # Variables para el poema actual
        current_title = None
        current_verses = []
        consecutive_empty = 0
        consecutive_verses = 0
        
        # Estado inicial
        state = VerseState.SEARCH_TITLE
        
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
                            # Solo agregar como poema si hay suficientes versos
                            segments.append({
                                "type": "poem",
                                "title": current_title,
                                "verses": current_verses,
                                "verses_count": len([v for v in current_verses if v.strip()]),
                                "stanzas": self.count_stanzas(current_verses),
                                "confidence": self._calculate_confidence(current_verses)
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
                segments.append({
                    "type": "poem",
                    "title": current_title,
                    "verses": current_verses,
                    "verses_count": len([v for v in current_verses if v.strip()]),
                    "stanzas": self.count_stanzas(current_verses),
                    "confidence": self._calculate_confidence(current_verses)
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
        Calcula un valor de confianza para el poema detectado.
        
        Args:
            verses: Lista de versos incluyendo líneas vacías
            
        Returns:
            Valor de confianza de 0.0 a 1.0
        """
        if not verses:
            return 0.0
            
        # Factores que aumentan la confianza
        factors = {
            "min_verses": 0.3,  # Base por tener versos suficientes
            "verse_regularity": 0.0,  # Consistencia en longitud de versos
            "stanza_structure": 0.0,  # Estructura clara de estrofas
            "rhyme_presence": 0.0,    # Posibles rimas (simplificado)
        }
        
        # 1. Calcular regularidad de versos (longitudes similares)
        non_empty = [v for v in verses if v.strip()]
        if len(non_empty) >= self.min_consecutive_verses:
            lengths = [len(v) for v in non_empty]
            if lengths:
                avg_len = sum(lengths) / len(lengths)
                # Desviación estándar simplificada
                variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
                std_dev = variance ** 0.5
                
                # Menor desviación = más regular = más confianza
                if avg_len > 0:
                    regularity = max(0, 1 - (std_dev / avg_len))
                    factors["verse_regularity"] = regularity * 0.3
        
        # 2. Estructura de estrofas
        stanzas = self.count_stanzas(verses)
        if stanzas > 1:
            # Más estrofas = estructura más clara = más confianza
            factors["stanza_structure"] = min(0.2, stanzas * 0.05)
        
        # 3. Rimas (simplificado - solo detecta terminaciones similares)
        if len(non_empty) >= 4:
            endings = [v[-2:] for v in non_empty if len(v) > 2]
            unique_endings = set(endings)
            
            if len(endings) > 0:
                repetition_ratio = 1 - (len(unique_endings) / len(endings))
                factors["rhyme_presence"] = repetition_ratio * 0.2
        
        # Calcular confianza total
        confidence = sum(factors.values())
        
        # Normalizar a rango 0.0-1.0
        return min(1.0, max(0.0, confidence)) 