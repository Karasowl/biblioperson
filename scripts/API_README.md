# API Flask para Biblioperson - Servidor Puente

## 🎯 Propósito

Este servidor Flask actúa como **puente/intermediario** entre el frontend Next.js y las funcionalidades existentes del sistema de procesamiento de datasets de Biblioperson.

**IMPORTANTE**: Este servidor **NO modifica** ninguna lógica existente del sistema `/dataset`. Solo expone las funcionalidades ya implementadas como API REST.

## 🏗️ Arquitectura

```
Frontend Next.js  ←→  API Flask (Puente)  ←→  Sistema Dataset Existente
     (app/)              (scripts/)              (dataset/)
```

### Componentes Preservados
- ✅ **UI de Python (PyQt/PySide6)**: Sigue funcionando independientemente
- ✅ **ProfileManager**: Sin modificaciones
- ✅ **core_process**: Lógica de procesamiento intacta
- ✅ **Sistema de deduplicación**: Blueprint existente integrado
- ✅ **CLI**: Funcionalidades de línea de comandos preservadas

## 🚀 Uso

### Iniciar el Servidor

```bash
# Desde el directorio raíz del proyecto
cd e:\dev-projects\biblioperson
python scripts/api_conexion.py
```

### Usando npm (como está configurado)

```bash
npm run dev:backend
```

## 📡 Endpoints Disponibles

### Estado del Servidor
- `GET /api/health` - Verificar que el servidor está funcionando

### Gestión de Perfiles
- `GET /api/profiles` - Lista todos los perfiles disponibles
- `GET /api/profiles/<nombre>` - Detalles de un perfil específico

### Procesamiento de Documentos
- `POST /api/processing/start` - Iniciar un trabajo de procesamiento
- `GET /api/processing/status/<job_id>` - Estado de un trabajo específico
- `GET /api/processing/jobs` - Lista todos los trabajos

### Exploración de Archivos
- `GET /api/files/browse?path=<ruta>` - Explorar directorios y archivos

### Deduplicación (Sistema Existente)
- `GET /dedup/stats` - Estadísticas de deduplicación
- `POST /dedup/check` - Verificar duplicados
- `DELETE /dedup/<hash>` - Eliminar por hash
- Y todos los demás endpoints del sistema de deduplicación existente

## 🔧 Ejemplos de Uso

### 1. Verificar Estado del Servidor

```bash
curl http://localhost:5000/api/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

### 2. Obtener Lista de Perfiles

```bash
curl http://localhost:5000/api/profiles
```

**Respuesta:**
```json
{
  "success": true,
  "profiles": [
    {
      "name": "literatura_clasica",
      "description": "Perfil para literatura clásica",
      "format_group": "text_based"
    }
  ]
}
```

### 3. Iniciar Procesamiento

```bash
curl -X POST http://localhost:5000/api/processing/start \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "C:/ruta/a/documentos",
    "profile": "literatura_clasica",
    "verbose": true
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "job_id": "job_1",
  "message": "Procesamiento iniciado"
}
```

### 4. Verificar Estado del Procesamiento

```bash
curl http://localhost:5000/api/processing/status/job_1
```

**Respuesta:**
```json
{
  "success": true,
  "job": {
    "id": "job_1",
    "status": "running",
    "progress": 75,
    "message": "Procesando archivos...",
    "stats": {
      "files_processed": 15,
      "files_success": 14,
      "files_error": 1
    }
  }
}
```

## 🔗 Integración con Frontend

En tu frontend Next.js, puedes usar estos endpoints así:

```typescript
// services/api.ts
const API_BASE = 'http://localhost:5000/api';

export const processingAPI = {
  // Iniciar procesamiento
  async startProcessing(config: ProcessingConfig) {
    const response = await fetch(`${API_BASE}/processing/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return response.json();
  },

  // Verificar estado
  async getJobStatus(jobId: string) {
    const response = await fetch(`${API_BASE}/processing/status/${jobId}`);
    return response.json();
  },

  // Obtener perfiles
  async getProfiles() {
    const response = await fetch(`${API_BASE}/profiles`);
    return response.json();
  }
};
```

## 🛡️ Características de Seguridad

- **CORS habilitado**: Permite conexiones desde el frontend
- **Validación de entrada**: Verifica datos requeridos
- **Manejo de errores**: Respuestas consistentes en caso de error
- **Aislamiento de procesos**: Cada trabajo se ejecuta en su propio hilo

## 🔄 Estados de Procesamiento

- `pending`: Trabajo creado, esperando inicio
- `running`: Procesamiento en curso
- `completed`: Procesamiento exitoso
- `error`: Error durante el procesamiento

## 📝 Notas Importantes

1. **No Modificación**: Este servidor NO modifica el sistema `/dataset` existente
2. **Compatibilidad**: La UI de Python sigue funcionando independientemente
3. **Extensibilidad**: Fácil agregar nuevos endpoints sin afectar funcionalidad existente
4. **Desarrollo**: Servidor de desarrollo Flask (para producción usar Gunicorn/uWSGI)

## 🐛 Solución de Problemas

### Error de Importación
Si ves errores como `ModuleNotFoundError`, asegúrate de ejecutar desde el directorio raíz:

```bash
cd e:\dev-projects\biblioperson
python scripts/api_conexion.py
```

### Puerto Ocupado
Si el puerto 5000 está ocupado, puedes cambiarlo:

```bash
set PORT=5001
python scripts/api_conexion.py
```

### Problemas de CORS
El servidor ya tiene CORS habilitado. Si tienes problemas, verifica que el frontend esté haciendo peticiones a `http://localhost:5000`.

## 🎯 Próximos Pasos

1. **Integrar con Frontend**: Conectar los endpoints con tu UI de Next.js
2. **Mejorar Progreso**: Implementar seguimiento de progreso en tiempo real
3. **WebSockets**: Para actualizaciones en tiempo real del estado de procesamiento
4. **Autenticación**: Si es necesario para producción

---

**Recuerda**: Este servidor es un puente que preserva toda la funcionalidad existente mientras permite la integración con el frontend moderno.