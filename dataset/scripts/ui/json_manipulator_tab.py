#!/usr/bin/env python3
"""
Tab de manipulación y limpieza de archivos JSON/NDJSON.

Este módulo proporciona una interfaz completa para:
- Visualizar estructura de archivos JSON
- Eliminar propiedades específicas
- Filtrar contenido por criterios
- Unir arrays de texto
- Limpiar datos innecesarios
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QCheckBox, QSpinBox,
    QGroupBox, QSplitter, QProgressBar, QComboBox,
    QMessageBox, QFrame, QScrollArea, QFormLayout,
    QTabWidget, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QFont, QTextDocument, QTextCursor


class JSONStructureViewer(QTreeWidget):
    """Widget para visualizar el esquema unificado de un JSON."""
    
    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Clave", "Tipo", "Frecuencia", "Seleccionar"])
        self.setAlternatingRowColors(True)
        self.selected_keys = set()
        self.key_checkboxes = {}  # Para poder acceder a los checkboxes por clave
        
    def load_json_structure(self, data: Any):
        print(f"DEBUG: load_json_structure llamado, limpiando estado previo")  # Debug
        """Carga el esquema unificado del JSON en el árbol."""
        self.clear()
        self.selected_keys.clear()
        self.key_checkboxes.clear()
        
        print(f"DEBUG: Tipo de data: {type(data)}")
        if isinstance(data, list):
            print(f"DEBUG: Es una lista con {len(data)} elementos")
        elif isinstance(data, dict):
            print(f"DEBUG: Es un dict con claves: {list(data.keys())[:5]}...")  # Solo primeras 5
        
        # Analizar la estructura para crear un esquema unificado
        schema = self._analyze_structure(data)
        print(f"DEBUG: Schema analizado con {len(schema)} paths")
        
        # Construir el árbol del esquema
        self._build_schema_tree(schema)
        
        print(f"DEBUG: Total de checkboxes creados: {len(self.key_checkboxes)}")
        print(f"DEBUG: Paths con checkboxes: {list(self.key_checkboxes.keys())[:5]}...")  # Solo primeros 5
        
        self.expandAll()
    
    def _analyze_structure(self, data: Any, path: str = "") -> Dict[str, Dict]:
        """Analiza la estructura del JSON para crear un esquema unificado."""
        schema = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if current_path not in schema:
                    schema[current_path] = {
                        'type': type(value).__name__,
                        'count': 0,
                        'children': {},
                        'sample_values': set()
                    }
                
                schema[current_path]['count'] += 1
                
                # Guardar valores de muestra para tipos primitivos
                if not isinstance(value, (dict, list)):
                    val_str = str(value)
                    if len(val_str) <= 50:
                        schema[current_path]['sample_values'].add(val_str)
                        if len(schema[current_path]['sample_values']) > 5:
                            schema[current_path]['sample_values'] = set(list(schema[current_path]['sample_values'])[:5])
                
                # Recursión para objetos anidados
                if isinstance(value, (dict, list)):
                    child_schema = self._analyze_structure(value, current_path)
                    for child_path, child_info in child_schema.items():
                        if child_path not in schema:
                            schema[child_path] = child_info
                        else:
                            schema[child_path]['count'] += child_info['count']
                            schema[child_path]['sample_values'].update(child_info['sample_values'])
                            
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    child_schema = self._analyze_structure(item, path)
                    for child_path, child_info in child_schema.items():
                        if child_path not in schema:
                            schema[child_path] = child_info
                        else:
                            schema[child_path]['count'] += child_info['count']
                            schema[child_path]['sample_values'].update(child_info['sample_values'])
        
        return schema
    
    def _build_schema_tree(self, schema: Dict[str, Dict]):
        """Construye el árbol del esquema a partir del análisis."""
        print(f"DEBUG _build_schema_tree: Construyendo árbol con {len(schema)} paths")
        for p, i in list(schema.items())[:5]:
            print(f"  Path: {p}, Info: {i}")
        
        # Organizar las claves por jerarquía
        root_keys = {}
        
        for path, info in schema.items():
            parts = path.split('.')
            current_level = root_keys
            
            for i, part in enumerate(parts):
                if part not in current_level:
                    current_level[part] = {
                        'info': None,
                        'children': {},
                        'path': '.'.join(parts[:i+1])
                    }
                
                if i == len(parts) - 1:  # Último nivel
                    current_level[part]['info'] = info
                    print(f"DEBUG: Asignando info a {part}, path completo: {path}")
                
                current_level = current_level[part]['children']
        
        print(f"DEBUG: root_keys tiene {len(root_keys)} claves principales")
        
        # Construir el árbol visual
        self._add_tree_items(root_keys, None)
    
    def _add_tree_items(self, keys_dict: Dict, parent: QTreeWidgetItem = None):
        """Agrega elementos al árbol de forma recursiva."""
        print(f"DEBUG _add_tree_items: Agregando {len(keys_dict)} items")
        for key, data in keys_dict.items():
            item = QTreeWidgetItem(parent or self)
            item.setText(0, key)
            
            if data['info']:
                # Es una clave final con información
                info = data['info']
                item.setText(1, info['type'])
                item.setText(2, f"{info['count']} veces")
                
                # Checkbox para seleccionar esta clave
                checkbox = QCheckBox()
                checkbox.setChecked(False)  # Asegurar que empiece desmarcado
                path = data['path']
                print(f"DEBUG: Creando checkbox para path: {path}")
                
                # Guardar primero el checkbox
                self.key_checkboxes[path] = checkbox
                
                # Luego conectar el handler
                checkbox.stateChanged.connect(lambda state, p=path: self._on_key_selected(state, p))
                self.setItemWidget(item, 3, checkbox)
                print(f"DEBUG: Checkbox creado y almacenado para {path}")
                
                # Tooltip con valores de muestra
                if info['sample_values']:
                    sample_text = ", ".join(list(info['sample_values'])[:3])
                    if len(info['sample_values']) > 3:
                        sample_text += "..."
                    item.setToolTip(2, f"Valores de muestra: {sample_text}")
            else:
                # Es un contenedor
                item.setText(1, "contenedor")
                item.setText(2, "")
            
            # Agregar hijos recursivamente
            if data['children']:
                self._add_tree_items(data['children'], item)
    
    def _on_key_selected(self, state: int, path: str):
        """Maneja la selección/deselección de claves."""
        print(f"DEBUG: _on_key_selected llamado - path: {path}, state: {state}")  # Debug
        print(f"DEBUG: Qt.Checked = {Qt.Checked}, Qt.Unchecked = {Qt.Unchecked}")  # Debug para ver valores
        
        # State 2 = Checked, State 0 = Unchecked
        if state == 2:  # Qt.Checked
            self.selected_keys.add(path)
            print(f"DEBUG: Clave agregada: {path}, Total seleccionadas: {len(self.selected_keys)}")  # Debug
        else:  # Qt.Unchecked u otro estado
            self.selected_keys.discard(path)
            print(f"DEBUG: Clave removida: {path}, Total seleccionadas: {len(self.selected_keys)}")  # Debug
    
    def get_selected_keys(self) -> Set[str]:
        """Retorna las claves seleccionadas para eliminación."""
        print(f"DEBUG get_selected_keys: Retornando {len(self.selected_keys)} claves")
        print(f"DEBUG get_selected_keys: Claves: {self.selected_keys}")
        
        # Verificar el estado actual de los checkboxes
        checked_count = 0
        for path, checkbox in self.key_checkboxes.items():
            if checkbox.isChecked():
                checked_count += 1
                print(f"DEBUG: Checkbox para {path} está marcado")
        
        print(f"DEBUG: Total de checkboxes marcados: {checked_count}")
        
        return self.selected_keys.copy()
    
    def select_all_keys(self):
        """Selecciona todas las claves disponibles."""
        for path, checkbox in self.key_checkboxes.items():
            checkbox.setChecked(True)
    
    def clear_selection(self):
        """Limpia la selección de todas las claves."""
        print(f"DEBUG: clear_selection llamado, limpiando {len(self.selected_keys)} claves")  # Debug
        for path, checkbox in self.key_checkboxes.items():
            checkbox.setChecked(False)
        self.selected_keys.clear()


class FileLoader(QThread):
    """Worker para cargar archivos JSON/NDJSON en un hilo separado."""
    
    progress_update = Signal(str)
    finished = Signal(object, str, str)  # (data, file_path, message)
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        """Carga el archivo JSON/NDJSON."""
        try:
            self.progress_update.emit("Abriendo archivo...")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                if self.file_path.endswith('.ndjson') or self.file_path.endswith('.jsonl'):
                    # Cargar NDJSON con límite para archivos grandes
                    self.progress_update.emit("Leyendo NDJSON...")
                    lines = []
                    line_count = 0
                    max_lines = 10000  # Límite para evitar congelamiento
                    
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                lines.append(json.loads(line))
                                line_count += 1
                                
                                # Actualizar progreso cada 1000 líneas
                                if line_count % 1000 == 0:
                                    self.progress_update.emit(f"Cargadas {line_count} líneas...")
                                
                                # Límite para archivos muy grandes
                                if line_count >= max_lines:
                                    self.progress_update.emit(f"Archivo muy grande. Cargando solo las primeras {max_lines} líneas...")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                continue  # Saltar líneas malformadas
                    
                    data = lines
                    
                else:
                    # Cargar JSON normal
                    self.progress_update.emit("Parseando JSON...")
                    data = json.load(f)
            
            self.progress_update.emit("Finalizando...")
            self.finished.emit(data, self.file_path, "Archivo cargado exitosamente")
            
        except Exception as e:
            self.finished.emit(None, self.file_path, f"Error al cargar archivo: {str(e)}")


class JSONCleaningWorker(QThread):
    """Worker para limpiar JSON en un hilo separado."""
    
    progress_update = Signal(str)
    finished = Signal(object, bool, str)  # (resultado, success, mensaje)
    
    def __init__(self, data: Any, operations: Dict[str, Any]):
        super().__init__()
        self.data = data
        self.operations = operations
        
    def run(self):
        """Ejecuta las operaciones de limpieza."""
        try:
            result = self._clean_data(self.data)
            self.finished.emit(result, True, "Limpieza completada exitosamente")
        except Exception as e:
            self.finished.emit(self.data, False, f"Error durante la limpieza: {str(e)}")
    
    def _clean_data(self, data: Any) -> Any:
        """Aplica todas las operaciones de limpieza."""
        operations = self.operations
        
        # 1. Eliminar claves específicas
        if operations.get('remove_keys'):
            data = self._remove_keys(data, operations['remove_keys'])
            self.progress_update.emit("Claves eliminadas")
        
        # 2. Filtrar por longitud de texto
        if operations.get('filter_by_length'):
            min_len = operations['filter_by_length']['min']
            max_len = operations['filter_by_length']['max']
            data = self._filter_by_text_length(data, min_len, max_len)
            self.progress_update.emit("Filtrado por longitud aplicado")
        
        # 3. Filtrar por contenido de claves
        if operations.get('filter_by_key_content'):
            data = self._filter_by_key_content(data, operations['filter_by_key_content'])
            self.progress_update.emit("Filtrado por contenido aplicado")
        
        # 4. Unir arrays de texto
        if operations.get('merge_text_arrays'):
            data = self._merge_text_arrays(data, operations['merge_text_arrays'])
            self.progress_update.emit("Arrays de texto unidos")
        
        # 5. Eliminar objetos vacíos
        if operations.get('remove_empty'):
            data = self._remove_empty_objects(data)
            self.progress_update.emit("Objetos vacíos eliminados")
        
        return data
    
    def _remove_keys(self, data: Any, keys_to_remove: Set[str]) -> Any:
        """Elimina claves específicas del JSON."""
        # Extraer solo los nombres de las claves (sin el path completo)
        simple_keys = set()
        for path in keys_to_remove:
            # Si el path contiene puntos, tomar solo la última parte
            if '.' in path:
                simple_keys.add(path.split('.')[-1])
            else:
                simple_keys.add(path)
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key not in simple_keys:
                    result[key] = self._remove_keys(value, keys_to_remove)
            return result
        elif isinstance(data, list):
            return [self._remove_keys(item, keys_to_remove) for item in data]
        else:
            return data
    
    def _filter_by_text_length(self, data: Any, min_len: int, max_len: Optional[int]) -> Any:
        """Filtra elementos basándose en la longitud del texto."""
        if isinstance(data, dict):
            # Buscar campo de texto
            text_fields = ['text', 'message', 'content', 'body']
            text_content = ""
            for field in text_fields:
                if field in data:
                    text_content = str(data[field])
                    break
            
            if text_content:
                text_len = len(text_content)
                if text_len < min_len:
                    return None  # Filtrar este elemento
                if max_len and text_len > max_len:
                    return None  # Filtrar este elemento
            
            # Aplicar recursivamente
            result = {}
            for key, value in data.items():
                filtered_value = self._filter_by_text_length(value, min_len, max_len)
                if filtered_value is not None:
                    result[key] = filtered_value
            return result if result else None
            
        elif isinstance(data, list):
            result = []
            for item in data:
                filtered_item = self._filter_by_text_length(item, min_len, max_len)
                if filtered_item is not None:
                    result.append(filtered_item)
            return result
        else:
            return data
    
    def _filter_by_key_content(self, data: Any, filter_config: Dict) -> Any:
        """Filtra elementos basándose en el contenido de claves específicas."""
        key = filter_config['key']
        value = filter_config['value']
        operation = filter_config.get('operation', 'equals')  # equals, contains, not_contains
        
        if isinstance(data, dict):
            # Verificar si este objeto cumple el criterio
            if key in data:
                obj_value = str(data[key])
                keep_item = False
                
                if operation == 'equals':
                    keep_item = obj_value == value
                elif operation == 'contains':
                    keep_item = value in obj_value
                elif operation == 'not_contains':
                    keep_item = value not in obj_value
                
                if not keep_item:
                    return None
            
            # Aplicar recursivamente
            result = {}
            for k, v in data.items():
                filtered_value = self._filter_by_key_content(v, filter_config)
                if filtered_value is not None:
                    result[k] = filtered_value
            return result if result else None
            
        elif isinstance(data, list):
            result = []
            for item in data:
                filtered_item = self._filter_by_key_content(item, filter_config)
                if filtered_item is not None:
                    result.append(filtered_item)
            return result
        else:
            return data
    
    def _merge_text_arrays(self, data: Any, keys_to_merge: List[str]) -> Any:
        """Une arrays de texto en un solo string."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key in keys_to_merge and isinstance(value, list):
                    # Unir elementos del array
                    text_parts = []
                    for item in value:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(str(item['text']))
                        elif isinstance(item, str):
                            text_parts.append(item)
                        else:
                            text_parts.append(str(item))
                    result[key] = ' '.join(text_parts)
                else:
                    result[key] = self._merge_text_arrays(value, keys_to_merge)
            return result
        elif isinstance(data, list):
            return [self._merge_text_arrays(item, keys_to_merge) for item in data]
        else:
            return data
    
    def _remove_empty_objects(self, data: Any) -> Any:
        """Elimina objetos y arrays vacíos."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                cleaned_value = self._remove_empty_objects(value)
                if cleaned_value is not None and cleaned_value != {} and cleaned_value != []:
                    result[key] = cleaned_value
            return result if result else None
        elif isinstance(data, list):
            result = []
            for item in data:
                cleaned_item = self._remove_empty_objects(item)
                if cleaned_item is not None and cleaned_item != {} and cleaned_item != []:
                    result.append(cleaned_item)
            return result
        else:
            return data


class JSONManipulatorTab(QWidget):
    """Tab principal para manipulación de JSON/NDJSON."""
    
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.original_data = None
        self.file_path = None
        self.operations_history = []  # Historial de operaciones
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🔧 Manipulador de JSON/NDJSON")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Botones de archivo
        self.load_btn = QPushButton("📁 Cargar JSON")
        self.save_btn = QPushButton("💾 Guardar")
        self.save_as_btn = QPushButton("💾 Guardar Como")
        
        self.load_btn.clicked.connect(self._load_file)
        self.save_btn.clicked.connect(self._save_file)
        self.save_as_btn.clicked.connect(self._save_file_as)
        
        header_layout.addWidget(self.load_btn)
        header_layout.addWidget(self.save_btn)
        header_layout.addWidget(self.save_as_btn)
        
        layout.addLayout(header_layout)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Panel izquierdo: Estructura y herramientas
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Panel derecho: Vista previa
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Configurar proporciones
        main_splitter.setSizes([400, 600])
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Estado inicial
        self.save_btn.setEnabled(False)
        self.save_as_btn.setEnabled(False)
    
    def _create_left_panel(self) -> QWidget:
        """Crea el panel izquierdo con herramientas."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Información del archivo
        file_group = QGroupBox("📄 Archivo Actual")
        file_layout = QVBoxLayout(file_group)
        
        self.file_label = QLabel("Ningún archivo cargado")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        self.stats_label = QLabel("")
        file_layout.addWidget(self.stats_label)
        
        layout.addWidget(file_group)
        
        # Visualizador de estructura
        structure_group = QGroupBox("🏗️ Estructura JSON")
        structure_layout = QVBoxLayout(structure_group)
        
        self.structure_viewer = JSONStructureViewer()
        structure_layout.addWidget(self.structure_viewer)
        
        # Botones de selección
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("Seleccionar Todo")
        clear_selection_btn = QPushButton("Limpiar Selección")
        select_all_btn.clicked.connect(self._select_all_keys)
        clear_selection_btn.clicked.connect(self._clear_selection)
        select_layout.addWidget(select_all_btn)
        select_layout.addWidget(clear_selection_btn)
        structure_layout.addLayout(select_layout)
        
        layout.addWidget(structure_group)
        
        # Herramientas de manipulación
        tools_group = QGroupBox("🛠️ Herramientas")
        tools_layout = QVBoxLayout(tools_group)
        
        # Tab de herramientas
        tools_tab = QTabWidget()
        
        # Tab 1: Eliminar claves
        remove_tab = self._create_remove_keys_tab()
        tools_tab.addTab(remove_tab, "🗑️ Eliminar")
        
        # Tab 2: Filtros
        filter_tab = self._create_filters_tab()
        tools_tab.addTab(filter_tab, "🔍 Filtros")
        
        # Tab 3: Unir texto
        merge_tab = self._create_merge_tab()
        tools_tab.addTab(merge_tab, "🔗 Unir")
        
        tools_layout.addWidget(tools_tab)
        
        # Botón de aplicar cambios
        self.apply_btn = QPushButton("✨ Aplicar Cambios")
        self.apply_btn.clicked.connect(self._apply_changes)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        tools_layout.addWidget(self.apply_btn)
        
        layout.addWidget(tools_group)
        
        return panel
    
    def _create_remove_keys_tab(self) -> QWidget:
        """Crea la tab para eliminar claves."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instrucciones
        info_label = QLabel("Selecciona claves en la estructura para eliminarlas")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Lista de claves seleccionadas
        self.selected_keys_list = QListWidget()
        layout.addWidget(QLabel("Claves marcadas para eliminación:"))
        layout.addWidget(self.selected_keys_list)
        
        # Botón para eliminar claves seleccionadas
        remove_selected_btn = QPushButton("🗑️ Eliminar Claves Seleccionadas")
        remove_selected_btn.clicked.connect(self._remove_selected_keys)
        layout.addWidget(remove_selected_btn)
        
        return tab
    
    def _create_filters_tab(self) -> QWidget:
        """Crea la tab para filtros."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filtro por longitud de texto
        length_group = QGroupBox("Filtrar por longitud de texto")
        length_layout = QFormLayout(length_group)
        
        self.min_length_spin = QSpinBox()
        self.min_length_spin.setRange(0, 10000)
        self.min_length_spin.setValue(10)
        
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(0, 10000)
        self.max_length_spin.setValue(1000)
        self.max_length_spin.setSpecialValueText("Sin límite")
        
        self.enable_length_filter = QCheckBox("Activar filtro de longitud")
        
        length_layout.addRow("Mínimo caracteres:", self.min_length_spin)
        length_layout.addRow("Máximo caracteres:", self.max_length_spin)
        length_layout.addRow(self.enable_length_filter)
        
        layout.addWidget(length_group)
        
        # Filtro por contenido de clave
        content_group = QGroupBox("Filtrar por contenido de clave")
        content_layout = QFormLayout(content_group)
        
        self.filter_key_edit = QLineEdit()
        self.filter_value_edit = QLineEdit()
        self.filter_operation_combo = QComboBox()
        self.filter_operation_combo.addItems(["equals", "contains", "not_contains"])
        self.enable_content_filter = QCheckBox("Activar filtro de contenido")
        
        content_layout.addRow("Clave a verificar:", self.filter_key_edit)
        content_layout.addRow("Valor:", self.filter_value_edit)
        content_layout.addRow("Operación:", self.filter_operation_combo)
        content_layout.addRow(self.enable_content_filter)
        
        layout.addWidget(content_group)
        
        return tab
    
    def _create_merge_tab(self) -> QWidget:
        """Crea la tab para unir arrays de texto."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instrucciones
        info_label = QLabel("Especifica las claves que contienen arrays de texto para unir en un solo string")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Lista de claves para unir
        self.merge_keys_edit = QLineEdit()
        self.merge_keys_edit.setPlaceholderText("text_entities, text, message (separadas por comas)")
        layout.addWidget(QLabel("Claves a unir:"))
        layout.addWidget(self.merge_keys_edit)
        
        # Separador
        self.merge_separator_edit = QLineEdit()
        self.merge_separator_edit.setText(" ")
        self.merge_separator_edit.setPlaceholderText("Separador entre elementos")
        layout.addWidget(QLabel("Separador:"))
        layout.addWidget(self.merge_separator_edit)
        
        self.enable_merge = QCheckBox("Activar unión de arrays")
        layout.addWidget(self.enable_merge)
        
        return tab
    
    def _create_right_panel(self) -> QWidget:
        """Crea el panel derecho con vista previa."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título
        preview_label = QLabel("👁️ Vista Previa")
        preview_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(preview_label)
        
        # Tabs de vista previa
        preview_tabs = QTabWidget()
        
        # Tab original
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setFont(QFont("Consolas", 10))
        preview_tabs.addTab(self.original_text, "📄 Original")
        
        # Tab resultado
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Consolas", 10))
        preview_tabs.addTab(self.result_text, "✨ Resultado")
        
        # Tab log de operaciones
        self.operations_log = QTextEdit()
        self.operations_log.setReadOnly(True)
        self.operations_log.setFont(QFont("Consolas", 9))
        preview_tabs.addTab(self.operations_log, "📋 Log Operaciones")
        
        layout.addWidget(preview_tabs)
        
        return panel
    
    def _load_file(self):
        """Carga un archivo JSON o NDJSON."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo JSON/NDJSON",
            "",
            "JSON Files (*.json *.ndjson *.jsonl);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Mostrar indicador de carga
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.progress_bar.setFormat("Cargando archivo...")
        
        # Cargar en un hilo separado
        self.loader = FileLoader(file_path)
        self.loader.progress_update.connect(self._on_load_progress)
        self.loader.finished.connect(self._on_load_finished)
        self.loader.start()
    
    def _on_load_progress(self, message: str):
        """Maneja actualizaciones de progreso durante la carga."""
        self.progress_bar.setFormat(message)
    
    def _on_load_finished(self, data: Any, file_path: str, message: str):
        """Maneja la finalización de la carga."""
        self.progress_bar.setVisible(False)
        
        if data is not None:
            self.current_data = data
            self.original_data = json.loads(json.dumps(data)) if len(str(data)) < 1000000 else data  # Deep copy solo para archivos pequeños
            self.file_path = file_path
            
            # Limpiar historial de operaciones al cargar nuevo archivo
            self.operations_history = []
            
            # Log de carga del archivo
            load_log = f"""
