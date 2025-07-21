# Guía de Procesamiento de Datos - Biblioperson

## Objetivo

Esta guía detalla el proceso completo para convertir múltiples fuentes textuales (mensajes, escritos, poemas, canciones, etc.) en una base de datos depurada y estandarizada que alimente el backend de Biblioperson como base de un "gemelo digital" consultable por IA.

## 🏗️ Arquitectura del Procesamiento

```
Archivos Originales → Conversión → Segmentación → Enriquecimiento → NDJSON → Base de Datos
     (Múltiples         (Loaders)    (Reglas)      (Metadatos)     (Estándar)   (SQLite +
      formatos)                                                                   Meilisearch)
```

## 📁 Estructura de Directorios

### Estructura Recomendada

```
dataset/
├── raw_data/                    # Archivos originales organizados por autor
│   ├── autor1/
│   │   ├── libro1.pdf
│   │   ├── articulo1.docx
│   │   └── poemas/
│   │       ├── poema1.txt
│   │       └── poema2.md
│   └── autor2/
│       ├── ensayo1.txt
│       └── redes_sociales/
│           └── telegram_export.ndjson
├── processed_data/              # Archivos NDJSON procesados
│   ├── autor1_libro1.ndjson
│   ├── autor1_articulo1.ndjson
│   ├── autor1_poemas.ndjson
│   └── autor2_ensayo1.ndjson
├── output/                      # Resultados finales y unificados
│   └── unified/
│       └── dataset_final.ndjson
└── scripts/                     # Scripts de procesamiento
    └── app_depuracion.py
```

### Organización por Autor

**Principio fundamental**: Cada autor tiene su propio directorio en `raw_data/`

```
raw_data/
├── garcia_marquez/              # Nombre del autor como directorio
│   ├── cien_anos_soledad.pdf    # Libros principales
│   ├── cronica_muerte.docx      # Otros trabajos
│   └── entrevistas/             # Subdirectorios por tipo
│       └── entrevista_1982.txt
├── borges/
│   ├── ficciones.pdf
│   ├── laberintos.txt
│   └── poemas/
│       ├── fervor.md
│       └── luna_enfrente.txt
└── usuario_personal/            # Para contenido personal
    ├── escritos/
    │   ├── ensayo1.md
    │   └── reflexiones.txt
    ├── poemas/
    │   └── mis_poemas.txt
    └── redes_sociales/
        ├── telegram_export.ndjson
        └── twitter_backup.json
```

## 📋 Formato Estándar NDJSON

### Estructura de Campos

Cada línea del archivo NDJSON es un objeto JSON con estos campos:

```json
{
  "id_unico": "autor_documento_001",
  "texto_segmento": "Contenido textual del segmento",
  "autor_documento": "Nombre del Autor",
  "titulo_documento": "Título del Documento",
  "orden_segmento_documento": 1,
  "tipo_segmento": "parrafo",
  "jerarquia_contextual": {"capitulo": "1", "seccion": "A"},
  "idioma_documento": "es",
  "fecha_publicacion_documento": "2023-12-01",
  "fuente_original": "escritos",
  "contexto_archivo": "raw_data/autor/libro.pdf",
  "hash_documento_original": "abc123def456"
}
```

### Campos Explicados

| Campo | Descripción | Ejemplo | Obligatorio |
|-------|-------------|---------|-------------|
| `id_unico` | Identificador único del segmento | `"garcia_marquez_cien_anos_001"` | ✅ |
| `texto_segmento` | Contenido textual | `"Muchos años después..."` | ✅ |
| `autor_documento` | Nombre del autor | `"Gabriel García Márquez"` | ✅ |
| `titulo_documento` | Título del documento | `"Cien años de soledad"` | ✅ |
| `orden_segmento_documento` | Posición en el documento | `1, 2, 3...` | ✅ |
| `tipo_segmento` | Tipo de contenido | `"parrafo", "titulo", "lista"` | ✅ |
| `jerarquia_contextual` | Estructura del documento | `{"capitulo": "1"}` | ✅ |
| `idioma_documento` | Código ISO del idioma | `"es", "en", "fr"` | ✅ |
| `fecha_publicacion_documento` | Fecha de publicación | `"1967-05-30"` | ⚠️ |
| `fuente_original` | Tipo de fuente | `"escritos", "poemas", "redes_sociales"` | ✅ |
| `contexto_archivo` | Ruta del archivo original | `"raw_data/autor/archivo.pdf"` | ✅ |
| `hash_documento_original` | Hash del documento | `"abc123def456"` | ✅ |

