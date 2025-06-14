# -*- coding: utf-8 -*-
"""
Detector de autores basado en estilometría
Integra bibliotecas especializadas para mejorar la detección de autores literarios
"""

import re
import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Importar bibliotecas de estilometría
try:
    from faststylometry import Corpus, calculate_burrows_delta, predict_proba
    FASTSTYLOMETRY_AVAILABLE = True
except ImportError:
    FASTSTYLOMETRY_AVAILABLE = False
    logging.warning("faststylometry no está disponible. Instalar con: pip install faststylometry")

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK no está disponible. Instalar con: pip install nltk")

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    logging.warning("textstat no está disponible. Instalar con: pip install textstat")

@dataclass
class StylometricFeatures:
    """Características estilométricas de un texto"""
    avg_sentence_length: float = 0.0
    avg_word_length: float = 0.0
    lexical_diversity: float = 0.0
    function_word_ratio: float = 0.0
    punctuation_ratio: float = 0.0
    readability_score: float = 0.0
    syllable_complexity: float = 0.0
    
@dataclass
class AuthorProfile:
    """Perfil estilométrico de un autor"""
    name: str
    works: List[str]
    features: StylometricFeatures
    confidence: float = 0.0

class LiteraryAuthorDatabase:
    """Base de datos de autores literarios conocidos"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), 'literary_authors_db.json')
        self.authors = self._load_authors_database()
        
    def _load_authors_database(self) -> Dict[str, Dict[str, Any]]:
        """Carga la base de datos de autores literarios"""
        # Base de datos inicial con autores hispanoamericanos importantes
        default_authors = {
            "rubén darío": {
                "full_name": "Rubén Darío",
                "aliases": ["ruben dario", "félix rubén garcía sarmiento"],
                "nationality": "nicaragüense",
                "period": "modernismo",
                "birth_year": 1867,
                "death_year": 1916,
                "famous_works": [
                    "Azul", "Prosas profanas", "Cantos de vida y esperanza",
                    "Canción de otoño en primavera", "Lo fatal", "Sonatina"
                ],
                "stylistic_markers": [
                    "juventud divino tesoro", "princesa", "cisne", "azul",
                    "modernista", "parnasiano", "simbolista"
                ]
            },
            "josé martí": {
                "full_name": "José Martí",
                "aliases": ["jose marti", "josé julián martí pérez"],
                "nationality": "cubano",
                "period": "modernismo",
                "birth_year": 1853,
                "death_year": 1895,
                "famous_works": ["Versos libres", "Versos sencillos", "Ismaelillo"],
                "stylistic_markers": ["patria", "libertad", "verso sencillo"]
            },
            "amado nervo": {
                "full_name": "Amado Nervo",
                "aliases": ["juan crisóstomo ruiz de nervo"],
                "nationality": "mexicano",
                "period": "modernismo",
                "birth_year": 1870,
                "death_year": 1919,
                "famous_works": ["Místicas", "Los jardines interiores", "Serenidad"],
                "stylistic_markers": ["serenidad", "místico", "jardín interior"]
            },
            "leopoldo lugones": {
                "full_name": "Leopoldo Lugones",
                "aliases": ["leopoldo antonio lugones argüello"],
                "nationality": "argentino",
                "period": "modernismo",
                "birth_year": 1874,
                "death_year": 1938,
                "famous_works": ["Las montañas del oro", "Lunario sentimental"],
                "stylistic_markers": ["lunario", "montañas del oro"]
            }
        }
        
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    loaded_authors = json.load(f)
                # Combinar con autores por defecto
                default_authors.update(loaded_authors)
            else:
                # Crear archivo con autores por defecto
                self._save_authors_database(default_authors)
        except Exception as e:
            logging.warning(f"Error cargando base de datos de autores: {e}")
            
        return default_authors
    
    def _save_authors_database(self, authors: Dict[str, Dict[str, Any]]):
        """Guarda la base de datos de autores"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(authors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error guardando base de datos de autores: {e}")
    
    def find_author(self, name: str) -> Optional[Dict[str, Any]]:
        """Busca un autor en la base de datos"""
        name_lower = name.lower().strip()
        
        # Búsqueda exacta
        if name_lower in self.authors:
            return self.authors[name_lower]
        
        # Búsqueda por alias
        for author_key, author_data in self.authors.items():
            aliases = author_data.get('aliases', [])
            if name_lower in [alias.lower() for alias in aliases]:
                return author_data
        
        # Búsqueda parcial
        name_parts = name_lower.split()
        if len(name_parts) >= 2:
            for author_key, author_data in self.authors.items():
                author_name_parts = author_key.split()
                if len(set(name_parts) & set(author_name_parts)) >= 2:
                    return author_data
        
        return None
    
    def get_stylistic_markers(self, author_name: str) -> List[str]:
        """Obtiene marcadores estilísticos de un autor"""
        author_data = self.find_author(author_name)
        if author_data:
            return author_data.get('stylistic_markers', [])
        return []

