# Guía de Gestión de Datos para Biblioperson

**Última actualización:** (dd-mm-aaaa)

## Índice

- [Guía de Gestión de Datos para Biblioperson](#guía-de-gestión-de-datos-para-biblioperson)
  - [Índice](#índice)
  - [Introducción](#introducción)
  - [1. Preparación Inicial de la Base de Datos](#1-preparación-inicial-de-la-base-de-datos)
    - [1.1. Creación e Inicialización de la Base de Datos (SQLite)](#11-creación-e-inicialización-de-la-base-de-datos-sqlite)
  - [2. Proceso de Importación de Contenidos](#2-proceso-de-importación-de-contenidos)
    - [2.1. Formato y Ubicación de los Archivos de Entrada](#21-formato-y-ubicación-de-los-archivos-de-entrada)
    - [2.2. Ejecución del Script de Importación (`importar_completo.py`)](#22-ejecución-del-script-de-importación-importar_completopy)
      - [2.2.1. Opciones del Script](#221-opciones-del-script)
    - [2.3. Verificación de la Importación](#23-verificación-de-la-importación)
  - [3. Generación de Embeddings Semánticos](#3-generación-de-embeddings-semánticos)
    - [3.1. Procesamiento de Nuevos Contenidos (`procesar_semantica.py`)](#31-procesamiento-de-nuevos-contenidos-procesar_semanticapy)
    - [3.2. Regeneración Completa de Todos los Embeddings](#32-regeneración-completa-de-todos-los-embeddings)
      - [3.2.1. Pasos para la Regeneración](#321-pasos-para-la-regeneración)
  - [4. Consultas y Verificación Directa en la Base de Datos](#4-consultas-y-verificación-directa-en-la-base-de-datos)
    - [4.1. Acceso a la Terminal de SQLite](#41-acceso-a-la-terminal-de-sqlite)
    - [4.2. Ejemplos de Consultas Útiles](#42-ejemplos-de-consultas-útiles)
  - [5. Preguntas Frecuentes sobre Gestión de Datos](#5-preguntas-frecuentes-sobre-gestión-de-datos)

---

## Introducción

Esta guía detalla los procedimientos para la gestión de datos dentro del proyecto Biblioperson. Cubre desde la configuración inicial de la base de datos, la importación de contenido desde archivos fuente, hasta la generación de embeddings semánticos necesarios para la búsqueda avanzada.

---

## 1. Preparación Inicial de la Base de Datos

### 1.1. Creación e Inicialización de la Base de Datos (SQLite)
Biblioperson utiliza SQLite como su base de datos, la cual se almacena en un archivo local.

* **Ubicación del archivo de base de datos:** `backend/data/biblioteca.db`

Si la base de datos no existe o necesitas recrear su estructura (tablas, índices, etc.) desde cero, puedes utilizar el script de inicialización:

1.  Navega a la carpeta de scripts del backend:
    ```bash
    cd backend/scripts
    ```
2.  Ejecuta el script de inicialización:
    ```bash
    python inicializar_db.py
    ```
    Este script creará el archivo `biblioteca.db` (si no existe) y definirá el esquema necesario (tablas como `contenidos`, `contenido_embeddings`, `autores`, etc.).
    **Advertencia:** Si la base de datos ya existe y contiene datos, ejecutar este script podría borrar las tablas existentes y recrearlas vacías, dependiendo de su implementación. Revisa el contenido del script `inicializar_db.py` para entender su comportamiento exacto con bases de datos preexistentes.

---

## 2. Proceso de Importación de Contenidos

Los contenidos se importan a Biblioperson a partir de archivos en formato NDJSON (Newline Delimited JSON). Estos archivos NDJSON son el resultado del procesamiento realizado por los scripts en la carpeta `dataset/scripts/` (como `app_depuracion.py`).

### 2.1. Formato y Ubicación de los Archivos de Entrada
* **Formato Esperado:** Archivos `.ndjson` donde cada línea es un objeto JSON que representa un fragmento de contenido con sus metadatos (ej. `id`, `texto_original`, `autor`, `fuente`, `fecha_creacion`, etc.).
* **Ubicación Predeterminada para Importación:**
    Los scripts de importación pueden buscar archivos NDJSON en la siguiente carpeta:
    `backend/data/import/`
    Puedes colocar tus archivos `.ndjson` directamente aquí.

### 2.2. Ejecución del Script de Importación (`importar_completo.py`)
El script principal para importar los datos desde los archivos NDJSON a la base de datos SQLite es `importar_completo.py`.

1.  Navega a la carpeta de scripts del backend:
    ```bash
    cd backend/scripts
    ```
2.  Ejecuta el script `importar_completo.py` con las opciones adecuadas:

#### 2.2.1. Opciones del Script

* **Importar archivos desde la carpeta `backend/data/import/`:**
    Si ya has colocado tus archivos NDJSON en la carpeta de importación predeterminada.
    ```bash
    python importar_completo.py --solo-importar
    ```
* **Importar un archivo NDJSON específico (copiándolo a la carpeta de importación):**
    Si tu archivo NDJSON unificado está en otra ubicación, este comando lo copiará primero a `backend/data/import/` y luego lo procesará.
    ```bash
    python importar_completo.py /ruta/completa/a/tu/archivo.ndjson
    ```
* **Reiniciar la base de datos antes de importar:**
    **¡Advertencia! Esta opción borrará todos los datos existentes en las tablas relevantes** antes de realizar la nueva importación. Útil si quieres empezar desde cero.
    ```bash
    python importar_completo.py /ruta/completa/a/tu/archivo.ndjson --reiniciar-db
    ```
    También puedes usar `--reiniciar-db` con `--solo-importar` si los archivos ya están en la carpeta de importación:
    ```bash
    python importar_completo.py --solo-importar --reiniciar-db
    ```
    El script se encargará de leer los archivos NDJSON, procesar cada registro e insertarlo en las tablas correspondientes de la base de datos SQLite. Los scripts están diseñados para añadir solo nuevos registros si no se especifica `--reiniciar-db`, evitando duplicados si un contenido con el mismo ID ya existe.

### 2.3. Verificación de la Importación
* Revisa los mensajes y logs generados por el script en la consola para confirmar que la importación se completó sin errores.
* Puedes realizar consultas directas a la base de datos (ver sección 4) para verificar que los datos se han cargado correctamente.

---

## 3. Generación de Embeddings Semánticos

Una vez que los contenidos textuales están en la base de datos SQLite, es necesario generar los embeddings vectoriales para habilitar la búsqueda semántica.

### 3.1. Procesamiento de Nuevos Contenidos (`procesar_semantica.py`)
El script `procesar_semantica.py` se encarga de generar estos embeddings.

1.  Asegúrate de estar en la carpeta `backend/scripts/`.
2.  Ejecuta el script:
    ```bash
    python procesar_semantica.py
    ```
* **Comportamiento:** Este script está diseñado para ser eficiente. Por defecto, solo procesará aquellos contenidos en la tabla `contenidos` que aún no tengan un embedding asociado en la tabla `contenido_embeddings`. Esto significa que puedes ejecutarlo después de cada importación para generar embeddings únicamente para los datos nuevos.

### 3.2. Regeneración Completa de Todos los Embeddings
Puede haber situaciones en las que necesites regenerar los embeddings para *todos* los contenidos almacenados, por ejemplo:
* Si cambias el modelo de `sentence-transformers` utilizado para generar los embeddings.
* Si detectas problemas o inconsistencias en los embeddings existentes.
* Después de una limpieza o modificación significativa de los textos base.

#### 3.2.1. Pasos para la Regeneración

1.  **Vaciar la Tabla de Embeddings:**
    La forma más directa de forzar la regeneración es eliminar todos los registros existentes en la tabla `contenido_embeddings`. Puedes hacerlo conectándote a la base de datos SQLite (ver sección 4.1) y ejecutando el siguiente comando SQL:
    ```sql
    DELETE FROM contenido_embeddings;
    ```
    Alternativamente, si el script `inicializar_db.py` o algún otro script de mantenimiento ofrece una opción para vaciar o recrear específicamente la tabla `contenido_embeddings` sin afectar otros datos, podrías usarlo. Una opción más drástica (si el esquema lo permite y no hay dependencias complejas) sería:
    ```sql
    DROP TABLE IF EXISTS contenido_embeddings;
    ```
    Y luego recrear la tabla con su estructura original (a menudo, `inicializar_db.py` o un script similar de "inicialización semántica" se encargaría de recrearla si no existe).

2.  **Ejecutar el Script de Procesamiento Semántico:**
    Una vez que la tabla `contenido_embeddings` está vacía, ejecuta el script como de costumbre:
    ```bash
    python procesar_semantica.py
    ```
    Dado que no encontrará embeddings existentes, procesará todos los contenidos de la tabla `contenidos`.

* **Nota Importante sobre el Tiempo de Procesamiento:** La generación de embeddings es una tarea computacionalmente intensiva. Regenerar embeddings para una gran cantidad de contenidos puede llevar un tiempo considerable (desde minutos hasta varias horas), dependiendo del volumen de datos, la potencia de tu CPU/GPU y el modelo de embedding utilizado.

---

## 4. Consultas y Verificación Directa en la Base de Datos

Puedes interactuar directamente con la base de datos SQLite para verificar datos, realizar consultas de diagnóstico o llevar a cabo tareas de mantenimiento manuales.

### 4.1. Acceso a la Terminal de SQLite
1.  Abre una terminal o línea de comandos.
2.  Navega al directorio donde se encuentra tu archivo de base de datos (`backend/data/`).
3.  Ejecuta el cliente de línea de comandos de SQLite:
    ```bash
    sqlite3 biblioteca.db
    ```
    (Si `sqlite3` no está en tu PATH, puede que necesites especificar la ruta completa al ejecutable de `sqlite3` o instalarlo).
    Esto te abrirá el prompt de SQLite (`sqlite>`).

### 4.2. Ejemplos de Consultas Útiles
Una vez dentro del prompt de SQLite, puedes ejecutar comandos SQL. Algunos ejemplos:

* **Listar todas las tablas:**
    ```sql
    .tables
    ```
* **Ver el esquema de una tabla (ej. `contenidos`):**
    ```sql
    .schema contenidos
    ```
* **Contar todos los registros en la tabla `contenidos`:**
    ```sql
    SELECT COUNT(*) FROM contenidos;
    ```
* **Ver los primeros 5 registros de la tabla `contenidos`:**
    ```sql
    SELECT id, texto_original, autor FROM contenidos LIMIT 5;
    ```
* **Contar cuántos contenidos tienen embeddings generados:**
    ```sql
    SELECT COUNT(DISTINCT contenido_id) FROM contenido_embeddings;
    ```
* **Listar autores únicos:**
    ```sql
    SELECT DISTINCT autor FROM contenidos WHERE autor IS NOT NULL AND autor != '';
    ```
* **Contar contenidos por autor:**
    ```sql
    SELECT autor, COUNT(*) AS total_contenidos FROM contenidos GROUP BY autor ORDER BY total_contenidos DESC;
    ```
* **Salir de la terminal de SQLite:**
    ```sql
    .quit
    ```

---

## 5. Preguntas Frecuentes sobre Gestión de Datos

* **¿Puedo importar nuevos datos sin perder los anteriores?**
    Sí. Por defecto, el script `importar_completo.py` está diseñado para añadir nuevos registros y actualizar los existentes si se encuentran por ID, pero no para borrar datos a menos que se use la opción `--reiniciar-db`.

* **¿Dónde deben estar los archivos de importación NDJSON?**
    La ubicación predeterminada que el script `importar_completo.py` puede usar (con la opción `--solo-importar`) es `backend/data/import/`. Si proporcionas una ruta a un archivo NDJSON, el script también puede manejarlo.

* **¿Cómo sé si los embeddings están actualizados para los nuevos contenidos?**
    El script `procesar_semantica.py` está diseñado para procesar únicamente aquellos contenidos que aún no tienen un embedding generado. Simplemente ejecútalo después de una importación para poner al día los embeddings.