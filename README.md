# Biblioteca de Conocimiento Personal

Sistema para gestionar y analizar contenido personal de diferentes plataformas y fuentes.

## Características

- Importación de contenido desde múltiples fuentes (Facebook, Twitter, Telegram, documentos)
- Análisis de evolución del pensamiento
- Identificación de patrones argumentales
- Generación de material para nuevo contenido
- API REST para acceso a los datos
- Interfaz web para exploración y análisis

## Requisitos

- Python 3.8+
- SQLite3
- Navegador web moderno

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd biblioperson
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Iniciar el backend:
```bash
python scripts/api_conexion.py
```

2. Servir el frontend:
```bash
cd interfaz
python -m http.server 8000
```

3. Acceder a la aplicación:
- Frontend: http://localhost:8000
- API: http://localhost:5000

## Estructura del Proyecto

- `scripts/`: Scripts de Python para la API y procesamiento
- `interfaz/`: Archivos del frontend
- `contenido/`: Contenido personal importado
- `indices/`: Índices generados
- `analisis/`: Resultados de análisis
- `exportacion/`: Archivos exportados

## Licencia

[ESPECIFICAR LICENCIA]