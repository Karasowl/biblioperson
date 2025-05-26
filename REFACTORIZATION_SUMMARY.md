# Resumen de Refactorización: process_file.py y profile_manager.py

## Objetivo
Refactorizar el script `dataset/scripts/process_file.py` para mejorar su modularidad y prepararlo para ser utilizado por una futura interfaz gráfica de usuario (UI). Además, modificar `dataset/processing/profile_manager.py` para asegurar que los segmentos exportados sean instancias del dataclass `ProcessedContentItem`.

## Cambios Realizados

### 1. Nueva Función `core_process` en process_file.py
Se creó una nueva función `core_process` que encapsula la lógica principal de procesamiento de un archivo individual:

```python
def core_process(manager: ProfileManager, input_path: Path, profile_name_override: Optional[str], output_spec: Optional[str], cli_args: argparse.Namespace) -> Tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
```

**Parámetros:**
- `manager`: Instancia de ProfileManager
- `input_path`: Ruta al archivo individual que se está procesando
- `profile_name_override`: Nombre del perfil especificado por el usuario, o None para detección automática
- `output_spec`: Ruta de salida especificada por el usuario (archivo o directorio)
- `cli_args`: Objeto argparse.Namespace completo con todos los argumentos CLI

**Valor de Retorno:**
Tupla con 5 elementos:
1. `result_code`: String indicando el resultado ('SUCCESS_WITH_UNITS', 'SUCCESS_NO_UNITS', 'LOADER_ERROR', 'CONFIG_ERROR', 'PROCESSING_EXCEPTION')
2. `message`: Mensaje opcional de error o advertencia
3. `document_metadata`: Diccionario de metadatos del documento (o None)
4. `segments`: Lista de segmentos procesados (o None)
5. `segmenter_stats`: Estadísticas del segmentador (o None)

### 2. Función `_process_single_file` Refactorizada
La función original `_process_single_file` se convirtió en un wrapper de compatibilidad que:
- Llama a `core_process` internamente
- Mantiene la misma interfaz original para compatibilidad con `process_path`
- Extrae solo `result_code` y `message` del resultado de `core_process`

### 3. Transformación a ProcessedContentItem en profile_manager.py

#### 3.1. Importaciones Agregadas
```python
from datetime import datetime, timezone
import uuid
from dataset.scripts.data_models import ProcessedContentItem, BatchContext
```

#### 3.2. Nuevo Bloque de Transformación
Se agregó un bloque completo de código después de la segmentación que:

1. **Crea BatchContext** si `job_config_dict` está disponible
2. **Extrae información común** del documento para todos los segmentos
3. **Transforma cada segmento** de diccionario a `ProcessedContentItem`
4. **Maneja diferentes tipos de segmentos**:
   - `poem`: Reconstruye texto desde `numbered_verses` o `verses`
   - `section`: Procesa contenido de `HeadingSegmenter`
   - Otros tipos: Usa campo `text` directamente
5. **Genera metadatos completos** para cada segmento:
   - ID único con UUID
   - Información del documento fuente
   - Jerarquía contextual
   - Timestamp de procesamiento
   - Metadatos adicionales del job si están disponibles

#### 3.3. Actualización de Exportación
- Cambió de usar `segments` (diccionarios) a `processed_content_items` (dataclasses)
- Mantiene compatibilidad con `_export_results` que usa `dataclasses.asdict()`
- Actualiza el valor de retorno del método `process_file`

### 4. Corrección en process_file.py
Se corrigió el código de visualización de segmentos para trabajar con instancias de `ProcessedContentItem`:

```python
# Antes (con diccionarios)
text_preview = segment.get('title', segment.get('text', ''))[:50]
segment_type = segment.get('type', 'unknown')

# Después (con dataclasses)
text_preview = segment.texto_segmento[:50] if hasattr(segment, 'texto_segmento') else str(segment)[:50]
segment_type = segment.tipo_segmento if hasattr(segment, 'tipo_segmento') else 'unknown'
```

### 5. Implementación de Detección de Idioma
Se agregó detección automática de idioma usando la biblioteca `langdetect`:

#### 5.1. Nueva Dependencia
```python
from langdetect import detect, LangDetectException
```

#### 5.2. Lógica de Detección
- **Muestra de texto**: Concatena los primeros 5 bloques o hasta 1000 caracteres
- **Detección robusta**: Maneja excepciones y texto insuficiente
- **Logging detallado**: Registra el idioma detectado o razones de fallo
- **Fallback seguro**: Usa "und" (undetermined) cuando no se puede detectar

#### 5.3. Lógica de Precedencia para Idioma
El campo `idioma_documento` en `ProcessedContentItem` se asigna según esta precedencia:

1. **Job Config**: `batch_context_obj.language_code` (del `job_config_dict`)
2. **Detección automática**: `detected_lang` (usando `langdetect`)
3. **Metadatos del loader**: `document_metadata.get("idioma_documento")`
4. **Fallback**: `"und"` como último recurso