=== ARCHIVO CARGADO ===
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Archivo: {os.path.basename(file_path)}
Ruta: {file_path}
Tipo: {'NDJSON' if file_path.endswith(('.ndjson', '.jsonl')) else 'JSON'}
Elementos: {len(data) if isinstance(data, list) else 'Objeto único'}
Tamaño: {len(str(data)):,} caracteres
Estado: ✅ {message}
{'='*50}
"""
            self.operations_history.append(load_log)
            self._update_operations_log()
            
            self._update_ui_after_load()
            
            # Mostrar mensaje de éxito si hay limitaciones
            if "primeras" in message:
                QMessageBox.information(self, "Información", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def _update_ui_after_load(self):
        """Actualiza la UI después de cargar un archivo."""
        if not self.current_data:
            return
        
        # Actualizar etiquetas
        filename = os.path.basename(self.file_path) if self.file_path else "Sin nombre"
        self.file_label.setText(f"📁 {filename}")
        
        # Estadísticas
        if isinstance(self.current_data, list):
            stats = f"📊 Tipo: Array con {len(self.current_data)} elementos"
        elif isinstance(self.current_data, dict):
            stats = f"📊 Tipo: Objeto con {len(self.current_data)} claves"
        else:
            stats = f"📊 Tipo: {type(self.current_data).__name__}"
        
        self.stats_label.setText(stats)
        
        # Cargar estructura (solo los primeros elementos para archivos grandes)
        self.structure_viewer.clear()
        
        # Cargar la estructura completa para análisis del esquema
        self.structure_viewer.load_json_structure(self.current_data)
        
        # Mostrar JSON original (limitado para archivos grandes)
        try:
            if isinstance(self.current_data, list) and len(self.current_data) > 100:
                # Para arrays grandes, mostrar solo una muestra
                preview_data = {
                    "info": f"Array con {len(self.current_data)} elementos (mostrando solo los primeros 3)",
                    "muestra": self.current_data[:3]
                }
                json_text = json.dumps(preview_data, indent=2, ensure_ascii=False)
            else:
                json_text = json.dumps(self.current_data, indent=2, ensure_ascii=False)
            
            # Limitar tamaño del texto mostrado
            if len(json_text) > 50000:
                json_text = json_text[:50000] + "\n\n... (contenido truncado para mejor rendimiento)"
            
            self.original_text.setPlainText(json_text)
        except Exception as e:
            self.original_text.setPlainText(f"Error al mostrar contenido: {str(e)}")
        
        # Habilitar botones
        self.save_btn.setEnabled(True)
        self.save_as_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)
    
    def _select_all_keys(self):
        """Selecciona todas las claves en el visualizador."""
        self.structure_viewer.select_all_keys()
        self._update_selected_keys_list()
    
    def _clear_selection(self):
        """Limpia la selección de claves."""
        self.structure_viewer.clear_selection()
        self.selected_keys_list.clear()
    
    def _update_selected_keys_list(self):
        """Actualiza la lista visual de claves seleccionadas."""
        selected_keys = self.structure_viewer.get_selected_keys()
        self.selected_keys_list.clear()
        for key in selected_keys:
            self.selected_keys_list.addItem(key)
    
    def _remove_selected_keys(self):
        """Elimina las claves seleccionadas del JSON."""
        selected_keys = self.structure_viewer.get_selected_keys()
        if not selected_keys:
            QMessageBox.information(self, "Info", "No hay claves seleccionadas para eliminar")
            return
        
        self._update_selected_keys_list()
        # Aplicar los cambios automáticamente
        self._apply_changes()
    
    def _apply_changes(self):
        """Aplica todos los cambios configurados."""
        if not self.current_data:
            QMessageBox.warning(self, "Advertencia", "No hay datos cargados")
            return
        
        # Recopilar operaciones
        operations = {}
        
        # Claves a eliminar
        selected_keys = self.structure_viewer.get_selected_keys()
        if selected_keys:
            operations['remove_keys'] = selected_keys
        
        # Filtro por longitud
        if self.enable_length_filter.isChecked():
            operations['filter_by_length'] = {
                'min': self.min_length_spin.value(),
                'max': self.max_length_spin.value() if self.max_length_spin.value() > 0 else None
            }
        
        # Filtro por contenido
        if self.enable_content_filter.isChecked() and self.filter_key_edit.text():
            operations['filter_by_key_content'] = {
                'key': self.filter_key_edit.text(),
                'value': self.filter_value_edit.text(),
                'operation': self.filter_operation_combo.currentText()
            }
        
        # Unir arrays
        if self.enable_merge.isChecked() and self.merge_keys_edit.text():
            keys_to_merge = [k.strip() for k in self.merge_keys_edit.text().split(',')]
            operations['merge_text_arrays'] = keys_to_merge
        
        # Siempre limpiar objetos vacíos
        operations['remove_empty'] = True
        
        if not operations:
            QMessageBox.information(self, "Info", "No hay operaciones configuradas")
            return
        
        # Log antes de ejecutar
        pre_operation_log = f"""
