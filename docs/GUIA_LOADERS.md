# Guía de Loaders - Biblioperson

## Introducción

Los loaders son componentes fundamentales del sistema Biblioperson que se encargan de leer archivos en diferentes formatos y convertirlos en una estructura de datos común para su procesamiento. Esta guía detalla todos los loaders disponibles y cómo utilizarlos.

## 🏗️ Arquitectura de Loaders

### Concepto Base

Todos los loaders heredan de la clase `BaseLoader` y proporcionan un método `load()` que devuelve un iterador de documentos. Esta arquitectura permite:

- **Procesamiento uniforme** de diferentes formatos
- **Extensibilidad** para nuevos tipos de archivo
- **Consistencia** en la estructura de datos de salida
- **Eficiencia** mediante procesamiento por streaming

### Estructura de Datos Común

Cada loader produce documentos con la siguiente estructura:

```python
{
    'text': "Contenido textual del segmento",
    'is_heading': False,  # True si es un título/encabezado
    'fuente': "nombre_autor",  # Extraído del directorio padre
    'contexto': "ruta/completa/al/archivo.ext",  # Ruta completa del archivo
    'fecha': "2023-12-01"  # Fecha extraída o inferida
}
```

## 📄 Loaders Disponibles

### 📝 txtLoader

**Propósito**: Procesa archivos de texto plano (`.txt`)

**Características especiales**:
- **Detección automática de título**: Si la primera línea está separada del resto
- **Extracción de fecha**: Del nombre del archivo con formatos reconocibles
- **Detección de tipo**: Distingue entre poemas y prosa usando heurísticas
- **Procesamiento línea por línea**: Mantiene estructura original

**Ejemplo de uso**:
```python
from dataset.processing.loaders import txtLoader

loader = txtLoader("ruta/al/archivo.txt", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(f"Texto: {documento['text'][:50]}...")
    print(f"Es título: {documento['is_heading']}")
```

**Casos de uso ideales**:
- Archivos de texto simple
- Poemas y canciones
- Notas y apuntes
- Transcripciones

### 📋 MarkdownLoader

**Propósito**: Procesa archivos Markdown (`.md`, `.markdown`)

**Características especiales**:
- **Preserva estructura Markdown**: Mantiene formato y jerarquía
- **Segmentación inteligente**: Según tipo de documento (escritos, poemas, canciones)
- **Extracción de metadatos**: Fecha del nombre o fecha de modificación
- **Detección de encabezados**: Identifica títulos y subtítulos automáticamente

**Ejemplo de uso**:
```python
from dataset.processing.loaders import MarkdownLoader

loader = MarkdownLoader("ruta/al/archivo.md", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    if documento['is_heading']:
        print(f"📌 Título: {documento['text']}")
    else:
        print(f"📄 Contenido: {documento['text'][:100]}...")
```

**Casos de uso ideales**:
- Documentación técnica
- Artículos y ensayos
- Libros estructurados
- Contenido web

### 📊 NDJSONLoader

**Propósito**: Procesa archivos NDJSON (JSON por línea)

**Características especiales**:
- **Procesamiento línea por línea**: Cada línea es un JSON independiente
- **Compatibilidad flexible**: Diferentes estructuras de datos JSON
- **Detección automática de contenido**: Busca campos `texto`/`text`/`content`
- **Preservación de metadatos**: Mantiene campos adicionales del JSON original

**Ejemplo de uso**:
```python
from dataset.processing.loaders import NDJSONLoader

loader = NDJSONLoader("ruta/al/archivo.ndjson", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(f"Procesado: {documento['text'][:50]}...")
```

**Casos de uso ideales**:
- Datos de redes sociales (Twitter, Telegram)
- Logs estructurados
- Datasets existentes
- Mensajes y conversaciones

### 📄 DocxLoader

**Propósito**: Procesa documentos Microsoft Word (`.docx`)

**Características especiales**:
- **Extracción de formato**: Preserva estructura de títulos y secciones
- **Procesamiento de estilos**: Detecta negrita, itálica, etc.
- **Metadatos del documento**: Extrae fecha de propiedades del archivo
- **Jerarquía de encabezados**: Identifica niveles de títulos automáticamente

**Ejemplo de uso**:
```python
from dataset.processing.loaders import DocxLoader

loader = DocxLoader("ruta/al/archivo.docx", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    nivel = "📌" if documento['is_heading'] else "📄"
    print(f"{nivel} {documento['text'][:80]}...")
```

**Casos de uso ideales**:
- Documentos académicos
- Informes y reportes
- Libros y manuscritos
- Documentación corporativa

### 📑 PDFLoader

**Propósito**: Procesa documentos PDF (`.pdf`)

