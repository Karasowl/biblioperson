# Biblioperson - Tu Biblioteca Personal Inteligente

## ¿Qué es Biblioperson?

Biblioperson transforma tu biblioteca personal en una base de conocimiento consultable con inteligencia artificial. Imagina poder preguntarle a todos tus libros y documentos: *"¿Qué piensa este autor sobre X tema?"* o *"¿Dónde he leído algo sobre Y concepto?"*

## 🚀 Inicio Rápido

**¿Primera vez aquí?** → Lee la [**Guía de Inicio Rápido**](INICIO_RAPIDO.md)

**¿Quieres procesar documentos?** → Ve al [**Pipeline NDJSON**](PIPELINE_NDJSON.md)

## ✨ ¿Qué puedes hacer?

### 🔍 **Búsqueda Inteligente**
- Encuentra ideas por significado, no solo palabras exactas
- Busca qué dice un autor específico sobre cualquier tema
- Descubre conexiones entre diferentes textos y autores

### 📚 **Análisis Profundo**
- Explora el pensamiento completo de cada autor en tu biblioteca
- Genera inferencias cruzadas entre múltiples fuentes
- Reconstruye y navega tus documentos originales

### 🤖 **Generación de Contenido**
- Crea material original basado en las ideas de tu biblioteca
- Sintetiza información de múltiples fuentes
- Mantén la trazabilidad hacia los textos originales

## 🏗️ Arquitectura del Sistema

```
Tus Documentos → Procesamiento → Base de Datos → Aplicación Web
   (PDF, DOCX,      (NDJSON)        (SQLite +        (React +
    TXT, MD)                        Meilisearch)      Flask API)
```

## 📋 Características Técnicas

- **Procesamiento inteligente**: Convierte PDFs, DOCX, TXT, Markdown, entre otros en datos estructurados
- **Búsqueda semántica avanzada**: Powered by Meilisearch + sentence-transformers
- **Interfaz web moderna**: React frontend con diseño intuitivo
- **API REST completa**: Integración programática para aplicaciones externas
- **Base de datos híbrida**: SQLite para estructura + Meilisearch para búsqueda
- **Procesamiento por lotes**: Maneja bibliotecas grandes eficientemente

## 📖 Documentación

### 🚀 **Para Empezar**
- [**Inicio Rápido**](INICIO_RAPIDO.md) - Configuración en 5 pasos
- [**Pipeline NDJSON**](PIPELINE_NDJSON.md) - Procesamiento de documentos paso a paso

### 📚 **Documentación Completa**
- [**📋 Índice General**](INDICE.md) - Navegación completa por objetivos
- [**🏗️ Arquitectura**](BIBLIOPERSON_ARQUITECTURA.md) - Diseño técnico del sistema
- [**🔧 Configuración**](GUIA_MEILISEARCH.md) - Búsqueda semántica avanzada
- [**📋 Especificaciones**](NDJSON_ESPECIFICACION.md) - Formato de datos técnico

> **💡 Tip**: ¿No sabes por dónde empezar? Ve al [**Índice General**](INDICE.md) para navegación por objetivos.

## Índice Detallado

