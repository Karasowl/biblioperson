"""
Validador de autores contra una base de datos de autores conocidos.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
from difflib import SequenceMatcher

try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

class KnownAuthorsValidator:
    """
    Valida candidatos de autor contra una base de datos de autores conocidos.
    """
    
    def __init__(self, authors_file: Optional[str] = None):
        """
        Args:
            authors_file: Ruta al archivo JSON con autores conocidos
        """
        self.logger = logging.getLogger(__name__)
        self.authors_file = authors_file or self._get_default_authors_file()
        self.known_authors = self._load_known_authors()
        self.fuzzy_available = FUZZYWUZZY_AVAILABLE
        
        if not self.fuzzy_available:
            self.logger.warning("fuzzywuzzy no instalado. Instale con: pip install fuzzywuzzy python-Levenshtein")
    
    def _get_default_authors_file(self) -> str:
        """Obtiene la ruta al archivo de autores por defecto."""
        current_dir = Path(__file__).parent
        return str(current_dir / "data" / "known_authors_es.json")
    
    def _load_known_authors(self) -> Dict[str, Dict[str, Any]]:
        """Carga la base de datos de autores conocidos."""
        if not os.path.exists(self.authors_file):
            self.logger.warning(f"Archivo de autores no encontrado: {self.authors_file}")
            return self._get_default_authors()
        
        try:
            with open(self.authors_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Normalizar estructura
            authors = {}
            for author in data.get('authors', []):
                if isinstance(author, dict) and 'name' in author:
                    normalized_name = self._normalize_name(author['name'])
                    authors[normalized_name] = {
                        'canonical_name': author['name'],
                        'aliases': author.get('aliases', []),
                        'birth_year': author.get('birth_year'),
                        'death_year': author.get('death_year'),
                        'nationality': author.get('nationality', 'unknown'),
                        'genres': author.get('genres', [])
                    }
            
            self.logger.info(f"Cargados {len(authors)} autores conocidos")
            return authors
            
        except Exception as e:
            self.logger.error(f"Error cargando autores: {e}")
            return self._get_default_authors()
    
    def _get_default_authors(self) -> Dict[str, Dict[str, Any]]:
        """Retorna una lista básica de autores hispanos conocidos."""
        default_authors = [
            # Poetas clásicos
            {"name": "Pablo Neruda", "aliases": ["Neftalí Ricardo Reyes Basoalto"], "nationality": "Chile"},
            {"name": "Gabriela Mistral", "aliases": ["Lucila Godoy Alcayaga"], "nationality": "Chile"},
            {"name": "Federico García Lorca", "nationality": "España"},
            {"name": "Antonio Machado", "nationality": "España"},
            {"name": "Rubén Darío", "aliases": ["Félix Rubén García Sarmiento"], "nationality": "Nicaragua"},
            {"name": "César Vallejo", "nationality": "Perú"},
            {"name": "Octavio Paz", "nationality": "México"},
            {"name": "Jorge Luis Borges", "nationality": "Argentina"},
            {"name": "Julio Cortázar", "nationality": "Argentina"},
            {"name": "Mario Benedetti", "nationality": "Uruguay"},
            
            # Escritores clásicos
            {"name": "Miguel de Cervantes", "aliases": ["Miguel de Cervantes Saavedra"], "nationality": "España"},
            {"name": "Gabriel García Márquez", "aliases": ["Gabo"], "nationality": "Colombia"},
            {"name": "Isabel Allende", "nationality": "Chile"},
            {"name": "Carlos Fuentes", "nationality": "México"},
            {"name": "Juan Rulfo", "nationality": "México"},
            {"name": "Roberto Bolaño", "nationality": "Chile"},
            {"name": "Horacio Quiroga", "nationality": "Uruguay"},
            {"name": "José Martí", "nationality": "Cuba"},
            {"name": "Sor Juana Inés de la Cruz", "nationality": "México"},
            {"name": "Gustavo Adolfo Bécquer", "nationality": "España"},
            
            # Contemporáneos
            {"name": "Elena Poniatowska", "nationality": "México"},
            {"name": "Laura Esquivel", "nationality": "México"},
            {"name": "Luis Sepúlveda", "nationality": "Chile"},
            {"name": "Eduardo Galeano", "nationality": "Uruguay"},
            {"name": "Alfonsina Storni", "nationality": "Argentina"},
            {"name": "Alejandra Pizarnik", "nationality": "Argentina"},
            {"name": "Rosario Castellanos", "nationality": "México"},
            {"name": "Juan Gelman", "nationality": "Argentina"},
            {"name": "Nicanor Parra", "nationality": "Chile"},
            {"name": "José Emilio Pacheco", "nationality": "México"}
        ]
        
        # Convertir a formato interno
        authors = {}
        for author in default_authors:
            normalized_name = self._normalize_name(author['name'])
            authors[normalized_name] = {
                'canonical_name': author['name'],
                'aliases': author.get('aliases', []),
                'nationality': author.get('nationality', 'unknown'),
                'genres': author.get('genres', [])
            }
        
        return authors
    
    def validate_author(self, author_name: str, threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """
        Valida si un nombre corresponde a un autor conocido.
        
        Args:
            author_name: Nombre a validar
            threshold: Umbral de similitud (0-1)
            
        Returns:
            Información del autor si se encuentra, None si no
        """
        if not author_name:
            return None
        
        normalized_query = self._normalize_name(author_name)
        
        # Búsqueda exacta
        if normalized_query in self.known_authors:
            return {
                'match_type': 'exact',
                'confidence': 1.0,
                'author_info': self.known_authors[normalized_query]
            }
        
        # Búsqueda en aliases
        for norm_name, author_info in self.known_authors.items():
            for alias in author_info.get('aliases', []):
                if self._normalize_name(alias) == normalized_query:
                    return {
                        'match_type': 'alias',
                        'confidence': 0.95,
                        'author_info': author_info
                    }
        
        # Búsqueda difusa
        if self.fuzzy_available:
            return self._fuzzy_match(author_name, threshold)
        else:
            return self._simple_fuzzy_match(author_name, threshold)
    
    def _fuzzy_match(self, author_name: str, threshold: float) -> Optional[Dict[str, Any]]:
        """Búsqueda difusa usando fuzzywuzzy."""
        # Preparar lista de nombres para búsqueda
        all_names = []
        name_to_info = {}
        
        for norm_name, author_info in self.known_authors.items():
            canonical = author_info['canonical_name']
            all_names.append(canonical)
            name_to_info[canonical] = author_info
            
            # Incluir aliases
            for alias in author_info.get('aliases', []):
                all_names.append(alias)
                name_to_info[alias] = author_info
        
        # Buscar mejores coincidencias
        matches = process.extract(author_name, all_names, scorer=fuzz.token_sort_ratio, limit=3)
        
        if matches and matches[0][1] >= threshold * 100:
            best_match = matches[0]
            return {
                'match_type': 'fuzzy',
                'confidence': best_match[1] / 100,
                'matched_name': best_match[0],
                'author_info': name_to_info[best_match[0]],
                'alternatives': [m[0] for m in matches[1:] if m[1] >= (threshold * 0.8) * 100]
            }
        
        return None
    
    def _simple_fuzzy_match(self, author_name: str, threshold: float) -> Optional[Dict[str, Any]]:
        """Búsqueda difusa simple sin fuzzywuzzy."""
        best_score = 0
        best_match = None
        
        normalized_query = self._normalize_name(author_name)
        
        for norm_name, author_info in self.known_authors.items():
            # Comparar con nombre canónico
            score = self._similarity_score(normalized_query, norm_name)
            if score > best_score:
                best_score = score
                best_match = author_info
            
            # Comparar con aliases
            for alias in author_info.get('aliases', []):
                score = self._similarity_score(normalized_query, self._normalize_name(alias))
                if score > best_score:
                    best_score = score
                    best_match = author_info
        
        if best_score >= threshold:
            return {
                'match_type': 'fuzzy_simple',
                'confidence': best_score,
                'author_info': best_match
            }
        
        return None
    
    def enhance_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mejora la lista de candidatos con información de autores conocidos.
        
        Args:
            candidates: Lista de candidatos de autor
            
        Returns:
            Lista mejorada de candidatos
        """
        enhanced = []
        
        for candidate in candidates:
            enhanced_candidate = candidate.copy()
            author_name = candidate.get('name', '')
            
            validation = self.validate_author(author_name)
            
            if validation:
                # Aumentar confianza si es autor conocido
                current_confidence = enhanced_candidate.get('confidence', 0.5)
                boost_factor = 1.3 if validation['match_type'] == 'exact' else 1.2
                enhanced_candidate['confidence'] = min(current_confidence * boost_factor, 1.0)
                
                # Agregar información del autor
                enhanced_candidate['is_known_author'] = True
                enhanced_candidate['known_author_info'] = validation['author_info']
                enhanced_candidate['match_type'] = validation['match_type']
                enhanced_candidate['match_confidence'] = validation['confidence']
                
                # Usar nombre canónico si la coincidencia es alta
                if validation['confidence'] >= 0.9:
                    enhanced_candidate['canonical_name'] = validation['author_info']['canonical_name']
                
                self.logger.debug(f"Autor conocido detectado: {author_name} → {validation['author_info']['canonical_name']}")
            else:
                enhanced_candidate['is_known_author'] = False
                # Penalizar ligeramente si no es conocido
                enhanced_candidate['confidence'] = enhanced_candidate.get('confidence', 0.5) * 0.95
            
            enhanced.append(enhanced_candidate)
        
        # Ordenar por confianza
        enhanced.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return enhanced
    
    def _normalize_name(self, name: str) -> str:
        """Normaliza un nombre para comparación."""
        if not name:
            return ""
        
        # Convertir a minúsculas y remover acentos
        import unicodedata
        name = unicodedata.normalize('NFD', name.lower())
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        
        # Remover puntuación y espacios extra
        import re
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calcula similitud entre dos cadenas."""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def save_authors(self, output_file: Optional[str] = None):
        """
        Guarda la base de datos de autores actual.
        
        Args:
            output_file: Archivo donde guardar (usa el actual si no se especifica)
        """
        output_file = output_file or self.authors_file
        
        # Convertir a formato serializable
        authors_list = []
        for norm_name, info in self.known_authors.items():
            author_dict = {
                'name': info['canonical_name'],
                'aliases': info.get('aliases', []),
                'nationality': info.get('nationality'),
                'genres': info.get('genres', [])
            }
            if info.get('birth_year'):
                author_dict['birth_year'] = info['birth_year']
            if info.get('death_year'):
                author_dict['death_year'] = info['death_year']
            
            authors_list.append(author_dict)
        
        # Guardar
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({'authors': authors_list}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Base de datos guardada en {output_file}")
        except Exception as e:
            self.logger.error(f"Error guardando autores: {e}") 