# API REST de Deduplicación - Referencia Completa

## 📋 Información General

La API REST de deduplicación proporciona endpoints para gestionar documentos duplicados programáticamente. Está integrada automáticamente en el backend de Biblioperson cuando el sistema de deduplicación está disponible.

### Base URL
```
http://localhost:5000/api/dedup
```

### Formato de Respuesta
Todas las respuestas están en formato JSON con la siguiente estructura:

```json
{
  "success": true,
  "data": { ... },
  "message": "Descripción de la operación",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 400 | Solicitud inválida |
| 404 | Recurso no encontrado |
| 500 | Error interno del servidor |

## 📚 Endpoints Disponibles

### 1. Listar Documentos

**GET** `/api/dedup`

Lista todos los documentos registrados con filtros opcionales.

#### Parámetros de Consulta

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `search` | string | Buscar en título o ruta | `?search=novela` |
| `before` | string | Documentos antes de fecha (YYYY-MM-DD) | `?before=2025-06-01` |
| `after` | string | Documentos después de fecha (YYYY-MM-DD) | `?after=2025-01-01` |
| `limit` | integer | Máximo número de resultados | `?limit=50` |
| `offset` | integer | Número de resultados a saltar | `?offset=100` |

#### Ejemplo de Solicitud

```bash
curl "http://localhost:5000/api/dedup?search=quijote&limit=10"
```

#### Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "hash": "a1b2c3d4e5f6789...",
        "file_path": "/docs/don_quijote.pdf",
        "title": "Don Quijote de la Mancha",
        "first_seen": "2025-06-14T10:30:00Z",
        "file_size": 2048576
      }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
  },
  "message": "Documentos recuperados exitosamente",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### 2. Eliminar por Hash

**DELETE** `/api/dedup/{hash}`

Elimina un documento específico por su hash SHA-256.

#### Parámetros de Ruta

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `hash` | string | Hash SHA-256 del documento |

#### Ejemplo de Solicitud

```bash
curl -X DELETE "http://localhost:5000/api/dedup/a1b2c3d4e5f6789..."
```

#### Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "hash": "a1b2c3d4e5f6789...",
    "removed": true
  },
  "message": "Documento eliminado exitosamente",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### 3. Eliminar por Ruta

**DELETE** `/api/dedup/path`

Elimina un documento específico por su ruta de archivo.

#### Cuerpo de la Solicitud

```json
{
  "file_path": "/ruta/al/archivo.pdf"
}
```

#### Ejemplo de Solicitud

```bash
curl -X DELETE "http://localhost:5000/api/dedup/path" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/docs/mi_documento.pdf"}'
```

#### Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "file_path": "/docs/mi_documento.pdf",
    "removed": true
  },
  "message": "Documento eliminado exitosamente",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### 4. Limpiar Todos los Documentos

**POST** `/api/dedup/clear`

Elimina todos los documentos de la base de datos de deduplicación.

#### Cuerpo de la Solicitud

```json
{
  "confirm": true
}
```

#### Ejemplo de Solicitud

```bash
curl -X POST "http://localhost:5000/api/dedup/clear" \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

#### Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "documents_removed": 150,
    "operation": "clear_all"
  },
  "message": "Todos los documentos eliminados exitosamente",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### 5. Eliminar por Fecha (Prune)

**POST** `/api/dedup/prune`

Elimina documentos procesados antes de una fecha específica.

#### Cuerpo de la Solicitud

```json
{
  "before": "2025-01-01",
  "confirm": true
}
```

#### Ejemplo de Solicitud

```bash
curl -X POST "http://localhost:5000/api/dedup/prune" \
  -H "Content-Type: application/json" \
  -d '{"before": "2025-01-01", "confirm": true}'
```

#### Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "documents_removed": 25,
    "before_date": "2025-01-01",
    "operation": "prune"
  },
  "message": "Documentos antiguos eliminados exitosamente",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### 6. Obtener Estadísticas

