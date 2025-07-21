#!/usr/bin/env python3
"""
Pestaña de unificación de archivos NDJSON para Biblioperson.

Este módulo contiene la interfaz para unificar múltiples archivos NDJSON
generados por el procesamiento en un solo archivo consolidado.
"""

import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QFileDialog, QCheckBox, QGroupBox,
    QFrame, QTextEdit, QProgressBar, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QObject
from PySide6.QtGui import QFont

# Importar el unificador
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from dataset.scripts.unify_ndjson import NDJSONUnifier


class UnificationWorker(QObject):
    """Worker para ejecutar la unificación en un hilo separado."""
    
    progress_update = Signal(str)  # Mensaje de progreso
    unification_finished = Signal(bool, str)  # (éxito, mensaje)
    
    def __init__(self, input_dir: str, output_file: str, recursive: bool = True, output_format: str = "ndjson"):
        super().__init__()
        self.input_dir = input_dir
        self.output_file = output_file
        self.recursive = recursive
        self.output_format = output_format.lower() # Asegurar minúsculas: 'json' o 'ndjson'
        
    def run(self):
        """Ejecuta la unificación."""
        try:
            self.progress_update.emit(f"Iniciando unificación de archivos a formato {self.output_format.upper()}...")
            
            # Crear unificador
            unifier = NDJSONUnifier(
                input_dir=self.input_dir,
                output_file=self.output_file,
                recursive=self.recursive,
                output_format=self.output_format # Pasar el formato al unificador
            )
            
            # Ejecutar unificación
            success = unifier.run()
            
            if success:
                stats = unifier.stats
                message = f"Unificación exitosa: {stats['files_processed']} archivos procesados, {stats['total_entries']} entradas totales"
                self.unification_finished.emit(True, message)
            else:
                self.unification_finished.emit(False, "Error durante la unificación")
                
        except Exception as e:
            self.progress_update.emit(f"❌ Error inesperado: {str(e)}")
            self.unification_finished.emit(False, f"Error inesperado: {str(e)}")


