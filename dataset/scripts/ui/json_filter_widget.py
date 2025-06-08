"""Widget para configurar filtros de archivos JSON."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTextEdit, QGroupBox, QScrollArea,
    QFrame, QMessageBox, QFileDialog, QCheckBox, QSpinBox
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
        
        self.setup_ui()
        if rule_data:
            self.load_rule_data(rule_data)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Primera fila: Campo y operador
        row1 = QHBoxLayout()
        
        row1.addWidget(QLabel("Campo:"))
        self.field_edit = QLineEdit()
        self.field_edit.setPlaceholderText("ej: status, user.name, metadata.type")
        row1.addWidget(self.field_edit)
        
        row1.addWidget(QLabel("Operador:"))
        self.operator_combo = QComboBox()
        # Operadores más amigables en español
        self.operator_combo.addItems([
            "Igual a", "Diferente de", "Contiene", "No contiene", 
            "Expresión regular", "Mayor o igual", "Menor o igual", "Existe", "No existe"
        ])
        # Mapeo interno para conversión
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
        # Mapeo inverso para cargar configuraciones
        self.reverse_operator_mapping = {v: k for k, v in self.operator_mapping.items()}
        row1.addWidget(self.operator_combo)
        
        # Botón eliminar
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setMaximumWidth(30)
        self.remove_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; }")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        row1.addWidget(self.remove_btn)
        
        layout.addLayout(row1)
        
        # Segunda fila: Valor
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Valor:"))
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Valor a comparar (opcional para exists/not_exists)")
        row2.addWidget(self.value_edit)
        
        layout.addLayout(row2)
        
        # Tercera fila: Opciones avanzadas
        row3 = QHBoxLayout()
        
        self.case_sensitive_cb = QCheckBox("Sensible a mayúsculas")
        row3.addWidget(self.case_sensitive_cb)
        
        self.negate_cb = QCheckBox("Negar resultado")
        row3.addWidget(self.negate_cb)
        
        row3.addStretch()
        layout.addLayout(row3)
    
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
    
    def __init__(self):
        super().__init__()
        self.filter_rules: List[FilterRuleWidget] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Configuración de Filtros JSON")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Configuración de extracción de texto
        text_group = QGroupBox("Extracción de Texto")
        text_layout = QVBoxLayout(text_group)
        
        text_paths_label = QLabel("Rutas de propiedades de texto (separadas por comas):")
        text_paths_label.setToolTip("Especifica qué campos del JSON contienen el texto que deseas extraer. Por ejemplo: 'text,content,message' buscará el texto en esos campos de cada objeto JSON.")
        text_layout.addWidget(text_paths_label)
        self.text_paths_edit = QLineEdit()
        self.text_paths_edit.setText("text,content,message,body")
        self.text_paths_edit.setPlaceholderText("ej: text,content,message,description")
        self.text_paths_edit.setToolTip("Lista de campos separados por comas donde se encuentra el texto a extraer")
        text_layout.addWidget(self.text_paths_edit)
        
        # Configuración de estructura JSON
        struct_layout = QHBoxLayout()
        
        root_array_label = QLabel("Ruta del array raíz:")
        root_array_label.setToolTip("Especifica dónde están los elementos a procesar en el JSON. Por ejemplo: 'data' si los elementos están en obj.data, o 'results.items' para obj.results.items. Déjalo vacío si los elementos están en la raíz.")
        struct_layout.addWidget(root_array_label)
        self.root_array_edit = QLineEdit()
        self.root_array_edit.setPlaceholderText("ej: data, results.items (opcional)")
        self.root_array_edit.setToolTip("Ruta hacia el array que contiene los elementos a procesar")
        struct_layout.addWidget(self.root_array_edit)
        
        self.single_object_cb = QCheckBox("Tratar como objeto único")
        self.single_object_cb.setToolTip("Marca esta opción si el JSON es un solo objeto en lugar de un array de objetos")
        struct_layout.addWidget(self.single_object_cb)
        
        text_layout.addLayout(struct_layout)
        
        # Configuración de metadatos
        meta_layout = QHBoxLayout()
        
        id_label = QLabel("Campo ID:")
        id_label.setToolTip("Especifica qué campo del JSON contiene el identificador único de cada elemento. Este se usará para referenciar y ordenar los elementos.")
        meta_layout.addWidget(id_label)
        self.pointer_edit = QLineEdit()
        self.pointer_edit.setText("id")
        self.pointer_edit.setPlaceholderText("ej: id, _id, uuid")
        self.pointer_edit.setToolTip("Campo que contiene el identificador único de cada elemento")
        meta_layout.addWidget(self.pointer_edit)
        
        date_label = QLabel("Campo fecha:")
        date_label.setToolTip("Especifica qué campo del JSON contiene la fecha/timestamp de cada elemento. Se usará para ordenar cronológicamente los elementos.")
        meta_layout.addWidget(date_label)
        self.date_edit = QLineEdit()
        self.date_edit.setText("date")
        self.date_edit.setPlaceholderText("ej: date, created_at, timestamp")
        self.date_edit.setToolTip("Campo que contiene la fecha o timestamp del elemento")
        meta_layout.addWidget(self.date_edit)
        
        text_layout.addLayout(meta_layout)
        layout.addWidget(text_group)
        
        # Sección de reglas de filtro
        filter_group = QGroupBox("Reglas de Filtrado")
        filter_layout = QVBoxLayout(filter_group)
        
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
        
        # Área de scroll para las reglas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(200)
        
        self.rules_widget = QWidget()
        self.rules_layout = QVBoxLayout(self.rules_widget)
        self.rules_layout.addStretch()
        
        self.scroll_area.setWidget(self.rules_widget)
        filter_layout.addWidget(self.scroll_area)
        
        layout.addWidget(filter_group)
        

        
        # Agregar una regla por defecto
        self.add_filter_rule()
    
    def add_filter_rule(self, rule_data: Optional[Dict[str, Any]] = None):
        """Agrega una nueva regla de filtro."""
        rule_widget = FilterRuleWidget(rule_data)
        rule_widget.remove_requested.connect(self.remove_filter_rule)
        
        # Insertar antes del stretch
        self.rules_layout.insertWidget(self.rules_layout.count() - 1, rule_widget)
        self.filter_rules.append(rule_widget)
        
        logger.debug(f"Regla de filtro agregada. Total: {len(self.filter_rules)}")
    
    def remove_filter_rule(self, rule_widget: FilterRuleWidget):
        """Elimina una regla de filtro."""
        if rule_widget in self.filter_rules:
            self.filter_rules.remove(rule_widget)
            rule_widget.setParent(None)
            rule_widget.deleteLater()
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
            "treat_as_single_object": self.single_object_cb.isChecked()
        }
        
        return config
    
    def load_configuration_data(self, config: Dict[str, Any]):
        """Carga una configuración en el widget."""
        # Limpiar reglas existentes
        for rule_widget in self.filter_rules[:]:
            self.remove_filter_rule(rule_widget)
        
        # Cargar configuración básica
        text_paths = config.get("text_property_paths", ["text", "content", "message", "body"])
        self.text_paths_edit.setText(",".join(text_paths))
        
        self.pointer_edit.setText(config.get("pointer_path", "id"))
        self.date_edit.setText(config.get("date_path", "date"))
        self.root_array_edit.setText(config.get("root_array_path", "") or "")
        self.single_object_cb.setChecked(config.get("treat_as_single_object", False))
        
        # Cargar reglas de filtro
        filter_rules = config.get("filter_rules", [])
        for rule_data in filter_rules:
            self.add_filter_rule(rule_data)
        
        # Si no hay reglas, agregar una vacía
        if not filter_rules:
            self.add_filter_rule()
        
        logger.info(f"Configuración cargada: {len(filter_rules)} reglas")
    
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