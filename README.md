# Biblioteca de Conocimiento Personal

Sistema para gestionar y analizar contenido personal de diferentes plataformas y fuentes.

## Características

- Importación de contenido desde múltiples fuentes (Facebook, Twitter, Telegram, documentos)
- Exploración de contenido por temas, fechas y plataformas
- Generación de material para nuevo contenido
- API REST para acceso a los datos
- Interfaz web para exploración y análisis

## Requisitos

- Python 3.8+
- Node.js 16+
- SQLite3
- Navegador web moderno

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd biblioperson
```

2. Crear y activar entorno virtual de Python:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias de Python:
```bash
pip install -r requirements.txt
```

4. Instalar dependencias de Node.js:
```bash
npm install
```

## Uso

1. Iniciar el proyecto en modo desarrollo:
```bash
npm run dev
```

Este comando iniciará:
- El servidor backend (Python/Flask) en http://localhost:5000
- El servidor frontend (Vite) en http://localhost:5173

## Estructura del Proyecto

- `src/`: Archivos del frontend (HTML, CSS, JS)
- `scripts/`: Scripts de Python para la API y procesamiento
- `contenido/`: Contenido personal importado
- `indices/`: Índices generados
- `exportacion/`: Archivos exportados
- `documentacion/`: Documentación del proyecto

## Licencia

[ESPECIFICAR LICENCIA]