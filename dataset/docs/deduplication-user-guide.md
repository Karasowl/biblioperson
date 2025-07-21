# Guía de Usuario: Sistema de Deduplicación de Biblioperson

## 🎯 Introducción

El sistema de deduplicación de Biblioperson te permite evitar procesar el mismo documento múltiples veces y elegir entre dos modos de salida según tus necesidades:

- **Modo Genérico**: Salida simple para alimentar sistemas de IA
- **Modo Biblioperson**: Salida completa con deduplicación y metadatos enriquecidos

## 🚀 Inicio Rápido

### 1. Activar Deduplicación

En la interfaz web, marca la casilla **"Salida Biblioperson"** en la sección de procesamiento:

```
☑️ Salida Biblioperson
```

Esto activará automáticamente:
- Deduplicación de documentos
- Metadatos enriquecidos en la salida
- Gestión de duplicados

### 2. Procesar Documentos

Procesa tus documentos normalmente. El sistema:
- Calculará un hash único para cada archivo
- Detectará automáticamente duplicados
- Te mostrará mensajes informativos sobre duplicados encontrados

### 3. Gestionar Duplicados

Haz clic en **"Gestor de Duplicados"** para:
- Ver todos los documentos procesados
- Buscar documentos específicos
- Eliminar registros de duplicados
- Ver estadísticas del sistema

## 📋 Modos de Salida Detallados

### Modo Genérico (Por Defecto)

**¿Cuándo usar?**
- Alimentar modelos de IA o LLMs
- Procesamiento simple de texto
- Cuando no necesitas metadatos adicionales
- Para obtener archivos más pequeños

**Características:**
- ❌ Sin deduplicación
- 📦 Estructura mínima
- ⚡ Procesamiento más rápido
- 💾 Archivos más pequeños

**Ejemplo de salida:**
```json
{
  "segment_id": "doc_001_seg_001",
  "text": "Contenido del segmento...",
  "segment_type": "paragraph",
  "document_title": "Mi Documento",
  "document_author": "Autor"
}
```

### Modo Biblioperson

**¿Cuándo usar?**
- Sistema completo de Biblioperson
- Cuando necesitas trazabilidad completa
- Para evitar duplicados
- Análisis detallado de documentos

**Características:**
- ✅ Deduplicación automática
- 📊 Metadatos completos
- 🔍 Trazabilidad total
- 🛡️ Hash de seguridad incluido

**Ejemplo de salida:**
```json
{
  "segment_id": "doc_001_seg_001",
  "text": "Contenido del segmento...",
  "segment_type": "paragraph",
  "document_title": "Mi Documento",
  "document_author": "Autor",
  "additional_metadata": {
    "document_hash": "a1b2c3d4e5f6...",
    "file_size": 1024576,
    "extraction_method": "pymupdf",
    "author_detection_confidence": 0.85
  }
}
```

## 🔍 Gestor de Duplicados

### Acceder al Gestor

1. Activa **"Salida Biblioperson"**
2. Haz clic en **"Gestor de Duplicados"**
3. Se abrirá una ventana con todos los documentos registrados

### Funciones Disponibles

#### 🔎 Búsqueda
- **Por título**: Busca en el nombre del documento
- **Por ruta**: Busca en la ruta del archivo
- **Búsqueda combinada**: Busca en ambos campos

```
🔍 [Buscar por título o ruta...]
```

#### 📅 Filtros de Fecha
- **Desde**: Documentos procesados después de esta fecha
- **Hasta**: Documentos procesados antes de esta fecha
- **Filtros rápidos**: Hoy, Esta semana, Este mes

```
📅 Desde: [2025-01-01] Hasta: [2025-12-31]
☑️ Hoy  ☑️ Esta semana  ☑️ Este mes
```

#### 📊 Tabla de Resultados

| ✓ | Fecha | Título | Ruta | Hash | 🗑 |
|---|-------|--------|------|------|---|
| ☑️ | 2025-06-14 | Mi Documento | /docs/archivo.pdf | a1b2c3... | 🗑️ |
| ☐ | 2025-06-13 | Otro Doc | /docs/otro.pdf | b2c3d4... | 🗑️ |

#### ⚡ Acciones Disponibles

**Acciones Individuales:**
- 🗑️ **Eliminar**: Borra un documento específico
- ☑️ **Seleccionar**: Marca para acciones masivas

**Acciones Masivas:**
- 🗑️ **Eliminar seleccionados**: Borra documentos marcados
- 🗑️ **Eliminar listado actual**: Borra todos los mostrados
- ⚠️ **Vaciar registro completo**: Borra TODOS los documentos (requiere confirmación)

### Casos de Uso Comunes

#### Limpiar Documentos Antiguos
1. Usa filtro **"Hasta"** con fecha límite
2. Selecciona **"Eliminar listado actual"**
3. Confirma la acción

#### Buscar Documento Específico
1. Escribe parte del título en la búsqueda
2. Revisa los resultados
3. Elimina si es necesario

