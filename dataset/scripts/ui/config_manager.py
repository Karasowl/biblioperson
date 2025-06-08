#!/usr/bin/env python3
"""
Sistema de gestión de configuración para el generador de perfiles IA.

Maneja la persistencia de API keys y el sistema de aprendizaje de errores.
"""

import json
import os
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib


class ConfigManager:
    """Gestor de configuración para API keys y configuraciones del generador IA."""
    
    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Detectar automáticamente la raíz del proyecto
            current_dir = Path(__file__).parent
            while current_dir.parent != current_dir:
                if (current_dir / '.git').exists() or (current_dir / 'README.md').exists():
                    self.project_root = current_dir
                    break
                current_dir = current_dir.parent
            else:
                self.project_root = Path.cwd()
        
        self.config_dir = self.project_root / 'config'
        self.config_dir.mkdir(exist_ok=True)
        
        self.api_keys_file = self.config_dir / 'api_keys.json'
        self.errors_file = self.config_dir / 'generation_errors.json'
        
        # Asegurar que el archivo esté en .gitignore
        self._ensure_gitignore()
    
    def _ensure_gitignore(self):
        """Asegura que los archivos de configuración estén en .gitignore."""
        gitignore_path = self.project_root / '.gitignore'
        
        entries_to_add = [
            'config/api_keys.json',
            'config/generation_errors.json'
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = ""
        
        new_entries = []
        for entry in entries_to_add:
            if entry not in existing_content:
                new_entries.append(entry)
        
        if new_entries:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                if not existing_content.endswith('\n'):
                    f.write('\n')
                f.write('\n# Configuración de API keys (generado automáticamente)\n')
                for entry in new_entries:
                    f.write(f'{entry}\n')
    
    def _encode_key(self, key: str) -> str:
        """Codifica una API key usando base64 (ofuscación básica)."""
        if not key:
            return ""
        return base64.b64encode(key.encode('utf-8')).decode('utf-8')
    
    def _decode_key(self, encoded_key: str) -> str:
        """Decodifica una API key desde base64."""
        if not encoded_key:
            return ""
        try:
            return base64.b64decode(encoded_key.encode('utf-8')).decode('utf-8')
        except Exception:
            return ""
    
    def save_api_keys(self, openai_key: str = "", google_key: str = "", anthropic_key: str = ""):
        """Guarda las API keys de forma persistente."""
        config_data = {
            'last_updated': datetime.now().isoformat(),
            'keys': {
                'openai': self._encode_key(openai_key),
                'google': self._encode_key(google_key),
                'anthropic': self._encode_key(anthropic_key)
            }
        }
        
        with open(self.api_keys_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    
    def load_api_keys(self) -> Dict[str, str]:
        """Carga las API keys guardadas."""
        if not self.api_keys_file.exists():
            return {'openai': '', 'google': '', 'anthropic': ''}
        
        try:
            with open(self.api_keys_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            keys = config_data.get('keys', {})
            return {
                'openai': self._decode_key(keys.get('openai', '')),
                'google': self._decode_key(keys.get('google', '')),
                'anthropic': self._decode_key(keys.get('anthropic', ''))
            }
        except Exception:
            return {'openai': '', 'google': '', 'anthropic': ''}
    
    def get_api_key_status(self) -> Dict[str, bool]:
        """Retorna el estado de configuración de cada API key."""
        keys = self.load_api_keys()
        return {
            'openai': len(keys['openai']) >= 10,
            'google': len(keys['google']) >= 10,
            'anthropic': len(keys['anthropic']) >= 10
        }


class ErrorLearningSystem:
    """Sistema de aprendizaje basado en errores de generación."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.errors_file = config_manager.errors_file
    
    def log_error(self, provider: str, model: str, document_type: str, 
                  error_type: str, error_details: str, user_description: str,
                  attempted_fix: str = ""):
        """Registra un error de generación para aprendizaje futuro."""
        error_entry = {
            'id': self._generate_error_id(provider, model, error_type),
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'model': model,
            'document_type': document_type,
            'error_type': error_type,
            'error_details': error_details,
            'user_description': user_description,
            'attempted_fix': attempted_fix
        }
        
        # Cargar errores existentes
        errors = self._load_errors()
        
        # Agregar nuevo error
        errors.append(error_entry)
        
        # Mantener solo los últimos 100 errores para evitar que el archivo crezca demasiado
        if len(errors) > 100:
            errors = errors[-100:]
        
        # Guardar
        self._save_errors(errors)
    
    def log_success(self, provider: str, model: str, document_type: str, 
                   user_description: str, generated_profile: Dict[str, Any]):
        """Registra una generación exitosa para aprendizaje."""
        success_entry = {
            'id': self._generate_error_id(provider, model, 'success'),
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'model': model,
            'document_type': document_type,
            'user_description': user_description,
            'profile_structure': {
                'segmenter': generated_profile.get('segmenter', ''),
                'patterns_count': len(generated_profile.get('patterns', [])),
                'has_thresholds': 'thresholds' in generated_profile,
                'has_filters': 'filters' in generated_profile
            },
            'type': 'success'
        }
        
        # Cargar errores existentes (incluye éxitos)
        errors = self._load_errors()
        errors.append(success_entry)
        
        # Mantener solo los últimos 100 registros
        if len(errors) > 100:
            errors = errors[-100:]
        
        self._save_errors(errors)
    
    def get_learning_context(self, provider: str, document_type: str) -> str:
        """Genera contexto de aprendizaje basado en errores previos."""
        errors = self._load_errors()
        
        # Filtrar errores relevantes
        relevant_errors = [
            error for error in errors 
            if error.get('provider') == provider or error.get('document_type') == document_type
        ]
        
        if not relevant_errors:
            return ""
        
        # Agrupar errores por tipo
        error_types = {}
        successes = []
        
        for error in relevant_errors[-20:]:  # Últimos 20 registros relevantes
            if error.get('type') == 'success':
                successes.append(error)
            else:
                error_type = error.get('error_type', 'unknown')
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(error)
        
        # Generar contexto
        context_parts = []
        
        if error_types:
            context_parts.append("ERRORES COMUNES A EVITAR:")
            for error_type, error_list in error_types.items():
                if len(error_list) >= 2:  # Solo incluir errores que han ocurrido múltiples veces
                    latest_error = error_list[-1]
                    context_parts.append(f"- {error_type}: {latest_error.get('error_details', '')}")
                    if latest_error.get('attempted_fix'):
                        context_parts.append(f"  Solución: {latest_error['attempted_fix']}")
        
        if successes:
            context_parts.append("\nPATRONES EXITOSOS:")
            for success in successes[-3:]:  # Últimos 3 éxitos
                profile = success.get('profile_structure', {})
                context_parts.append(f"- Segmentador: {profile.get('segmenter', 'N/A')}")
                context_parts.append(f"  Patrones: {profile.get('patterns_count', 0)} definidos")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _generate_error_id(self, provider: str, model: str, error_type: str) -> str:
        """Genera un ID único para el error."""
        content = f"{provider}_{model}_{error_type}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _load_errors(self) -> List[Dict[str, Any]]:
        """Carga el historial de errores."""
        if not self.errors_file.exists():
            return []
        
        try:
            with open(self.errors_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_errors(self, errors: List[Dict[str, Any]]):
        """Guarda el historial de errores."""
        with open(self.errors_file, 'w', encoding='utf-8') as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de errores para debugging."""
        errors = self._load_errors()
        
        if not errors:
            return {'total': 0, 'by_type': {}, 'by_provider': {}}
        
        stats = {
            'total': len(errors),
            'by_type': {},
            'by_provider': {},
            'success_rate': 0
        }
        
        successes = 0
        for error in errors:
            # Por tipo
            error_type = error.get('error_type', error.get('type', 'unknown'))
            stats['by_type'][error_type] = stats['by_type'].get(error_type, 0) + 1
            
            # Por proveedor
            provider = error.get('provider', 'unknown')
            stats['by_provider'][provider] = stats['by_provider'].get(provider, 0) + 1
            
            # Contar éxitos
            if error.get('type') == 'success':
                successes += 1
        
        if len(errors) > 0:
            stats['success_rate'] = (successes / len(errors)) * 100
        
        return stats 