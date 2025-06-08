# -*- coding: utf-8 -*-
"""
Estilos modernos para la aplicación Biblioperson
Sistema de temas con modo claro y oscuro
"""

# Paleta de colores para modo claro
LIGHT_COLORS = {
    # Colores primarios
    'primary_dark': '#1e293b',
    'primary_darker': '#0f172a', 
    'primary_medium': '#334155',
    'primary_light': '#475569',
    
    # Colores de acento
    'accent_blue': '#3b82f6',
    'accent_blue_hover': '#2563eb',
    'accent_green': '#10b981',
    'accent_red': '#ef4444',
    'accent_yellow': '#f59e0b',
    
    # Colores neutros
    'white': '#ffffff',
    'white_soft': '#f8fafc',
    'gray_light': '#e2e8f0',
    'gray_medium': '#94a3b8',
    'gray_dark': '#64748b',
    'gray_darker': '#475569',
    
    # Colores de fondo
    'bg_main': '#ffffff',
    'bg_panel': '#f8fafc',
    'bg_input': '#ffffff',
    'bg_hover': '#f1f5f9',
    'bg_selected': '#e0f2fe',
    
    # Bordes
    'border_light': '#e2e8f0',
    'border_medium': '#cbd5e1',
    'border_focus': '#3b82f6',
}

# Paleta de colores para modo oscuro
DARK_COLORS = {
    # Colores primarios
    'primary_dark': '#f1f5f9',
    'primary_darker': '#ffffff', 
    'primary_medium': '#cbd5e1',
    'primary_light': '#94a3b8',
    
    # Colores de acento
    'accent_blue': '#60a5fa',
    'accent_blue_hover': '#3b82f6',
    'accent_green': '#34d399',
    'accent_red': '#f87171',
    'accent_yellow': '#fbbf24',
    
    # Colores neutros
    'white': '#0f172a',
    'white_soft': '#1e293b',
    'gray_light': '#374151',
    'gray_medium': '#6b7280',
    'gray_dark': '#9ca3af',
    'gray_darker': '#d1d5db',
    
    # Colores de fondo
    'bg_main': '#0f172a',
    'bg_panel': '#1e293b',
    'bg_input': '#374151',
    'bg_hover': '#334155',
    'bg_selected': '#1e40af',
    
    # Bordes
    'border_light': '#374151',
    'border_medium': '#4b5563',
    'border_focus': '#60a5fa',
}

# Variable global para el tema actual
CURRENT_THEME = 'dark'
COLORS = DARK_COLORS.copy()

# Breakpoints para responsive design
BREAKPOINTS = {
    'mobile': 768,
    'tablet': 1024,
    'desktop': 1200
}

# Variable global para el tamaño de pantalla actual
CURRENT_SCREEN_SIZE = 'desktop'  # 'mobile', 'tablet', 'desktop'

def detect_screen_size(width):
    """Detecta el tamaño de pantalla basado en el ancho de la ventana."""
    global CURRENT_SCREEN_SIZE
    if width < BREAKPOINTS['mobile']:
        CURRENT_SCREEN_SIZE = 'mobile'
    elif width < BREAKPOINTS['tablet']:
        CURRENT_SCREEN_SIZE = 'tablet'
    else:
        CURRENT_SCREEN_SIZE = 'desktop'
    return CURRENT_SCREEN_SIZE

def get_responsive_value(mobile_val, tablet_val, desktop_val):
    """Retorna el valor apropiado según el tamaño de pantalla actual."""
    if CURRENT_SCREEN_SIZE == 'mobile':
        return mobile_val
    elif CURRENT_SCREEN_SIZE == 'tablet':
        return tablet_val
    else:
        return desktop_val

# Estilos para la aplicación principal con responsive design
def get_app_style():
    font_size = get_responsive_value('16px', '15px', '14px')
    return f"""
QMainWindow {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['primary_dark']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: {font_size};
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['primary_dark']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
}}

/* Responsive layout helpers */
QWidget[responsive="mobile"] {{
    max-width: 100%;
    margin: 8px;
}}

QWidget[responsive="tablet"] {{
    max-width: 90%;
    margin: 12px;
}}

QWidget[responsive="desktop"] {{
    margin: 16px;
}}
"""

APP_STYLE = get_app_style()

