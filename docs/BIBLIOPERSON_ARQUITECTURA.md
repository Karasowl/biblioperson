# Arquitectura del Proyecto Biblioperson

**Última actualización:** (dd-mm-aaaa)

## Introducción

Este documento describe en detalle la arquitectura del proyecto "Biblioperson". Su propósito es servir como referencia técnica centralizada para el equipo de desarrollo y para la asistencia de Inteligencia Artificial (IA) en tareas de desarrollo, depuración y optimización. Proporciona una comprensión profunda de los componentes del sistema, sus interacciones, las tecnologías empleadas y los flujos de datos.

---

## 1. Visión General del Proyecto

### 1.1. Nombre del Proyecto
Biblioperson

### 1.2. Objetivo Fundamental (Visión a Largo Plazo)
Crear una aplicación robusta que permita a los usuarios realizar búsquedas exhaustivas (tanto por palabras clave como semánticas) dentro de una vasta colección de textos indexados. Estos textos pueden provenir de diversos autores y formatos de archivo (Word, TXT, PDF, Markdown, etc.).

La finalidad última es:
* Poder interrogar la base de conocimiento para entender qué podría pensar un autor específico sobre un tema determinado.
* Analizar qué se puede inferir de la biblioteca completa de autores sobre un tema particular.
* Facilitar la creación de contenido original y atractivo para redes sociales, partiendo de las ideas fundamentales encontradas, adaptando el estilo para maximizar el *engagement* y el crecimiento de seguidores.

### 1.3. Objetivo de la Fase Actual de Desarrollo (Enfoque Inmediato)
* Lograr que la aplicación permita búsquedas efectivas por palabras y frases exactas en todo el corpus de contenido indexado.
* Asegurar que el proceso de indexación pueda manejar de manera inteligente diversos tipos de documentos alojados en una estructura de carpetas, identificando elementos estructurales como títulos, poemas, canciones, o párrafos dentro de capítulos de libros.
* Implementar búsquedas rápidas y, crucialmente, búsquedas semánticas donde el significado y la intención de la búsqueda prevalezcan sobre la coincidencia literal de palabras.

---

## 2. Pila Tecnológica Principal

* **Backend:** Python 3.8+, Flask (para la API REST).
* **Frontend:** React, Vite, JavaScript/TypeScript, Tailwind CSS (para la Interfaz de Usuario SPA).
* **Base de Datos:** SQLite (para almacenamiento de metadatos, contenido procesado y embeddings).
* **Motor de Búsqueda e Indexación:** Meilisearch (versión >= 1.3, con `vectorStore` habilitado para búsqueda vectorial).
* **Generación de Embeddings:** Modelos de `sentence-transformers` (ej. `paraphrase-multilingual-mpnet-base-v2`, generando vectores de 768 dimensiones).
* **Procesamiento y Conversión de Documentos:** Pandoc, Python-Textract, y scripts personalizados en Python.
* **Gestión de Dependencias Python:** `requirements.txt` (gestionado con `pip`).
* **Gestión de Dependencias Node.js:** `package.json` (gestionado con `npm` o `yarn`).

---

## 3. Arquitectura Detallada del Sistema

### 3.1. Estructura de Carpetas Top-Level y Propósito

* **`backend/`**: Contiene todo el código del lado del servidor.
    * **`backend/api/`** (sugerido): Módulos y rutas de la API Flask.
    * **`backend/scripts/`**: Scripts de apoyo para el backend, como importación completa, procesamiento semántico, indexación en Meilisearch, limpieza de base deatos.
    * **`backend/services/`** (sugerido): Lógica de negocio y servicios (ej. `embedding_service.py`).
    * **`backend/models/`** (sugerido): Si se usa un ORM o clases para representar los datos.
    * **`backend/data/`**: Almacena la base de datos SQLite (ej. `biblioteca.db`) y el esquema SQL (ej. `db_schema.sql`).
    * **`backend/meilisearch/`** (sugerido): Binarios o configuraciones de Meilisearch si se gestionan localmente.
    * `requirements.txt`: Dependencias específicas del backend.
    * `nodemon.json` (opcional): Configuración si se usa `nodemon` para el desarrollo con Flask.

