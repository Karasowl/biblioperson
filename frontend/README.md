# Biblioteca de Conocimiento Personal (Biblioperson)

**Última actualización:** 9 de mayo de 2025

Sistema para gestionar, analizar y realizar búsquedas avanzadas sobre contenido personal proveniente de diferentes plataformas y fuentes documentales.

## Índice del README
- [Biblioteca de Conocimiento Personal (Biblioperson)](#biblioteca-de-conocimiento-personal-biblioperson)
  - [Índice del README](#índice-del-readme)
  - [Características Principales](#características-principales)
  - [Requisitos Previos](#requisitos-previos)
  - [Instalación](#instalación)
  - [Estructura del Proyecto](#estructura-del-proyecto)
  - [Cómo Ejecutar la Aplicación](#cómo-ejecutar-la-aplicación)

---

## Características Principales

* Importación de contenido desde múltiples fuentes (formatos DOCX, PDF, TXT, NDJSON, etc.).
* Procesamiento y normalización de textos para análisis.
* Base de datos centralizada para el contenido (SQLite).
* Generación de embeddings semánticos para búsqueda por significado.
* Motor de búsqueda avanzado (Meilisearch) para full-text y búsqueda vectorial.
* API REST (Flask) para acceder a los datos y funcionalidades.
* Interfaz web interactiva (React) para exploración y análisis.

---

## Requisitos Previos

Asegúrate de tener instalados los siguientes componentes en tu sistema:

* **Python:** Versión 3.8 o superior.
* **Node.js:** Versión 16 o superior (incluye npm).
* **SQLite3:** Generalmente viene preinstalado en muchos sistemas operativos o se instala fácilmente.
* **Git:** Para clonar el repositorio.
* **Meilisearch:** Opcional para la instalación inicial, pero necesario para la funcionalidad de búsqueda. Consulta la [Guía de Meilisearch](docs/GUIA_MEILISEARCH.md) para su instalación y configuración.

---

## Instalación

Sigue estos pasos para configurar el proyecto en tu entorno local:

1.  **Clonar el Repositorio:**
    ```bash
    git clone [URL_DEL_REPOSITORIO_AQUI]
    cd biblioperson
    ```
    *(Reemplaza `[URL_DEL_REPOSITORIO_AQUI]` con la URL real de tu repositorio)*

2.  **Configurar Entorno Virtual de Python y Activar:**
    Se recomienda usar un entorno virtual para aislar las dependencias del proyecto.
    ```bash
    python -m venv venv
    ```
    * En Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    * En Linux/macOS:
        ```bash
        source venv/bin/activate
        ```

3.  **Instalar Dependencias de Python:**
    El proyecto tiene diferentes conjuntos de dependencias. Instala las que necesites:
    * Para el **backend y la API Flask**:
        ```bash
        pip install -r backend/requirements.txt
        ```
    * Para el **procesamiento de datos/datasets** (si vas a trabajar con la carpeta `dataset/`):
        ```bash
        pip install -r dataset/requirements.txt
        ```
        *(Considera tener un `requirements.txt` general en la raíz si las dependencias son compartidas o si deseas simplificar este paso).*

4.  **Instalar Dependencias del Frontend (Node.js):**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

5.  **Configurar la Base de Datos Inicial:**
    Si es la primera vez que configuras el proyecto, o si necesitas una base de datos limpia, puedes inicializarla:
    ```bash
    cd backend/scripts
    python inicializar_db.py
    cd ../..
    ```
    Para más detalles sobre la gestión de datos y la importación, consulta la [Guía de Gestión de Datos](docs/GUIA_GESTION_DATOS.md).

---

## Estructura del Proyecto

El proyecto está organizado en varias carpetas principales:

* `backend/`: Contiene la lógica del servidor API (Flask), scripts de procesamiento, y la base de datos.
* `frontend/`: Alberga la aplicación de interfaz de usuario (React).
* `dataset/`: Scripts y herramientas para la ingesta, limpieza y normalización de datos fuente.
* `docs/`: Documentación detallada del proyecto.

Para una descripción exhaustiva de la arquitectura y la estructura de carpetas, consulta el documento:
**[📄 Arquitectura del Proyecto Biblioperson](docs/BIBLIOPERSON_ARQUITECTURA.md)**

---

## Cómo Ejecutar la Aplicación

Una vez completada la instalación y configuración (incluyendo la inicialización de la base de datos y la configuración de Meilisearch si se va a usar la búsqueda), puedes ejecutar la aplicación completa (backend y frontend) con un solo comando desde la raíz del proyecto:

```bash

Esto debería:

Iniciar el servidor backend de Flask (generalmente en http://localhost:5000).
Iniciar el servidor de desarrollo del frontend React (generalmente en http://localhost:5173 o el puerto que indique la consola).
Nota:

Asegúrate de que Meilisearch esté en ejecución si deseas utilizar las funcionalidades de búsqueda. Consulta la Guía de Meilisearch.
Para levantar los componentes individualmente (solo backend, solo frontend) o para flujos de trabajo más específicos como la importación de datos o la generación de embeddings, consulta las guías detalladas en la sección de Documentación.
Documentación Detallada
Para profundizar en aspectos específicos del proyecto, consulta las siguientes guías en la carpeta docs/:

📄 Arquitectura del Proyecto Biblioperson:
Visión general de la arquitectura, componentes principales, flujos de datos y decisiones de diseño.

💾 Guía de Gestión de Datos:
Instrucciones detalladas sobre la preparación de la base de datos, importación de contenidos, generación y regeneración de embeddings semánticos, y consultas directas a la base de datos.

🔍 Guía de Meilisearch:
Todo sobre la instalación, configuración, integración, indexación (completa e incremental), verificación, depuración y mantenimiento de Meilisearch en Biblioperson.

Licencia
[ESPECIFICAR LICENCIA AQUÍ - Ej: MIT, Apache 2.0, GPLv3, etc.]


**Recordatorios:**

1.  **Reemplaza `[URL_DEL_REPOSITORIO_AQUI]`** con la URL real de tu repositorio Git.
2.  **Asegúrate de que los nombres de archivo y las rutas en los enlaces** (ej. `docs/GUIA_MEILISEARCH.md`) coincidan exactamente con cómo has nombrado y ubicado tus archivos de documentación.
3.  **Actualiza la sección de "Licencia"** con la licencia que hayas elegido para tu proyecto.
4.  Considera si necesitas un archivo `requirements.txt` general en la raíz del proyecto además de los específicos en `backend/` y `dataset/` para simplificar la instalación de todas las dependencias Python de una vez.

Espero que esta versión completa te sea de utilidad. ¡Hemos logrado una buena reestructuración de tu documentación!

Fuentes y contenido relacionado





