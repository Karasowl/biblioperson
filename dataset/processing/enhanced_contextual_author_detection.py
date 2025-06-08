#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from contextual_author_detection import ContextualAuthorDetector, ContextualAuthorCandidate

@dataclass
class DocumentContext:
    """Contexto del documento para mejorar la detección de autores"""
    title: Optional[str] = None
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EnhancedContextualAuthorDetector(ContextualAuthorDetector):
    """Detector de autores mejorado que considera el contexto del documento"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.document_title_patterns = [
            # Patrón para "Apellido Nombre_Título"
            r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)_',
            # Patrón para "Nombre Apellido - Título"
            r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*[-–—]',
            # Patrón para "Título - Nombre Apellido"
            r'[-–—]\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*$',
            # Patrón para "Nombre Apellido (año)"
            r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*\(',
        ]
        
        # Patrones para evitar falsos positivos en títulos
        self.title_exclusion_patterns = [
            r'\b(?:poemas?|canciones?|obras?|libros?|textos?)\b',
            r'\b(?:desesperada?|hermosa?|bella?)\b',
            r'\b(?:amor|vida|muerte|tiempo)\b'
        ]
    
    def extract_author_from_document_context(self, document_context: DocumentContext) -> Optional[str]:
        """Extrae el autor del contexto del documento (título, nombre de archivo, etc.)"""
        candidates = []
        
        # Extraer de título del documento
        if document_context.title:
            title_candidates = self._extract_from_title(document_context.title)
            candidates.extend(title_candidates)
        
        # Extraer de nombre de archivo
        if document_context.filename:
            filename_candidates = self._extract_from_title(document_context.filename)
            candidates.extend(filename_candidates)
        
        # Filtrar y validar candidatos
        valid_candidates = []
        for candidate in candidates:
            if self._is_valid_author_name(candidate):
                valid_candidates.append(candidate)
        
        # Retornar el candidato más probable
        if valid_candidates:
            return self._select_best_title_candidate(valid_candidates)
        
        return None
    
    def _extract_from_title(self, title: str) -> List[str]:
        """Extrae nombres de autores del título"""
        candidates = []
        
        for pattern in self.document_title_patterns:
            matches = re.finditer(pattern, title, re.IGNORECASE)
            for match in matches:
                candidate = match.group(1).strip()
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    def _is_valid_author_name(self, name: str) -> bool:
        """Valida si un nombre es un posible autor"""
        if not name or len(name.split()) < 2:
            return False
        
        # Verificar patrones de exclusión
        for pattern in self.title_exclusion_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # Verificar que tenga formato de nombre (primera letra mayúscula)
        words = name.split()
        for word in words:
            if not word[0].isupper():
                return False
        
        return True
    
    def _select_best_title_candidate(self, candidates: List[str]) -> str:
        """Selecciona el mejor candidato de título"""
        # Normalizar nombres (convertir "Apellido Nombre" a "Nombre Apellido")
        normalized_candidates = []
        
        for candidate in candidates:
            # Intentar diferentes variaciones del nombre
            words = candidate.split()
            if len(words) == 2:
                # Probar tanto "Nombre Apellido" como "Apellido Nombre"
                normal_order = f"{words[0]} {words[1]}"
                reversed_order = f"{words[1]} {words[0]}"
                
                # Verificar cuál es más probable que sea un autor conocido
                if self._is_known_author(normal_order):
                    normalized_candidates.append(normal_order)
                elif self._is_known_author(reversed_order):
                    normalized_candidates.append(reversed_order)
                else:
                    # Si ninguno es conocido, preferir el orden normal
                    normalized_candidates.append(normal_order)
            else:
                normalized_candidates.append(candidate)
        
        # Retornar el primer candidato normalizado
        return normalized_candidates[0] if normalized_candidates else candidates[0]
    
    def detect_author_enhanced(self, segments: List[Dict[str, Any]], content_type: str = 'poetry', 
                             document_context: Optional[DocumentContext] = None) -> Optional[Dict[str, Any]]:
        """Detección de autor mejorada que considera el contexto del documento"""
        
        # Primero extraer autor del contexto del documento
        document_author = None
        if document_context:
            document_author = self.extract_author_from_document_context(document_context)
        
        # Intentar detección estándar
        standard_result = self.detect_author(segments, content_type)
        
        # Lógica de decisión mejorada
        if document_author and self._is_known_author(document_author):
            # Si tenemos un autor conocido del documento, darle alta prioridad
            if not standard_result:
                # No hay detección estándar, usar el del documento
                return {
                    'name': document_author,
                    'confidence': 0.85,
                    'method': 'document_context',
                    'details': {
                        'source': 'document_title',
                        'original_title': document_context.title or document_context.filename,
                        'standard_detection': None
                    }
                }
            elif standard_result['name'].lower() != document_author.lower():
                # Hay conflicto entre detección estándar y documento
                # Verificar si la detección estándar es un título de sección
                if self._is_likely_section_title(standard_result['name'], document_context):
                    # La detección estándar parece ser un título de sección, usar el del documento
                    return {
                        'name': document_author,
                        'confidence': 0.90,
                        'method': 'document_context_override',
                        'details': {
                            'source': 'document_title',
                            'original_title': document_context.title or document_context.filename,
                            'overridden_detection': standard_result['name'],
                            'reason': 'section_title_detected'
                        }
                    }
                else:
                    # Ambos parecen válidos, preferir el del documento si es conocido
                    return {
                        'name': document_author,
                        'confidence': 0.80,
                        'method': 'document_context_preferred',
                        'details': {
                            'source': 'document_title',
                            'original_title': document_context.title or document_context.filename,
                            'alternative_detection': standard_result['name']
                        }
                    }
            # Si los nombres coinciden, usar la detección estándar con sus detalles
        
        # Si no hay autor del documento o no es conocido, usar detección estándar
        if standard_result:
            return standard_result
        
        # Como último recurso, usar el autor del documento aunque no sea conocido
        if document_author:
            return {
                'name': document_author,
                'confidence': 0.65,
                'method': 'document_context_fallback',
                'details': {
                    'source': 'document_title',
                    'original_title': document_context.title or document_context.filename,
                    'is_known_author': False
                }
            }
        
        return None
    
    def _filter_section_titles(self, candidates: List[ContextualAuthorCandidate], 
                              document_context: Optional[DocumentContext] = None) -> List[ContextualAuthorCandidate]:
        """Filtra títulos de secciones que no son autores"""
        if not document_context or not document_context.title:
            return candidates
        
        filtered = []
        document_title_lower = document_context.title.lower()
        
        for candidate in candidates:
            candidate_lower = candidate.name.lower()
            
            # Si el candidato aparece en el título del documento como parte del título de la obra
            # (no como autor), es probable que sea un título de sección
            if candidate_lower in document_title_lower:
                # Verificar si aparece después del nombre del autor en el título
                title_parts = document_title_lower.split('_')
                if len(title_parts) > 1 and candidate_lower in title_parts[1]:
                    # Es parte del título de la obra, no del autor
                    continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _is_likely_section_title(self, name: str, document_context: Optional[DocumentContext] = None) -> bool:
        """Determina si un nombre es probablemente un título de sección y no un autor"""
        if not document_context or not document_context.title:
            return False
        
        name_lower = name.lower()
        title_lower = document_context.title.lower()
        
        # Si el nombre aparece en el título del documento después del autor
        if '_' in title_lower:
            title_parts = title_lower.split('_', 1)
            if len(title_parts) > 1 and name_lower in title_parts[1]:
                return True
        
        # Patrones comunes de títulos de secciones
        section_patterns = [
            r'\b(?:canción|poema|verso|estrofa|canto)\b',
            r'\b(?:desesperada?|hermosa?|bella?|triste)\b',
            r'\b(?:primera?|segunda?|tercera?|última?)\b'
        ]
        
        for pattern in section_patterns:
            if re.search(pattern, name_lower):
                return True
        
        return False

def test_enhanced_detection():
    """Función de prueba para el detector mejorado"""
    print("=== PRUEBA DEL DETECTOR MEJORADO ===\n")
    
    # Crear detector mejorado
    detector = EnhancedContextualAuthorDetector(config={'debug': True, 'strict_mode': False})
    
    # Caso problemático original
    poem_text = """Poema 1