* **`frontend/`**: Alberga la aplicación web de tipo Single Page Application (SPA).
    * **`frontend/src/`**: Código fuente principal de la aplicación React.
        * **`frontend/src/components/`**: Componentes reutilizables de React.
        * **`frontend/src/pages/`**: Componentes que representan las vistas principales (ej. `SearchPage.tsx`, `SemanticSearchPage.tsx`).
        * **`frontend/src/services/`**: Lógica para interactuar con la API del backend (ej. `api.ts`).
        * **`frontend/src/hooks/`**: Custom hooks de React.
        * **`frontend/src/assets/`**: Imágenes, fuentes y otros activos estáticos.
        * `App.tsx` (o `App.js`): Componente raíz de la aplicación.
        * `main.tsx` (o `index.js`): Punto de entrada de la aplicación React.
    * `public/`: Activos estáticos que se sirven directamente (ej. `index.html`, `favicon.ico`).
    * `package.json`: Dependencias y scripts de Node.js para el frontend.
    * `vite.config.js` (o `vite.config.ts`): Archivo de configuración de Vite.
    * `tailwind.config.js`: Archivo de configuración de Tailwind CSS.

* **`dataset/`**: Destinada a los datos crudos (fuentes originales) y los scripts para el proceso de Ingesta, Transformación y Carga (ETL).
    * **`dataset/fuentes/`**: Carpetas por autor o fuente conteniendo los documentos originales (DOCX, PDF, TXT, MD).
    * **`dataset/salidas/`**: Resultados del procesamiento de los scripts de `dataset/scripts/` (ej. archivos NDJSON, reportes de duplicados).
    * **`dataset/scripts/`**: Scripts Python para la conversión, limpieza, normalización y depuración de documentos (ej. `app_depuracion.py`, `converters.py`, `processors.py`, `utils.py`).
    * `requirements.txt` (opcional): Dependencias específicas para los scripts de `dataset/`.

* **`scripts/`** (opcional, a nivel raíz): Directorio para scripts Python generales o utilidades que no encajan directamente en `backend` o `dataset` (ej. scripts de despliegue, tareas de mantenimiento globales).

* **`docs/`**: Documentación del proyecto.
    * `BIBLIOPERSON_ARQUITECTURA.md`: Este mismo archivo.
    * (Otros documentos: guías de instalación, ejemplos de API, etc.).

* `.gitignore`: Especifica los archivos y directorios ignorados por Git.
* `README.md`: Descripción general del proyecto, instrucciones de instalación y uso básico.

### 3.2. Patrones Arquitectónicos y Observaciones Clave

* **Separación Clara de Responsabilidades (SoC):** Existe una distinción marcada entre:
    * **Capa de Presentación:** Gestionada por el frontend (React/Vite).
    * **Capa de Lógica de Negocio y Acceso a Datos (API):** Gestionada por el backend (Flask).
    * **Capa de Procesamiento e Ingesta de Datos (ETL):** Gestionada por scripts en `dataset/` y `backend/scripts/`.
* **Módulo de Ingestión/ETL Desacoplado:** Los procesos de ETL son en su mayoría scripts batch que operan independientemente del servidor web principal. Esto permite ejecuciones manuales o programadas (ej. vía `cron` o `celery` en el futuro) y facilita el mantenimiento y la escalabilidad de esta parte del sistema.
* **API RESTful como Intermediario:** El frontend interactúa con los datos y la lógica de negocio exclusivamente a través de la API REST expuesta por el backend Flask. Esto promueve un bajo acoplamiento entre el frontend y el backend.
* **Modelo Vista Controlador (MVC) Ligero (implícito en Backend):**
    * **Modelos:** Representados por las tablas de la base de datos SQLite y la lógica de acceso a datos (potencialmente a través de un ORM ligero o funciones de acceso directo).
    * **Vistas:** Gestionadas principalmente por el frontend React, que consume los datos de la API.
    * **Controladores:** Implementados como las rutas y manejadores de peticiones en la aplicación Flask.
* **Single Page Application (SPA):** El frontend es una SPA, lo que implica que la interfaz de usuario se carga una sola vez y las actualizaciones de contenido se realizan dinámicamente mediante JavaScript, interactuando con la API.

### 3.3. Flujo de Datos y Componentes Principales del Sistema

#### 3.3.1. Fuentes Externas de Datos
* Documentos locales proporcionados por el usuario en diversos formatos: DOCX, PDF, TXT, MD.
* Estos documentos se organizan típicamente en `dataset/fuentes/<autor>/`.

