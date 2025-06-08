# -*- coding: utf-8 -*-
"""
Utilidades para manejo responsive en la aplicación Biblioperson
Funciones para detectar tamaño de pantalla y aplicar estilos adaptativos
"""

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from . import styles

class ResponsiveManager(QObject):
    """Gestor de responsive design para la aplicación."""
    
    screen_size_changed = pyqtSignal(str)  # Emite cuando cambia el tamaño de pantalla
    
    def __init__(self):
        super().__init__()
        self.current_size = 'desktop'
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_screen_size)
        self.timer.start(500)  # Verificar cada 500ms
        
    def check_screen_size(self):
        """Verifica el tamaño actual de la pantalla y actualiza estilos si es necesario."""
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                size = screen.size()
                width = size.width()
                
                new_size = styles.detect_screen_size(width)
                
                if new_size != self.current_size:
                    self.current_size = new_size
                    self.screen_size_changed.emit(new_size)
                    self.update_styles()
                    
    def update_styles(self):
        """Actualiza todos los estilos cuando cambia el tamaño de pantalla."""
        styles._regenerate_styles()
        
    def apply_responsive_properties(self, widget, widget_type='default'):
        """Aplica propiedades responsive a un widget específico."""
        if not isinstance(widget, QWidget):
            return
            
        # Aplicar propiedades según el tamaño de pantalla
        if styles.CURRENT_SCREEN_SIZE == 'mobile':
            widget.setProperty('responsive', 'mobile')
            if widget_type == 'button':
                widget.setProperty('layout', 'mobile')
            elif widget_type == 'input':
                widget.setProperty('layout', 'mobile')
        elif styles.CURRENT_SCREEN_SIZE == 'tablet':
            widget.setProperty('responsive', 'tablet')
            if widget_type == 'button':
                widget.setProperty('layout', 'tablet')
            elif widget_type == 'input':
                widget.setProperty('layout', 'tablet')
        else:
            widget.setProperty('responsive', 'desktop')
            if widget_type == 'button':
                widget.setProperty('layout', 'desktop')
            elif widget_type == 'input':
                widget.setProperty('layout', 'desktop')
                
        # Forzar actualización del estilo
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        
    def setup_responsive_layout(self, main_widget):
        """Configura el layout responsive para el widget principal."""
        if not isinstance(main_widget, QWidget):
            return
            
        # Aplicar configuración responsive inicial
        self.apply_responsive_properties(main_widget)
        
        # Conectar señal para actualizaciones futuras
        self.screen_size_changed.connect(
            lambda size: self.apply_responsive_properties(main_widget)
        )
        
    def get_responsive_spacing(self):
        """Retorna el espaciado apropiado según el tamaño de pantalla."""
        return styles.get_responsive_value(8, 12, 16)
        
    def get_responsive_margin(self):
        """Retorna el margen apropiado según el tamaño de pantalla."""
        return styles.get_responsive_value(8, 12, 16)
        
    def get_responsive_font_size(self, base_size=14):
        """Retorna el tamaño de fuente apropiado según el tamaño de pantalla."""
        mobile_size = base_size + 2
        tablet_size = base_size + 1
        return styles.get_responsive_value(mobile_size, tablet_size, base_size)

# Instancia global del gestor responsive
responsive_manager = ResponsiveManager()

def setup_responsive_widget(widget, widget_type='default'):
    """Función de conveniencia para configurar un widget como responsive."""
    responsive_manager.apply_responsive_properties(widget, widget_type)
    
def get_current_screen_size():
    """Retorna el tamaño de pantalla actual."""
    return styles.CURRENT_SCREEN_SIZE
    
def is_mobile():
    """Retorna True si estamos en modo mobile."""
    return styles.CURRENT_SCREEN_SIZE == 'mobile'
    
def is_tablet():
    """Retorna True si estamos en modo tablet."""
    return styles.CURRENT_SCREEN_SIZE == 'tablet'
    
def is_desktop():
    """Retorna True si estamos en modo desktop."""
    return styles.CURRENT_SCREEN_SIZE == 'desktop'