# Estilos para pestañas con responsive design
def get_tab_style():
    tab_padding = get_responsive_value('8px 12px', '10px 16px', '12px 20px')
    tab_min_width = get_responsive_value('80px', '100px', '120px')
    tab_font_size = get_responsive_value('13px', '14px', '14px')
    
    return f"""
QTabWidget::pane {{
    border: 1px solid {COLORS['border_light']};
    background-color: {COLORS['bg_panel']};
    border-radius: 8px;
    margin-top: 2px;
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background-color: {COLORS['gray_light']};
    color: {COLORS['gray_dark']};
    padding: {tab_padding};
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
    font-size: {tab_font_size};
    min-width: {tab_min_width};
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['primary_dark']};
    border-bottom: 2px solid {COLORS['accent_blue']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['primary_medium']};
}}

/* Mobile: Stack tabs vertically if needed */
QTabBar[orientation="vertical"] {{
    width: 100%;
}}

QTabBar[orientation="vertical"]::tab {{
    margin-bottom: 2px;
    margin-right: 0px;
    border-radius: 8px;
}}
"""

TAB_STYLE = get_tab_style()

# Estilos para grupos
GROUP_STYLE = f"""
QGroupBox {{
    font-weight: 600;
    font-size: 15px;
    color: {COLORS['primary_dark']};
    border: 2px solid {COLORS['border_light']};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 8px;
    background-color: {COLORS['bg_panel']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px 0 8px;
    color: {COLORS['primary_dark']};
    background-color: {COLORS['bg_panel']};
}}
"""

# Estilos para botones con responsive design
def get_button_style():
    button_padding = get_responsive_value('12px 20px', '11px 18px', '10px 16px')
    button_font_size = get_responsive_value('16px', '15px', '14px')
    button_min_height = get_responsive_value('44px', '32px', '20px')  # Touch-friendly en mobile
    
    process_padding = get_responsive_value('16px 24px', '15px 22px', '14px 20px')
    process_font_size = get_responsive_value('18px', '17px', '16px')
    process_min_height = get_responsive_value('48px', '35px', '25px')
    
    control_padding = get_responsive_value('10px 16px', '9px 14px', '8px 12px')
    control_font_size = get_responsive_value('15px', '14px', '13px')
    
    return f"""
QPushButton {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_blue']}, 
                                stop: 1 {COLORS['accent_blue_hover']});
    color: {COLORS['white']};
    border: none;
    border-radius: 8px;
    padding: {button_padding};
    font-weight: 600;
    font-size: {button_font_size};
    min-height: {button_min_height};
}}

QPushButton:hover {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_blue_hover']}, 
                                stop: 1 #1d4ed8);
}}

QPushButton:pressed {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #1d4ed8, 
                                stop: 1 #1e40af);
}}

QPushButton:disabled {{
    background-color: {COLORS['gray_medium']};
    color: {COLORS['gray_dark']};
}}

/* Botón de procesamiento especial */
QPushButton#process_btn {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_green']}, 
                                stop: 1 #059669);
    font-size: {process_font_size};
    font-weight: 700;
    padding: {process_padding};
    min-height: {process_min_height};
}}

QPushButton#process_btn:hover {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #059669, 
                                stop: 1 #047857);
}}

/* Botones de control */
QPushButton#control_btn {{
    background-color: {COLORS['gray_medium']};
    color: {COLORS['white']};
    padding: {control_padding};
    font-size: {control_font_size};
}}

QPushButton#control_btn:hover {{
    background-color: {COLORS['gray_dark']};
}}

/* Responsive button layouts */
QPushButton[layout="mobile"] {{
    width: 100%;
    margin-bottom: 8px;
}}

QPushButton[layout="tablet"] {{
    min-width: 120px;
    margin: 4px;
}}
"""

BUTTON_STYLE = get_button_style()

