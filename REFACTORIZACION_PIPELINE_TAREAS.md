# 🔄 Refactorización Pipeline Biblioperson - Plan de Tareas

## 📋 Estado General del Proyecto
- **Inicio**: [Fecha]
- **Estado**: 🟡 En Planificación
- **Hardware**: i7 14ª gen + RTX 4060 8GB
- **Corpus**: ~150GB documentos
- **Chunk target**: 750 caracteres + 200 overlap

---

## 🎯 FASE 1: Ingesta y Parsing Unificado
**Objetivo**: Reemplazar loaders/segmenters manuales con unstructured + OCR

### ✅ Tarea 1.1: Investigar e instalar dependencias
- [ ] **Estado**: ⏳ Pendiente
- [ ] Instalar `unstructured[all-docs]`
- [ ] Instalar `pdf2image` 
- [ ] Instalar `pytesseract`
- [ ] Configurar Tesseract PATH en Windows
- [ ] Test básico de cada librería
- **Archivos afectados**: `requirements.txt`, `setup.py`
- **Tiempo estimado**: 2-3 horas

### ✅ Tarea 1.2: Crear módulo de ingesta unificado
- [ ] **Estado**: ⏳ Pendiente
- [ ] Crear `src/pipeline/ingest.py`
- [ ] Función `detect_document_type(file_path)` → digital vs escaneado
- [ ] Función `extract_to_markdown(file_path)` → Markdown unificado
- [ ] Soporte OCR para PDFs escaneados
- [ ] Soporte directo para DOCX/EPUB/TXT
- **Archivos afectados**: `src/pipeline/ingest.py` (nuevo)
- **Tiempo estimado**: 8-10 horas

### ✅ Tarea 1.3: Configurar chunking con LangChain
- [ ] **Estado**: ⏳ Pendiente
- [ ] Instalar `langchain-text-splitters`
- [ ] Configurar `RecursiveCharacterTextSplitter`
- [ ] Chunk size = 750, overlap = 200
- [ ] Crear `config/chunking.yaml`
- [ ] Test con documentos de diferentes tipos
- **Archivos afectados**: `config/chunking.yaml` (nuevo), `requirements.txt`
- **Tiempo estimado**: 4-5 horas

### ✅ Tarea 1.4: Normalizar procesamiento NDJSON/JSON
- [ ] **Estado**: ⏳ Pendiente
- [ ] Stream línea-a-línea para NDJSON
- [ ] Extraer solo campo `text` de cada objeto
- [ ] Convertir a Markdown para chunking uniforme
- [ ] Test con archivos grandes (>1GB)
- **Archivos afectados**: `src/pipeline/ingest.py`
- **Tiempo estimado**: 3-4 horas

### ✅ Tarea 1.5: Eliminar loaders/segmenters obsoletos
- [ ] **Estado**: ⏳ Pendiente
- [ ] Deprecar `dataset/processing/loaders/`
- [ ] Deprecar `dataset/processing/segmenters/`
- [ ] Migrar tests a nueva implementación
- [ ] Actualizar documentación
- **Archivos afectados**: `dataset/processing/` (limpieza)
- **Tiempo estimado**: 2-3 horas

---

## 🗄️ FASE 2: Almacenamiento para Reconstrucción
**Objetivo**: Rediseñar esquema SQLite para soporte dual (lectura + búsqueda)

### ✅ Tarea 2.1: Diseñar nuevo esquema SQLite
- [ ] **Estado**: ⏳ Pendiente
- [ ] Tabla `documents` (id, title, author, metadata)
- [ ] Tabla `structural_blocks` (doc_id, order, type, text)
- [ ] Índices optimizados para consultas
- [ ] Script SQL de creación
- **Archivos afectados**: `database/schema_v2.sql` (nuevo)
- **Tiempo estimado**: 3-4 horas

### ✅ Tarea 2.2: Script de migración de datos
- [ ] **Estado**: ⏳ Pendiente
- [ ] Backup automático de BD actual
- [ ] Migrar datos existentes al nuevo esquema
- [ ] Validar integridad post-migración
- [ ] Script de rollback
- **Archivos afectados**: `scripts/migrate_database.py` (nuevo)
- **Tiempo estimado**: 6-8 horas

### ✅ Tarea 2.3: Implementar persistencia desde unstructured
- [ ] **Estado**: ⏳ Pendiente
- [ ] Función `save_structural_blocks(doc, elements)`
- [ ] Preservar orden y tipo de elementos
- [ ] Batch insert optimizado (>2000 blocks/s)
- [ ] Manejo de errores y transacciones
- **Archivos afectados**: `src/database/persistence.py`
- **Tiempo estimado**: 5-6 horas

### ✅ Tarea 2.4: Eliminar columnas redundantes
- [ ] **Estado**: ⏳ Pendiente
- [ ] Identificar campos obsoletos en esquema actual
- [ ] Limpiar hashes, offsets, flags no utilizados
- [ ] Optimizar tamaño de BD
- [ ] Documentar cambios
- **Archivos afectados**: `database/schema_v2.sql`
- **Tiempo estimado**: 2-3 horas

