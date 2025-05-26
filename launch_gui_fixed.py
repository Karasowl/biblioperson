#!/usr/bin/env python3
"""
Versión corregida de la GUI de Biblioperson que evita el problema de widgets eliminados.

Esta versión usa un enfoque más simple y directo para evitar los problemas de Qt.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional
import threading
import argparse
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLabel, QLineEdit, 
    QComboBox, QTextEdit, QFileDialog, QCheckBox, QGroupBox,
    QFrame, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QObject
from PySide6.QtGui import QFont

# Importar el backend de procesamiento
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from dataset.processing.profile_manager import ProfileManager
from dataset.scripts.process_file import core_process, ProcessingStats


class SimpleProcessingWorker(QObject):
    """Worker simplificado para procesamiento."""
    
    progress_update = Signal(str)
    processing_finished = Signal(bool, str)
    
    def __init__(self, manager, input_path, profile_name, output_path=None, 
                 verbose=False, language_override=None, author_override=None):
        super().__init__()
        self.manager = manager
        self.input_path = Path(input_path)
        self.profile_name = profile_name
        self.output_path = output_path
        self.verbose = verbose
        self.language_override = language_override
        self.author_override = author_override
        
    def run(self):
        """Ejecuta el procesamiento."""
        try:
            self.progress_update.emit("Iniciando procesamiento...")
            
            # Crear argumentos para core_process
            args = argparse.Namespace()
            args.input_path = str(self.input_path)
            args.profile = self.profile_name
            args.verbose = self.verbose
            args.encoding = "utf-8"
            args.force_type = None
            args.confidence_threshold = 0.5
            args.language_override = self.language_override
            args.author_override = self.author_override
            args.output = self.output_path
            
            self.progress_update.emit(f"Procesando: {self.input_path.name}")
            
            result_code, message, document_metadata, segments, segmenter_stats = core_process(
                manager=self.manager,
                input_path=self.input_path,
                profile_name_override=self.profile_name,
                output_spec=self.output_path,
                cli_args=args
            )
            
            if result_code.startswith('SUCCESS'):
                self.progress_update.emit(f"✅ Procesamiento exitoso")
                self.processing_finished.emit(True, "Procesamiento completado exitosamente")
            else:
                error_msg = message or f"Error: {result_code}"
                self.progress_update.emit(f"❌ Error: {error_msg}")
                self.processing_finished.emit(False, error_msg)
                
        except Exception as e:
            self.progress_update.emit(f"❌ Error inesperado: {str(e)}")
            self.processing_finished.emit(False, f"Error inesperado: {str(e)}")


class SimpleBibliopersonGUI(QMainWindow):
    """GUI simplificada y robusta para Biblioperson."""
    
    def __init__(self):
        super().__init__()
        
        # Configurar logger
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("Biblioperson - Procesador de Datasets (Versión Corregida)")
        self.setMinimumSize(QSize(1000, 700))
        self.resize(1200, 800)
        
        # Variables de estado
        self.input_path = None
        self.output_path = None
        self.profile_manager = None
        self.processing_thread = None
        self.processing_worker = None
        
        # Inicializar ProfileManager
        try:
            self.profile_manager = ProfileManager()
            self.logger.info("ProfileManager inicializado exitosamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar ProfileManager: {str(e)}")
        
        # Configurar UI
        self._setup_ui()
        self._setup_connections()
        self._load_profiles()
        
        # Mensaje inicial
        self._log_message("=== Biblioperson Dataset Processor (Versión Corregida) ===")
        self._log_message("Listo para procesar documentos.")
        self._log_message("Selecciona un archivo de entrada y un perfil para comenzar.")
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Panel izquierdo (controles)
        left_panel = self._create_controls_panel()
        main_layout.addWidget(left_panel)
        
        # Panel derecho (logs)
        right_panel = self._create_logs_panel()
        main_layout.addWidget(right_panel)
        
        # Proporciones
        main_layout.setStretch(0, 1)  # Panel izquierdo
        main_layout.setStretch(1, 2)  # Panel derecho (más grande)
        
        # Barra de estado
        self.statusBar().showMessage("Listo para procesar documentos")
        
    def _create_controls_panel(self):
        """Crea el panel de controles."""
        panel = QWidget()
        panel.setMaximumWidth(400)
        panel.setMinimumWidth(350)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Procesador de Datasets Literarios")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        layout.addWidget(title)
        
        # === Archivo de entrada ===
        input_group = QGroupBox("Archivo de Entrada")
        input_layout = QVBoxLayout(input_group)
        
        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Selecciona un archivo...")
        self.input_edit.setReadOnly(True)
        
        self.browse_btn = QPushButton("Examinar")
        self.browse_btn.setMaximumWidth(100)
        
        input_row.addWidget(self.input_edit)
        input_row.addWidget(self.browse_btn)
        input_layout.addLayout(input_row)
        layout.addWidget(input_group)
        
        # === Perfil ===
        profile_group = QGroupBox("Perfil de Procesamiento")
        profile_layout = QVBoxLayout(profile_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Seleccionar perfil...")
        profile_layout.addWidget(self.profile_combo)
        layout.addWidget(profile_group)
        
        # === Override de Metadatos ===
        override_group = QGroupBox("Override de Metadatos")
        override_layout = QVBoxLayout(override_group)
        
        # Override de idioma
        lang_row = QHBoxLayout()
        self.lang_check = QCheckBox("Forzar idioma:")
        self.lang_combo = QComboBox()
        self.lang_combo.setEnabled(False)
        self.lang_combo.addItems([
            "es - Español", "en - English", "fr - Français", "de - Deutsch",
            "it - Italiano", "pt - Português", "ca - Català", "eu - Euskera",
            "gl - Galego", "la - Latín", "grc - Griego Antiguo"
        ])
        
        lang_row.addWidget(self.lang_check)
        lang_row.addWidget(self.lang_combo)
        override_layout.addLayout(lang_row)
        
        # Override de autor
        author_row = QHBoxLayout()
        self.author_check = QCheckBox("Forzar autor:")
        self.author_edit = QLineEdit()
        self.author_edit.setEnabled(False)
        self.author_edit.setPlaceholderText("Nombre del autor...")
        
        author_row.addWidget(self.author_check)
        author_row.addWidget(self.author_edit)
        override_layout.addLayout(author_row)
        
        layout.addWidget(override_group)
        
        # === Archivo de salida ===
        output_group = QGroupBox("Archivo de Salida (Opcional)")
        output_layout = QVBoxLayout(output_group)
        
        output_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Archivo de salida (opcional)...")
        
        self.output_btn = QPushButton("Examinar")
        self.output_btn.setMaximumWidth(100)
        
        output_row.addWidget(self.output_edit)
        output_row.addWidget(self.output_btn)
        output_layout.addLayout(output_row)
        layout.addWidget(output_group)
        
        # === Opciones ===
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)
        
        self.verbose_check = QCheckBox("Modo detallado (verbose)")
        options_layout.addWidget(self.verbose_check)
        layout.addWidget(options_group)
        
        # === Botón de procesamiento ===
        self.process_btn = QPushButton("🚀 Iniciar Procesamiento")
        self.process_btn.setMinimumHeight(50)
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.process_btn)
        
        # === Barra de progreso ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Espaciador
        layout.addStretch()
        
        return panel
        
    def _create_logs_panel(self):
        """Crea el panel de logs."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("Logs del Procesamiento")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff; padding: 6px; background-color: #34495e; border-radius: 4px;")
        layout.addWidget(title)
        
        # Área de logs
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
        layout.addWidget(self.logs_text)
        
        # Botón limpiar
        self.clear_btn = QPushButton("Limpiar Logs")
        self.clear_btn.setMaximumWidth(120)
        layout.addWidget(self.clear_btn)
        
        return panel
        
    def _setup_connections(self):
        """Configura las conexiones de señales."""
        # Conexiones básicas
        self.browse_btn.clicked.connect(self._browse_input)
        self.output_btn.clicked.connect(self._browse_output)
        self.process_btn.clicked.connect(self._start_processing)
        self.clear_btn.clicked.connect(self._clear_logs)
        
        # Validación
        self.input_edit.textChanged.connect(self._validate_inputs)
        self.profile_combo.currentTextChanged.connect(self._validate_inputs)
        
        # Override toggles
        self.lang_check.toggled.connect(self._on_lang_toggle)
        self.author_check.toggled.connect(self._on_author_toggle)
        
    def _load_profiles(self):
        """Carga los perfiles disponibles."""
        if not self.profile_manager:
            self._log_message("❌ Error: ProfileManager no inicializado")
            return
            
        try:
            profiles = self.profile_manager.list_profiles()
            
            self.profile_combo.clear()
            self.profile_combo.addItem("Seleccionar perfil...")
            
            for profile in profiles:
                self.profile_combo.addItem(profile['name'])
            
            self._log_message(f"✅ Cargados {len(profiles)} perfiles disponibles")
            
        except Exception as e:
            self._log_message(f"❌ Error al cargar perfiles: {str(e)}")
            
    def _browse_input(self):
        """Selecciona archivo de entrada."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de entrada",
            "",
            "Archivos soportados (*.txt *.md *.docx *.pdf);;Todos los archivos (*.*)"
        )
        
        if file_path:
            self.input_edit.setText(file_path)
            self.input_path = file_path
            self._log_message(f"📁 Archivo seleccionado: {Path(file_path).name}")
            
    def _browse_output(self):
        """Selecciona archivo de salida."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Especificar archivo de salida",
            "",
            "NDJSON (*.ndjson);;Todos los archivos (*.*)"
        )
        
        if file_path:
            self.output_edit.setText(file_path)
            self.output_path = file_path
            self._log_message(f"💾 Salida: {Path(file_path).name}")
            
    def _validate_inputs(self):
        """Valida las entradas y habilita/deshabilita el botón."""
        has_input = bool(self.input_edit.text().strip())
        has_profile = self.profile_combo.currentIndex() > 0
        
        self.process_btn.setEnabled(has_input and has_profile)
        
        if has_input and has_profile:
            self.statusBar().showMessage("Listo para procesar")
        else:
            self.statusBar().showMessage("Selecciona archivo y perfil")
            
    def _on_lang_toggle(self, checked):
        """Maneja el toggle de override de idioma."""
        self.lang_combo.setEnabled(checked)
        if checked:
            self._log_message("🌐 Override de idioma activado")
        else:
            self._log_message("🌐 Override de idioma desactivado")
            
    def _on_author_toggle(self, checked):
        """Maneja el toggle de override de autor."""
        self.author_edit.setEnabled(checked)
        if checked:
            self._log_message("👤 Override de autor activado")
            self.author_edit.setFocus()
        else:
            self._log_message("👤 Override de autor desactivado")
            
    def _start_processing(self):
        """Inicia el procesamiento."""
        if self.processing_thread and self.processing_thread.isRunning():
            self._log_message("⚠️ Ya hay un procesamiento en curso")
            return
            
        # Obtener parámetros
        input_path = self.input_edit.text().strip()
        profile_name = self.profile_combo.currentText()
        output_path = self.output_edit.text().strip() or None
        verbose = self.verbose_check.isChecked()
        
        # Override de idioma
        language_override = None
        if self.lang_check.isChecked():
            selected = self.lang_combo.currentText()
            if " - " in selected:
                language_override = selected.split(" - ")[0]
                
        # Override de autor
        author_override = None
        if self.author_check.isChecked():
            author = self.author_edit.text().strip()
            if author:
                author_override = author
                
        # Log de inicio
        self._log_message("=== INICIANDO PROCESAMIENTO ===")
        self._log_message(f"📁 Entrada: {Path(input_path).name}")
        self._log_message(f"⚙️ Perfil: {profile_name}")
        if output_path:
            self._log_message(f"💾 Salida: {Path(output_path).name}")
        if language_override:
            self._log_message(f"🌐 Idioma forzado: {language_override}")
        if author_override:
            self._log_message(f"👤 Autor forzado: {author_override}")
        self._log_message("")
        
        # Configurar UI
        self.process_btn.setEnabled(False)
        self.process_btn.setText("⏳ Procesando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Crear worker y thread
        self.processing_worker = SimpleProcessingWorker(
            manager=self.profile_manager,
            input_path=input_path,
            profile_name=profile_name,
            output_path=output_path,
            verbose=verbose,
            language_override=language_override,
            author_override=author_override
        )
        
        self.processing_thread = QThread()
        self.processing_worker.moveToThread(self.processing_thread)
        
        # Conectar señales
        self.processing_thread.started.connect(self.processing_worker.run)
        self.processing_worker.progress_update.connect(self._on_progress)
        self.processing_worker.processing_finished.connect(self._on_finished)
        
        # Iniciar
        self.processing_thread.start()
        
    def _on_progress(self, message):
        """Maneja actualizaciones de progreso."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_message(f"[{timestamp}] {message}")
        
    def _on_finished(self, success, message):
        """Maneja finalización del procesamiento."""
        # Limpiar thread
        if self.processing_thread:
            self.processing_thread.quit()
            self.processing_thread.wait()
            self.processing_thread = None
        self.processing_worker = None
        
        # Restaurar UI
        self.process_btn.setEnabled(True)
        self.process_btn.setText("🚀 Iniciar Procesamiento")
        self.progress_bar.setVisible(False)
        
        # Mostrar resultado
        timestamp = datetime.now().strftime("%H:%M:%S")
        if success:
            self._log_message(f"[{timestamp}] ✅ {message}")
            self.statusBar().showMessage("Procesamiento completado exitosamente")
        else:
            self._log_message(f"[{timestamp}] ❌ {message}")
            self.statusBar().showMessage("Error en procesamiento")
            
        self._log_message("=== PROCESAMIENTO FINALIZADO ===")
        self._log_message("")
        
        # Revalidar inputs
        self._validate_inputs()
        
    def _clear_logs(self):
        """Limpia los logs."""
        self.logs_text.clear()
        self._log_message("=== Logs limpiados ===")
        
    def _log_message(self, message):
        """Agrega un mensaje a los logs."""
        self.logs_text.append(message)
        # Auto-scroll
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Procesamiento en curso",
                "¿Cerrar la aplicación? Esto cancelará el procesamiento actual.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.processing_thread:
                    self.processing_thread.quit()
                    self.processing_thread.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Función principal."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SimpleBibliopersonGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 