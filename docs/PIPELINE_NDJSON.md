# Pipeline NDJSON - Guía Práctica

## Visión General del Pipeline

El pipeline NDJSON es el corazón del procesamiento de documentos en Biblioperson. Convierte documentos de cualquier formato en registros estructurados listos para búsqueda semántica.

```
Documento Original → Extracción → Segmentación → Enriquecimiento → NDJSON → Base de Datos
```

## Estructura del Directorio de Trabajo

```
dataset/
├── raw_data/
│   ├── autor1/
│   │   ├── libro1.pdf
│   │   └── articulo1.docx
│   └── autor2/
│       └── ensayo1.txt
├── processed_data/
│   ├── autor1_libro1.ndjson
│   ├── autor1_articulo1.ndjson
│   └── autor2_ensayo1.ndjson
└── scripts/
    └── app_depuracion.py
```

## Paso a Paso: De Documento a NDJSON

### 1. Preparar el Documento

**Estructura requerida:**
```
raw_data/[nombre_autor]/[documento].[extensión]
```

**Formatos soportados:**
- PDF (`.pdf`)
- Word (`.docx`)
- Texto plano (`.txt`)
- Markdown (`.md`)

**Ejemplo:**
```
raw_data/
└── garcia_marquez/
    └── cien_anos_soledad.pdf
```

### 2. Ejecutar el Procesamiento

```bash
cd dataset
python scripts/app_depuracion.py
```

**Lo que sucede internamente:**
1. **Extracción**: Convierte PDF/DOCX a texto plano
2. **Segmentación**: Divide en párrafos, títulos, listas, etc.
3. **Enriquecimiento**: Añade metadatos y jerarquía contextual
4. **Generación**: Crea archivo NDJSON en `processed_data/`

### 3. Verificar el Resultado

**Archivo generado:**
```
processed_data/garcia_marquez_cien_anos_soledad.ndjson
```

**Contenido de ejemplo:**
```json
{"id_unico":"garcia_marquez_cien_anos_soledad_001","texto_segmento":"Muchos años después, frente al pelotón de fusilamiento, el coronel Aureliano Buendía había de recordar aquella tarde remota en que su padre lo llevó a conocer el hielo.","autor_documento":"Gabriel García Márquez","titulo_documento":"Cien años de soledad","orden_segmento_documento":1,"tipo_segmento":"parrafo","jerarquia_contextual":{"capitulo":"1"},"idioma_documento":"es","fecha_publicacion_documento":"1967-05-30","hash_documento_original":"abc123def456"}
{"id_unico":"garcia_marquez_cien_anos_soledad_002","texto_segmento":"El mundo era tan reciente, que muchas cosas carecían de nombre, y para mencionarlas había que señalarlas con el dedo.","autor_documento":"Gabriel García Márquez","titulo_documento":"Cien años de soledad","orden_segmento_documento":2,"tipo_segmento":"parrafo","jerarquia_contextual":{"capitulo":"1"},"idioma_documento":"es","fecha_publicacion_documento":"1967-05-30","hash_documento_original":"abc123def456"}
```

## Campos del NDJSON Explicados

### Campos Obligatorios

| Campo | Descripción | Ejemplo |
|-------|-------------|----------|
| `id_unico` | Identificador único del segmento | `"autor_libro_001"` |
| `texto_segmento` | Contenido textual del segmento | `"Este es el párrafo..."` |
| `autor_documento` | Nombre del autor | `"Gabriel García Márquez"` |
| `orden_segmento_documento` | Posición en el documento original | `1, 2, 3...` |
| `tipo_segmento` | Tipo de contenido | `"parrafo", "titulo", "lista"` |

### Campos de Metadatos

| Campo | Descripción | Ejemplo |
|-------|-------------|----------|
| `titulo_documento` | Título del documento | `"Cien años de soledad"` |
| `idioma_documento` | Código ISO del idioma | `"es", "en", "fr"` |
| `fecha_publicacion_documento` | Fecha de publicación | `"1967-05-30"` |
| `jerarquia_contextual` | Estructura del documento | `{"capitulo": "1", "seccion": "A"}` |

## Tipos de Segmento

### Vocabulario Controlado

