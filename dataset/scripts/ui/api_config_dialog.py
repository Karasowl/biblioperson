#!/usr/bin/env python3
"""
Diálogo de configuración de API keys para el generador de perfiles IA.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QMessageBox, QFrame, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon

from .config_manager import ConfigManager


class APIConfigDialog(QDialog):
    """Diálogo para configurar las API keys de los proveedores de IA."""
    
    # Señal emitida cuando se guardan las configuraciones
    config_saved = Signal(dict)  # {provider: bool} - estado de cada proveedor
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        # Cargar configuración actual
        self.current_keys = config_manager.load_api_keys()
        
        self._setup_ui()
        self._load_current_config()
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Configuración de API Keys")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("Configuración de Claves API")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel(
            "Configura las claves API para los proveedores de IA. "
            "Las claves se guardarán de forma segura y no necesitarás ingresarlas nuevamente."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # === OpenAI ===
        openai_group = self._create_provider_group(
            "OpenAI", 
            "Modelos: GPT-4, GPT-3.5-turbo, etc.",
            "https://platform.openai.com/api-keys"
        )
        self.openai_key_edit = openai_group.findChild(QLineEdit)
        layout.addWidget(openai_group)
        
        # === Google Gemini ===
        google_group = self._create_provider_group(
            "Google Gemini",
            "Modelos: Gemini Pro, Gemini Flash, etc.", 
            "https://makersuite.google.com/app/apikey"
        )
        self.google_key_edit = google_group.findChild(QLineEdit)
        layout.addWidget(google_group)
        
        # === Anthropic ===
        anthropic_group = self._create_provider_group(
            "Anthropic",
            "Modelos: Claude 3.5 Sonnet, Claude 3 Haiku, etc.",
            "https://console.anthropic.com/account/keys"
        )
        self.anthropic_key_edit = anthropic_group.findChild(QLineEdit)
        layout.addWidget(anthropic_group)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator)
        
        # Información de seguridad
        security_label = QLabel(
            "🔒 Las claves se almacenan localmente con codificación base64 y no se comparten. "
            "Los archivos de configuración están excluidos del control de versiones."
        )
        security_label.setWordWrap(True)
        security_label.setStyleSheet(
            "background-color: #ecf0f1; padding: 10px; border-radius: 5px; "
            "color: #2c3e50; font-size: 11px;"
        )
        layout.addWidget(security_label)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🧪 Probar Conexiones")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        self.save_btn = QPushButton("💾 Guardar")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        buttons_layout.addWidget(self.test_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
        
        # Conectar señales
        self.test_btn.clicked.connect(self._test_connections)
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save_config)
    
    def _create_provider_group(self, name: str, description: str, url: str) -> QGroupBox:
        """Crea un grupo de configuración para un proveedor."""
        group = QGroupBox(name)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Descripción del proveedor
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #7f8c8d; font-weight: normal; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Campo de API key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        
        key_edit = QLineEdit()
        key_edit.setEchoMode(QLineEdit.Password)
        key_edit.setPlaceholderText("Ingresa tu clave API...")
        key_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-family: monospace;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        key_layout.addWidget(key_edit)
        
        # Botón para mostrar/ocultar
        toggle_btn = QPushButton("👁")
        toggle_btn.setFixedSize(30, 30)
        toggle_btn.setCheckable(True)
        toggle_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ecf0f1;
            }
            QPushButton:checked {
                background-color: #3498db;
                color: white;
            }
        """)
        toggle_btn.toggled.connect(
            lambda checked: key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        )
        key_layout.addWidget(toggle_btn)
        
        layout.addLayout(key_layout)
        
        # Link para obtener API key
        link_label = QLabel(f'<a href="{url}" style="color: #3498db;">Obtener API Key</a>')
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet("font-size: 11px; font-weight: normal;")
        layout.addWidget(link_label)
        
        return group
    
    def _load_current_config(self):
        """Carga la configuración actual en los campos."""
        self.openai_key_edit.setText(self.current_keys.get('openai', ''))
        self.google_key_edit.setText(self.current_keys.get('google', ''))
        self.anthropic_key_edit.setText(self.current_keys.get('anthropic', ''))
    
    def _test_connections(self):
        """Prueba las conexiones con las APIs."""
        # Obtener claves actuales de los campos
        keys = {
            'openai': self.openai_key_edit.text().strip(),
            'google': self.google_key_edit.text().strip(),
            'anthropic': self.anthropic_key_edit.text().strip()
        }
        
        # Probar cada clave que no esté vacía
        results = {}
        
        for provider, key in keys.items():
            if not key:
                results[provider] = "No configurada"
                continue
            
            if len(key) < 10:
                results[provider] = "❌ Clave muy corta"
                continue
            
            # Aquí podrías agregar pruebas reales de conexión
            # Por ahora, solo validamos el formato básico
            if provider == 'openai' and key.startswith('sk-'):
                results[provider] = "✅ Formato válido"
            elif provider == 'google' and len(key) >= 20:
                results[provider] = "✅ Formato válido"
            elif provider == 'anthropic' and key.startswith('sk-ant-'):
                results[provider] = "✅ Formato válido"
            else:
                results[provider] = "⚠️ Formato inusual"
        
        # Mostrar resultados
        message = "Resultados de la validación:\n\n"
        for provider, result in results.items():
            message += f"• {provider.title()}: {result}\n"
        
        message += "\nNota: Para una validación completa, guarda la configuración y prueba generar un perfil."
        
        QMessageBox.information(self, "Prueba de Conexiones", message)
    
    def _save_config(self):
        """Guarda la configuración de API keys."""
        # Obtener claves de los campos
        openai_key = self.openai_key_edit.text().strip()
        google_key = self.google_key_edit.text().strip()
        anthropic_key = self.anthropic_key_edit.text().strip()
        
        # Validar que al menos una clave esté configurada
        if not any([openai_key, google_key, anthropic_key]):
            QMessageBox.warning(
                self,
                "Configuración Incompleta",
                "Debes configurar al menos una clave API para continuar."
            )
            return
        
        try:
            # Guardar configuración
            self.config_manager.save_api_keys(
                openai_key=openai_key,
                google_key=google_key,
                anthropic_key=anthropic_key
            )
            
            # Emitir señal con el estado de cada proveedor
            status = {
                'openai': len(openai_key) >= 10,
                'google': len(google_key) >= 10,
                'anthropic': len(anthropic_key) >= 10
            }
            self.config_saved.emit(status)
            
            QMessageBox.information(
                self,
                "Configuración Guardada",
                "Las claves API se han guardado correctamente.\n\n"
                "Ahora puedes generar perfiles usando los proveedores configurados."
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al Guardar",
                f"Ocurrió un error al guardar la configuración:\n\n{str(e)}"
            )
    
    def get_configured_providers(self) -> list:
        """Retorna la lista de proveedores configurados."""
        keys = self.config_manager.load_api_keys()
        configured = []
        
        if len(keys.get('openai', '')) >= 10:
            configured.append('OpenAI')
        if len(keys.get('google', '')) >= 10:
            configured.append('Google Gemini')
        if len(keys.get('anthropic', '')) >= 10:
            configured.append('Anthropic')
        
        return configured 