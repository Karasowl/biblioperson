# ============================================
# Biblioperson Dataset Processor - Dockerfile
# Aplicación web con OCR inteligente
# ============================================

FROM python:3.11-slim

# Configurar variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema y Tesseract OCR
RUN apt-get update && apt-get install -y \
    # Tesseract OCR y paquetes de idiomas
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libtesseract-dev \
    # Dependencias para procesamiento de imágenes
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    # Dependencias para PyMuPDF
    libfontconfig1-dev \
    libglib2.0-0 \
    # Utilidades del sistema
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Verificar instalación de Tesseract
RUN tesseract --version && tesseract --list-langs

# Configurar directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .
COPY package.json .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Instalar dependencias adicionales para OCR cloud (opcional)
RUN pip install \
    google-cloud-vision==3.4.0 \
    boto3==1.26.0 \
    azure-cognitiveservices-vision-computervision==0.9.0 \
    --no-deps || echo "OCR cloud dependencies opcional"

# Copiar código de la aplicación
COPY dataset/ ./dataset/
COPY frontend/ ./frontend/
COPY backend/ ./backend/
COPY launch_gui.py .
COPY *.md ./

# Crear directorios necesarios
RUN mkdir -p uploads output logs temp

# Configurar variables de entorno para la aplicación
ENV TESSERACT_CMD=/usr/bin/tesseract \
    TESSERACT_LANG=spa+eng \
    OCR_PROVIDER=tesseract,google_vision,aws_textract,azure_vision \
    MAX_OCR_RETRIES=3 \
    ENABLE_OCR_FALLBACK=true \
    PYTHONPATH=/app

# Crear usuario no-root para seguridad
RUN groupadd -r biblioperson && useradd -r -g biblioperson biblioperson
RUN chown -R biblioperson:biblioperson /app
USER biblioperson

# Exponer puerto
EXPOSE 8000

# Punto de entrada con healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto (se puede sobrescribir)
CMD ["python", "launch_gui.py"] 