#### 3.3.2. Capa de Ingestión de Datos (ETL)
* **Localización:** Principalmente scripts en `dataset/scripts/` (ej. `app_depuracion.py`, `converters.py`) y scripts de orquestación o importación en `backend/scripts/` (ej. `importar_completo.py`).
* **Responsabilidades:**
    1.  **Detección y Lectura:** Identificar los archivos en las carpetas fuente.
    2.  **Conversión de Formato:** Utilizar herramientas como Pandoc y Textract para convertir DOCX, PDF, etc., a texto plano o Markdown.
    3.  **Normalización y Limpieza:** Eliminar caracteres no deseados, corregir codificación, manejar saltos de línea inconsistentes.
    4.  **Segmentación de Contenido:** Dividir los documentos en unidades manejables (párrafos, secciones, o según la estructura del documento original) para la indexación y búsqueda. Identificar metadatos como títulos, autor, fuente, fecha si es posible.
    5.  **Generación de Formato Intermedio:** Usualmente se genera un archivo `NDJSON` (Newline Delimited JSON) con campos como `id`, `texto`, `fuente`, `autor`, `fecha_creacion`, `contexto`.
    6.  **Carga en Base de Datos (SQLite):** Los datos depurados y estructurados del NDJSON se importan a la tabla `contenidos` de la base de datos SQLite.
    7.  **Generación de Embeddings:** Para cada segmento de texto relevante en `contenidos`, se generan embeddings vectoriales utilizando modelos de `sentence-transformers`. Estos embeddings se almacenan en la tabla `contenido_embeddings`, vinculada a `contenidos`.
    8.  **Indexación en Meilisearch:** Los datos de `contenidos` junto con sus embeddings vectoriales (si Meilisearch los soporta directamente o se gestionan vía IDs) se envían a Meilisearch para crear o actualizar los índices de búsqueda full-text y vectorial.

* **Scripts Clave (Ejemplos):**
    * `dataset/scripts/app_depuracion.py`: Orquesta la conversión y limpieza de documentos fuente a NDJSON.
    * `dataset/scripts/converters.py`: Contiene funciones específicas para convertir diferentes tipos de archivo.
    * `backend/scripts/importar_completo.py`: Gestiona la importación del NDJSON final a SQLite.
    * `backend/scripts/procesar_semantica.py`: Genera los embeddings para el contenido en SQLite.
    * `backend/scripts/indexar_meilisearch.py`: Envía los datos de SQLite a Meilisearch para indexación.

#### 3.3.3. Almacenamiento (Storage)
* **Tecnología Principal:** Base de datos SQLite.
* **Ubicación del Archivo de BD:** `backend/data/biblioteca.db`.
* **Esquema de la Base de Datos:** Definido en `backend/data/db_schema.sql` (o gestionado mediante migraciones si se usa un ORM).
* **Tablas Principales (Ejemplos):**
    * `contenidos`: Almacena los segmentos de texto procesados, metadatos (autor, fuente, fecha, tipo de contenido), y un ID único.
        * Campos: `id` (PK), `texto_original`, `texto_limpio`, `autor_id` (FK), `fuente_id` (FK), `fecha_creacion`, `metadatos_adicionales` (JSON).
    * `contenido_embeddings`: Almacena los embeddings vectoriales para los textos.
        * Campos: `id` (PK), `contenido_id` (FK a `contenidos.id`), `embedding_vector` (BLOB o TEXT), `modelo_embedding`.
    * `autores`: Información sobre los autores.
    * `fuentes`: Información sobre las fuentes de los documentos.
* **Motor de Búsqueda:** Meilisearch (opera como un servicio separado, pero funcionalmente es parte de la capa de almacenamiento y recuperación).
    * **Índices:** Un índice principal (ej. "documentos") que contiene los textos y está configurado para búsqueda full-text y búsqueda vectorial (usando los embeddings).

#### 3.3.4. Backend REST API
* **Tecnología:** Aplicación Flask escrita en Python.
* **Localización del Código Principal:** `backend/` (posiblemente en un archivo como `backend/app.py` o módulos dentro de `backend/api/`).
* **Puerto de Escucha (Desarrollo Típico):** `5000`.
* **Responsabilidades:**
    1.  Exponer endpoints HTTP para que el frontend (u otros clientes) interactúen con el sistema.
    2.  Manejar la lógica de autenticación y autorización (si aplica en el futuro).
    3.  Procesar las solicitudes de búsqueda:
        * Para búsquedas full-text, construir y ejecutar consultas contra Meilisearch.
        * Para búsquedas semánticas, generar el embedding de la consulta del usuario y usarlo para buscar los vectores más similares en Meilisearch (o directamente en SQLite/FAISS si se implementara así).
    4.  Recuperar y formatear los resultados de la base de datos SQLite y/o Meilisearch.
    5.  Potencialmente, ofrecer endpoints para la gestión de datos (CRUD de autores, fuentes, etc., si es necesario).
    6.  En el futuro, podría manejar la lógica para generar contenido nuevo basado en los resultados de búsqueda.
