#!/usr/bin/env python3
"""
Especificación de la API para generación de perfiles asistida por IA.

Este módulo define las estructuras de datos, esquemas de validación y 
tipos para la comunicación entre la UI y el backend de generación de perfiles.
"""

from typing import Dict, Any, List, Optional, Union, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path


class LLMProvider(Enum):
    """Proveedores de LLM soportados."""
    GEMINI = "gemini"
    CLAUDE = "claude"
    GPT4 = "gpt-4"
    GPT35 = "gpt-3.5"


class SegmenterType(Enum):
    """Tipos de segmentadores base disponibles."""
    AUTO = "auto"
    HEADING = "heading"
    VERSE = "verse"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"


@dataclass
class LLMConfig:
    """Configuración para el modelo de lenguaje."""
    provider: LLMProvider
    model_name: str
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 60  # segundos


@dataclass
class DocumentInfo:
    """Información del documento de ejemplo."""
    file_path: str
    file_name: str
    file_size: int  # bytes
    mime_type: str
    content_preview: str  # Primeros 500 caracteres para contexto


@dataclass
class ProfileGenerationRequest:
    """Estructura de datos para solicitud de generación de perfil."""
    
    # Datos del documento
    document: DocumentInfo
    
    # Descripción del usuario
    user_description: str
    
    # Configuración de IA
    llm_config: LLMConfig
    
    # Metadatos de la solicitud
    request_id: str
    timestamp: str
    
    # Segmentador base (opcional)
    base_segmenter: Optional[SegmenterType] = None
    
    # Configuraciones adicionales
    generate_python_code: bool = False
    profile_name_suggestion: Optional[str] = None
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización JSON."""
        data = asdict(self)
        # Convertir enums a strings
        if 'llm_config' in data and 'provider' in data['llm_config']:
            data['llm_config']['provider'] = data['llm_config']['provider'].value
        if 'base_segmenter' in data and data['base_segmenter'] is not None:
            data['base_segmenter'] = data['base_segmenter'].value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileGenerationRequest':
        """Crea instancia desde diccionario."""
        # Convertir enums
        data['llm_config']['provider'] = LLMProvider(data['llm_config']['provider'])
        if data.get('base_segmenter'):
            data['base_segmenter'] = SegmenterType(data['base_segmenter'])
        
        # Crear objetos anidados
        data['document'] = DocumentInfo(**data['document'])
        data['llm_config'] = LLMConfig(**data['llm_config'])
        
        return cls(**data)


@dataclass
class GeneratedProfile:
    """Perfil YAML generado por el LLM."""
    name: str
    description: str
    segmenter: str
    patterns: List[str]
    thresholds: Dict[str, Union[int, float]]
    metadata: Dict[str, Any]


@dataclass
class GeneratedSegmenter:
    """Código Python de segmentador personalizado (opcional)."""
    class_name: str
    code: str
    dependencies: List[str]
    description: str


@dataclass
class ProfileGenerationResponse:
    """Estructura de datos para respuesta de generación de perfil."""
    
    # Estado de la operación
    success: bool
    message: str
    
    # Metadatos de la respuesta
    request_id: str
    processing_time: float  # segundos
    llm_tokens_used: int
    
    # Datos del LLM
    llm_provider: str
    llm_model: str
    
    # Datos generados (opcionales)
    profile: Optional[GeneratedProfile] = None
    python_segmenter: Optional[GeneratedSegmenter] = None
    llm_cost: Optional[float] = None  # USD
    
    # Información de validación
    yaml_valid: bool = False
    python_valid: bool = False
    validation_errors: Optional[List[str]] = None
    llm_response_raw: Optional[str] = None  # Para debugging

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileGenerationResponse':
        """Crea instancia desde diccionario."""
        # Crear objetos anidados si existen
        if data.get('profile'):
            data['profile'] = GeneratedProfile(**data['profile'])
        if data.get('python_segmenter'):
            data['python_segmenter'] = GeneratedSegmenter(**data['python_segmenter'])
        
        return cls(**data)


@dataclass
class ErrorResponse:
    """Estructura para respuestas de error."""
    error_code: str
    error_message: str
    timestamp: str
    success: bool = False
    error_details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización JSON."""
        return asdict(self)