- [Biblioteca de Conocimiento Personal](#biblioteca-de-conocimiento-personal)
  - [Índice](#índice)
  - [Características](#características)
  - [Requisitos](#requisitos)
  - [Instalación](#instalación)
  - [Estructura del Proyecto](#estructura-del-proyecto)
  - [Importar nuevos datos](#importar-nuevos-datos)
  - [Procesar y poblar la base de datos](#procesar-y-poblar-la-base-de-datos)
  - [Generar embeddings semánticos](#generar-embeddings-semánticos)
  - [Ejecutar la aplicación](#ejecutar-la-aplicación)
  - [Búsqueda Full-Text con Meilisearch](#búsqueda-full-text-con-meilisearch)
    - [Instalación y uso local](#instalación-y-uso-local)
    - [Nota sobre Meilisearch y el backend](#nota-sobre-meilisearch-y-el-backend)
    - [Notas](#notas)
  - [Indexación incremental en Meilisearch](#indexación-incremental-en-meilisearch)
  - [Verificación y depuración de la indexación en Meilisearch](#verificación-y-depuración-de-la-indexación-en-meilisearch)
  - [Importante: Borrar el índice de Meilisearch](#importante-borrar-el-índice-de-meilisearch)
  - [Preguntas frecuentes](#preguntas-frecuentes)
  - [Licencia](#licencia)
  - [Regenerar todos los embeddings semánticos](#regenerar-todos-los-embeddings-semánticos)
  - [Levantar la base de datos, backend y frontend](#levantar-la-base-de-datos-backend-y-frontend)
    - [1. Levantar la base de datos (SQLite)](#1-levantar-la-base-de-datos-sqlite)
    - [2. Levantar el backend (API Flask)](#2-levantar-el-backend-api-flask)
    - [3. Levantar el frontend (React)](#3-levantar-el-frontend-react)
    - [4. Consultas básicas en la base de datos (SQLite)](#4-consultas-básicas-en-la-base-de-datos-sqlite)

## Características

- Importación de contenido desde múltiples fuentes (Facebook, Twitter, Telegram, documentos)
- Exploración de contenido por temas, fechas, autores, idiomas y plataformas
- Generación de material para nuevo contenido
- API REST para acceso a los datos
- Interfaz web para exploración y análisis
-  Lectura de los documentos originales tipo ebook al reconostruirlos con la base de datos.

## ⚡ Instalación Rápida

### Requisitos Mínimos
- **Python 3.8+** y **Node.js 16+**
- **4GB RAM** y espacio en disco para tu biblioteca
- **Git** para clonar el repositorio

### Instalación en 3 Comandos

```bash
# 1. Clonar y preparar
git clone [URL_DEL_REPOSITORIO] && cd biblioperson
python -m venv venv && .\venv\Scripts\activate  # Windows

# 2. Instalar dependencias
pip install -r backend/requirements.txt -r dataset/requirements.txt
cd frontend && npm install && cd ..

# 3. Configurar y ejecutar
cd dataset && python scripts/app_depuracion.py  # Procesar primer documento
cd ../backend/scripts && python importar_completo.py  # Importar a DB
```

**¿Necesitas más detalles?** → Ver [**Guía de Inicio Rápido**](INICIO_RAPIDO.md)

## Estructura del Proyecto

- `backend/`: Backend y scripts de procesamiento
- `backend/data/import/`: Carpeta donde colocar archivos NDJSON o TXT para importar
- `backend/scripts/`: Scripts de Python para la API y procesamiento
- `frontend/`: Frontend (React)
- `shared/`: Recursos compartidos
- `dataset/`: Procesamiento y normalización de datasets

## Importar nuevos datos

1. **Coloca tus archivos NDJSON en la carpeta:**
   - `backend/data/import/`
   - O bien, ten a mano la ruta de tu archivo NDJSON unificado.

2. **Ubícate en la carpeta de scripts:**
   ```bash
   cd backend/scripts
   ```

3. **Ejecuta el script de importación completa:**
   - Si ya tienes archivos NDJSON en la carpeta de importación:
     ```bash
     python importar_completo.py --solo-importar
     ```
   - Si quieres importar un archivo NDJSON específico y copiarlo automáticamente:
     ```bash
     python importar_completo.py /ruta/a/tu/archivo.ndjson
     ```
   - Si quieres reiniciar la base de datos antes de importar (¡esto borra todo lo anterior!):
     ```bash
     python importar_completo.py /ruta/a/tu/archivo.ndjson --reiniciar-db
     ```

   - El script se encargará de copiar el archivo (si lo especificas), importar los datos y generar los índices necesarios.

4. **Verifica que la importación fue exitosa revisando los mensajes en consola.**

## Procesar y poblar la base de datos

- Si necesitas limpiar o inicializar la base de datos, ejecuta:
  ```bash
  python inicializar_db.py
  ```
- Para actualizar o añadir nuevos registros, simplemente repite el paso de importación.

## Generar embeddings semánticos

- Una vez que los nuevos contenidos están en la base de datos, genera los embeddings:
  ```bash
  python procesar_semantica.py
  ```
- Este script solo procesará los contenidos nuevos que no tengan embedding.

## Ejecutar la aplicación

- Desde la raíz del proyecto:
  ```bash
  npm run dev
  ```
- Esto levantará tanto el backend como el frontend.

## Búsqueda Full-Text con Meilisearch

Este proyecto utiliza [Meilisearch](https://www.meilisearch.com/) como motor de búsqueda de texto completo para ofrecer búsquedas rápidas y modernas.

### Instalación y uso local

1. **Descarga Meilisearch:**
   - Ve a [https://github.com/meilisearch/meilisearch/releases](https://github.com/meilisearch/meilisearch/releases)
   - Descarga el archivo `meilisearch-windows-amd64.exe.zip` (o el que corresponda a tu sistema operativo).
   - Descomprime el archivo.

2. **Ejecuta Meilisearch:**
   - Abre una terminal en la carpeta donde está el ejecutable.
   - Ejecuta:  
     ```
     .\meilisearch.exe
     ```
   - El servidor estará disponible en [http://127.0.0.1:7700](http://127.0.0.1:7700)

3. **Master Key:**
   - Al iniciar, Meilisearch genera una master key (token de administración).  
     Ejemplo:  
     ```
     --master-key zg0_by09jiVS_kcLdoVgvO9J7fefp1uGvyF-YNonMRg
     ```
   - Guarda este valor, lo necesitarás para configurar el backend y proteger el acceso en producción.

4. **Documentación oficial:**  
   [https://www.meilisearch.com/docs](https://www.meilisearch.com/docs)

### Nota sobre Meilisearch y el backend

- Meilisearch se inicia automáticamente cuando levantas el backend (por ejemplo, ejecutando `api_conexion.py`).
- El ejecutable de Meilisearch debe estar en `backend/meilisearch/meilisearch-windows-amd64.exe`.
- Si deseas iniciar Meilisearch manualmente, puedes ejecutar:
  ```bash
  python backend/scripts/levantar_meilisearch.py
  ```
- Si cambias de carpeta o servidor, recuerda copiar también el archivo/carpeta `data.ms` para conservar la indexación, o vuelve a indexar desde la base de datos.

### Notas

- Si actualizas Meilisearch, repite el proceso de descarga y reemplaza el ejecutable.
- Si cambias de PC o servidor, repite estos pasos.
- Para producción, configura la master key y revisa la documentación de seguridad.

## Indexación incremental en Meilisearch

Cuando añadas nuevos contenidos a la base de datos, puedes indexar solo los nuevos documentos en Meilisearch (sin volver a subir todo) ejecutando:

```bash
python backend/scripts/indexar_meilisearch.py --indexar-nuevos
```

Esto detecta automáticamente los registros que aún no están en Meilisearch y los añade al índice. Es útil para mantener la búsqueda actualizada después de cada importación o edición masiva.

## Verificación y depuración de la indexación en Meilisearch

Si notas que el número de documentos en Meilisearch es menor que en tu base de datos:

1. **Verifica cuántos documentos hay en la base de datos y en Meilisearch:**
   Puedes usar el siguiente script para comparar y listar los IDs faltantes:

   ```python
   import sqlite3
   import meilisearch

   DB_PATH = '../../backend/data/biblioteca.db'
   MEILI_URL = 'http://127.0.0.1:7700'
   MEILI_INDEX = 'contenidos'
   MEILI_KEY = None

   conn = sqlite3.connect(DB_PATH)
   cursor = conn.cursor()
   cursor.execute("SELECT id FROM contenidos")
   db_ids = set(row[0] for row in cursor.fetchall())

   client = meilisearch.Client(MEILI_URL, MEILI_KEY)
   index = client.index(MEILI_INDEX)

   meili_ids = set()
   offset = 0
   limit = 10000
   while True:
       docs = index.get_documents({'fields': ['id'], 'limit': limit, 'offset': offset})
       if not docs:
           break
       for doc in docs:
           meili_ids.add(doc['id'])
       if len(docs) < limit:
           break
       offset += limit

   print(f'IDs en base de datos: {len(db_ids)}')
   print(f'IDs en Meilisearch: {len(meili_ids)}')
   faltan = db_ids - meili_ids
   print(f'IDs que faltan en Meilisearch: {len(faltan)}')
   if faltan:
       print(f'Ejemplo de IDs faltantes: {list(faltan)[:10]}')
   ```

2. **Causas comunes de diferencias:**
   - Documentos demasiado grandes (más de 2 MB) no se indexan.
   - IDs duplicados en la base de datos.
   - Errores de red o timeouts durante la indexación.

3. **Solución:**
   - Revisa los IDs faltantes y verifica si hay problemas con esos registros.
   - Puedes reintentar indexar solo los faltantes, o limpiar/ajustar los datos problemáticos y volver a indexar.

4. **Reindexar todo si es necesario:**
   Si hay muchos problemas, puedes borrar el índice en Meilisearch y volver a indexar desde cero. Recuerda detener Meilisearch antes de borrar la carpeta `data.ms`.

Esto te ayudará a mantener la integridad entre tu base de datos y el índice de búsqueda.

## Importante: Borrar el índice de Meilisearch

Si necesitas borrar el índice (por ejemplo, para reindexar desde cero):

1. **Detén Meilisearch completamente**
   - Si lo levantaste con el script o desde el backend, detén el backend o cierra la terminal donde se ejecutó Meilisearch.
   - O bien, busca el proceso `meilisearch-windows-amd64.exe` en el Administrador de tareas de Windows y finalízalo.

2. **Borra la carpeta de datos**
   - Borra la carpeta `backend/meilisearch/data.ms/` (o el archivo/carpeta de datos que corresponda).

3. **Vuelve a iniciar Meilisearch**
   - Se creará una nueva carpeta de datos vacía y podrás reindexar desde cero.

> **Nota:** No puedes borrar los índices mientras Meilisearch está corriendo. Siempre detén el proceso primero.

## Preguntas frecuentes

- **¿Puedo importar nuevos datos sin perder los anteriores?**  
  Sí, los scripts están diseñados para añadir solo los nuevos registros y generar embeddings solo para ellos.

- **¿Dónde deben estar los archivos de importación?**  
  En `backend/data/import/`.

- **¿Cómo sé si los embeddings están actualizados?**  
  El script `procesar_semantica.py` solo procesa los contenidos que no tienen embedding.

- Para `/api/busqueda` usa `contenido_texto`
- Para `/api/busqueda/semantica` usa `contenido_texto`

## Licencia

[ESPECIFICAR LICENCIA]

## Regenerar todos los embeddings semánticos

Si necesitas **regenerar los embeddings para todos los contenidos** (por ejemplo, tras cambiar de modelo o para limpiar embeddings antiguos), sigue estos pasos:

1. **Vacía la tabla de embeddings en la base de datos:**
   Puedes hacerlo desde SQLite con el siguiente comando:
   ```sql
   DELETE FROM contenido_embeddings;
   ```
   O, si prefieres borrar y recrear la tabla:
   ```sql
   DROP TABLE IF EXISTS contenido_embeddings;
   -- Luego ejecuta el script de inicialización semántica para recrearla
   ```

2. **Ejecuta el script de procesamiento semántico:**
   ```bash
   python procesar_semantica.py
   ```
   Esto generará embeddings para **todos** los contenidos, ya que la tabla estará vacía.

> **Nota:** Si tienes muchos contenidos, este proceso puede tardar varios minutos u horas según la cantidad y el modelo usado.

## Levantar la base de datos, backend y frontend

### 1. Levantar la base de datos (SQLite)

No necesitas un servidor especial, solo asegúrate de que el archivo `backend/data/biblioteca.db` existe. Si necesitas crearla desde cero:

```bash
cd backend/scripts
python inicializar_db.py
```

Esto creará la estructura básica de la base de datos si no existe.

### 2. Levantar el backend (API Flask)

Desde la raíz del proyecto o desde `backend/scripts`:

```bash
python api_conexion.py
```

Esto iniciará el backend en `http://localhost:5000`.

### 3. Levantar el frontend (React)

Desde la carpeta `frontend`:

```bash
cd frontend
npm install  # Solo la primera vez
npm run dev
```

Esto abrirá la aplicación en `http://localhost:5173` (o el puerto que indique la consola).

### 4. Consultas básicas en la base de datos (SQLite)

Puedes usar la terminal de SQLite para hacer consultas directas:

```bash
sqlite3 backend/data/biblioteca.db
```

Ejemplos de consultas útiles:

- Contar todos los contenidos:
  ```sql
  SELECT COUNT(*) FROM contenidos;
  ```
- Listar autores únicos:
  ```sql
  SELECT DISTINCT autor FROM contenidos WHERE autor IS NOT NULL AND autor != '';
  ```
- Contar contenidos por autor:
  ```sql
  SELECT autor, COUNT(*) FROM contenidos GROUP BY autor;
  ```
- Ver los primeros 5 contenidos:
  ```sql
  SELECT id, contenido_texto FROM contenidos LIMIT 5;
  ```