* **Endpoints Principales (Ejemplos):**
    * `GET /api/busqueda?termino_busqueda=<query>[&autor=<autor_id>&...]`: Para búsqueda full-text.
    * `GET /api/busqueda/semantica?texto_consulta=<query>[&autor=<autor_id>&similitud_min=<float>&...]`: Para búsqueda semántica.
    * `GET /api/autores`: Para listar autores disponibles.
    * `GET /api/estadisticas`: Para obtener estadísticas del corpus.

#### 3.3.5. Frontend SPA (Interfaz de Usuario)
* **Tecnología:** React con Vite (usando JavaScript o TypeScript). Estilos con Tailwind CSS.
* **Localización del Código Principal:** `frontend/src/`.
* **Servidor de Desarrollo (Vite):** Típicamente en el puerto `5173`.
* **Responsabilidades:**
    1.  Presentar la interfaz de usuario al usuario final a través de un navegador web.
    2.  Permitir al usuario ingresar consultas de búsqueda (textual y/o semántica) y seleccionar filtros (autor, fuente, etc.).
    3.  Realizar solicitudes HTTP (usando `Workspace` o `axios`) a los endpoints de la API del backend.
    4.  Recibir y mostrar los resultados de búsqueda de manera clara e interactiva.
    5.  Gestionar el estado de la aplicación en el cliente (ej. estado de carga, errores, datos de usuario).
    6.  Navegación dentro de la aplicación sin recargas de página completa.

#### 3.3.6. Usuarios Finales
* Interactúan con el sistema exclusivamente a través del Frontend SPA, utilizando un navegador web estándar.

### 3.4. Diagrama de Flujo de Datos e Interacciones Principales

