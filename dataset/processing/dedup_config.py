#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de configuración para el sistema de deduplicación de Biblioperson.

Este módulo maneja la carga y acceso a la configuración del sistema de deduplicación,
permitiendo que sea completamente opcional y configurable.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DeduplicationConfig:
    """Configuración del sistema de deduplicación."""
    enabled: bool = True
    default_output_mode: str = "biblioperson"
    database_path: str = "dataset/data/deduplication.db"
    continue_on_error: bool = True
    log_errors: bool = True
    warn_when_disabled: bool = False

@dataclass
class OutputModeConfig:
    """Configuración de un modo de salida."""
    description: str
    included_fields: List[str] | str
    enable_deduplication: bool
    include_document_hash: bool = False

@dataclass
class CompatibilityConfig:
    """Configuración de compatibilidad."""
    min_pipeline_version: str = "1.0.0"
    validate_compatibility: bool = True
    supported_profiles: List[str] = None
    supported_file_formats: List[str] = None

@dataclass
class PerformanceConfig:
    """Configuración de rendimiento."""
    hash_chunk_size: int = 8192
    operation_timeout: int = 30
    enable_hash_cache: bool = True
    max_cache_size: int = 1000

class DedupConfigManager:
    """Gestor de configuración para el sistema de deduplicación."""
    
    def __init__(self, project_root: Optional[str] = None, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            project_root: Ruta raíz del proyecto. Si es None, se detecta automáticamente.
            config_file: Ruta al archivo de configuración. Si es None, se busca automáticamente.
        """
        # Inicializar logger
        self.logger = logging.getLogger(__name__)
        
        # Inicializar atributos
        self._config_file = config_file
        self._config_data = {}
        
        if project_root is None:
            # Detectar la raíz del proyecto automáticamente
            current_dir = Path(__file__).parent
            # Buscar hacia arriba hasta encontrar el directorio que contiene 'dataset'
            while current_dir.parent != current_dir:
                if (current_dir / 'dataset').exists():
                    self.project_root = current_dir
                    break
                current_dir = current_dir.parent
            else:
                # Fallback: usar el directorio padre de 'dataset'
                self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Cargar la configuración
        self._load_config()
    
    def get_database_path(self) -> Path:
        """
        Obtiene la ruta a la base de datos de deduplicación.
        
        Returns:
            Path: Ruta al archivo de base de datos SQLite
        """
        cache_dir = self.project_root / "dataset" / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "dedup_registry.sqlite"
    
    def get_cache_directory(self) -> Path:
        """
        Obtiene el directorio de caché.
        
        Returns:
            Path: Directorio de caché
        """
        cache_dir = self.project_root / "dataset" / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_project_root(self) -> Path:
        """
        Obtiene la ruta raíz del proyecto.
        
        Returns:
            Path: Ruta raíz del proyecto
        """
        return self.project_root
    
    def _find_config_file(self) -> Optional[Path]:
        """Busca el archivo de configuración en ubicaciones estándar."""
        # Buscar desde el directorio actual hacia arriba
        current_dir = Path(__file__).parent
        
        # Ubicaciones posibles para el archivo de configuración
        possible_locations = [
            current_dir / "../config/deduplication_config.yaml",
            current_dir / "../../config/deduplication_config.yaml",
            current_dir / "../../../config/deduplication_config.yaml",
            current_dir / "deduplication_config.yaml",
            Path.cwd() / "dataset/config/deduplication_config.yaml",
            Path.cwd() / "config/deduplication_config.yaml"
        ]
        
        for location in possible_locations:
            resolved_path = location.resolve()
            if resolved_path.exists():
                self.logger.debug(f"Archivo de configuración encontrado: {resolved_path}")
                return resolved_path
        
        return None
    
    def _load_config(self):
        """Carga la configuración desde el archivo YAML."""
        config_file = None
        
        if self._config_file:
            config_file = Path(self._config_file)
        else:
            config_file = self._find_config_file()
        
        if config_file and config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
                self.logger.info(f"Configuración de deduplicación cargada desde: {config_file}")
            except Exception as e:
                self.logger.warning(f"Error cargando configuración de deduplicación: {e}")
                self._config_data = {}
        else:
            self.logger.info("Archivo de configuración de deduplicación no encontrado, usando valores por defecto")
            self._config_data = {}
        
        # Asegurar que existan las secciones básicas
        self._ensure_default_structure()
    
    def _ensure_default_structure(self):
        """Asegura que la configuración tenga la estructura mínima requerida."""
        defaults = {
            'deduplication': {
                'enabled': True,
                'default_output_mode': 'biblioperson',
                'database_path': 'dataset/data/deduplication.db',
                'error_handling': {
                    'continue_on_error': True,
                    'log_errors': True,
                    'warn_when_disabled': False
                }
            },
            'output_modes': {
                'generic': {
                    'description': 'Salida NDJSON simple sin metadatos adicionales',
                    'included_fields': [
                        'segment_id', 'document_id', 'text', 'segment_type', 
                        'segment_order', 'text_length', 'processing_timestamp',
                        'source_file_path', 'document_title', 'document_author',
                        'document_language', 'pipeline_version', 'segmenter_used'
                    ],
                    'enable_deduplication': False,
                    'include_document_hash': False
                },
                'biblioperson': {
                    'description': 'Salida NDJSON enriquecida con metadatos completos y deduplicación',
                    'included_fields': 'all',
                    'enable_deduplication': True,
                    'include_document_hash': True
                }
            },
            'compatibility': {
                'min_pipeline_version': '1.0.0',
                'validate_compatibility': True,
                'supported_profiles': ['json', 'prosa', 'verso', 'automático'],
                'supported_file_formats': ['.pdf', '.docx', '.txt', '.md', '.json', '.ndjson']
            },
            'performance': {
                'hash_chunk_size': 8192,
                'operation_timeout': 30,
                'enable_hash_cache': True,
                'max_cache_size': 1000
            }
        }
        
        # Fusionar configuración por defecto con la cargada
        self._merge_defaults(self._config_data, defaults)
    
    def _merge_defaults(self, config: Dict[str, Any], defaults: Dict[str, Any]):
        """Fusiona la configuración por defecto con la configuración cargada."""
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict) and isinstance(config[key], dict):
                self._merge_defaults(config[key], value)
    
    def get_deduplication_config(self) -> DeduplicationConfig:
        """Obtiene la configuración de deduplicación."""
        dedup_section = self._config_data.get('deduplication', {})
        error_handling = dedup_section.get('error_handling', {})
        
        return DeduplicationConfig(
            enabled=dedup_section.get('enabled', True),
            default_output_mode=dedup_section.get('default_output_mode', 'biblioperson'),
            database_path=dedup_section.get('database_path', 'dataset/data/deduplication.db'),
            continue_on_error=error_handling.get('continue_on_error', True),
            log_errors=error_handling.get('log_errors', True),
            warn_when_disabled=error_handling.get('warn_when_disabled', False)
        )
    
    def get_output_mode_config(self, mode: str) -> Optional[OutputModeConfig]:
        """
        Obtiene la configuración de un modo de salida específico.
        
        Args:
            mode: Nombre del modo ('generic' o 'biblioperson')
            
        Returns:
            Configuración del modo o None si no existe
        """
        output_modes = self._config_data.get('output_modes', {})
        mode_config = output_modes.get(mode)
        
        if not mode_config:
            return None
        
        return OutputModeConfig(
            description=mode_config.get('description', ''),
            included_fields=mode_config.get('included_fields', []),
            enable_deduplication=mode_config.get('enable_deduplication', False),
            include_document_hash=mode_config.get('include_document_hash', False)
        )
    
    def get_compatibility_config(self) -> CompatibilityConfig:
        """Obtiene la configuración de compatibilidad."""
        compat_section = self._config_data.get('compatibility', {})
        
        return CompatibilityConfig(
            min_pipeline_version=compat_section.get('min_pipeline_version', '1.0.0'),
            validate_compatibility=compat_section.get('validate_compatibility', True),
            supported_profiles=compat_section.get('supported_profiles', ['json', 'prosa', 'verso', 'automático']),
            supported_file_formats=compat_section.get('supported_file_formats', ['.pdf', '.docx', '.txt', '.md', '.json', '.ndjson'])
        )
    
    def get_performance_config(self) -> PerformanceConfig:
        """Obtiene la configuración de rendimiento."""
        perf_section = self._config_data.get('performance', {})
        
        return PerformanceConfig(
            hash_chunk_size=perf_section.get('hash_chunk_size', 8192),
            operation_timeout=perf_section.get('operation_timeout', 30),
            enable_hash_cache=perf_section.get('enable_hash_cache', True),
            max_cache_size=perf_section.get('max_cache_size', 1000)
        )
    
    def is_deduplication_enabled(self) -> bool:
        """Verifica si la deduplicación está habilitada globalmente."""
        return self.get_deduplication_config().enabled
    
    def is_deduplication_enabled_for_mode(self, mode: str) -> bool:
        """
        Verifica si la deduplicación está habilitada para un modo específico.
        
        Args:
            mode: Nombre del modo ('generic' o 'biblioperson')
            
        Returns:
            True si la deduplicación está habilitada para este modo
        """
        if not self.is_deduplication_enabled():
            return False
        
        mode_config = self.get_output_mode_config(mode)
        if not mode_config:
            return False
        
        return mode_config.enable_deduplication
    
    def is_profile_supported(self, profile_name: str) -> bool:
        """
        Verifica si un perfil es compatible con el sistema de deduplicación.
        
        Args:
            profile_name: Nombre del perfil
            
        Returns:
            True si el perfil es compatible
        """
        compat_config = self.get_compatibility_config()
        return profile_name in compat_config.supported_profiles
    
    def is_file_format_supported(self, file_path: str) -> bool:
        """
        Verifica si un formato de archivo es compatible con deduplicación.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            True si el formato es compatible
        """
        file_extension = Path(file_path).suffix.lower()
        compat_config = self.get_compatibility_config()
        return file_extension in compat_config.supported_file_formats
    
    def reload_config(self):
        """Recarga la configuración desde el archivo."""
        self._load_config()
        self.logger.info("Configuración de deduplicación recargada")

# Instancia global del gestor de configuración
_config_manager = None

def get_config_manager() -> DedupConfigManager:
    """
    Obtiene la instancia global del gestor de configuración.
    
    Returns:
        Instancia del DedupConfigManager
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = DedupConfigManager()
    
    return _config_manager

def is_deduplication_enabled() -> bool:
    """Verifica si la deduplicación está habilitada globalmente."""
    return get_config_manager().is_deduplication_enabled()

def is_deduplication_enabled_for_mode(mode: str) -> bool:
    """Verifica si la deduplicación está habilitada para un modo específico."""
    return get_config_manager().is_deduplication_enabled_for_mode(mode)

def get_default_output_mode() -> str:
    """Obtiene el modo de salida por defecto."""
    return get_config_manager().get_deduplication_config().default_output_mode 