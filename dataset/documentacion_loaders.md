# Documentación de Loaders para Biblioperson

Este documento describe los diferentes loaders implementados para el sistema Biblioperson, que permiten la carga y procesamiento de diversos formatos de archivo.

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Loaders Disponibles](#loaders-disponibles)
   - [txtLoader](#txtLoader)
   - [MarkdownLoader](#markdownloader)
   - [NDJSONLoader](#ndjsonloader)
   - [DocxLoader](#docxloader)
   - [PDFLoader](#pdfloader)
   - [ExcelLoader](#excelloader)
   - [CSVLoader](#csvloader)
3. [Uso del ProfileManager](#uso-del-profilemanager)
4. [Extensión del Sistema](#extensión-del-sistema)

## Introducción

Los loaders son componentes encargados de leer archivos en diferentes formatos y convertirlos en una estructura de datos común que puede ser procesada por el sistema. Todos los loaders heredan de la clase base `BaseLoader` y proporcionan un método `load()` que devuelve un iterador de documentos.

## Loaders Disponibles

### txtLoader

**Descripción**: Carga archivos de texto plano (.txt).

**Características**:
- Detecta automáticamente título si la primera línea está separada del resto
- Extrae fecha del nombre del archivo si tiene un formato reconocible
- Procesa el contenido línea por línea
- Soporta detección de poemas vs. prosa basada en características heurísticas

**Ejemplo de uso**:
```python
from dataset.processing.loaders import txtLoader

loader = txtLoader("ruta/al/archivo.txt", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(documento)
```

### MarkdownLoader

**Descripción**: Carga archivos en formato Markdown (.md, .markdown).

**Características**:
- Preserva la estructura de Markdown
- Segmenta el contenido según el tipo de documento (escritos, poemas, canciones)
- Extrae fecha del nombre del archivo o usa la fecha de modificación como respaldo

**Ejemplo de uso**:
```python
from dataset.processing.loaders import MarkdownLoader

loader = MarkdownLoader("ruta/al/archivo.md", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(documento)
```

### NDJSONLoader

**Descripción**: Carga archivos NDJSON (JSON por línea).

**Características**:
- Procesa cada línea como un objeto JSON independiente
- Compatible con diferentes estructuras de datos JSON
- Busca campos texto/text/content para determinar el contenido principal

**Ejemplo de uso**:
```python
from dataset.processing.loaders import NDJSONLoader

loader = NDJSONLoader("ruta/al/archivo.ndjson", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(documento)
```

### DocxLoader

**Descripción**: Carga documentos de Microsoft Word (.docx).

**Características**:
- Extrae texto formateado preservando estructura
- Detecta títulos, subtítulos y secciones
- Procesa estilos como negrita, itálica, etc.
- Extrae fecha de las propiedades del documento

**Ejemplo de uso**:
```python
from dataset.processing.loaders import DocxLoader

loader = DocxLoader("ruta/al/archivo.docx", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(documento)
```

### PDFLoader

**Descripción**: Carga documentos PDF (.pdf).

**Características**:
- Extrae texto manteniendo estructura básica de párrafos
- Procesa metadatos del PDF como título y autor
- Mantiene referencia al número de página
- Utiliza PyPDF2 para la extracción de contenido

**Ejemplo de uso**:
```python
from dataset.processing.loaders import PDFLoader

loader = PDFLoader("ruta/al/archivo.pdf", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(documento)
```

### ExcelLoader

**Descripción**: Carga hojas de cálculo de Excel (.xlsx, .xls, .xlsm).

**Características**:
- Procesa múltiples hojas dentro del mismo archivo
- Trata nombres de hojas como títulos y columnas como encabezados
- Convierte filas a texto legible
- Soporta formato alternativo de tabla estructurada

**Ejemplo de uso**:
```python
from dataset.processing.loaders import ExcelLoader

loader = ExcelLoader("ruta/al/archivo.xlsx", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(documento)
```

### CSVLoader

**Descripción**: Carga archivos CSV y TSV (.csv, .tsv).

**Características**:
- Detecta automáticamente el delimitador (coma, punto y coma, tabulación)
- Procesa encabezados como títulos
- Formatea filas como "campo: valor" para mejor legibilidad
- Manejo inteligente de diferentes codificaciones

**Ejemplo de uso**:
```python
from dataset.processing.loaders import CSVLoader

loader = CSVLoader("ruta/al/archivo.csv", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(documento)
```

## Uso del ProfileManager

El `ProfileManager` facilita la selección del loader adecuado basado en la extensión del archivo y un perfil específico:

```python
from dataset.processing.profile_manager import ProfileManager

manager = ProfileManager()

# Lista perfiles disponibles
perfiles = manager.list_profiles()
print(perfiles)

# Procesa un archivo con un perfil específico
resultados = manager.process_file(
    "ruta/al/archivo.txt", 
    profile_name="book_structure",
    encoding="utf-8",
    force_content_type="escritos",  # Opcional
    confidence_threshold=0.5        # Para detección automática
)
```

## Extensión del Sistema

Para implementar soporte para un nuevo formato de archivo:

1. Crear una nueva clase que herede de `BaseLoader`
2. Implementar el método `load()` siguiendo la estructura común
3. Registrar el nuevo loader en `__init__.py`
4. Registrar la extensión en `ProfileManager.register_default_components()`

Ejemplo mínimo:

```python
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from .base_loader import BaseLoader

class MiNuevoLoader(BaseLoader):
    """Loader para el nuevo formato."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
    
    def load(self) -> Iterator[Dict[str, Any]]:
        fuente, contexto = self.get_source_info()
        
        # Implementación específica para procesar el archivo
        # ...
        
        yield {
            'text': "Contenido extraído",
            'is_heading': False,
            'fuente': fuente,
            'contexto': contexto,
            'fecha': None
        }
``` 