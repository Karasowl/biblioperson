# Indexación en Meilisearch

Este README documenta el proceso de indexación de documentos en Meilisearch.

## Iniciar el servidor Meilisearch

Para iniciar el servidor Meilisearch con configuración optimizada:

```bash
# Desde la carpeta de Meilisearch
cd E:\dev-projects\biblioperson\backend\meilisearch
.\meilisearch-windows-amd64.exe --max-indexing-threads 6
```

## Indexar documentos en Meilisearch

Para indexar documentos desde la base de datos SQLite a Meilisearch:

```bash
# Desde la carpeta de scripts del backend
cd E:\dev-projects\biblioperson\backend\scripts
python indexar_meilisearch.py --hilos 12
```

## Opciones de configuración para la indexación

El script acepta varios parámetros para optimizar el rendimiento:

```bash
python indexar_meilisearch.py [opciones]

Opciones:
  --tabla NOMBRE          Nombre de la tabla que contiene los documentos (por defecto: contenidos)
  --db-path RUTA          Ruta a la base de datos SQLite (por defecto: E:\dev-projects\biblioperson\backend\data\biblioteca.db)
  --hilos NUM             Número de hilos a utilizar (por defecto: 8)
  --batch-size NUM        Tamaño del lote de la base de datos (por defecto: 5000)
  --docs-per-request NUM  Documentos por solicitud a Meilisearch (por defecto: 1000)
  --timeout NUM           Timeout para solicitudes HTTP en segundos (por defecto: 60)
  --listar                Listar todas las tablas disponibles en la base de datos
```

## Configuración recomendada para mejor rendimiento

Para obtener el mejor rendimiento en un sistema de gama alta:

```bash
# Para CPU i7/i9 con 32GB RAM:
python indexar_meilisearch.py --hilos 12 --batch-size 5000 --docs-per-request 1000 --timeout 120
```

## Rendimiento esperado

Con la configuración recomendada, se pueden alcanzar velocidades de indexación de:
- Aproximadamente 450-500 documentos por segundo
- Completar la indexación de 234,528 documentos en ~8-10 minutos

## Configuración del índice

El script configura automáticamente el índice "documentos" en Meilisearch con:
- Clave primaria: "id"
- Atributos buscables: contenido_texto, autor, contexto, url_original
- Atributos filtrables: id, autor, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, idioma
- Atributos ordenables: id, fecha_creacion, fecha_importacion
- Incluye los embeddings para cada documento

## Solución de problemas

- Si ves errores relacionados con "0 successful tasks and X failed tasks", revisa la configuración del índice
- Para reiniciar la indexación desde cero, elimina el índice desde la interfaz web o API de Meilisearch 