- **`parrafo`**: Párrafo de texto normal
- **`titulo`**: Títulos y encabezados
- **`subtitulo`**: Subtítulos y subencabezados
- **`lista`**: Elementos de listas
- **`cita`**: Citas textuales
- **`nota`**: Notas al pie o marginales
- **`tabla`**: Contenido de tablas
- **`codigo`**: Bloques de código
- **`formula`**: Fórmulas matemáticas
- **`referencia`**: Referencias bibliográficas

### Ejemplos por Tipo

```json
// Título
{"tipo_segmento":"titulo","texto_segmento":"Capítulo 1: Los Fundamentos","jerarquia_contextual":{"capitulo":"1"}}

// Párrafo
{"tipo_segmento":"parrafo","texto_segmento":"El concepto de realidad mágica..."}

// Lista
{"tipo_segmento":"lista","texto_segmento":"• Primer elemento de la lista"}

// Cita
{"tipo_segmento":"cita","texto_segmento":"\"La realidad supera a la ficción\" - García Márquez"}
```

## Jerarquía Contextual

### Estructura Flexible

La `jerarquia_contextual` se adapta al tipo de documento:

**Libro académico:**
```json
{"jerarquia_contextual": {
  "parte": "I",
  "capitulo": "3",
  "seccion": "3.2",
  "subseccion": "3.2.1"
}}
```

**Artículo científico:**
```json
{"jerarquia_contextual": {
  "seccion": "Metodología",
  "subseccion": "Análisis de datos"
}}
```

**Novela:**
```json
{"jerarquia_contextual": {
  "capitulo": "5"
}}
```

## Solución de Problemas

### Error: "No se puede procesar el archivo"

**Causa común**: Archivo corrupto o formato no soportado

**Solución:**
```bash
# Verificar que el archivo se puede abrir
# Para PDF:
python -c "import PyPDF2; print('PDF OK')"

# Para DOCX:
python -c "import docx; print('DOCX OK')"
```

### Error: "Autor no detectado"

**Causa**: El nombre del directorio no sigue la convención

**Solución:**
```bash
# Estructura correcta:
raw_data/nombre_autor/documento.pdf

# NO:
raw_data/documentos/autor/documento.pdf
```

### Error: "NDJSON malformado"

**Verificación:**
```bash
# Validar NDJSON
python -c "
import json
with open('processed_data/archivo.ndjson') as f:
    for i, line in enumerate(f):
        try:
            json.loads(line)
        except:
            print(f'Error en línea {i+1}')
"
```

### Error: "Texto muy largo"

**Causa**: Segmentos que exceden límites de tokens

**Solución**: Ajustar parámetros de segmentación en el script de procesamiento

## Optimización del Pipeline

### Procesamiento por Lotes

```bash
# Procesar múltiples autores
for autor in raw_data/*/; do
    echo "Procesando $autor"
    python scripts/app_depuracion.py --autor="$(basename "$autor")"
done
```

### Verificación de Calidad

```bash
# Contar segmentos por tipo
grep -o '"tipo_segmento":"[^"]*"' processed_data/*.ndjson | sort | uniq -c

# Verificar autores únicos
grep -o '"autor_documento":"[^"]*"' processed_data/*.ndjson | sort | uniq

# Estadísticas de longitud de texto
grep -o '"texto_segmento":"[^"]*"' processed_data/*.ndjson | wc -c
```

## Integración con la Base de Datos

Una vez generados los archivos NDJSON:

```bash
# Importar a SQLite + Meilisearch
cd ../backend/scripts
python importar_completo.py

# Verificar importación
python -c "
import sqlite3
conn = sqlite3.connect('../data/biblioteca.db')
print('Segmentos importados:', conn.execute('SELECT COUNT(*) FROM segmentos').fetchone()[0])
"
```

## Mejores Prácticas

1. **Nombres de archivo**: Usa nombres descriptivos sin espacios
2. **Estructura de directorios**: Un directorio por autor
3. **Metadatos**: Incluye fechas y títulos precisos cuando sea posible
4. **Verificación**: Siempre valida el NDJSON antes de importar
5. **Backup**: Mantén copias de los archivos originales
6. **Versionado**: Usa nombres de archivo que incluyan versión si actualizas documentos

## Próximos Pasos

Después de generar NDJSON exitosamente:

1. **Importar**: `GUIA_GESTION_DATOS.md`
2. **Configurar búsqueda**: `GUIA_MEILISEARCH.md`
3. **Usar la aplicación**: `INICIO_RAPIDO.md`