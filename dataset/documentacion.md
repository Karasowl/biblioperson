# Documentación de Depuración y Estandarización de Datos

## Objetivo

Crear una base de datos depurada y estandarizada a partir de múltiples fuentes textuales (mensajes, escritos, poemas, canciones, etc.) para alimentar un backend que sirva como base de un "gemelo digital" consultable por IA.

---

## Estructura de Carpetas

```
dataset/
    scripts/      # Scripts de depuración, conversión, segmentación
    fuentes/      # Archivos originales por fuente (Telegram, Facebook, Escritos, etc.)
    salidas/      # Archivos depurados y unificados por fuente o el dataset final
    documentacion.md  # Este archivo
```

---

## Formato Estándar del Dataset (NDJSON)

Cada línea es un JSON con los siguientes campos:

- `id`: número entero incremental (1, 2, 3, ...)
- `texto`: contenido textual de la entrada (mensaje, párrafo, poema, etc.)
- `fecha`: formato preferido `YYYY-MM-DD`, si no hay día, `YYYY-MM`, si solo año, `YYYY`
- `fuente`: carpeta principal de donde proviene el archivo (ej: Telegram, Escritos, Poemas)
- `contexto`: ruta completa del archivo original (incluyendo subcarpetas y nombre de archivo)

**Ejemplo:**
```json
{"id": 1, "texto": "Este es el primer párrafo de un libro...", "fecha": "2020-05", "fuente": "escritos", "contexto": "contenido/escritos/La Permanencia.md"}
{"id": 2, "texto": "Texto completo del poema...", "fecha": "2018", "fuente": "poemas", "contexto": "contenido/creativo/poemas/003.md"}
{"id": 3, "texto": "Mensaje de Telegram...", "fecha": "2019-11-19", "fuente": "Telegram", "contexto": "contenido/redes_sociales/Telegram/debates_ismael_filtrado.ndjson"}
```

---

## Reglas de Segmentación

### 1. Poemas y Canciones
- **Segmentación:** El archivo completo es una sola entrada.
- **Fuente:** Carpeta padre (ej: "poemas", "canciones").
- **Contexto:** Ruta completa del archivo.

### 2. Mensajes y Redes Sociales
- **Segmentación:** Cada mensaje, comentario o entrada es una sola entrada (ya suelen venir así en JSON/NDJSON).
- **Fuente:** Carpeta padre (ej: "Telegram", "Facebook").
- **Contexto:** Ruta completa del archivo.

### 3. Escritos y Libros
- **Segmentación:** Por doble salto de línea (`\n\n`), es decir, por párrafos.
- **Fuente:** Carpeta padre (ej: "escritos").
- **Contexto:** Ruta completa del archivo.

---

## Pasos/Fases del Proceso de Depuración y Estandarización

1. **Conversión de formatos**
   - Convertir todos los archivos Word, Excel, PDF, etc. a Markdown (`.md`).
   - Herramienta sugerida: [Pandoc](https://pandoc.org/) o scripts automáticos.
   - **El usuario debe:** Ejecutar la conversión o indicar la carpeta de entrada.

2. **Conversión de Markdown a NDJSON**
   - Segmentar los archivos Markdown por doble salto de línea (`\n\n`) para obtener párrafos.
   - Generar una entrada por párrafo, con los campos estándar.
   - **Automático:** El script lo hace.

3. **Procesamiento de archivos JSON/NDJSON**
   - Procesar mensajes, comentarios, etc. (Telegram, Facebook, etc.)
   - Cada mensaje es una entrada.
   - **Automático:** El script lo hace.

4. **Procesamiento de poemas y canciones**
   - Cada archivo es una sola entrada.
   - **Automático:** El script lo hace.

5. **Extracción de metadatos**
   - Extraer fecha (si está disponible en el archivo o metadatos).
   - Inferir fuente y contexto a partir de la ruta del archivo.
   - **Automático:** El script lo hace, pero el usuario puede revisar/corregir si es necesario.

6. **Eliminación de duplicados**
   - Detectar y eliminar entradas duplicadas (por texto exacto o similaridad).
   - **Automático:** El script puede sugerir duplicados, el usuario puede revisar antes de eliminar definitivamente.

7. **Estandarización de campos**
   - Asegurar que todos los campos requeridos estén presentes y en el formato correcto.
   - **Automático:** El script lo hace.

8. **Unificación y exportación**
   - Unir todas las entradas depuradas en un solo archivo NDJSON final.
   - **Automático:** El script lo hace.

---

## ¿Qué debe hacer el usuario y qué hace el script?

- **Usuario:**
  - Seleccionar la carpeta/fuente a procesar.
  - Indicar la categoría (poema/canción, mensaje/red social, escrito/libro).
  - Ejecutar la conversión de formatos si es necesario (Word a Markdown, etc.).
  - Revisar sugerencias de duplicados antes de eliminar.
  - Revisar/corregir fechas o metadatos si el script no los puede inferir.

- **Script:**
  - Segmentar archivos según la categoría.
  - Extraer texto, fecha, fuente y contexto.
  - Generar el NDJSON con el formato estándar.
  - Sugerir duplicados.
  - Unificar y exportar el dataset final.

---

## Consideraciones
- El campo `autor` se omite porque el dataset es para un solo gemelo digital.
- Si no hay fecha, dejar el campo vacío o intentar inferirla de la carpeta/archivo.
- El campo `contexto` es importante para poder rastrear el origen del texto.
- Si se requiere segmentar de otra forma, se puede ajustar el script de depuración.

---

## Flujo de Trabajo
1. Colocar los archivos originales en `dataset/fuentes/`.
2. Ejecutar los scripts de depuración y segmentación en `dataset/scripts/`.
3. Guardar los archivos depurados en `dataset/salidas/`.
4. Unificar todo en un solo archivo NDJSON final (`dataset/salidas/dataset_final.ndjson`).
5. El backend consumirá este archivo para exponerlo al frontend y a la IA.

---

## Futuras Mejoras
- Añadir módulos de enriquecimiento (temas, tags, etc.) usando IA.
- Permitir añadir más autores y fuentes.
- Mejorar la extracción de metadatos (fecha, contexto, etc.). 