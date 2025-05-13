# Estrategia de Procesamiento: Refactorización 2023-2024

> **Documento técnico:** Establece la estrategia de refactorización para el sistema de procesamiento de documentos de Biblioperson.

## 1. Estado actual y limitaciones detectadas

El código actual en `dataset/scripts/processors.py` contiene tres funciones principales que manejan la segmentación de documentos:

| Función | Tipo de texto | Heurística de segmentación |
|---------|---------------|----------------------------|
| `segmentar_poema_cancion` | Poemas/canciones | Detecta versos cortos consecutivos, títulos en Markdown (`#...`) o líneas cortas como encabezados |
| `segmentar_libro` | Libros/escritos largos | Busca encabezados Markdown (`#`, `##`), o patrones "línea corta → párrafo largo" |
| *(Sin nombre fijo)* | Mensajes/JSON de redes | No segmenta realmente: procesa cada mensaje JSON como unidad independiente |

### Problemas detectados

1. **Código monolítico:** Lógica compleja con muchas condiciones anidadas, difícil de mantener y probar.
2. **Parámetros hard-coded:** Umbrales fijos (135 caracteres para versos, 80 para títulos, 180 para párrafos) que no se adaptan a todos los casos.
3. **Pérdida de estilos en conversión:** Al convertir documentos con Pandoc se pierden metadatos valiosos (encabezados Word, negritas, etc.).
4. **Dificultad para extender:** Añadir un nuevo algoritmo implica modificar un archivo monolítico.
5. **Sin aprovechamiento de formatos:** No se explotan las características estructurales de DOCX, PDF, etc.
6. **Pruebas limitadas:** Sin framework sistemático de testing para validar algoritmos.

## 2. Nueva arquitectura propuesta

Proponemos una arquitectura modular con cuatro componentes principales:

```
Documento → [LOADER] → bloques → [SEGMENTER] → unidades → [POST-PROCESSOR] → [EXPORTER] → NDJSON/DB
```

### 2.1. Loader (extracción de contenido)

Responsable de **convertir cualquier formato a bloques de texto estructurados**, preservando metadatos críticos:

- **Input:** Archivo (PDF, DOCX, TXT, MD, PPTX, JSON, etc.)
- **Output:** Lista de bloques con metadatos (estilo, nivel de encabezado, página, etc.)
- **Tecnologías:**
  - PDF → `pdfminer.six` o `PyMuPDF`
  - DOCX → `python-docx` (extrae estilos **antes** de convertir)
  - JSON → `ijson` para archivos grandes
  - Binarios no soportados → `apache-tika` o `unstructured`

```python
# Ejemplo conceptual
class DocxLoader(BaseLoader):
    def load(self, filepath):
        doc = Document(filepath)
        blocks = []
        for paragraph in doc.paragraphs:
            blocks.append({
                "text": paragraph.text,
                "style": paragraph.style.name,  # Preserva "Heading 1", "Title", etc.
                "is_bold": any(run.bold for run in paragraph.runs),
                "is_heading": paragraph.style.name.startswith("Heading"),
                "heading_level": extract_heading_level(paragraph)
            })
        return blocks
```

> **CRÍTICO:** Los loaders deben preservar información de estilo/formato para alimentar las heurísticas de los segmenters.

### 2.2. Segmenter (definición de unidad semántica)

Define qué constituye una "unidad documental" (poema, párrafo, capítulo, mensaje) según reglas:

- **Input:** Lista de bloques con metadatos
- **Output:** Lista de unidades documentales discretas
- **Interfaz común:**

```python
# dataset/segmenters/base.py
class Segmenter:
    name: str                  # "poem", "paragraph", etc.
    config: dict               # Parámetros cargados de config.json
    
    def segment(self, blocks: list[dict]) -> list[dict]:
        """Divide los bloques en unidades semánticas."""
        ...
```

#### Implementaciones base (mínimo 4)

| Segmentador | Uso | Heurística principal |
|-------------|-----|----------------------|
| `VerseSegmenter` | Poemas/canciones | Líneas ≤ 120 chars o alta proporción de espacios + ≥ 2 líneas similares seguidas |
| `HeadingSegmenter` | Libros/escritos | Corta en encabezados (estilo Word "Heading 1-3" o markdown `#`) |
| `ParagraphSegmenter` | Artículos, blogs | Doble salto (`\n\n`). Une párrafos pequeños hasta umbral configurable |
| `MessageSegmenter` | JSON/feeds | Cada objeto del array es una unidad sin modificar |

### 2.3. Post-processor (filtrado y enriquecimiento)

Aplicación de filtros y transformaciones genéricas a las unidades:

- Filtrado por longitud mínima
- Detección de idioma
- Deduplicación
- Normalización Unicode
- Cálculo de estadísticas (tokens, frases, etc.)

