#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Avanzado de Detección Automática de Perfiles

Este módulo implementa detección inteligente de perfiles de procesamiento basada en:

🎯 ANÁLISIS CONSERVADOR:
   - JSON: Detección por extensión (fácil)
   - PROSA: Por defecto para todo contenido
   - VERSO: Solo cuando >80% del texto cumple criterios estructurales puros
   
📊 CRITERIOS ESTRUCTURALES PARA VERSO:
   - Mayoría de líneas <180 caracteres
   - Alta densidad de saltos de línea
   - >60% de bloques cortos (<100 caracteres)
   - NO usa rimas, métrica, vocabulario poético (débiles para poesía contemporánea)

🔧 EXTENSIBLE:
   - Sistema de plugins para nuevos perfiles
   - Configuración en YAML para umbrales
   - Métricas de confianza para auditabilidad

Autor: Sistema IA Biblioperson
Fecha: 2024
"""

import re
import logging
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter, defaultdict

@dataclass
class ProfileCandidate:
    """Candidato a perfil con información de confianza"""
    profile_name: str
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    structural_metrics: Dict[str, float] = field(default_factory=dict)
    content_sample: str = ""

@dataclass 
class TextStructuralAnalysis:
    """Análisis estructural del texto"""
    total_lines: int = 0
    non_empty_lines: int = 0
    short_lines_count: int = 0  # <180 chars
    very_short_lines_count: int = 0  # <100 chars
    empty_lines_count: int = 0
    average_line_length: float = 0.0
    line_breaks_density: float = 0.0
    short_blocks_ratio: float = 0.0
    consecutive_short_lines_groups: int = 0

class ProfileDetector:
    """
    Detector avanzado de perfiles para archivos de procesamiento.
    
    Implementa un algoritmo conservador que:
    1. Detecta JSON por extensión
    2. Analiza contenido estructural para VERSO vs PROSA
    3. Usa PROSA como perfil por defecto (conservador)
    4. Solo asigna VERSO cuando >80% cumple criterios estructurales
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar el detector de perfiles.
        
        Args:
            config: Configuración opcional del detector
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.8)
        self.debug_mode = self.config.get('debug', False)
        
        # Configurar logging
        self.logger = logging.getLogger(f"{__name__}.ProfileDetector")
        if self.debug_mode:
            self.logger.setLevel(logging.DEBUG)
            
        self.logger.info("🔍 INICIALIZANDO PROFILE DETECTOR V1.0 - ALGORITMO CONSERVADOR")
        
        # === CONFIGURACIÓN DE UMBRALES CONSERVADORES ===
        # Estos valores están diseñados para ser conservadores según las reglas de memoria
        self.thresholds = {
            # Líneas cortas para verso
            'short_line_threshold': self.config.get('short_line_threshold', 180),
            'very_short_line_threshold': self.config.get('very_short_line_threshold', 100),
            
            # Ratios para clasificar como verso (conservadores: >80%)
            'verso_short_lines_ratio': self.config.get('verso_short_lines_ratio', 0.8),
            'verso_short_blocks_ratio': self.config.get('verso_short_blocks_ratio', 0.6),
            'verso_confidence_threshold': self.config.get('verso_confidence_threshold', 0.8),
            
            # Parámetros de análisis
            'min_lines_for_analysis': self.config.get('min_lines_for_analysis', 5),
            'max_sample_lines': self.config.get('max_sample_lines', 100),
        }
        
        # === EXTENSIONES POR PERFIL ===
        self.profile_extensions = {
            'json': {'.json', '.ndjson', '.jsonl'},
            'verso': {'.txt', '.md', '.docx', '.pdf', '.rtf'},
            'prosa': {'.txt', '.md', '.docx', '.pdf', '.rtf', '.doc', '.odt'}
        }
        
        # === PALABRAS CLAVE EN NOMBRES DE ARCHIVO ===
        self.filename_keywords = {
            'verso': {
                'poema', 'poemas', 'poesía', 'poesías', 'versos', 'verso', 'estrofa', 'estrofas',
                'poeta', 'poem', 'poems', 'poetry', 'verse', 'verses', 'stanza', 'lyric', 'lyrics',
                'canción', 'canciones', 'song', 'songs', 'soneto', 'sonetos', 'sonnet', 'sonnets'
            },
            'prosa': {
                'libro', 'libros', 'capítulo', 'capítulos', 'book', 'books', 'chapter', 'chapters',
                'novela', 'novelas', 'novel', 'novels', 'ensayo', 'ensayos', 'essay', 'essays',
                'artículo', 'artículos', 'article', 'articles', 'documento', 'documentos',
                'texto', 'textos', 'text', 'texts', 'escrito', 'escritos', 'writing', 'writings',
                'manual', 'manuales', 'manual', 'manuals', 'guía', 'guías', 'guide', 'guides'
            }
        }
        
        self.logger.info(f"✅ Detector configurado - umbral verso: {self.thresholds['verso_confidence_threshold']}")
    
    def detect_profile(self, file_path: str, content_sample: Optional[str] = None) -> ProfileCandidate:
        """
        Detectar automáticamente el perfil más adecuado para un archivo.
        
        Args:
            file_path: Ruta al archivo
            content_sample: Muestra del contenido (opcional, se leerá si no se proporciona)
            
        Returns:
            ProfileCandidate con el perfil recomendado y métricas de confianza
        """
        file_path = Path(file_path)
        self.logger.info(f"🔍 Detectando perfil para: {file_path.name}")
        
        # === PASO 1: DETECCIÓN POR EXTENSIÓN (JSON) ===
        extension = file_path.suffix.lower()
        if extension in self.profile_extensions['json']:
            self.logger.info(f"✅ JSON detectado por extensión: {extension}")
            return ProfileCandidate(
                profile_name='json',
                confidence=1.0,
                reasons=[f'Extensión JSON detectada: {extension}'],
                structural_metrics={'extension_match': True}
            )
        
        # === PASO 2: ANÁLISIS DE NOMBRE DE ARCHIVO ===
        filename_hint = self._analyze_filename(file_path)
        
        # === PASO 3: ANÁLISIS ESTRUCTURAL DEL CONTENIDO ===
        if content_sample is None:
            content_sample = self._read_content_sample(file_path)
        
        if not content_sample or not content_sample.strip():
            self.logger.warning(f"⚠️ No se pudo leer contenido de: {file_path.name}")
            # Fallback basado en nombre de archivo
            if filename_hint:
                return ProfileCandidate(
                    profile_name=filename_hint,
                    confidence=0.5,
                    reasons=[f'Basado en nombre de archivo (contenido no disponible)'],
                    structural_metrics={'filename_based': True}
                )
            return ProfileCandidate(
                profile_name='prosa',  # Default conservador
                confidence=0.3,
                reasons=['Fallback conservador a prosa (contenido no disponible)'],
                structural_metrics={'fallback': True}
            )
        
        # Análisis estructural detallado
        analysis = self._analyze_text_structure(content_sample)
        profile_candidate = self._classify_based_on_structure(analysis, filename_hint)
        
        self.logger.info(f"📊 Perfil detectado: {profile_candidate.profile_name} "
                        f"(confianza: {profile_candidate.confidence:.2f})")
        
        return profile_candidate
    
    def _analyze_filename(self, file_path: Path) -> Optional[str]:
        """Analizar el nombre del archivo en busca de pistas del tipo de contenido"""
        filename_lower = file_path.stem.lower()
        
        # Buscar palabras clave de verso
        for keyword in self.filename_keywords['verso']:
            if keyword in filename_lower:
                self.logger.debug(f"🏷️ Palabra clave de verso encontrada: {keyword}")
                return 'verso'
        
        # Buscar palabras clave de prosa
        for keyword in self.filename_keywords['prosa']:
            if keyword in filename_lower:
                self.logger.debug(f"🏷️ Palabra clave de prosa encontrada: {keyword}")
                return 'prosa'
        
        return None
    
    def _read_content_sample(self, file_path: Path) -> str:
        """Leer una muestra del contenido del archivo para análisis"""
        try:
            # Intentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        # Leer solo las primeras líneas para análisis estructural
                        lines = []
                        for i, line in enumerate(f):
                            if i >= self.thresholds['max_sample_lines']:
                                break
                            lines.append(line.rstrip())
                        content = '\n'.join(lines)
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                self.logger.warning(f"⚠️ No se pudo decodificar: {file_path.name}")
                return ""
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ Error leyendo {file_path.name}: {str(e)}")
            return ""
    
    def _analyze_text_structure(self, content: str) -> TextStructuralAnalysis:
        """
        Realizar análisis estructural detallado del texto.
        
        Implementa los criterios conservadores según ALGORITMOS_PROPUESTOS.md:
        - Mayoría de líneas <180 caracteres
        - Alta densidad de saltos de línea
        - >60% de bloques cortos (<100 caracteres)
        """
        # === PRE-PROCESADO AVANZADO ===
        # Muchos PDFs insertan retornos de carro "duros" cada ~70-80 caracteres.
        # Eso fragmenta artificialmente los párrafos y hace que el detector crea
        # que hay multitud de "líneas cortas" (falso positivo de verso).
        # 
        # Estrategia:  
        # 1. Consideramos que un salto de línea simple (\n) que **NO** está
        #    separado por una línea en blanco forma parte del mismo párrafo.  
        # 2. Fusionamos todas las líneas consecutivas no vacías en un único
        #    bloque, insertando un espacio para conservar las palabras.  
        # 3. Mantenemos los saltos de párrafo reales (una o más líneas vacías)
        #    porque sí aportan información estructural útil.
        processed_lines: List[str] = []
        paragraph_buffer: List[str] = []

        for raw_line in content.split('\n'):
            stripped = raw_line.rstrip()
            if stripped:
                # Línea con texto ⇒ acumular en el buffer del párrafo actual
                paragraph_buffer.append(stripped)
            else:
                # Línea vacía ⇒ fin del párrafo actual
                if paragraph_buffer:
                    processed_lines.append(' '.join(paragraph_buffer))
                    paragraph_buffer = []
                # Conservar la línea vacía como separador de párrafos
                processed_lines.append('')

        # Restos del último párrafo
        if paragraph_buffer:
            processed_lines.append(' '.join(paragraph_buffer))

        # Reconstruir contenido pre-procesado
        content = '\n'.join(processed_lines)

        lines = content.split('\n')
        analysis = TextStructuralAnalysis()
        
        analysis.total_lines = len(lines)
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        analysis.non_empty_lines = len(non_empty_lines)
        analysis.empty_lines_count = analysis.total_lines - analysis.non_empty_lines
        
        if analysis.non_empty_lines == 0:
            return analysis
        
        # Análisis de longitudes de línea
        line_lengths = [len(line.strip()) for line in non_empty_lines]
        analysis.average_line_length = sum(line_lengths) / len(line_lengths)
        
        # Contar líneas cortas según umbrales conservadores
        analysis.short_lines_count = sum(1 for length in line_lengths 
                                       if length <= self.thresholds['short_line_threshold'])
        analysis.very_short_lines_count = sum(1 for length in line_lengths 
                                            if length <= self.thresholds['very_short_line_threshold'])
        
        # Calcular ratios
        analysis.line_breaks_density = analysis.empty_lines_count / analysis.total_lines if analysis.total_lines > 0 else 0
        analysis.short_blocks_ratio = analysis.very_short_lines_count / analysis.non_empty_lines if analysis.non_empty_lines > 0 else 0
        
        # Detectar grupos de líneas cortas consecutivas (indicador de verso)
        consecutive_count = 0
        in_short_group = False
        
        for line in lines:
            line_clean = line.strip()
            if line_clean and len(line_clean) <= self.thresholds['short_line_threshold']:
                if not in_short_group:
                    consecutive_count += 1
                    in_short_group = True
            else:
                in_short_group = False
        
        analysis.consecutive_short_lines_groups = consecutive_count
        
        return analysis
    
    def _classify_based_on_structure(self, analysis: TextStructuralAnalysis, 
                                   filename_hint: Optional[str]) -> ProfileCandidate:
        """
        Clasificar el contenido basándose en análisis estructural.
        
        ALGORITMO CONSERVADOR:
        - Prosa por defecto
        - Verso solo si >80% cumple criterios estructurales
        """
        reasons = []
        metrics = {
            'total_lines': analysis.total_lines,
            'non_empty_lines': analysis.non_empty_lines,
            'average_line_length': analysis.average_line_length,
            'short_lines_ratio': analysis.short_lines_count / analysis.non_empty_lines if analysis.non_empty_lines > 0 else 0,
            'short_blocks_ratio': analysis.short_blocks_ratio,
            'line_breaks_density': analysis.line_breaks_density,
            'consecutive_groups': analysis.consecutive_short_lines_groups
        }
        
        # Logging detallado de métricas
        self.logger.debug(f"📊 MÉTRICAS ESTRUCTURALES:")
        self.logger.debug(f"📊   Total líneas: {analysis.total_lines}")
        self.logger.debug(f"📊   Líneas no vacías: {analysis.non_empty_lines}")
        self.logger.debug(f"📊   Longitud promedio: {analysis.average_line_length:.1f}")
        self.logger.debug(f"📊   Líneas cortas (<180): {analysis.short_lines_count}/{analysis.non_empty_lines} ({metrics['short_lines_ratio']:.1%})")
        self.logger.debug(f"📊   Bloques muy cortos (<100): {analysis.very_short_lines_count}/{analysis.non_empty_lines} ({analysis.short_blocks_ratio:.1%})")
        self.logger.debug(f"📊   Densidad saltos: {analysis.line_breaks_density:.1%}")
        self.logger.debug(f"📊   Grupos consecutivos: {analysis.consecutive_short_lines_groups}")
        
        # Verificar si hay suficientes líneas para análisis confiable
        if analysis.non_empty_lines < self.thresholds['min_lines_for_analysis']:
            reasons.append(f'Pocas líneas para análisis ({analysis.non_empty_lines})')
            self.logger.debug(f"❌ INSUFICIENTES LÍNEAS: {analysis.non_empty_lines} < {self.thresholds['min_lines_for_analysis']}")
            return ProfileCandidate(
                profile_name=filename_hint or 'prosa',
                confidence=0.4,
                reasons=reasons,
                structural_metrics=metrics
            )
        
        # === CRITERIOS PARA VERSO (CONSERVADORES) ===
        verso_score = 0.0
        verso_criteria = []
        
        self.logger.debug(f"🔍 EVALUANDO CRITERIOS DE VERSO:")
        
        # Criterio 1: Mayoría de líneas cortas (<180 chars)
        short_lines_ratio = metrics['short_lines_ratio']
        required_ratio = self.thresholds['verso_short_lines_ratio']
        self.logger.debug(f"🔍   Criterio 1 - Líneas cortas: {short_lines_ratio:.1%} vs {required_ratio:.1%} requerido")
        if short_lines_ratio >= required_ratio:
            verso_score += 0.4
            verso_criteria.append(f'{short_lines_ratio:.1%} líneas <180 chars')
            self.logger.debug(f"✅     CUMPLE: +0.4 puntos")
        else:
            reasons.append(f'Solo {short_lines_ratio:.1%} líneas cortas (necesita ≥{required_ratio:.1%})')
            self.logger.debug(f"❌     NO CUMPLE: {short_lines_ratio:.1%} < {required_ratio:.1%}")
        
        # Criterio 2: Alta proporción de bloques muy cortos (<100 chars)  
        required_blocks_ratio = self.thresholds['verso_short_blocks_ratio']
        self.logger.debug(f"🔍   Criterio 2 - Bloques cortos: {analysis.short_blocks_ratio:.1%} vs {required_blocks_ratio:.1%} requerido")
        if analysis.short_blocks_ratio >= required_blocks_ratio:
            verso_score += 0.3
            verso_criteria.append(f'{analysis.short_blocks_ratio:.1%} bloques <100 chars')
            self.logger.debug(f"✅     CUMPLE: +0.3 puntos")
        else:
            reasons.append(f'Solo {analysis.short_blocks_ratio:.1%} bloques muy cortos (necesita ≥{required_blocks_ratio:.1%})')
            self.logger.debug(f"❌     NO CUMPLE: {analysis.short_blocks_ratio:.1%} < {required_blocks_ratio:.1%}")
        
        # Criterio 3: Densidad de saltos de línea (ajustado para PDFs extraídos)
        required_density = 0.005  # 0.5% - más realista para contenido extraído de PDF
        self.logger.debug(f"🔍   Criterio 3 - Densidad saltos: {analysis.line_breaks_density:.1%} vs {required_density:.1%} requerido")
        if analysis.line_breaks_density > required_density:  # Reducido a 0.5% para PDFs
            verso_score += 0.2
            verso_criteria.append(f'Densidad saltos: {analysis.line_breaks_density:.1%}')
            self.logger.debug(f"✅     CUMPLE: +0.2 puntos")
        else:
            self.logger.debug(f"❌     NO CUMPLE: {analysis.line_breaks_density:.1%} <= {required_density:.1%}")
        
        # Criterio 4: Múltiples grupos de líneas cortas consecutivas
        required_groups = 2
        self.logger.debug(f"🔍   Criterio 4 - Grupos consecutivos: {analysis.consecutive_short_lines_groups} vs {required_groups} requerido")
        if analysis.consecutive_short_lines_groups >= required_groups:  # Reducido de 3 a 2
            verso_score += 0.1
            verso_criteria.append(f'{analysis.consecutive_short_lines_groups} grupos de versos')
            self.logger.debug(f"✅     CUMPLE: +0.1 puntos")
        else:
            self.logger.debug(f"❌     NO CUMPLE: {analysis.consecutive_short_lines_groups} < {required_groups}")
        
        self.logger.debug(f"📊 SCORE FINAL VERSO: {verso_score:.2f} (umbral: {self.thresholds['verso_confidence_threshold']})")
        self.logger.debug(f"📊 CRITERIOS CUMPLIDOS: {len(verso_criteria)} (mínimo: 2)")
        
        # === DECISIÓN CONSERVADORA ===
        if verso_score >= self.thresholds['verso_confidence_threshold'] and len(verso_criteria) >= 2:
            # VERSO solo si cumple criterios estructurales estrictos
            reasons.extend(verso_criteria)
            reasons.append('Criterios estructurales de verso cumplidos (>80%)')
            self.logger.debug(f"✅ CLASIFICADO COMO VERSO")
            
            return ProfileCandidate(
                profile_name='verso',
                confidence=verso_score,
                reasons=reasons,
                structural_metrics=metrics
            )
        else:
            # === VERIFICACIÓN ESPECIAL PARA POESÍA REAL ===
            # Si tenemos indicadores muy fuertes de verso, relajar umbrales
            strong_verse_indicators = 0
            
            # Indicador 1: 100% líneas cortas (muy fuerte)
            if metrics['short_lines_ratio'] >= 0.95:  # 95%+
                strong_verse_indicators += 1
                self.logger.debug(f"🎯 INDICADOR FUERTE: {metrics['short_lines_ratio']:.1%} líneas cortas")
            
            # Indicador 2: 100% bloques muy cortos (muy fuerte)  
            if analysis.short_blocks_ratio >= 0.95:  # 95%+
                strong_verse_indicators += 1
                self.logger.debug(f"🎯 INDICADOR FUERTE: {analysis.short_blocks_ratio:.1%} bloques muy cortos")
            
            # Indicador 3: Longitud promedio muy corta (típico de verso)
            if analysis.average_line_length <= 60:  # Líneas muy cortas
                strong_verse_indicators += 1
                self.logger.debug(f"🎯 INDICADOR FUERTE: Longitud promedio {analysis.average_line_length:.1f} chars")
            
            # Indicador 4: Palabra clave de verso en filename
            if filename_hint == 'verso':
                strong_verse_indicators += 1
                self.logger.debug(f"🎯 INDICADOR FUERTE: Palabra clave de verso en filename")
            
            self.logger.debug(f"📊 INDICADORES FUERTES DE VERSO: {strong_verse_indicators}/4")
            
            # Si tenemos 3+ indicadores fuertes, clasificar como verso aunque no cumpla todos los criterios
            if strong_verse_indicators >= 3:
                adjusted_confidence = min(0.85, 0.6 + strong_verse_indicators * 0.1)
                reasons.append(f'Múltiples indicadores fuertes de verso ({strong_verse_indicators}/4)')
                reasons.append('Clasificado como verso por evidencia estructural convincente')
                self.logger.debug(f"✅ CLASIFICADO COMO VERSO POR INDICADORES FUERTES (confianza: {adjusted_confidence:.2f})")
                
                return ProfileCandidate(
                    profile_name='verso',
                    confidence=adjusted_confidence,
                    reasons=reasons,
                    structural_metrics=metrics
                )
            
            # PROSA por defecto (conservador)
            reasons.append('Criterios estructurales insuficientes para verso')
            reasons.append('Clasificado como prosa (decisión conservadora)')
            self.logger.debug(f"❌ CLASIFICADO COMO PROSA (score: {verso_score:.2f}, criterios: {len(verso_criteria)}, indicadores: {strong_verse_indicators})")
            
            # Boost de confianza si hay hint de filename
            confidence = 0.7
            if filename_hint == 'prosa':
                confidence = 0.8
                reasons.append('Confirmado por nombre de archivo')
            elif filename_hint == 'verso':
                confidence = 0.6  # Menor confianza, estructura contradice filename
                reasons.append('Nombre sugiere verso, pero estructura es prosa')
            
            return ProfileCandidate(
                profile_name='prosa',
                confidence=confidence,
                reasons=reasons,
                structural_metrics=metrics
            )
    
    def get_supported_profiles(self) -> List[str]:
        """Obtener lista de perfiles soportados"""
        return ['json', 'verso', 'prosa']
    
    def get_detection_report(self, file_path: str, content_sample: Optional[str] = None) -> Dict[str, Any]:
        """
        Generar reporte detallado de detección para debugging.
        
        Args:
            file_path: Ruta al archivo
            content_sample: Muestra del contenido (opcional)
            
        Returns:
            Reporte detallado con métricas y análisis
        """
        candidate = self.detect_profile(file_path, content_sample)
        
        return {
            'file_path': str(file_path),
            'detected_profile': candidate.profile_name,
            'confidence': candidate.confidence,
            'reasons': candidate.reasons,
            'structural_metrics': candidate.structural_metrics,
            'thresholds_used': self.thresholds,
            'algorithm_version': '1.0',
            'conservative_mode': True
        }

def detect_profile_for_file(file_path: str, 
                          config: Optional[Dict[str, Any]] = None,
                          content_sample: Optional[str] = None) -> ProfileCandidate:
    """
    Función de conveniencia para detectar perfil de un archivo.
    
    Args:
        file_path: Ruta al archivo
        config: Configuración opcional
        content_sample: Muestra del contenido (opcional)
        
    Returns:
        ProfileCandidate con el perfil recomendado
    """
    detector = ProfileDetector(config)
    return detector.detect_profile(file_path, content_sample)

def get_profile_detection_config() -> Dict[str, Any]:
    """
    Obtener configuración por defecto para detección de perfiles.
    
    Returns:
        Configuración recomendada conservadora
    """
    return {
        'confidence_threshold': 0.8,
        'debug': False,
        'short_line_threshold': 180,
        'very_short_line_threshold': 100,
        'verso_short_lines_ratio': 0.8,  # Conservador: 80%
        'verso_short_blocks_ratio': 0.6,
        'verso_confidence_threshold': 0.8,
        'min_lines_for_analysis': 5,
        'max_sample_lines': 100,
    } 