=== INICIANDO OPERACIONES ===
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Datos de entrada: {len(self.current_data) if isinstance(self.current_data, list) else 'Objeto único'} elementos
Tamaño entrada: {len(str(self.current_data)):,} caracteres

Configuración:
{self._get_applied_operations_summary()}
{'='*50}
"""
        self.operations_history.append(pre_operation_log)
        self._update_operations_log()
        
        # Ejecutar limpieza sobre TODO el conjunto de datos
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        
        # IMPORTANTE: Usar self.current_data completo, no una muestra
        self.worker = JSONCleaningWorker(self.current_data, operations)
        self.worker.progress_update.connect(self._on_progress_update)
        self.worker.finished.connect(self._on_cleaning_finished)
        self.worker.start()
    
    def _on_progress_update(self, message: str):
        """Maneja actualizaciones de progreso."""
        self.progress_bar.setFormat(message)
    
    def _on_cleaning_finished(self, result: Any, success: bool, message: str):
        """Maneja la finalización de la limpieza."""
        self.progress_bar.setVisible(False)
        
        if success:
            # Guardar estado anterior para el log
            original_size = len(str(self.current_data))
            
            # Actualizar datos
            self.current_data = result
            
            # Mostrar resultado
            try:
                if isinstance(result, list) and len(result) > 100:
                    # Para arrays grandes, mostrar resumen + muestra
                    preview_data = {
                        "info": f"Array procesado con {len(result)} elementos (mostrando primeros 3)",
                        "muestra": result[:3]
                    }
                    result_text = json.dumps(preview_data, indent=2, ensure_ascii=False)
                else:
                    result_text = json.dumps(result, indent=2, ensure_ascii=False)
                
                # Limitar tamaño para mejor rendimiento
                if len(result_text) > 50000:
                    result_text = result_text[:50000] + "\n\n... (resultado truncado para visualización)"
                
                self.result_text.setPlainText(result_text)
            except Exception as e:
                self.result_text.setPlainText(f"Error al mostrar resultado: {str(e)}")
            
            # Actualizar estructura del esquema con los nuevos datos
            self.structure_viewer.load_json_structure(self.current_data)
            
            # Actualizar log de operaciones
            new_size = len(str(result))
            reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
            
            operation_summary = f"""