```python
if batch_context_obj and batch_context_obj.language_code not in [None, "und"]:
    idioma_doc = batch_context_obj.language_code
elif detected_lang and detected_lang != "und":
    idioma_doc = detected_lang
elif processed_document_metadata.get("idioma_documento") and processed_document_metadata.get("idioma_documento") != "und":
    idioma_doc = processed_document_metadata.get("idioma_documento")
else:
    idioma_doc = "und"
```

## Beneficios Logrados

### 1. Interfaz Limpia para UI
La función `core_process` proporciona una interfaz clara y bien definida que la UI puede usar directamente:

```python
# Ejemplo de uso desde la UI
result_code, message, metadata, segments, stats = core_process(
    manager=profile_manager,
    input_path=Path("archivo.txt"),
    profile_name_override="poem_or_lyrics",
    output_spec="/ruta/salida",
    cli_args=args_simulados
)

if result_code == 'SUCCESS_WITH_UNITS':
    # Mostrar segmentos en la UI
    for segment in segments:
        display_segment(segment)
```

### 2. Datos Estructurados
- Los segmentos ahora son instancias de `ProcessedContentItem` con estructura bien definida
- Todos los campos están tipados y documentados
- Compatibilidad completa con la especificación NDJSON
- Metadatos ricos para cada segmento

### 3. Compatibilidad CLI Preservada
- La funcionalidad de línea de comandos se mantiene completamente intacta
- `process_path` sigue funcionando igual
- `ProcessingStats` sigue siendo actualizado correctamente
- Todos los argumentos CLI funcionan como antes

### 4. Resolución del Error Original
- **Error resuelto**: `TypeError: asdict() should be called on dataclass instances`
- Los segmentos ahora son dataclasses válidos que pueden ser serializados con `dataclasses.asdict()`
- El archivo NDJSON se genera correctamente con la estructura esperada

### 5. Detección Automática de Idioma
- **Detección inteligente**: Identifica automáticamente el idioma del documento
- **Robustez**: Maneja casos edge como texto insuficiente o ambiguo
- **Precedencia clara**: Sistema de fallback bien definido para asignación de idioma
- **Logging detallado**: Facilita debugging y monitoreo de la detección

## Estructura del Código Actualizada

```
core_process()  ← Nueva función principal para UI
    ↓
_process_single_file()  ← Wrapper de compatibilidad
    ↓
process_path()  ← Maneja archivos/directorios
    ↓
main()  ← Punto de entrada CLI

ProfileManager.process_file()  ← Transformación a ProcessedContentItem
    ↓
_export_results()  ← Serialización NDJSON con dataclasses.asdict()
```

## Pruebas Realizadas

1. **Compilación**: Ambos archivos compilan sin errores
2. **Funcionalidad CLI**: `--list-profiles` y procesamiento funcionan correctamente
3. **Función core_process**: Se ejecuta y devuelve la estructura esperada
4. **Transformación de datos**: Los segmentos se convierten correctamente a `ProcessedContentItem`
5. **Exportación NDJSON**: El archivo se genera con la estructura correcta
6. **Manejo de errores**: Captura y reporta errores apropiadamente
7. **Detección de idioma**: Probada con múltiples idiomas (español, inglés, francés, alemán, italiano)
8. **Casos edge**: Verificado manejo de texto insuficiente y excepciones de `langdetect`
9. **Archivo real**: Detección exitosa en `test_prosa.txt` (detectado como español)

## Archivos Modificados

1. **`dataset/scripts/process_file.py`**:
   - Agregada función `core_process`
   - Refactorizada `_process_single_file` como wrapper
   - Corregida visualización de segmentos para dataclasses

2. **`dataset/processing/profile_manager.py`**:
   - Agregadas importaciones para `ProcessedContentItem` y `BatchContext`
   - Agregada importación de `langdetect` para detección de idioma
   - Implementado bloque de transformación completo
   - Implementada detección automática de idioma
   - Actualizada lógica de exportación
   - Modificado valor de retorno de `process_file`
   - Agregada lógica de precedencia para asignación de idioma

## Estado
✅ **Refactorización completada exitosamente**

Todas las funcionalidades están implementadas y probadas:
- `core_process` para ser utilizada por una interfaz gráfica de usuario
- `ProfileManager.process_file` genera correctamente instancias de `ProcessedContentItem`
- Detección automática de idioma implementada y funcionando
- La funcionalidad CLI existente se mantiene completamente funcional
- El error de serialización NDJSON está resuelto
- Sistema robusto de precedencia para asignación de idioma

## Dependencias Nuevas
- **`langdetect`**: Para detección automática de idioma
  - Instalación: `pip install langdetect`
  - Manejo robusto de excepciones incluido 