---

## 🔍 FASE 3: Indexación Semántica (RAG)
**Objetivo**: Pipeline de embeddings intercambiable con FAISS local

### ✅ Tarea 3.1: Módulo de embeddings intercambiable
- [ ] **Estado**: ⏳ Pendiente
- [ ] Clase `EmbeddingClient` abstracta
- [ ] Backend local: `HuggingFaceEmbeddings` (bge-large-es)
- [ ] Backend cloud: `OpenAIEmbeddings` (text-embedding-3-small)
- [ ] Configuración via ENV: `EMBEDDING_BACKEND=local|openai`
- [ ] Auto-detección de GPU disponible
- **Archivos afectados**: `src/embeddings/client.py` (nuevo)
- **Tiempo estimado**: 6-8 horas

### ✅ Tarea 3.2: Configurar modelos locales
- [ ] **Estado**: ⏳ Pendiente
- [ ] Instalar `sentence-transformers`
- [ ] Descargar `BAAI/bge-large-es` (1024 dims)
- [ ] Test en RTX 4060 (verificar <8GB VRAM)
- [ ] Benchmark: >300 chunks/s
- [ ] Fallback a CPU si GPU no disponible
- **Archivos afectados**: `config/embeddings.yaml` (nuevo)
- **Tiempo estimado**: 4-5 horas

### ✅ Tarea 3.3: Implementar indexación FAISS
- [ ] **Estado**: ⏳ Pendiente
- [ ] Instalar `faiss-cpu` y `faiss-gpu`
- [ ] Crear índices FAISS flat L2 por documento
- [ ] Persistencia en `indexes/{doc_id}.faiss`
- [ ] Batch processing optimizado para GPU
- [ ] Procesamiento incremental (solo docs nuevos)
- **Archivos afectados**: `src/search/faiss_index.py` (nuevo)
- **Tiempo estimado**: 8-10 horas

### ✅ Tarea 3.4: Pipeline de chunking para búsqueda
- [ ] **Estado**: ⏳ Pendiente
- [ ] Concatenar texto de `structural_blocks`
- [ ] Aplicar `RecursiveCharacterTextSplitter`
- [ ] Generar embeddings por chunk
- [ ] Mantener metadatos (doc_id, chunk_index)
- **Archivos afectados**: `src/search/chunking.py`
- **Tiempo estimado**: 4-5 horas

### ✅ Tarea 3.5: Búsqueda semántica con re-ranking
- [ ] **Estado**: ⏳ Pendiente
- [ ] Función `search(query)` → embed → FAISS top-k
- [ ] Re-ranking opcional con `bge-reranker-large`
- [ ] Configurar k=20 por defecto
- [ ] Métricas de similitud y tiempo de respuesta
- [ ] API endpoint `/api/search/semantic`
- **Archivos afectados**: `src/search/semantic.py`, `app/src/app/api/search/semantic/route.ts`
- **Tiempo estimado**: 6-8 horas

---

## 🖥️ FASE 4: Frontend y Ampliaciones
**Objetivo**: Integrar python-bible y actualizar componentes UI

### ✅ Tarea 4.1: Integrar python-bible
- [ ] **Estado**: ⏳ Pendiente
- [ ] Instalar `python-bible`
- [ ] Cargar múltiples versiones (ESV, RVR60, NVI)
- [ ] Almacenar en esquema unificado (`documents`/`structural_blocks`)
- [ ] Navegación por libro/capítulo/verso
- [ ] API endpoints para consulta bíblica
- **Archivos afectados**: `src/bible/`, `app/src/app/api/bible/` (nuevos)
- **Tiempo estimado**: 8-10 horas

### ✅ Tarea 4.2: Actualizar EbookReader
- [ ] **Estado**: ⏳ Pendiente
- [ ] Leer desde tabla `structural_blocks`
- [ ] Renderizar elementos por tipo (Title → `<h1>`, NarrativeText → `<p>`)
- [ ] Preservar orden original del documento
- [ ] Navegación fluida entre bloques
- [ ] Soporte para libros bíblicos
- **Archivos afectados**: `app/src/components/ebook/EbookReader.tsx`
- **Tiempo estimado**: 6-8 horas

### ✅ Tarea 4.3: Actualizar Chatbot con RAG
- [ ] **Estado**: ⏳ Pendiente
- [ ] Integrar búsqueda semántica en chatbot
- [ ] Enviar chunks encontrados como contexto a LLM
- [ ] Mostrar fuentes de información en respuesta
- [ ] UI para ajustar número de chunks (k)
- [ ] Historial de conversación con contexto
- **Archivos afectados**: `app/src/components/chatbot/`, `app/src/app/api/chat/`
- **Tiempo estimado**: 8-10 horas

### ✅ Tarea 4.4: UI para configuración de chunking
- [ ] **Estado**: ⏳ Pendiente
- [ ] Slider para chunk size (500-1000 caracteres)
- [ ] Slider para overlap (100-300 caracteres)
- [ ] Preview de chunking en tiempo real
- [ ] Guardar configuración por usuario
- [ ] Re-indexar automáticamente si cambian parámetros
- **Archivos afectados**: `app/src/app/settings/page.tsx`
- **Tiempo estimado**: 4-5 horas