=== OPERACIÓN COMPLETADA ===
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Archivo: {os.path.basename(self.file_path) if self.file_path else 'Sin nombre'}
Tamaño original: {original_size:,} caracteres
Tamaño resultado: {new_size:,} caracteres  
Reducción: {reduction:.1f}%

Operaciones aplicadas:
{self._get_applied_operations_summary()}

Estado: ✅ {message}
{'='*50}
"""
            
            self.operations_history.append(operation_summary)
            self._update_operations_log()
            
            QMessageBox.information(self, "Éxito", f"{message}\nReducción de tamaño: {reduction:.1f}%")
        else:
            error_log = f"""
=== ERROR EN OPERACIÓN ===
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: ❌ {message}
{'='*50}
"""
            self.operations_history.append(error_log)
            self._update_operations_log()
            QMessageBox.critical(self, "Error", message)
    
    def _get_applied_operations_summary(self) -> str:
        """Genera un resumen de las operaciones que se aplicaron."""
        operations = []
        
        # Claves eliminadas
        selected_keys = self.structure_viewer.get_selected_keys()
        if selected_keys:
            operations.append(f"• Claves eliminadas: {', '.join(list(selected_keys)[:5])}{'...' if len(selected_keys) > 5 else ''}")
        
        # Filtro por longitud
        if self.enable_length_filter.isChecked():
            min_len = self.min_length_spin.value()
            max_len = self.max_length_spin.value()
            operations.append(f"• Filtro de longitud: {min_len}-{max_len} caracteres")
        
        # Filtro por contenido
        if self.enable_content_filter.isChecked() and self.filter_key_edit.text():
            operations.append(f"• Filtro de contenido: {self.filter_key_edit.text()} {self.filter_operation_combo.currentText()} '{self.filter_value_edit.text()}'")
        
        # Unir arrays
        if self.enable_merge.isChecked() and self.merge_keys_edit.text():
            operations.append(f"• Arrays unidos: {self.merge_keys_edit.text()}")
        
        operations.append("• Objetos vacíos eliminados")
        
        return '\n'.join(operations) if operations else "No se aplicaron operaciones específicas"
    
    def _update_operations_log(self):
        """Actualiza el log de operaciones en la UI."""
        log_text = '\n'.join(self.operations_history)
        self.operations_log.setPlainText(log_text)
        
        # Scroll al final para mostrar la operación más reciente
        cursor = self.operations_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.operations_log.setTextCursor(cursor)
    
    def _save_file(self):
        """Guarda el archivo actual."""
        if not self.file_path:
            self._save_file_as()
            return
        
        self._write_file(self.file_path)
    
    def _save_file_as(self):
        """Guarda el archivo con un nuevo nombre."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo JSON/NDJSON",
            "",
            "JSON Files (*.json);;NDJSON Files (*.ndjson);;All Files (*)"
        )
        
        if file_path:
            self._write_file(file_path)
            self.file_path = file_path
            self._update_ui_after_load()
    
    def _write_file(self, file_path: str):
        """Escribe el archivo al disco."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.ndjson') or file_path.endswith('.jsonl'):
                    # Escribir como NDJSON
                    if isinstance(self.current_data, list):
                        for item in self.current_data:
                            f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    else:
                        f.write(json.dumps(self.current_data, ensure_ascii=False) + '\n')
                else:
                    # Escribir como JSON
                    json.dump(self.current_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Éxito", f"Archivo guardado: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar archivo: {str(e)}")