**GET** `/api/dedup/stats`

Obtiene estadísticas generales de la base de datos de deduplicación.

#### Ejemplo de Solicitud

```bash
curl "http://localhost:5000/api/dedup/stats"
```

#### Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "total_documents": 150,
    "total_size_bytes": 104857600,
    "total_size_human": "100 MB",
    "oldest_document": "2025-01-15T08:30:00Z",
    "newest_document": "2025-06-14T22:30:00Z",
    "documents_today": 5,
    "documents_this_week": 23,
    "documents_this_month": 87,
    "average_file_size": 699050,
    "database_size_bytes": 32768,
    "database_size_human": "32 KB"
  },
  "message": "Estadísticas recuperadas exitosamente",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### 7. Eliminación por Lotes

**DELETE** `/api/dedup/batch`

Elimina múltiples documentos por sus hashes.

#### Cuerpo de la Solicitud

```json
{
  "hashes": [
    "a1b2c3d4e5f6789...",
    "b2c3d4e5f6789a...",
    "c3d4e5f6789ab..."
  ],
  "confirm": true
}
```

#### Ejemplo de Solicitud

```bash
curl -X DELETE "http://localhost:5000/api/dedup/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "hashes": ["a1b2c3...", "b2c3d4..."],
    "confirm": true
  }'
```

#### Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "requested": 2,
    "removed": 2,
    "not_found": 0,
    "operation": "batch_delete"
  },
  "message": "Eliminación por lotes completada",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

## 🚨 Manejo de Errores

### Errores Comunes

#### 400 - Solicitud Inválida

```json
{
  "success": false,
  "error": "INVALID_REQUEST",
  "message": "Parámetro 'before' debe estar en formato YYYY-MM-DD",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

#### 404 - No Encontrado

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Documento con hash 'a1b2c3...' no encontrado",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

#### 500 - Error Interno

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Error de base de datos: no se puede acceder al archivo",
  "timestamp": "2025-06-14T22:45:19.823Z"
}
```

### Códigos de Error Específicos

| Código | Descripción |
|--------|-------------|
| `INVALID_REQUEST` | Parámetros de solicitud inválidos |
| `MISSING_CONFIRMATION` | Falta confirmación para operación destructiva |
| `INVALID_DATE_FORMAT` | Formato de fecha incorrecto |
| `INVALID_HASH` | Hash SHA-256 inválido |
| `NOT_FOUND` | Recurso no encontrado |
| `DATABASE_ERROR` | Error de acceso a base de datos |
| `INTERNAL_ERROR` | Error interno del servidor |

## 🔧 Ejemplos de Uso

### Ejemplo 1: Buscar y Eliminar Duplicados

```python
import requests

# Buscar documentos con "novela" en el título
response = requests.get(
    "http://localhost:5000/api/dedup",
    params={"search": "novela", "limit": 10}
)

documents = response.json()["data"]["documents"]

# Eliminar el primer documento encontrado
if documents:
    hash_to_delete = documents[0]["hash"]
    delete_response = requests.delete(
        f"http://localhost:5000/api/dedup/{hash_to_delete}"
    )
    print(f"Eliminado: {delete_response.json()['message']}")
```

### Ejemplo 2: Limpieza Programática

```python
import requests
from datetime import datetime, timedelta

# Eliminar documentos más antiguos de 30 días
cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

response = requests.post(
    "http://localhost:5000/api/dedup/prune",
    json={"before": cutoff_date, "confirm": True}
)

result = response.json()
print(f"Eliminados {result['data']['documents_removed']} documentos antiguos")
```

### Ejemplo 3: Monitoreo de Estadísticas

```python
import requests

def get_dedup_stats():
    response = requests.get("http://localhost:5000/api/dedup/stats")
    stats = response.json()["data"]
    
    print(f"Total documentos: {stats['total_documents']}")
    print(f"Tamaño total: {stats['total_size_human']}")
    print(f"Documentos hoy: {stats['documents_today']}")
    print(f"Documentos esta semana: {stats['documents_this_week']}")

get_dedup_stats()
```

