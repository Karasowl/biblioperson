"""
Validador de autores usando reconocimiento de entidades nombradas (NER) con spaCy.
"""

import logging
from typing import List, Dict, Any, Optional, Set
import re

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

class SpacyNERValidator:
    """
    Valida candidatos de autor usando NER de spaCy para identificar nombres de personas.
    """
    
    def __init__(self, model_name: str = "es_core_news_sm"):
        """
        Args:
            model_name: Nombre del modelo de spaCy a usar (default: es_core_news_sm)
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.nlp = None
        self._initialize_spacy()
        
    def _initialize_spacy(self):
        """Inicializa el modelo de spaCy."""
        if not SPACY_AVAILABLE:
            self.logger.warning("spaCy no está instalado. Instale con: pip install spacy")
            self.logger.warning("Y descargue el modelo: python -m spacy download es_core_news_sm")
            return
            
        try:
            self.nlp = spacy.load(self.model_name)
            self.logger.info(f"Modelo spaCy '{self.model_name}' cargado exitosamente")
        except OSError:
            self.logger.warning(f"Modelo '{self.model_name}' no encontrado. Intentando con modelo pequeño...")
            try:
                # Intentar con el modelo más básico
                self.nlp = spacy.load("es_core_news_sm")
                self.logger.info("Modelo 'es_core_news_sm' cargado como fallback")
            except:
                self.logger.error("No se pudo cargar ningún modelo de spaCy")
                self.nlp = None
    
    def extract_person_entities(self, text: str, limit_chars: int = 5000) -> List[Dict[str, Any]]:
        """
        Extrae entidades de tipo PERSONA del texto.
        
        Args:
            text: Texto a analizar
            limit_chars: Límite de caracteres a procesar (para optimización)
            
        Returns:
            Lista de entidades persona encontradas
        """
        if not self.nlp or not text:
            return []
            
        # Limitar texto para optimización
        text_to_process = text[:limit_chars] if len(text) > limit_chars else text
        
        try:
            doc = self.nlp(text_to_process)
            persons = []
            
            for ent in doc.ents:
                if ent.label_ == "PER":  # Persona
                    person_name = ent.text.strip()
                    
                    # Validar que sea un nombre válido
                    if self._is_valid_person_name(person_name):
                        persons.append({
                            'name': self._normalize_person_name(person_name),
                            'start': ent.start_char,
                            'end': ent.end_char,
                            'context': self._get_context(text_to_process, ent.start_char, ent.end_char)
                        })
            
            # Eliminar duplicados manteniendo el primero
            seen = set()
            unique_persons = []
            for person in persons:
                normalized = person['name'].lower()
                if normalized not in seen:
                    seen.add(normalized)
                    unique_persons.append(person)
            
            return unique_persons
            
        except Exception as e:
            self.logger.error(f"Error procesando texto con spaCy: {e}")
            return []
    
    def validate_author_candidates(self, candidates: List[Dict[str, Any]], 
                                 segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida candidatos de autor contra entidades NER extraídas del texto.
        
        Args:
            candidates: Lista de candidatos de autor
            segments: Segmentos de texto para análisis
            
        Returns:
            Lista de candidatos validados/mejorados
        """
        if not self.nlp or not candidates:
            return candidates
            
        # Extraer personas de las primeras páginas
        early_text = self._extract_early_text(segments, pages=3)
        persons_found = self.extract_person_entities(early_text)
        
        # Crear conjunto de nombres normalizados para búsqueda rápida
        person_names = {p['name'].lower() for p in persons_found}
        person_dict = {p['name'].lower(): p for p in persons_found}
        
        validated_candidates = []
        
        for candidate in candidates:
            candidate_name = candidate.get('name', '').strip()
            candidate_lower = candidate_name.lower()
            
            # Copia del candidato para modificación
            validated = candidate.copy()
            
            # Verificación exacta
            if candidate_lower in person_names:
                validated['ner_validated'] = True
                validated['confidence'] = min(validated.get('confidence', 0.5) * 1.2, 1.0)
                validated['ner_context'] = person_dict[candidate_lower].get('context', '')
                self.logger.debug(f"Candidato validado por NER (exacto): {candidate_name}")
            
            # Verificación parcial (apellido o nombre)
            else:
                candidate_parts = set(candidate_lower.split())
                matches = []
                
                for person_name in person_names:
                    person_parts = set(person_name.split())
                    common_parts = candidate_parts & person_parts
                    
                    if len(common_parts) >= 1 and len(common_parts) >= len(person_parts) * 0.5:
                        matches.append(person_name)
                
                if matches:
                    validated['ner_validated'] = True
                    validated['confidence'] = min(validated.get('confidence', 0.5) * 1.1, 1.0)
                    validated['ner_matches'] = matches
                    self.logger.debug(f"Candidato validado por NER (parcial): {candidate_name} → {matches}")
                else:
                    validated['ner_validated'] = False
                    # Penalizar ligeramente si no se encuentra en NER
                    validated['confidence'] = validated.get('confidence', 0.5) * 0.95
            
            validated_candidates.append(validated)
        
        # Ordenar por confianza
        validated_candidates.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return validated_candidates
    
    def find_author_mentions(self, text: str, author_name: str) -> List[Dict[str, Any]]:
        """
        Busca menciones específicas de un autor en el texto.
        
        Args:
            text: Texto donde buscar
            author_name: Nombre del autor a buscar
            
        Returns:
            Lista de menciones encontradas con contexto
        """
        if not text or not author_name:
            return []
            
        mentions = []
        author_lower = author_name.lower()
        author_parts = author_lower.split()
        
        # Buscar menciones exactas
        pattern = re.compile(re.escape(author_name), re.IGNORECASE)
        for match in pattern.finditer(text):
            mentions.append({
                'type': 'exact',
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'context': self._get_context(text, match.start(), match.end())
            })
        
        # Buscar por apellido (última palabra del nombre)
        if len(author_parts) > 1:
            last_name = author_parts[-1]
            pattern = re.compile(r'\b' + re.escape(last_name) + r'\b', re.IGNORECASE)
            
            for match in pattern.finditer(text):
                # Verificar que no sea parte de otro nombre
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                if not any(part in context.lower() for part in author_parts[:-1]):
                    mentions.append({
                        'type': 'last_name',
                        'start': match.start(),
                        'end': match.end(),
                        'text': match.group(),
                        'context': self._get_context(text, match.start(), match.end())
                    })
        
        return mentions
    
    def _extract_early_text(self, segments: List[Dict[str, Any]], pages: int = 3) -> str:
        """Extrae texto de las primeras páginas."""
        early_segments = []
        page_count = 0
        
        for segment in segments:
            # Estimar páginas por número de caracteres (aprox 2000 chars por página)
            segment_text = segment.get('text', '') or segment.get('content', '')
            page_count += len(segment_text) / 2000
            
            early_segments.append(segment_text)
            
            if page_count >= pages:
                break
        
        return '\n\n'.join(early_segments)
    
    def _is_valid_person_name(self, name: str) -> bool:
        """Valida si un texto es un nombre de persona válido."""
        if not name or len(name) < 3:
            return False
            
        # Debe tener al menos 2 palabras para ser nombre completo
        words = name.split()
        if len(words) < 2:
            return False
            
        # Rechazar si tiene demasiados números o caracteres especiales
        if re.search(r'\d{3,}', name):  # 3 o más dígitos seguidos
            return False
            
        # Rechazar si parece una organización
        org_keywords = ['empresa', 'compañía', 'instituto', 'universidad', 'editorial']
        name_lower = name.lower()
        if any(keyword in name_lower for keyword in org_keywords):
            return False
            
        return True
    
    def _normalize_person_name(self, name: str) -> str:
        """Normaliza un nombre de persona."""
        # Remover títulos comunes
        titles = ['dr.', 'dra.', 'sr.', 'sra.', 'don', 'doña', 'prof.', 'lic.']
        name_lower = name.lower()
        
        for title in titles:
            if name_lower.startswith(title):
                name = name[len(title):].strip()
                break
        
        # Capitalizar correctamente
        words = name.split()
        normalized = []
        
        for word in words:
            if word.lower() in ['de', 'del', 'la', 'el', 'los', 'las', 'y', 'e']:
                normalized.append(word.lower())
            else:
                normalized.append(word.capitalize())
        
        return ' '.join(normalized)
    
    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Obtiene contexto alrededor de una posición."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        context = text[context_start:context_end]
        context = re.sub(r'\s+', ' ', context).strip()
        
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
            
        return context 