class UnifyTab(QWidget):
    """
    Pestaña para unificación de archivos NDJSON.
    
    Esta clase implementa la interfaz que permite a los usuarios:
    - Seleccionar directorio de entrada con archivos NDJSON
    - Especificar archivo de salida unificado
    - Configurar opciones de unificación
    - Monitorear el progreso de la unificación
    """
    
    def __init__(self):
        super().__init__()
        
        # Variables de estado
        self.input_dir: Optional[str] = None
        self.output_file: Optional[str] = None
        
        # Worker y thread para unificación
        self.unification_thread: Optional[QThread] = None
        self.unification_worker: Optional[UnificationWorker] = None
        
        # Configurar la interfaz
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Configura todos los elementos de la interfaz de usuario."""
        # Layout principal usando splitter
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Título
        title_label = QLabel("Unificación de Archivos NDJSON")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 15px; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        main_layout.addWidget(title_label)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel de configuración (izquierda)
        config_panel = self._create_config_panel()
        main_splitter.addWidget(config_panel)
        
        # Panel de logs (derecha)
        logs_panel = self._create_logs_panel()
        main_splitter.addWidget(logs_panel)
        
        # Configurar proporciones del splitter
        main_splitter.setSizes([400, 600])
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
    
    def _create_config_panel(self) -> QWidget:
        """Crea el panel de configuración."""
        panel = QWidget()
        panel.setMaximumWidth(450)
        panel.setMinimumWidth(350)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # === Sección de Entrada ===
        input_group = QGroupBox("Directorio de Entrada")
        input_layout = QVBoxLayout(input_group)
        
        # Selector de directorio de entrada
        input_dir_layout = QHBoxLayout()
        self.input_dir_edit = QLineEdit()
        self.input_dir_edit.setPlaceholderText("Selecciona directorio con archivos NDJSON...")
        self.input_dir_edit.setReadOnly(True)
        
        self.browse_input_btn = QPushButton("Examinar")
        self.browse_input_btn.setMaximumWidth(100)
        
        input_dir_layout.addWidget(QLabel("Directorio:"))
        input_dir_layout.addWidget(self.input_dir_edit)
        input_dir_layout.addWidget(self.browse_input_btn)
        
        input_layout.addLayout(input_dir_layout)
        layout.addWidget(input_group)
        
        # === Sección de Configuración ===
        config_group = QGroupBox("Configuración")
        config_layout = QVBoxLayout(config_group)
        
        # Checkbox para búsqueda recursiva
        self.recursive_check = QCheckBox("Búsqueda recursiva en subdirectorios")
        self.recursive_check.setChecked(True)
        self.recursive_check.setToolTip("Buscar archivos NDJSON en todas las subcarpetas")
        config_layout.addWidget(self.recursive_check)

        # Selector de formato de salida
        output_format_layout = QHBoxLayout()
        output_format_label = QLabel("Formato de Salida:")
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["NDJSON (líneas JSON)", "JSON (array único)"])
        self.output_format_combo.setToolTip("Elige el formato para el archivo unificado de salida")
        output_format_layout.addWidget(output_format_label)
        output_format_layout.addWidget(self.output_format_combo)
        config_layout.addLayout(output_format_layout)
        
        layout.addWidget(config_group)
        
        # === Sección de Salida ===
        output_group = QGroupBox("Archivo de Salida")
        output_layout = QVBoxLayout(output_group)
        
        # Selector de archivo de salida
        output_file_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setPlaceholderText("Archivo NDJSON unificado de salida...")
        
        self.browse_output_btn = QPushButton("Examinar")
        self.browse_output_btn.setMaximumWidth(100)
        
        output_file_layout.addWidget(QLabel("Archivo:"))
        output_file_layout.addWidget(self.output_file_edit)
        output_file_layout.addWidget(self.browse_output_btn)
        
        output_layout.addLayout(output_file_layout)
        layout.addWidget(output_group)
        
        # === Botón de Unificación ===
        self.unify_btn = QPushButton("🔗 Iniciar Unificación")
        self.unify_btn.setMinimumHeight(50)
        self.unify_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        layout.addWidget(self.unify_btn)
        
        # === Barra de Progreso ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Espaciador
        layout.addStretch()
        
        return panel
    
    def _create_logs_panel(self) -> QWidget:
        """Crea el panel de logs."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título del panel
        logs_title = QLabel("Logs de Unificación")
        logs_title.setFont(QFont("Arial", 12, QFont.Bold))
        logs_title.setStyleSheet("color: #ffffff; margin-bottom: 10px; background-color: rgba(52, 73, 94, 0.8); padding: 6px; border-radius: 4px;")
        layout.addWidget(logs_title)
        
        # Área de texto para logs
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 9))
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Mensaje inicial
        self.logs_text.append("=== Unificador de Archivos NDJSON ===")
        self.logs_text.append("Selecciona un directorio de entrada y archivo de salida para comenzar.")
        self.logs_text.append("")
        
        layout.addWidget(self.logs_text)
        
        # Panel de estado inferior
        status_frame = QFrame()
        status_frame.setMaximumHeight(60)
        status_layout = QHBoxLayout(status_frame)
        
        # Indicador de estado
        self.status_label = QLabel("Estado: Listo")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        # Botón para limpiar logs
        self.clear_logs_btn = QPushButton("Limpiar Logs")
        self.clear_logs_btn.setMaximumWidth(120)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.clear_logs_btn)
        
        layout.addWidget(status_frame)
        
        return panel
    
    def _setup_connections(self):
        """Configura las conexiones de señales y slots."""
        self.browse_input_btn.clicked.connect(self._browse_input_dir)
        self.browse_output_btn.clicked.connect(self._browse_output_file)
        self.unify_btn.clicked.connect(self._start_unification)
        self.clear_logs_btn.clicked.connect(self._clear_logs)
        
        # Conexiones para validación y actualización de UI
        self.input_dir_edit.textChanged.connect(self._validate_inputs)
        self.output_file_edit.textChanged.connect(self._validate_inputs)
        self.output_format_combo.currentTextChanged.connect(self._update_output_placeholder_and_validate)

    def _update_output_placeholder_and_validate(self):
        """Actualiza el placeholder y valida las entradas."""
        self._update_output_file_placeholder()
        self._validate_inputs()

    def _update_output_file_placeholder(self):
        """Actualiza el placeholder del campo de archivo de salida según el formato seleccionado."""
        if self.output_format_combo.currentText() == "JSON (array único)":
            self.output_file_edit.setPlaceholderText("Archivo JSON unificado de salida (.json)...")
        else:
            self.output_file_edit.setPlaceholderText("Archivo NDJSON unificado de salida (.ndjson)...")

    def _browse_input_dir(self):
        """Abre diálogo para seleccionar directorio de entrada."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar directorio con archivos NDJSON"
        )
        
        if dir_path:
            self.input_dir_edit.setText(dir_path)
            self.input_dir = dir_path
            self._log_message(f"Directorio de entrada: {dir_path}")
    
    def _browse_output_file(self):
        """Abre diálogo para seleccionar archivo de salida."""
        current_output_file = self.output_file_edit.text()
        directory = os.path.dirname(current_output_file) if current_output_file else ""
        
        if self.output_format_combo.currentText() == "JSON (array único)":
            default_suffix = ".json"
            file_filter = "JSON (*.json);;Todos los archivos (*.*)"
        else:
            default_suffix = ".ndjson"
            file_filter = "NDJSON (*.ndjson);;Todos los archivos (*.*)"
            
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Especificar archivo de salida unificado",
            directory,
            file_filter,
            file_filter.split(";;")[0] # Usar el primer filtro como seleccionado por defecto
        )
        
        if file_path:
            # Asegurar que tenga la extensión correcta si el usuario no la puso
            if not file_path.lower().endswith(default_suffix):
                file_path += default_suffix
            self.output_file_edit.setText(file_path)
            self.output_file = file_path
            self._log_message(f"Archivo de salida seleccionado: {file_path}")
    
    def _validate_inputs(self):
        """Valida las entradas y habilita/deshabilita el botón de unificación."""
        has_input = bool(self.input_dir_edit.text().strip())
        has_output = bool(self.output_file_edit.text().strip())
        
        self.unify_btn.setEnabled(has_input and has_output)
        
        if has_input and has_output:
            self.status_label.setText("Estado: Listo para unificar")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.status_label.setText("Estado: Configuración incompleta")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def _start_unification(self):
        """Inicia la unificación de archivos."""
        if self.unification_thread and self.unification_thread.isRunning():
            self._log_message("⚠️ Ya hay un proceso de unificación en curso")
            return
        
        # Obtener parámetros
        input_dir = self.input_dir_edit.text().strip()
        output_file = self.output_file_edit.text().strip()
        recursive = self.recursive_check.isChecked()
        output_format_text = self.output_format_combo.currentText()
        
        selected_format = "json" if "JSON (array único)" in output_format_text else "ndjson"

        # Validaciones básicas
        if not input_dir or not output_file:
            self._log_message("❌ Error: Directorio de entrada y archivo de salida son requeridos")
            QMessageBox.critical(
                self,
                "Error de Validación",
                "Por favor, especifica el directorio de entrada y el archivo de salida."
            )
            return
        
        if not Path(input_dir).exists() or not Path(input_dir).is_dir():
            self._log_message(f"❌ Error: Directorio de entrada no válido: {input_dir}")
            QMessageBox.critical(
                self,
                "Error de Directorio",
                f"El directorio de entrada especificado no existe o no es válido:\n{input_dir}"
            )
            return

        # Confirmación si el archivo de salida ya existe
        if Path(output_file).exists():
            reply = QMessageBox.question(
                self,
                "Confirmar Sobrescritura",
                f"El archivo de salida \"{Path(output_file).name}\" ya existe.\n¿Deseas sobrescribirlo?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                self._log_message("Unificación cancelada por el usuario.")
                return
        
        self._log_message(f"=== INICIANDO UNIFICACIÓN ({selected_format.upper()}) ===")
        self._log_message(f"📁 Directorio de entrada: {input_dir}")
        self._log_message(f"💾 Archivo de salida: {output_file}")
        self._log_message(f"🔄 Búsqueda recursiva: {'Activada' if recursive else 'Desactivada'}")
        self._log_message(f"📄 Formato de salida: {selected_format.upper()}")
        self._log_message("")
        
        # Configurar UI para unificación
        self.unify_btn.setEnabled(False)
        self.unify_btn.setText("⏳ Unificando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        
        # Crear worker y thread
        self.unification_worker = UnificationWorker(
            input_dir=input_dir,
            output_file=output_file,
            recursive=recursive,
            output_format=selected_format # Pasar el formato aquí
        )
        
        self.unification_thread = QThread()
        self.unification_worker.moveToThread(self.unification_thread)
        
        # Conectar señales
        self.unification_thread.started.connect(self.unification_worker.run)
        self.unification_worker.progress_update.connect(self._on_progress_update)
        self.unification_worker.unification_finished.connect(self._on_unification_finished)
        
        # Iniciar thread
        self.unification_thread.start()
        
        # Actualizar estado
        self.status_label.setText("Estado: Unificando...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
    
    def _on_progress_update(self, message: str):
        """Maneja actualizaciones de progreso del worker."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_message(f"[{timestamp}] {message}")
    
    def _on_unification_finished(self, success: bool, message: str):
        """Maneja la finalización de la unificación."""
        # Limpiar thread
        if self.unification_thread:
            self.unification_thread.quit()
            self.unification_thread.wait()
            self.unification_thread = None
        self.unification_worker = None
        
        # Restaurar UI
        self.unify_btn.setEnabled(True)
        self.unify_btn.setText("🔗 Iniciar Unificación")
        self.progress_bar.setVisible(False)
        
        # Mostrar resultado
        timestamp = datetime.now().strftime("%H:%M:%S")
        if success:
            self._log_message(f"[{timestamp}] ✅ {message}")
            self.status_label.setText("Estado: Unificación completada exitosamente")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            # Mostrar diálogo de éxito
            QMessageBox.information(
                self,
                "Unificación Exitosa",
                f"Los archivos NDJSON se han unificado exitosamente.\n\n{message}"
            )
        else:
            self._log_message(f"[{timestamp}] ❌ {message}")
            self.status_label.setText("Estado: Error en unificación")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            # Mostrar diálogo de error
            QMessageBox.critical(
                self,
                "Error en Unificación",
                f"Ocurrió un error durante la unificación:\n\n{message}"
            )
        
        self._log_message("")
        self._log_message("=== UNIFICACIÓN FINALIZADA ===")
    
    def _clear_logs(self):
        """Limpia el área de logs."""
        self.logs_text.clear()
        self.logs_text.append("=== Logs limpiados ===")
        self._log_message("Listo para nuevas operaciones.")
    
    def _log_message(self, message: str):
        """Agrega un mensaje al área de logs."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.append(f"[{timestamp}] {message}")
        # Auto-scroll al final
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum()) 