# Guía de Comandos para Procesamiento de Documentos

Esta guía describe cómo utilizar los scripts de procesamiento de documentos en el proyecto Biblioperson, incluyendo cómo convertir documentos o carpetas completas a NDJSON.

## app_depuracion.py

**Ruta:** `dataset/scripts/app_depuracion.py`

### ¿Cómo funciona?

El script `app_depuracion.py` NO utiliza argumentos de línea de comandos. Todo el procesamiento se controla mediante archivos de configuración JSON:

- `jobs_config.json`: Define los trabajos a ejecutar (qué carpetas procesar, qué perfil usar, etc.).
- `content_profiles.json`: Define los perfiles de procesamiento (algoritmos, estrategias de chunking, etc.).

### ¿Cómo convertir documentos o carpetas completas a NDJSON?

1. **Configura tu trabajo en `jobs_config.json`:**
   - Especifica el `job_id`, el nombre del autor, el tipo de origen, el nombre de la carpeta de entrada (`source_directory_name`), el perfil de procesamiento (`content_profile_name`), y otros parámetros opcionales.
   - Ejemplo:

```json
[
  {
    "job_id": "ejemplo1",
    "author_name": "Autor Demo",
    "origin_type_name": "libro",
    "source_directory_name": "carpeta_a_procesar",
    "content_profile_name": "perfil_pdf",
    "enabled": true
  }
]
```

2. **Configura el perfil en `content_profiles.json`:**
   - Define el perfil de procesamiento que será referenciado en el job.

3. **Coloca los archivos a procesar en la carpeta indicada:**
   - Por ejemplo, si `source_directory_name` es `carpeta_a_procesar`, coloca los archivos en `dataset/raw_data/carpeta_a_procesar/`.

4. **Ejecuta el script:**
   - Desde la raíz del proyecto, ejecuta:

```bash
python dataset/scripts/app_depuracion.py
```

5. **Salida:**
   - Los archivos NDJSON generados se guardarán en `dataset/output/{author_name}/{origin_type_name}/{job_id}/`.

### Resumen de parámetros relevantes

- **`jobs_config.json`**
  - `job_id`: Identificador único del trabajo
  - `author_name`: Nombre del autor
  - `origin_type_name`: Tipo de origen (ej. libro, artículo)
  - `source_directory_name`: Carpeta de entrada a procesar
  - `content_profile_name`: Perfil de procesamiento a usar
  - `enabled`: Si el trabajo está habilitado

- **`content_profiles.json`**
  - Define el algoritmo, chunking, y procesamiento específico para cada tipo de documento

---

## Otros scripts

### importar_datos.py

**Ruta:** `backend/scripts/importar_datos.py`

Este script SÍ utiliza argumentos de línea de comandos para importar NDJSON a la base de datos. Consulta la sección correspondiente para detalles de uso.

---

## Resumen

- Para convertir documentos o carpetas completas a NDJSON, configura los archivos JSON y ejecuta `app_depuracion.py` sin argumentos.
- Para importar NDJSON a la base de datos, utiliza `importar_datos.py` con los argumentos adecuados.

# Banderas y Argumentos CLI de los Scripts Principales

A continuación se documentan todas las banderas (argumentos de línea de comandos) disponibles en los scripts principales de procesamiento e importación de Biblioperson. Utiliza estos argumentos para personalizar el comportamiento de cada script según tus necesidades.

---

## process_file.py (`dataset/scripts/process_file.py`)

| Bandera / Posicional         | Tipo     | Descripción                                                                 | Valor por defecto | Ejemplo de uso                                  |
|-----------------------------|----------|-----------------------------------------------------------------------------|-------------------|------------------------------------------------|
| `input_path` (posicional)   | str      | Ruta al archivo o directorio a procesar                                     | Obligatorio       | `python process_file.py carpeta/`               |
| `--list-profiles`           | bool     | Muestra los perfiles de procesamiento disponibles                           | False             | `--list-profiles`                              |
| `--profile`, `-p`           | str      | Nombre del perfil a utilizar (si se omite, se detecta automáticamente)      | None              | `--profile=poesia`                             |
| `--output`, `-o`            | str      | Ruta de salida para el archivo NDJSON generado                              | None              | `--output=salida.ndjson`                       |
| `--force-type`              | str      | Forzar tipo de documento (poemas, escritos, canciones, capitulos)           | None              | `--force-type=poemas`                          |
| `--confidence-threshold`    | float    | Umbral de confianza para segmentación automática                            | 0.5               | `--confidence-threshold=0.7`                   |
| `--verbose`, `-v`           | bool     | Muestra información de depuración detallada                                 | False             | `--verbose`                                    |
| `--profiles-dir`            | str      | Ruta a un directorio de perfiles personalizado                              | None              | `--profiles-dir=perfiles/`                     |
| `--encoding`                | str      | Codificación de caracteres del archivo de entrada                           | utf-8             | `--encoding=latin1`                            |

---

## importar_datos.py (`backend/scripts/importar_datos.py`)