### ✅ Tarea 4.5: Navegación bíblica avanzada
- [ ] **Estado**: ⏳ Pendiente
- [ ] Selector de versión bíblica
- [ ] Navegación por libro/capítulo/verso
- [ ] Búsqueda por referencia (ej: "Juan 3:16")
- [ ] Comparación entre versiones
- [ ] Marcadores y notas en versículos
- **Archivos afectados**: `app/src/components/bible/` (nuevo)
- **Tiempo estimado**: 10-12 horas

---

## 🧪 FASE 5: Testing y Optimización
**Objetivo**: Validar calidad y rendimiento del nuevo pipeline

### ✅ Tarea 5.1: Suite de tests automatizados
- [ ] **Estado**: ⏳ Pendiente
- [ ] Tests unitarios para cada módulo
- [ ] Tests de integración end-to-end
- [ ] Tests de rendimiento (GPU/CPU)
- [ ] Tests de calidad de búsqueda
- [ ] CI/CD pipeline
- **Archivos afectados**: `tests/` (refactor completo)
- **Tiempo estimado**: 12-15 horas

### ✅ Tarea 5.2: Métricas de calidad de búsqueda
- [ ] **Estado**: ⏳ Pendiente
- [ ] Dataset de queries de prueba (Platón, poesía, Biblia)
- [ ] Métricas: Recall@10, Precision@10, MRR
- [ ] Comparación: sistema actual vs nuevo
- [ ] Target: Recall@10 ≥ 90%
- [ ] Dashboard de métricas
- **Archivos afectados**: `tests/evaluation/` (nuevo)
- **Tiempo estimado**: 8-10 horas

### ✅ Tarea 5.3: Optimización de rendimiento
- [ ] **Estado**: ⏳ Pendiente
- [ ] Profiling de memoria y CPU
- [ ] Optimización de batch processing
- [ ] Cache de embeddings frecuentes
- [ ] Compresión de índices FAISS
- [ ] Target: <500ms por búsqueda
- **Archivos afectados**: Múltiples archivos de optimización
- **Tiempo estimado**: 10-12 horas

### ✅ Tarea 5.4: Documentación y limpieza
- [ ] **Estado**: ⏳ Pendiente
- [ ] Actualizar README con nuevo pipeline
- [ ] Documentar APIs y configuración
- [ ] Guías de instalación y uso
- [ ] Eliminar código obsoleto
- [ ] Changelog detallado
- **Archivos afectados**: `docs/`, `README.md`
- **Tiempo estimado**: 6-8 horas

---

## 📊 Resumen de Progreso

### Por Fase
- **FASE 1** (Ingesta): 0/5 tareas completadas (0%)
- **FASE 2** (Almacenamiento): 0/4 tareas completadas (0%)
- **FASE 3** (RAG): 0/5 tareas completadas (0%)
- **FASE 4** (Frontend): 0/5 tareas completadas (0%)
- **FASE 5** (Testing): 0/4 tareas completadas (0%)

### Total General
**0/23 tareas completadas (0%)**

### Tiempo Estimado Total
**140-180 horas** (aproximadamente 4-6 semanas a tiempo completo)

---

## 🔧 Dependencias Técnicas a Instalar

```bash
# Procesamiento de documentos
pip install unstructured[all-docs]
pip install pdf2image
pip install pytesseract

# LangChain y chunking
pip install langchain-text-splitters
pip install langchain-community

# Embeddings y búsqueda
pip install sentence-transformers
pip install faiss-cpu faiss-gpu
pip install transformers torch

# Biblia
pip install python-bible

# Utilidades
pip install huggingface-hub
pip install numpy pandas
```

---

## 📝 Notas de Implementación

### Prioridades
1. **FASE 1** es crítica - sin esto no avanzamos
2. **FASE 3** es el corazón del sistema - embeddings y búsqueda
3. **FASE 2** puede hacerse en paralelo con FASE 3
4. **FASE 4** depende de FASE 2 completada
5. **FASE 5** es continua durante todo el proyecto

### Riesgos Identificados
- ⚠️ **GPU Memory**: Verificar que bge-large-es cabe en 8GB
- ⚠️ **Migración de datos**: Backup obligatorio antes de cambiar esquema
- ⚠️ **Rendimiento**: Puede requerir optimizaciones adicionales
- ⚠️ **Calidad**: Sistema actual podría ser mejor en algunos casos

### Checkpoints de Validación
- [ ] **Checkpoint 1**: Pipeline básico funciona con un documento
- [ ] **Checkpoint 2**: Migración de BD completada sin pérdidas
- [ ] **Checkpoint 3**: Búsqueda semántica supera sistema actual
- [ ] **Checkpoint 4**: UI integrada y funcional
- [ ] **Checkpoint 5**: Tests pasan y métricas son satisfactorias

---

*Última actualización: [Fecha]*
*Próxima revisión: [Fecha]* 