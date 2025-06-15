# Guía Técnica del Sistema de Deduplicación de Biblioperson

## 📖 Índice

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Componentes Principales](#componentes-principales)
3. [Configuración](#configuración)
4. [API de Programación](#api-de-programación)
5. [Base de Datos](#base-de-datos)
6. [Modos de Salida](#modos-de-salida)
7. [Manejo de Errores](#manejo-de-errores)
8. [Rendimiento](#rendimiento)
9. [Troubleshooting](#troubleshooting)

## 🏗️ Arquitectura del Sistema

### Visión General

El sistema de deduplicación de Biblioperson está diseñado con una arquitectura modular que permite:

- **Integración opcional**: Puede habilitarse/deshabilitarse sin afectar el pipeline existente
- **Configuración granular**: Control fino sobre comportamiento y rendimiento
- **Múltiples interfaces**: CLI, API REST, y UI web
- **Fallbacks robustos**: Continúa funcionando aunque componentes fallen

### Principios de Diseño

1. **Opcional por Defecto**: No interrumpe flujos existentes
2. **Configuración Externa**: Comportamiento controlado por archivos YAML
3. **Manejo de Errores Graceful**: Continúa procesamiento en caso de fallos
4. **Performance Optimizada**: Hash incremental, cache en memoria
5. **Compatibilidad Retroactiva**: Funciona con código existente

## 🔧 Componentes Principales

### 1. DeduplicationManager (`dataset/processing/deduplication.py`)

**Responsabilidades:**
- Cálculo de hashes SHA-256
- Gestión de base de datos SQLite
- Detección de duplicados
- Estadísticas y reportes

**Métodos Principales:**

```python
class DeduplicationManager:
    def compute_sha256(self, file_path: Union[str, Path]) -> str:
        """Calcula hash SHA-256 de un archivo usando chunks eficientes."""
        
    def check_and_register(self, file_path: Union[str, Path], title: str = None) -> Tuple[str, bool]:
        """Verifica si es duplicado y registra si es nuevo."""
        
    def get_duplicate_info(self, document_hash: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de un documento duplicado."""
        
    def list_documents(self, search: str = None, before: str = None, after: str = None) -> List[Dict[str, Any]]:
        """Lista documentos con filtros opcionales."""
        
    def remove_by_hash(self, document_hash: str) -> bool:
        """Elimina documento por hash."""
        
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de datos."""
```

### 2. OutputModeSerializer (`dataset/processing/output_modes.py`)

**Responsabilidades:**
- Serialización diferenciada por modo
- Exportación a JSON/NDJSON
- Filtrado de campos según configuración

**Modos Disponibles:**

```python
class OutputMode(Enum):
    GENERIC = "generic"      # NDJSON simple para IAs
    BIBLIOPERSON = "biblioperson"  # NDJSON enriquecido completo
```

### 3. DedupConfigManager (`dataset/processing/dedup_config.py`)

**Responsabilidades:**
- Carga de configuración desde YAML
- Validación de parámetros
- Acceso centralizado a configuración

**Configuración Principal:**

```python
@dataclass
class DeduplicationConfig:
    enabled: bool = True
    default_output_mode: str = "biblioperson"
    database_path: str = "dataset/data/deduplication.db"
    continue_on_error: bool = True
    log_errors: bool = True
    warn_when_disabled: bool = False
```

### 4. API REST (`dataset/processing/dedup_api.py`)

**Endpoints Disponibles:**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/dedup` | Listar documentos con filtros |
| DELETE | `/api/dedup/{hash}` | Eliminar por hash |
| DELETE | `/api/dedup/path` | Eliminar por ruta |
| POST | `/api/dedup/clear` | Limpiar todos |
| POST | `/api/dedup/prune` | Eliminar por fecha |
| GET | `/api/dedup/stats` | Estadísticas |
| DELETE | `/api/dedup/batch` | Eliminación por lotes |

## ⚙️ Configuración

### Archivo Principal: `dataset/config/deduplication_config.yaml`

```yaml
# Configuración principal
deduplication:
  enabled: true
  default_output_mode: "biblioperson"
  database_path: "dataset/data/deduplication.db"
  
  error_handling:
    continue_on_error: true
    log_errors: true
    warn_when_disabled: false

# Configuración de modos de salida
output_modes:
  generic:
    description: "Salida NDJSON simple sin metadatos adicionales"
    enable_deduplication: false
    included_fields:
      - "segment_id"
      - "document_id"
      - "text"
      - "segment_type"
      - "segment_order"
      - "text_length"
      - "processing_timestamp"
      - "source_file_path"
      - "document_title"
      - "document_author"
      - "document_language"
      - "pipeline_version"
      - "segmenter_used"
  
  biblioperson:
    description: "Salida NDJSON enriquecida con metadatos completos"
    enable_deduplication: true
    included_fields: "all"
    include_document_hash: true

# Configuración de compatibilidad
compatibility:
  supported_profiles:
    - "json"
    - "prosa"
    - "verso"
    - "automático"
  
  supported_file_formats:
    - ".pdf"
    - ".docx"
    - ".txt"
    - ".md"
    - ".json"
    - ".ndjson"

# Configuración de rendimiento
performance:
  hash_chunk_size: 8192
  operation_timeout: 30
  enable_hash_cache: true
  max_cache_size: 1000
```

### Configuración Programática

```python
from dataset.processing.dedup_config import get_config_manager

# Obtener configuración
config_manager = get_config_manager()

# Verificar si está habilitado
if config_manager.is_deduplication_enabled():
    print("Deduplicación habilitada")

# Verificar para modo específico
if config_manager.is_deduplication_enabled_for_mode("biblioperson"):
    print("Deduplicación habilitada para modo biblioperson")

# Obtener configuración detallada
dedup_config = config_manager.get_deduplication_config()
print(f"Base de datos: {config_manager.get_database_path()}")
```

## 🗄️ Base de Datos

### Esquema SQLite

```sql
CREATE TABLE IF NOT EXISTS documents (
    hash TEXT PRIMARY KEY,           -- SHA-256 del archivo
    file_path TEXT NOT NULL,         -- Ruta completa del archivo
    title TEXT,                      -- Título extraído o nombre base
    first_seen TEXT NOT NULL,        -- Timestamp ISO-8601 UTC
    file_size INTEGER,               -- Tamaño en bytes
    last_modified TEXT               -- Última modificación del archivo
);

CREATE INDEX IF NOT EXISTS idx_documents_first_seen ON documents(first_seen);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
```

### Ubicación por Defecto

- **Desarrollo**: `dataset/.cache/dedup_registry.sqlite`
- **Producción**: Configurable en `deduplication_config.yaml`

### Operaciones Principales

```python
# Inicializar gestor
from dataset.processing.deduplication import get_dedup_manager
dedup_manager = get_dedup_manager()

# Verificar duplicado
hash_value, is_new = dedup_manager.check_and_register("/path/to/file.pdf")

if not is_new:
    duplicate_info = dedup_manager.get_duplicate_info(hash_value)
    print(f"Duplicado detectado: {duplicate_info['first_seen']}")

# Listar con filtros
documents = dedup_manager.list_documents(
    search="novela",
    after="2025-01-01T00:00:00Z"
)

# Estadísticas
stats = dedup_manager.get_stats()
print(f"Total documentos: {stats['total_documents']}")
```

## 📤 Modos de Salida

### Modo Generic

**Propósito**: Alimentar sistemas de IA y procesamiento simple

**Características:**
- Campos mínimos esenciales
- Sin deduplicación
- Estructura ligera
- Ideal para LLMs

**Ejemplo de Salida:**

```json
{
  "segment_id": "doc_001_seg_001",
  "document_id": "doc_001",
  "text": "Este es el contenido del segmento...",
  "segment_type": "paragraph",
  "segment_order": 1,
  "text_length": 156,
  "processing_timestamp": "2025-06-14T22:45:19.823Z",
  "source_file_path": "/path/to/document.pdf",
  "document_title": "Mi Documento",
  "document_author": "Autor Desconocido",
  "document_language": "es",
  "pipeline_version": "1.0.0",
  "segmenter_used": "HeadingSegmenter"
}
```

### Modo Biblioperson

**Propósito**: Sistema completo con trazabilidad y deduplicación

**Características:**
- Todos los metadatos disponibles
- Deduplicación activa
- Hash del documento incluido
- Trazabilidad completa

**Ejemplo de Salida:**

```json
{
  "segment_id": "doc_001_seg_001",
  "document_id": "doc_001",
  "document_language": "es",
  "text": "Este es el contenido del segmento...",
  "segment_type": "paragraph",
  "segment_order": 1,
  "text_length": 156,
  "processing_timestamp": "2025-06-14T22:45:19.823Z",
  "source_file_path": "/path/to/document.pdf",
  "document_title": "Mi Documento",
  "document_author": "Autor Desconocido",
  "additional_metadata": {
    "document_hash": "a1b2c3d4e5f6...",
    "file_size": 1024576,
    "extraction_method": "pymupdf",
    "corruption_detected": false,
    "author_detection_confidence": 0.85,
    "language_detection_confidence": 0.95
  },
  "pipeline_version": "1.0.0",
  "segmenter_used": "HeadingSegmenter"
}
```

## 🚨 Manejo de Errores

### Estrategias de Recuperación

1. **Continue on Error**: Continúa procesamiento sin deduplicación
2. **Fallback Export**: Usa exportación tradicional si falla sistema de modos
3. **Graceful Degradation**: Desactiva funciones problemáticas automáticamente

### Configuración de Errores

```yaml
deduplication:
  error_handling:
    continue_on_error: true      # Continuar si falla deduplicación
    log_errors: true             # Registrar errores en logs
    warn_when_disabled: false    # Advertir cuando esté deshabilitado
```

### Códigos de Error Comunes

| Código | Descripción | Acción Recomendada |
|--------|-------------|-------------------|
| `DEDUP_001` | Base de datos no accesible | Verificar permisos y ruta |
| `DEDUP_002` | Error calculando hash | Verificar archivo existe y es legible |
| `DEDUP_003` | Configuración inválida | Revisar `deduplication_config.yaml` |
| `DEDUP_004` | Timeout en operación | Aumentar `operation_timeout` |

## ⚡ Rendimiento

### Optimizaciones Implementadas

1. **Hash Incremental**: Lectura en chunks de 8KB
2. **Cache en Memoria**: Hashes recientes en RAM
3. **Índices de Base de Datos**: Búsquedas optimizadas
4. **Lazy Loading**: Carga bajo demanda

### Configuración de Performance

```yaml
performance:
  hash_chunk_size: 8192          # Tamaño de chunk para hash (bytes)
  operation_timeout: 30          # Timeout para operaciones (segundos)
  enable_hash_cache: true        # Cache de hashes en memoria
  max_cache_size: 1000          # Máximo de hashes en cache
```

### Benchmarks

| Operación | Archivo 1MB | Archivo 10MB | Archivo 100MB |
|-----------|-------------|--------------|---------------|
| Cálculo Hash | ~5ms | ~45ms | ~450ms |
| Consulta DB | ~1ms | ~1ms | ~1ms |
| Registro Nuevo | ~2ms | ~2ms | ~2ms |

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Deduplicación No Funciona

**Síntomas:**
- Documentos duplicados no se detectan
- No aparecen mensajes de duplicados en logs

**Soluciones:**
```python
# Verificar configuración
from dataset.processing.dedup_config import get_config_manager
config = get_config_manager()

print(f"Habilitado: {config.is_deduplication_enabled()}")
print(f"Modo biblioperson: {config.is_deduplication_enabled_for_mode('biblioperson')}")

# Verificar base de datos
from dataset.processing.deduplication import get_dedup_manager
dedup = get_dedup_manager()
stats = dedup.get_stats()
print(f"Documentos registrados: {stats['total_documents']}")
```

#### 2. Error de Permisos en Base de Datos

**Síntomas:**
- `PermissionError` al acceder SQLite
- Logs muestran errores de escritura

**Soluciones:**
```bash
# Verificar permisos del directorio
ls -la dataset/data/

# Crear directorio si no existe
mkdir -p dataset/data/

# Dar permisos de escritura
chmod 755 dataset/data/
```

#### 3. Performance Lenta

**Síntomas:**
- Procesamiento muy lento con deduplicación
- Timeouts frecuentes

**Soluciones:**
```yaml
# Optimizar configuración
performance:
  hash_chunk_size: 16384    # Duplicar tamaño de chunk
  operation_timeout: 60     # Aumentar timeout
  enable_hash_cache: true   # Asegurar cache habilitado
  max_cache_size: 2000     # Aumentar tamaño de cache
```

### Herramientas de Diagnóstico

#### Validar Sistema Completo

```python
from dataset.processing.profile_manager import ProfileManager

pm = ProfileManager()

# Validar compatibilidad
compatibility = pm.validate_pipeline_compatibility()
print("Compatibilidad:", compatibility)

# Estado de deduplicación
status = pm.get_deduplication_status()
print("Estado:", status)
```

#### Logs Detallados

```python
import logging

# Habilitar logs detallados
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('dataset.processing')
logger.setLevel(logging.DEBUG)
```
 