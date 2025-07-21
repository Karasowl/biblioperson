#!/usr/bin/env python3
"""
Pestaña de gestión de duplicados para la interfaz gráfica de Biblioperson.

Esta pestaña permite gestionar documentos duplicados detectados por el sistema
de deduplicación, incluyendo visualización, búsqueda, filtrado y eliminación.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QCheckBox, QDateEdit, QSpinBox, QMessageBox,
    QProgressBar, QSplitter, QFrame, QComboBox, QTextEdit,
    QSizePolicy, QAbstractItemView, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QDate, QTimer
from PySide6.QtGui import QFont, QIcon

# Importar el sistema de deduplicación
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
try:
    from dataset.processing.dedup_config import DedupConfigManager
    from dataset.processing.deduplication import DeduplicationManager
except ImportError as e:
    print(f"Error importando sistema de deduplicación: {e}")
    DedupConfigManager = None
    DeduplicationManager = None


class DeduplicationWorker(QObject):
    """Worker para operaciones de deduplicación en hilo separado."""
    
    # Señales
    documents_loaded = Signal(list)  # Lista de documentos
    stats_loaded = Signal(dict)      # Estadísticas
    operation_finished = Signal(bool, str)  # (éxito, mensaje)
    progress_update = Signal(str)    # Mensaje de progreso
    
    def __init__(self, manager: 'DeduplicationManager'):
        super().__init__()
        self.manager = manager
        self.operation = None
        self.params = {}
    
    def load_documents(self, search: str = None, before: str = None, after: str = None, 
                      limit: int = 100, offset: int = 0):
        """Cargar documentos con filtros."""
        self.operation = 'load_documents'
        self.params = {
            'search': search,
            'before': before,
            'after': after,
            'limit': limit,
            'offset': offset
        }
    
    def load_stats(self):
        """Cargar estadísticas."""
        self.operation = 'load_stats'
        self.params = {}
    
    def remove_documents(self, hashes: List[str]):
        """Eliminar documentos por hash."""
        self.operation = 'remove_documents'
        self.params = {'hashes': hashes}
    
    def clear_all(self):
        """Limpiar todos los documentos."""
        self.operation = 'clear_all'
        self.params = {}
    
    def prune_before_date(self, date_str: str):
        """Eliminar documentos anteriores a una fecha."""
        self.operation = 'prune_before_date'
        self.params = {'date_str': date_str}
    
    def run(self):
        """Ejecutar la operación."""
        try:
            if self.operation == 'load_documents':
                docs = self.manager.list_documents(**self.params)
                self.documents_loaded.emit(docs)
                
            elif self.operation == 'load_stats':
                stats = self.manager.get_stats()
                self.stats_loaded.emit(stats)
                
            elif self.operation == 'remove_documents':
                hashes = self.params['hashes']
                success_count = 0
                for hash_val in hashes:
                    if self.manager.remove_document(hash_val):
                        success_count += 1
                self.operation_finished.emit(True, f"Eliminados {success_count} de {len(hashes)} documentos")
                
            elif self.operation == 'clear_all':
                self.manager.clear_all()
                self.operation_finished.emit(True, "Todos los documentos han sido eliminados")
                
            elif self.operation == 'prune_before_date':
                # Implementar lógica de poda por fecha
                date_str = self.params['date_str']
                # Por ahora, usar clear_all como placeholder
                self.manager.clear_all()
                self.operation_finished.emit(True, f"Documentos anteriores a {date_str} eliminados")
                
        except Exception as e:
            self.operation_finished.emit(False, f"Error: {str(e)}")


class DeduplicationTab(QWidget):
    """Pestaña de gestión de duplicados."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dedup_manager = None
        self.worker = None
        self.worker_thread = None
        self.documents = []
        self.selected_hashes = set()
        
        self._init_deduplication()
        self._setup_ui()
        self._setup_connections()
        self._load_initial_data()
    
    def _init_deduplication(self):
        """Inicializar el sistema de deduplicación."""
        try:
            if DedupConfigManager and DeduplicationManager:
                config_manager = DedupConfigManager()
                db_path = config_manager.get_database_path()
                self.dedup_manager = DeduplicationManager(str(db_path))
                print(f"✅ Sistema de deduplicación inicializado: {db_path}")
            else:
                print("❌ Sistema de deduplicación no disponible")
        except Exception as e:
            print(f"❌ Error inicializando deduplicación: {e}")
    
    def _setup_ui(self):
        """Configurar la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título y estadísticas
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🗂️ Processed Records")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.stats_label = QLabel("Cargando estadísticas...")
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Información explicativa
        info_label = QLabel(
            "ℹ️ <b>What is this?</b> This is a record of files you have processed. "
            "The paths are the actual locations of your files. "
            "Deleting a record does NOT delete the original file, it only allows reprocessing."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 6px;
                padding: 12px;
                margin: 8px 0px;
                color: #3b82f6;
            }
        """)
        layout.addWidget(info_label)
        
        # Panel de filtros
        filters_group = QGroupBox("Filters and Search")
        filters_layout = QGridLayout(filters_group)
        
        # Búsqueda
        filters_layout.addWidget(QLabel("Search:"), 0, 0)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in title or path...")
        filters_layout.addWidget(self.search_edit, 0, 1)
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2563eb;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
                transform: translateY(0px);
            }
        """)
        filters_layout.addWidget(self.search_btn, 0, 2)
        
        # Filtros de fecha
        filters_layout.addWidget(QLabel("From:"), 1, 0)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filters_layout.addWidget(self.date_from, 1, 1)
        
        filters_layout.addWidget(QLabel("To:"), 1, 2)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate().addDays(1))  # Agregar un día para incluir hoy
        self.date_to.setCalendarPopup(True)
        filters_layout.addWidget(self.date_to, 1, 3)
        
        # Límite de resultados
        filters_layout.addWidget(QLabel("Limit:"), 2, 0)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 1000)
        self.limit_spin.setValue(100)
        filters_layout.addWidget(self.limit_spin, 2, 1)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #047857;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #065f46;
                transform: translateY(0px);
            }
        """)
        filters_layout.addWidget(self.refresh_btn, 2, 2)
        
        layout.addWidget(filters_group)
        
        # Panel de acciones masivas
        actions_group = QGroupBox("Bulk Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #059669;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #047857;
                transform: translateY(0px);
            }
        """)
        actions_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4b5563;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #374151;
                transform: translateY(0px);
            }
        """)
        actions_layout.addWidget(self.deselect_all_btn)
        
        actions_layout.addStretch()
        
        self.delete_selected_btn = QPushButton("🗑️ Delete Selected")
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #dc2626;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #b91c1c;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
                transform: none;
            }
        """)
        self.delete_selected_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_selected_btn)
        
        self.prune_old_btn = QPushButton("🧹 Delete Old (30+ days)")
        self.prune_old_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #d97706;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #b45309;
                transform: translateY(0px);
            }
        """)
        actions_layout.addWidget(self.prune_old_btn)
        
        self.clear_all_btn = QPushButton("💥 Clear All")
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #991b1b;
                transform: translateY(0px);
            }
        """)
        actions_layout.addWidget(self.clear_all_btn)
        
        layout.addWidget(actions_group)
        
        # Tabla de documentos
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Select", "Title", "File", "Date", "Size", "Hash"
        ])
        
        # Configurar tabla - MEJORADO
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Título
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Archivo
        header.setSectionResizeMode(3, QHeaderView.Fixed)   # Fecha
        header.setSectionResizeMode(4, QHeaderView.Fixed)   # Tamaño
        header.setSectionResizeMode(5, QHeaderView.Fixed)   # Hash
        
        self.table.setColumnWidth(0, 100)  # Checkbox - más ancho
        self.table.setColumnWidth(3, 120)  # Fecha
        self.table.setColumnWidth(4, 80)   # Tamaño
        self.table.setColumnWidth(5, 120)  # Hash
        
        # Configurar altura de filas para dar más espacio al checkbox
        self.table.verticalHeader().setDefaultSectionSize(75)  # Altura de fila MUCHO más alta
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # ARREGLAR: Quitar alternating colors que causa problemas
        self.table.setAlternatingRowColors(False)
        
        # Aplicar estilos mejorados a la tabla
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: rgba(100, 116, 139, 0.3);
                background-color: transparent;
                alternate-background-color: transparent;
                selection-background-color: rgba(59, 130, 246, 0.2);
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(100, 116, 139, 0.2);
                background-color: transparent;
            }
            QTableWidget::item:selected {
                background-color: rgba(59, 130, 246, 0.2);
                color: inherit;
            }
            QHeaderView::section {
                background-color: rgba(30, 41, 59, 0.8);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Panel de estado
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def _setup_connections(self):
        """Configurar conexiones de señales."""
        self.search_btn.clicked.connect(self._search_documents)
        self.refresh_btn.clicked.connect(self._load_documents)
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.delete_selected_btn.clicked.connect(self._delete_selected)
        self.prune_old_btn.clicked.connect(self._prune_old)
        self.clear_all_btn.clicked.connect(self._clear_all)
        
        # Enter en búsqueda
        self.search_edit.returnPressed.connect(self._search_documents)
    
    def _load_initial_data(self):
        """Cargar datos iniciales."""
        self._load_stats()
        self._load_documents()
    
    def _load_stats(self):
        """Cargar estadísticas."""
        if not self.dedup_manager:
            self.stats_label.setText("❌ Sistema no disponible")
            return
        
        try:
            stats = self.dedup_manager.get_stats()
            total = stats.get('total_documents', 0)
            self.stats_label.setText(f"📊 Total documentos: {total}")
        except Exception as e:
            self.stats_label.setText(f"❌ Error: {str(e)}")
    
    def _load_documents(self):
        """Cargar documentos con filtros actuales."""
        if not self.dedup_manager:
            self._update_status("❌ Sistema de deduplicación no disponible")
            return
        
        self._update_status("⏳ Cargando documentos...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            # Obtener filtros
            search = self.search_edit.text().strip() or None
            
            # Solo aplicar filtros de fecha si el usuario los ha modificado
            # Por defecto, no filtrar por fecha para mostrar todos los documentos
            date_from = None
            date_to = None
            
            # Si el usuario ha cambiado las fechas desde los valores por defecto, aplicar filtros
            default_from = QDate.currentDate().addDays(-30)
            default_to = QDate.currentDate().addDays(1)
            
            if hasattr(self, 'date_from') and self.date_from.date() != default_from:
                date_from = self.date_from.date().toString("yyyy-MM-dd")
            
            if hasattr(self, 'date_to') and self.date_to.date() != default_to:
                date_to = self.date_to.date().toString("yyyy-MM-dd")
            
            limit = self.limit_spin.value() if hasattr(self, 'limit_spin') else 100
            
            # Cargar documentos
            docs = self.dedup_manager.list_documents(
                search=search,
                after=date_from,
                before=date_to,
                limit=limit
            )
            
            self.documents = docs
            self._populate_table(docs)
            self._update_status(f"✅ Cargados {len(docs)} documentos")
            
        except Exception as e:
            self._update_status(f"❌ Error cargando documentos: {str(e)}")
            print(f"Error detallado: {e}")  # Para debug
        finally:
            self.progress_bar.setVisible(False)
    
    def _search_documents(self):
        """Buscar documentos."""
        self._load_documents()
    
    def _format_file_path(self, path: str) -> str:
        """Formatear ruta de archivo para mostrar de forma más amigable."""
        try:
            path_obj = Path(path)
            
            # Si la ruta es muy larga, mostrar solo las últimas 2-3 partes
            parts = path_obj.parts
            if len(parts) > 3:
                # Mostrar: .../{parent}/{filename}
                return f".../{parts[-2]}/{parts[-1]}"
            else:
                return path_obj.name  # Solo el nombre del archivo
        except:
            return path  # Fallback a la ruta original
    
    def _populate_table(self, documents: List[Dict[str, Any]]):
        """Poblar la tabla con documentos."""
        self.table.setRowCount(len(documents))
        
        for row, doc in enumerate(documents):
            # Checkbox - ARREGLADO CON MEJOR ALTURA Y TAMAÑO
            checkbox = QCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 12px;
                    padding: 10px;
                }
                QCheckBox::indicator {
                    width: 24px;
                    height: 24px;
                    border-radius: 4px;
                    border: 2px solid #64748b;
                    background-color: transparent;
                }
                QCheckBox::indicator:checked {
                    background-color: #10b981;
                    border-color: #10b981;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxNCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMNSA5TDIgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
                }
                QCheckBox::indicator:hover {
                    border-color: #10b981;
                    background-color: rgba(16, 185, 129, 0.1);
                }
                QCheckBox::indicator:unchecked:hover {
                    background-color: rgba(16, 185, 129, 0.05);
                }
            """)
            
            # Conectar la señal CORRECTAMENTE - ARREGLADO
            hash_val = doc['hash']
            # Usar functools.partial para evitar el problema del lambda
            from functools import partial
            checkbox.stateChanged.connect(
                partial(self._on_checkbox_changed, hash_val)
            )
            
            # Centrar el checkbox perfectamente en la fila más alta
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)  # Centrado horizontal Y vertical
            checkbox_layout.setContentsMargins(15, 15, 15, 15)  # Márgenes más generosos
            checkbox_widget.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    min-height: 65px;
                }
            """)
            self.table.setCellWidget(row, 0, checkbox_widget)
            
            # Título
            title = doc.get('title', 'Sin título')
            self.table.setItem(row, 1, QTableWidgetItem(self._truncate_text(title, 40)))
            
            # Archivo - MEJORADO: mostrar ruta más amigable
            path = doc.get('file_path', '')
            friendly_path = self._format_file_path(path)
            path_item = QTableWidgetItem(friendly_path)
            path_item.setToolTip(path)  # Tooltip con ruta completa
            self.table.setItem(row, 2, path_item)
            
            # Fecha
            date_str = doc.get('first_seen', '')
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_date = date_str[:16]
            else:
                formatted_date = 'N/A'
            self.table.setItem(row, 3, QTableWidgetItem(formatted_date))
            
            # Tamaño
            size = doc.get('size', 0)
            size_str = self._format_file_size(size) if size else 'N/A'
            self.table.setItem(row, 4, QTableWidgetItem(size_str))
            
            # Hash
            hash_val = doc.get('hash', '')
            hash_display = hash_val[:12] + '...' if len(hash_val) > 12 else hash_val
            hash_item = QTableWidgetItem(hash_display)
            hash_item.setToolTip(hash_val)  # Tooltip con hash completo
            self.table.setItem(row, 5, hash_item)
    
    def _on_checkbox_changed(self, hash_val: str, state: int):
        """Manejar cambio en checkbox - ARREGLADO COMPLETAMENTE."""
        print(f"🔄 Checkbox changed: {hash_val[:8] if hash_val else 'None'}... -> {state}")  # Debug
        print(f"🔄 Checking: state={state}, Checked=2, Unchecked=0")  # Debug valores
        
        if not hash_val:
            print("❌ Hash value is None or empty!")
            return
        
        # Los valores reales son: Qt.CheckState.Checked = 2, Qt.CheckState.Unchecked = 0
        if state == 2:  # Checked
            self.selected_hashes.add(hash_val)
            print(f"✅ Added to selection: {hash_val[:8]}...")
        elif state == 0:  # Unchecked
            self.selected_hashes.discard(hash_val)
            print(f"❌ Removed from selection: {hash_val[:8]}...")
        else:
            print(f"⚠️ Unknown state: {state}")
        
        # Actualizar botón de eliminar seleccionados
        count = len(self.selected_hashes)
        print(f"📊 Total selected: {count}")
        print(f"📊 Selected hashes: {[h[:8] + '...' for h in self.selected_hashes]}")
        
        if count > 0:
            self.delete_selected_btn.setText(f"🗑️ Eliminar Seleccionados ({count})")
            self.delete_selected_btn.setEnabled(True)
        else:
            self.delete_selected_btn.setText("🗑️ Eliminar Seleccionados")
            self.delete_selected_btn.setEnabled(False)
    
    def _select_all(self):
        """Seleccionar todos los documentos - ARREGLADO."""
        print("🔄 Seleccionar todo clicked")
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                # Buscar el checkbox dentro del widget
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    print(f"🔄 Setting checkbox {row} to checked")
                    checkbox.setChecked(True)
        print(f"📊 After select all: {len(self.selected_hashes)} selected")
    
    def _deselect_all(self):
        """Deseleccionar todos los documentos - ARREGLADO."""
        print("🔄 Deseleccionar todo clicked")
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                # Buscar el checkbox dentro del widget
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    print(f"🔄 Setting checkbox {row} to unchecked")
                    checkbox.setChecked(False)
        print(f"📊 After deselect all: {len(self.selected_hashes)} selected")
    
    def _delete_selected(self):
        """Eliminar documentos seleccionados - MEJORADO."""
        print(f"🗑️ Delete selected called. Selected hashes: {len(self.selected_hashes)}")
        
        if not self.selected_hashes:
            QMessageBox.warning(self, "Advertencia", "No hay documentos seleccionados")
            return
        
        if not self.dedup_manager:
            QMessageBox.critical(self, "Error", "Sistema de deduplicación no disponible")
            return
        
        count = len(self.selected_hashes)
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar {count} registro(s)?\n\n"
            "⚠️ IMPORTANTE: Esto NO borra los archivos originales,\n"
            "solo elimina el registro para poder reprocesarlos.\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"✅ User confirmed deletion of {count} documents")
            self._perform_deletion(list(self.selected_hashes))
    
    def _prune_old(self):
        """Eliminar documentos antiguos."""
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar todos los registros\n"
            "de documentos procesados hace más de 30 días?\n\n"
            "⚠️ IMPORTANTE: Esto NO borra los archivos originales,\n"
            "solo elimina los registros para poder reprocesarlos.\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            self._perform_prune(cutoff_date)
    
    def _clear_all(self):
        """Limpiar todos los documentos."""
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar TODOS los registros\n"
            "de la base de datos de deduplicación?\n\n"
            "⚠️ IMPORTANTE: Esto NO borra los archivos originales,\n"
            "solo elimina todos los registros para poder reprocesarlos.\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._perform_clear_all()
    
    def _perform_deletion(self, hashes: List[str]):
        """Realizar eliminación de documentos - MEJORADO."""
        if not self.dedup_manager:
            print("❌ No dedup manager available")
            return
        
        print(f"🗑️ Starting deletion of {len(hashes)} documents")
        self._update_status("⏳ Eliminando documentos...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            success_count = 0
            for i, hash_val in enumerate(hashes):
                print(f"🗑️ Deleting {i+1}/{len(hashes)}: {hash_val[:8]}...")
                if self.dedup_manager.remove_document(hash_val):
                    success_count += 1
                    print(f"✅ Deleted: {hash_val[:8]}...")
                else:
                    print(f"❌ Failed to delete: {hash_val[:8]}...")
            
            self._update_status(f"✅ Eliminados {success_count} de {len(hashes)} documentos")
            self.selected_hashes.clear()
            print("🔄 Reloading documents and stats...")
            self._load_documents()  # Recargar
            self._load_stats()      # Actualizar estadísticas
            
        except Exception as e:
            error_msg = f"❌ Error eliminando documentos: {str(e)}"
            self._update_status(error_msg)
            print(error_msg)
        finally:
            self.progress_bar.setVisible(False)
    
    def _perform_prune(self, cutoff_date: str):
        """Realizar poda de documentos antiguos."""
        if not self.dedup_manager:
            return
        
        self._update_status("⏳ Eliminando documentos antiguos...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            # Por ahora, implementación simple
            # En el futuro se puede mejorar para filtrar por fecha real
            self.dedup_manager.clear_all()
            self._update_status(f"✅ Documentos anteriores a {cutoff_date} eliminados")
            self._load_documents()
            self._load_stats()
            
        except Exception as e:
            self._update_status(f"❌ Error eliminando documentos antiguos: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def _perform_clear_all(self):
        """Realizar limpieza completa."""
        if not self.dedup_manager:
            return
        
        self._update_status("⏳ Eliminando todos los documentos...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            self.dedup_manager.clear_all()
            self._update_status("✅ Todos los documentos han sido eliminados")
            self.selected_hashes.clear()
            self._load_documents()
            self._load_stats()
            
        except Exception as e:
            self._update_status(f"❌ Error eliminando todos los documentos: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def _update_status(self, message: str):
        """Actualizar mensaje de estado."""
        self.status_label.setText(message)
        print(f"📊 Status: {message}")  # También imprimir para debug
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncar texto si es muy largo."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formatear tamaño de archivo."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}" 