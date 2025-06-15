#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Detección Contextual de Autores
==========================================

Sistema simplificado y robusto para detectar autores basado en:
1. Análisis de contextos de atribución específicos
2. Validación posicional y sintáctica
3. Detección de patrones morfológicos hispanos
4. Validación cruzada para evitar falsos positivos

Sin dependencias externas complejas - funciona con bibliotecas estándar.
"""

import re
import logging
import unicodedata
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import Counter, defaultdict

@dataclass
class ContextualAuthorCandidate:
    """Candidato a autor con información contextual"""
    name: str
    confidence: float = 0.0
    attribution_contexts: List[str] = None
    positions: List[int] = None
    morphological_score: float = 0.0
    contextual_score: float = 0.0
    cross_validation_score: float = 0.0
    
    def __post_init__(self):
        if self.attribution_contexts is None:
            self.attribution_contexts = []
        if self.positions is None:
            self.positions = []

class HispanicMorphologyAnalyzer:
    """Analizador de morfología de nombres hispanos sin bases de datos externas"""
    
    def __init__(self):
        # Patrones morfológicos comunes en nombres hispanos
        self.name_endings = {
            # Terminaciones masculinas comunes
            'masculine': {'o', 'os', 'án', 'ón', 'és', 'ez', 'iz', 'uz'},
            # Terminaciones femeninas comunes
            'feminine': {'a', 'as', 'ía', 'ción', 'sión', 'dad', 'tad', 'ez'}
        }
        
        # Prefijos y sufijos típicos de apellidos hispanos
        self.surname_patterns = {
            'prefixes': {'de', 'del', 'la', 'las', 'los', 'san', 'santa'},
            'suffixes': {'ez', 'az', 'iz', 'oz', 'uz', 'ández', 'énez', 'ínez', 'ónez', 'únez'}
        }
        
        # Títulos y tratamientos que acompañan nombres
        self.titles = {
            'don', 'doña', 'fray', 'sor', 'san', 'santa', 'santo',
            'dr', 'dra', 'prof', 'lic', 'ing', 'arq'
        }
    
    def analyze_name_morphology(self, name: str) -> float:
        """Analiza la morfología de un nombre para determinar si es hispano"""
        if not name or len(name.split()) < 2:
            return 0.0
        
        parts = [part.lower().strip() for part in name.split()]
        score = 0.0
        total_parts = len(parts)
        
        for i, part in enumerate(parts):
            part_score = 0.0
            
            # Verificar si es un título
            if part in self.titles:
                part_score += 0.3
            
            # Verificar terminaciones típicas
            for ending in self.name_endings['masculine'] | self.name_endings['feminine']:
                if part.endswith(ending):
                    part_score += 0.4
                    break
            
            # Verificar patrones de apellidos
            if i > 0:  # No es el primer nombre
                for suffix in self.surname_patterns['suffixes']:
                    if part.endswith(suffix):
                        part_score += 0.5
                        break
                
                for prefix in self.surname_patterns['prefixes']:
                    if part.startswith(prefix):
                        part_score += 0.3
                        break
            
            # Verificar estructura silábica típica
            if self._has_hispanic_syllable_pattern(part):
                part_score += 0.2
            
            score += min(part_score, 1.0)
        
        return min(score / total_parts, 1.0)
    
    def _has_hispanic_syllable_pattern(self, word: str) -> bool:
        """Verifica si una palabra tiene patrones silábicos típicos del español"""
        # Patrones consonante-vocal típicos del español
        hispanic_patterns = [
            r'[bcdfghjklmnpqrstvwxyz][aeiouáéíóú]',
            r'[aeiouáéíóú][bcdfghjklmnpqrstvwxyz]',
            r'rr', r'll', r'ch', r'ñ'
        ]
        
        for pattern in hispanic_patterns:
            if re.search(pattern, word.lower()):
                return True
    
    def _load_known_authors(self) -> Set[str]:
        """Carga la lista blanca de autores conocidos"""
        try:
            # Buscar el archivo de autores conocidos
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(os.path.dirname(current_dir), 'config')
            authors_file = os.path.join(config_dir, 'known_authors.json')
            
            if os.path.exists(authors_file):
                with open(authors_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extraer todos los autores de todas las categorías
                known_authors = set()
                for category in data.get('authors', {}).values():
                    if isinstance(category, list):
                        for author in category:
                            known_authors.add(author.lower())
                            # También agregar variaciones comunes
                            known_authors.add(author.lower().replace(',', ''))
                
                if self.debug:
                    self.logger.info(f"Cargados {len(known_authors)} autores conocidos")
                
                return known_authors
            else:
                if self.debug:
                    self.logger.warning(f"No se encontró archivo de autores conocidos: {authors_file}")
                return set()
                
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error cargando autores conocidos: {e}")
            return set()
    
    def _is_known_author(self, name: str) -> bool:
        """Verifica si un nombre está en la lista de autores conocidos"""
        if not self.known_authors:
            return False
        
        name_lower = name.lower().strip()
        
        # Búsqueda exacta
        if name_lower in self.known_authors:
            return True
        
        # Búsqueda por partes (nombre y apellido por separado)
        name_parts = name_lower.split()
        if len(name_parts) >= 2:
            # Buscar combinaciones comunes
            full_name_variants = [
                ' '.join(name_parts),
                ' '.join(name_parts[:2]),  # Solo primeros dos nombres
                f"{name_parts[-1]}, {' '.join(name_parts[:-1])}",  # Apellido, Nombre
            ]
            
            for variant in full_name_variants:
                if variant in self.known_authors:
                    return True
        
        return False

class AttributionContextAnalyzer:
    """Analizador de contextos de atribución de autoría"""
    
    def __init__(self):
        # Patrones explícitos de atribución
        self.explicit_attribution_patterns = [
            # Patrón más específico para "por" - requiere contexto de autoría explícito
            r'(?:autor|autora)\s*:?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
            r'(?:escrito|compuesto|creado|redactado|obra)\s+por\s*:?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
            r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)\s*(?:escribió|compuso|creó|redactó)',
            # Patrón "de" solo al final de línea y con contexto de título
            r'(?:poema|obra|texto|libro)\s+(?:de|del)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)$',
            # Patrón de guión mejorado: solo nombres típicos de autor (máximo 3 palabras, evitar frases poéticas)
            r'^(?!.*(?:zumbas|vuela|canta|baila|danza|susurra|murmura|grita|llora|ríe))([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})\s*[-–—]',
            # Patrón para nombres al final del texto (típico en poemas)
            r'\n\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*$',
        ]
        
        # Verbos de autoría
        self.authorship_verbs = {
            'escribir', 'componer', 'crear', 'redactar', 'firmar',
            'elaborar', 'desarrollar', 'producir', 'realizar'
        }
        
        # Sustantivos de autoría
        self.authorship_nouns = {
            'autor', 'autora', 'poeta', 'poetisa', 'escritor', 'escritora',
            'novelista', 'dramaturgo', 'ensayista', 'cronista'
        }
    
    def find_attribution_contexts(self, text: str) -> List[Tuple[str, str, int]]:
        """Encuentra contextos de atribución en el texto"""
        contexts = []
        
        # Buscar patrones explícitos
        for pattern in self.explicit_attribution_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                name = match.group(1).strip()
                context = match.group(0)
                position = match.start()
                contexts.append((name, context, position))
        
        return contexts
    
    def analyze_contextual_strength(self, name: str, text: str) -> float:
        """Analiza la fuerza del contexto de autoría para un nombre"""
        score = 0.0
        name_lower = name.lower()
        
        # Buscar el nombre en contextos de autoría
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            if name_lower in sentence.lower():
                sentence_score = 0.0
                
                # Verificar verbos de autoría
                for verb in self.authorship_verbs:
                    if verb in sentence.lower():
                        sentence_score += 0.4
                
                # Verificar sustantivos de autoría
                for noun in self.authorship_nouns:
                    if noun in sentence.lower():
                        sentence_score += 0.3
                
                # Verificar patrones de atribución
                if re.search(r'(?:por|de)\s+' + re.escape(name_lower), sentence.lower()):
                    sentence_score += 0.5
                
                score += min(sentence_score, 1.0)
        
        return min(score, 1.0)

class PositionalAnalyzer:
    """Analizador de posición de nombres en el texto"""
    
    def analyze_position_score(self, name: str, text: str, positions: List[int]) -> float:
        """Analiza la puntuación basada en la posición del nombre"""
        if not positions:
            return 0.0
        
        text_length = len(text)
        score = 0.0
        
        for pos in positions:
            # Posiciones al inicio del texto tienen mayor peso
            if pos < text_length * 0.1:  # Primer 10%
                score += 0.8
            elif pos < text_length * 0.2:  # Primer 20%
                score += 0.6
            elif pos > text_length * 0.9:  # Último 10%
                score += 0.7
            elif pos > text_length * 0.8:  # Último 20%
                score += 0.5
            else:
                score += 0.2
        
        return min(score / len(positions), 1.0)

class CrossValidator:
    """Validador cruzado para evitar falsos positivos"""
    
    def validate_author_candidate(self, name: str, text: str) -> float:
        """Valida que el candidato sea realmente autor y no solo mencionado"""
        score = 1.0  # Empezar con puntuación máxima
        name_lower = name.lower()
        
        # Penalizar si aparece como objeto de biografía
        biography_patterns = [
            r'biografía\s+de\s+' + re.escape(name_lower),
            r'vida\s+de\s+' + re.escape(name_lower),
            r'historia\s+de\s+' + re.escape(name_lower),
            name_lower + r'\s+(?:nació|murió|vivió|fue)'
        ]
        
        for pattern in biography_patterns:
            if re.search(pattern, text.lower()):
                score -= 0.4
        
        # Penalizar si aparece como personaje
        character_patterns = [
            r'personaje\s+' + re.escape(name_lower),
            r'protagonista\s+' + re.escape(name_lower),
            name_lower + r'\s+(?:dijo|pensó|sintió|caminó)'
        ]
        
        for pattern in character_patterns:
            if re.search(pattern, text.lower()):
                score -= 0.3
        
        # Penalizar si aparece demasiado frecuentemente (posible tema principal)
        name_count = text.lower().count(name_lower)
        text_words = len(text.split())
        frequency_ratio = name_count / max(text_words, 1)
        
        if frequency_ratio > 0.02:  # Más del 2% del texto
            score -= 0.5
        
        return max(score, 0.0)

class ContextualAuthorDetector:
    """Detector contextual de autores con análisis morfológico y posicional"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.debug = self.config.get('debug', False)
        
        # Logger (inicializar primero)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar analizadores
        self.morphology_analyzer = HispanicMorphologyAnalyzer()
        self.attribution_analyzer = AttributionContextAnalyzer()
        self.positional_analyzer = PositionalAnalyzer()
        self.cross_validator = CrossValidator()
        
        # Cargar lista blanca de autores conocidos
        self.known_authors = self._load_known_authors()
        self.strict_mode = self.config.get('strict_mode', True)
    
    def detect_author(self, segments: List[Dict[str, Any]], profile_type: str) -> Optional[Dict[str, Any]]:
        """Detecta el autor usando análisis contextual mejorado con contexto de documento"""
        if not segments:
            return None
        
        # Extraer contexto del documento
        doc_context = self._extract_document_context(segments)
        
        # Combinar todo el texto
        full_text = self._combine_segments_text(segments)
        
        if not full_text.strip():
            return None
        
        # Encontrar candidatos en contextos de atribución
        candidates = self._find_attribution_candidates(full_text)
        
        # Analizar y puntuar candidatos
        scored_candidates = self._analyze_candidates(candidates, full_text) if candidates else []
        
        # Seleccionar el mejor candidato del análisis estándar
        standard_best = self._select_best_candidate(scored_candidates) if scored_candidates else None
        
        # Aplicar lógica mejorada con contexto de documento
        return self._apply_enhanced_detection_logic(standard_best, doc_context, full_text)
    
    def _extract_document_context(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrae contexto del documento de los segmentos"""
        context = {
            'document_title': None,
            'source_file_path': None,
            'authors_from_title': [],
            'authors_from_path': []
        }
        
        # Extraer información del primer segmento
        if segments:
            first_segment = segments[0]
            context['document_title'] = first_segment.get('document_title')
            context['source_file_path'] = first_segment.get('source_file_path')
            
            # Extraer autores del título
            if context['document_title']:
                context['authors_from_title'] = self._extract_authors_from_title(context['document_title'])
            
            # Extraer autores del path
            if context['source_file_path']:
                context['authors_from_path'] = self._extract_authors_from_path(context['source_file_path'])
        
        return context
    
    def _apply_enhanced_detection_logic(self, standard_result: Optional[ContextualAuthorCandidate], 
                                      doc_context: Dict[str, Any], full_text: str) -> Optional[Dict[str, Any]]:
        """Aplica lógica mejorada considerando contexto del documento"""
        
        # Obtener autores del contexto del documento
        doc_authors = doc_context['authors_from_title'] + doc_context['authors_from_path']
        known_doc_authors = [author for author in doc_authors if self._is_known_author(author)]
        
        # Si hay autores conocidos en el contexto del documento
        if known_doc_authors:
            # Si no hay detección estándar o es de baja confianza
            if not standard_result or standard_result.confidence < 0.7:
                return {
                    'name': known_doc_authors[0],
                    'confidence': 0.9,
                    'method': 'document_context_override',
                    'details': {
                        'source': 'document_title' if known_doc_authors[0] in doc_context['authors_from_title'] else 'file_path',
                        'original_detection': standard_result.name if standard_result else None,
                        'original_confidence': standard_result.confidence if standard_result else 0.0
                    }
                }
            
            # Si hay detección estándar pero es probable título de sección
            if standard_result and self._is_likely_section_title(standard_result.name, doc_context):
                return {
                    'name': known_doc_authors[0],
                    'confidence': 0.9,
                    'method': 'document_context_override',
                    'details': {
                        'source': 'document_title',
                        'section_title_detected': standard_result.name,
                        'section_title_confidence': standard_result.confidence,
                        'override_reason': 'section_title_filter'
                    }
                }
        
        # Si no hay override, usar resultado estándar
        if standard_result and standard_result.confidence >= self.confidence_threshold:
            return {
                'name': standard_result.name,
                'confidence': standard_result.confidence,
                'method': 'contextual_analysis',
                'details': {
                    'attribution_contexts': standard_result.attribution_contexts,
                    'morphological_score': standard_result.morphological_score,
                    'contextual_score': standard_result.contextual_score,
                    'cross_validation_score': standard_result.cross_validation_score,
                    'positions': standard_result.positions
                }
            }
        
        return None
    
    def _combine_segments_text(self, segments: List[Dict[str, Any]]) -> str:
        """Combina el texto de todos los segmentos"""
        texts = []
        for segment in segments:
            if isinstance(segment, dict) and 'text' in segment:
                texts.append(segment['text'])
            elif isinstance(segment, dict) and 'content' in segment:
                texts.append(segment['content'])
            elif isinstance(segment, str):
                texts.append(segment)
        return ' '.join(texts)
    
    def _find_attribution_candidates(self, text: str) -> List[ContextualAuthorCandidate]:
        """Encuentra candidatos en contextos de atribución"""
        candidates = {}
        
        # Buscar contextos de atribución
        attribution_contexts = self.attribution_analyzer.find_attribution_contexts(text)
        
        for name, context, position in attribution_contexts:
            name = self._clean_name(name)
            if not name or len(name.split()) < 2:
                continue
            
            if name not in candidates:
                candidates[name] = ContextualAuthorCandidate(name=name)
            
            candidates[name].attribution_contexts.append(context)
            candidates[name].positions.append(position)
        
        return list(candidates.values())
    
    def _analyze_candidates(self, candidates: List[ContextualAuthorCandidate], text: str) -> List[ContextualAuthorCandidate]:
        """Analiza y puntúa todos los candidatos"""
        for candidate in candidates:
            # Análisis morfológico
            candidate.morphological_score = self.morphology_analyzer.analyze_name_morphology(candidate.name)
            
            # Análisis contextual
            candidate.contextual_score = self.attribution_analyzer.analyze_contextual_strength(candidate.name, text)
            
            # Validación cruzada
            candidate.cross_validation_score = self.cross_validator.validate_author_candidate(candidate.name, text)
            
            # Análisis posicional
            position_score = self.positional_analyzer.analyze_position_score(candidate.name, text, candidate.positions)
            
            # Calcular confianza final
            candidate.confidence = self._calculate_final_confidence(
                candidate.morphological_score,
                candidate.contextual_score,
                candidate.cross_validation_score,
                position_score,
                len(candidate.attribution_contexts)
            )
        
        return candidates
    
    def _calculate_final_confidence(self, morphological: float, contextual: float, 
                                  cross_validation: float, positional: float, 
                                  attribution_count: int) -> float:
        """Calcula la confianza final del candidato"""
        # Pesos para cada factor
        weights = {
            'morphological': 0.30,
            'contextual': 0.20,
            'cross_validation': 0.30,
            'positional': 0.15,
            'attribution_frequency': 0.05
        }
        
        # Normalizar frecuencia de atribución
        attribution_score = min(attribution_count / 3.0, 1.0)
        
        # Calcular puntuación ponderada
        final_score = (
            morphological * weights['morphological'] +
            contextual * weights['contextual'] +
            cross_validation * weights['cross_validation'] +
            positional * weights['positional'] +
            attribution_score * weights['attribution_frequency']
        )
        
        return min(final_score, 1.0)
    
    def _select_best_candidate(self, candidates: List[ContextualAuthorCandidate]) -> Optional[ContextualAuthorCandidate]:
        """Selecciona el mejor candidato"""
        if not candidates:
            return None
        
        # Ordenar por confianza
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        
        best = candidates[0]
        
        if self.debug:
            self.logger.info(f"Mejor candidato: {best.name} (confianza: {best.confidence:.3f})")
        
        return best
    
    def _clean_name(self, name: str) -> str:
        """Limpia y normaliza un nombre"""
        if not name:
            return ""
        
        # Remover caracteres especiales al inicio y final
        name = re.sub(r'^[^A-Za-záéíóúñÁÉÍÓÚÑ]+|[^A-Za-záéíóúñÁÉÍÓÚÑ]+$', '', name)
        
        # Normalizar espacios
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Capitalizar correctamente
        words = name.split()
        cleaned_words = []
        
        for word in words:
            if word.lower() in {'de', 'del', 'la', 'las', 'los', 'y', 'e'}:
                cleaned_words.append(word.lower())
            else:
                cleaned_words.append(word.capitalize())
        
        return ' '.join(cleaned_words)
    
    def _extract_authors_from_title(self, document_title: str) -> List[str]:
        """Extrae posibles autores del título del documento"""
        if not document_title:
            return []
        
        # Limpiar y normalizar el título
        title_clean = document_title.replace('_', ' ').strip()
        title_parts = title_clean.split()
        
        potential_authors = []
        
        # Patrón: Apellido Nombre al inicio
        if len(title_parts) >= 2:
            for i in range(2, min(5, len(title_parts) + 1)):
                candidate = ' '.join(title_parts[:i])
                if self._is_valid_author_name(candidate):
                    # Normalizar orden del nombre
                    normalized = self._normalize_author_name(candidate)
                    if normalized:
                        potential_authors.append(normalized)
        
        return potential_authors
    
    def _extract_authors_from_path(self, file_path: str) -> List[str]:
        """Extrae posibles autores del path del archivo"""
        if not file_path:
            return []
        
        import os
        filename = os.path.basename(file_path)
        # Remover extensión
        filename_no_ext = os.path.splitext(filename)[0]
        
        return self._extract_authors_from_title(filename_no_ext)
    
    def _normalize_author_name(self, name: str) -> Optional[str]:
        """Normaliza el nombre del autor, manejando diferentes formatos"""
        if not name or not self._is_valid_author_name(name):
            return None
        
        parts = name.strip().split()
        if len(parts) < 2:
            return None
        
        # Si ya está en formato "Nombre Apellido" y es conocido, mantenerlo
        if self._is_known_author(name):
            return name
        
        # Probar formato "Apellido Nombre" -> "Nombre Apellido"
        if len(parts) == 2:
            reversed_name = f"{parts[1]} {parts[0]}"
            if self._is_known_author(reversed_name):
                return reversed_name
        
        # Si ninguno es conocido, mantener el original
        return name
    
    def _is_likely_section_title(self, detected_name: str, doc_context: Dict[str, Any]) -> bool:
        """Determina si el nombre detectado es probablemente un título de sección"""
        if not detected_name:
            return False
        
        # Verificar si aparece en el título del documento
        document_title = doc_context.get('document_title', '')
        if document_title and detected_name.lower() in document_title.lower():
            return True
        
        # Patrones comunes de títulos de sección
        section_patterns = [
            r'\bcanción\b',
            r'\bpoema\b',
            r'\bcapítulo\b',
            r'\bparte\b',
            r'\bsección\b',
            r'\bla\s+\w+\s+desesperada\b',
            r'\bel\s+\w+\s+perdido\b'
        ]
        
        import re
        for pattern in section_patterns:
            if re.search(pattern, detected_name.lower()):
                return True
        
        return False
    
    def _is_valid_author_name(self, name: str) -> bool:
        """Valida si un nombre parece ser un nombre de autor válido"""
        if not name or len(name) < 3:
            return False
        
        # En modo estricto, solo aceptar autores conocidos
        if self.strict_mode:
            is_known = self._is_known_author(name)
            if self.debug and not is_known:
                self.logger.info(f"Nombre '{name}' rechazado: no está en la lista de autores conocidos")
            return is_known
        
        # Modo permisivo: validaciones básicas
        words = name.split()
        if len(words) < 2:
            return False
        
        # Cada palabra debe empezar con mayúscula
        for word in words:
            if not word[0].isupper():
                return False
        
        # No debe contener números
        if any(char.isdigit() for char in name):
            return False
        
        # Verificar que no sea una frase poética común
        poetic_words = {'zumbas', 'vuela', 'canta', 'baila', 'danza', 'susurra', 'murmura', 'grita', 'llora', 'ríe', 'blanca', 'negra', 'dorada', 'plateada'}
        name_lower = name.lower()
        if any(word in name_lower for word in poetic_words):
            if self.debug:
                self.logger.info(f"Nombre '{name}' rechazado: contiene palabras poéticas")
            return False
        
        return True
    
    def _load_known_authors(self) -> Set[str]:
        """Carga la lista blanca de autores conocidos"""
        try:
            # Buscar el archivo de autores conocidos
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(os.path.dirname(current_dir), 'config')
            authors_file = os.path.join(config_dir, 'known_authors.json')
            
            if os.path.exists(authors_file):
                with open(authors_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extraer todos los autores de todas las categorías
                known_authors = set()
                for category in data.get('authors', {}).values():
                    if isinstance(category, list):
                        for author in category:
                            known_authors.add(author.lower())
                            # También agregar variaciones comunes
                            known_authors.add(author.lower().replace(',', ''))
                
                if self.debug:
                    self.logger.info(f"Cargados {len(known_authors)} autores conocidos")
                
                return known_authors
            else:
                if self.debug:
                    self.logger.warning(f"No se encontró archivo de autores conocidos: {authors_file}")
                return set()
                
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error cargando autores conocidos: {e}")
            return set()
    
    def _is_known_author(self, name: str) -> bool:
        """Verifica si un nombre está en la lista de autores conocidos"""
        if not self.known_authors:
            return False
        
        name_lower = name.lower().strip()
        
        # Búsqueda exacta
        if name_lower in self.known_authors:
            return True
        
        # Búsqueda por partes (nombre y apellido por separado)
        name_parts = name_lower.split()
        if len(name_parts) >= 2:
            # Buscar combinaciones comunes
            full_name_variants = [
                ' '.join(name_parts),
                ' '.join(name_parts[:2]),  # Solo primeros dos nombres
                f"{name_parts[-1]}, {' '.join(name_parts[:-1])}",  # Apellido, Nombre
            ]
            
            for variant in full_name_variants:
                if variant in self.known_authors:
                    return True
        
        return False

# Función de conveniencia para usar desde otros módulos
def detect_author_contextual(segments: List[Dict[str, Any]], profile_type: str, 
                           config: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Función de conveniencia para detección contextual de autores"""
    detector = ContextualAuthorDetector(config)
    return detector.detect_author(segments, profile_type)

def get_contextual_detection_config(profile_type: str) -> Dict[str, Any]:
    """Obtiene configuración por defecto para detección contextual"""
    base_config = {
        'confidence_threshold': 0.7,
        'debug': False
    }
    
    # Ajustes específicos por tipo de perfil
    if profile_type == 'verso':
        base_config.update({
            'confidence_threshold': 0.65,  # Más permisivo para poesía
        })
    elif profile_type == 'prosa':
        base_config.update({
            'confidence_threshold': 0.75,  # Más estricto para prosa
        })
    
    return base_config