# Estilos para inputs con responsive design
def get_input_style():
    input_padding = get_responsive_value('14px 16px', '12px 14px', '10px 12px')
    input_font_size = get_responsive_value('16px', '15px', '14px')  # 16px en mobile previene zoom
    input_min_height = get_responsive_value('44px', '36px', '32px')
    
    textarea_padding = get_responsive_value('16px', '14px', '12px')
    textarea_font_size = get_responsive_value('15px', '14px', '13px')
    
    return f"""
QLineEdit {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: {input_padding};
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: {input_font_size};
    min-height: {input_min_height};
    selection-background-color: {COLORS['bg_selected']};
}}

QLineEdit:focus {{
    border-color: {COLORS['border_focus']};
    background-color: {COLORS['white']};
}}

QLineEdit:read-only {{
    background-color: {COLORS['gray_light']};
    color: {COLORS['gray_dark']};
}}

QTextEdit {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 8px;
    padding: {textarea_padding};
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: {textarea_font_size};
    line-height: 1.4;
}}

QTextEdit:focus {{
    border-color: {COLORS['border_focus']};
}}

/* Responsive input layouts */
QLineEdit[layout="mobile"] {{
    width: 100%;
    margin-bottom: 12px;
}}

QTextEdit[layout="mobile"] {{
    min-height: 120px;
}}

QTextEdit[layout="tablet"] {{
    min-height: 100px;
}}

QTextEdit[layout="desktop"] {{
    min-height: 80px;
}}
"""

INPUT_STYLE = get_input_style()

# Estilos para combobox
COMBOBOX_STYLE = f"""
QComboBox {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px 12px;
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: 14px;
    min-height: 20px;
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['gray_dark']};
    margin-right: 5px;
}}

QComboBox QAbstractItemView {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    background-color: {COLORS['bg_panel']};
    selection-background-color: {COLORS['bg_selected']};
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS['accent_blue']};
    color: {COLORS['white']};
}}
"""

# Estilos para checkboxes
CHECKBOX_STYLE = f"""
QCheckBox {{
    color: {COLORS['primary_dark']};
    font-size: 14px;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border_medium']};
    border-radius: 4px;
    background-color: {COLORS['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_green']};
    border-color: {COLORS['accent_green']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['accent_blue']};
}}
"""

# Estilos para spinbox
SPINBOX_STYLE = f"""
QSpinBox {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px 12px;
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: 14px;
    min-height: 20px;
}}

QSpinBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    border: none;
    background-color: {COLORS['gray_light']};
    width: 20px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {COLORS['gray_medium']};
}}

QSpinBox::up-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid {COLORS['gray_dark']};
}}

QSpinBox::down-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid {COLORS['gray_dark']};
}}
"""

# Estilos para progress bar
PROGRESS_STYLE = f"""
QProgressBar {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 8px;
    background-color: {COLORS['gray_light']};
    text-align: center;
    font-weight: 600;
    font-size: 13px;
    color: {COLORS['primary_dark']};
    height: 25px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_blue']}, 
                                stop: 1 {COLORS['accent_blue_hover']});
    border-radius: 6px;
    margin: 2px;
}}
"""

# Estilos para labels
LABEL_STYLE = f"""
QLabel {{
    color: {COLORS['primary_dark']};
    font-size: 14px;
}}

/* Título principal */
QLabel#title_label {{
    color: {COLORS['white']};
    font-size: 18px;
    font-weight: 700;
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 {COLORS['primary_dark']}, 
                                stop: 1 {COLORS['primary_medium']});
    padding: 16px;
    border-radius: 10px;
    margin: 8px 0;
}}

/* Labels de sección */
QLabel#section_label {{
    color: {COLORS['primary_dark']};
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 8px;
}}
"""

# Estilos para scroll areas
SCROLL_STYLE = f"""
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {COLORS['gray_light']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['gray_medium']};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['gray_dark']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['gray_light']};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['gray_medium']};
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['gray_dark']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""

# Estilos para frames
FRAME_STYLE = f"""
QFrame {{
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    background-color: {COLORS['bg_panel']};
    padding: 12px;
}}

