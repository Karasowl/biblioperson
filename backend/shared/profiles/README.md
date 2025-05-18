# Sistema de Perfiles de Procesamiento de Documentos

Este módulo implementa un sistema modular y extensible para procesar diversos tipos de documentos (texto, JSON, DOCX, PDF, etc.) en unidades semánticas significativas mediante perfiles configurables.

## Arquitectura

La arquitectura sigue un patrón de pipeline con cuatro componentes principales:

```Documento → [LOADER] → bloques → [SEGMENTER] → unidades → [POST-PROCESSOR] → [EXPORTER] → NDJSON/DB
```

### 1. Loader

Responsable de cargar cualquier formato de archivo y convertirlo en una secuencia de bloques de texto con metadatos de formato preservados:

- Convierte documentos estructurados en bloques uniformes
- Preserva metadatos críticos (estilo, nivel de encabezado, formato, etc.)
- Hace las transformaciones formato-específicas necesarias

**Loaders disponibles:**
- `DocxLoader`: Archivos Microsoft Word (.docx)
- `txtLoader`: Archivos de texto plano (.txt, .md)
- *Próximamente:* `PdfLoader`, `JsonLoader`, etc.

### 2. Segmenter

Define qué constituye una "unidad semántica" según el perfil, aplicando reglas específicas para:

- Detectar límites de unidades (poemas, párrafos, capítulos, mensajes)
- Procesar bloques agrupándolos en unidades coherentes
- Generar metadatos adicionales (estrofas, versos, nivel jerárquico)

Implementa algoritmos como máquinas de estado para seguir los patrones definidos en `docs/ALGORITMOS_PROPUESTOS.md`.

**Segmenters disponibles:**
- `VerseSegmenter`: Detecta poemas y canciones
- `HeadingSegmenter`: Detecta estructura de libros y documentos jerárquicos
- `ParagraphSegmenter`: Detecta párrafos en artículos y textos generales
- `MessageSegmenter`: Procesa mensajes en formato JSON

### 3. Post-Processor

Aplica filtros y transformaciones genéricas a las unidades detectadas:

- Filtrado por longitud mínima
- Normalización de texto (Unicode, espacios, etc.)
- Detección de idioma
- Deduplicación
- Enriquecimiento de metadatos

### 4. Exporter

Exporta las unidades procesadas a diversos formatos:

- NDJSON (formato histórico de Biblioperson)
- SQLite
- Meilisearch
- Otros destinos configurables

## Perfiles y Configuración

Los perfiles de procesamiento se definen en archivos YAML en `profiles/`. Cada perfil especifica:

```yaml
name: poem_or_lyrics
description: "Detecta poemas y canciones en archivos de texto"
segmenter: verse
file_types: [".txt", ".md", ".docx", ".pdf"]
thresholds:
  max_verse_length: 120
  # Otros umbrales configurables
title_patterns:
  - "^# "
  # Patrones regex para detección
post_processor: text_normalizer
post_processor_config:
  min_length: 30
metadata_map:
  titulo: title
  versos: verses_count
exporter: ndjson
```

## Máquina de Estados

Los segmentadores utilizan máquinas de estado claras para modelar el procesamiento línea a línea. Por ejemplo, el `VerseSegmenter` usa los siguientes estados:

- `SEARCH_TITLE`: Buscando título de poema
- `TITLE_FOUND`: Título encontrado, esperando versos
- `COLLECTING_VERSE`: Recolectando versos
- `STANZA_GAP`: En hueco entre estrofas
- `END_POEM`: Finalizando poema actual
- `OUTSIDE_POEM`: Procesando otro tipo de contenido

## Uso

Para procesar un archivo con un perfil:

```python
from backend.shared.profiles.profile_manager import ProfileManager

# Inicializar gestor de perfiles
profile_manager = ProfileManager("/ruta/a/perfiles")

# Procesar archivo
units = profile_manager.process_file(
    file_path="mi_documento.docx",
    profile_name="poem_or_lyrics",
    output_path="resultados.ndjson"  # Opcional
)

# Acceder a unidades procesadas
for unit in units:
    print(f"Tipo: {unit['type']}")
    if unit['type'] == 'poem':
        print(f"Título: {unit.get('title')}")
        print(f"Estrofas: {unit.get('stanzas')}")
```

## Extensibilidad

El sistema está diseñado para ser fácilmente extensible:

1. **Agregar un nuevo loader**: Crear una subclase de `BaseLoader` e implementar `load()`
2. **Agregar un nuevo segmenter**: Crear una subclase de `BaseSegmenter` e implementar `segment()`
3. **Agregar un nuevo perfil**: Crear un archivo YAML en `profiles/`

## Ventajas sobre el sistema anterior

- Separación completa entre I/O, lógica y configuración
- Umbrales 100% parametrizables en YAML (no hard-code)
- Máquinas de estado explícitas en lugar de ifs anidados
- Preservación de metadatos de formato desde el origen
- Métricas de confianza para cada unidad detectada
- Pipeline modular que permite intercambiar componentes
- Fácil extensión con nuevos perfiles sin modificar código

## Próximos pasos

- Implementar `PdfLoader` con extracción de formato
- Añadir soporte para documentos HTML
- Implementar detección de idioma en post-procesador
- Crear interfaz de usuario para ajuste de perfiles 