# Biblioperson - Interfaz Gráfica de Usuario

Este documento explica las dos versiones de la interfaz gráfica disponibles para Biblioperson.

## 🚀 Versiones Disponibles

### 1. Versión Completa (Recomendada) ✅

**Archivo:** `launch_gui.py`

**Características:**
- ✅ **Funciona sin errores** de widgets eliminados
- ✅ **Interfaz completa y estable**
- ✅ **Funcionalidad completa**:
  - Selección de archivos y carpetas
  - Selección de perfiles de procesamiento
  - **Controles de override de idioma y autor** (integrados en pestaña de procesamiento)
  - Configuración de salida
  - Procesamiento en tiempo real con logs
  - Generación de perfiles con IA
  - Unificación de archivos NDJSON

**Uso:**
```bash
python launch_gui.py
```

### 2. Versión Simplificada (Alternativa) ✅

**Archivo:** `launch_gui_simple.py`

**Características:**
- ✅ **Funciona sin errores** de widgets eliminados
- ✅ **Interfaz limpia y minimalista**
- ✅ **Funcionalidad esencial**:
  - Selección de archivos y carpetas
  - Selección de perfiles de procesamiento
  - Configuración de salida
  - Procesamiento en tiempo real con logs
  - Unificación de archivos NDJSON
- ⚠️ **Sin controles visuales de override** (idioma/autor)

**Uso:**
```bash
python launch_gui_simple.py
```

## 🎯 Recomendación de Uso

### Para Uso Diario: Versión Completa (GUI)

1. **Usa la versión completa** para todas las funcionalidades:
   ```bash
   python launch_gui.py
   ```
   - Incluye controles de override en la pestaña "🔧 Override"
   - Interfaz completa y estable
   - Todas las funcionalidades disponibles

2. **Alternativa: Línea de comandos** para automatización:
   ```bash
   # Ejemplo con override de idioma y autor
   python dataset/scripts/process_file.py archivo.txt --profile book_structure --language-override fr --author-override "Autor de Prueba"
   
   # Ejemplo con carpeta completa
   python dataset/scripts/process_file.py carpeta_documentos/ --profile poem_or_lyrics --language-override es --author-override "TSC"
   ```

## 📋 Funcionalidades Disponibles

### En la Versión Completa (GUI)
- ✅ Selección de archivos individuales
- ✅ Selección de carpetas completas
- ✅ Todos los perfiles de procesamiento
- ✅ **Override de idioma y autor** (integrado en pestaña de procesamiento)
- ✅ Configuración de archivos de salida
- ✅ Modo verbose para logs detallados
- ✅ Procesamiento en tiempo real con progreso
- ✅ Preservación de estructura de directorios
- ✅ Generación de perfiles con IA
- ✅ Unificación de archivos NDJSON

### En la Versión Simplificada (GUI)
- ✅ Selección de archivos individuales
- ✅ Selección de carpetas completas
- ✅ Todos los perfiles de procesamiento
- ✅ Configuración de archivos de salida
- ✅ Modo verbose para logs detallados
- ✅ Procesamiento en tiempo real con progreso
- ✅ Preservación de estructura de directorios
- ✅ Unificación de archivos NDJSON

### Solo en Línea de Comandos
- ✅ Forzar tipo de contenido (`--force-type`)
- ✅ Configuración de encoding (`--encoding`)
- ✅ Umbral de confianza (`--confidence-threshold`)

## 🔧 Comandos de Línea de Comandos Útiles

### Procesamiento Básico
```bash
# Archivo individual
python dataset/scripts/process_file.py documento.txt --profile book_structure

# Carpeta completa
python dataset/scripts/process_file.py mi_carpeta/ --profile poem_or_lyrics
```

### Con Overrides de Metadatos
```bash
# Override de idioma
python dataset/scripts/process_file.py documento.txt --profile book_structure --language-override fr

# Override de autor
python dataset/scripts/process_file.py documento.txt --profile book_structure --author-override "Mi Autor"

# Ambos overrides
python dataset/scripts/process_file.py documento.txt --profile book_structure --language-override es --author-override "TSC"
```

### Opciones Avanzadas
```bash
# Modo verbose + encoding específico
python dataset/scripts/process_file.py documento.txt --profile book_structure --verbose --encoding utf-8

# Forzar tipo de contenido
python dataset/scripts/process_file.py documento.txt --profile book_structure --force-type poemas

# Salida específica
python dataset/scripts/process_file.py documento.txt --profile book_structure --output mi_salida.ndjson
```

## 🌐 Códigos de Idioma Soportados

Para usar con `--language-override`:

- `es` - Español
- `en` - English
- `fr` - Français
- `de` - Deutsch
- `it` - Italiano
- `pt` - Português
- `ca` - Català
- `eu` - Euskera
- `gl` - Galego
- `la` - Latín
- `grc` - Griego Antiguo

## 📁 Perfiles Disponibles

- `book_structure` - Para libros con capítulos y secciones
- `poem_or_lyrics` - Para poemas y letras de canciones
- `biblical_verse_segmentation` - Para textos bíblicos
- `chapter_heading` - Para documentos con encabezados
- `perfil_docx_heading` - Para documentos Word con encabezados

## 🔍 Solución de Problemas

### Si la versión simplificada no funciona:
1. Verifica que todas las dependencias estén instaladas:
   ```bash
   pip install -r requirements.txt
   ```

2. Verifica que PySide6 esté correctamente instalado:
   ```bash
   pip install PySide6
   ```

### Si necesitas funcionalidad de override:
- Usa la línea de comandos como se muestra arriba
- La funcionalidad está completamente implementada y probada

### Para reportar problemas:
- Incluye el archivo de log `processing_errors.log`
- Especifica qué versión estás usando
- Proporciona el comando exacto que causó el problema

## 📈 Estado del Desarrollo

- ✅ **Funcionalidad de procesamiento**: 100% completa
- ✅ **Override de metadatos**: 100% funcional (GUI y línea de comandos)
- ✅ **Preservación de estructura**: 100% funcional
- ✅ **Interfaz completa**: 100% funcional
- ✅ **Interfaz simplificada**: 100% funcional

**¡Problema resuelto!** La funcionalidad de override ahora está completamente integrada en la pestaña de procesamiento de la interfaz gráfica completa. Los problemas técnicos de Qt se resolvieron mediante manejo robusto de errores y validación de widgets. 