**Características especiales**:
- **Extracción de texto**: Mantiene estructura básica de párrafos
- **Metadatos PDF**: Procesa título, autor y propiedades del documento
- **Referencia de página**: Mantiene información de ubicación
- **Manejo de formato**: Utiliza PyPDF2 para extracción robusta

**Ejemplo de uso**:
```python
from dataset.processing.loaders import PDFLoader

loader = PDFLoader("ruta/al/archivo.pdf", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(f"📖 Página: {documento.get('page', 'N/A')}")
    print(f"📄 Texto: {documento['text'][:100]}...")
```

**Casos de uso ideales**:
- Libros digitales
- Artículos científicos
- Documentos oficiales
- Manuales técnicos

### 📊 ExcelLoader

**Propósito**: Procesa hojas de cálculo Excel (`.xlsx`, `.xls`, `.xlsm`)

**Características especiales**:
- **Múltiples hojas**: Procesa todas las hojas del archivo
- **Estructura tabular**: Convierte filas y columnas a texto legible
- **Encabezados como títulos**: Usa nombres de hojas y columnas
- **Formato estructurado**: Convierte datos tabulares a narrativa

**Ejemplo de uso**:
```python
from dataset.processing.loaders import ExcelLoader

loader = ExcelLoader("ruta/al/archivo.xlsx", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    if documento['is_heading']:
        print(f"📊 Hoja/Columna: {documento['text']}")
    else:
        print(f"📋 Datos: {documento['text']}")
```

**Casos de uso ideales**:
- Datos financieros
- Inventarios y catálogos
- Listas y registros
- Análisis y reportes

### 📈 CSVLoader

**Propósito**: Procesa archivos CSV y TSV (`.csv`, `.tsv`)

**Características especiales**:
- **Detección automática**: Identifica delimitadores (coma, punto y coma, tabulación)
- **Encabezados inteligentes**: Procesa headers como títulos
- **Formato legible**: Convierte filas a formato "campo: valor"
- **Codificación flexible**: Manejo inteligente de diferentes encodings

**Ejemplo de uso**:
```python
from dataset.processing.loaders import CSVLoader

loader = CSVLoader("ruta/al/archivo.csv", tipo='escritos', encoding='utf-8')
for documento in loader.load():
    print(f"📊 Registro: {documento['text']}")
```

**Casos de uso ideales**:
- Bases de datos exportadas
- Logs de aplicaciones
- Datos de investigación
- Registros históricos

## 🔧 ProfileManager

### ¿Qué es el ProfileManager?

El `ProfileManager` es el componente que facilita la selección automática del loader adecuado basado en:

- **Extensión del archivo**
- **Perfil de procesamiento específico**
- **Configuración de contenido**
- **Umbrales de confianza**

### Uso Básico

```python
from dataset.processing.profile_manager import ProfileManager

manager = ProfileManager()

# Listar perfiles disponibles
perfiles = manager.list_profiles()
print("Perfiles disponibles:", perfiles)

# Procesar archivo automáticamente
resultados = manager.process_file(
    "ruta/al/archivo.txt", 
    profile_name="book_structure",
    encoding="utf-8",
    force_content_type="escritos",  # Opcional: forzar tipo
    confidence_threshold=0.5        # Umbral para detección automática
)

for resultado in resultados:
    print(f"Procesado: {resultado['text'][:50]}...")
```

### Configuración Avanzada

```python
# Configurar perfil personalizado
manager.configure_profile("mi_perfil", {
    "segmentation_strategy": "paragraph",
    "min_segment_length": 50,
    "preserve_formatting": True,
    "extract_metadata": True
})

# Procesar con perfil personalizado
resultados = manager.process_file(
    "mi_documento.docx",
    profile_name="mi_perfil"
)
```

## 🔨 Extensión del Sistema

### Crear un Nuevo Loader

Para añadir soporte para un nuevo formato:

#### 1. Crear la Clase Loader

```python
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
from .base_loader import BaseLoader

class MiNuevoLoader(BaseLoader):
    """Loader para formato personalizado."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        super().__init__(file_path)
        self.tipo = tipo.lower()
        self.encoding = encoding
    
    def load(self) -> Iterator[Dict[str, Any]]:
        fuente, contexto = self.get_source_info()
        
        # Implementación específica para tu formato
        with open(self.file_path, 'r', encoding=self.encoding) as file:
            content = file.read()
            
            # Procesar contenido según tu lógica
            segments = self._process_content(content)
            
            for i, segment in enumerate(segments):
                yield {
                    'text': segment['text'],
                    'is_heading': segment.get('is_heading', False),
                    'fuente': fuente,
                    'contexto': contexto,
                    'fecha': self._extract_date(),
                    'segment_order': i + 1
                }
    
    def _process_content(self, content: str) -> List[Dict[str, Any]]:
        """Lógica específica de procesamiento."""
        # Implementar según el formato
        pass
    
    def _extract_date(self) -> Optional[str]:
        """Extraer fecha del archivo o metadatos."""
        # Implementar extracción de fecha
        pass
```