### Ejemplos por Tipo de Contenido

#### Libro/Ensayo
```json
{"id_unico":"garcia_marquez_cien_anos_001","texto_segmento":"Muchos años después, frente al pelotón de fusilamiento, el coronel Aureliano Buendía había de recordar aquella tarde remota en que su padre lo llevó a conocer el hielo.","autor_documento":"Gabriel García Márquez","titulo_documento":"Cien años de soledad","orden_segmento_documento":1,"tipo_segmento":"parrafo","jerarquia_contextual":{"capitulo":"1"},"idioma_documento":"es","fecha_publicacion_documento":"1967-05-30","fuente_original":"escritos","contexto_archivo":"raw_data/garcia_marquez/cien_anos_soledad.pdf","hash_documento_original":"abc123def456"}
```

#### Poema
```json
{"id_unico":"borges_fervor_001","texto_segmento":"Las calles de Buenos Aires\nya son mi entraña.\nNo las ávidas calles,\nincómodas de turba y ajetreo,\nsino las calles desganadas del barrio,\ncasi invisibles de habituales,\nenternecidas de penumbra y de ocaso","autor_documento":"Jorge Luis Borges","titulo_documento":"Fervor de Buenos Aires","orden_segmento_documento":1,"tipo_segmento":"poema_completo","jerarquia_contextual":{"seccion":"Calles"},"idioma_documento":"es","fecha_publicacion_documento":"1923","fuente_original":"poemas","contexto_archivo":"raw_data/borges/fervor_buenos_aires.txt","hash_documento_original":"def456ghi789"}
```

#### Mensaje de Red Social
```json
{"id_unico":"usuario_telegram_001","texto_segmento":"Interesante reflexión sobre la naturaleza del tiempo en la física cuántica. ¿Será que el tiempo es realmente una ilusión como sugiere Einstein?","autor_documento":"Usuario Personal","titulo_documento":"Conversaciones Telegram","orden_segmento_documento":1,"tipo_segmento":"mensaje","jerarquia_contextual":{"chat":"Debates Filosofía","fecha_mensaje":"2023-11-15"},"idioma_documento":"es","fecha_publicacion_documento":"2023-11-15","fuente_original":"redes_sociales","contexto_archivo":"raw_data/usuario_personal/telegram_export.ndjson","hash_documento_original":"ghi789jkl012"}
```

## 🔧 Reglas de Segmentación

### 1. Poemas y Canciones

**Estrategia**: Archivo completo como una sola entrada

**Características**:
- **Un segmento por archivo**: Todo el poema/canción en un solo registro
- **Preservación de estructura**: Mantiene saltos de línea y estrofas
- **Tipo de segmento**: `"poema_completo"` o `"cancion_completa"`
- **Jerarquía contextual**: Puede incluir sección, libro, álbum

**Ejemplo de procesamiento**:
```
Archivo: raw_data/poeta/mi_poema.txt
↓
Un solo registro NDJSON con todo el contenido
```

### 2. Mensajes y Redes Sociales

**Estrategia**: Cada mensaje es una entrada independiente

**Características**:
- **Un segmento por mensaje**: Cada mensaje/comentario/post individual
- **Preservación de metadatos**: Fecha, hora, contexto de conversación
- **Tipo de segmento**: `"mensaje"`, `"comentario"`, `"post"`
- **Jerarquía contextual**: Chat, hilo, conversación

**Ejemplo de procesamiento**:
```
Archivo NDJSON con 100 mensajes
↓
100 registros NDJSON individuales
```

### 3. Escritos y Libros

**Estrategia**: Segmentación por párrafos (doble salto de línea `\n\n`)

**Características**:
- **Un segmento por párrafo**: División natural del texto
- **Detección de títulos**: Párrafos cortos y aislados como títulos
- **Tipo de segmento**: `"parrafo"`, `"titulo"`, `"subtitulo"`
- **Jerarquía contextual**: Capítulo, sección, subsección

**Ejemplo de procesamiento**:
```
Archivo con 50 párrafos
↓
50 registros NDJSON (párrafos + títulos)
```

### 4. Documentos Estructurados (PDF, DOCX)

**Estrategia**: Segmentación basada en estructura del documento