Cuerpo de mujer, blancas colinas, muslos blancos,
te pareces al mundo en tu actitud de entrega.
Mi cuerpo de labriego salvaje te socava
y hace saltar el hijo del fondo de la tierra.
Fui solo como un túnel. De mí huían los pájaros
y en mí la noche entraba su invasión poderosa.
Para sobrevivirme te forjé como un arma,
como una flecha en mi arco, como una piedra en mi honda.
Pero cae la hora de la venganza, te amo.
Cuerpo de piel, de musgo, de leche ávida firme.
Ah los vasos del pecho! Ah los ojos de ausencia!
Ah las rosas del pubis! Ah tu voz lenta triste!
Cuerpo de mujer mía, persistirá en tu gracia.
Mi sed, mi ansia sin limite, mi camino indeciso!
Oscuros cauces donde la sed eterna sigue,
y la fatiga sigue, el dolor infinito.

[... otros poemas ...]

La Canción Desesperada

Emerge tu recuerdo de la noche en que estoy..."""
    
    # Contexto del documento
    doc_context = DocumentContext(
        title="Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada",
        filename="Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    )
    
    segments = [{'text': poem_text, 'type': 'content'}]
    
    print("1. Detección estándar:")
    standard_result = detector.detect_author(segments, 'poetry')
    if standard_result:
        print(f"   ✅ {standard_result['name']} (confianza: {standard_result['confidence']:.3f})")
    else:
        print(f"   ❌ No detectado")
    
    print("\n2. Extracción del contexto del documento:")
    doc_author = detector.extract_author_from_document_context(doc_context)
    if doc_author:
        print(f"   ✅ Extraído del título: {doc_author}")
        is_known = detector._is_known_author(doc_author)
        print(f"   ¿Autor conocido?: {is_known}")
    else:
        print(f"   ❌ No extraído")
    
    print("\n3. Detección mejorada:")
    enhanced_result = detector.detect_author_enhanced(segments, 'poetry', doc_context)
    if enhanced_result:
        print(f"   ✅ {enhanced_result['name']} (confianza: {enhanced_result['confidence']:.3f})")
        print(f"   Método: {enhanced_result['method']}")
        if 'details' in enhanced_result:
            print(f"   Detalles: {enhanced_result['details']}")
    else:
        print(f"   ❌ No detectado")

if __name__ == "__main__":
    test_enhanced_detection()