| Bandera                | Tipo   | Descripción                                              | Valor por defecto         | Ejemplo de uso                       |
|------------------------|--------|----------------------------------------------------------|---------------------------|--------------------------------------|
| `--base-dir`           | str    | Directorio base del proyecto                             | (ruta base por defecto)   | `--base-dir=../`                     |
| `--contenido-dir`      | str    | Directorio con archivos a importar                       | None                      | `--contenido-dir=import/`            |
| `--db-path`            | str    | Ruta a la base de datos SQLite                           | (ruta por defecto)        | `--db-path=mi_biblioteca.db`         |
| `--ndjson-file`        | str    | Ruta al archivo NDJSON unificado para importar           | None                      | `--ndjson-file=unificado.ndjson`     |

---

## importar_completo.py (`backend/scripts/importar_completo.py`)

| Bandera / Posicional   | Tipo   | Descripción                                              | Valor por defecto | Ejemplo de uso                                 |
|-----------------------|--------|----------------------------------------------------------|-------------------|-----------------------------------------------|
| `archivo_ndjson`      | str    | Ruta al archivo NDJSON a importar (opcional)             | None              | `python importar_completo.py datos.ndjson`    |
| `--reiniciar-db`      | bool   | Reinicia la base de datos antes de importar (borra todo) | False             | `--reiniciar-db`                             |
| `--solo-importar`     | bool   | Solo importa datos, sin reiniciar la base de datos       | False             | `--solo-importar`                            |

---

## indexar_meilisearch.py (`backend/scripts/indexar_meilisearch.py`)

| Bandera                | Tipo   | Descripción                                              | Valor por defecto         | Ejemplo de uso                       |
|------------------------|--------|----------------------------------------------------------|---------------------------|--------------------------------------|
| `--tabla`              | str    | Nombre de la tabla que contiene los documentos           | None                      | `--tabla=documentos`                 |
| `--listar`             | bool   | Listar todas las tablas disponibles                      | False                     | `--listar`                           |
| `--db-path`            | str    | Ruta a la base de datos SQLite                           | (ruta por defecto)        | `--db-path=mi_biblioteca.db`         |
| `--hilos`              | int    | Número de hilos a utilizar                               | (valor por defecto)       | `--hilos=4`                          |
| `--batch-size`         | int    | Tamaño del lote de la base de datos                      | (valor por defecto)       | `--batch-size=1000`                  |
| `--docs-per-request`   | int    | Documentos por solicitud a Meilisearch                   | (valor por defecto)       | `--docs-per-request=500`             |
| `--timeout`            | int    | Timeout para solicitudes HTTP en segundos                | (valor por defecto)       | `--timeout=60`                       |

---

## limpiar_datos_duplicados.py (`backend/scripts/limpiar_datos_duplicados.py`)

| Bandera     | Tipo   | Descripción                                 | Valor por defecto | Ejemplo de uso                        |
|-------------|--------|---------------------------------------------|-------------------|---------------------------------------|
| `--db-path` | str    | Ruta a la base de datos SQLite              | Obligatorio       | `--db-path=mi_biblioteca.db`          |

---

## preparar_importacion.py (`backend/scripts/preparar_importacion.py`)

| Bandera / Posicional   | Tipo   | Descripción                                              | Valor por defecto | Ejemplo de uso                                 |
|-----------------------|--------|----------------------------------------------------------|-------------------|-----------------------------------------------|
| `archivo_ndjson`      | str    | Ruta al archivo NDJSON a preparar                        | Obligatorio       | `python preparar_importacion.py datos.ndjson`  |

---

## generador_asistido.py (`backend/scripts/generador_asistido.py`)

| Bandera / Posicional   | Tipo   | Descripción                                              | Valor por defecto | Ejemplo de uso                                 |
|-----------------------|--------|----------------------------------------------------------|-------------------|-----------------------------------------------|
| `tema`                | str    | Tema sobre el que generar contenido                      | Obligatorio       | `python generador_asistido.py "El amor"`     |
| `--tipo`, `-t`        | str    | Tipo de contenido a generar (post, articulo, etc.)       | post              | `--tipo=articulo`                             |
| `--estilo`, `-e`      | str    | Estilo de escritura (formal, conversacional, etc.)       | None              | `--estilo=formal`                             |
| `--llm`, `-l`         | str    | Modelo LLM a utilizar (gemini, openai)                   | gemini            | `--llm=openai`                                |
| `--resultados`, `-r`  | int    | Número de resultados a generar                           | (valor por defecto)| `--resultados=3`                              |
| `--solo-prompt`, `-p` | bool   | Solo mostrar el prompt generado, sin ejecutar            | False             | `--solo-prompt`                               |

---

## cli.py (`dataset/scripts/cli.py`)

| Bandera         | Tipo   | Descripción                                 | Valor por defecto | Ejemplo de uso                        |
|-----------------|--------|---------------------------------------------|-------------------|---------------------------------------|
| `--validate`    | bool   | Validar configuraciones existentes          | False             | `--validate`                          |

---

> **Nota:** Para ver todas las banderas disponibles y su descripción, ejecuta cualquier script con la opción `--help`.