**Características**:
- **Respeta jerarquía**: Títulos, subtítulos, párrafos
- **Preserva formato**: Listas, tablas, citas
- **Tipo de segmento**: `"titulo"`, `"parrafo"`, `"lista"`, `"tabla"`, `"cita"`
- **Jerarquía contextual**: Estructura completa del documento

### 5. Datos Tabulares (CSV, Excel)

**Estrategia**: Conversión a formato narrativo

**Características**:
- **Filas como registros**: Cada fila se convierte en texto descriptivo
- **Encabezados como contexto**: Nombres de columnas proporcionan estructura
- **Tipo de segmento**: `"registro_datos"`, `"encabezado_tabla"`
- **Jerarquía contextual**: Hoja, tabla, sección

## 🔄 Proceso de Depuración y Estandarización

### Fase 1: Conversión de Formatos

**Objetivo**: Convertir todos los archivos a formatos procesables

**Acciones**:
1. **Detectar formato** del archivo de entrada
2. **Seleccionar loader** apropiado automáticamente
3. **Convertir contenido** a estructura común
4. **Validar extracción** de contenido

**Herramientas**:
- **Loaders específicos**: Para cada formato de archivo
- **ProfileManager**: Selección automática de loader
- **Validación**: Verificación de contenido extraído

```python
# Ejemplo de conversión automática
from dataset.processing.profile_manager import ProfileManager

manager = ProfileManager()
resultados = manager.process_file("documento.pdf", profile_name="book_structure")
```

### Fase 2: Segmentación Inteligente

**Objetivo**: Dividir contenido según reglas específicas por tipo

**Acciones**:
1. **Identificar tipo** de contenido (libro, poema, mensaje)
2. **Aplicar reglas** de segmentación correspondientes
3. **Generar segmentos** con metadatos apropiados
4. **Validar coherencia** de segmentación

**Algoritmos**:
- **Detección de párrafos**: Por doble salto de línea
- **Identificación de títulos**: Por longitud y posición
- **Preservación de estructura**: Para poemas y código
- **Extracción de listas**: Para contenido enumerado

### Fase 3: Enriquecimiento de Metadatos

**Objetivo**: Añadir información contextual y estructural

**Acciones**:
1. **Extraer fecha** del archivo o contenido
2. **Inferir autor** del directorio padre
3. **Detectar idioma** del contenido
4. **Generar jerarquía** contextual
5. **Calcular hash** del documento original

**Fuentes de metadatos**:
- **Nombre de archivo**: Fechas, títulos, versiones
- **Propiedades de archivo**: Fecha de creación/modificación
- **Estructura de directorios**: Autor, categoría, tipo
- **Contenido del documento**: Títulos, fechas internas
- **Metadatos embebidos**: PDF, DOCX properties

### Fase 4: Eliminación de Duplicados

**Objetivo**: Detectar y eliminar contenido duplicado

**Estrategias**:
1. **Hash exacto**: Para duplicados idénticos
2. **Similaridad textual**: Para duplicados aproximados
3. **Análisis semántico**: Para contenido similar
4. **Validación manual**: Para casos ambiguos

**Algoritmos**:
```python
# Detección de duplicados por hash
import hashlib

def detect_exact_duplicates(segments):
    seen_hashes = set()
    duplicates = []
    
    for segment in segments:
        text_hash = hashlib.md5(segment['texto_segmento'].encode()).hexdigest()
        if text_hash in seen_hashes:
            duplicates.append(segment)
        else:
            seen_hashes.add(text_hash)
    
    return duplicates

# Detección por similaridad
from difflib import SequenceMatcher

def detect_similar_duplicates(segments, threshold=0.9):
    duplicates = []
    
    for i, seg1 in enumerate(segments):
        for j, seg2 in enumerate(segments[i+1:], i+1):
            similarity = SequenceMatcher(None, seg1['texto_segmento'], seg2['texto_segmento']).ratio()
            if similarity > threshold:
                duplicates.append((seg1, seg2, similarity))
    
    return duplicates
```

### Fase 5: Estandarización de Campos

**Objetivo**: Asegurar consistencia en formato y contenido

**Validaciones**:
1. **Campos obligatorios**: Verificar presencia de todos los campos requeridos
2. **Formato de fechas**: Normalizar a ISO 8601
3. **Códigos de idioma**: Validar códigos ISO 639-1
4. **Tipos de segmento**: Verificar vocabulario controlado
5. **Jerarquía contextual**: Validar estructura JSON

