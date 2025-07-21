# Sistema de Deduplicación y Modo Biblioperson vs Genérico

## 📋 Resumen Ejecutivo

Este documento detalla todos los accionables definidos para implementar un sistema de deduplicación de documentos y dos modos de salida en el pipeline de procesamiento de Biblioperson:

- **Modo Genérico**: NDJSON simple para alimentar IAs y otros sistemas
- **Modo Biblioperson**: NDJSON enriquecido con metadatos completos y sistema de deduplicación

## 🎯 Objetivos Principales

1. **Deduplicación Inteligente**: Evitar procesar el mismo documento múltiples veces usando hash SHA-256
2. **Flexibilidad de Salida**: Permitir exportar datos simples o enriquecidos según el uso
3. **Gestión Visual**: Interfaz completa para administrar duplicados con búsqueda y filtros
4. **Compatibilidad**: Mantener el flujo actual sin cambios disruptivos
5. **Opcionalidad**: Todo el sistema debe ser completamente opcional

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Loader Base   │───▶│  Dedup Registry  │───▶│  Output Mode    │
│   (SHA-256)     │    │   (SQLite)       │    │  Selector       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  CLI Commands   │    │   REST API       │    │   UI Modal      │
│  (dedup mgmt)   │    │  (endpoints)     │    │  (management)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📝 Lista Completa de Accionables

### 🔧 Backend - Sistema de Deduplicación

#### 1. Crear Tabla SQLite de Deduplicación
- **Ubicación**: `dataset/.cache/dedup_registry.sqlite`
- **Esquema**:
  ```sql
  CREATE TABLE IF NOT EXISTS docs (
    hash        TEXT PRIMARY KEY,   -- SHA-256
    file_path   TEXT NOT NULL,
    title       TEXT NOT NULL,      -- nombre base sin extensión
    first_seen  TEXT NOT NULL       -- ISO-8601 UTC
  );
  CREATE INDEX IF NOT EXISTS idx_docs_first_seen ON docs(first_seen);
  ```

#### 2. Implementar Función de Hash
- **Función**: `compute_sha256(file_path: str) -> str`
- **Características**:
  - Lectura en chunks de 8192 bytes para eficiencia de memoria
  - Manejo de archivos grandes sin problemas de RAM
  - Integración en `dataset/processing/loaders/base_loader.py`

#### 3. Lógica de Deduplicación en Loader
- **Flujo**:
  1. Calcular hash del archivo
  2. Consultar tabla `docs` por hash existente
  3. Si existe → saltar con warning, registrar incidencia
  4. Si no existe → insertar registro, procesar normalmente
- **Activación**: Solo cuando `output_mode='biblioperson'`

#### 4. Módulo CLI de Deduplicación
- **Archivo**: `dataset/processing/dedup_cli.py`
- **Comandos**:
  ```bash
  dataset_cli dedup list [--search "texto"] [--before fecha] [--after fecha]
  dataset_cli dedup remove --hash <sha256> | --path <ruta> | --search <patrón>
  dataset_cli dedup prune --before <fecha>
  dataset_cli dedup clear
  ```

### 🎛️ Backend - Modos de Salida

#### 5. Parámetro output_mode
- **CLI**: `--output-mode generic|biblioperson`
- **GUI**: Checkbox "Salida Biblioperson"
- **Default**: `generic`

#### 6. Serialización Diferenciada
- **Modo Generic**:
  - Campos mínimos: `segment_id`, `text`, `segment_type`, `segment_order`
  - Sin `document_hash`, sin metadatos complejos
  - Ideal para alimentar LLMs

- **Modo Biblioperson**:
  - Estructura completa actual + `document_hash`
  - Todos los metadatos de trazabilidad
  - Compatible con sistema de indexación

#### 7. Campo document_hash
- **Inclusión**: Solo en modo `biblioperson`
- **Ubicación**: Dentro de `document_metadata`
- **Formato**: String SHA-256 hexadecimal

### 🌐 Backend - API REST

#### 8. Endpoint de Consulta
```http
GET /api/dedup?search=<texto>&before=<fecha>&after=<fecha>&limit=<num>
```
- **Respuesta**: Lista paginada de documentos duplicados
- **Filtros**: Búsqueda por título/ruta, rango de fechas

#### 9. Endpoint de Eliminación Individual
```http
DELETE /api/dedup/{hash}
```
- **Parámetro**: Hash SHA-256 del documento
- **Respuesta**: Confirmación de eliminación

#### 10. Endpoints de Eliminación Masiva
```http
POST /api/dedup/clear
POST /api/dedup/prune
Content-Type: application/json
{ "before": "2025-05-01T00:00:00Z" }
```

### 🖥️ Frontend - Interfaz de Usuario

#### 11. Checkbox "Salida Biblioperson"
- **Ubicación**: Sección "Procesamiento" (no pestaña separada)
- **Comportamiento**: 
  - Desmarcado → modo `generic`
  - Marcado → modo `biblioperson` + deduplicación activa

#### 12. Botón "Gestor de Duplicados"
- **Ubicación**: Junto al checkbox, dentro del contenedor con scroll
- **Acción**: Abrir modal de gestión

