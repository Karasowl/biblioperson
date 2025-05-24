# Inicio Rápido - Biblioperson

## ¿Qué es Biblioperson?

Biblioperson convierte tu biblioteca personal en una base de conocimiento consultable. Imagina poder preguntarle a todos tus libros y documentos: "¿Qué piensa este autor sobre X tema?" o "¿Dónde he leído algo sobre Y concepto?"

## ¿Qué puedes hacer?

- **Buscar ideas específicas**: Encuentra qué dice un autor particular sobre cualquier tema
- **Descubrir conexiones**: Encuentra relaciones entre diferentes textos y autores
- **Generar contenido**: Crea material original basado en las ideas de tu biblioteca
- **Navegar como ebooks**: Reconstruye y navega tus documentos originales
- **Búsqueda semántica**: Encuentra conceptos similares aunque usen palabras diferentes

## Flujo de Trabajo Simple

```
Tus Documentos → Procesamiento → Base de Datos → Búsqueda Inteligente
   (PDF, DOCX,      (NDJSON)        (SQLite +      (Web + API)
    TXT, MD)                        Meilisearch)
```

## Instalación Rápida (5 pasos)

### 1. Preparar el entorno
```bash
# Clonar y entrar al proyecto
git clone [URL_DEL_REPOSITORIO]
cd biblioperson

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 2. Instalar dependencias
```bash
# Backend
pip install -r backend/requirements.txt

# Dataset (procesamiento)
pip install -r dataset/requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 3. Procesar tu primer documento
```bash
# Coloca un documento de prueba en dataset/raw_data/autor_prueba/
# Luego procésalo:
cd dataset
python scripts/app_depuracion.py
```

### 4. Importar a la base de datos
```bash
cd ../backend/scripts
python importar_completo.py
```

### 5. Levantar la aplicación
```bash
# Terminal 1: Backend
cd backend/scripts
python api_conexion.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

¡Abre http://localhost:5173 y comienza a buscar!

## Ejemplo Práctico

### Documento de entrada:
`mi_libro.pdf` → "Capítulo 1: La filosofía griega..."

### Después del procesamiento:
- **Segmento 1**: `{"texto_segmento": "La filosofía griega...", "tipo_segmento": "parrafo", "autor_documento": "Platón", "jerarquia_contextual": {"capitulo": "1"}}`
- **Búsqueda**: "filosofía antigua" → Encuentra este segmento aunque no diga "antigua"
- **Navegación**: Reconstruye el libro completo desde la base de datos

## Próximos Pasos

- **Documentación técnica**: Ver `BIBLIOPERSON_ARQUITECTURA.md`
- **Especificaciones NDJSON**: Ver `NDJSON_ESPECIFICACION.md`
- **Configuración avanzada**: Ver `GUIA_MEILISEARCH.md`
- **Gestión de datos**: Ver `GUIA_GESTION_DATOS.md`

## Solución de Problemas Comunes

### Error: "No se encuentra meilisearch"
```bash
# Descargar meilisearch desde:
# https://github.com/meilisearch/meilisearch/releases
# Colocar el ejecutable en backend/meilisearch/
```

### Error: "Base de datos no existe"
```bash
cd backend/scripts
python inicializar_db.py
```

### Error: "Puerto ocupado"
- Backend usa puerto 5000
- Frontend usa puerto 5173
- Meilisearch usa puerto 7700

¿Necesitas ayuda? Revisa la documentación completa en la carpeta `docs/`.