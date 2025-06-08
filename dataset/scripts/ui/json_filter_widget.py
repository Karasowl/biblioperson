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
        self.operator_combo.addItems([
            "eq", "neq", "contains", "not_contains", 
            "regex", "gte", "lte", "exists", "not_exists"
        ])
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
        rule = {
            "field": self.field_edit.text().strip(),
            "operator": self.operator_combo.currentText(),
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
        
        operator = rule_data.get("operator", "eq")
        index = self.operator_combo.findText(operator)
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
        
        text_layout.addWidget(QLabel("Rutas de propiedades de texto (separadas por comas):"))
        self.text_paths_edit = QLineEdit()
        self.text_paths_edit.setText("text,content,message,body")
        self.text_paths_edit.setPlaceholderText("ej: text,content,message,description")
        text_layout.addWidget(self.text_paths_edit)
        
        # Configuración de estructura JSON
        struct_layout = QHBoxLayout()
        
        struct_layout.addWidget(QLabel("Ruta del array raíz:"))
        self.root_array_edit = QLineEdit()
        self.root_array_edit.setPlaceholderText("ej: data, results.items (opcional)")
        struct_layout.addWidget(self.root_array_edit)
        
        self.single_object_cb = QCheckBox("Tratar como objeto único")
        struct_layout.addWidget(self.single_object_cb)
        
        text_layout.addLayout(struct_layout)
        
        # Configuración de metadatos
        meta_layout = QHBoxLayout()
        
        meta_layout.addWidget(QLabel("Campo ID:"))
        self.pointer_edit = QLineEdit()
        self.pointer_edit.setText("id")
        self.pointer_edit.setPlaceholderText("ej: id, _id, uuid")
        meta_layout.addWidget(self.pointer_edit)
        
        meta_layout.addWidget(QLabel("Campo fecha:"))
        self.date_edit = QLineEdit()
        self.date_edit.setText("date")
        self.date_edit.setPlaceholderText("ej: date, created_at, timestamp")
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
        
        # Sección de prueba
        test_group = QGroupBox("Probar Configuración")
        test_layout = QVBoxLayout(test_group)
        
        test_buttons = QHBoxLayout()
        
        self.test_file_btn = QPushButton("Seleccionar Archivo JSON de Prueba")
        self.test_file_btn.clicked.connect(self.select_test_file)
        test_buttons.addWidget(self.test_file_btn)
        
        self.run_test_btn = QPushButton("Ejecutar Prueba")
        self.run_test_btn.clicked.connect(self.run_test)
        test_buttons.addWidget(self.run_test_btn)
        
        test_layout.addLayout(test_buttons)
        
        self.test_file_label = QLabel("Ningún archivo seleccionado")
        test_layout.addWidget(self.test_file_label)
        
        self.test_results = QTextEdit()
        self.test_results.setMaximumHeight(150)
        self.test_results.setPlaceholderText("Los resultados de la prueba aparecerán aquí...")
        test_layout.addWidget(self.test_results)
        
        layout.addWidget(test_group)
        
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
    
    def select_test_file(self):
        """Selecciona un archivo JSON para probar la configuración."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo JSON de Prueba",
            "", "JSON Files (*.json)"
        )
        
        if file_path:
            self.test_file_path = file_path
            self.test_file_label.setText(f"Archivo: {Path(file_path).name}")
            logger.debug(f"Archivo de prueba seleccionado: {file_path}")
    
    def run_test(self):
        """Ejecuta una prueba de la configuración actual."""
        if not hasattr(self, 'test_file_path'):
            QMessageBox.warning(
                self, "Advertencia", 
                "Primero seleccione un archivo JSON de prueba."
            )
            return
        
        try:
            from ...processing.loaders.json_loader import JSONLoader
            
            config = self.get_configuration()
            
            # Crear loader con la configuración
            loader = JSONLoader(Path(self.test_file_path), **config)
            
            # Procesar archivo
            data = loader.load()
            blocks = data['blocks']
            document_metadata = data['document_metadata']
            
            # Mostrar resultados
            self.test_results.clear()
            self.test_results.append(f"=== RESULTADOS DE PRUEBA ===\n")
            self.test_results.append(f"Archivo: {Path(self.test_file_path).name}")
            self.test_results.append(f"Bloques procesados: {len(blocks)}")
            self.test_results.append(f"Configuración aplicada: {len(config['filter_rules'])} reglas")
            self.test_results.append(f"Formato: {document_metadata.get('file_format', 'N/A')}\n")
            
            if blocks:
                self.test_results.append("=== PRIMEROS 3 BLOQUES ===")
                for i, block in enumerate(blocks[:3]):
                    self.test_results.append(f"\n--- Bloque {i+1} ---")
                    self.test_results.append(f"Texto: {block.get('text', '')[:100]}...")
                    self.test_results.append(f"Fecha: {block.get('detected_date', 'N/A')}")
                    self.test_results.append(f"Orden: {block.get('order_in_document', 'N/A')}")
                    pointer = block.get('metadata', {}).get('pointer', 'N/A')
                    self.test_results.append(f"ID: {pointer}")
            else:
                self.test_results.append("\n⚠️ No se obtuvieron bloques.")
                self.test_results.append("Verifique las reglas de filtro y la estructura del JSON.")
                if document_metadata.get('error'):
                    self.test_results.append(f"Error: {document_metadata['error']}")
            
            logger.info(f"Prueba ejecutada: {len(blocks)} bloques obtenidos")
            
        except Exception as e:
            self.test_results.clear()
            self.test_results.append(f"❌ ERROR EN LA PRUEBA:\n{str(e)}")
            logger.error(f"Error en prueba de configuración: {e}") 