### 2.4. Exporter (serialización y almacenamiento)

Volcado de las unidades procesadas a destinos configurable:

- NDJSON (formato histórico)
- SQLite
- Meilisearch
- MongoDB, etc.

## 3. Configuración declarativa de perfiles

Los perfiles se definirán en archivos YAML/JSON, no en código:

```yaml
# dataset/config/profiles/poem_or_lyrics.yaml
name: poem_or_lyrics
segmenter: VerseSegmenter
file_types: [".txt", ".md", ".docx", ".pdf"]
params:
  max_verse_length: 120      # Longitud máxima para considerar verso
  max_title_length: 80       # Longitud máxima para considerar título
  max_space_ratio: 0.35      # Proporción máxima de espacios/caracteres
  min_consecutive_verses: 2  # Mínimo de versos consecutivos para detectar poema
  stanza_separator: "\n\n"   # Patrón que separa estrofas
  title_patterns:            # Patrones para detectar títulos
    - "^# "
    - "^\\* "
    - "^> "
    - "^[A-Z ]{4,}:$"
post_processor:
  min_length: 30           # Longitud mínima para conservar unidad
  min_verses: 2            # Mínimo de versos para conservar poema
metadata_map:
  titulo: detected_title
  versos: verses_count
  estrofas: stanzas_count
```

El sistema cargará dinámicamente el segmentador apropiado según el perfil elegido:

```python
# Mapa de perfiles a segmentadores en config.json
{
  "profiles": {
    "poemas":     "VerseSegmenter",
    "canciones":  "VerseSegmenter",
    "libros":     "HeadingSegmenter",
    "escritos":   "ParagraphSegmenter",
    "tweets":     "MessageSegmenter",
    "telegram":   "MessageSegmenter"
  }
}
```

## 4. Mejoras específicas por algoritmo/segmentador

### 4.1. Mejoras para VerseSegmenter (poemas)

```python
def is_verse(line: str, config) -> bool:
    """Determina si una línea es un verso según heurísticas configurables."""
    stripped = line.rstrip()
    return (
        len(stripped) <= config["max_verse_length"]
        or spaces_ratio(stripped) >= config["max_space_ratio"]
    )

def segment(self, blocks: list[dict]) -> list[dict]:
    """Algoritmo mejorado para detectar poemas."""
    segments = []
    current_verses = []
    
    for block in blocks:
        # Usa estilo si está disponible
        if block.get("is_heading") or block.get("style") == "Title":
            # Cerrar poema actual si existe
            if current_verses:
                segments.append({
                    "type": "poem",
                    "verses": current_verses,
                    "stanzas": count_stanzas(current_verses)
                })
                current_verses = []
            # Guardar título como unidad separada
            segments.append({
                "type": "title",
                "text": block["text"]
            })
            continue
        
        # Verificar si es verso por longitud/espaciado
        if is_verse(block["text"], self.config):
            current_verses.append(block["text"])
        # Si no es verso y hay acumulados, cerrar poema
        elif current_verses:
            segments.append({
                "type": "poem",
                "verses": current_verses,
                "stanzas": count_stanzas(current_verses)
            })
            current_verses = []
            # El bloque actual inicia posible nuevo segmento
            if len(block["text"]) > 0:
                segments.append({
                    "type": "paragraph",
                    "text": block["text"]
                })
    
    # No olvidar último poema si existe
    if current_verses:
        segments.append({
            "type": "poem",
            "verses": current_verses,
            "stanzas": count_stanzas(current_verses)
        })
    
    return segments
```

### 4.2. Mejoras para HeadingSegmenter (libros)

- Extraer estilos DOCX con `python-docx` antes de conversión
- Usar información de jerarquía (nivel de encabezado) para mantener estructura
- Algoritmo mejorado para detección de capítulos en texto plano:
  ```
  1. Buscar líneas cortas (<80 chars) seguidas de 2+ párrafos largos
  2. Verificar si la línea corta tiene formato de título o separador
  3. Mantener jerarquía libro→capítulo→sección→párrafo
  ```

### 4.3. Evaluación automática de segmentadores

Propuesta para validar objetivamente las mejoras:

1. Crear dataset anotado manualmente (gold standard)
2. Métricas:
   - F1-score: precisión/recall de puntos de corte
   - Error de segmentación: distancia entre cortes reales y predichos
3. Script comparativo:
   ```
   python -m segmenters.evaluate tests/gold_corpus.ndjson --profile=poems
   ```

## 5. Plan de implementación

### Fase 1: Preparación (Semana 1)

