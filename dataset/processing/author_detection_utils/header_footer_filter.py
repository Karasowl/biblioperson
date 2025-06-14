"""
Filtro para detectar y excluir headers/footers repetitivos en la detección de autores.
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple
from collections import Counter
import unicodedata

class HeaderFooterFilter:
    """
    Detecta texto que aparece repetidamente en múltiples páginas (headers/footers)
    para evitar falsos positivos en la detección de autores.
    """
    
    def __init__(self, threshold: float = 0.9):
        """
        Args:
            threshold: Porcentaje mínimo de páginas donde debe aparecer el texto
                      para considerarlo header/footer (default: 0.9 = 90%)
        """
        self.threshold = threshold
        self.logger = logging.getLogger(__name__)
        self._structural_phrases: Set[str] = set()
        self._page_count = 0
        
    def analyze_blocks(self, blocks: List[Dict[str, Any]]) -> None:
        """
        Analiza bloques de texto para identificar frases estructurales repetitivas.
        
        Args:
            blocks: Lista de bloques con información de página
        """
        if not blocks:
            return
            
        # Agrupar bloques por página
        pages = {}
        for block in blocks:
            page_num = block.get('page_num', 0)
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(block)
        
        self._page_count = len(pages)
        
        # Extraer frases de cada página
        page_phrases = {}
        for page_num, page_blocks in pages.items():
            phrases = self._extract_phrases_from_page(page_blocks)
            page_phrases[page_num] = phrases
        
        # Contar frecuencia de frases entre páginas
        phrase_counter = Counter()
        for phrases in page_phrases.values():
            for phrase in phrases:
                phrase_counter[phrase] += 1
        
        # Identificar frases estructurales (aparecen en >= threshold de páginas)
        min_pages = int(self._page_count * self.threshold)
        for phrase, count in phrase_counter.items():
            if count >= min_pages:
                self._structural_phrases.add(phrase)
                self.logger.info(f"Frase estructural detectada (en {count}/{self._page_count} páginas): '{phrase[:50]}...'")
    
    def _extract_phrases_from_page(self, blocks: List[Dict[str, Any]]) -> Set[str]:
        """
        Extrae frases candidatas de una página.
        """
        phrases = set()
        
        for block in blocks:
            text = block.get('text', '').strip()
            if not text or len(text) > 200:  # Ignorar textos muy largos
                continue
                
            # Normalizar texto para comparación
            normalized = self._normalize_text(text)
            if normalized and len(normalized) >= 3:
                phrases.add(normalized)
                
            # También extraer líneas individuales si el bloque tiene múltiples
            if '\n' in text:
                for line in text.split('\n'):
                    line_normalized = self._normalize_text(line.strip())
                    if line_normalized and len(line_normalized) >= 3:
                        phrases.add(line_normalized)
        
        return phrases
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto para comparación robusta.
        Maneja casos como "*Antolo* *g* *ía* *Rubén Darío*"
        """
        if not text:
            return ""
            
        # Remover asteriscos y espacios extra
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Unir palabras fragmentadas (e.g., "Antolo g ía" -> "Antología")
        text = re.sub(r'\b(\w)\s+(\w)\b', r'\1\2', text)
        text = re.sub(r'\b(\w{2,})\s+(\w{1,2})\s+(\w{2,})\b', r'\1\2\3', text)
        
        # Normalizar unicode y convertir a minúsculas
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        text = text.lower().strip()
        
        # Remover puntuación al inicio/final
        text = re.sub(r'^[^\w]+|[^\w]+$', '', text)
        
        return text
    
    def is_structural_text(self, text: str) -> bool:
        """
        Verifica si un texto es estructural (header/footer).
        
        Args:
            text: Texto a verificar
            
        Returns:
            True si el texto es estructural
        """
        if not text or not self._structural_phrases:
            return False
            
        normalized = self._normalize_text(text)
        
        # Verificación exacta
        if normalized in self._structural_phrases:
            return True
            
        # Verificación parcial (el texto estructural está contenido)
        for structural in self._structural_phrases:
            if structural in normalized or normalized in structural:
                return True
                
        return False
    
    def filter_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra candidatos de autor removiendo aquellos que son texto estructural.
        
        Args:
            candidates: Lista de candidatos de autor
            
        Returns:
            Lista filtrada de candidatos
        """
        filtered = []
        
        for candidate in candidates:
            name = candidate.get('name', '')
            context = candidate.get('context', [])
            
            # Verificar si el nombre es estructural
            if self.is_structural_text(name):
                self.logger.debug(f"Candidato filtrado (texto estructural): '{name}'")
                continue
                
            # Verificar si aparece en contexto estructural
            structural_contexts = sum(1 for ctx in context if self.is_structural_text(ctx))
            if structural_contexts > len(context) * 0.5:
                self.logger.debug(f"Candidato filtrado (contexto estructural): '{name}'")
                continue
                
            filtered.append(candidate)
        
        return filtered
    
    def get_structural_phrases(self) -> List[str]:
        """
        Obtiene la lista de frases estructurales detectadas.
        """
        return list(self._structural_phrases) 