#### 13. Modal de Gestión de Duplicados
- **Componentes**:
  - Barra de búsqueda (placeholder: "Buscar por título o ruta...")
  - Filtros de fecha (calendario "Desde/Hasta")
  - Checkboxes rápidos (hoy/semana/mes)

#### 14. Tabla de Duplicados
- **Columnas**: 
  | ✓ | Fecha | Título | Ruta (relativa) | Hash (abreviado) | 🗑 |
- **Características**:
  - Selección múltiple con checkboxes
  - Botón papelera por fila
  - Sin scroll anidado (usa scroll del contenedor principal)

#### 15. Acciones Masivas
- **Botones**:
  - "Eliminar seleccionados"
  - "Eliminar todo el listado (X ítems)"
  - "Vaciar registro completo" (botón rojo con confirmación)

### ⚙️ CLI - Línea de Comandos

#### 16. Flag output-mode
```bash
dataset_cli ingest carpeta/ --output-mode generic    # NDJSON simple
dataset_cli ingest carpeta/ --output-mode biblioperson  # NDJSON rico + dedup
```

#### 17. Sub-comandos de Deduplicación
- **Integración**: Comandos `dedup` dentro del CLI principal
- **Salida**: Tabla ASCII para terminal, JSON para consumo programático

#### 18. Filtros y Opciones CLI
- **Por búsqueda**: `--search "monte cristo"`
- **Por fecha**: `--before 2025-06-01`, `--after 2025-05-01`
- **Por hash**: `--hash c3a9b2f1...`
- **Por ruta**: `--path "libros/novela.pdf"`

## 🗂️ Organización en Taskmaster

### Tarea Principal: #16
**"Implement Deduplication and Biblioperson/Generic Output Modes"**
- Estado: Pending
- Prioridad: High
- Subtareas: 8

### Subtareas Detalladas

| ID | Título | Accionables Cubiertos | Dependencias |
|----|--------|----------------------|--------------|
| 16.1 | Implement SHA-256 Hashing for Deduplication | 1, 2, 3 | Ninguna |
| 16.2 | Develop 'Generic' and 'Biblioperson' Output Modes | 5, 6, 7 | Ninguna |
| 16.3 | Create Duplicate Management Interface | 11, 12, 13, 14, 15 | 16.1 |
| 16.4 | Implement Optional Integration and Pipeline Compatibility | Integración general | 16.1, 16.2 |
| 16.5 | Document Implementation and Usage | Documentación | 16.1, 16.2, 16.3, 16.4 |
| 16.6 | Implementar CLI dedup con comandos list/remove/prune/clear | 4, 16, 17, 18 | Ninguna |
| 16.7 | Implementar API REST para gestión de duplicados | 8, 9, 10 | Ninguna |
| 16.8 | Implementar modal Gestor de Duplicados en UI | 11, 12, 13, 14, 15 | Ninguna |

## 🔄 Flujo de Implementación Recomendado

### Fase 1: Backend Core (Paralelo)
1. **16.1** - Sistema de hash y deduplicación
2. **16.2** - Modos de salida diferenciados

### Fase 2: Interfaces (Paralelo, requiere Fase 1)
3. **16.6** - CLI de gestión
4. **16.7** - API REST
5. **16.3** - UI Modal (requiere 16.1)

### Fase 3: Integración
6. **16.4** - Compatibilidad y opcionalidad
7. **16.8** - Refinamiento UI

### Fase 4: Finalización
8. **16.5** - Documentación completa

## 🧪 Estrategia de Pruebas

### Unit Tests
- Función `compute_sha256()` con archivos conocidos
- Lógica de deduplicación con casos edge
- Serialización diferenciada por modo

### Integration Tests
- Pipeline completo en ambos modos
- API endpoints con datos reales
- CLI commands con diferentes filtros

### UI Tests
- Modal de gestión con interacciones
- Búsqueda y filtros funcionales
- Acciones masivas seguras

### Performance Tests
- Impacto de deduplicación en velocidad
- Manejo de archivos grandes (>100MB)
- Consultas rápidas en SQLite con miles de registros

## 📊 Métricas de Éxito

- ✅ **Funcionalidad**: Deduplicación 100% efectiva
- ✅ **Performance**: <5% impacto en velocidad de procesamiento
- ✅ **Usabilidad**: Modal intuitivo con búsqueda <1s
- ✅ **Compatibilidad**: Cero cambios disruptivos en flujo actual
- ✅ **Flexibilidad**: Modo genérico reduce tamaño NDJSON >40%

## 🚀 Comandos de Inicio Rápido

```bash
# Ver estado actual
task-master show 16

# Comenzar implementación
task-master set-status --id=16.1 --status=in-progress

# Seguir progreso
task-master list --status=in-progress
```

## 📚 Referencias

- [Taskmaster Documentation](../.cursor/rules/taskmaster.mdc)
- [Development Workflow](../.cursor/rules/dev_workflow.mdc)
- [UI Guidelines](../.cursor/rules/cursor_rules.mdc)
- [Pipeline Architecture](../README.md)

---

**Documento creado**: 2025-06-14  
**Última actualización**: 2025-06-14  
**Estado**: Planificación completa ✅ 