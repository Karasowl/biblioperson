# Especificación del Formato NDJSON Enriquecido para Biblioperson

Este documento detalla la estructura y los campos requeridos para los archivos NDJSON generados por el pipeline ETL de Biblioperson. Esta especificación corresponde a la Tarea #23 del proyecto.

## Estructura General

Cada línea en el archivo NDJSON representa un "segmento" de texto extraído de un documento fuente. Un segmento puede ser un párrafo, un título, una nota al pie, etc.

## Campos Detallados

La especificación del NDJSON enriquecido debe incluir, como mínimo:

### 1. Identificadores Unívocos

*   **`id_segmento`**: (UUID string) UUID único para cada segmento de texto. Generado durante el proceso ETL.
*   **`id_documento_fuente`**: (string) Identificador único para el documento original del que proviene el segmento. Puede ser un hash del archivo original o un UUID asignado al documento durante su primera ingesta.

### 2. Metadatos del Documento Fuente

Estos metadatos se replican en cada segmento para facilitar consultas y evitar joins constantes en la base de datos o al procesar el NDJSON.

*   **`ruta_archivo_original`**: (string) Ruta completa al archivo original en el sistema de archivos donde fue procesado.
*   **`hash_documento_original`**: (string) Hash (ej. SHA256) del archivo original. Útil para control de versiones y detección de duplicados.
*   **`titulo_documento`**: (string) Título del documento, extraído de los metadatos del archivo o inferido.
*   **`autor_documento`**: (string) Autor(es) del documento.
*   **`fecha_publicacion_documento`**: (string) Fecha de publicación original del documento (formato YYYY-MM-DD o YYYY).
*   **`editorial_documento`**: (string, Opcional) Editorial del documento.
*   **`isbn_documento`**: (string, Opcional) ISBN del documento.
*   **`idioma_documento`**: (string) Código ISO 639-1 (ej. "es", "en") del idioma principal del documento.
*   **`metadatos_adicionales_fuente`**: (object, Opcional) Objeto JSON para cualquier otro metadato relevante extraído del archivo fuente (ej., propiedades de DOCX, metadatos de PDF, etc.).

### 3. Metadatos del Segmento

*   **`texto_segmento`**: (string) El contenido textual del segmento.
*   **`tipo_segmento`**: (string) Vocabulario controlado que define la naturaleza del segmento. Ver lista abajo.
*   **`orden_segmento_documento`**: (integer) Número secuencial del segmento dentro del documento fuente completo (global, 0-indexed o 1-indexed a definir).
*   **`jerarquia_contextual`**: (object) Objeto JSON que describe la posición del segmento en la estructura jerárquica del documento. (Ver especificación detallada en `JERARQUIA_CONTEXTUAL_ESPECIFICACION.md`, corresponde a Tarea #26). Ejemplo: `{"capitulo": "1", "seccion": "3", "parrafo_num": "5"}`.
*   **`longitud_caracteres_segmento`**: (integer) Número de caracteres en `texto_segmento`.
*   **`embedding_vectorial`**: (array de floats, Opcional) El vector de embedding del `texto_segmento`. Puede generarse en una etapa posterior al ETL inicial.

### 4. Metadatos del Proceso ETL

*   **`timestamp_procesamiento`**: (string) Fecha y hora en formato ISO 8601 (ej. `YYYY-MM-DDTHH:MM:SSZ`) de cuando el segmento fue procesado.
*   **`version_pipeline_etl`**: (string) Versión del pipeline ETL que generó el segmento (ej. "1.2.0").
*   **`nombre_segmentador_usado`**: (string) Nombre del segmentador específico que produjo este segmento (ej. "segmentador_prosa_general_v1").

### Vocabulario Controlado para `tipo_segmento` (Inicial)

Esta lista es inicial y puede expandirse:

*   `encabezado_h1`
*   `encabezado_h2`
*   `encabezado_h3`
*   `encabezado_h4`
*   `encabezado_h5`
*   `encabezado_h6`
*   `parrafo`
*   `item_lista_ordenada`
*   `item_lista_desordenada`
*   `cita_bloque`
*   `nota_al_pie`
*   `nota_al_final`
*   `celda_tabla_encabezado`
*   `celda_tabla_dato`
*   `titulo_tabla`
*   `descripcion_figura`
*   `epigrafe`
*   `verso_poema`
*   `encabezado_pagina` (header)
*   `pie_pagina` (footer)
*   `desconocido` (para contenido que no pudo ser clasificado)

## Ejemplo de un Registro NDJSON

```json
{
  "id_segmento": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "id_documento_fuente": "sha256-deadbeefcafe00112233445566778899aabbccddeeff",
  "ruta_archivo_original": "/mnt/docs_a_procesar/filosofia/Cosmologías de India.pdf",
  "hash_documento_original": "sha256-deadbeefcafe00112233445566778899aabbccddeeff",
  "titulo_documento": "Cosmologías de India: Védica, Sāmkhya y Budista",
  "autor_documento": "Ernesto Aroldo Ceballos",
  "fecha_publicacion_documento": "2017-01-01",
  "editorial_documento": "Universidad Nacional de Córdoba",
  "isbn_documento": null,
  "idioma_documento": "es",
  "metadatos_adicionales_fuente": {"palabras_clave": ["filosofía", "india", "cosmología"], "fuente_scan": "Archivo personal del autor"},
  "texto_segmento": "El concepto de māyā es central en la Advaita Vedānta, representando la ilusión cósmica que vela la realidad última (Brahman).",
  "tipo_segmento": "parrafo",
  "orden_segmento_documento": 152,
  "jerarquia_contextual": {"capitulo": "3", "titulo_capitulo": "La No-Dualidad y la Ilusión", "subseccion": "2", "titulo_subseccion": "Māyā y la Creación Aparente", "parrafo_num": "4"},
  "longitud_caracteres_segmento": 125,
  "embedding_vectorial": null,
  "timestamp_procesamiento": "2025-05-17T18:50:00Z",
  "version_pipeline_etl": "1.2.0",
  "nombre_segmentador_usado": "segmentador_prosa_general_v1"
}
```

## Consideraciones Adicionales

*   Todos los campos de texto deben estar en UTF-8.
*   Las fechas deben seguir el formato ISO 8601 siempre que sea posible.
*   La estructura de `jerarquia_contextual` se detallará en `JERARQUIA_CONTEXTUAL_ESPECIFICACION.md`.