**Normalizaciones**:
```python
# Normalización de fechas
from datetime import datetime
import re

def normalize_date(date_string):
    """Normaliza diferentes formatos de fecha a ISO 8601."""
    if not date_string:
        return None
    
    # Patrones comunes
    patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{4})-(\d{2})',         # YYYY-MM
        r'(\d{4})',                 # YYYY
        r'(\d{2})/(\d{2})/(\d{4})', # MM/DD/YYYY
        r'(\d{2})-(\d{2})-(\d{4})', # DD-MM-YYYY
    ]
    
    for pattern in patterns:
        match = re.match(pattern, date_string.strip())
        if match:
            # Procesar según el patrón
            return format_date(match.groups())
    
    return None

# Normalización de tipos de segmento
VOCABULARIO_TIPOS = {
    'parrafo', 'titulo', 'subtitulo', 'lista', 'cita', 'nota',
    'tabla', 'codigo', 'formula', 'referencia', 'poema_completo',
    'cancion_completa', 'mensaje', 'comentario', 'post'
}

def validate_segment_type(tipo):
    """Valida que el tipo de segmento esté en el vocabulario controlado."""
    return tipo.lower() in VOCABULARIO_TIPOS
```

### Fase 6: Unificación y Exportación

**Objetivo**: Combinar todos los archivos procesados en un dataset final

**Acciones**:
1. **Recopilar archivos** NDJSON procesados
2. **Asignar IDs únicos** globales
3. **Validar integridad** del dataset completo
4. **Generar estadísticas** de procesamiento
5. **Exportar dataset final** unificado

**Estructura final**:
```
output/
├── unified/
│   ├── dataset_final.ndjson      # Dataset completo
│   ├── estadisticas.json         # Métricas del procesamiento
│   ├── errores.log              # Log de errores encontrados
│   └── metadatos.json           # Información del dataset
└── por_autor/
    ├── garcia_marquez.ndjson    # Dataset por autor
    ├── borges.ndjson
    └── usuario_personal.ndjson
```

## 🔍 División de Responsabilidades

### 👤 Responsabilidades del Usuario

1. **Organización inicial**:
   - Colocar archivos en estructura de directorios correcta
   - Nombrar directorios con nombres de autores
   - Organizar archivos por tipo cuando sea necesario

2. **Configuración de procesamiento**:
   - Seleccionar perfil de procesamiento apropiado
   - Indicar tipo de contenido cuando no sea obvio
   - Configurar parámetros específicos si es necesario

3. **Revisión y validación**:
   - Revisar sugerencias de duplicados antes de eliminar
   - Corregir fechas o metadatos cuando el script no pueda inferirlos
   - Validar resultados de segmentación en casos complejos

4. **Conversión de formatos**:
   - Convertir archivos muy específicos a formatos estándar
   - Preparar archivos corruptos o con problemas de encoding

### 🤖 Responsabilidades del Script

1. **Procesamiento automático**:
   - Detectar formato de archivo automáticamente
   - Seleccionar loader y estrategia de segmentación apropiados
   - Extraer contenido y metadatos disponibles

2. **Segmentación inteligente**:
   - Aplicar reglas de segmentación según tipo de contenido
   - Detectar títulos, párrafos, listas automáticamente
   - Preservar estructura y formato cuando sea relevante

3. **Enriquecimiento de datos**:
   - Inferir autor del directorio padre
   - Extraer fechas de nombres de archivo y metadatos
   - Generar jerarquía contextual automáticamente
   - Calcular hashes y IDs únicos

4. **Control de calidad**:
   - Detectar duplicados exactos y similares
   - Validar formato y consistencia de datos
   - Generar reportes de errores y estadísticas
   - Sugerir correcciones cuando sea posible

## 📊 Flujo de Trabajo Completo

### Preparación

```bash
# 1. Organizar archivos
mkdir -p raw_data/mi_autor
cp mis_documentos/* raw_data/mi_autor/

# 2. Verificar estructura
ls -la raw_data/mi_autor/
```

### Procesamiento

```bash
# 3. Ejecutar procesamiento
cd dataset
python scripts/app_depuracion.py --autor="mi_autor" --profile="book_structure"

# 4. Verificar resultados
ls -la processed_data/
head -n 5 processed_data/mi_autor_*.ndjson
```

### Validación