### Ejemplo 4: Cliente Python Completo

```python
import requests
from typing import List, Dict, Optional

class DeduplicationClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = f"{base_url}/api/dedup"
    
    def list_documents(self, search: str = None, before: str = None, 
                      after: str = None, limit: int = 100, 
                      offset: int = 0) -> Dict:
        """Lista documentos con filtros opcionales."""
        params = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        if before:
            params["before"] = before
        if after:
            params["after"] = after
            
        response = requests.get(self.base_url, params=params)
        return response.json()
    
    def delete_by_hash(self, document_hash: str) -> Dict:
        """Elimina documento por hash."""
        response = requests.delete(f"{self.base_url}/{document_hash}")
        return response.json()
    
    def delete_by_path(self, file_path: str) -> Dict:
        """Elimina documento por ruta."""
        response = requests.delete(
            f"{self.base_url}/path",
            json={"file_path": file_path}
        )
        return response.json()
    
    def clear_all(self) -> Dict:
        """Elimina todos los documentos."""
        response = requests.post(
            f"{self.base_url}/clear",
            json={"confirm": True}
        )
        return response.json()
    
    def prune_before(self, before_date: str) -> Dict:
        """Elimina documentos antes de fecha."""
        response = requests.post(
            f"{self.base_url}/prune",
            json={"before": before_date, "confirm": True}
        )
        return response.json()
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas."""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()
    
    def batch_delete(self, hashes: List[str]) -> Dict:
        """Elimina múltiples documentos por hash."""
        response = requests.delete(
            f"{self.base_url}/batch",
            json={"hashes": hashes, "confirm": True}
        )
        return response.json()

# Uso del cliente
client = DeduplicationClient()

# Obtener estadísticas
stats = client.get_stats()
print(f"Total: {stats['data']['total_documents']}")

# Buscar y eliminar
docs = client.list_documents(search="test")
if docs["data"]["documents"]:
    result = client.delete_by_hash(docs["data"]["documents"][0]["hash"])
    print(f"Eliminado: {result['message']}")
```

## 🔒 Seguridad y Consideraciones

### Autenticación
La API actualmente no requiere autenticación, pero se recomienda implementar autenticación en entornos de producción.

### Validación de Entrada
- Todos los parámetros de fecha se validan en formato YYYY-MM-DD
- Los hashes se validan como strings hexadecimales válidos
- Las rutas de archivo se normalizan para prevenir ataques de path traversal

### Operaciones Destructivas
- Todas las operaciones de eliminación requieren confirmación explícita
- Las operaciones masivas (clear, prune, batch) requieren el parámetro `confirm: true`

### Límites de Tasa
- No hay límites de tasa implementados actualmente
- Se recomienda implementar rate limiting en producción

## 📊 Monitoreo y Logging

### Logs de API
Todas las operaciones se registran con el siguiente formato:

```
[2025-06-14 22:45:19] INFO: API /api/dedup GET - search=novela, limit=10
[2025-06-14 22:45:20] INFO: API /api/dedup/{hash} DELETE - hash=a1b2c3...
[2025-06-14 22:45:21] ERROR: API /api/dedup/clear POST - Missing confirmation
```

### Métricas Recomendadas
- Número de solicitudes por endpoint
- Tiempo de respuesta promedio
- Errores por tipo
- Documentos eliminados por día
- Uso de filtros de búsqueda

### Health Check
```bash
curl "http://localhost:5000/api/dedup/stats"
```

Si la respuesta es exitosa (200), la API está funcionando correctamente.

---

Esta API proporciona una interfaz completa para gestionar la deduplicación programáticamente, permitiendo integración con sistemas externos y automatización de tareas de mantenimiento. 