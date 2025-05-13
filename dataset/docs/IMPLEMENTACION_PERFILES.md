# Implementación del Sistema de Perfiles

> Documento técnico que describe la implementación del sistema de perfiles para el procesamiento de documentos en Biblioperson.

## Introducción

Este documento detalla la implementación técnica del sistema de perfiles de procesamiento descrito en `docs/ESTRATEGIA_PROCESAMIENTO.md`. El sistema reemplaza los antiguos algoritmos monolíticos por un pipeline modular y configurable mediante perfiles declarativos.

## Estructura de directorios

```
backend/
  shared/
    profiles/                # Módulo principal
      __init__.py
      schema.py              # Validación de schema para perfiles
      profile_manager.py     # Gestor centralizado
      loaders/               # Loaders para diferentes formatos
        __init__.py
        base.py
        docx_loader.py
        pdf_loader.py
        text_loader.py
      segmenters/            # Segmentadores por tipo de contenido
        __init__.py
        base.py
        verse_segmenter.py   # Poemas/canciones
        heading_segmenter.py # Estructura de libros
        paragraph_segmenter.py
        message_segmenter.py
      post_processors/       # Filtrados y transformaciones
        __init__.py
        base.py
        text_normalizer.py
      exporters/             # Salida a diferentes formatos
        __init__.py
        base.py
        ndjson_exporter.py
        sqlite_exporter.py
      profiles/              # Perfiles YAML
        poem_or_lyrics.yaml
        book_structure.yaml
        generic_text.yaml
        json_messages.yaml
```

## Diseño basado en máquina de estados

Los segmentadores implementan máquinas de estado explícitas para modelar el procesamiento, lo que resulta en código más mantenible y menos propenso a errores lógicos. Por ejemplo, el `VerseSegmenter` utiliza los siguientes estados:

```python
class VerseState(Enum):
    SEARCH_TITLE = 1      # Buscando título de poema
    TITLE_FOUND = 2       # Título encontrado, esperando versos iniciales
    COLLECTING_VERSE = 3  # Recolectando versos de un poema
    STANZA_GAP = 4        # En hueco entre estrofas
    END_POEM = 5          # Finalizando poema actual
    OUTSIDE_POEM = 6      # Fuera de poema
```

Cada estado tiene transiciones claras y predecibles basadas en las reglas definidas en `docs/ALGORITMOS_PROPUESTOS.md`, resultando en una implementación que sigue esta estructura:

```python
# Procesamiento basado en estados
for bloque in bloques:
    if estado == VerseState.SEARCH_TITLE:
        # Lógica para buscar título
        if [condiciones]:
            estado = VerseState.TITLE_FOUND
    
    elif estado == VerseState.TITLE_FOUND:
        # Lógica para verificar si lo que sigue al título confirma que es un poema
        if [condiciones]:
            estado = VerseState.COLLECTING_VERSE
    
    # Otros estados...
```

## Perfiles declarativos (YAML)

Los perfiles se definen en archivos YAML, separando completamente la configuración del código. Ejemplo de perfil para poemas:

```yaml
# backend/shared/profiles/profiles/poem_or_lyrics.yaml
name: poem_or_lyrics
description: "Detecta poemas y canciones en archivos de texto"
segmenter: verse
file_types: [".txt", ".md", ".docx", ".pdf"]
thresholds:
  max_verse_length: 120      # Longitud máxima para considerar verso
  max_title_length: 80       # Longitud máxima para considerar título
  max_space_ratio: 0.35      # Proporción máxima de espacios/caracteres
  min_consecutive_verses: 3  # Mínimo de versos consecutivos para detectar poema
  min_stanza_verses: 2       # Mínimo de versos para formar estrofa
  max_consecutive_empty: 2   # Máximo de líneas vacías entre versos de misma estrofa
title_patterns:            # Patrones para detectar títulos
  - "^# "
  - "^\\* "
  - "^> "
  - "^[A-Z ]{4,}:$"
post_processor: text_normalizer
post_processor_config:
  min_length: 30           # Longitud mínima para conservar unidad
  min_verses: 2            # Mínimo de versos para conservar poema
metadata_map:              # Mapeo de campos internos a nombres finales
  titulo: title
  versos: verses_count
  estrofas: stanzas_count
exporter: ndjson
```

## ProfileManager: Control centralizado

El `ProfileManager` carga y gestiona los perfiles y componentes:

```python
# Inicialización
profile_manager = ProfileManager("/ruta/a/perfiles")

# Procesamiento de archivo
units = profile_manager.process_file(
    file_path="mi_documento.docx",
    profile_name="poem_or_lyrics",
    output_path="resultados.ndjson"  # Opcional
)
```

Internamente, el `ProfileManager` implementa el flujo completo:

1. Selecciona el loader adecuado según la extensión del archivo
2. Carga el perfil y sus configuraciones
3. Instancia el segmenter apropiado con los thresholds del perfil
4. Aplica el post-processor especificado
5. Exporta los resultados si se proporciona output_path

## Implementación del VerseSegmenter

El `VerseSegmenter` es un ejemplo de implementación basada en estados, que se guía por los algoritmos definidos en `docs/ALGORITMOS_PROPUESTOS.md`:

