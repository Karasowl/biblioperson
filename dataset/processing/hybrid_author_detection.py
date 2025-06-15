# -*- coding: utf-8 -*-
"""
Detector híbrido de autores que combina múltiples enfoques:
1. Análisis contextual existente
2. Análisis estilométrico
3. Base de datos de autores literarios
4. Análisis de contexto de documento
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Importar detectores existentes
from contextual_author_detection import ContextualAuthorDetector
from enhanced_contextual_author_detection import EnhancedContextualAuthorDetector
from stylometric_author_detection import StylometricAuthorDetector

@dataclass
class AuthorDetectionResult:
    """Resultado de detección de autor"""
    name: str
    confidence: float
    method: str
    details: Dict[str, Any]
    secondary_candidates: List[Dict[str, Any]] = None

class HybridAuthorDetector:
    """Detector híbrido que combina múltiples enfoques de detección de autores"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.debug = self.config.get('debug', False)
        
        # Inicializar detectores
        self.contextual_detector = ContextualAuthorDetector(config)
        self.enhanced_detector = EnhancedContextualAuthorDetector(config)
        self.stylometric_detector = StylometricAuthorDetector(config)
        
        # Pesos para cada método
        self.method_weights = {
            'literary_database_match': 1.0,
            'document_context_override': 0.95,
            'stylistic_markers_match': 0.9,
            'contextual_analysis': 0.8,
            'document_context': 0.85,
            'stylistic_analysis': 0.7,
            'enhanced_contextual': 0.75
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
    def detect_author(self, segments: List[Dict[str, Any]], profile_type: str) -> Optional[Dict[str, Any]]:
        """Detecta el autor usando enfoque híbrido"""
        if not segments:
            return None
        
        candidates = []
        
        # 1. Análisis estilométrico (prioridad alta para autores literarios)
        try:
            stylometric_result = self.stylometric_detector.detect_author(segments, profile_type)
            if stylometric_result:
                candidates.append(self._normalize_result(stylometric_result, 'stylometric'))
                
                # Si es una coincidencia de base de datos literaria con alta confianza, usar directamente
                if (stylometric_result.get('method') == 'literary_database_match' and 
                    stylometric_result.get('confidence', 0) > 0.8):
                    return stylometric_result
                    
        except Exception as e:
            if self.debug:
                self.logger.warning(f"Error en análisis estilométrico: {e}")
        
        # 2. Detector contextual mejorado
        try:
            enhanced_result = self.enhanced_detector.detect_author(segments, profile_type)
            if enhanced_result:
                candidates.append(self._normalize_result(enhanced_result, 'enhanced_contextual'))
        except Exception as e:
            if self.debug:
                self.logger.warning(f"Error en detector mejorado: {e}")
        
        # 3. Detector contextual básico
        try:
            contextual_result = self.contextual_detector.detect_author(segments, profile_type)
            if contextual_result:
                candidates.append(self._normalize_result(contextual_result, 'contextual'))
        except Exception as e:
            if self.debug:
                self.logger.warning(f"Error en detector contextual: {e}")
        
        # Seleccionar el mejor candidato
        if candidates:
            best_candidate = self._select_best_candidate(candidates)
            
            # Aplicar lógica de validación final
            validated_result = self._validate_final_result(best_candidate, segments)
            
            if validated_result and validated_result.confidence >= self.confidence_threshold:
                return {
                    'name': validated_result.name,
                    'confidence': validated_result.confidence,
                    'method': validated_result.method,
                    'details': validated_result.details
                }
        
        return None
    
    def _normalize_result(self, result: Dict[str, Any], detector_type: str) -> AuthorDetectionResult:
        """Normaliza resultado de detector a formato estándar"""
        return AuthorDetectionResult(
            name=result.get('name', ''),
            confidence=result.get('confidence', 0.0),
            method=result.get('method', detector_type),
            details=result.get('details', {})
        )
    
    def _select_best_candidate(self, candidates: List[AuthorDetectionResult]) -> Optional[AuthorDetectionResult]:
        """Selecciona el mejor candidato basado en confianza ponderada"""
        if not candidates:
            return None
        
        # Calcular puntuación ponderada para cada candidato
        scored_candidates = []
        
        for candidate in candidates:
            weight = self.method_weights.get(candidate.method, 0.5)
            weighted_score = candidate.confidence * weight
            
            scored_candidates.append({
                'candidate': candidate,
                'weighted_score': weighted_score,
                'original_confidence': candidate.confidence
            })
        
        # Ordenar por puntuación ponderada
        scored_candidates.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        best = scored_candidates[0]
        
        # Verificar si hay consenso entre múltiples detectores
        consensus_bonus = self._calculate_consensus_bonus(candidates, best['candidate'].name)
        
        # Ajustar confianza final
        final_confidence = min(1.0, best['original_confidence'] + consensus_bonus)
        
        result = best['candidate']
        result.confidence = final_confidence
        result.details['weighted_score'] = best['weighted_score']
        result.details['consensus_bonus'] = consensus_bonus
        result.details['all_candidates'] = [{
            'name': c.name,
            'confidence': c.confidence,
            'method': c.method
        } for c in candidates]
        
        return result
    
    def _calculate_consensus_bonus(self, candidates: List[AuthorDetectionResult], best_name: str) -> float:
        """Calcula bonus por consenso entre detectores"""
        if len(candidates) <= 1:
            return 0.0
        
        # Contar cuántos detectores coinciden con el mejor candidato
        matching_count = sum(1 for c in candidates if self._names_match(c.name, best_name))
        
        if matching_count > 1:
            # Bonus proporcional al número de detectores que coinciden
            return min(0.2, (matching_count - 1) * 0.1)
        
        return 0.0
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Verifica si dos nombres se refieren al mismo autor"""
        if not name1 or not name2:
            return False
        
        name1_lower = name1.lower().strip()
        name2_lower = name2.lower().strip()
        
        # Coincidencia exacta
        if name1_lower == name2_lower:
            return True
        
        # Coincidencia de palabras principales
        words1 = set(name1_lower.split())
        words2 = set(name2_lower.split())
        
        # Si al menos 2 palabras coinciden, considerar como el mismo autor
        common_words = words1 & words2
        if len(common_words) >= 2:
            return True
        
        # Verificar si uno es subconjunto del otro
        if words1.issubset(words2) or words2.issubset(words1):
            return True
        
        return False
    
    def _validate_final_result(self, result: AuthorDetectionResult, segments: List[Dict[str, Any]]) -> Optional[AuthorDetectionResult]:
        """Validación final del resultado"""
        if not result:
            return None
        
        # Validaciones específicas para casos problemáticos
        
        # 1. Verificar que no sea un título de sección o frase poética
        if self._is_likely_section_title_or_phrase(result.name):
            # Reducir confianza significativamente
            result.confidence *= 0.3
            result.details['validation_warning'] = 'possible_section_title_or_phrase'
        
        # 2. Verificar contexto del documento para casos como "Rubén Darío"
        doc_context = self._extract_document_context(segments)
        if doc_context and self._has_strong_document_context(result.name, doc_context):
            # Aumentar confianza si hay fuerte contexto de documento
            result.confidence = min(1.0, result.confidence + 0.1)
            result.details['document_context_boost'] = True
        
        # 3. Verificar que la confianza final sea razonable
        if result.confidence < 0.2:
            return None
        
        return result
    
    def _is_likely_section_title_or_phrase(self, name: str) -> bool:
        """Verifica si el nombre es probablemente un título de sección o frase poética"""
        name_lower = name.lower()
        
        # Frases poéticas comunes que no son autores
        poetic_phrases = [
            'de tantos poetas', 'en primavera', 'divino tesoro', 'para no volver',
            'sin querer', 'de otoño', 'canción de', 'juventud divino'
        ]
        
        for phrase in poetic_phrases:
            if phrase in name_lower:
                return True
        
        # Verificar si contiene palabras que indican que no es un nombre
        non_name_words = ['de', 'en', 'para', 'sin', 'con', 'por', 'tantos', 'muchos']
        name_words = name_lower.split()
        
        if len(name_words) > 2 and any(word in non_name_words for word in name_words):
            return True
        
        return False
    
    def _extract_document_context(self, segments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extrae contexto del documento"""
        if not segments:
            return None
        
        first_segment = segments[0]
        return {
            'document_title': first_segment.get('document_title'),
            'source_file_path': first_segment.get('source_file_path'),
            'filename': first_segment.get('source_file_path', '').split('\\')[-1] if first_segment.get('source_file_path') else None
        }
    
    def _has_strong_document_context(self, author_name: str, doc_context: Dict[str, Any]) -> bool:
        """Verifica si hay fuerte contexto de documento que apoye al autor"""
        author_lower = author_name.lower()
        
        # Verificar en título del documento
        title = doc_context.get('document_title', '').lower()
        if title and any(word in title for word in author_lower.split()):
            return True
        
        # Verificar en nombre de archivo
        filename = doc_context.get('filename', '').lower()
        if filename and any(word in filename for word in author_lower.split()):
            return True
        
        return False

# Función de conveniencia para usar el detector híbrido
def detect_author_hybrid(segments: List[Dict[str, Any]], profile_type: str = 'poetry', 
                        config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Función de conveniencia para detección híbrida de autores"""
    detector = HybridAuthorDetector(config)
    return detector.detect_author(segments, profile_type)