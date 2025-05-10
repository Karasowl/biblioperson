# Guía de Meilisearch para Biblioperson

**Última actualización:** 9-05-2025

## Índice

- [Guía de Meilisearch para Biblioperson](#guía-de-meilisearch-para-biblioperson)
  - [Índice](#índice)
  - [Introducción](#introducción)
  - [1. Instalación y Configuración Inicial de Meilisearch](#1-instalación-y-configuración-inicial-de-meilisearch)
    - [1.1. Descarga de Meilisearch](#11-descarga-de-meilisearch)
    - [1.2. Primera Ejecución y Master Key](#12-primera-ejecución-y-master-key)
    - [1.3. Ubicación del Ejecutable en el Proyecto](#13-ubicación-del-ejecutable-en-el-proyecto)
    - [1.4. Documentación Oficial](#14-documentación-oficial)
  - [2. Integración con el Backend de Biblioperson](#2-integración-con-el-backend-de-biblioperson)
    - [2.1. Inicio Automático de Meilisearch](#21-inicio-automático-de-meilisearch)
    - [2.2. Inicio Manual de Meilisearch](#22-inicio-manual-de-meilisearch)
    - [2.3. Persistencia de Datos (data.ms)](#23-persistencia-de-datos-datams)
  - [3. Indexación de Contenidos](#3-indexación-de-contenidos)
    - [3.1. Indexación Completa](#31-indexación-completa)
    - [3.2. Indexación Incremental](#32-indexación-incremental)
  - [4. Verificación y Depuración del Índice](#4-verificación-y-depuración-del-índice)
    - [4.1. Comparación de Documentos](#41-comparación-de-documentos)
    - [4.2. Causas Comunes de Discrepancias](#42-causas-comunes-de-discrepancias)
    - [4.3. Soluciones y Reindexación](#43-soluciones-y-reindexación)
  - [5. Mantenimiento del Índice](#5-mantenimiento-del-índice)
    - [5.1. Borrar el Índice (Reindexación desde Cero)](#51-borrar-el-índice-reindexación-desde-cero)
  - [6. Consideraciones Adicionales](#6-consideraciones-adicionales)
    - [6.1. Actualización de Meilisearch](#61-actualización-de-meilisearch)
    - [6.2. Migración a Otro Servidor/PC](#62-migración-a-otro-servidorpc)
    - [6.3. Seguridad en Producción](#63-seguridad-en-producción)

---

## Introducción

Este documento proporciona una guía detallada sobre la instalación, configuración, uso y mantenimiento de [Meilisearch](https://www.meilisearch.com/) dentro del proyecto Biblioperson. Meilisearch se utiliza como motor de búsqueda de texto completo (full-text search) y para capacidades de búsqueda vectorial, ofreciendo resultados rápidos y relevantes.

---

## 1. Instalación y Configuración Inicial de Meilisearch

### 1.1. Descarga de Meilisearch

1. Visita la página de lanzamientos de Meilisearch: [https://github.com/meilisearch/meilisearch/releases](https://github.com/meilisearch/meilisearch/releases).
2. Descarga la versión más reciente adecuada para tu sistema operativo (ej. `meilisearch-windows-amd64.exe.zip` para Windows 64-bit).
3. Descomprime el archivo descargado. Obtendrás un archivo ejecutable (`meilisearch.exe` o `meilisearch`).

### 1.2. Primera Ejecución y Master Key

1. Abre una terminal o línea de comandos en la carpeta donde descomprimiste el ejecutable.
2. Ejecuta Meilisearch:
   - **Windows:**
     ```bash
     .\meilisearch.exe
     ```
   - **Linux/macOS:**
     ```bash
     ./meilisearch
     ```
3. Al iniciarse por primera vez (o sin `master-key`), Meilisearch generará una. Verás mensajes como:

   ```text
   INFO  meilisearch_http::helpers: Server is running with a randomly generated master key.
   INFO  meilisearch_http::helpers: Listening on 127.0.0.1:7700
   ```

   Para producción, establece siempre una master-key:

   ```bash
   # Usando variable de entorno
   export MEILI_MASTER_KEY="TuClaveSuperSegura"

   # O al iniciar
   ./meilisearch --master-key="TuClaveSuperSegura"
   ```

   El servidor quedará disponible en [http://127.0.0.1:7700](http://127.0.0.1:7700).

### 1.3. Ubicación del Ejecutable en el Proyecto

Coloca el binario de Meilisearch en:

```bash
backend/meilisearch/meilisearch-windows-amd64.exe
```

Si lo mueves, actualiza los scripts del backend que lo invoquen.

### 1.4. Documentación Oficial

Para más detalles, consulta la [Documentación Oficial de Meilisearch](https://www.meilisearch.com/docs/).

---

## 2. Integración con el Backend de Biblioperson

### 2.1. Inicio Automático de Meilisearch

El backend (por ejemplo, `backend/scripts/api_conexion.py`) arranca Meilisearch si no detecta una instancia en ejecución, usando el ejecutable configurado.

### 2.2. Inicio Manual de Meilisearch

Si prefieres iniciarlo tú mismo:

```bash
python backend/scripts/levantar_meilisearch.py
```

O inicia el binario tal como en la sección 1.2. Asegúrate de hacerlo antes de arrancar el backend.

### 2.3. Persistencia de Datos (data.ms)

Meilisearch guarda índices y configuración en `data.ms` (creada en el directorio de ejecución).

> **Nota:** Mantén la misma carpeta `data.ms` si cambias la ubicación o método de arranque, para conservar tus índices.

---

## 3. Indexación de Contenidos

### 3.1. Indexación Completa

Para la importación inicial o masiva de datos:

```bash
python backend/scripts/indexar_meilisearch.py
```

Puedes usar opciones como `--hilos` o `--docs-per-request`. Revisa la ayuda:

```bash
python backend/scripts/indexar_meilisearch.py --help
```

### 3.2. Indexación Incremental

Para añadir solo nuevos registros:

```bash
python backend/scripts/indexar_meilisearch.py --indexar-nuevos
```

---

## 4. Verificación y Depuración del Índice

### 4.1. Comparación de Documentos

Usa el siguiente script para comparar IDs entre SQLite y Meilisearch:

```python
# backend/scripts/utils/verificar_indice_meili.py

import sqlite3
import meilisearch
import os

# --- Configuración ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(BASE_DIR, 'backend', 'data', 'biblioteca.db')
MEILI_URL = 'http://127.0.0.1:7700'
MEILI_INDEX_NAME = 'contenidos'
MEILI_API_KEY = None
# --- Fin Configuración ---

def verificar_sincronizacion():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contenidos")
        db_ids = set(str(row[0]) for row in cursor.fetchall())
        conn.close()
    except sqlite3.Error as e:
        print(f"Error en SQLite: {e}")
        return

    try:
        client = meilisearch.Client(MEILI_URL, MEILI_API_KEY)
        index = client.index(MEILI_INDEX_NAME)
        meili_ids = set()
        offset, limit = 0, 1000

        while True:
            docs = index.get_documents({'fields': ['id'], 'limit': limit, 'offset': offset})
            if not docs:
                break
            meili_ids.update(str(doc['id']) for doc in docs)
            if len(docs) < limit:
                break
            offset += limit

    except Exception as e:
        print(f"Error en Meilisearch: {e}")
        return

    faltantes = db_ids - meili_ids
    extras    = meili_ids - db_ids

    print(f"SQLite: {len(db_ids)} IDs, Meilisearch: {len(meili_ids)} IDs")
    if faltantes:
        print(f"IDs faltantes ({len(faltantes)}): {list(faltantes)[:20]}")
    if extras:
        print(f"IDs extraños ({len(extras)}): {list(extras)[:20]}")
    if not faltantes and not extras:
        print("¡Sincronización perfecta!")

if __name__ == '__main__':
    verificar_sincronizacion()
```

Guárdalo como `verificar_indice_meili.py`, ajusta la configuración y ejecútalo:

```bash
python backend/scripts/utils/verificar_indice_meili.py
```

### 4.2. Causas Comunes de Discrepancias

- **Tamaño de documentos:** límite ~100 KB JSON; payload global ~2 GB.
- **Errores de indexación:** timeouts, red o datos corruptos.
- **IDs duplicados/inválidos:** asegúrate de unicidad y formato.
- **Procesos interrumpidos:** scripts detenidos prematuramente.

### 4.3. Soluciones y Reindexación

- Identificar y corregir datos problemáticos.
- Reintentar indexación selectiva de documentos corregidos.
- Reindexación completa: borrar índice y volver a indexar (ver 5.1).

---

## 5. Mantenimiento del Índice

### 5.1. Borrar el Índice (Reindexación desde Cero)

1. Detén Meilisearch: cierra el proceso o servicio.
2. Elimina `data.ms`:

   ```bash
   rm -rf backend/meilisearch/data.ms
   ```

3. Reinicia Meilisearch: crea una carpeta `data.ms` vacía.
4. Indexación completa:

   ```bash
   python backend/scripts/indexar_meilisearch.py
   ```

---

## 6. Consideraciones Adicionales

### 6.1. Actualización de Meilisearch

1. Descarga el nuevo ejecutable (ver 1.1).
2. Detén la instancia actual.
3. Sustituye el binario.
4. Inicia la nueva versión.
5. Haz copia de seguridad de `data.ms` antes de actualizaciones mayores.

### 6.2. Migración a Otro Servidor/PC

1. Instala la misma versión o compatible.
2. Copia la carpeta `data.ms`.
3. Arranca Meilisearch en el nuevo entorno.

### 6.3. Seguridad en Producción

- **Master Key:** obligatoria (`MEILI_MASTER_KEY` o `--master-key`).
- **API Keys:** crea claves con permisos restringidos.
- **HTTPS:** expón bajo TLS.
- **Firewall:** limita acceso sólo a máquinas necesarias.