```python
def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    segments = []
    state = VerseState.SEARCH_TITLE
    
    # Variables de contexto
    current_title = None
    current_verses = []
    consecutive_empty = 0
    
    for i, block in enumerate(blocks):
        # Determinar características del bloque actual
        text = block.get('text', '').strip()
        is_empty = not text
        
        if is_empty:
            consecutive_empty += 1
            continue
            
        # Análisis según estado actual
        is_potential_title = self.has_title_format(block)
        is_verse = self.is_verse(text)
        
        # Máquina de estados para procesamiento
        if state == VerseState.SEARCH_TITLE:
            if is_potential_title:
                # Posible título encontrado
                current_title = text
                state = VerseState.TITLE_FOUND
            elif is_verse:
                # Posible inicio de poema sin título
                # ...
                
        # Otros estados y transiciones...
```

### Características clave del VerseSegmenter:

1. **Detección de unidades**: Usa thresholds configurables para determinar qué es un verso, título, etc.
2. **Preservación de metadatos**: Genera información estructural como número de versos, estrofas, etc.
3. **Evaluación de confianza**: Calcula un valor de confianza (0-1) para cada poema detectado.
4. **Look-ahead**: Implementa funciones de "mirada adelante" para confirmar patrones.

## Instrucciones para añadir nuevos componentes

### Creación de un nuevo Loader

Para soportar un nuevo formato, crea una subclase de `BaseLoader`:

```python
# backend/shared/profiles/loaders/my_loader.py
from typing import List, Dict, Any
from .base import BaseLoader

class MyCustomLoader(BaseLoader):
    @classmethod
    def supports_extension(cls, extension: str) -> bool:
        # Indica qué extensiones soporta este loader
        return extension.lower() in ['.custom', '.myformat']
    
    def load(self, file_path: str) -> List[Dict[str, Any]]:
        # Implementar carga de archivo
        blocks = []
        
        # ... Lógica para cargar el archivo y convertirlo en bloques ...
        
        return blocks
```

Registra el loader en el `ProfileManager`:

```python
# En profile_manager.py o donde se use
from .loaders.my_loader import MyCustomLoader
profile_manager.register_loader('my_format', MyCustomLoader)
```

### Creación de un nuevo Segmenter

Para implementar un nuevo algoritmo de segmentación:

```python
# backend/shared/profiles/segmenters/my_segmenter.py
from enum import Enum
from typing import List, Dict, Any
from .base import BaseSegmenter

class MyState(Enum):
    # Define tus estados aquí
    STATE_1 = 1
    STATE_2 = 2
    # ...

class MySegmenter(BaseSegmenter):
    def __init__(self, config=None):
        super().__init__(config or {})
        # Inicializar thresholds específicos
        
    def segment(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Implementar máquina de estados
        segments = []
        state = MyState.STATE_1
        
        # ... Lógica de segmentación ...
        
        return segments
```

Registra el segmenter en el `ProfileManager`:

```python
from .segmenters.my_segmenter import MySegmenter
profile_manager.register_segmenter('my_algorithm', MySegmenter)
```

### Creación de un nuevo Perfil

Crea un archivo YAML en `profiles/`:

```yaml
# backend/shared/profiles/profiles/my_profile.yaml
name: my_profile
description: "Mi nuevo perfil de procesamiento"
segmenter: my_algorithm
file_types: [".custom", ".txt"]
thresholds:
  # ... Parámetros para tu algoritmo ...
post_processor: text_normalizer
exporter: ndjson
```

## Uso desde CLI

El sistema incluye un script en `backend/scripts/process_file.py` para usarlo desde la línea de comandos:

```bash
python backend/scripts/process_file.py mi_archivo.docx --profile poem_or_lyrics --output resultados.ndjson
```

Para listar perfiles disponibles:

```bash
python backend/scripts/process_file.py --list-profiles
```

## Pruebas automatizadas

Cada componente debe tener sus tests unitarios:

```python
# tests/test_verse_segmenter.py
def test_verse_recognition():
    segmenter = VerseSegmenter({"thresholds": {"max_verse_length": 120}})
    
    # Test casos básicos
    assert segmenter.is_verse("Una línea corta")
    assert not segmenter.is_verse("Una línea muy larga " * 10)
    
    # Test detección de títulos
    block = {"text": "# Título", "is_heading": False}
    assert segmenter.has_title_format(block)
```

Para tests de integración, usar fixtures de documentos reales.

## Conclusiones

Esta implementación ofrece notables ventajas:

1. **Mejor mantenibilidad**: Código modular y máquinas de estado explícitas
2. **Flexibilidad**: Todos los umbrales configurables sin tocar código
3. **Extensibilidad**: Fácil incorporación de nuevos formatos y algoritmos
4. **Trazabilidad**: Métricas de confianza y logs detallados
5. **Preservación de formato**: Mantenimiento de metadatos críticos desde la fuente

## Referencias

- [ALGORITMOS_PROPUESTOS.md](./ALGORITMOS_PROPUESTOS.md) - Algoritmos y reglas base
- [ESTRATEGIA_PROCESAMIENTO.md](./ESTRATEGIA_PROCESAMIENTO.md) - Estrategia general
- [ALGORITMOS_ANTERIORES](./ALGORITMOS_ANTERIORES) - Algoritmos históricos 