+----------------------+     +----------------------+     +----------------------+
|   Fuentes Externas   | --> | Capa de Ingestión    | --> | Almacenamiento       |
| (DOCX, PDF, TXT...)  |     | (ETL Scripts)        |     | (SQLite + Meilisearch|
+----------------------+     +----------------------+     +----------^-----------+
|
| (Lectura/Escritura)
|
+----------------------+     +----------------------+     +----------v-----------+
|   Usuario Final      | <-> | Frontend SPA         | <-> | Backend REST API     |
| (Navegador Web)      |     | (React/Vite)         |     | (Flask)              |
+----------------------+     +----------------------+     +----------------------+

**Flujo de Ingesta:**
1.  Usuario coloca documentos en `dataset/fuentes/`.
2.  Se ejecutan scripts de ETL (`dataset/scripts/` y `backend/scripts/`).
    * Convierten, limpian, normalizan documentos.
    * Generan NDJSON.
    * Importan NDJSON a SQLite (`contenidos`).
    * Generan embeddings para `contenidos` y los guardan en `contenido_embeddings`.
    * Indexan datos de `contenidos` y embeddings en Meilisearch.

**Flujo de Búsqueda:**
1.  Usuario ingresa una consulta en el Frontend SPA.
2.  Frontend envía la solicitud al Backend REST API.
3.  Backend API:
    * Si es búsqueda semántica, genera embedding de la consulta.
    * Consulta a Meilisearch (y/o SQLite para metadatos adicionales).
    * Devuelve los resultados formateados (JSON) al Frontend.
4.  Frontend muestra los resultados al Usuario.

### 3.5. Tecnologías Clave por Capa/Componente (Repaso)

* **Ingestión/ETL:** Python, Pandas (para manipulación de datos tabulares si es necesario), Textract, PyPandoc (o llamadas directas a Pandoc), `sentence-transformers`.
* **Backend/API:** Python, Flask, Flask-RESTx (o similar para APIs estructuradas, opcional), Flask-CORS, `sqlite3` (módulo Python), cliente `meilisearch` (Python).
* **Frontend:** Node.js (entorno de desarrollo), Vite (empaquetador y servidor de desarrollo), React, TypeScript (preferido sobre JavaScript), Tailwind CSS, `axios` (o `Workspace API`).
* **Almacenamiento:** SQLite3 (motor de base de datos), Meilisearch (motor de búsqueda).

### 3.6. Herramientas de Desarrollo

* **Control de Versiones:** Git, GitHub/GitLab/Bitbucket.
* **Entornos Virtuales Python:** `venv` o `conda`.
* **Gestor de Paquetes Frontend:** `npm` o `yarn`.
* **Servidor de Desarrollo Backend:** Servidor de desarrollo de Flask (para producción, se usaría Gunicorn/uWSGI + Nginx). `nodemon` para reinicio automático durante el desarrollo.
* **Servidor de Desarrollo Frontend:** Servidor de desarrollo de Vite (`npm run dev`).
* **Linters y Formateadores:**
    * Python: Black, Flake8, Pylint, isort.
    * JavaScript/TypeScript: ESLint, Prettier.
* **Testing:**
    * Python: `pytest`.
    * JavaScript/TypeScript: Jest, React Testing Library, Vitest.

---

## 4. Scripts Principales y Módulos Relevantes (Referencia Rápida)

*(Esta sección se puede expandir con una lista más detallada y descripciones a medida que el proyecto evoluciona)*

* **`dataset/scripts/app_depuracion.py`**: Orquestador principal para la conversión de documentos fuente a un formato NDJSON limpio.
* **`dataset/scripts/converters.py`**: Librería de funciones para convertir diferentes tipos de archivo (DOCX, PDF, etc.) a texto.
* **`dataset/scripts/processors.py`**: Funciones para el procesamiento y limpieza de texto (ej. segmentación, eliminación de metadatos no deseados).
* **`dataset/scripts/utils.py`**: Utilidades generales para los scripts de ETL (manejo de archivos, logging, etc.).
* **`backend/scripts/importar_completo.py`**: Script para importar los datos del archivo NDJSON final a la base de datos SQLite.
* **`backend/scripts/importar_datos.py`**: Lógica subyacente para la inserción de datos en SQLite, llamado por `importar_completo.py`.
* **`backend/scripts/procesar_semantica.py`**: Script para generar embeddings para los textos almacenados en la base de datos. Llama a `embedding_service.py`.
* **`backend/services/embedding_service.py`**: Servicio que encapsula la lógica de carga del modelo de embeddings y la generación de vectores.
* **`backend/scripts/indexar_meilisearch.py`**: Script para enviar datos desde SQLite a Meilisearch para su indexación, incluyendo la configuración para búsqueda vectorial.
* **`backend/scripts/levantar_meilisearch.py`**: Script de utilidad para iniciar una instancia de Meilisearch.
* **`backend/app.py` (o `backend/api/routes.py`)**: Archivo principal de la aplicación Flask que define las rutas de la API.
* **`frontend/src/services/api.ts`**: Módulo en el frontend que encapsula la lógica para realizar llamadas a la API del backend.

---

## 5. Convenciones y Buenas Prácticas Específicas del Proyecto

*(Esta sección puede ser llenada o expandida más adelante con decisiones específicas del proyecto)*

* **Estilo de Código:** Seguir las recomendaciones de los linters y formateadores configurados (Black, Flake8 para Python; ESLint, Prettier para TS/JS).
* **Mensajes de Commit:** Utilizar Conventional Commits (`feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`).
* **Manejo de Errores:**
    * API: Devolver códigos de estado HTTP apropiados y mensajes de error JSON estructurados.
    * Scripts: Uso robusto de `try-except` y logging detallado.
* **Logging:** Configurar logging centralizado y estructurado para todos los componentes backend y scripts.
* **Variables de Entorno:** Utilizar archivos `.env` para configurar parámetros sensibles o específicos del entorno (URLs de bases de datos, claves API, puertos). No comitear archivos `.env` directamente, sino un `.env.example`.
* **Documentación de Código:** Escribir docstrings para funciones y clases Python (estilo Google o NumPy). Comentarios JSDoc/TSDoc para funciones y componentes frontend.

---

## 6. Glosario de Términos

* **Embedding:** Representación vectorial densa de un fragmento de texto en un espacio multidimensional, capturando su significado semántico.
* **ETL:** Proceso de Extract, Transform, Load (Extraer, Transformar, Cargar) datos de una o más fuentes a un destino.
* **Full-text Search:** Búsqueda basada en la coincidencia de palabras clave exactas o variaciones morfológicas dentro del contenido textual.
* **Meilisearch:** Motor de búsqueda rápido y de código abierto.
* **NDJSON (Newline Delimited JSON):** Formato de datos donde cada línea es un objeto JSON válido.
* **Pandoc:** Herramienta universal de conversión de documentos.
* **Sentence Transformers:** Librería Python para generar embeddings de frases y párrafos.
* **SPA (Single Page Application):** Aplicación web que carga una única página HTML y actualiza su contenido dinámicamente mediante JavaScript.
* **SQLite:** Motor de base de datos relacional ligero basado en archivos.
* **Textract (Python):** Librería Python para extraer texto de varios tipos de documentos.
* **Vector Search (Búsqueda Semántica/Por Similitud):** Búsqueda basada en la similitud semántica entre el embedding de una consulta y los embeddings de los documentos almacenados, en lugar de coincidencias exactas de palabras clave.
* **Vite:** Herramienta de frontend moderna que proporciona un servidor de desarrollo rápido y empaquetado optimizado para producción.