#### Mantenimiento Periódico
1. Abre el gestor mensualmente
2. Usa **"Este mes"** para ver documentos recientes
3. Elimina duplicados innecesarios

## ⚙️ Configuración Avanzada

### Cambiar Ubicación de Base de Datos

Edita `dataset/config/deduplication_config.yaml`:

```yaml
deduplication:
  database_path: "mi/ruta/personalizada/deduplication.db"
```

### Optimizar Rendimiento

Para archivos muy grandes:

```yaml
performance:
  hash_chunk_size: 16384    # Duplicar tamaño de chunk
  operation_timeout: 60     # Aumentar timeout
  max_cache_size: 2000     # Más cache en memoria
```

### Configurar Manejo de Errores

```yaml
deduplication:
  error_handling:
    continue_on_error: true      # Continuar si hay errores
    log_errors: true             # Registrar errores
    warn_when_disabled: false    # No advertir si está deshabilitado
```

## 🚨 Mensajes del Sistema

### Mensajes Informativos

**✅ Documento nuevo registrado**
```
[INFO] Documento registrado: mi_archivo.pdf (hash: a1b2c3...)
```

**⚠️ Duplicado detectado**
```
[WARNING] Duplicado detectado: mi_archivo.pdf
Procesado originalmente: 2025-06-14 10:30:00
Saltando procesamiento...
```

**📊 Estadísticas**
```
[INFO] Estadísticas de deduplicación:
- Total documentos: 150
- Duplicados detectados hoy: 3
- Espacio ahorrado: ~45MB
```

### Mensajes de Error

**❌ Error de base de datos**
```
[ERROR] No se puede acceder a la base de datos de deduplicación
Continuando sin deduplicación...
```

**❌ Error de permisos**
```
[ERROR] Sin permisos para escribir en: dataset/data/
Verifica los permisos del directorio
```

## 🔧 Solución de Problemas

### Problema: No se detectan duplicados

**Posibles causas:**
- Modo Genérico activado (sin deduplicación)
- Base de datos corrupta
- Configuración incorrecta

**Soluciones:**
1. Verifica que **"Salida Biblioperson"** esté marcada
2. Revisa los logs para errores
3. Reinicia el procesamiento

### Problema: Procesamiento muy lento

**Posibles causas:**
- Archivos muy grandes
- Configuración de rendimiento baja
- Disco lento

**Soluciones:**
1. Aumenta `hash_chunk_size` en configuración
2. Aumenta `operation_timeout`
3. Usa SSD si es posible

### Problema: Error de permisos

**Posibles causas:**
- Sin permisos de escritura
- Directorio no existe
- Antivirus bloqueando

**Soluciones:**
1. Crea el directorio: `mkdir -p dataset/data/`
2. Da permisos: `chmod 755 dataset/data/`
3. Configura excepción en antivirus

## 📈 Mejores Prácticas

### 🎯 Uso Eficiente

1. **Usa Modo Genérico** para:
   - Entrenar modelos de IA
   - Análisis de texto simple
   - Cuando el tamaño del archivo importa

2. **Usa Modo Biblioperson** para:
   - Sistema completo de Biblioperson
   - Cuando necesitas evitar duplicados
   - Análisis detallado con metadatos

### 🧹 Mantenimiento

1. **Limpieza Regular**:
   - Revisa duplicados mensualmente
   - Elimina registros antiguos innecesarios
   - Mantén la base de datos pequeña

2. **Monitoreo**:
   - Revisa logs regularmente
   - Verifica estadísticas de duplicados
   - Ajusta configuración según necesidades

3. **Respaldos**:
   - Respalda `dataset/data/deduplication.db` regularmente
   - Guarda configuración personalizada
   - Documenta cambios importantes

### ⚡ Optimización

1. **Para Muchos Archivos Pequeños**:
   ```yaml
   performance:
     hash_chunk_size: 4096
     max_cache_size: 5000
   ```

2. **Para Pocos Archivos Grandes**:
   ```yaml
   performance:
     hash_chunk_size: 32768
     operation_timeout: 120
   ```

3. **Para Uso Intensivo**:
   ```yaml
   performance:
     enable_hash_cache: true
     max_cache_size: 10000
   ```

## 📞 Soporte

### Información de Diagnóstico

Si necesitas ayuda, incluye esta información:

1. **Versión del sistema**
2. **Configuración actual** (`deduplication_config.yaml`)
3. **Logs de error** (últimas 50 líneas)
4. **Estadísticas** del gestor de duplicados
5. **Descripción detallada** del problema

### Logs Útiles

Habilita logs detallados temporalmente:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Comandos de Diagnóstico

```python
# Verificar estado del sistema
from dataset.processing.profile_manager import ProfileManager
pm = ProfileManager()
print(pm.get_deduplication_status())

# Ver estadísticas
from dataset.processing.deduplication import get_dedup_manager
dedup = get_dedup_manager()
print(dedup.get_stats())
```

---

¡El sistema de deduplicación está diseñado para ser simple y eficiente! Si tienes dudas, consulta la documentación técnica o contacta al equipo de soporte. 