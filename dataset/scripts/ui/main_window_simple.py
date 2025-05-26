#!/usr/bin/env python3
"""
Interfaz gráfica simplificada para Biblioperson - Procesador de Datasets.

Esta versión elimina los widgets problemáticos y mantiene solo la funcionalidad esencial.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional
import argparse
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QFileDialog, 
    QCheckBox, QGroupBox, QMessageBox, QProgressBar, QTabWidget
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QObject
from PySide6.QtGui import QFont

# Importar el backend de procesamiento
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dataset.processing.profile_manager import ProfileManager
from dataset.scripts.process_file import core_process, ProcessingStats

# Importar la pestaña de unificación de NDJSON
from dataset.scripts.ui.unify_tab import UnifyTab


class SimpleProcessingWorker(QObject):
    """Worker simplificado para ejecutar el procesamiento en un hilo separado."""
    
    progress_update = Signal(str)
    processing_finished = Signal(bool, str)
    
    def __init__(self, manager: ProfileManager, input_path: str, profile_name: str, 
                 output_path: str = None, verbose: bool = False):
        super().__init__()
        self.manager = manager
        self.input_path = Path(input_path)
        self.profile_name = profile_name
        self.output_path = output_path
        self.verbose = verbose
        
    def run(self):
        """Ejecuta el procesamiento simplificado."""
        try:
            self.progress_update.emit("Iniciando procesamiento...")
            
            # Crear argumentos básicos
            args = argparse.Namespace()
            args.input_path = str(self.input_path)
            args.profile = self.profile_name
            args.verbose = self.verbose
            args.encoding = "utf-8"
            args.force_type = None
            args.confidence_threshold = 0.5
            args.language_override = None
            args.author_override = None
            
            if self.input_path.is_file():
                args.output = self.output_path
                self.progress_update.emit(f"Procesando archivo: {self.input_path.name}")
                
                result_code, message, document_metadata, segments, segmenter_stats = core_process(
                    manager=self.manager,
                    input_path=self.input_path,
                    profile_name_override=self.profile_name,
                    output_spec=self.output_path,
                    cli_args=args
                )
                
                if result_code.startswith('SUCCESS'):
                    if segments:
                        self.progress_update.emit(f"✅ Procesamiento exitoso: {len(segments)} segmentos encontrados")
                    else:
                        self.progress_update.emit("✅ Procesamiento exitoso: No se encontraron segmentos")
                    self.processing_finished.emit(True, "Archivo procesado exitosamente")
                else:
                    error_msg = message or f"Error en procesamiento: {result_code}"
                    self.progress_update.emit(f"❌ Error: {error_msg}")
                    self.processing_finished.emit(False, error_msg)
                    
            elif self.input_path.is_dir():
                if self.output_path:
                    output_dir = Path(self.output_path)
                    if output_dir.is_file():
                        args.output = str(output_dir.parent)
                    else:
                        args.output = str(output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                else:
                    args.output = str(Path.cwd())
                
                self.progress_update.emit(f"Explorando directorio: {self.input_path}")
                
                files_to_process = []
                for file_path in self.input_path.rglob('*'):
                    if file_path.is_file():
                        files_to_process.append(file_path)
                
                if not files_to_process:
                    self.processing_finished.emit(False, "No se encontraron archivos para procesar")
                    return
                
                self.progress_update.emit(f"Encontrados {len(files_to_process)} archivos para procesar")
                
                stats = ProcessingStats()
                stats.total_files_attempted = len(files_to_process)
                
                for i, file_path in enumerate(files_to_process, 1):
                    relative_path = file_path.relative_to(self.input_path)
                    self.progress_update.emit(f"Procesando {i}/{len(files_to_process)}: {relative_path}")
                    
                    try:
                        result_code, message, document_metadata, segments, segmenter_stats = core_process(
                            manager=self.manager,
                            input_path=file_path,
                            profile_name_override=self.profile_name,
                            output_spec=args.output,
                            cli_args=args
                        )
                        
                        if result_code == 'SUCCESS_WITH_UNITS':
                            stats.success_with_units += 1
                        elif result_code == 'SUCCESS_NO_UNITS':
                            stats.success_no_units += 1
                        elif result_code == 'LOADER_ERROR':
                            stats.loader_errors += 1
                            stats.add_failure(str(file_path), result_code, message or "Error del loader")
                        else:
                            stats.processing_exceptions += 1
                            stats.add_failure(str(file_path), result_code, message or "Error de procesamiento")
                            
                    except Exception as e:
                        stats.processing_exceptions += 1
                        stats.add_failure(str(file_path), "EXCEPTION", str(e))
                        self.progress_update.emit(f"❌ Error procesando {relative_path}: {str(e)}")
                
                total_success = stats.success_with_units + stats.success_no_units
                total_errors = stats.loader_errors + stats.config_errors + stats.processing_exceptions
                
                self.progress_update.emit(f"=== RESUMEN FINAL ===")
                self.progress_update.emit(f"Archivos procesados exitosamente: {total_success}/{stats.total_files_attempted}")
                self.progress_update.emit(f"Errores totales: {total_errors}")
                
                success = total_errors == 0
                summary_msg = f"Procesamiento completado: {total_success} éxitos, {total_errors} errores"
                self.processing_finished.emit(success, summary_msg)
            else:
                self.processing_finished.emit(False, "La ruta de entrada no es válida")
                
        except Exception as e:
            self.progress_update.emit(f"❌ Error inesperado: {str(e)}")
            self.processing_finished.emit(False, f"Error inesperado: {str(e)}")


class SimpleBibliopersonMainWindow(QMainWindow):
    """Ventana principal simplificada de Biblioperson."""
    
    processing_started = Signal()
    processing_finished = Signal(bool)
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("Biblioperson - Procesador de Datasets (Versión Simplificada)")
        self.setMinimumSize(QSize(800, 600))
        self.resize(1000, 700)
        
        # Variables de estado
        self.input_path: Optional[str] = None
        self.output_path: Optional[str] = None
        self.selected_profile: Optional[str] = None
        self.input_is_folder: bool = False
        
        # Backend de procesamiento
        self.profile_manager: Optional[ProfileManager] = None
        self.processing_thread: Optional[QThread] = None
        self.processing_worker: Optional[SimpleProcessingWorker] = None
        
        # Configurar la interfaz
        self._setup_ui()
        
        # Inicializar ProfileManager
        self._initialize_profile_manager()
        
        # Cargar perfiles
        self._load_profiles()
        
        # Configurar conexiones
        self._setup_connections()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario simplificada."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Título
        title_label = QLabel("Procesador de Datasets Literarios - Versión Simplificada")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; margin: 10px 0; background-color: rgba(52, 73, 94, 0.8); padding: 8px; border-radius: 5px;")
        main_layout.addWidget(title_label)
        
        # Sistema de pestañas
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Pestaña de procesamiento
        processing_tab = self._create_processing_tab()
        self.tab_widget.addTab(processing_tab, "📄 Procesamiento")
        
        # Pestaña de unificación
        unify_tab = UnifyTab()
        self.tab_widget.addTab(unify_tab, "🔗 Unificar NDJSON")
        
        # Barra de estado
        self.statusBar().showMessage("Listo para procesar documentos")
    
    def _create_processing_tab(self) -> QWidget:
        """Crea la pestaña de procesamiento simplificada."""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setSpacing(10)
        
        # Panel de configuración (izquierda)
        config_panel = self._create_simple_config_panel()
        layout.addWidget(config_panel)
        
        # Panel de logs (derecha)
        logs_panel = self._create_logs_panel()
        layout.addWidget(logs_panel)
        
        return tab_widget
    
    def _create_simple_config_panel(self) -> QWidget:
        """Crea un panel de configuración simplificado."""
        panel = QWidget()
        panel.setMaximumWidth(400)
        panel.setMinimumWidth(300)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # === Entrada ===
        input_group = QGroupBox("Archivos de Entrada")
        input_layout = QVBoxLayout(input_group)
        
        # Campo de entrada
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Selecciona archivo o carpeta...")
        self.input_path_edit.setReadOnly(True)
        input_layout.addWidget(self.input_path_edit)
        
        # Botones de selección
        buttons_layout = QHBoxLayout()
        self.browse_file_btn = QPushButton("Seleccionar Archivo")
        self.browse_folder_btn = QPushButton("Seleccionar Carpeta")
        buttons_layout.addWidget(self.browse_file_btn)
        buttons_layout.addWidget(self.browse_folder_btn)
        input_layout.addLayout(buttons_layout)
        
        layout.addWidget(input_group)
        
        # === Perfil ===
        profile_group = QGroupBox("Perfil de Procesamiento")
        profile_layout = QVBoxLayout(profile_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Seleccionar perfil...")
        profile_layout.addWidget(self.profile_combo)
        
        layout.addWidget(profile_group)
        
        # === Salida ===
        output_group = QGroupBox("Archivo de Salida (Opcional)")
        output_layout = QVBoxLayout(output_group)
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Archivo o carpeta de salida...")
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton("Examinar")
        output_layout.addWidget(self.browse_output_btn)
        
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
            QPushButton:pressed {
                background-color: #21618c;
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
    
    def _create_logs_panel(self) -> QWidget:
        """Crea el panel de logs."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título
        logs_title = QLabel("Logs del Procesamiento")
        logs_title.setFont(QFont("Arial", 12, QFont.Bold))
        logs_title.setStyleSheet("color: #ffffff; margin-bottom: 10px; background-color: rgba(52, 73, 94, 0.8); padding: 6px; border-radius: 4px;")
        layout.addWidget(logs_title)
        
        # Área de texto
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
        self.logs_text.append("=== Biblioperson Dataset Processor (Simplificado) ===")
        self.logs_text.append("Listo para procesar documentos.")
        self.logs_text.append("Selecciona un archivo o carpeta de entrada para comenzar.")
        self.logs_text.append("")
        
        layout.addWidget(self.logs_text)
        
        # Panel inferior
        bottom_layout = QHBoxLayout()
        
        self.status_label = QLabel("Estado: Listo")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        self.clear_logs_btn = QPushButton("Limpiar Logs")
        self.clear_logs_btn.setMaximumWidth(120)
        
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.clear_logs_btn)
        
        layout.addLayout(bottom_layout)
        
        return panel
    
    def _initialize_profile_manager(self):
        """Inicializa el ProfileManager."""
        try:
            self.profile_manager = ProfileManager()
            self.logger.info("ProfileManager inicializado exitosamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar ProfileManager: {str(e)}")
            self.profile_manager = None
    
    def _load_profiles(self):
        """Carga los perfiles en el combo box."""
        if not self.profile_manager:
            self._log_message("❌ Error: ProfileManager no está inicializado")
            return
            
        try:
            profiles = self.profile_manager.list_profiles()
            
            self.profile_combo.clear()
            self.profile_combo.addItem("Seleccionar perfil...")
            
            for profile in profiles:
                self.profile_combo.addItem(profile['name'])
            
            self._log_message(f"✅ Cargados {len(profiles)} perfiles disponibles")
            
        except Exception as e:
            self.logger.error(f"Error al cargar perfiles: {str(e)}")
            self._log_message(f"❌ Error al cargar perfiles: {str(e)}")
    
    def _setup_connections(self):
        """Configura las conexiones de señales."""
        try:
            self.browse_file_btn.clicked.connect(self._browse_input_file)
            self.browse_folder_btn.clicked.connect(self._browse_input_folder)
            self.browse_output_btn.clicked.connect(self._browse_output_file)
            self.process_btn.clicked.connect(self._start_processing)
            self.clear_logs_btn.clicked.connect(self._clear_logs)
            self.input_path_edit.textChanged.connect(self._validate_inputs)
            self.profile_combo.currentTextChanged.connect(self._validate_inputs)
            
            self.logger.info("Conexiones configuradas exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en _setup_connections: {str(e)}")
    
    def _browse_input_file(self):
        """Selecciona archivo de entrada."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de entrada",
            "",
            "Todos los archivos soportados (*.txt *.md *.docx *.pdf *.ndjson);;Archivos de texto (*.txt);;Markdown (*.md);;Word (*.docx);;PDF (*.pdf);;NDJSON (*.ndjson);;Todos los archivos (*.*)"
        )
        
        if file_path:
            self.input_path_edit.setText(file_path)
            self.input_path = file_path
            self.input_is_folder = False
            self._log_message(f"Archivo seleccionado: {file_path}")
    
    def _browse_input_folder(self):
        """Selecciona carpeta de entrada."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de entrada"
        )
        
        if folder_path:
            self.input_path_edit.setText(folder_path)
            self.input_path = folder_path
            self.input_is_folder = True
            self._log_message(f"Carpeta seleccionada: {folder_path}")
    
    def _browse_output_file(self):
        """Selecciona archivo o carpeta de salida."""
        if self.input_is_folder:
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta de salida"
            )
            
            if folder_path:
                self.output_path_edit.setText(folder_path)
                self.output_path = folder_path
                self._log_message(f"Carpeta de salida: {folder_path}")
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Especificar archivo de salida",
                "",
                "NDJSON (*.ndjson);;Todos los archivos (*.*)",
                "NDJSON (*.ndjson)"
            )
            
            if file_path:
                self.output_path_edit.setText(file_path)
                self.output_path = file_path
                self._log_message(f"Archivo de salida: {file_path}")
    
    def _validate_inputs(self):
        """Valida las entradas."""
        has_input = bool(self.input_path_edit.text().strip())
        has_profile = self.profile_combo.currentIndex() > 0
        
        self.process_btn.setEnabled(has_input and has_profile)
        
        if has_input and has_profile:
            self.status_label.setText("Estado: Listo para procesar")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.status_label.setText("Estado: Configuración incompleta")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def _start_processing(self):
        """Inicia el procesamiento."""
        if not self.profile_manager:
            self._log_message("❌ Error: ProfileManager no está inicializado")
            return
        
        if self.processing_thread and self.processing_thread.isRunning():
            self._log_message("⚠️ Ya hay un procesamiento en curso")
            return
        
        # Obtener parámetros
        input_path = self.input_path_edit.text().strip()
        profile_name = self.profile_combo.currentText()
        output_path = self.output_path_edit.text().strip() or None
        verbose = self.verbose_check.isChecked()
        
        # Log de inicio
        self._log_message("=== INICIANDO PROCESAMIENTO ===")
        self._log_message(f"📁 Entrada: {input_path}")
        self._log_message(f"⚙️ Perfil: {profile_name}")
        if output_path:
            self._log_message(f"💾 Salida: {output_path}")
        if verbose:
            self._log_message("🔍 Modo detallado activado")
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
            verbose=verbose
        )
        
        self.processing_thread = QThread()
        self.processing_worker.moveToThread(self.processing_thread)
        
        # Conectar señales
        self.processing_thread.started.connect(self.processing_worker.run)
        self.processing_worker.progress_update.connect(self._on_progress_update)
        self.processing_worker.processing_finished.connect(self._on_processing_finished)
        
        # Iniciar thread
        self.processing_thread.start()
        
        self.status_label.setText("Estado: Procesando...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
    
    def _on_progress_update(self, message: str):
        """Maneja actualizaciones de progreso."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_message(f"[{timestamp}] {message}")
    
    def _on_processing_finished(self, success: bool, message: str):
        """Maneja la finalización del procesamiento."""
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
            self.status_label.setText("Estado: Procesamiento completado exitosamente")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self._log_message(f"[{timestamp}] ❌ {message}")
            self.status_label.setText("Estado: Error en procesamiento")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        self._log_message("")
        self._log_message("=== PROCESAMIENTO FINALIZADO ===")
        
        self.processing_finished.emit(success)
    
    def _clear_logs(self):
        """Limpia el área de logs."""
        self.logs_text.clear()
        self.logs_text.append("=== Logs limpiados ===")
        self._log_message("Listo para nuevas operaciones.")
    
    def _log_message(self, message: str):
        """Agrega un mensaje al área de logs."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.append(f"[{timestamp}] {message}")
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Función principal."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SimpleBibliopersonMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 