#### 2. Registrar el Loader

```python
# En __init__.py del módulo loaders
from .mi_nuevo_loader import MiNuevoLoader

__all__ = [
    'txtLoader',
    'MarkdownLoader',
    'NDJSONLoader',
    'DocxLoader',
    'PDFLoader',
    'ExcelLoader',
    'CSVLoader',
    'MiNuevoLoader'  # Añadir aquí
]
```

#### 3. Configurar en ProfileManager

```python
# En ProfileManager.register_default_components()
self.register_loader('.mi_extension', MiNuevoLoader)
```

### Mejores Prácticas para Nuevos Loaders

1. **Herencia consistente**: Siempre heredar de `BaseLoader`
2. **Manejo de errores**: Implementar try/catch para archivos corruptos
3. **Encoding flexible**: Soportar diferentes codificaciones
4. **Metadatos ricos**: Extraer toda la información disponible
5. **Segmentación inteligente**: Adaptar según el tipo de contenido
6. **Documentación completa**: Incluir ejemplos y casos de uso

## 🔍 Solución de Problemas

### Error: "Loader no encontrado"

**Causa**: Extensión de archivo no registrada

**Solución**:
```python
# Verificar loaders registrados
manager = ProfileManager()
print(manager.get_registered_loaders())

# Registrar manualmente si es necesario
manager.register_loader('.mi_ext', MiLoader)
```

### Error: "Encoding no soportado"

**Causa**: Archivo con codificación especial

**Solución**:
```python
# Detectar encoding automáticamente
import chardet

with open('archivo.txt', 'rb') as f:
    raw_data = f.read()
    encoding = chardet.detect(raw_data)['encoding']
    print(f"Encoding detectado: {encoding}")

# Usar encoding específico
loader = txtLoader('archivo.txt', encoding=encoding)
```

### Error: "Archivo muy grande"

**Causa**: Archivo excede memoria disponible

**Solución**:
```python
# Procesar en chunks
def process_large_file(file_path, chunk_size=1024*1024):  # 1MB chunks
    with open(file_path, 'r', encoding='utf-8') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            # Procesar chunk
            yield process_chunk(chunk)
```

### Error: "Formato no reconocido"

**Causa**: Archivo con formato interno inesperado

**Solución**:
```python
# Validar formato antes de procesar
def validate_file_format(file_path):
    try:
        # Intentar abrir con el loader esperado
        loader = get_loader_for_file(file_path)
        first_doc = next(loader.load())
        return True
    except Exception as e:
        print(f"Formato no válido: {e}")
        return False
```

## 📚 Recursos Adicionales

### Documentación Relacionada

- [**Pipeline NDJSON**](PIPELINE_NDJSON.md) - Flujo completo de procesamiento
- [**Especificación NDJSON**](NDJSON_ESPECIFICACION.md) - Formato de salida detallado
- [**Gestión de Datos**](GUIA_GESTION_DATOS.md) - Importación a base de datos

### Ejemplos Prácticos

```python
# Procesamiento por lotes
def process_directory(directory_path, file_pattern="*"):
    from pathlib import Path
    
    directory = Path(directory_path)
    manager = ProfileManager()
    
    for file_path in directory.glob(file_pattern):
        if file_path.is_file():
            print(f"Procesando: {file_path}")
            try:
                results = manager.process_file(str(file_path))
                for result in results:
                    # Procesar resultado
                    save_to_ndjson(result)
            except Exception as e:
                print(f"Error procesando {file_path}: {e}")

# Uso
process_directory("raw_data/mi_autor/", "*.txt")
```

### Configuración de Perfiles

```python
# Perfil para libros académicos
academic_profile = {
    "segmentation_strategy": "heading_based",
    "min_segment_length": 100,
    "preserve_citations": True,
    "extract_footnotes": True,
    "heading_levels": [1, 2, 3, 4]
}

# Perfil para poesía
poetry_profile = {
    "segmentation_strategy": "stanza_based",
    "preserve_line_breaks": True,
    "detect_meter": True,
    "whole_file_as_segment": True
}

# Perfil para redes sociales
social_profile = {
    "segmentation_strategy": "message_based",
    "extract_hashtags": True,
    "extract_mentions": True,
    "preserve_timestamps": True
}
```

Esta guía proporciona todo lo necesario para entender, usar y extender el sistema de loaders de Biblioperson. Para casos específicos o problemas no cubiertos, consulta la documentación técnica adicional o el código fuente de los loaders existentes.