```bash
# 5. Validar formato NDJSON
python -c "
import json
with open('processed_data/mi_autor_libro.ndjson') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f'Error en línea {i}: {e}')
"

# 6. Estadísticas básicas
wc -l processed_data/*.ndjson
grep -c '"tipo_segmento":"titulo"' processed_data/*.ndjson
```

### Unificación

```bash
# 7. Unificar dataset
python scripts/unificar_dataset.py --input="processed_data/" --output="output/unified/"

# 8. Verificar dataset final
wc -l output/unified/dataset_final.ndjson
cat output/unified/estadisticas.json
```

### Importación

```bash
# 9. Importar a base de datos
cd ../backend/scripts
python importar_completo.py --source="../../dataset/output/unified/dataset_final.ndjson"

# 10. Verificar importación
python -c "
import sqlite3
conn = sqlite3.connect('../data/biblioteca.db')
print('Segmentos importados:', conn.execute('SELECT COUNT(*) FROM segmentos').fetchone()[0])
print('Autores únicos:', conn.execute('SELECT COUNT(DISTINCT autor_documento) FROM segmentos').fetchone()[0])
"
```

## 🔧 Consideraciones Técnicas

### Rendimiento

- **Procesamiento por streaming**: Para archivos grandes
- **Paralelización**: Procesamiento simultáneo de múltiples archivos
- **Caché inteligente**: Evitar reprocesar archivos sin cambios
- **Optimización de memoria**: Liberación de recursos durante procesamiento

### Escalabilidad

- **Procesamiento incremental**: Añadir nuevos documentos sin reprocesar todo
- **Versionado de datasets**: Mantener historial de cambios
- **Distribución de carga**: Para bibliotecas muy grandes
- **Monitoreo de recursos**: Control de uso de CPU y memoria

### Robustez

- **Manejo de errores**: Continuar procesamiento aunque algunos archivos fallen
- **Validación exhaustiva**: Verificar integridad en cada paso
- **Recuperación de errores**: Reanudar procesamiento desde puntos de control
- **Logging detallado**: Trazabilidad completa del proceso

## 📚 Próximos Pasos

Después de completar el procesamiento de datos:

1. **Importación**: [Gestión de Datos](GUIA_GESTION_DATOS.md) - Importar NDJSON a base de datos
2. **Configuración**: [Meilisearch](GUIA_MEILISEARCH.md) - Configurar motor de búsqueda
3. **Uso**: [Inicio Rápido](INICIO_RAPIDO.md) - Usar la aplicación completa
4. **Extensión**: [Loaders](GUIA_LOADERS.md) - Añadir soporte para nuevos formatos

## 🆘 Solución de Problemas Comunes

### Error: "Archivo no procesable"

**Síntomas**: El script no puede leer ciertos archivos

**Causas comunes**:
- Archivo corrupto o formato no estándar
- Encoding incorrecto
- Permisos de archivo insuficientes

**Soluciones**:
```bash
# Verificar encoding
file -i mi_archivo.txt

# Convertir encoding si es necesario
iconv -f ISO-8859-1 -t UTF-8 mi_archivo.txt > mi_archivo_utf8.txt

# Verificar permisos
ls -la mi_archivo.txt
chmod 644 mi_archivo.txt
```

### Error: "Segmentación incorrecta"

**Síntomas**: Los párrafos se dividen mal o los títulos no se detectan

**Causas comunes**:
- Formato de texto inconsistente
- Reglas de segmentación no apropiadas para el tipo de documento

**Soluciones**:
```python
# Usar perfil específico
manager.process_file("archivo.txt", profile_name="poetry_structure")

# Configurar parámetros manualmente
manager.configure_profile("custom", {
    "segmentation_strategy": "sentence_based",
    "min_segment_length": 30
})
```

### Error: "Metadatos faltantes"

**Síntomas**: Fechas o títulos no se extraen correctamente

**Causas comunes**:
- Nombres de archivo sin información de fecha
- Metadatos no estándar en documentos

**Soluciones**:
```python
# Proporcionar metadatos manualmente
resultados = manager.process_file(
    "archivo.pdf",
    override_metadata={
        "fecha_publicacion": "2023-01-01",
        "titulo_documento": "Mi Título"
    }
)
```

Esta guía proporciona todo lo necesario para entender y ejecutar el proceso completo de conversión de documentos a NDJSON en Biblioperson. Para casos específicos o problemas técnicos, consulta las guías especializadas de loaders y especificaciones técnicas.