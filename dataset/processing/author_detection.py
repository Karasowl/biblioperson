#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Contextual de Detección Automática de Autores

Este módulo implementa detección inteligente de autores basada en:

🎯 ANÁLISIS CONTEXTUAL:
   - Patrones de atribución ("Por:", "Autor:", etc.)
   - Análisis posicional (inicio/final vs medio del texto)
   - Validación contextual (autor vs sujeto narrativo)
   - Morfología hispana inteligente
   - Validación cruzada

📊 Ejemplo práctico:
   - Biografía de Einstein: "Einstein" aparece 50 veces en el MEDIO → Score bajo
   - Artículo por García: "García" aparece 3 veces al INICIO/FINAL → Score alto

El sistema distingue entre menciones narrativas y atribuciones autorales reales.

Autor: Sistema de IA
Fecha: 2024
"""

import re
import logging
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from pathlib import Path

# Sistema de detección mejorado con contexto de documento
from .enhanced_contextual_author_detection import EnhancedContextualAuthorDetector, DocumentContext

# Importar nuevas utilidades de detección
try:
    from .author_detection_utils import (
        HeaderFooterFilter,
        PDFMetadataExtractor,
        SpacyNERValidator,
        KnownAuthorsValidator
    )
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Utilidades de detección avanzada no disponibles. Instale dependencias opcionales.")

@dataclass
class AuthorCandidate:
    """Candidato a autor con información de confianza (sistema básico)"""
    name: str
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    positions: List[int] = field(default_factory=list)
    extraction_method: str = ""
    context: List[str] = field(default_factory=list)

logger = logging.getLogger(__name__)

class AutorDetector:
    """
    Detector avanzado de autores para textos de verso y prosa.
    
    Implementa un algoritmo multi-nivel:
    1. Extracción de metadatos estructurados
    2. Análisis de patrones textuales específicos
    3. Análisis de contexto y frecuencia
    4. Scoring y validación final
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar el detector de autores.
        
        Args:
            config: Configuración opcional del detector
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        self.debug_mode = self.config.get('debug', False)
        
        # Configurar logging
        self.logger = logging.getLogger(f"{__name__}.AutorDetector")
        if self.debug_mode:
            self.logger.setLevel(logging.DEBUG)
            
        self.logger.info("🔍 INICIALIZANDO AUTOR DETECTOR V2.0 - ALGORITMO AVANZADO CON UTILIDADES")
        
        # Inicializar utilidades si están disponibles
        self.header_footer_filter = None
        self.pdf_metadata_extractor = None
        self.spacy_validator = None
        self.known_authors_validator = None
        
        if UTILS_AVAILABLE:
            # Header/Footer filter
            if self.config.get('use_header_footer_filter', True):
                threshold = self.config.get('structural_header_threshold', 0.9)
                self.header_footer_filter = HeaderFooterFilter(threshold)
                self.logger.info(f"✅ Filtro de headers/footers activado (umbral: {threshold})")
            
            # PDF metadata extractor
            if self.config.get('use_pdf_metadata', True):
                self.pdf_metadata_extractor = PDFMetadataExtractor()
                self.logger.info("✅ Extractor de metadatos PDF activado")
            
            # SpaCy NER validator
            if self.config.get('use_spacy_ner', True):
                model_name = self.config.get('spacy_model', 'es_core_news_sm')
                self.spacy_validator = SpacyNERValidator(model_name)
                self.logger.info(f"✅ Validador NER spaCy activado (modelo: {model_name})")
            
            # Known authors validator
            if self.config.get('use_known_authors', True):
                authors_file = self.config.get('known_authors_path')
                self.known_authors_validator = KnownAuthorsValidator(authors_file)
                self.logger.info("✅ Validador de autores conocidos activado")
        
        # === NIVEL 1: PATRONES DE METADATOS EXPLÍCITOS ===
        self.metadata_patterns = {
            'explicit_author': [
                r'(?:^|\n)\s*(?:Autor|Author|Por|By|Escrito por|Written by):\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})',
                r'(?:^|\n)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*\(autor\)',
                r'(?:^|\n)\s*©\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})',
            ],
            'byline_patterns': [
                r'(?:^|\n)\s*(?:Por|By)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*(?:\n|$)',
                r'(?:^|\n)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*[-–—]\s*\d{4}',
            ]
        }
        
        # === NIVEL 2A: PATRONES ESPECÍFICOS PARA VERSO (POESÍA) ===
        self.verso_patterns = {
            'signature_end': [
                r'(?:^|\n)\s*—\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*$',
                r'(?:^|\n)\s*[-–—]\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*$',
            ],
            'attribution_verse': [
                r'(?:^|\n)\s*(?:De|Por)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*$',
                r'(?:^|\n)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*\([Aa]utor\)',
            ],
            'poem_title_author': [
                r'(?:Soneto|Canción|Elegía|Oda|Balada|Poema)\s+(?:de\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})',
                r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*\(poem[as]?\)',
            ],
            'isolated_name': [
                r'(?:^|\n)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*(?:\n|$)',
            ]
        }
        
        # === NIVEL 2B: PATRONES ESPECÍFICOS PARA PROSA ===
        self.prosa_patterns = {
            'academic_format': [
                r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*\(\d{4}\)',
                r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+),\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})\s*\(\d{4}\)',
            ],
            'article_header': [
                r'(?:^|\n)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*[-–—]\s*\d{1,2}/\d{1,2}/\d{4}',
                r'(?:^|\n)\s*\*\*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\*\*',
            ],
            'book_author': [
                r'(?:^|\n)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\s*\n.*(?:ISBN|Edición|Editorial)',
                r'Editorial.*\n.*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})',
            ]
        }
        
        # === NIVEL 3: LISTA DE PALABRAS NO VÁLIDAS COMO NOMBRES ===
        self.invalid_names = {
            # Artículos, preposiciones, conjunciones
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'en', 'con', 'por', 'para', 'desde', 'hasta',
            'sobre', 'bajo', 'ante', 'tras', 'durante', 'mediante',
            'y', 'o', 'pero', 'sino', 'aunque', 'porque', 'como', 'cuando',
            # Palabras comunes que no son nombres
            'señor', 'señora', 'don', 'doña', 'casa', 'vida', 'mundo',
            'tiempo', 'hombre', 'mujer', 'día', 'noche', 'amor', 'muerte',
            'dios', 'cristo', 'virgen', 'santo', 'santa', 'san',
            # Meses y días
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
            'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
            # Palabras técnicas
            'página', 'capítulo', 'título', 'índice', 'prólogo', 'epílogo',
            'introducción', 'conclusión', 'anexo', 'apéndice', 'bibliografía'
        }
        
        # === COMPILAR PATRONES REGEX ===
        self._compile_patterns()
        
        self.logger.info(f"✅ Detector configurado - umbral: {self.confidence_threshold}")
    
    def _compile_patterns(self) -> None:
        """Compilar todos los patrones regex para mayor eficiencia"""
        self.compiled_patterns = {}
        
        # Compilar patrones de metadatos
        for category, patterns in self.metadata_patterns.items():
            self.compiled_patterns[category] = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in patterns]
        
        # Compilar patrones de verso
        for category, patterns in self.verso_patterns.items():
            self.compiled_patterns[f"verso_{category}"] = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in patterns]
        
        # Compilar patrones de prosa
        for category, patterns in self.prosa_patterns.items():
            self.compiled_patterns[f"prosa_{category}"] = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in patterns]
    
    def detect_author(self, segments: List[Dict[str, Any]], profile_type: str, 
                     document_title: Optional[str] = None, source_file_path: Optional[str] = None,
                     blocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Detectar autor usando sistema mejorado con contexto de documento y utilidades avanzadas.
        
        Args:
            segments: Lista de segmentos de texto procesados
            profile_type: Tipo de perfil ('verso' o 'prosa')
            document_title: Título del documento (opcional)
            source_file_path: Ruta del archivo fuente (opcional)
            blocks: Bloques originales para análisis de headers/footers (opcional)
            
        Returns:
            Diccionario con información del autor detectado o None
        """
        self.logger.debug(f"Iniciando AutorDetector.detect_author para profile_type: {profile_type}")
        if not segments:
            self.logger.warning("No se proporcionaron segmentos para la detección de autor.")
            return None

        # === PASO 1: EXTRAER METADATOS PDF SI ESTÁ DISPONIBLE ===
        pdf_author = None
        if self.pdf_metadata_extractor and source_file_path:
            pdf_metadata = self.pdf_metadata_extractor.extract_author_metadata(source_file_path)
            if pdf_metadata:
                pdf_author = pdf_metadata
                filename = Path(source_file_path).name if source_file_path else "archivo"
                self.logger.info(f"📄 Autor extraído de metadatos PDF ({filename}): {pdf_metadata['name']}")

        # === PASO 2: ANALIZAR HEADERS/FOOTERS SI HAY BLOQUES ===
        if self.header_footer_filter and blocks:
            self.header_footer_filter.analyze_blocks(blocks)
            self.logger.info(f"📋 Analizados {len(blocks)} bloques para headers/footers")

        self.logger.debug(f"Valor de document_title recibido: {document_title}")
        self.logger.debug(f"Valor de source_file_path recibido: {source_file_path}")

        filename = Path(source_file_path).name if source_file_path else None
        
        # Utilizar el metadata del primer segmento si está disponible
        metadata_for_context = {}
        if segments and isinstance(segments[0], dict):
            segment_metadata = segments[0].get('additional_metadata')
            if isinstance(segment_metadata, dict):
                metadata_for_context = segment_metadata.copy()

        doc_context = DocumentContext(
            title=document_title,
            filename=filename,
            metadata=metadata_for_context
        )
        self.logger.debug(f"DocumentContext creado: title='{doc_context.title}', filename='{doc_context.filename}'")

        # === PASO 3: DETECCIÓN PRINCIPAL CON ENHANCED DETECTOR ===
        current_config = self.config if isinstance(self.config, dict) else {}
        enhanced_config = {
            'confidence_threshold': current_config.get('confidence_threshold', 0.6),
            'debug': current_config.get('debug', False),
            'strict_mode': current_config.get('strict_mode', True)
        }
        
        enhanced_detector = EnhancedContextualAuthorDetector(enhanced_config)
        content_type_for_enhanced = 'poetry' if profile_type == 'verso' else 'prose'

        try:
            result = enhanced_detector.detect_author_enhanced(segments, content_type_for_enhanced, doc_context)
            
            if result and isinstance(result, dict) and result.get('name'):
                # === PASO 4: VALIDAR Y MEJORAR CON UTILIDADES ===
                result = self._enhance_with_utilities(result, segments, pdf_author)
                
                confidence_pct = result.get('confidence', 0) * 100
                self.logger.info(f"✅ Autor detectado por AutorDetector: {result.get('name')} (Confianza: {confidence_pct:.1f}%)")
                if enhanced_detector.debug and result.get('details'):
                    self.logger.debug(f"Detalles de detección: {result.get('details')}")
                return result
            else:
                # Si no hay resultado del detector principal, intentar con metadatos PDF
                if pdf_author:
                    self.logger.info("Usando autor de metadatos PDF como fallback")
                    return self._enhance_with_utilities(pdf_author, segments, pdf_author)
                
                self.logger.warning("No se pudo detectar autor con el detector principal")
                return None
                
        except Exception as e:
            self.logger.error(f"Error durante detección: {e}", exc_info=True)
            # Fallback a metadatos PDF si hay error
            if pdf_author:
                return pdf_author
            return None
    
    def _enhance_with_utilities(self, result: Dict[str, Any], segments: List[Dict[str, Any]], 
                               pdf_author: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Mejorar resultado de detección con utilidades adicionales.
        """
        enhanced_result = result.copy()
        
        # === FILTRAR SI ES TEXTO ESTRUCTURAL ===
        if self.header_footer_filter:
            author_name = enhanced_result.get('name', '')
            if self.header_footer_filter.is_structural_text(author_name):
                self.logger.warning(f"⚠️ Autor '{author_name}' detectado como header/footer estructural")
                enhanced_result['confidence'] *= 0.5
                enhanced_result['is_structural'] = True
        
        # === VALIDAR CON NER ===
        if self.spacy_validator:
            candidates = [enhanced_result]
            validated = self.spacy_validator.validate_author_candidates(candidates, segments)
            if validated:
                enhanced_result = validated[0]
                if enhanced_result.get('ner_validated'):
                    self.logger.info(f"✅ Autor validado por NER: {enhanced_result['name']}")
        
        # === VALIDAR CONTRA AUTORES CONOCIDOS ===
        if self.known_authors_validator:
            candidates = [enhanced_result]
            enhanced = self.known_authors_validator.enhance_candidates(candidates)
            if enhanced:
                enhanced_result = enhanced[0]
                if enhanced_result.get('is_known_author'):
                    self.logger.info(f"✅ Autor conocido confirmado: {enhanced_result['name']} (base de datos de autores hispanos)")
        
        # === COMBINAR CON METADATOS PDF SI COINCIDEN ===
        if pdf_author:
            pdf_name = pdf_author.get('name', '').lower()
            detected_name = enhanced_result.get('name', '').lower()
            
            # Verificar coincidencia (exacta o parcial)
            if pdf_name == detected_name or any(part in detected_name for part in pdf_name.split()):
                enhanced_result['confidence'] = min(enhanced_result.get('confidence', 0.5) * 1.2, 1.0)
                enhanced_result['pdf_metadata_match'] = True
                self.logger.info(f"✅ Coincidencia con metadatos PDF: confianza aumentada")
        
        return enhanced_result
    
    def _detect_author_basic(self, segments: List[Dict[str, Any]], profile_type: str) -> Optional[Dict[str, Any]]:
        """
        Detectar automáticamente el autor usando análisis básico (respaldo).
        
        Args:
            segments: Lista de segmentos de texto procesados
            profile_type: Tipo de perfil ('verso' o 'prosa')
            
        Returns:
            Diccionario con información del autor detectado o None
        """
        # Unir todo el texto para análisis global
        full_text = self._combine_segments_text(segments)
        if not full_text:
            return None
        
        candidates = []
        
        # === NIVEL 1: METADATOS EXPLÍCITOS ===
        metadata_candidates = self._extract_metadata_authors(full_text)
        candidates.extend(metadata_candidates)
        self.logger.debug(f"Nivel 1 - Metadatos: {len(metadata_candidates)} candidatos")
        
        # === NIVEL 2: PATRONES ESPECÍFICOS POR TIPO ===
        if profile_type == 'verso':
            type_candidates = self._detect_verse_authors(full_text, segments)
        elif profile_type == 'prosa':
            type_candidates = self._detect_prose_authors(full_text, segments)
        else:
            type_candidates = []
        
        candidates.extend(type_candidates)
        self.logger.debug(f"Nivel 2 - Patrones específicos: {len(type_candidates)} candidatos")
        
        # === NIVEL 3: SCORING Y VALIDACIÓN ===
        if not candidates:
            self.logger.info("❌ No se encontraron candidatos de autor")
            return None
        
        scored_candidates = self._score_candidates(candidates, segments, full_text)
        
        # === NIVEL 4: SELECCIÓN FINAL ===
        best_author = self._select_best_author(scored_candidates)
        
        if best_author:
            confidence_pct = best_author['confidence'] * 100
            self.logger.info(f"✅ AUTOR DETECTADO (método básico): '{best_author['name']}' (confianza: {confidence_pct:.1f}%)")
            return best_author
        else:
            self.logger.info("❌ No se pudo determinar autor con suficiente confianza")
            return None
    
    def _combine_segments_text(self, segments: List[Dict[str, Any]]) -> str:
        """Combinar el texto de todos los segmentos para análisis global"""
        texts = []
        for segment in segments:
            text = segment.get('text', '') or segment.get('content', '')
            if text:
                texts.append(text.strip())
        return '\n\n'.join(texts)
    
    def _extract_metadata_authors(self, text: str) -> List[AuthorCandidate]:
        """NIVEL 1: Extraer autores de metadatos explícitos"""
        candidates = []
        
        for category, compiled_patterns in self.compiled_patterns.items():
            if not category.startswith(('verso_', 'prosa_')):
                for pattern in compiled_patterns:
                    matches = pattern.finditer(text)
                    for match in matches:
                        name = self._clean_author_name(match.group(1))
                        if self._is_valid_name(name):
                            candidates.append(AuthorCandidate(
                                name=name,
                                confidence=0.0,  # Se calculará después
                                sources=[category],
                                positions=[match.start()],
                                extraction_method='metadata',
                                context=[self._get_context(text, match.start(), match.end())]
                            ))
        
        return candidates
    
    def _detect_verse_authors(self, text: str, segments: List[Dict[str, Any]]) -> List[AuthorCandidate]:
        """NIVEL 2A: Detectar autores específicos en textos de verso"""
        candidates = []
        
        for category, compiled_patterns in self.compiled_patterns.items():
            if category.startswith('verso_'):
                for pattern in compiled_patterns:
                    matches = pattern.finditer(text)
                    for match in matches:
                        name = self._clean_author_name(match.group(1))
                        if self._is_valid_name(name):
                            candidates.append(AuthorCandidate(
                                name=name,
                                confidence=0.0,
                                sources=[category],
                                positions=[match.start()],
                                extraction_method='verse_pattern',
                                context=[self._get_context(text, match.start(), match.end())]
                            ))
        
        return candidates
    
    def _detect_prose_authors(self, text: str, segments: List[Dict[str, Any]]) -> List[AuthorCandidate]:
        """NIVEL 2B: Detectar autores específicos en textos de prosa"""
        candidates = []
        
        for category, compiled_patterns in self.compiled_patterns.items():
            if category.startswith('prosa_'):
                for pattern in compiled_patterns:
                    matches = pattern.finditer(text)
                    for match in matches:
                        # Algunos patrones de prosa pueden capturar múltiples grupos
                        for i in range(1, len(match.groups()) + 1):
                            try:
                                name = self._clean_author_name(match.group(i))
                                if self._is_valid_name(name):
                                    candidates.append(AuthorCandidate(
                                        name=name,
                                        confidence=0.0,
                                        sources=[category],
                                        positions=[match.start()],
                                        extraction_method='prose_pattern',
                                        context=[self._get_context(text, match.start(), match.end())]
                                    ))
                                    break  # Solo tomar el primer nombre válido del match
                            except IndexError:
                                break
        
        return candidates
    
    def _score_candidates(self, candidates: List[AuthorCandidate], 
                         segments: List[Dict[str, Any]], full_text: str) -> List[AuthorCandidate]:
        """NIVEL 3: Calcular score de confianza para cada candidato"""
        
        # Agrupar candidatos por nombre
        name_groups = defaultdict(list)
        for candidate in candidates:
            normalized_name = self._normalize_name(candidate.name)
            name_groups[normalized_name].append(candidate)
        
        scored_candidates = []
        
        for normalized_name, group in name_groups.items():
            # Combinar información de todos los candidatos del mismo nombre
            combined_candidate = self._combine_candidates(group)
            
            # Calcular score
            score = self._calculate_candidate_score(combined_candidate, segments, full_text)
            combined_candidate.confidence = score
            
            self.logger.debug(f"Candidato '{combined_candidate.name}' → Score: {score:.3f}")
            
            scored_candidates.append(combined_candidate)
        
        # Ordenar por score descendente
        scored_candidates.sort(key=lambda c: c.confidence, reverse=True)
        
        return scored_candidates
    
    def _combine_candidates(self, candidates: List[AuthorCandidate]) -> AuthorCandidate:
        """Combinar múltiples candidatos del mismo nombre"""
        if len(candidates) == 1:
            return candidates[0]
        
        # Tomar el nombre más común/completo
        names = [c.name for c in candidates]
        name_counter = Counter(names)
        best_name = name_counter.most_common(1)[0][0]
        
        # Combinar sources, positions y context
        all_sources = []
        all_positions = []
        all_context = []
        extraction_methods = []
        
        for candidate in candidates:
            all_sources.extend(candidate.sources)
            all_positions.extend(candidate.positions)
            all_context.extend(candidate.context)
            extraction_methods.append(candidate.extraction_method)
        
        return AuthorCandidate(
            name=best_name,
            confidence=0.0,  # Se calculará después
            sources=list(set(all_sources)),
            positions=all_positions,
            extraction_method='|'.join(set(extraction_methods)),
            context=all_context
        )
    
    def _calculate_candidate_score(self, candidate: AuthorCandidate, 
                                 segments: List[Dict[str, Any]], full_text: str) -> float:
        """Calcular score de confianza para un candidato"""
        score = 0.0
        
        # === FACTOR 1: MÉTODO DE EXTRACCIÓN (0.0 - 0.4) ===
        if 'metadata' in candidate.extraction_method:
            score += 0.4  # Metadatos explícitos son más confiables
        elif 'verse_pattern' in candidate.extraction_method:
            if any('signature' in source for source in candidate.sources):
                score += 0.35  # Firmas en versos
            elif any('attribution' in source for source in candidate.sources):
                score += 0.3   # Atribuciones
            else:
                score += 0.25  # Otros patrones de verso
        elif 'prose_pattern' in candidate.extraction_method:
            if any('academic' in source for source in candidate.sources):
                score += 0.3   # Formato académico
            elif any('header' in source for source in candidate.sources):
                score += 0.25  # Headers de artículos
            else:
                score += 0.2   # Otros patrones de prosa
        
        # === FACTOR 2: FRECUENCIA DE APARICIÓN (0.0 - 0.3) ===
        frequency = len(candidate.positions)
        if frequency >= 3:
            score += 0.3
        elif frequency == 2:
            score += 0.2
        else:
            score += 0.1
        
        # === FACTOR 3: POSICIÓN EN EL TEXTO (0.0 - 0.2) ===
        text_length = len(full_text)
        for position in candidate.positions:
            relative_position = position / text_length
            if relative_position <= 0.1 or relative_position >= 0.9:  # Inicio o final
                score += 0.2 / len(candidate.positions)  # Distribuir entre posiciones
            elif relative_position <= 0.2 or relative_position >= 0.8:  # Cerca del inicio/final
                score += 0.1 / len(candidate.positions)
        
        # === FACTOR 4: VALIDACIÓN COMO NOMBRE PROPIO (0.0 - 0.1) ===
        if self._is_proper_name_format(candidate.name):
            score += 0.1
        
        # Asegurar que el score esté entre 0 y 1
        return min(score, 1.0)
    
    def _select_best_author(self, scored_candidates: List[AuthorCandidate]) -> Optional[Dict[str, Any]]:
        """NIVEL 4: Seleccionar el mejor candidato basado en el score"""
        if not scored_candidates:
            return None
        
        best_candidate = scored_candidates[0]
        
        if best_candidate.confidence >= self.confidence_threshold:
            return {
                'name': best_candidate.name,
                'confidence': best_candidate.confidence,
                'extraction_method': best_candidate.extraction_method,
                'sources': best_candidate.sources,
                'frequency': len(best_candidate.positions),
                'positions': best_candidate.positions,
                'detection_details': {
                    'total_candidates': len(scored_candidates),
                    'threshold_used': self.confidence_threshold,
                    'context_samples': best_candidate.context[:3]  # Primeros 3 contextos
                }
            }
        
        return None
    
    def _clean_author_name(self, name: str) -> str:
        """Limpiar y normalizar nombre de autor"""
        if not name:
            return ""
        
        # Eliminar espacios extra y normalizar
        cleaned = re.sub(r'\s+', ' ', name.strip())
        
        # Eliminar caracteres especiales al inicio/final
        cleaned = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', cleaned)
        
        # Capitalizar correctamente
        words = cleaned.split()
        capitalized_words = []
        for word in words:
            if len(word) > 1:
                capitalized_words.append(word.capitalize())
            else:
                capitalized_words.append(word.upper())
        
        return ' '.join(capitalized_words)
    
    def _is_valid_name(self, name: str) -> bool:
        """Validar si una cadena es un nombre válido"""
        if not name or len(name) < 3:
            return False
        
        # Normalizar para comparación
        normalized = self._normalize_name(name)
        words = normalized.lower().split()
        
        # Rechazar si contiene palabras inválidas
        for word in words:
            if word in self.invalid_names:
                return False
        
        # Debe tener al menos una palabra que parezca nombre
        if len(words) < 2:
            return False
        
        # Verificar formato básico de nombre
        if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+$', name):
            return False
        
        return True
    
    def _is_proper_name_format(self, name: str) -> bool:
        """Verificar si tiene formato de nombre propio"""
        words = name.split()
        
        # Al menos 2 palabras
        if len(words) < 2:
            return False
        
        # Todas las palabras deben estar capitalizadas
        for word in words:
            if not word[0].isupper():
                return False
        
        # No más de 4 palabras (nombres muy largos son sospechosos)
        if len(words) > 4:
            return False
        
        return True
    
    def _normalize_name(self, name: str) -> str:
        """Normalizar nombre para comparación"""
        # Remover acentos
        normalized = unicodedata.normalize('NFD', name)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # Convertir a minúsculas para comparación
        return normalized.lower().strip()
    
    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Obtener contexto alrededor de una coincidencia"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        context = text[context_start:context_end]
        
        # Agregar indicadores si se truncó
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        return context.replace('\n', ' ').strip()

# === FUNCIONES DE UTILIDAD PARA INTEGRACIÓN ===

def detect_author_in_segments(segments: List[Dict[str, Any]], 
                            profile_type: str,
                            config: Optional[Dict[str, Any]] = None,
                            document_title: Optional[str] = None,
                            source_file_path: Optional[str] = None,
                            blocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    Función de conveniencia para detectar autor en segmentos.
    
    Args:
        segments: Lista de segmentos procesados
        profile_type: Tipo de perfil ('verso' o 'prosa')
        config: Configuración opcional del detector
        document_title: Título del documento (opcional)
        source_file_path: Ruta del archivo fuente (opcional)
        blocks: Bloques originales para análisis de headers/footers (opcional)
        
    Returns:
        Información del autor detectado o None
    """
    # Usar detector híbrido si está disponible y habilitado
    use_hybrid = config.get('use_hybrid_detection', True) if config else True
    
    if use_hybrid:
        try:
            from .hybrid_author_detection import HybridAuthorDetector
            hybrid_detector = HybridAuthorDetector(config)
            result = hybrid_detector.detect_author(segments, profile_type)
            if result:
                return result
        except ImportError:
            # Si no está disponible el detector híbrido, usar el mejorado
            pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error en detector híbrido, usando detector estándar: {e}")
    
    # Usar el detector principal con todas las utilidades
    detector = AutorDetector(config)
    return detector.detect_author(segments, profile_type, document_title, source_file_path, blocks)

def get_author_detection_config(profile_type: str) -> Dict[str, Any]:
    """
    Obtener configuración por defecto para detección de autores.
    
    Args:
        profile_type: Tipo de perfil ('verso' o 'prosa')
        
    Returns:
        Configuración recomendada
    """
    base_config = {
        'confidence_threshold': 0.7,
        'debug': False
    }
    
    if profile_type == 'verso':
        base_config.update({
            'confidence_threshold': 0.6,  # Más permisivo para poesía pero aún estricto
        })
    elif profile_type == 'prosa':
        base_config.update({
            'confidence_threshold': 0.85,  # Muy estricto para prosa
        })
    
    return base_config