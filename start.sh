#!/bin/bash

echo "========================================"
echo "    BIBLIOPERSON - INICIO AUTOMATICO"
echo "========================================"
echo
echo "Iniciando sistema completo..."
echo

# Verificar si Python está disponible
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python no está instalado o no está en el PATH"
    exit 1
fi

# Verificar si Node.js está disponible
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js no está instalado o no está en el PATH"
    exit 1
fi

echo "✓ Python y Node.js detectados"
echo

# Obtener el directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Iniciando Backend Flask (Puerto 5000)..."
# Usar python3 si está disponible, sino python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Iniciar backend en segundo plano
$PYTHON_CMD scripts/api_conexion.py &
BACKEND_PID=$!

echo "⏳ Esperando 5 segundos para que el backend se inicie..."
sleep 5

echo "🌐 Iniciando Frontend Electron (Puerto 3001)..."
cd app
npm run electron:dev &
FRONTEND_PID=$!

echo
echo "========================================"
echo "           SISTEMA INICIADO"
echo "========================================"
echo
echo "📱 Frontend: http://localhost:3001"
echo "🔧 Backend:  http://localhost:5000"
echo
echo "Para detener el sistema:"
echo "- Presiona Ctrl+C"
echo
echo "¡Listo para procesar archivos!"
echo

# Función para limpiar procesos al salir
cleanup() {
    echo
    echo "🛑 Deteniendo servicios..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Sistema detenido"
    exit 0
}

# Capturar señal de interrupción
trap cleanup SIGINT SIGTERM

# Esperar indefinidamente
while true; do
    sleep 1
done