class StylometricAnalyzer:
    """Analizador estilométrico de textos"""
    
    def __init__(self):
        self.spanish_stopwords = self._get_spanish_stopwords()
        
    def _get_spanish_stopwords(self) -> set:
        """Obtiene palabras vacías en español"""
        if NLTK_AVAILABLE:
            try:
                return set(stopwords.words('spanish'))
            except:
                nltk.download('stopwords')
                return set(stopwords.words('spanish'))
        else:
            # Lista básica de palabras vacías en español
            return {
                'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
                'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como',
                'pero', 'sus', 'me', 'ya', 'muy', 'mi', 'sin', 'sobre', 'este', 'ser', 'tiene',
                'todo', 'esta', 'era', 'cuando', 'él', 'más', 'si', 'puede', 'hasta', 'otros'
            }
    
    def extract_features(self, text: str) -> StylometricFeatures:
        """Extrae características estilométricas del texto"""
        if not text.strip():
            return StylometricFeatures()
        
        # Tokenización básica
        sentences = self._tokenize_sentences(text)
        words = self._tokenize_words(text)
        
        # Calcular características
        features = StylometricFeatures()
        
        if sentences:
            features.avg_sentence_length = sum(len(self._tokenize_words(sent)) for sent in sentences) / len(sentences)
        
        if words:
            features.avg_word_length = sum(len(word) for word in words) / len(words)
            features.lexical_diversity = len(set(words)) / len(words)
            
            # Ratio de palabras funcionales
            function_words = [word for word in words if word.lower() in self.spanish_stopwords]
            features.function_word_ratio = len(function_words) / len(words)
        
        # Ratio de puntuación
        punctuation_chars = sum(1 for char in text if char in '.,;:!?¡¿()[]{}""''—–-')
        features.punctuation_ratio = punctuation_chars / len(text) if text else 0
        
        # Puntuación de legibilidad (si textstat está disponible)
        if TEXTSTAT_AVAILABLE:
            try:
                features.readability_score = textstat.flesch_reading_ease(text)
                features.syllable_complexity = textstat.avg_syllables_per_word(text)
            except:
                pass
        
        return features
    
    def _tokenize_sentences(self, text: str) -> List[str]:
        """Tokeniza oraciones"""
        if NLTK_AVAILABLE:
            return sent_tokenize(text, language='spanish')
        else:
            # Tokenización básica por puntos
            return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    
    def _tokenize_words(self, text: str) -> List[str]:
        """Tokeniza palabras"""
        if NLTK_AVAILABLE:
            return [word.lower() for word in word_tokenize(text, language='spanish') if word.isalpha()]
        else:
            # Tokenización básica
            return [word.lower() for word in re.findall(r'\b[a-záéíóúñü]+\b', text, re.IGNORECASE)]

