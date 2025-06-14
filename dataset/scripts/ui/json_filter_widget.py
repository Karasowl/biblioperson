"""Widget para configurar filtros de archivos JSON."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTextEdit, QGroupBox, QScrollArea,
    QFrame, QMessageBox, QFileDialog, QCheckBox, QSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class FilterRuleWidget(QFrame):
    """Widget para configurar una regla de filtro individual."""
    
    remove_requested = Signal(object)  # Señal para solicitar eliminación
    
    def __init__(self, rule_data: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 5px; }")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(260)  # Altura mínima mayor para que se vean todos los controles
        
        self.setup_ui()
        if rule_data:
            self.load_rule_data(rule_data)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 14, 12, 14)

        # --- Campo ---
        campo_lbl = QLabel("Campo:")
        self.field_edit = QLineEdit()
        self.field_edit.setPlaceholderText("ej: status, user.name, metadata.type")
        self.field_edit.setFixedHeight(52)
        self.field_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(campo_lbl)
        layout.addWidget(self.field_edit)

        # --- Operador ---
        operador_lbl = QLabel("Operador:")
        self.operator_combo = QComboBox()
        self.operator_combo.setFixedHeight(46)
        self.operator_combo.addItems([
            "Igual a", "Diferente de", "Contiene", "No contiene", 
            "Expresión regular", "Mayor o igual", "Menor o igual", "Existe", "No existe"
        ])
        self.operator_mapping = {
            "Igual a": "eq",
            "Diferente de": "neq",
            "Contiene": "contains",
            "No contiene": "not_contains",
            "Expresión regular": "regex",
            "Mayor o igual": "gte",
            "Menor o igual": "lte",
            "Existe": "exists",
            "No existe": "not_exists"
        }
        self.reverse_operator_mapping = {v: k for k, v in self.operator_mapping.items()}
        layout.addWidget(operador_lbl)
        layout.addWidget(self.operator_combo)

        # --- Valor ---
        valor_lbl = QLabel("Valor:")
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Valor a comparar (opcional para exists/not_exists)")
        self.value_edit.setFixedHeight(52)
        self.value_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(valor_lbl)
        layout.addWidget(self.value_edit)

        # --- Opciones avanzadas + botón eliminar ---
        opts_layout = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("Sensible a mayúsculas")
        self.case_sensitive_cb.setFixedHeight(32)
        self.negate_cb = QCheckBox("Negar resultado")
        self.negate_cb.setFixedHeight(32)
        opts_layout.addWidget(self.case_sensitive_cb)
        opts_layout.addWidget(self.negate_cb)
        opts_layout.addStretch()

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedWidth(28)
        self.remove_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; }")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        opts_layout.addWidget(self.remove_btn)

        layout.addLayout(opts_layout)
    
    def get_rule_data(self) -> Dict[str, Any]:
        """Obtiene los datos de la regla configurada."""
        # Convertir operador amigable a formato interno
        friendly_operator = self.operator_combo.currentText()
        internal_operator = self.operator_mapping.get(friendly_operator, "eq")
        
        rule = {
            "field": self.field_edit.text().strip(),
            "operator": internal_operator,
            "value": self.value_edit.text().strip()
        }
        
        if self.case_sensitive_cb.isChecked():
            rule["case_sensitive"] = True
        
        if self.negate_cb.isChecked():
            rule["negate"] = True
            
        return rule
    
    def load_rule_data(self, rule_data: Dict[str, Any]):
        """Carga datos de regla en el widget."""
        self.field_edit.setText(rule_data.get("field", ""))
        
        # Convertir operador interno a formato amigable
        internal_operator = rule_data.get("operator", "eq")
        friendly_operator = self.reverse_operator_mapping.get(internal_operator, "Igual a")
        index = self.operator_combo.findText(friendly_operator)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)
        
        self.value_edit.setText(str(rule_data.get("value", "")))
        self.case_sensitive_cb.setChecked(rule_data.get("case_sensitive", False))
        self.negate_cb.setChecked(rule_data.get("negate", False))


class JSONFilterWidget(QWidget):
    """Widget principal para configurar filtros de archivos JSON."""
    
    configuration_changed = Signal()  # Señal emitida cuando cambia la configuración
    
    def __init__(self):
        super().__init__()
        self.filter_rules: List[FilterRuleWidget] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)  # Espaciado muy aumentado entre secciones
        layout.setContentsMargins(15, 25, 15, 20)  # Márgenes significativamente aumentados
        
        # Título
        title = QLabel("Configuración de Filtros JSON")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Configuración de extracción de texto
        text_group = QGroupBox("Extracción de Texto")
        text_group.setObjectName("extraction_container")  # Para aplicar estilos CSS
        text_group.setMinimumHeight(800)  # Altura mínima aún mayor para evitar compresión
        text_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        text_layout = QVBoxLayout(text_group)
        text_layout.setSpacing(18)  # Espaciado muy aumentado entre elementos
        text_layout.setContentsMargins(18, 25, 18, 20)  # Márgenes internos aumentados
        
        text_paths_label = QLabel("Rutas de propiedades de texto (separadas por comas):")
        text_paths_label.setToolTip("Especifica qué campos del JSON contienen el texto que deseas extraer. Por ejemplo: 'text,content,message' buscará el texto en esos campos de cada objeto JSON.")
        text_layout.addWidget(text_paths_label)
        self.text_paths_edit = QLineEdit()
        self.text_paths_edit.setText("text,content,message,body")
        self.text_paths_edit.setPlaceholderText("ej: text,content,message,description")
        self.text_paths_edit.setToolTip("Lista de campos separados por comas donde se encuentra el texto a extraer")
        text_layout.addWidget(self.text_paths_edit)
        
        # --- Ruta del array raíz ---
        root_array_label = QLabel("Ruta del array raíz:")
        root_array_label.setToolTip("Especifica dónde están los elementos a procesar en el JSON. Por ejemplo: 'data' si los elementos están en obj.data, o 'results.items' para obj.results.items. Déjalo vacío si los elementos están en la raíz.")
        text_layout.addWidget(root_array_label)

        self.root_array_edit = QLineEdit()
        self.root_array_edit.setPlaceholderText("ej: data, results.items (opcional)")
        self.root_array_edit.setToolTip("Ruta hacia el array que contiene los elementos a procesar")
        text_layout.addWidget(self.root_array_edit)

        # Checkbox de objeto único en línea aparte para evitar compresión
        self.single_object_cb = QCheckBox("Tratar como objeto único")
        self.single_object_cb.setToolTip("Marca esta opción si el JSON es un solo objeto en lugar de un array de objetos")
        text_layout.addWidget(self.single_object_cb)

        # Separador visual
        text_layout.addSpacing(12)
        
        # Configuración de metadatos
        # --- Metadatos: Campo ID ---
        id_label = QLabel("Campo ID:")
        id_label.setToolTip("Especifica qué campo del JSON contiene el identificador único de cada elemento.")
        text_layout.addWidget(id_label)

        self.pointer_edit = QLineEdit()
        self.pointer_edit.setText("id")
        self.pointer_edit.setPlaceholderText("ej: id, _id, uuid")
        self.pointer_edit.setToolTip("Campo que contiene el identificador único de cada elemento")
        text_layout.addWidget(self.pointer_edit)

        # --- Metadatos: Campo fecha ---
        date_label = QLabel("Campo fecha:")
        date_label.setToolTip("Especifica qué campo del JSON contiene la fecha/timestamp de cada elemento.")
        text_layout.addWidget(date_label)

        self.date_edit = QLineEdit()
        self.date_edit.setText("date")
        self.date_edit.setPlaceholderText("ej: date, created_at, timestamp")
        self.date_edit.setToolTip("Campo que contiene la fecha o timestamp del elemento")
        text_layout.addWidget(self.date_edit)

        text_layout.addSpacing(12)
        
        # Configuración de longitud de texto
        length_layout = QVBoxLayout()
        
        # Longitud mínima
        min_length_row = QHBoxLayout()
        self.min_length_enabled_cb = QCheckBox("Aplicar longitud mínima de texto (caracteres):")
        self.min_length_enabled_cb.setToolTip("Marcar para aplicar un filtro de longitud mínima en caracteres")
        self.min_length_enabled_cb.toggled.connect(self._on_min_length_enabled_changed)
        min_length_row.addWidget(self.min_length_enabled_cb)
        
        self.min_text_length_spin = QSpinBox()
        self.min_text_length_spin.setMinimum(1)
        self.min_text_length_spin.setMaximum(999999)
        self.min_text_length_spin.setValue(1)
        self.min_text_length_spin.setEnabled(False)
        self.min_text_length_spin.setToolTip("Longitud mínima en caracteres")
        min_length_row.addWidget(self.min_text_length_spin)
        min_length_row.addStretch()
        
        length_layout.addLayout(min_length_row)
        
        # Longitud máxima
        max_length_row = QHBoxLayout()
        self.max_length_enabled_cb = QCheckBox("Aplicar longitud máxima de texto (caracteres):")
        self.max_length_enabled_cb.setToolTip("Marcar para aplicar un filtro de longitud máxima en caracteres")
        self.max_length_enabled_cb.toggled.connect(self._on_max_length_enabled_changed)
        max_length_row.addWidget(self.max_length_enabled_cb)
        
        self.max_text_length_spin = QSpinBox()
        self.max_text_length_spin.setMinimum(1)
        self.max_text_length_spin.setMaximum(999999)
        self.max_text_length_spin.setValue(1000)
        self.max_text_length_spin.setEnabled(False)
        self.max_text_length_spin.setToolTip("Longitud máxima en caracteres")
        max_length_row.addWidget(self.max_text_length_spin)
        max_length_row.addStretch()
        
        length_layout.addLayout(max_length_row)
        
        text_layout.addLayout(length_layout)
        # Aplicar ajustes de tamaño ahora que todos los widgets existen
        for _le in [self.text_paths_edit, self.root_array_edit, self.pointer_edit, self.date_edit]:
            _le.setFixedHeight(52)
            _le.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        for _cb in [self.single_object_cb, self.min_length_enabled_cb, self.max_length_enabled_cb]:
            _cb.setFixedHeight(40)
            _cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        for _spin in [self.min_text_length_spin, self.max_text_length_spin]:
            _spin.setFixedHeight(36)
            _spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        text_layout.addSpacing(12)

        # Agregar directamente el grupo al layout principal (el scroll global del panel de configuración ya gestiona el desbordamiento)
        layout.addWidget(text_group)
        
        # Sección de reglas de filtro
        filter_group = QGroupBox("Reglas de Filtrado")
        filter_group.setMinimumHeight(650)  # Altura mínima amplia para visualizar regla completa
        filter_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(18)  # Espaciado muy aumentado entre elementos
        filter_layout.setContentsMargins(18, 25, 18, 20)  # Márgenes internos aumentados
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        
        self.add_rule_btn = QPushButton("+ Agregar Regla")
        self.add_rule_btn.clicked.connect(self.add_filter_rule)
        buttons_layout.addWidget(self.add_rule_btn)
        
        self.clear_rules_btn = QPushButton("Limpiar Todo")
        self.clear_rules_btn.clicked.connect(self.clear_all_rules)
        buttons_layout.addWidget(self.clear_rules_btn)
        
        buttons_layout.addStretch()
        
        self.save_config_btn = QPushButton("Guardar Configuración")
        self.save_config_btn.clicked.connect(self.save_configuration)
        buttons_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("Cargar Configuración")
        self.load_config_btn.clicked.connect(self.load_configuration)
        buttons_layout.addWidget(self.load_config_btn)
        
        filter_layout.addLayout(buttons_layout)
        
        # Área de scroll para las reglas con altura controlada
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(500)
        self.scroll_area.setMaximumHeight(1000)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.rules_widget = QWidget()
        self.rules_widget.setObjectName("filter_rules_container")  # Para aplicar estilos CSS
        self.rules_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.rules_layout = QVBoxLayout(self.rules_widget)
        self.rules_layout.setAlignment(Qt.AlignTop)  # Alinear arriba en lugar de stretch
        
        self.scroll_area.setWidget(self.rules_widget)
        filter_layout.addWidget(self.scroll_area)
        
        # Añadir el grupo de reglas al layout principal
        layout.addWidget(filter_group)

        # Conectar señales para auto-guardado
        self._connect_configuration_signals()

        # Agregar una regla por defecto
        self.add_filter_rule()
    
    def _connect_configuration_signals(self):
        """Conecta las señales de los elementos de UI para emitir configuration_changed."""
        # Conectar elementos de configuración de texto
        self.text_paths_edit.textChanged.connect(lambda: self.configuration_changed.emit())
        self.root_array_edit.textChanged.connect(lambda: self.configuration_changed.emit())
        self.single_object_cb.toggled.connect(lambda: self.configuration_changed.emit())
        
        # Conectar elementos de metadatos
        self.pointer_edit.textChanged.connect(lambda: self.configuration_changed.emit())
        self.date_edit.textChanged.connect(lambda: self.configuration_changed.emit())
        
        # Conectar elementos de longitud
        self.min_length_enabled_cb.toggled.connect(lambda: self.configuration_changed.emit())
        self.min_text_length_spin.valueChanged.connect(lambda: self.configuration_changed.emit())
        self.max_length_enabled_cb.toggled.connect(lambda: self.configuration_changed.emit())
        self.max_text_length_spin.valueChanged.connect(lambda: self.configuration_changed.emit())
    
    def add_filter_rule(self, rule_data: Optional[Dict[str, Any]] = None):
        """Agrega una nueva regla de filtro."""
        rule_widget = FilterRuleWidget(rule_data)
        rule_widget.remove_requested.connect(self.remove_filter_rule)
        
        # Conectar señales de la regla para detectar cambios
        if hasattr(rule_widget, 'field_edit'):
            rule_widget.field_edit.textChanged.connect(lambda: self.configuration_changed.emit())
        if hasattr(rule_widget, 'operator_combo'):
            rule_widget.operator_combo.currentTextChanged.connect(lambda: self.configuration_changed.emit())
        if hasattr(rule_widget, 'value_edit'):
            rule_widget.value_edit.textChanged.connect(lambda: self.configuration_changed.emit())
        if hasattr(rule_widget, 'case_sensitive_cb'):
            rule_widget.case_sensitive_cb.toggled.connect(lambda: self.configuration_changed.emit())
        if hasattr(rule_widget, 'negate_cb'):
            rule_widget.negate_cb.toggled.connect(lambda: self.configuration_changed.emit())
        
        # Agregar al final del layout (ya no hay stretch)
        self.rules_layout.addWidget(rule_widget)
        self.filter_rules.append(rule_widget)
        
        # Emitir señal de cambio de configuración
        self.configuration_changed.emit()
        
        logger.debug(f"Regla de filtro agregada. Total: {len(self.filter_rules)}")
    
    def remove_filter_rule(self, rule_widget: FilterRuleWidget):
        """Elimina una regla de filtro."""
        if rule_widget in self.filter_rules:
            self.filter_rules.remove(rule_widget)
            rule_widget.setParent(None)
            rule_widget.deleteLater()
            
            # Emitir señal de cambio de configuración
            self.configuration_changed.emit()
            
            logger.debug(f"Regla de filtro eliminada. Total: {len(self.filter_rules)}")
    
    def clear_all_rules(self):
        """Elimina todas las reglas de filtro."""
        reply = QMessageBox.question(
            self, "Confirmar", 
            "¿Está seguro de que desea eliminar todas las reglas?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for rule_widget in self.filter_rules[:]:
                self.remove_filter_rule(rule_widget)
    
    def _on_min_length_enabled_changed(self, enabled: bool):
        """Callback cuando se habilita/deshabilita el filtro de longitud mínima."""
        self.min_text_length_spin.setEnabled(enabled)
    
    def _on_max_length_enabled_changed(self, enabled: bool):
        """Callback cuando se habilita/deshabilita el filtro de longitud máxima."""
        self.max_text_length_spin.setEnabled(enabled)
    
    def get_configuration(self) -> Dict[str, Any]:
        """Obtiene la configuración completa de filtros."""
        config = {
            "text_property_paths": [
                path.strip() for path in self.text_paths_edit.text().split(",") 
                if path.strip()
            ],
            "filter_rules": [
                rule.get_rule_data() for rule in self.filter_rules
                if rule.get_rule_data().get("field")  # Solo reglas con campo definido
            ],
            "pointer_path": self.pointer_edit.text().strip() or "id",
            "date_path": self.date_edit.text().strip() or "date",
            "root_array_path": self.root_array_edit.text().strip() or None,
            "treat_as_single_object": self.single_object_cb.isChecked(),
            "min_text_length": self.min_text_length_spin.value() if self.min_length_enabled_cb.isChecked() else None,
            "max_text_length": self.max_text_length_spin.value() if self.max_length_enabled_cb.isChecked() else None
        }
        
        return config
    
    def load_configuration_data(self, config: Dict[str, Any]):
        """Carga una configuración en el widget."""
        # Limpiar reglas existentes (bloquea señales para evitar callbacks sobre objetos eliminados)
        self.blockSignals(True)
        try:
            for rule_widget in self.filter_rules[:]:
                self.remove_filter_rule(rule_widget)
        finally:
            self.blockSignals(False)
        
        # Cargar configuración básica
        text_paths = config.get("text_property_paths", ["text", "content", "message", "body"])
        self.text_paths_edit.setText(",".join(text_paths))
        
        self.pointer_edit.setText(config.get("pointer_path", "id"))
        self.date_edit.setText(config.get("date_path", "date"))
        self.root_array_edit.setText(config.get("root_array_path", "") or "")
        self.single_object_cb.setChecked(config.get("treat_as_single_object", False))
        
        # Cargar configuración de longitud de texto
        min_length = config.get("min_text_length")
        if min_length is not None:
            self.min_length_enabled_cb.setChecked(True)
            self.min_text_length_spin.setValue(min_length)
            self.min_text_length_spin.setEnabled(True)
        else:
            self.min_length_enabled_cb.setChecked(False)
            self.min_text_length_spin.setValue(1)
            self.min_text_length_spin.setEnabled(False)
        
        max_length = config.get("max_text_length")
        if max_length is not None:
            self.max_length_enabled_cb.setChecked(True)
            self.max_text_length_spin.setValue(max_length)
            self.max_text_length_spin.setEnabled(True)
        else:
            self.max_length_enabled_cb.setChecked(False)
            self.max_text_length_spin.setValue(1000)
            self.max_text_length_spin.setEnabled(False)
        
        # Cargar reglas de filtro
        filter_rules = config.get("filter_rules", [])
        for rule_data in filter_rules:
            self.add_filter_rule(rule_data)
        
        # Si no hay reglas, agregar una vacía
        if not filter_rules:
            self._ensure_default_rule()
        
        # En caso de que la carga fallara y dejara el layout sin reglas
        self._ensure_default_rule()
        
        logger.info(f"Configuración cargada: {len(filter_rules)} reglas")
    
    def _ensure_default_rule(self):
        """Garantiza que exista al menos una regla visible para evitar que el usuario se quede sin interfaz cuando
        la carga de configuración falle o venga vacía."""
        if not self.filter_rules:
            self.add_filter_rule()
    
    def save_configuration(self):
        """Guarda la configuración actual en un archivo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Filtros JSON",
            "json_filter_config.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                config = self.get_configuration()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(
                    self, "Éxito", 
                    f"Configuración guardada en:\n{file_path}"
                )
                logger.info(f"Configuración guardada en: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Error al guardar configuración:\n{str(e)}"
                )
                logger.error(f"Error al guardar configuración: {e}")
    
    def load_configuration(self):
        """Carga una configuración desde un archivo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Filtros JSON",
            "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.load_configuration_data(config)
                
                QMessageBox.information(
                    self, "Éxito", 
                    f"Configuración cargada desde:\n{file_path}"
                )
                logger.info(f"Configuración cargada desde: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Error al cargar configuración:\n{str(e)}"
                )
                logger.error(f"Error al cargar configuración: {e}")