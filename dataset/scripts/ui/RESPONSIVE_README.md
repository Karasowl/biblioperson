# Sistema Responsive para Biblioperson

Este documento explica cómo usar el sistema responsive implementado en la aplicación Biblioperson para que funcione correctamente en dispositivos móviles, tablets y navegadores de escritorio.

## Características Implementadas

### 🎯 Breakpoints Responsive

- **Mobile**: < 768px de ancho
- **Tablet**: 768px - 1024px de ancho  
- **Desktop**: > 1024px de ancho

### 📱 Adaptaciones por Dispositivo

#### Mobile (< 768px)
- Fuentes más grandes (16px base) para evitar zoom automático
- Botones con altura mínima de 44px (touch-friendly)
- Inputs con altura mínima de 44px
- Padding y márgenes aumentados
- Layout en columna única
- Botones ocupan 100% del ancho disponible

#### Tablet (768px - 1024px)
- Fuentes intermedias (15px base)
- Botones con altura mínima de 32px
- Espaciado medio
- Layout adaptativo
- Elementos se reorganizan en 2 columnas cuando es posible

#### Desktop (> 1024px)
- Fuentes estándar (14px base)
- Espaciado completo
- Layout horizontal optimizado
- Todos los elementos visibles simultáneamente

## 🚀 Cómo Usar el Sistema Responsive

### 1. Importar los Módulos

```python
from dataset.scripts.ui import styles
from dataset.scripts.ui.responsive_utils import (
    responsive_manager, 
    setup_responsive_widget,
    is_mobile, 
    is_tablet, 
    is_desktop
)
```

### 2. Configurar la Ventana Principal

```python
class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configurar tamaño mínimo para mobile
        self.setMinimumSize(320, 480)
        
        # Conectar señal de cambio de tamaño
        responsive_manager.screen_size_changed.connect(self.on_screen_size_changed)
        
        # Aplicar estilos responsive
        self.apply_responsive_styles()
        
    def apply_responsive_styles(self):
        # Detectar tamaño actual
        current_size = self.size()
        styles.detect_screen_size(current_size.width())
        
        # Aplicar hoja de estilos
        self.setStyleSheet(styles.get_responsive_stylesheet())
```

### 3. Configurar Widgets Individuales

```python
# Para botones
button = QPushButton("Mi Botón")
setup_responsive_widget(button, 'button')

# Para inputs
input_field = QLineEdit()
setup_responsive_widget(input_field, 'input')

# Para áreas de texto
text_area = QTextEdit()
setup_responsive_widget(text_area, 'input')
```

### 4. Layouts Adaptativos

```python
def create_adaptive_layout(self):
    if is_mobile():
        # Layout vertical para mobile
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
    elif is_tablet():
        # Layout mixto para tablet
        layout = QGridLayout()
        layout.setSpacing(12)
    else:
        # Layout horizontal para desktop
        layout = QHBoxLayout()
        layout.setSpacing(16)
    
    return layout
```

### 5. Manejo de Cambios de Tamaño

```python
def resizeEvent(self, event):
    super().resizeEvent(event)
    
    # Actualizar tamaño de pantalla
    new_width = event.size().width()
    old_size = styles.CURRENT_SCREEN_SIZE
    new_size = styles.detect_screen_size(new_width)
    
    # Si cambió el tamaño, actualizar estilos
    if old_size != new_size:
        QTimer.singleShot(100, self.apply_responsive_styles)
```

## 🎨 Personalización de Estilos

### Valores Responsive Personalizados

```python
# Usar valores diferentes según el tamaño de pantalla
font_size = styles.get_responsive_value(
    mobile_val='18px',   # Mobile
    tablet_val='16px',   # Tablet  
    desktop_val='14px'   # Desktop
)

padding = styles.get_responsive_value('16px', '12px', '8px')
margin = styles.get_responsive_value('12px', '10px', '8px')
```

### Propiedades CSS Responsive

```python
# En los estilos CSS, usar propiedades responsive
style = f"""
QWidget[responsive="mobile"] {{
    max-width: 100%;
    margin: 8px;
}}

QWidget[responsive="tablet"] {{
    max-width: 90%;
    margin: 12px;
}}

QPushButton[layout="mobile"] {{
    width: 100%;
    margin-bottom: 8px;
}}
"""
```

## 📋 Ejemplo Completo

Ver el archivo `responsive_example.py` para un ejemplo completo de implementación que incluye:

- Ventana principal responsive
- Tabs adaptativos
- Formularios que se reorganizan según el tamaño
- Botones touch-friendly en mobile
- Manejo automático de cambios de tamaño

## 🔧 Funciones Utilitarias

### Detección de Tamaño

```python
# Verificar tamaño actual
if is_mobile():
    print("Estamos en mobile")
elif is_tablet():
    print("Estamos en tablet")
else:
    print("Estamos en desktop")

# Obtener tamaño actual
current_size = get_current_screen_size()  # 'mobile', 'tablet', 'desktop'
```

### Aplicación Manual de Estilos

```python
# Actualizar estilos cuando cambia el tamaño
styles.update_responsive_styles(new_width)

# Aplicar tema y responsive juntos
styles.apply_responsive_theme(widget, theme='dark', screen_width=800)
```

## 🎯 Mejores Prácticas

### 1. Tamaños Touch-Friendly
- Botones mínimo 44px de altura en mobile
- Inputs mínimo 44px de altura en mobile
- Espaciado suficiente entre elementos clickeables

### 2. Tipografía Responsive
- Usar 16px como mínimo en mobile para evitar zoom
- Escalar fuentes proporcionalmente
- Mantener legibilidad en todos los tamaños

### 3. Layout Adaptativo
- Priorizar contenido importante en mobile
- Usar layouts verticales en pantallas pequeñas
- Aprovechar espacio horizontal en desktop

### 4. Performance
- El sistema verifica cambios cada 500ms
- Los estilos se regeneran solo cuando es necesario
- Usar QTimer.singleShot para evitar actualizaciones excesivas

## 🐛 Solución de Problemas

### Estilos No Se Aplican
```python
# Forzar actualización de estilos
widget.style().unpolish(widget)
widget.style().polish(widget)
widget.update()
```

### Detección de Tamaño Incorrecta
```python
# Verificar detección manual
width = self.width()
detected_size = styles.detect_screen_size(width)
print(f"Ancho: {width}px, Detectado: {detected_size}")
```

### Layout No Se Reorganiza
```python
# Forzar reorganización del layout
layout.invalidate()
layout.activate()
self.adjustSize()
```

## 📱 Pruebas en Diferentes Tamaños

Para probar la responsividad:

1. Ejecutar `responsive_example.py`
2. Redimensionar la ventana manualmente
3. Observar cómo cambian los estilos y layouts
4. Verificar que los elementos se reorganizan correctamente

El sistema detectará automáticamente los cambios y aplicará los estilos apropiados para cada tamaño de pantalla.