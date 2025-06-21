@echo off
echo ========================================
echo    BIBLIOPERSON - INICIO AUTOMATICO
echo ========================================
echo.
echo Iniciando sistema completo...
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Verificar si Node.js está disponible
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no está instalado o no está en el PATH
    pause
    exit /b 1
)

echo ✓ Python y Node.js detectados
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

echo 🚀 Iniciando Backend Flask (Puerto 5000)...
start "Backend Flask" cmd /k "python scripts/api_conexion.py"

echo ⏳ Esperando 5 segundos para que el backend se inicie...
timeout /t 5 /nobreak >nul

echo 🌐 Iniciando Frontend Electron (Puerto 3001)...
cd app
start "Frontend Electron" cmd /k "npm run electron:dev"

echo.
echo ========================================
echo           SISTEMA INICIADO
echo ========================================
echo.
echo 📱 Frontend: http://localhost:3001
echo 🔧 Backend:  http://localhost:5000
echo.
echo Para detener el sistema:
echo - Cierra las ventanas de terminal que se abrieron
echo - O presiona Ctrl+C en cada una
echo.
echo ¡Listo para procesar archivos!
echo.
pause