QFrame#info_frame {{
    background-color: {COLORS['bg_selected']};
    border: 2px solid {COLORS['accent_blue']};
    border-radius: 8px;
    padding: 12px;
}}
"""

# Estilo completo combinado
COMPLETE_STYLE = (
    APP_STYLE + 
    TAB_STYLE + 
    GROUP_STYLE + 
    BUTTON_STYLE + 
    INPUT_STYLE + 
    COMBOBOX_STYLE + 
    CHECKBOX_STYLE + 
    SPINBOX_STYLE + 
    PROGRESS_STYLE + 
    LABEL_STYLE + 
    SCROLL_STYLE + 
    FRAME_STYLE
)

def get_modern_style():
    """Retorna el estilo completo moderno para la aplicación."""
    return COMPLETE_STYLE

def toggle_theme():
    """Alterna entre modo claro y oscuro."""
    global CURRENT_THEME, COLORS
    
    if CURRENT_THEME == 'light':
        CURRENT_THEME = 'dark'
        COLORS.clear()
        COLORS.update(DARK_COLORS)
    else:
        CURRENT_THEME = 'light'
        COLORS.clear()
        COLORS.update(LIGHT_COLORS)
    
    # Regenerar estilos con los nuevos colores
    _regenerate_styles()
    
    return CURRENT_THEME

def set_theme(theme_name):
    """Establece un tema específico ('light' o 'dark')."""
    global CURRENT_THEME, COLORS
    
    if theme_name == 'dark':
        CURRENT_THEME = 'dark'
        COLORS.clear()
        COLORS.update(DARK_COLORS)
    else:
        CURRENT_THEME = 'light'
        COLORS.clear()
        COLORS.update(LIGHT_COLORS)
    
    # Regenerar estilos con los nuevos colores
    _regenerate_styles()
    
    return CURRENT_THEME

def get_current_theme():
    """Retorna el tema actual."""
    return CURRENT_THEME

def _regenerate_styles():
    """Regenera todos los estilos con el tema actual y configuración responsive."""
    global APP_STYLE, TAB_STYLE, GROUP_STYLE, BUTTON_STYLE, INPUT_STYLE
    global COMBOBOX_STYLE, CHECKBOX_STYLE, SPINBOX_STYLE, PROGRESS_STYLE
    global LABEL_STYLE, SCROLL_STYLE, FRAME_STYLE, COMPLETE_STYLE
    
    # Regenerar cada estilo con los nuevos colores usando funciones responsive
    APP_STYLE = get_app_style()
    TAB_STYLE = get_tab_style()
    BUTTON_STYLE = get_button_style()
    INPUT_STYLE = get_input_style()
    
    GROUP_STYLE = f"""
