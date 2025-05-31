# Sistema de Filtros JSON - Biblioperson

## 📋 Descripción

El sistema de filtros JSON permite procesar archivos JSON complejos aplicando reglas de filtrado avanzadas y extrayendo contenido específico para su análisis literario.

## 🚀 Características Principales

### ✅ Extracción de Contenido
- **Múltiples rutas de texto**: Especifica qué campos contienen el texto a extraer
- **Dot notation**: Acceso a propiedades anidadas (`metadata.language`, `user.profile.name`)
- **Arrays automáticos**: Concatenación inteligente de contenido en arrays
- **Campos configurables**: ID, fecha y otros metadatos

### ✅ Filtrado Avanzado
- **Operadores múltiples**: `eq`, `neq`, `contains`, `regex`, `gte`, `lte`, `exists`, `not_exists`
- **Propiedades anidadas**: Filtrar por cualquier campo usando dot notation
- **Reglas combinadas**: Múltiples filtros aplicados en secuencia
- **Negación**: Invertir cualquier regla de filtrado

### ✅ Interfaz Gráfica
- **Editor visual**: Configuración intuitiva sin código
- **Pruebas en vivo**: Probar configuración con archivos reales
- **Guardar/Cargar**: Persistir configuraciones para reutilizar
- **Validación**: Verificación automática de sintaxis

## 🎯 Casos de Uso

### 📚 Procesamiento de Literatura Digital
```json
{
  "text_property_paths": ["content", "text", "body"],
  "filter_rules": [
    {"field": "type", "operator": "eq", "value": "poem"},
    {"field": "language", "operator": "eq", "value": "es"}
  ],
  "root_array_path": "documents"
}
```

### 📰 Análisis de Artículos
```json
{
  "text_property_paths": ["title", "content", "summary"],
  "filter_rules": [
    {"field": "category", "operator": "contains", "value": "literature"},
    {"field": "published_date", "operator": "gte", "value": "2020-01-01"}
  ]
}
```

### 💬 Procesamiento de Mensajes
```json
{
  "text_property_paths": ["message", "text"],
  "filter_rules": [
    {"field": "user.verified", "operator": "eq", "value": true},
    {"field": "content_type", "operator": "neq", "value": "spam"}
  ]
}
```

## 🔧 Configuración

### Estructura de Configuración

```json
{
  "text_property_paths": ["content", "title"],
  "filter_rules": [
    {
      "field": "status",
      "operator": "eq", 
      "value": "published",
      "case_sensitive": false,
      "negate": false
    }
  ],
  "pointer_path": "id",
  "date_path": "created_at",
  "root_array_path": "data",
  "treat_as_single_object": false
}
```

### Parámetros Principales

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `text_property_paths` | Campos que contienen texto | `["content", "title", "body"]` |
| `filter_rules` | Reglas de filtrado | Ver sección de operadores |
| `pointer_path` | Campo que actúa como ID único | `"id"`, `"uuid"`, `"_id"` |
| `date_path` | Campo que contiene la fecha | `"date"`, `"created_at"` |
| `root_array_path` | Ruta al array principal | `"data"`, `"results.items"` |
| `treat_as_single_object` | Procesar como objeto único | `true`/`false` |

### Operadores Disponibles

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `eq` | Igual a | `{"field": "type", "operator": "eq", "value": "poem"}` |
| `neq` | No igual a | `{"field": "status", "operator": "neq", "value": "draft"}` |
| `contains` | Contiene texto | `{"field": "title", "operator": "contains", "value": "amor"}` |
| `regex` | Expresión regular | `{"field": "content", "operator": "regex", "value": "\\d{4}"}` |
| `gte` | Mayor o igual | `{"field": "year", "operator": "gte", "value": 2020}` |
| `lte` | Menor o igual | `{"field": "length", "operator": "lte", "value": 1000}` |
| `exists` | Campo existe | `{"field": "metadata.author", "operator": "exists"}` |
| `not_exists` | Campo no existe | `{"field": "deleted_at", "operator": "not_exists"}` |

## 📖 Guía de Uso

### 1. Usando la Interfaz Gráfica

1. **Abrir la aplicación**:
   ```bash
   python launch_gui.py
   ```

2. **Ir a la pestaña "🔧 Filtros JSON"**

3. **Configurar extracción de texto**:
   - Especificar rutas de propiedades de texto
   - Configurar campos de ID y fecha
   - Definir estructura del JSON

4. **Agregar reglas de filtrado**:
   - Hacer clic en "+ Agregar Regla"
   - Configurar campo, operador y valor
   - Ajustar opciones avanzadas si es necesario

