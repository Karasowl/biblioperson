# Configuración del Procesamiento de Documentos (`app_depuracion.py`)

El script `app_depuracion.py` ubicado en `dataset/scripts/` es el motor principal para procesar documentos y convertirlos al formato NDJSON estándar de Biblioperson. Este script no utiliza argumentos de línea de comandos tradicionales. En su lugar, se configura a través de dos archivos JSON principales: `jobs_config.json` y `content_profiles.json`, ambos ubicados en `dataset/config/`.

## 1. `jobs_config.json`

Este archivo define una lista de "trabajos" (jobs) de procesamiento. Cada objeto en el array representa un conjunto de documentos a procesar con una configuración específica.

**Ubicación**: `e:\dev-projects\biblioperson\dataset\config\jobs_config.json`

**Esquema**: `e:\dev-projects\biblioperson\dataset\config\schema\jobs_config.schema.json`

### Parámetros por Job:

| Parámetro                   | Tipo                          | Obligatorio | Descripción                                                                                                                               |
|-----------------------------|-------------------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `job_id`                    | `string`                      | ✅           | Identificador único para el trabajo (e.g., "autor_ensayos_01").                                                                         |
| `author_name`               | `string`                      | ✅           | Nombre del autor para este trabajo. Se usará para organizar los archivos de salida.                                                       |
| `language_code`             | `string`                      | ✅           | Código de idioma principal del contenido (e.g., 'es', 'en').                                                                              |
| `source_directory_name`     | `string`                      | ✅           | Nombre del subdirectorio dentro de `dataset/raw_data/` que contiene los archivos fuente para este trabajo (e.g., "mi_autor/libros_pdf"). |
| `content_profile_name`      | `string`                      | ✅           | Nombre del perfil de contenido (definido en `content_profiles.json`) a utilizar para este trabajo.                                        |
| `origin_type_name`          | `string`                      | ✅           | Nombre descriptivo para el tipo de origen del contenido (e.g., "Telegram Export", "Libros Escaneados").                                   |
| `acquisition_date`          | `string` (YYYY-MM-DD) / `null`| ❌           | Fecha en que se adquirió el material fuente. Opcional.                                                                                    |
| `force_null_publication_date`| `boolean`                     | ❌           | Si es `true`, fuerza que `publication_date` sea `null` en los metadatos, ignorando cualquier fecha extraída. Por defecto es `false`.        |
| `filter_rules`              | `array` / `null`              | ❌           | Reglas de filtrado específicas para contenido de tipo `json_like` (ver `content_profiles.json`). Opcional.                               |
| `job_specific_metadata`     | `object` / `null`             | ❌           | Cualquier otro metadato específico del trabajo que pueda ser útil. Opcional.                                                              |

**Ejemplo de `jobs_config.json`**:

```json
[
  {
    "job_id": "prueba_docx_headings_01",
    "author_name": "autor_prueba",
    "language_code": "es",
    "source_directory_name": "autor_prueba/documentos_generales",
    "content_profile_name": "perfil_docx_heading",
    "origin_type_name": "documentos_generales",
    "acquisition_date": null,
    "force_null_publication_date": false
  }
]
```

## 2. `content_profiles.json`

Este archivo define diferentes "perfiles de contenido". Cada perfil especifica cómo se deben procesar los archivos según su formato y tipo de contenido. El `content_profile_name` en `jobs_config.json` hace referencia a una clave en este archivo.

**Ubicación**: `e:\dev-projects\biblioperson\dataset\config\content_profiles.json`

**Esquema**: `e:\dev-projects\biblioperson\dataset\config\schema\content_profiles.schema.json`

### Estructura de un Perfil de Contenido:

Cada clave de primer nivel en `content_profiles.json` es un nombre de perfil (e.g., `"perfil_docx_heading"`). El valor es un objeto con los siguientes parámetros:

| Parámetro                 | Tipo                                      | Obligatorio | Descripción                                                                                                                                                              |
|---------------------------|-------------------------------------------|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `description`             | `string`                                  | ✅           | Descripción legible del perfil.                                                                                                                                          |
| `source_format_group`     | `string` (enum)                           | ✅           | Grupo general del formato fuente: `"document"` (DOCX, PDF, TXT), `"text_plain"`, `"json_like"` (JSON, NDJSON).                                                              |
| `content_kind`            | `string` (enum)                           | ✅           | Tipo de contenido que maneja el perfil: `"prose"` (libros, artículos), `"messages"` (chats), `"reference_material"`, `"poetry"`, `"structured_data"`.                     |
| `parser_config`           | `object` / `null`                         | ❌           | Configuración para el parseo si `source_format_group` es `"json_like"`. Nulo para otros tipos. Contiene sub-parámetros como `json_item_prefix_ijson`, `text_property_paths`, etc. |
| `converter_config`        | `object` / `null`                         | ❌           | Configuración para la conversión de archivos (e.g., opciones de Pandoc para DOCX a Markdown, encoding de texto). Nulo si no aplica.                                          |
| `chunking_strategy_name`  | `string`                                  | ✅           | Nombre de la clase de la estrategia de segmentación (ChunkingStrategy) a utilizar (e.g., `"ParagraphChunkerStrategy"`).                                                  |
| `chunking_config`         | `object`                                  | ❌           | Configuración específica para la estrategia de segmentación elegida (e.g., `{"min_chunk_size": 10}`).                                                                     |
| `post_chunk_processors`   | `array` de `string`                       | ❌           | Lista de nombres de funciones de post-procesamiento que se aplicarán después de la segmentación.                                                                           |

**Ejemplo de `content_profiles.json`**:

```json
{
  "perfil_docx_heading": {
    "description": "Procesa archivos DOCX usando DocxLoader y HeadingSegmenter",
    "source_format_group": "document",
    "content_kind": "prose",
    "chunking_strategy_name": "ParagraphChunkerStrategy",
    "chunking_config": {
      "min_chunk_size": 10
    }
  }
}
```

## Flujo de Configuración:

1.  El script `app_depuracion.py` lee `jobs_config.json`.
2.  Para cada "job" habilitado:
    *   Identifica el `source_directory_name` para encontrar los archivos de entrada.
    *   Utiliza el `content_profile_name` para buscar la configuración detallada en `content_profiles.json`.
    *   Aplica las estrategias de parseo, conversión y segmentación definidas en el perfil de contenido a los archivos del job.
    *   Guarda los resultados en un subdirectorio dentro de `dataset/output/` estructurado por `author_name`, `origin_type_name` y `job_id`.

Para modificar el comportamiento del procesamiento, se deben editar estos archivos JSON en lugar de pasar argumentos al script. Consulte los esquemas (`*.schema.json`) para obtener detalles completos sobre todos los campos y valores permitidos.