QGroupBox {{
    font-weight: 600;
    font-size: 15px;
    color: {COLORS['primary_dark']};
    border: 2px solid {COLORS['border_light']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px 0 8px;
    color: {COLORS['primary_dark']};
    background-color: {COLORS['bg_panel']};
}}
"""
    
    BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_blue']}, 
                                stop: 1 {COLORS['accent_blue_hover']});
    color: {COLORS['white']};
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
    font-size: 14px;
    min-height: 20px;
}}

QPushButton:hover {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_blue_hover']}, 
                                stop: 1 #1d4ed8);
}}

QPushButton:pressed {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #1d4ed8, 
                                stop: 1 #1e40af);
}}

QPushButton:disabled {{
    background-color: {COLORS['gray_medium']};
    color: {COLORS['gray_dark']};
}}

/* Botón de procesamiento especial */
QPushButton#process_btn {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_green']}, 
                                stop: 1 #059669);
    font-size: 16px;
    font-weight: 700;
    padding: 14px 20px;
    min-height: 25px;
}}

QPushButton#process_btn:hover {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #059669, 
                                stop: 1 #047857);
}}

/* Botones de control */
QPushButton#control_btn {{
    background-color: {COLORS['gray_medium']};
    color: {COLORS['white']};
    padding: 8px 12px;
    font-size: 13px;
}}

QPushButton#control_btn:hover {{
    background-color: {COLORS['gray_dark']};
}}

/* Botón de cambio de tema */
QPushButton#theme_toggle_btn {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['primary_dark']};
    border: 2px solid {COLORS['border_medium']};
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    min-width: 80px;
}}

QPushButton#theme_toggle_btn:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['accent_blue']};
}}

QPushButton#theme_toggle_btn:pressed {{
    background-color: {COLORS['bg_selected']};
}}
"""
    
    INPUT_STYLE = f"""
QLineEdit {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 10px 12px;
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: 14px;
    selection-background-color: {COLORS['bg_selected']};
}}

QLineEdit:focus {{
    border-color: {COLORS['border_focus']};
    background-color: {COLORS['white']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['gray_light']};
    color: {COLORS['gray_dark']};
}}

QTextEdit {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px;
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: 14px;
    font-family: 'Consolas', 'Monaco', monospace;
}}

QTextEdit:focus {{
    border-color: {COLORS['border_focus']};
}}

QPlainTextEdit {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px;
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: 14px;
    font-family: 'Consolas', 'Monaco', monospace;
}}

QPlainTextEdit:focus {{
    border-color: {COLORS['border_focus']};
}}
"""
    
    COMBOBOX_STYLE = f"""
QComboBox {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px 12px;
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: 14px;
    min-width: 120px;
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    border-top: 5px solid {COLORS['gray_dark']};
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
}}

QComboBox QAbstractItemView {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    background-color: {COLORS['bg_panel']};
    selection-background-color: {COLORS['bg_selected']};
}}
"""
    
    CHECKBOX_STYLE = f"""
QCheckBox {{
    color: {COLORS['primary_dark']};
    font-size: 14px;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border_medium']};
    border-radius: 4px;
    background-color: {COLORS['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_green']};
    border-color: {COLORS['accent_green']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['accent_blue']};
}}

QCheckBox#warning_checkbox::indicator:checked {{
    background-color: {COLORS['accent_yellow']};
    border-color: {COLORS['accent_yellow']};
}}

QCheckBox#success_checkbox::indicator:checked {{
    background-color: {COLORS['accent_green']};
    border-color: {COLORS['accent_green']};
}}
"""
    
    SPINBOX_STYLE = f"""
QSpinBox {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px 12px;
    background-color: {COLORS['bg_input']};
    color: {COLORS['primary_dark']};
    font-size: 14px;
}}

QSpinBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {COLORS['gray_light']};
    border: none;
    width: 20px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {COLORS['gray_medium']};
}}

QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
    background-color: {COLORS['gray_dark']};
}}
"""
    
    PROGRESS_STYLE = f"""
QProgressBar {{
    border: 2px solid {COLORS['border_light']};
    border-radius: 8px;
    text-align: center;
    background-color: {COLORS['gray_light']};
    color: {COLORS['primary_dark']};
    font-weight: 600;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 {COLORS['accent_blue']}, 
                                stop: 1 {COLORS['accent_blue_hover']});
    border-radius: 6px;
    margin: 2px;
}}
"""
    
    LABEL_STYLE = f"""
QLabel {{
    color: {COLORS['primary_dark']};
    font-size: 14px;
}}

QLabel#title_label {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['primary_darker']};
    padding: 8px 0;
}}

QLabel#subtitle_label {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS['primary_medium']};
    padding: 4px 0;
}}

QLabel#info_label {{
    color: {COLORS['primary_dark']};
    background-color: {COLORS['bg_panel']};
    padding: 8px;
    border-radius: 4px;
}}
"""
    
    SCROLL_STYLE = f"""
QScrollBar:vertical {{
    background-color: {COLORS['gray_light']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['gray_medium']};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['gray_dark']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['gray_light']};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['gray_medium']};
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['gray_dark']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}
"""
    
    FRAME_STYLE = f"""
QFrame#info_frame {{
    background-color: {COLORS['bg_selected']};
    border: 2px solid {COLORS['accent_blue']};
    border-radius: 8px;
    padding: 12px;
}}
"""
    
    # Regenerar estilo completo
    global COMPLETE_STYLE
    COMPLETE_STYLE = (
        APP_STYLE + 
        TAB_STYLE + 
        GROUP_STYLE + 
        BUTTON_STYLE + 
        INPUT_STYLE + 
        COMBOBOX_STYLE + 
        CHECKBOX_STYLE + 
        SPINBOX_STYLE + 
        PROGRESS_STYLE + 
        LABEL_STYLE + 
        SCROLL_STYLE + 
        FRAME_STYLE
    )

def get_theme_toggle_style():
    """Retorna el estilo específico para el botón de cambio de tema."""
    return f"""
QPushButton#theme_toggle_btn {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['primary_dark']};
    border: 2px solid {COLORS['border_medium']};
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    min-width: 80px;
}}

QPushButton#theme_toggle_btn:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['accent_blue']};
}}

QPushButton#theme_toggle_btn:pressed {{
    background-color: {COLORS['bg_selected']};
}}
"""

def update_responsive_styles(screen_width):
    """Actualiza los estilos cuando cambia el tamaño de pantalla."""
    detect_screen_size(screen_width)
    _regenerate_styles()
    
def get_responsive_stylesheet():
    """Retorna la hoja de estilos completa con configuración responsive actual."""
    return COMPLETE_STYLE
    
def apply_responsive_theme(widget, theme='dark', screen_width=1200):
    """Aplica tema y configuración responsive a un widget."""
    toggle_theme(theme)
    update_responsive_styles(screen_width)
    if hasattr(widget, 'setStyleSheet'):
        widget.setStyleSheet(get_responsive_stylesheet())

# Regenerar estilos al importar el módulo para asegurar consistencia con el tema por defecto
_regenerate_styles()