1. Crear estructura de directorios:
   ```
   dataset/
     segmenters/
       __init__.py
       base.py         # Clase base Segmenter
       verse.py        # VerseSegmenter
       heading.py      # HeadingSegmenter
       paragraph.py    # ParagraphSegmenter
       message.py      # MessageSegmenter
     loaders/
       __init__.py
       base.py
       docx.py
       pdf.py
       text.py
       json.py
     config/
       profiles/
         poem_or_lyrics.yaml
         book_structure.yaml
         article.yaml
         json_messages.yaml
       segmenters_config.json  # Mapa perfil→segmentador
     tests/
       fixtures/        # Ejemplos documentados
       test_verse.py
       test_heading.py
       ...
   ```

2. Migrar lógica actual a `dataset/segmenters/legacy.py` (sin cambios)

### Fase 2: Base y prueba de concepto (Semana 2)

1. Implementar interfaces base:
   - `BaseLoader`
   - `BaseSegmenter`
   - `BasePostProcessor`
   - `BaseExporter`

2. Implementar primera versión de `VerseSegmenter`
3. Crear tests unitarios con casos sencillos
4. Validar equivalencia con función original `segmentar_poema_cancion`

### Fase 3: Implementación incremental (Semanas 3-5)

1. Implementar demás segmentadores, uno a uno:
   - `HeadingSegmenter` (libros)
   - `ParagraphSegmenter` (artículos)
   - `MessageSegmenter` (JSON)

2. Añadir loaders por formato:
   - `DocxLoader` + preservación de estilos
   - `PdfLoader` + detección de estructura
   - `JsonLoader` con streaming para archivos grandes

3. Integración con la aplicación principal

### Fase 4: Refinamiento y transición (Semanas 6-8)

1. Completar suite de tests (cobertura >90%)
2. Script de migración para configuraciones antiguas
3. Documentación de usuario final (cómo crear perfiles personalizados)
4. Deprecación de código legacy

## 6. Consideraciones técnicas importantes

### 6.1. Preservación de estilos

**CRÍTICO:** El sistema actual convierte todo a texto plano, perdiendo información valiosa de formato.

Solución:
1. Extraer metadatos de estilo **antes** de la conversión Pandoc
2. Para DOCX: usar `python-docx` y generar CSV auxiliar:
   ```csv
   line_number,text,style_name,is_bold,is_italic,is_heading,heading_level
   1,"Mi título",Heading1,True,False,True,1
   2,"Primer párrafo",Normal,False,False,False,0
   ```
3. Para PDF: usar `PyMuPDF` para extraer tamaño de fuente y estilo

### 6.2. Capacidad de extensión

El sistema debe ser extensible sin modificar código base:

- Segmentadores registrados vía entrypoints en `setup.cfg`:
  ```ini
  [options.entry_points]
  biblioperson.segmenters =
      verse = dataset.segmenters.verse:VerseSegmenter
      heading = dataset.segmenters.heading:HeadingSegmenter
      paragraph = dataset.segmenters.paragraph:ParagraphSegmenter
      message = dataset.segmenters.message:MessageSegmenter
      # Añadir nuevos segmentadores aquí
  ```

- Nuevos perfiles creados solo con YAML, sin tocar código

### 6.3. Pruebas automáticas

Cada segmentador debe tener su suite de pruebas:

```python
# tests/test_verse.py
def test_basic_poem_detection():
    segmenter = VerseSegmenter(config={"max_verse_length": 120, ...})
    blocks = [
        {"text": "TÍTULO DEL POEMA", "is_heading": True},
        {"text": "Primera línea del poema", "is_heading": False},
        {"text": "Segunda línea corta", "is_heading": False},
        {"text": "", "is_heading": False},
        {"text": "Nueva estrofa aquí", "is_heading": False},
    ]
    
    result = segmenter.segment(blocks)
    
    assert len(result) == 2  # Título + poema
    assert result[0]["type"] == "title"
    assert result[1]["type"] == "poem"
    assert len(result[1]["verses"]) == 3
    assert result[1]["stanzas"] == 2
```

## 7. Beneficios esperados

1. **Mantenibilidad:** Código modular, bien estructurado y testeado
2. **Flexibilidad:** Perfiles configurables sin cambiar código
3. **Calidad:** Mejor detección de unidades semánticas
4. **Extensibilidad:** Fácil añadir nuevos formatos y algoritmos
5. **Rendimiento:** Procesamiento paralelo de documentos grandes
6. **Trazabilidad:** Mejor logging y diagnóstico

## 8. Próximos pasos inmediatos

1. Crear repositorio de prueba con estructura propuesta
2. Implementar primer segmentador (`VerseSegmenter`) y tests
3. Validar con conjunto representativo de documentos reales
4. Iterar y refinar antes de implementación completa

---

> Documento generado: [Fecha]. Este documento debe ser revisado y actualizado según avance la implementación. 