class StylometricAuthorDetector:
    """Detector de autores basado en estilometría"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        self.debug = self.config.get('debug', False)
        
        # Inicializar componentes
        self.author_db = LiteraryAuthorDatabase()
        self.stylometric_analyzer = StylometricAnalyzer()
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
    def detect_author(self, segments: List[Dict[str, Any]], profile_type: str) -> Optional[Dict[str, Any]]:
        """Detecta el autor usando análisis estilométrico"""
        if not segments:
            return None
        
        # Combinar texto de todos los segmentos
        full_text = self._combine_segments_text(segments)
        
        if not full_text.strip():
            return None
        
        # Extraer contexto del documento
        doc_context = self._extract_document_context(segments)
        
        # Buscar en base de datos de autores literarios
        literary_match = self._find_literary_author_match(full_text, doc_context)
        
        if literary_match:
            return literary_match
        
        # Análisis estilométrico avanzado (si las bibliotecas están disponibles)
        if FASTSTYLOMETRY_AVAILABLE:
            stylometric_match = self._perform_stylometric_analysis(full_text)
            if stylometric_match:
                return stylometric_match
        
        # Análisis de características estilísticas básicas
        features_match = self._analyze_stylistic_features(full_text, doc_context)
        
        return features_match
    
    def _combine_segments_text(self, segments: List[Dict[str, Any]]) -> str:
        """Combina el texto de todos los segmentos"""
        texts = []
        for segment in segments:
            text = segment.get('text', '')
            if text:
                texts.append(text)
        return '\n\n'.join(texts)
    
    def _extract_document_context(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrae contexto del documento"""
        context = {
            'document_title': None,
            'source_file_path': None,
            'filename': None
        }
        
        if segments:
            first_segment = segments[0]
            context['document_title'] = first_segment.get('document_title')
            context['source_file_path'] = first_segment.get('source_file_path')
            
            if context['source_file_path']:
                context['filename'] = os.path.basename(context['source_file_path'])
        
        return context
    
    def _find_literary_author_match(self, text: str, doc_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca coincidencias con autores literarios conocidos"""
        
        # Buscar en título del documento
        if doc_context.get('document_title'):
            title_author = self._extract_author_from_title(doc_context['document_title'])
            if title_author:
                author_data = self.author_db.find_author(title_author)
                if author_data:
                    # Verificar marcadores estilísticos en el texto
                    stylistic_score = self._calculate_stylistic_match_score(text, author_data)
                    if stylistic_score > 0.3:
                        return {
                            'name': author_data['full_name'],
                            'confidence': min(0.9, 0.7 + stylistic_score),
                            'method': 'literary_database_match',
                            'details': {
                                'source': 'document_title',
                                'stylistic_score': stylistic_score,
                                'matched_markers': self._get_matched_markers(text, author_data),
                                'author_period': author_data.get('period'),
                                'author_nationality': author_data.get('nationality')
                            }
                        }
        
        # Buscar en nombre de archivo
        if doc_context.get('filename'):
            filename_author = self._extract_author_from_title(doc_context['filename'])
            if filename_author:
                author_data = self.author_db.find_author(filename_author)
                if author_data:
                    stylistic_score = self._calculate_stylistic_match_score(text, author_data)
                    if stylistic_score > 0.2:
                        return {
                            'name': author_data['full_name'],
                            'confidence': min(0.85, 0.6 + stylistic_score),
                            'method': 'literary_database_match',
                            'details': {
                                'source': 'filename',
                                'stylistic_score': stylistic_score,
                                'matched_markers': self._get_matched_markers(text, author_data)
                            }
                        }
        
        # Buscar marcadores estilísticos en el texto
        for author_key, author_data in self.author_db.authors.items():
            stylistic_score = self._calculate_stylistic_match_score(text, author_data)
            if stylistic_score > 0.5:
                return {
                    'name': author_data['full_name'],
                    'confidence': min(0.8, stylistic_score),
                    'method': 'stylistic_markers_match',
                    'details': {
                        'stylistic_score': stylistic_score,
                        'matched_markers': self._get_matched_markers(text, author_data)
                    }
                }
        
        return None
    
    def _extract_author_from_title(self, title: str) -> Optional[str]:
        """Extrae nombre de autor del título"""
        # Patrones para extraer autores de títulos
        patterns = [
            r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*[-–—_]',
            r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*[-–—_]',
            r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*[-–—_].*(?:antologia|obras|poemas)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                author_name = match.group(1).strip()
                # Normalizar formato "Apellido, Nombre" a "Nombre Apellido"
                if ',' in author_name:
                    parts = author_name.split(',')
                    if len(parts) == 2:
                        author_name = f"{parts[1].strip()} {parts[0].strip()}"
                return author_name
        
        return None
    
    def _calculate_stylistic_match_score(self, text: str, author_data: Dict[str, Any]) -> float:
        """Calcula puntuación de coincidencia estilística"""
        score = 0.0
        text_lower = text.lower()
        
        # Verificar marcadores estilísticos
        stylistic_markers = author_data.get('stylistic_markers', [])
        matched_markers = 0
        
        for marker in stylistic_markers:
            if marker.lower() in text_lower:
                matched_markers += 1
                score += 0.2
        
        # Verificar obras famosas
        famous_works = author_data.get('famous_works', [])
        for work in famous_works:
            if work.lower() in text_lower:
                score += 0.3
        
        # Normalizar puntuación
        if stylistic_markers:
            marker_ratio = matched_markers / len(stylistic_markers)
            score = max(score, marker_ratio * 0.8)
        
        return min(score, 1.0)
    
    def _get_matched_markers(self, text: str, author_data: Dict[str, Any]) -> List[str]:
        """Obtiene marcadores estilísticos que coinciden en el texto"""
        matched = []
        text_lower = text.lower()
        
        for marker in author_data.get('stylistic_markers', []):
            if marker.lower() in text_lower:
                matched.append(marker)
        
        for work in author_data.get('famous_works', []):
            if work.lower() in text_lower:
                matched.append(f"obra: {work}")
        
        return matched
    
    def _perform_stylometric_analysis(self, text: str) -> Optional[Dict[str, Any]]:
        """Realiza análisis estilométrico usando faststylometry"""
        # Esta función requeriría un corpus de entrenamiento
        # Por ahora, retornamos None para implementación futura
        return None
    
    def _analyze_stylistic_features(self, text: str, doc_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analiza características estilísticas básicas"""
        features = self.stylometric_analyzer.extract_features(text)
        
        # Análisis básico de características para determinar período/estilo
        confidence = 0.0
        detected_style = None
        
        # Características del modernismo (Rubén Darío, etc.)
        if (features.avg_word_length > 5.5 and 
            features.lexical_diversity > 0.6 and
            features.punctuation_ratio > 0.05):
            detected_style = "modernismo"
            confidence = 0.4
        
        # Si hay características modernistas y contexto de documento apropiado
        if detected_style == "modernismo" and doc_context.get('document_title'):
            title = doc_context['document_title'].lower()
            if any(word in title for word in ['dario', 'ruben', 'antologia', 'poemas']):
                confidence = 0.7
                return {
                    'name': 'Rubén Darío',
                    'confidence': confidence,
                    'method': 'stylistic_analysis',
                    'details': {
                        'detected_style': detected_style,
                        'features': {
                            'avg_word_length': features.avg_word_length,
                            'lexical_diversity': features.lexical_diversity,
                            'punctuation_ratio': features.punctuation_ratio
                        }
                    }
                }
        
        return None