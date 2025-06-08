# -*- coding: utf-8 -*-
"""
Ejemplo de implementación responsive para la aplicación Biblioperson
Muestra cómo usar el sistema responsive en la interfaz principal
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QTabWidget, QGroupBox,
    QLabel, QComboBox, QCheckBox, QProgressBar
)
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QResizeEvent

from . import styles
from .responsive_utils import responsive_manager, setup_responsive_widget

class ResponsiveMainWindow(QMainWindow):
    """Ventana principal con soporte responsive."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biblioperson - Procesador de Datasets Literarios")
        self.setMinimumSize(320, 480)  # Tamaño mínimo para mobile
        
        # Configurar widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Configurar responsive manager
        responsive_manager.screen_size_changed.connect(self.on_screen_size_changed)
        
        # Crear interfaz
        self.setup_ui()
        
        # Aplicar estilos iniciales
        self.apply_responsive_styles()
        
    def setup_ui(self):
        """Configura la interfaz de usuario con layout responsive."""
        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Header con botón de tema
        self.setup_header()
        
        # Contenido principal con tabs
        self.setup_main_content()
        
        # Footer con controles
        self.setup_footer()
        
    def setup_header(self):
        """Configura el header responsive."""
        header_layout = QHBoxLayout()
        
        # Título
        title_label = QLabel("Procesador de Datasets")
        title_label.setObjectName("title_label")
        setup_responsive_widget(title_label, 'label')
        
        # Botón de tema
        theme_btn = QPushButton("🌙 Tema")
        theme_btn.setObjectName("theme_toggle_btn")
        theme_btn.clicked.connect(self.toggle_theme)
        setup_responsive_widget(theme_btn, 'button')
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(theme_btn)
        
        self.main_layout.addLayout(header_layout)
        
    def setup_main_content(self):
        """Configura el contenido principal con tabs responsive."""
        self.tab_widget = QTabWidget()
        setup_responsive_widget(self.tab_widget, 'tab')
        
        # Tab 1: Configuración
        config_tab = self.create_config_tab()
        self.tab_widget.addTab(config_tab, "Configuración")
        
        # Tab 2: Procesamiento
        process_tab = self.create_process_tab()
        self.tab_widget.addTab(process_tab, "Procesamiento")
        
        # Tab 3: Resultados
        results_tab = self.create_results_tab()
        self.tab_widget.addTab(results_tab, "Resultados")
        
        self.main_layout.addWidget(self.tab_widget)
        
    def create_config_tab(self):
        """Crea la pestaña de configuración responsive."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de archivos
        files_group = QGroupBox("Archivos de Entrada")
        files_layout = QVBoxLayout(files_group)
        
        # Input de archivo
        file_input = QLineEdit()
        file_input.setPlaceholderText("Seleccionar archivo...")
        setup_responsive_widget(file_input, 'input')
        
        # Botón de selección
        select_btn = QPushButton("Examinar")
        setup_responsive_widget(select_btn, 'button')
        
        files_layout.addWidget(file_input)
        files_layout.addWidget(select_btn)
        
        # Grupo de opciones
        options_group = QGroupBox("Opciones de Procesamiento")
        options_layout = QVBoxLayout(options_group)
        
        # Combobox de perfil
        profile_combo = QComboBox()
        profile_combo.addItems(["Perfil 1", "Perfil 2", "Perfil 3"])
        setup_responsive_widget(profile_combo, 'input')
        
        # Checkbox de opciones
        option1_check = QCheckBox("Detectar autores")
        option2_check = QCheckBox("Procesar semántica")
        setup_responsive_widget(option1_check, 'checkbox')
        setup_responsive_widget(option2_check, 'checkbox')
        
        options_layout.addWidget(QLabel("Perfil:"))
        options_layout.addWidget(profile_combo)
        options_layout.addWidget(option1_check)
        options_layout.addWidget(option2_check)
        
        layout.addWidget(files_group)
        layout.addWidget(options_group)
        layout.addStretch()
        
        return tab
        
    def create_process_tab(self):
        """Crea la pestaña de procesamiento responsive."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Botón de procesamiento principal
        process_btn = QPushButton("🚀 Iniciar Procesamiento")
        process_btn.setObjectName("process_btn")
        setup_responsive_widget(process_btn, 'button')
        
        # Barra de progreso
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        setup_responsive_widget(progress_bar, 'progress')
        
        # Área de logs
        log_area = QTextEdit()
        log_area.setPlaceholderText("Los logs de procesamiento aparecerán aquí...")
        log_area.setReadOnly(True)
        setup_responsive_widget(log_area, 'input')
        
        # Botones de control
        controls_layout = QHBoxLayout()
        
        pause_btn = QPushButton("⏸️ Pausar")
        pause_btn.setObjectName("control_btn")
        setup_responsive_widget(pause_btn, 'button')
        
        stop_btn = QPushButton("⏹️ Detener")
        stop_btn.setObjectName("control_btn")
        setup_responsive_widget(stop_btn, 'button')
        
        controls_layout.addWidget(pause_btn)
        controls_layout.addWidget(stop_btn)
        controls_layout.addStretch()
        
        layout.addWidget(process_btn)
        layout.addWidget(progress_bar)
        layout.addWidget(QLabel("Logs de Procesamiento:"))
        layout.addWidget(log_area)
        layout.addLayout(controls_layout)
        
        return tab
        
    def create_results_tab(self):
        """Crea la pestaña de resultados responsive."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Área de resultados
        results_area = QTextEdit()
        results_area.setPlaceholderText("Los resultados del procesamiento aparecerán aquí...")
        results_area.setReadOnly(True)
        setup_responsive_widget(results_area, 'input')
        
        # Botones de exportación
        export_layout = QHBoxLayout()
        
        export_json_btn = QPushButton("📄 Exportar JSON")
        setup_responsive_widget(export_json_btn, 'button')
        
        export_csv_btn = QPushButton("📊 Exportar CSV")
        setup_responsive_widget(export_csv_btn, 'button')
        
        export_layout.addWidget(export_json_btn)
        export_layout.addWidget(export_csv_btn)
        export_layout.addStretch()
        
        layout.addWidget(QLabel("Resultados del Procesamiento:"))
        layout.addWidget(results_area)
        layout.addLayout(export_layout)
        
        return tab
        
    def setup_footer(self):
        """Configura el footer responsive."""
        footer_layout = QHBoxLayout()
        
        # Información de estado
        status_label = QLabel("Listo")
        status_label.setObjectName("status_label")
        setup_responsive_widget(status_label, 'label')
        
        # Información de pantalla (para debug)
        screen_info = QLabel(f"Pantalla: {styles.CURRENT_SCREEN_SIZE}")
        screen_info.setObjectName("screen_info")
        setup_responsive_widget(screen_info, 'label')
        
        footer_layout.addWidget(status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(screen_info)
        
        self.main_layout.addLayout(footer_layout)
        
        # Guardar referencia para actualizar
        self.screen_info_label = screen_info
        
    def apply_responsive_styles(self):
        """Aplica los estilos responsive a toda la aplicación."""
        # Detectar tamaño actual
        current_size = self.size()
        styles.detect_screen_size(current_size.width())
        
        # Aplicar hoja de estilos
        self.setStyleSheet(styles.get_responsive_stylesheet())
        
        # Configurar layout según tamaño de pantalla
        self.adjust_layout_for_screen_size()
        
    def adjust_layout_for_screen_size(self):
        """Ajusta el layout según el tamaño de pantalla actual."""
        if styles.CURRENT_SCREEN_SIZE == 'mobile':
            # En mobile, usar layout vertical y ocultar algunos elementos
            self.main_layout.setSpacing(8)
            self.main_layout.setContentsMargins(8, 8, 8, 8)
            
        elif styles.CURRENT_SCREEN_SIZE == 'tablet':
            # En tablet, usar espaciado medio
            self.main_layout.setSpacing(12)
            self.main_layout.setContentsMargins(12, 12, 12, 12)
            
        else:
            # En desktop, usar espaciado completo
            self.main_layout.setSpacing(16)
            self.main_layout.setContentsMargins(16, 16, 16, 16)
            
    def on_screen_size_changed(self, new_size):
        """Maneja cambios en el tamaño de pantalla."""
        print(f"Tamaño de pantalla cambió a: {new_size}")
        
        # Actualizar estilos
        self.apply_responsive_styles()
        
        # Actualizar información de pantalla
        if hasattr(self, 'screen_info_label'):
            self.screen_info_label.setText(f"Pantalla: {new_size}")
            
    def toggle_theme(self):
        """Alterna entre tema claro y oscuro."""
        current_theme = styles.get_current_theme()
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        
        styles.toggle_theme(new_theme)
        self.apply_responsive_styles()
        
        # Actualizar texto del botón
        theme_btn = self.findChild(QPushButton, "theme_toggle_btn")
        if theme_btn:
            icon = "☀️" if new_theme == 'light' else "🌙"
            theme_btn.setText(f"{icon} Tema")
            
    def resizeEvent(self, event: QResizeEvent):
        """Maneja eventos de redimensionamiento de ventana."""
        super().resizeEvent(event)
        
        # Actualizar tamaño de pantalla
        new_width = event.size().width()
        old_size = styles.CURRENT_SCREEN_SIZE
        new_size = styles.detect_screen_size(new_width)
        
        # Si cambió el tamaño, actualizar estilos
        if old_size != new_size:
            QTimer.singleShot(100, self.apply_responsive_styles)

def main():
    """Función principal para probar la interfaz responsive."""
    app = QApplication(sys.argv)
    
    # Crear ventana principal
    window = ResponsiveMainWindow()
    window.show()
    
    # Configurar responsive manager
    responsive_manager.setup_responsive_layout(window)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()