5. **Probar configuración**:
   - Seleccionar archivo JSON de prueba
   - Ejecutar prueba y revisar resultados
   - Ajustar configuración según sea necesario

6. **Guardar configuración**:
   - Usar "Guardar Configuración" para persistir
   - Cargar configuraciones previamente guardadas

### 2. Usando Programáticamente

```python
from pathlib import Path
from dataset.processing.loaders.json_loader import JSONLoader

# Configuración
config = {
    'text_property_paths': ['content', 'title'],
    'filter_rules': [
        {'field': 'type', 'operator': 'eq', 'value': 'poem'},
        {'field': 'status', 'operator': 'eq', 'value': 'published'}
    ],
    'root_array_path': 'data',
    'pointer_path': 'id',
    'date_path': 'date'
}

# Procesar archivo
loader = JSONLoader(Path('mi_archivo.json'), **config)
data = loader.load()

# Acceder a resultados
blocks = data['blocks']
metadata = data['document_metadata']

print(f"Procesados {len(blocks)} bloques")
for block in blocks:
    print(f"Texto: {block['text'][:100]}...")
```

### 3. Integración en el Pipeline

El JSONLoader se integra automáticamente en el sistema de procesamiento:

```bash
# Procesar archivo JSON con perfil específico
python -m dataset.scripts.process_file mi_archivo.json --profile mi_perfil
```

## 🧪 Ejemplos Prácticos

### Ejemplo 1: Filtrar Poemas Publicados

**Archivo JSON**:
```json
{
  "poems": [
    {
      "id": 1,
      "title": "Soneto de Amor",
      "content": "Cuando contemplo el cielo...",
      "author": "Poeta Clásico",
      "status": "published",
      "type": "sonnet"
    },
    {
      "id": 2,
      "title": "Borrador",
      "content": "Texto incompleto...",
      "author": "Poeta Moderno", 
      "status": "draft",
      "type": "free_verse"
    }
  ]
}
```

**Configuración**:
```json
{
  "text_property_paths": ["content", "title"],
  "filter_rules": [
    {"field": "status", "operator": "eq", "value": "published"}
  ],
  "root_array_path": "poems",
  "pointer_path": "id",
  "date_path": "created_at"
}
```

**Resultado**: Solo el poema con `status: "published"` será procesado.

### Ejemplo 2: Filtrar por Múltiples Criterios

**Configuración**:
```json
{
  "text_property_paths": ["content"],
  "filter_rules": [
    {"field": "type", "operator": "eq", "value": "poem"},
    {"field": "metadata.language", "operator": "eq", "value": "es"},
    {"field": "metadata.verified", "operator": "eq", "value": true}
  ],
  "root_array_path": "documents"
}
```

**Resultado**: Solo documentos que sean poemas, en español y verificados.

### Ejemplo 3: Filtrar por Fecha

**Configuración**:
```json
{
  "text_property_paths": ["text"],
  "filter_rules": [
    {"field": "published_date", "operator": "gte", "value": "2020-01-01"},
    {"field": "published_date", "operator": "lte", "value": "2023-12-31"}
  ]
}
```

**Resultado**: Solo contenido publicado entre 2020 y 2023.

## 🔍 Solución de Problemas

### Error: "No se obtuvieron bloques"

**Causas posibles**:
- Reglas de filtrado demasiado restrictivas
- Ruta del array raíz incorrecta
- Campos de texto no encontrados

**Soluciones**:
1. Verificar la estructura del JSON
2. Simplificar las reglas de filtrado
3. Usar la función de prueba para depurar

### Error: "Campo no encontrado"

**Causa**: Ruta de campo incorrecta en dot notation

**Solución**: 
- Verificar la estructura exacta del JSON
- Usar herramientas como `jq` para explorar la estructura
- Probar con rutas más simples primero

### Rendimiento Lento

**Causas**:
- Archivos JSON muy grandes
- Reglas regex complejas
- Múltiples filtros anidados

**Soluciones**:
- Dividir archivos grandes
- Optimizar expresiones regulares
- Usar filtros más específicos primero

## 📚 Referencias

- [Documentación de Loaders](GUIA_LOADERS.md)
- [Arquitectura del Sistema](BIBLIOPERSON_ARQUITECTURA.md)
- [Algoritmos de Procesamiento](ALGORITMOS_PROPUESTOS.md)

## 🤝 Contribuir

Para agregar nuevos operadores o funcionalidades:

1. Modificar `dataset/scripts/utils.py` para nuevos operadores
2. Actualizar `dataset/scripts/ui/json_filter_widget.py` para la UI
3. Agregar pruebas en `test_json_loader.py`
4. Actualizar esta documentación

---

*Última actualización: Diciembre 2024* 