# Esquemas de validación para la API
API_SCHEMAS = {
    "profile_generation_request": {
        "type": "object",
        "required": ["document", "user_description", "llm_config", "request_id", "timestamp"],
        "properties": {
            "document": {
                "type": "object",
                "required": ["file_path", "file_name", "file_size", "mime_type", "content_preview"],
                "properties": {
                    "file_path": {"type": "string"},
                    "file_name": {"type": "string"},
                    "file_size": {"type": "integer", "minimum": 1},
                    "mime_type": {"type": "string"},
                    "content_preview": {"type": "string", "maxLength": 1000}
                }
            },
            "user_description": {
                "type": "string",
                "minLength": 10,
                "maxLength": 2000
            },
            "llm_config": {
                "type": "object",
                "required": ["provider", "model_name"],
                "properties": {
                    "provider": {"type": "string", "enum": ["gemini", "claude", "gpt-4", "gpt-3.5"]},
                    "model_name": {"type": "string"},
                    "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
                    "max_tokens": {"type": "integer", "minimum": 100, "maximum": 8000},
                    "timeout": {"type": "integer", "minimum": 10, "maximum": 300}
                }
            },
            "base_segmenter": {
                "type": "string",
                "enum": ["auto", "heading", "verse", "paragraph", "sentence"],
                "nullable": True
            },
            "generate_python_code": {"type": "boolean"},
            "profile_name_suggestion": {"type": "string", "nullable": True},
            "request_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "user_id": {"type": "string", "nullable": True}
        }
    },
    
    "profile_generation_response": {
        "type": "object",
        "required": ["success", "message", "request_id", "processing_time", "llm_tokens_used", "yaml_valid"],
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "profile": {
                "type": "object",
                "nullable": True,
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "segmenter": {"type": "string"},
                    "patterns": {"type": "array", "items": {"type": "string"}},
                    "thresholds": {"type": "object"},
                    "metadata": {"type": "object"}
                }
            },
            "python_segmenter": {
                "type": "object",
                "nullable": True,
                "properties": {
                    "class_name": {"type": "string"},
                    "code": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"}
                }
            },
            "request_id": {"type": "string"},
            "processing_time": {"type": "number", "minimum": 0},
            "llm_tokens_used": {"type": "integer", "minimum": 0},
            "llm_cost": {"type": "number", "minimum": 0, "nullable": True},
            "yaml_valid": {"type": "boolean"},
            "python_valid": {"type": "boolean"},
            "validation_errors": {"type": "array", "items": {"type": "string"}, "nullable": True},
            "llm_provider": {"type": "string"},
            "llm_model": {"type": "string"},
            "llm_response_raw": {"type": "string", "nullable": True}
        }
    }
}


class APIEndpoints:
    """Definición de endpoints de la API."""
    
    # Endpoint principal para generación de perfiles
    GENERATE_PROFILE = "/api/v1/profiles/generate"
    
    # Endpoints auxiliares
    VALIDATE_YAML = "/api/v1/profiles/validate-yaml"
    SAVE_PROFILE = "/api/v1/profiles/save"
    LIST_PROFILES = "/api/v1/profiles/list"
    GET_PROFILE = "/api/v1/profiles/{profile_id}"
    
    # Endpoints de configuración
    LIST_LLM_PROVIDERS = "/api/v1/config/llm-providers"
    LIST_SEGMENTERS = "/api/v1/config/segmenters"
    
    # Endpoints de estado
    HEALTH_CHECK = "/api/v1/health"
    STATUS = "/api/v1/status"


