# 🔍 Guía de Instalación de Tesseract OCR

## Para Desarrollo Local



### Windows
```bash
# Opción 1: Chocolatey (Recomendado)
choco install tesseract

# Opción 2: Scoop
scoop install tesseract

# Opción 3: Descarga Manual
# Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
# Agregar a PATH: C:\Program Files\Tesseract-OCR
```

### macOS
```bash
# Homebrew
brew install tesseract

# Verificar idiomas disponibles
brew install tesseract-lang
```

### Linux (Ubuntu/Debian)
```bash
# Instalación básica
sudo apt update
sudo apt install tesseract-ocr

# Paquetes de idiomas (español)
sudo apt install tesseract-ocr-spa

# Verificar instalación
tesseract --version
```

### Python Dependencies
```bash
pip install pytesseract pillow
```

### Verificar Instalación
```python
import pytesseract
print(pytesseract.get_tesseract_version())
print(pytesseract.get_languages())
```

---

## Para Producción Web (Docker)

### Dockerfile Optimizado
```dockerfile
FROM python:3.11-slim

# Instalar Tesseract y dependencias del sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY . /app
WORKDIR /app

EXPOSE 8000
CMD ["python", "app.py"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  biblioperson:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TESSERACT_CMD=/usr/bin/tesseract
      - OCR_PROVIDER=tesseract
    volumes:
      - ./uploads:/app/uploads
      - ./output:/app/output
```

---

## Alternativas Cloud para Producción

### 1. Google Vision API
```python
# requirements.txt
google-cloud-vision==3.4.0

# Configuración
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
export OCR_PROVIDER=google_vision
```

### 2. AWS Textract
```python
# requirements.txt
boto3==1.26.0

# Configuración
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
export OCR_PROVIDER=aws_textract
```

### 3. Azure Cognitive Services
```python
# requirements.txt
azure-cognitiveservices-vision-computervision==0.9.0

# Configuración
export AZURE_VISION_KEY=your_key
export AZURE_VISION_ENDPOINT=your_endpoint
export OCR_PROVIDER=azure_vision
```

---

## Variables de Entorno

```bash
# Prioridad de OCR (orden de prueba)
OCR_PROVIDER=google_vision,tesseract,fallback

# Configuración Tesseract
TESSERACT_CMD=/usr/bin/tesseract
TESSERACT_LANG=spa+eng

# Configuración Cloud (según proveedor)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
AWS_ACCESS_KEY_ID=your_aws_key
AZURE_VISION_KEY=your_azure_key

# Fallback
ENABLE_OCR_FALLBACK=true
MAX_OCR_RETRIES=3
```

---

## Costos Aproximados (por 1000 páginas)

| Proveedor | Costo | Pros | Contras |
|-----------|-------|------|---------|
| **Tesseract** | **Gratis** | Sin límites, privacidad | Calidad variable |
| **Google Vision** | **$1.50** | Excelente calidad | Requiere internet |
| **AWS Textract** | **$1.50** | Integración AWS | Más complejo |
| **Azure Vision** | **$1.00** | Buen precio | Menos features |

---

## Estrategia Recomendada

### Para Desarrollo
1. **Instalar Tesseract localmente**
2. **Usar fallback mejorado** si no está disponible

### Para Producción Web
1. **Docker con Tesseract** para costos mínimos
2. **Google Vision API** para máxima calidad
3. **Fallback mejorado** como última opción

### Para Escala Enterprise
1. **Balanceador de carga OCR**: Tesseract local + Cloud API
2. **Cache inteligente** de resultados OCR
3. **Métricas y monitoreo** de calidad OCR 