# Interfaz Gráfica de Biblioperson

Este directorio contiene la interfaz gráfica de usuario (GUI) para el procesador de datasets de Biblioperson, desarrollada con PySide6 (Qt for Python).

## Archivos

- `main_window.py`: Ventana principal de la aplicación
- `__init__.py`: Archivo de inicialización del paquete
- `README.md`: Este archivo de documentación

## Características Implementadas

### Ventana Principal
- **Título**: "Biblioperson - Procesador de Datasets"
- **Tamaño**: 1200x800 píxeles (redimensionable, mínimo 900x700)
- **Layout**: Diseño con splitter horizontal dividido en panel de configuración y panel de logs

### Panel de Configuración (Izquierda)
- **Selección de Entrada**: Botones para seleccionar archivo individual o carpeta completa
- **Perfiles de Procesamiento**: ComboBox con perfiles predefinidos:
  - `poem_or_lyrics`
  - `book_structure` 
  - `general_text`
- **Opciones Avanzadas**:
  - Checkbox para modo detallado (verbose)
  - Checkbox para forzar tipo de contenido
  - ComboBox para tipo de contenido (habilitado solo si se fuerza)
  - Campo de encoding (por defecto: utf-8)
- **Selección de Salida**: Campo opcional para especificar archivo o carpeta de salida (se adapta automáticamente al tipo de entrada)
- **Botón de Procesamiento**: Botón principal estilizado para iniciar el procesamiento

### Panel de Logs (Derecha)
- **Área de Logs**: TextEdit de solo lectura con estilo de terminal
- **Indicador de Estado**: Muestra el estado actual de la aplicación
- **Botón Limpiar Logs**: Para limpiar el área de mensajes

### Funcionalidades
- **Validación de Entrada**: El botón de procesamiento solo se habilita cuando hay archivo/carpeta y perfil seleccionados
- **Diálogos de Archivo**: Filtros apropiados para tipos de archivo soportados
- **Salida Inteligente**: El diálogo de salida se adapta automáticamente (archivo si entrada es archivo, carpeta si entrada es carpeta)
- **Placeholders Dinámicos**: Los textos de ayuda cambian según el contexto
- **Confirmación de Salida**: Diálogo de confirmación al cerrar la aplicación
- **Auto-scroll**: Los logs se desplazan automáticamente al final

## Instalación y Ejecución

### Requisitos
```bash
pip install PySide6==6.6.0
```

### Ejecución

#### Opción 1: Desde la raíz del proyecto
```bash
python launch_gui.py
```

#### Opción 2: Directamente
```bash
python dataset/scripts/ui/main_window.py
```

#### Opción 3: Como módulo
```python
from dataset.scripts.ui import BibliopersonMainWindow
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = BibliopersonMainWindow()
window.show()
sys.exit(app.exec())
```

## Estado Actual

Esta es la **versión completamente funcional** de la interfaz. Las características implementadas incluyen:

✅ **Completado:**
- Estructura visual completa
- Todos los widgets y controles
- Validación básica de entrada
- Navegación de archivos y carpetas
- Logs y mensajes de estado con timestamps
- Estilo visual moderno
- **Integración completa con `ProfileManager`**
- **Ejecución real del procesamiento de documentos**
- **Barra de progreso para operaciones largas**
- **Manejo de errores específicos**
- **Carga dinámica de perfiles desde archivos YAML**
- **Threading para no bloquear la interfaz**
- **Procesamiento tanto de archivos individuales como directorios**
- **Estadísticas detalladas de procesamiento**

🚧 **Pendiente (para futuras iteraciones):**
- Configuración persistente de preferencias de usuario
- Cancelación manual de procesamiento en curso
- Vista previa de resultados en la interfaz
- Exportación de logs a archivo

## Arquitectura

La aplicación sigue el patrón Model-View-Controller con threading:

- **Vista**: `BibliopersonMainWindow` - Interfaz gráfica
- **Controlador**: Métodos de la clase principal para manejar eventos
- **Modelo**: `ProfileManager` y `core_process` completamente integrados
- **Worker**: `ProcessingWorker` - Ejecuta procesamiento en hilo separado

### Señales Qt Implementadas
- `processing_started`: Se emite al iniciar procesamiento
- `processing_finished(bool)`: Se emite al terminar (True=éxito, False=error)
- `progress_update(str)`: Actualizaciones de progreso del worker
- `ProcessingWorker.processing_finished(bool, str)`: Finalización con resultado y mensaje

### Threading
- El procesamiento se ejecuta en un `QThread` separado para mantener la UI responsiva
- `ProcessingWorker` maneja tanto archivos individuales como directorios completos
- Progreso en tiempo real con timestamps
- Manejo seguro de cancelación al cerrar la aplicación

## Próximos Pasos

1. **Configuración Persistente**: Guardar preferencias del usuario (último perfil usado, rutas, etc.)
2. **Cancelación de Procesamiento**: Permitir cancelar operaciones en curso
3. **Vista Previa de Resultados**: Mostrar algunos resultados directamente en la interfaz
4. **Exportación de Logs**: Guardar logs de sesión en archivos
5. **Validación Avanzada**: Verificar que los archivos sean compatibles con los perfiles
6. **Configuración de Perfiles**: Interfaz para editar perfiles existentes 