class HTTPStatusCodes:
    """Códigos de estado HTTP utilizados."""
    
    # Éxito
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    
    # Errores del cliente
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Errores del servidor
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class ErrorCodes:
    """Códigos de error específicos de la aplicación."""
    
    # Errores de validación
    INVALID_REQUEST_FORMAT = "INVALID_REQUEST_FORMAT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    
    # Errores de documento
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_TOO_LARGE = "DOCUMENT_TOO_LARGE"
    UNSUPPORTED_DOCUMENT_TYPE = "UNSUPPORTED_DOCUMENT_TYPE"
    DOCUMENT_READ_ERROR = "DOCUMENT_READ_ERROR"
    
    # Errores de LLM
    LLM_API_ERROR = "LLM_API_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_QUOTA_EXCEEDED = "LLM_QUOTA_EXCEEDED"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    
    # Errores de perfil
    PROFILE_GENERATION_FAILED = "PROFILE_GENERATION_FAILED"
    INVALID_YAML_GENERATED = "INVALID_YAML_GENERATED"
    INVALID_PYTHON_GENERATED = "INVALID_PYTHON_GENERATED"
    PROFILE_SAVE_ERROR = "PROFILE_SAVE_ERROR"
    
    # Errores del sistema
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


def create_error_response(
    error_code: str,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Función helper para crear respuestas de error."""
    from datetime import datetime
    
    return ErrorResponse(
        error_code=error_code,
        error_message=error_message,
        error_details=error_details,
        request_id=request_id,
        timestamp=datetime.now().isoformat()
    )


def validate_request_schema(data: Dict[str, Any], schema_name: str) -> List[str]:
    """
    Valida un diccionario contra un esquema definido.
    
    Args:
        data: Datos a validar
        schema_name: Nombre del esquema en API_SCHEMAS
        
    Returns:
        Lista de errores de validación (vacía si es válido)
    """
    # Implementación básica - en producción usar jsonschema
    errors = []
    
    if schema_name not in API_SCHEMAS:
        errors.append(f"Esquema '{schema_name}' no encontrado")
        return errors
    
    schema = API_SCHEMAS[schema_name]
    
    # Validar campos requeridos
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Campo requerido faltante: {field}")
    
    # Validaciones básicas adicionales se pueden agregar aquí
    
    return errors


# Ejemplo de uso y testing
if __name__ == "__main__":
    # Ejemplo de creación de request
    doc_info = DocumentInfo(
        file_path="/path/to/document.pdf",
        file_name="document.pdf",
        file_size=1024000,
        mime_type="application/pdf",
        content_preview="Este es un documento de ejemplo..."
    )
    
    llm_config = LLMConfig(
        provider=LLMProvider.GEMINI,
        model_name="gemini-pro",
        temperature=0.3,
        max_tokens=2000
    )
    
    request = ProfileGenerationRequest(
        document=doc_info,
        user_description="Extraer capítulos y secciones del documento",
        llm_config=llm_config,
        base_segmenter=SegmenterType.HEADING,
        request_id="req_123456",
        timestamp="2024-01-01T12:00:00Z"
    )
    
    # Serializar a JSON
    request_json = json.dumps(request.to_dict(), indent=2)
    print("Ejemplo de request JSON:")
    print(request_json)
    
    # Ejemplo de response
    profile = GeneratedProfile(
        name="documento_capitulos",
        description="Perfil para extraer capítulos",
        segmenter="heading",
        patterns=["Capítulo \\d+", "Sección \\d+"],
        thresholds={"min_length": 50, "confidence": 0.7},
        metadata={"generated_by": "ai", "version": "1.0"}
    )
    
    response = ProfileGenerationResponse(
        success=True,
        message="Perfil generado exitosamente",
        profile=profile,
        request_id="req_123456",
        processing_time=5.2,
        llm_tokens_used=1500,
        yaml_valid=True,
        llm_provider="gemini",
        llm_model="gemini-pro"
    )
    
    response_json = json.dumps(response.to_dict(), indent=2)
    print("\nEjemplo de response JSON:")
    print(response_json) 