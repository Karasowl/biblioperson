#!/usr/bin/env python3
"""
Interfaz gráfica principal para Biblioperson - Procesador de Datasets.

Este módulo contiene la ventana principal de la aplicación de escritorio
para el procesamiento de datasets de documentos literarios.
"""

import sys
import os
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QSplitter, QPushButton, QLabel, QLineEdit, 
    QComboBox, QTextEdit, QFileDialog, QCheckBox, QGroupBox,
    QFrame, QSizePolicy, QMessageBox, QProgressBar, QTabWidget,
    QScrollArea, QSpinBox
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QObject, QTimer, QSettings
from PySide6.QtGui import QFont, QIcon, QTextCursor

# Importar el backend de procesamiento
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dataset.processing.profile_manager import ProfileManager
from dataset.scripts.process_file import core_process, ProcessingStats
from dataset.scripts.unify_ndjson import NDJSONUnifier

# Importar la nueva pestaña de generación de perfiles IA
from dataset.scripts.ui.ai_profile_generator_tab import AIProfileGeneratorTab

# Importar el widget de filtros JSON
from dataset.scripts.ui.json_filter_widget import JSONFilterWidget

# Importar la pestaña de unificación de NDJSON - ELIMINADA (funcionalidad integrada)
# from dataset.scripts.ui.unify_tab import UnifyTab


class ProcessingWorker(QObject):
    """Worker para ejecutar el procesamiento en un hilo separado."""
    
    # Señales para comunicar progreso y resultados
    progress_update = Signal(str)  # Mensaje de progreso
    processing_finished = Signal(bool, str)  # (éxito, mensaje)
    
    def __init__(self, manager: ProfileManager, input_path: str, profile_name: str, 
                 output_path: str = None, verbose: bool = False, 
                 force_content_type: str = None, encoding: str = "utf-8",
                 language_override: str = None, author_override: str = None,
                 output_format: str = "ndjson", unify_output: bool = False,
                 parallel_enabled: bool = False, workers_count: int = 4, 
                 timing_enabled: bool = False):
        super().__init__()
        self.manager = manager
        self.input_path = Path(input_path)
        self.profile_name = profile_name
        self.output_path = output_path
        self.verbose = verbose
        self.force_content_type = force_content_type
        self.encoding = encoding
        self.language_override = language_override
        self.author_override = author_override
        self.output_format = output_format  # Mantener el formato original ("JSON" o "NDJSON")
        self.unify_output = unify_output
        self.parallel_enabled = parallel_enabled
        self.workers_count = workers_count
        self.timing_enabled = timing_enabled
        
        # Estadísticas detalladas por extensión
        self.success_by_extension = {}  # {'.pdf': 10, '.txt': 5}
        self.errors_by_extension = {}   # {'.png': {'loader_error': 15}, '.mp4': {'loader_error': 8}}
        self.unsupported_extensions = set()  # Extensiones no soportadas encontradas
        
    def run(self):
        """Ejecuta el procesamiento."""
        try:
            self.progress_update.emit("Iniciando procesamiento...")
            
            # Crear argumentos simulados para core_process
            args = argparse.Namespace()
            args.input_path = str(self.input_path)  # Mantener la ruta original (directorio o archivo)
            args.profile = self.profile_name
            args.verbose = self.verbose
            args.encoding = self.encoding
            args.force_type = self.force_content_type
            args.confidence_threshold = 0.5
            args.language_override = self.language_override
            args.author_override = self.author_override
            
            if self.input_path.is_file():
                # Procesar archivo único
                args.output = self.output_path  # Para archivos, usar output_path tal como está
                
                self.progress_update.emit(f"Procesando archivo: {self.input_path.name}")
                
                result_code, message, document_metadata, segments, segmenter_stats = core_process(
                    manager=self.manager,
                    input_path=self.input_path,
                    profile_name_override=self.profile_name,
                    output_spec=self.output_path,
                    cli_args=args,
                    output_format=self.output_format
                )
                
                if result_code.startswith('SUCCESS'):
                    if segments:
                        self.progress_update.emit(f"✅ Procesamiento exitoso: {len(segments)} segmentos encontrados")
                    else:
                        self.progress_update.emit("✅ Procesamiento exitoso: No se encontraron segmentos")
                    self.processing_finished.emit(True, f"Archivo procesado exitosamente")
                else:
                    error_msg = message or f"Error en procesamiento: {result_code}"
                    self.progress_update.emit(f"❌ Error: {error_msg}")
                    self.processing_finished.emit(False, error_msg)
                    
            elif self.input_path.is_dir():
                # Procesar directorio - configurar output para preservar estructura
                if self.output_path:
                    # Si se especificó output_path, usarlo como directorio base
                    output_dir = Path(self.output_path)
                    if output_dir.is_file():
                        # Si output_path es un archivo, usar su directorio padre
                        args.output = str(output_dir.parent)
                        self.progress_update.emit(f"⚠️ Advertencia: Output especificado como archivo, usando directorio padre: {output_dir.parent}")
                    else:
                        # Output_path es un directorio, usarlo directamente
                        args.output = str(output_dir)
                        # Crear el directorio si no existe
                        output_dir.mkdir(parents=True, exist_ok=True)
                else:
                    # Si no se especificó output_path, usar directorio actual
                    args.output = str(Path.cwd())
                
                self.progress_update.emit(f"Explorando directorio: {self.input_path}")
                self.progress_update.emit(f"Estructura de directorios se preservará en: {args.output}")
                
                files_to_process = []
                for file_path_iter in self.input_path.rglob('*'): # Renombrar para evitar conflicto
                    if file_path_iter.is_file():
                        files_to_process.append(file_path_iter)
                
                if not files_to_process:
                    self.processing_finished.emit(False, "No se encontraron archivos para procesar")
                    return
                
                self.progress_update.emit(f"Encontrados {len(files_to_process)} archivos para procesar")
                
                stats = ProcessingStats()
                stats.total_files_attempted = len(files_to_process)

                # Limpiar estadísticas previas antes de un nuevo procesamiento de directorio
                self.success_by_extension = {}
                self.errors_by_extension = {}
                self.unsupported_extensions = set()
                
                # Inicializar timing si está habilitado
                start_time = time.time() if self.timing_enabled else None
                file_times = {} if self.timing_enabled else None
                
                if self.parallel_enabled and len(files_to_process) > 1:
                    # Procesamiento paralelo
                    self.progress_update.emit(f"⚡ Procesamiento paralelo activado: {self.workers_count} workers")
                    
                    def process_single_file_wrapper(file_info):
                        """Wrapper para procesar un archivo individual en paralelo."""
                        i, current_file_path = file_info
                        file_start_time = time.time() if self.timing_enabled else None
                        
                        relative_path = current_file_path.relative_to(self.input_path)
                        file_extension = current_file_path.suffix.lower()
                        
                        try:
                            result_code, message, document_metadata, segments, segmenter_stats = core_process(
                                manager=self.manager,
                                input_path=current_file_path,
                                profile_name_override=self.profile_name,
                                output_spec=args.output,
                                cli_args=args,
                                output_format=self.output_format
                            )
                            
                            # Calcular tiempo si está habilitado
                            file_time = time.time() - file_start_time if self.timing_enabled and file_start_time else 0
                            
                            return {
                                'index': i,
                                'file_path': current_file_path,
                                'relative_path': relative_path,
                                'extension': file_extension,
                                'result_code': result_code,
                                'message': message,
                                'segments': segments,
                                'file_time': file_time
                            }
                            
                        except Exception as e:
                            file_time = time.time() - file_start_time if self.timing_enabled and file_start_time else 0
                            return {
                                'index': i,
                                'file_path': current_file_path,
                                'relative_path': relative_path,
                                'extension': file_extension,
                                'result_code': 'EXCEPTION',
                                'message': str(e),
                                'segments': None,
                                'file_time': file_time,
                                'exception': True
                            }
                    
                    # Ejecutar procesamiento paralelo
                    with ThreadPoolExecutor(max_workers=self.workers_count) as executor:
                        # Crear lista de tareas
                        file_tasks = [(i, file_path) for i, file_path in enumerate(files_to_process, 1)]
                        
                        # Enviar tareas al pool
                        future_to_file = {executor.submit(process_single_file_wrapper, task): task for task in file_tasks}
                        
                        # Procesar resultados conforme van completándose
                        for future in as_completed(future_to_file):
                            result = future.result()
                            i = result['index']
                            current_file_path = result['file_path']
                            relative_path = result['relative_path']
                            file_extension = result['extension']
                            result_code = result['result_code']
                            message = result['message']
                            segments = result['segments']
                            file_time = result['file_time']
                            
                            # Mostrar progreso con timing si está habilitado
                            if self.timing_enabled:
                                self.progress_update.emit(f"Procesando {i}/{len(files_to_process)}: {relative_path} ({file_time:.2f}s)")
                                if file_times is not None:
                                    file_times[str(relative_path)] = file_time
                            else:
                                self.progress_update.emit(f"Procesando {i}/{len(files_to_process)}: {relative_path}")
                            
                            # Procesar resultado (mismo código que la versión secuencial)
                            if result_code == 'SUCCESS_WITH_UNITS' or result_code == 'SUCCESS_NO_UNITS':
                                if result_code == 'SUCCESS_WITH_UNITS':
                                    stats.success_with_units += 1
                                    file_extension_for_log = ".json" if self.output_format == "JSON" else ".ndjson"
                                    expected_output = Path(args.output) / relative_path.parent / f"{current_file_path.stem}{file_extension_for_log}"
                                    self.progress_update.emit(f"  ✅ Guardado en: {expected_output.relative_to(Path(args.output))}")
                                else:
                                    stats.success_no_units += 1
                                self.success_by_extension[file_extension] = self.success_by_extension.get(file_extension, 0) + 1
                            
                            elif result_code == 'LOADER_ERROR':
                                stats.loader_errors += 1
                                stats.add_failure(str(current_file_path), result_code, message or "Error del loader")
                                self.errors_by_extension.setdefault(file_extension, {}).setdefault('loader_error', 0)
                                self.errors_by_extension[file_extension]['loader_error'] += 1
                                if "No hay loader registrado para extensión:" in (message or ""):
                                    self.unsupported_extensions.add(file_extension)
                            elif result_code == 'CONFIG_ERROR':
                                stats.config_errors += 1
                                stats.add_failure(str(current_file_path), result_code, message or "Error de configuración")
                                self.errors_by_extension.setdefault(file_extension, {}).setdefault('config_error', 0)
                                self.errors_by_extension[file_extension]['config_error'] += 1
                            else:
                                stats.processing_exceptions += 1
                                stats.add_failure(str(current_file_path), result_code, message or "Excepción de procesamiento")
                                self.errors_by_extension.setdefault(file_extension, {}).setdefault('processing_error', 0)
                                self.errors_by_extension[file_extension]['processing_error'] += 1
                
                else:
                    # Procesamiento secuencial (código original)
                    if self.parallel_enabled:
                        self.progress_update.emit("🔄 Procesamiento secuencial (un solo archivo o paralelización deshabilitada)")
                    
                    for i, current_file_path in enumerate(files_to_process, 1):
                        file_start_time = time.time() if self.timing_enabled else None
                        
                        relative_path = current_file_path.relative_to(self.input_path)
                        
                        # Mostrar progreso
                        if self.timing_enabled:
                            self.progress_update.emit(f"Procesando {i}/{len(files_to_process)}: {relative_path}")
                        else:
                            self.progress_update.emit(f"Procesando {i}/{len(files_to_process)}: {relative_path}")
                        
                        file_extension = current_file_path.suffix.lower()

                        try:
                            result_code, message, document_metadata, segments, segmenter_stats = core_process(
                                manager=self.manager,
                                input_path=current_file_path,
                                profile_name_override=self.profile_name,
                                output_spec=args.output,
                                cli_args=args,
                                output_format=self.output_format
                            )
                            
                            # Calcular tiempo si está habilitado
                            if self.timing_enabled and file_start_time:
                                file_time = time.time() - file_start_time
                                if file_times is not None:
                                    file_times[str(relative_path)] = file_time
                                self.progress_update.emit(f"  ⏱️ Tiempo: {file_time:.2f}s")
                            
                            if result_code == 'SUCCESS_WITH_UNITS' or result_code == 'SUCCESS_NO_UNITS':
                                if result_code == 'SUCCESS_WITH_UNITS':
                                    stats.success_with_units += 1
                                    file_extension_for_log = ".json" if self.output_format == "JSON" else ".ndjson"
                                    expected_output = Path(args.output) / relative_path.parent / f"{current_file_path.stem}{file_extension_for_log}"
                                    self.progress_update.emit(f"  ✅ Guardado en: {expected_output.relative_to(Path(args.output))}")
                                else:
                                    stats.success_no_units += 1
                                self.success_by_extension[file_extension] = self.success_by_extension.get(file_extension, 0) + 1
                            
                            elif result_code == 'LOADER_ERROR':
                                stats.loader_errors += 1
                                stats.add_failure(str(current_file_path), result_code, message or "Error del loader")
                                self.errors_by_extension.setdefault(file_extension, {}).setdefault('loader_error', 0)
                                self.errors_by_extension[file_extension]['loader_error'] += 1
                                if "No hay loader registrado para extensión:" in (message or ""):
                                    self.unsupported_extensions.add(file_extension)
                            elif result_code == 'CONFIG_ERROR':
                                stats.config_errors += 1
                                stats.add_failure(str(current_file_path), result_code, message or "Error de configuración")
                                self.errors_by_extension.setdefault(file_extension, {}).setdefault('config_error', 0)
                                self.errors_by_extension[file_extension]['config_error'] += 1
                            else:
                                stats.processing_exceptions += 1
                                stats.add_failure(str(current_file_path), result_code, message or "Excepción de procesamiento")
                                self.errors_by_extension.setdefault(file_extension, {}).setdefault('processing_error', 0)
                                self.errors_by_extension[file_extension]['processing_error'] += 1
                                
                        except Exception as e:
                            # Calcular tiempo incluso en caso de excepción
                            if self.timing_enabled and file_start_time:
                                file_time = time.time() - file_start_time
                                if file_times is not None:
                                    file_times[str(relative_path)] = file_time
                                self.progress_update.emit(f"  ⏱️ Tiempo: {file_time:.2f}s (con error)")
                            
                            stats.processing_exceptions += 1
                            stats.add_failure(str(current_file_path), "EXCEPTION", str(e))
                            self.progress_update.emit(f"❌ Error procesando {relative_path}: {str(e)}")
                            current_file_extension_for_exception = current_file_path.suffix.lower() 
                            self.errors_by_extension.setdefault(current_file_extension_for_exception, {}).setdefault('exception', 0)
                            self.errors_by_extension[current_file_extension_for_exception]['exception'] += 1
                
                # Resumen final
                total_success = stats.success_with_units + stats.success_no_units
                total_errors = stats.loader_errors + stats.config_errors + stats.processing_exceptions
                
                # Calcular tiempo total si está habilitado
                if self.timing_enabled and start_time:
                    total_time = time.time() - start_time
                    self.progress_update.emit(f"=== RESUMEN DETALLADO DEL PROCESAMIENTO ===")
                    self.progress_update.emit(f"⏱️ Tiempo total: {total_time:.2f}s")
                    if file_times and len(file_times) > 0:
                        avg_time = sum(file_times.values()) / len(file_times)
                        max_time = max(file_times.values())
                        min_time = min(file_times.values())
                        self.progress_update.emit(f"⏱️ Tiempo promedio por archivo: {avg_time:.2f}s")
                        self.progress_update.emit(f"⏱️ Archivo más rápido: {min_time:.2f}s")
                        self.progress_update.emit(f"⏱️ Archivo más lento: {max_time:.2f}s")
                        if self.parallel_enabled and len(files_to_process) > 1:
                            theoretical_sequential = sum(file_times.values())
                            speedup = theoretical_sequential / total_time if total_time > 0 else 1
                            self.progress_update.emit(f"🚀 Aceleración lograda: {speedup:.2f}x")
                else:
                    self.progress_update.emit(f"=== RESUMEN DETALLADO DEL PROCESAMIENTO ===")
                
                self.progress_update.emit(f"Archivos intentados: {stats.total_files_attempted}")
                self.progress_update.emit(f"Archivos procesados exitosamente: {total_success}/{stats.total_files_attempted}")
                if self.success_by_extension:
                    self.progress_update.emit("  Éxitos por extensión:")
                    for ext, count in sorted(self.success_by_extension.items()):
                        self.progress_update.emit(f"    ├── {ext}: {count} exitosos")
                
                self.progress_update.emit(f"Errores totales: {total_errors}")
                if self.errors_by_extension:
                    self.progress_update.emit("  Errores por extensión y tipo:")
                    for ext, error_types in sorted(self.errors_by_extension.items()):
                        self.progress_update.emit(f"    ├── {ext}:")
                        for error_type, count in sorted(error_types.items()):
                            self.progress_update.emit(f"        └── {error_type.replace('_', ' ').capitalize()}: {count} errores")

                if self.unsupported_extensions:
                    self.progress_update.emit("  Extensiones no soportadas encontradas:")
                    for ext in sorted(list(self.unsupported_extensions)):
                        count = self.errors_by_extension.get(ext, {}).get('loader_error', 0)
                        self.progress_update.emit(f"    ├── {ext} ({count} archivos)")
                
                self.progress_update.emit(f"Archivos con segmentos: {stats.success_with_units}")
                self.progress_update.emit(f"Archivos sin segmentos (pero exitosos): {stats.success_no_units}")
                self.progress_update.emit(f"Estructura preservada en: {args.output}")

                if total_errors > 0 : # Mostrar desglose general si hay errores
                    self.progress_update.emit(f"  Desglose general de errores:")
                    self.progress_update.emit(f"    ├── Errores de loader: {stats.loader_errors}")
                    self.progress_update.emit(f"    ├── Errores de configuración: {stats.config_errors}")
                    self.progress_update.emit(f"    ├── Excepciones de procesamiento: {stats.processing_exceptions}")

                self.progress_update.emit("Recomendaciones:")
                if self.unsupported_extensions:
                    self.progress_update.emit("  • Considera excluir o convertir los archivos con extensiones no soportadas antes del procesamiento.")
                self.progress_update.emit("  • Revisa los logs detallados para errores específicos de configuración o procesamiento si los hubiera.")

                # === Unificación de archivos si está activada ===
                if self.unify_output and total_success > 0:
                    self.progress_update.emit("")
                    self.progress_update.emit("=== INICIANDO UNIFICACIÓN DE ARCHIVOS ===")
                    
                    try:
                        # Determinar formato de salida
                        # Usar el formato real que se usó para guardar los archivos
                        output_format = self.output_format  # Ya viene en minúsculas desde _get_output_format()
                        
                        # Crear nombre de archivo unificado
                        if self.output_path:
                            output_dir = Path(self.output_path)
                            if output_dir.is_file():
                                # Si output_path es un archivo, usar su directorio padre
                                unified_file = output_dir.parent / f"unified_dataset.{output_format}"
                            else:
                                # Output_path es un directorio
                                unified_file = output_dir / f"unified_dataset.{output_format}"
                        else:
                            # Si no se especificó output_path, usar directorio actual
                            unified_file = Path.cwd() / f"unified_dataset.{output_format}"
                        
                        self.progress_update.emit(f"🔗 Unificando archivos en formato {output_format.upper()}")
                        self.progress_update.emit(f"📁 Directorio fuente: {args.output}")
                        self.progress_update.emit(f"📄 Archivo unificado: {unified_file}")
                        
                        # Crear unificador con el formato correcto
                        unifier = NDJSONUnifier(
                            input_dir=args.output,
                            output_file=str(unified_file),
                            recursive=True,
                            output_format=output_format,
                            input_extension=f".{output_format}"  # Buscar archivos con la extensión correcta
                        )
                        
                        # Ejecutar unificación
                        unify_success = unifier.run()
                        
                        if unify_success:
                            self.progress_update.emit(f"✅ Unificación exitosa: {unifier.stats['files_processed']} archivos unificados")
                            self.progress_update.emit(f"📊 Total de entradas: {unifier.stats['total_entries']}")
                            if unified_file.exists():
                                size_mb = unified_file.stat().st_size / (1024 * 1024)
                                self.progress_update.emit(f"📏 Tamaño del archivo: {size_mb:.2f} MB")
                        else:
                            self.progress_update.emit("❌ Error durante la unificación")
                            # Mostrar estadísticas de error para diagnóstico
                            self.progress_update.emit(f"📊 Archivos encontrados: {unifier.stats['files_found']}")
                            self.progress_update.emit(f"📊 Archivos procesados: {unifier.stats['files_processed']}")
                            self.progress_update.emit(f"📊 Archivos saltados: {unifier.stats['files_skipped']}")
                            self.progress_update.emit(f"📊 Errores: {unifier.stats['errors']}")
                            if unifier.stats['files_found'] == 0:
                                self.progress_update.emit(f"🔍 Buscando archivos *.{output_format} en: {args.output}")
                                # Listar archivos realmente presentes para diagnóstico
                                actual_files = list(Path(args.output).rglob("*.*"))
                                if actual_files:
                                    self.progress_update.emit("📁 Archivos encontrados en el directorio:")
                                    for f in actual_files[:10]:  # Mostrar solo los primeros 10
                                        rel_path = f.relative_to(Path(args.output))
                                        self.progress_update.emit(f"   • {rel_path}")
                                    if len(actual_files) > 10:
                                        self.progress_update.emit(f"   ... y {len(actual_files) - 10} más")
                                else:
                                    self.progress_update.emit("📁 No se encontraron archivos en el directorio de salida")
                            
                    except Exception as e:
                        self.progress_update.emit(f"❌ Error en unificación: {str(e)}")
                    
                    self.progress_update.emit("=== UNIFICACIÓN FINALIZADA ===")
                    self.progress_update.emit("")

                success = total_errors == 0
                summary_msg = f"Procesamiento completado: {total_success} éxitos, {total_errors} errores. Revisa los logs para el resumen detallado." # Mensaje más genérico
                self.processing_finished.emit(success, summary_msg)
            else:
                self.processing_finished.emit(False, "La ruta de entrada no es válida")
                
        except Exception as e:
            self.progress_update.emit(f"❌ Error inesperado: {str(e)}")
            self.processing_finished.emit(False, f"Error inesperado: {str(e)}")


class BibliopersonMainWindow(QMainWindow):
    """
    Ventana principal de la aplicación Biblioperson para procesamiento de datasets.
    
    Esta clase implementa la interfaz gráfica principal que permite a los usuarios:
    - Seleccionar archivos o carpetas de entrada
    - Configurar perfiles de procesamiento
    - Especificar rutas de salida
    - Monitorear el progreso y logs del procesamiento
    """
    
    # Señales para comunicación entre componentes
    processing_started = Signal()
    processing_finished = Signal(bool)  # True si exitoso, False si error
    
    def __init__(self):
        super().__init__()
        
        # Configurar logger temprano para evitar errores
        self.logger = logging.getLogger(__name__)
        
        # Configurar persistencia de configuración
        self.settings = QSettings("Biblioperson", "DatasetProcessor")
        
        self.setWindowTitle("Biblioperson - Procesador de Datasets")
        self.setMinimumSize(QSize(900, 700))
        self.resize(1200, 800)
        
        # Variables de estado
        self.input_path: Optional[str] = None
        self.output_path: Optional[str] = None
        self.selected_profile: Optional[str] = None
        self.input_is_folder: bool = False  # Recordar si la entrada es carpeta o archivo
        
        # Backend de procesamiento - inicializar temprano
        self.profile_manager: Optional[ProfileManager] = None
        self.processing_thread: Optional[QThread] = None
        self.processing_worker: Optional[ProcessingWorker] = None
        
        # Configurar la interfaz primero
        self._setup_ui()
        
        # Inicializar ProfileManager después de crear la UI
        self._initialize_profile_manager()
        
        # Configurar conexiones inmediatamente después de crear la UI
        self._setup_basic_functionality()
        
        # Cargar configuración guardada DESPUÉS de que las conexiones estén listas
        # Aumentar el delay para asegurar que todo esté inicializado
        QTimer.singleShot(500, self._load_settings)
    
    def _setup_ui(self):
        """Configura todos los elementos de la interfaz de usuario."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Título de la aplicación
        title_label = QLabel("Procesador de Datasets Literarios")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; margin: 10px 0; background-color: rgba(52, 73, 94, 0.8); padding: 8px; border-radius: 5px;")
        main_layout.addWidget(title_label)
        
        # Sistema de pestañas
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Pestaña 1: Procesamiento (funcionalidad actual)
        processing_tab = self._create_processing_tab()
        self.tab_widget.addTab(processing_tab, "📄 Procesamiento")
        
        # Pestaña 2: Filtros JSON
        json_filter_tab = self._create_json_filter_tab()
        self.tab_widget.addTab(json_filter_tab, "🔧 Filtros JSON")
        
        # Pestaña 3: Generación de Perfiles IA
        try:
            if self.profile_manager:
                ai_tab = AIProfileGeneratorTab(self.profile_manager)
                ai_tab.profile_saved.connect(self._on_profile_saved)
                self.tab_widget.addTab(ai_tab, "🤖 Generar Perfil IA")
        except Exception as e:
            self.logger.error(f"Error al cargar pestaña de IA: {str(e)}")
        
        # Pestaña 3: Unificación de NDJSON - ELIMINADA (funcionalidad integrada)
        # unify_tab = UnifyTab()
        # self.tab_widget.addTab(unify_tab, "🔗 Unificar NDJSON")
        
        # Barra de estado
        self.statusBar().showMessage("Listo para procesar documentos")
    
    def _create_processing_tab(self) -> QWidget:
        """Crea la pestaña de procesamiento (funcionalidad original)."""
        tab_widget = QWidget()
        
        # Layout principal usando splitter para redimensionamiento flexible
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Splitter principal (horizontal)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel de configuración (izquierda)
        config_panel = self._create_config_panel()
        main_splitter.addWidget(config_panel)
        
        # Panel de logs/estado (derecha)
        logs_panel = self._create_logs_panel()
        main_splitter.addWidget(logs_panel)
        
        # Configurar proporciones del splitter
        main_splitter.setSizes([400, 600])  # 40% config, 60% logs
        main_splitter.setStretchFactor(0, 0)  # Panel config no se estira
        main_splitter.setStretchFactor(1, 1)  # Panel logs se estira
        
        return tab_widget
    
    def _create_json_filter_tab(self) -> QWidget:
        """Crea la pestaña de configuración de filtros JSON."""
        tab_widget = QWidget()
        
        # Layout principal
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Descripción de la funcionalidad
        description = QLabel(
            "Esta herramienta permite configurar filtros avanzados para procesar archivos JSON. "
            "Puedes especificar qué campos extraer como texto, aplicar reglas de filtrado, "
            "y probar la configuración antes de usarla en el procesamiento."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
                color: #2c3e50;
                font-size: 11px;
            }
        """)
        main_layout.addWidget(description)
        
        # Widget de filtros JSON
        self.json_filter_widget = JSONFilterWidget()
        
        # Crear área de scroll para el widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.json_filter_widget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        main_layout.addWidget(scroll_area)
        
        return tab_widget
    
    def _create_config_panel(self) -> QWidget:
        """Crea el panel de configuración con todos los controles."""
        panel = QWidget()
        panel.setMaximumWidth(450)
        panel.setMinimumWidth(350)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # === Sección de Archivos de Entrada ===
        input_group = QGroupBox("Archivos de Entrada")
        input_layout = QVBoxLayout(input_group)
        
        # Selector de archivo/carpeta de entrada
        input_file_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Selecciona archivo o carpeta...")
        self.input_path_edit.setReadOnly(True)
        
        self.browse_file_btn = QPushButton("Archivo")
        self.browse_file_btn.setMaximumWidth(80)
        self.browse_folder_btn = QPushButton("Carpeta")
        self.browse_folder_btn.setMaximumWidth(80)
        
        input_file_layout.addWidget(QLabel("Entrada:"))
        input_file_layout.addWidget(self.input_path_edit)
        input_file_layout.addWidget(self.browse_file_btn)
        input_file_layout.addWidget(self.browse_folder_btn)
        
        input_layout.addLayout(input_file_layout)
        layout.addWidget(input_group)
        
        # === Sección de Configuración de Procesamiento ===
        processing_group = QGroupBox("Configuración de Procesamiento")
        processing_layout = QVBoxLayout(processing_group)
        
        # Selector de perfil - CREAR INMEDIATAMENTE SIN REFERENCIAS EXTERNAS
        profile_layout = QHBoxLayout()
        profile_label = QLabel("Perfil:")
        profile_layout.addWidget(profile_label)
        
        # Crear combo y poblarlo inmediatamente
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Seleccionar perfil...")
        self.profile_combo.addItem("biblical_verse_segmentation")
        self.profile_combo.addItem("book_structure") 
        self.profile_combo.addItem("chapter_heading")
        self.profile_combo.addItem("perfil_docx_heading")
        self.profile_combo.addItem("poem_or_lyrics")
        
        profile_layout.addWidget(self.profile_combo)
        processing_layout.addLayout(profile_layout)
        
        # === Sección de Override de Metadatos ===
        override_frame = QFrame()
        override_frame.setFrameStyle(QFrame.Box)
        override_frame.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 5px; padding: 5px; }")
        override_layout = QVBoxLayout(override_frame)
        
        # Título de la sección
        override_title = QLabel("Override de Metadatos")
        override_title.setFont(QFont("Arial", 10, QFont.Bold))
        override_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        override_layout.addWidget(override_title)
        
        # Override de idioma
        language_layout = QHBoxLayout()
        self.language_override_check = QCheckBox("Forzar idioma:")
        self.language_override_check.setMaximumWidth(120)
        
        self.language_combo = QComboBox()
        self.language_combo.setEnabled(False)
        self.language_combo.addItems([
            "es - Español",
            "en - English", 
            "fr - Français",
            "de - Deutsch",
            "it - Italiano",
            "pt - Português",
            "ca - Català",
            "eu - Euskera",
            "gl - Galego",
            "la - Latín",
            "grc - Griego Antiguo"
        ])
        self.language_combo.setCurrentText("es - Español")
        
        # Botón para limpiar override de idioma
        self.clear_language_btn = QPushButton("✕")
        self.clear_language_btn.setMaximumWidth(25)
        self.clear_language_btn.setEnabled(False)
        self.clear_language_btn.setToolTip("Limpiar override de idioma")
        self.clear_language_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        language_layout.addWidget(self.language_override_check)
        language_layout.addWidget(self.language_combo)
        language_layout.addWidget(self.clear_language_btn)
        override_layout.addLayout(language_layout)
        
        # Override de autor
        author_layout = QHBoxLayout()
        self.author_override_check = QCheckBox("Forzar autor:")
        self.author_override_check.setMaximumWidth(120)
        
        self.author_edit = QLineEdit()
        self.author_edit.setEnabled(False)
        self.author_edit.setPlaceholderText("Nombre del autor...")
        
        # Botón para limpiar override de autor
        self.clear_author_btn = QPushButton("✕")
        self.clear_author_btn.setMaximumWidth(25)
        self.clear_author_btn.setEnabled(False)
        self.clear_author_btn.setToolTip("Limpiar override de autor")
        self.clear_author_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        author_layout.addWidget(self.author_override_check)
        author_layout.addWidget(self.author_edit)
        author_layout.addWidget(self.clear_author_btn)
        override_layout.addLayout(author_layout)
        
        processing_layout.addWidget(override_frame)
        layout.addWidget(processing_group)
        
        # === Opciones Avanzadas ===
        advanced_group = QGroupBox("Opciones Avanzadas")
        advanced_layout = QGridLayout(advanced_group)
        advanced_layout.setSpacing(8)
        
        # Checkboxes para opciones
        self.verbose_check = QCheckBox("Modo detallado (verbose)")
        self.force_type_check = QCheckBox("Forzar tipo de contenido")
        
        # ComboBox para tipo de contenido (inicialmente deshabilitado)
        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems([
            "poemas", "escritos", "canciones", "capitulos"
        ])
        self.content_type_combo.setEnabled(False)
        
        # === Nuevas opciones de rendimiento ===
        # Checkbox para procesamiento paralelo
        self.parallel_check = QCheckBox("Procesamiento paralelo (recomendado)")
        self.parallel_check.setChecked(True)  # Activado por defecto
        self.parallel_check.setToolTip("Procesar múltiples archivos simultáneamente para mejor rendimiento")
        
        # Selector de workers
        workers_layout = QHBoxLayout()
        workers_label = QLabel("Workers:")
        self.workers_spin = QSpinBox()
        self.workers_spin.setMinimum(1)
        self.workers_spin.setMaximum(32)
        import os
        default_workers = min(os.cpu_count() or 4, 16)  # Máximo 16 workers
        self.workers_spin.setValue(default_workers)
        self.workers_spin.setToolTip(f"Número de archivos a procesar simultáneamente (CPU detectada: {os.cpu_count()} cores)")
        workers_layout.addWidget(workers_label)
        workers_layout.addWidget(self.workers_spin)
        workers_layout.addStretch()
        
        # Checkbox para mostrar tiempos
        self.timing_check = QCheckBox("Mostrar tiempos de procesamiento")
        self.timing_check.setChecked(True)  # Activado por defecto
        self.timing_check.setToolTip("Mostrar tiempo de procesamiento por archivo y estadísticas de rendimiento")
        
        # === Nuevas opciones de formato de salida ===
        # Selector de formato de salida
        output_format_layout = QHBoxLayout()
        output_format_label = QLabel("Formato de salida:")
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems([
            "NDJSON (líneas JSON)", 
            "JSON"
        ])
        self.output_format_combo.setToolTip("Formato para los archivos de salida")
        output_format_layout.addWidget(output_format_label)
        output_format_layout.addWidget(self.output_format_combo)
        
        # Checkbox para unificar archivos cuando se procesa una carpeta
        self.unify_output_check = QCheckBox("Unificar en archivo único (para carpetas)")
        self.unify_output_check.setToolTip("Cuando se procesa una carpeta, unificar todos los resultados en un solo archivo")
        self.unify_output_check.setChecked(False)
        
        # Campo de encoding
        encoding_layout = QHBoxLayout()
        encoding_layout.addWidget(QLabel("Encoding:"))
        self.encoding_edit = QLineEdit("utf-8")
        self.encoding_edit.setMaximumWidth(100)
        encoding_layout.addWidget(self.encoding_edit)
        encoding_layout.addStretch()
        
        # Agregar al layout avanzado
        advanced_layout.addWidget(self.verbose_check, 0, 0, 1, 2)
        advanced_layout.addWidget(self.force_type_check, 1, 0)
        advanced_layout.addWidget(self.content_type_combo, 1, 1)
        advanced_layout.addWidget(self.parallel_check, 2, 0, 1, 2)
        advanced_layout.addLayout(workers_layout, 3, 0, 1, 2)
        advanced_layout.addWidget(self.timing_check, 4, 0, 1, 2)
        advanced_layout.addLayout(output_format_layout, 5, 0, 1, 2)
        advanced_layout.addWidget(self.unify_output_check, 6, 0, 1, 2)
        advanced_layout.addLayout(encoding_layout, 7, 0, 1, 2)
        
        layout.addWidget(advanced_group)
        
        # === Sección de Salida ===
        output_group = QGroupBox("Archivo de Salida")
        output_layout = QVBoxLayout(output_group)
        
        output_file_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Archivo o carpeta de salida (opcional)...")
        
        self.browse_output_btn = QPushButton("Examinar")
        self.browse_output_btn.setMaximumWidth(100)
        
        output_file_layout.addWidget(QLabel("Salida:"))
        output_file_layout.addWidget(self.output_path_edit)
        output_file_layout.addWidget(self.browse_output_btn)
        
        output_layout.addLayout(output_file_layout)
        layout.addWidget(output_group)
        
        # === Botón de Procesamiento ===
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
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Espaciador para empujar todo hacia arriba
        layout.addStretch()
        
        return panel
    
    def _create_logs_panel(self) -> QWidget:
        """Crea el panel de logs y estado del procesamiento."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título del panel
        logs_title = QLabel("Logs y Estado del Procesamiento")
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
        self.logs_text.append("=== Biblioperson Dataset Processor ===")
        self.logs_text.append("Listo para procesar documentos.")
        self.logs_text.append("Selecciona un archivo o carpeta de entrada para comenzar.")
        self.logs_text.append("")
        
        layout.addWidget(self.logs_text)
        
        # Panel de estado inferior
        status_frame = QFrame()
        status_frame.setMaximumHeight(60)
        status_layout = QHBoxLayout(status_frame)
        
        # Indicador de estado
        self.status_label = QLabel("Estado: Listo")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        # Botón para guardar configuración manualmente
        self.save_config_btn = QPushButton("💾 Guardar Config")
        self.save_config_btn.setMaximumWidth(130)
        self.save_config_btn.setToolTip("Guardar configuración manualmente")
        
        # Botón para limpiar logs
        self.clear_logs_btn = QPushButton("Limpiar Logs")
        self.clear_logs_btn.setMaximumWidth(120)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.save_config_btn)
        status_layout.addWidget(self.clear_logs_btn)
        
        layout.addWidget(status_frame)
        
        return panel
    
    def _setup_connections(self):
        """Configura las conexiones de señales y slots."""
        try:
            # Solo conexiones básicas - NO widgets de override
            self._setup_basic_connections()
            
            self.logger.info("Conexiones básicas configuradas exitosamente")
                    
        except Exception as e:
            self.logger.error(f"Error en _setup_connections: {str(e)}")
            # Continuar sin conexiones si hay errores
    
    def _setup_basic_connections(self):
        """Configura solo las conexiones básicas que no dependen de widgets problemáticos."""
        try:
            # Solo conexiones básicas que sabemos que funcionan
            if hasattr(self, 'browse_file_btn') and self.browse_file_btn is not None:
                self.browse_file_btn.clicked.connect(self._browse_input_file)
            
            if hasattr(self, 'browse_folder_btn') and self.browse_folder_btn is not None:
                self.browse_folder_btn.clicked.connect(self._browse_input_folder)
            
            if hasattr(self, 'browse_output_btn') and self.browse_output_btn is not None:
                self.browse_output_btn.clicked.connect(self._browse_output_file)
            
            if hasattr(self, 'process_btn') and self.process_btn is not None:
                self.process_btn.clicked.connect(self._start_processing)
            
            if hasattr(self, 'clear_logs_btn') and self.clear_logs_btn is not None:
                self.clear_logs_btn.clicked.connect(self._clear_logs)
            
            if hasattr(self, 'save_config_btn') and self.save_config_btn is not None:
                self.save_config_btn.clicked.connect(self._manual_save_settings)
            
            # Conexiones de validación y guardado automático
            if hasattr(self, 'input_path_edit') and self.input_path_edit is not None:
                self.input_path_edit.textChanged.connect(self._validate_inputs)
                self.input_path_edit.textChanged.connect(self._auto_save_settings)
            
            if hasattr(self, 'profile_combo') and self.profile_combo is not None:
                self.profile_combo.currentTextChanged.connect(self._validate_inputs)
                self.profile_combo.currentTextChanged.connect(self._auto_save_settings)
            
            if hasattr(self, 'output_path_edit') and self.output_path_edit is not None:
                self.output_path_edit.textChanged.connect(self._auto_save_settings)
            
            # Conexión de forzar tipo si existe
            if hasattr(self, 'force_type_check') and self.force_type_check is not None and hasattr(self, 'content_type_combo') and self.content_type_combo is not None:
                self.force_type_check.toggled.connect(
                    lambda checked: self.content_type_combo.setEnabled(checked)
                )
            
            # === Conexiones para las nuevas opciones de formato ===
            # Conexiones para formato de salida y unificación
            if hasattr(self, 'output_format_combo') and self.output_format_combo is not None:
                self.output_format_combo.currentTextChanged.connect(self._auto_save_settings)
                self.output_format_combo.currentTextChanged.connect(self._update_output_placeholder)
            
            if hasattr(self, 'unify_output_check') and self.unify_output_check is not None:
                self.unify_output_check.toggled.connect(self._auto_save_settings)
                self.unify_output_check.toggled.connect(self._validate_inputs)
            
            # === Conexiones para las nuevas opciones de rendimiento ===
            if hasattr(self, 'parallel_check') and self.parallel_check is not None:
                self.parallel_check.toggled.connect(self._auto_save_settings)
                self.parallel_check.toggled.connect(self._on_parallel_toggled)
            
            if hasattr(self, 'workers_spin') and self.workers_spin is not None:
                self.workers_spin.valueChanged.connect(self._auto_save_settings)
            
            if hasattr(self, 'timing_check') and self.timing_check is not None:
                self.timing_check.toggled.connect(self._auto_save_settings)
            
            # Conexiones de override (con protección contra widgets eliminados)
            try:
                if hasattr(self, 'language_override_check') and self.language_override_check is not None:
                    self.language_override_check.toggled.connect(self._on_language_override_toggled)
                    self.language_override_check.toggled.connect(self._auto_save_settings)
                if hasattr(self, 'clear_language_btn') and self.clear_language_btn is not None:
                    self.clear_language_btn.clicked.connect(self._clear_language_override)
                if hasattr(self, 'language_combo') and self.language_combo is not None:
                    self.language_combo.currentTextChanged.connect(self._auto_save_settings)
                if hasattr(self, 'author_override_check') and self.author_override_check is not None:
                    self.author_override_check.toggled.connect(self._on_author_override_toggled)
                    self.author_override_check.toggled.connect(self._auto_save_settings)
                if hasattr(self, 'clear_author_btn') and self.clear_author_btn is not None:
                    self.clear_author_btn.clicked.connect(self._clear_author_override)
                if hasattr(self, 'author_edit') and self.author_edit is not None:
                    self.author_edit.textChanged.connect(self._auto_save_settings)
                if hasattr(self, 'verbose_check') and self.verbose_check is not None:
                    self.verbose_check.toggled.connect(self._auto_save_settings)
                if hasattr(self, 'encoding_combo') and self.encoding_combo is not None:
                    self.encoding_combo.currentTextChanged.connect(self._auto_save_settings)
            except RuntimeError as e:
                self.logger.warning(f"Error conectando widgets de override: {str(e)}")
            
            self.logger.info("Conexiones básicas configuradas exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en _setup_basic_connections: {str(e)}")
    
    def _safe_enable_widget(self, widget, enabled):
        """Habilita/deshabilita un widget de forma segura."""
        try:
            if widget is not None and hasattr(widget, 'setEnabled'):
                widget.setEnabled(enabled)
        except RuntimeError:
            # Widget ya fue eliminado, ignorar
            pass
    
    def _widgets_are_valid(self):
        """Verifica que los widgets principales estén disponibles."""
        required_widgets = [
            'input_path_edit', 'profile_combo', 'process_btn', 
            'status_label', 'output_path_edit', 'logs_text'
        ]
        
        for widget_name in required_widgets:
            if not hasattr(self, widget_name) or getattr(self, widget_name) is None:
                self.logger.warning(f"Widget requerido no disponible: {widget_name}")
                return False
                
        return True
    
    def _initialize_profile_manager(self):
        """Inicializa el ProfileManager antes de crear la UI."""
        try:
            self.profile_manager = ProfileManager()
            self.logger.info(f"ProfileManager inicializado exitosamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar ProfileManager: {str(e)}")
            self.profile_manager = None
    
    def _setup_basic_functionality(self):
        """Configura la funcionalidad básica sin widgets problemáticos."""
        try:
            # Cargar perfiles en el combo básico
            self._load_basic_profiles()
            
            # Configurar conexiones básicas
            self._setup_basic_connections()
            
            self.logger.info("Funcionalidad básica configurada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en configuración básica: {str(e)}")
    
    def _load_basic_profiles(self):
        """Carga perfiles en el combo básico sin widgets de override."""
        if not self.profile_manager:
            self.logger.error("ProfileManager no está inicializado")
            return
            
        try:
            profiles = self.profile_manager.list_profiles()
            
            # Solo cargar en profile_combo si existe y no está eliminado
            try:
                if hasattr(self, 'profile_combo') and self.profile_combo is not None:
                    # Verificar que el widget no esté eliminado
                    self.profile_combo.objectName()  # Esto falla si el widget está eliminado
                    
                    self.profile_combo.clear()
                    self.profile_combo.addItem("Seleccionar perfil...")
                    
                    for profile in profiles:
                        self.profile_combo.addItem(profile['name'])
                    
                    self.logger.info(f"Cargados {len(profiles)} perfiles en combo básico")
                    self._log_message(f"✅ Cargados {len(profiles)} perfiles disponibles")
                else:
                    self.logger.warning("profile_combo no está disponible")
            except RuntimeError:
                # Widget eliminado, usar perfiles por defecto
                self.logger.warning("profile_combo eliminado, usando perfiles por defecto")
                
        except Exception as e:
            self.logger.error(f"Error al cargar perfiles básicos: {str(e)}")
    
    def _delayed_setup(self):
        """Configuración retrasada para asegurar que todos los widgets estén disponibles."""
        try:
            # Verificar que los widgets principales existen
            if not hasattr(self, 'profile_combo') or self.profile_combo is None:
                self.logger.error("profile_combo no está disponible para configuración retrasada")
                return
                
            # Cargar perfiles
            self._load_profiles_into_combo()
            
            # Configurar conexiones
            self._setup_connections()
            
            self.logger.info("Configuración retrasada completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en configuración retrasada: {str(e)}")
            # Intentar configuración básica sin los widgets problemáticos
            self._setup_basic_connections()
    
    def _load_profiles_into_combo(self):
        """Carga los perfiles en el combo box."""
        if not self.profile_manager:
            self.logger.error("ProfileManager no está inicializado")
            return
            
        try:
            # Cargar perfiles reales
            profiles = self.profile_manager.list_profiles()
            
            # Limpiar el combo y agregar perfiles reales
            self.profile_combo.clear()
            self.profile_combo.addItem("Seleccionar perfil...")
            
            for profile in profiles:
                self.profile_combo.addItem(profile['name'])
            
            self.logger.info(f"ProfileManager inicializado con {len(profiles)} perfiles")
            
            # Mostrar perfiles disponibles en logs
            self._log_message(f"✅ ProfileManager inicializado con {len(profiles)} perfiles")
            if profiles:
                self._log_message("Perfiles disponibles:")
                for profile in profiles:
                    self._log_message(f"  • {profile['name']}: {profile['description']}")
            
        except Exception as e:
            self.logger.error(f"Error al cargar perfiles: {str(e)}")
            self._log_message(f"❌ Error al cargar perfiles: {str(e)}")
    
    def _load_ai_tab(self):
        """Carga la pestaña de IA después de que todo esté inicializado."""
        if not self.profile_manager:
            self.logger.warning("No se puede cargar pestaña de IA: ProfileManager no inicializado")
            return
            
        try:
            # Usar QTimer para cargar la pestaña de IA después de que la UI esté completamente lista
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._delayed_load_ai_tab)
        except Exception as e:
            self.logger.error(f"Error al programar carga de pestaña de IA: {str(e)}")
    
    def _delayed_load_ai_tab(self):
        """Carga la pestaña de IA con retraso para evitar conflictos."""
        try:
            self.ai_generator_tab = AIProfileGeneratorTab(self.profile_manager)
            self.tab_widget.addTab(self.ai_generator_tab, "🤖 Generar Perfil IA")
            
            # Conexiones de la pestaña de generación de perfiles IA
            self.ai_generator_tab.profile_saved.connect(self._on_profile_saved)
            self.logger.info("Pestaña de IA cargada exitosamente")
        except Exception as e:
            self.logger.error(f"Error al cargar pestaña de IA: {str(e)}")
            # No mostrar en logs de UI para evitar más conflictos
    
    def _browse_input_file(self):
        """Abre diálogo para seleccionar archivo de entrada."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de entrada",
            "",
            "Todos los archivos soportados (*.txt *.md *.docx *.pdf *.ndjson);;Archivos de texto (*.txt);;Markdown (*.md);;Word (*.docx);;PDF (*.pdf);;NDJSON (*.ndjson);;Todos los archivos (*.*)"
        )
        
        if file_path:
            self.input_path_edit.setText(file_path)
            self.input_path = file_path
            self.input_is_folder = False  # Es un archivo
            self._log_message(f"Archivo seleccionado: {file_path}")
    
    def _browse_input_folder(self):
        """Abre diálogo para seleccionar carpeta de entrada."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de entrada"
        )
        
        if folder_path:
            self.input_path_edit.setText(folder_path)
            self.input_path = folder_path
            self.input_is_folder = True  # Es una carpeta
            self._log_message(f"Carpeta seleccionada: {folder_path}")
    
    def _browse_output_file(self):
        """Abre diálogo para seleccionar archivo o carpeta de salida según la entrada."""
        if self.input_is_folder:
            # Si la entrada es una carpeta, permitir seleccionar carpeta de salida
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta de salida"
            )
            
            if folder_path:
                self.output_path_edit.setText(folder_path)
                self.output_path = folder_path
                self._log_message(f"Carpeta de salida: {folder_path}")
        else:
            # Si la entrada es un archivo, permitir seleccionar archivo de salida
            # Obtener formato actual para establecer filtros y extensión por defecto
            current_format = self._get_output_format()
            
            if current_format == "json":
                default_filter = "JSON (*.json)"
                all_filters = "JSON (*.json);;NDJSON (*.ndjson);;Todos los archivos (*.*)"
                default_ext = ".json"
            else:  # ndjson
                default_filter = "NDJSON (*.ndjson)"
                all_filters = "NDJSON (*.ndjson);;JSON (*.json);;Todos los archivos (*.*)"
                default_ext = ".ndjson"
            
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Especificar archivo de salida",
                "",
                all_filters,
                default_filter
            )
            
            if file_path:
                # Asegurar que tiene la extensión correcta
                if not file_path.lower().endswith(('.json', '.ndjson')):
                    file_path += default_ext
                    self._log_message(f"⚠️ Extensión agregada automáticamente: {default_ext}")
                
                self.output_path_edit.setText(file_path)
                self.output_path = file_path
                self._log_message(f"Archivo de salida: {file_path}")
    
    def _validate_inputs(self):
        """Valida las entradas y habilita/deshabilita el botón de procesamiento."""
        try:
            # Verificar que los widgets existen antes de usarlos
            if not hasattr(self, 'input_path_edit') or self.input_path_edit is None:
                return
            
            if not hasattr(self, 'profile_combo') or self.profile_combo is None:
                return
                
            has_input = bool(self.input_path_edit.text().strip())
            has_profile = self.profile_combo.currentIndex() > 0
            
            # Actualizar placeholder del output según el tipo de entrada
            self._update_output_placeholder()
            
            if hasattr(self, 'process_btn') and self.process_btn is not None:
                self.process_btn.setEnabled(has_input and has_profile)
            
            if hasattr(self, 'status_label') and self.status_label is not None:
                if has_input and has_profile:
                    self.status_label.setText("Estado: Listo para procesar")
                    self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                else:
                    self.status_label.setText("Estado: Configuración incompleta")
                    self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        except RuntimeError as e:
            # Widget eliminado, ignorar silenciosamente
            self.logger.warning(f"Widget eliminado durante validación: {str(e)}") # Log para info
            pass
        except Exception as e:
            self.logger.error(f"Error en _validate_inputs: {e}")
    
    def _update_output_placeholder(self):
        """Actualiza el placeholder del campo de salida según el tipo de entrada."""
        try:
            input_path = self.input_path_edit.text().strip()
            
            if not input_path:
                self.output_path_edit.setPlaceholderText("Archivo o carpeta de salida (opcional)...")
            elif self.input_is_folder:
                self.output_path_edit.setPlaceholderText("Carpeta de salida (opcional)...")
            else:
                self.output_path_edit.setPlaceholderText("Archivo de salida (opcional)...")
        except Exception as e:
            self.logger.error(f"Error en _update_output_placeholder: {e}")
    
    def _start_processing(self):
        """Inicia el procesamiento real de documentos."""
        if not self.profile_manager:
            self._log_message("❌ Error: ProfileManager no está inicializado")
            QMessageBox.critical(
                self,
                "Error de Inicialización",
                "El sistema de procesamiento no se ha inicializado correctamente.\n\nPor favor, reinicia la aplicación."
            )
            return
        
        if self.processing_thread and self.processing_thread.isRunning():
            self._log_message("⚠️ Ya hay un procesamiento en curso")
            return
        
        # Verificar que los widgets principales existen
        if not hasattr(self, 'input_path_edit') or self.input_path_edit is None:
            self._log_message("❌ Error: Widget de entrada no disponible")
            return
            
        if not hasattr(self, 'profile_combo') or self.profile_combo is None:
            self._log_message("❌ Error: Widget de perfil no disponible")
            return
        
        try:
            # Obtener parámetros
            input_path = self.input_path_edit.text().strip()
            profile_name = self.profile_combo.currentText()
            output_path = self.output_path_edit.text().strip() or None if hasattr(self, 'output_path_edit') and self.output_path_edit is not None else None
            verbose = self.verbose_check.isChecked() if hasattr(self, 'verbose_check') and self.verbose_check is not None else False
            force_content_type = self.content_type_combo.currentText() if hasattr(self, 'force_type_check') and self.force_type_check is not None and self.force_type_check.isChecked() and hasattr(self, 'content_type_combo') and self.content_type_combo is not None else None
            encoding = self.encoding_edit.text().strip() or "utf-8" if hasattr(self, 'encoding_edit') and self.encoding_edit is not None else "utf-8"
            
            # Obtener nuevas opciones de formato
            output_format = self._get_output_format()
            unify_output = self._get_unify_output()
            
            # Obtener nuevas opciones de rendimiento
            parallel_enabled = self._get_parallel_enabled()
            workers_count = self._get_workers_count()
            timing_enabled = self._get_timing_enabled()
            
            # Validar overrides antes de continuar
            language_override = self._get_language_code()
            author_override = self._get_author_override()
        except RuntimeError as e:
            self._log_message(f"❌ Error: Widget eliminado durante obtención de parámetros: {str(e)}")
            return
        except Exception as e:
            self._log_message(f"❌ Error al obtener parámetros: {str(e)}")
            return
        
        # Validar overrides si están activados
        try:
            if hasattr(self, 'language_override_check') and self.language_override_check is not None and self.language_override_check.isChecked() and language_override is None:
                self._log_message("❌ Error: No se puede procesar con override de idioma inválido")
                return
            
            if hasattr(self, 'author_override_check') and self.author_override_check is not None and self.author_override_check.isChecked() and author_override is None:
                self._log_message("❌ Error: No se puede procesar con override de autor inválido")
                return
        except RuntimeError:
            # Widgets eliminados, continuar sin validación de override
            pass
        
        # Log de inicio
        self._log_message("=== INICIANDO PROCESAMIENTO REAL ===")
        self._log_message(f"📁 Entrada: {input_path}")
        self._log_message(f"⚙️ Perfil: {profile_name}")
        
        if output_path:
            output_type = "Carpeta" if self.input_is_folder else "Archivo"
            self._log_message(f"💾 {output_type} de salida: {output_path}")
        else:
            self._log_message("💾 Salida: Directorio actual (por defecto)")
        
        if verbose:
            self._log_message("🔍 Modo detallado activado")
        
        if force_content_type:
            self._log_message(f"🔧 Tipo forzado: {force_content_type}")
        
        self._log_message(f"📝 Encoding: {encoding}")
        
        # Mostrar información de formato de salida
        self._log_message(f"📄 Formato de salida: {output_format}")
        
        # Mostrar información de unificación
        if unify_output and self.input_is_folder:
            self._log_message("🔗 Unificación activada: Se creará un archivo único")
        elif unify_output and not self.input_is_folder:
            self._log_message("⚠️ Unificación ignorada: Solo aplica para carpetas")
        
        # Mostrar información de rendimiento
        if parallel_enabled and self.input_is_folder:
            self._log_message(f"⚡ Procesamiento paralelo: {workers_count} workers")
        elif parallel_enabled and not self.input_is_folder:
            self._log_message("🔄 Procesamiento secuencial: Un solo archivo")
        else:
            self._log_message("🔄 Procesamiento secuencial: Paralelización deshabilitada")
        
        if timing_enabled:
            self._log_message("⏱️ Medición de tiempos activada")
        
        # Mostrar información de override
        if language_override:
            self._log_message(f"🌐 Idioma forzado: {language_override}")
        else:
            self._log_message("🌐 Idioma: Detección automática")
            
        if author_override:
            self._log_message(f"👤 Autor forzado: '{author_override}'")
        else:
            self._log_message("👤 Autor: Detección automática")
            
        self._log_message("")
        
        # Configurar UI para procesamiento
        self.process_btn.setEnabled(False)
        self.process_btn.setText("⏳ Procesando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        
        # Crear worker y thread
        self.processing_worker = ProcessingWorker(
            manager=self.profile_manager,
            input_path=input_path,
            profile_name=profile_name,
            output_path=output_path,
            verbose=verbose,
            force_content_type=force_content_type,
            encoding=encoding,
            language_override=language_override,
            author_override=author_override,
            output_format=output_format,
            unify_output=unify_output,
            parallel_enabled=parallel_enabled,
            workers_count=workers_count,
            timing_enabled=timing_enabled
        )
        
        self.processing_thread = QThread()
        self.processing_worker.moveToThread(self.processing_thread)
        
        # Conectar señales
        self.processing_thread.started.connect(self.processing_worker.run)
        self.processing_worker.progress_update.connect(self._on_progress_update)
        self.processing_worker.processing_finished.connect(self._on_processing_finished)
        
        # Iniciar thread
        self.processing_thread.start()
        
        # Actualizar estado
        self.status_label.setText("Estado: Procesando...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
    
    def _on_progress_update(self, message: str):
        """Maneja actualizaciones de progreso del worker."""
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
        
        # Emitir señal para compatibilidad
        self.processing_finished.emit(success)
    
    def _clear_logs(self):
        """Limpia el área de logs."""
        self.logs_text.clear()
        self.logs_text.append("=== Logs limpiados ===")
        self._log_message("Listo para nuevas operaciones.")
    
    def _on_language_override_toggled(self, checked: bool):
        """Maneja el cambio de estado del checkbox de override de idioma."""
        try:
            if hasattr(self, 'language_combo') and self.language_combo is not None:
                self.language_combo.setEnabled(checked)
            if hasattr(self, 'clear_language_btn') and self.clear_language_btn is not None:
                self.clear_language_btn.setEnabled(checked)
            
            if checked:
                self._log_message("🌐 Override de idioma activado")
                # Mostrar indicador visual
                if hasattr(self, 'language_override_check') and self.language_override_check is not None:
                    self.language_override_check.setStyleSheet("QCheckBox { color: #e67e22; font-weight: bold; }")
            else:
                self._log_message("🌐 Override de idioma desactivado")
                # Quitar indicador visual
                if hasattr(self, 'language_override_check') and self.language_override_check is not None:
                    self.language_override_check.setStyleSheet("")
        except RuntimeError as e:
            self.logger.warning(f"Error en _on_language_override_toggled: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error inesperado en _on_language_override_toggled: {str(e)}")
    
    def _clear_language_override(self):
        """Limpia el override de idioma."""
        try:
            if hasattr(self, 'language_override_check') and self.language_override_check is not None:
                self.language_override_check.setChecked(False)
            if hasattr(self, 'language_combo') and self.language_combo is not None:
                self.language_combo.setCurrentText("es - Español")
            self._log_message("🌐 Override de idioma limpiado")
        except RuntimeError:
            pass
    
    def _on_author_override_toggled(self, checked: bool):
        """Maneja el cambio de estado del checkbox de override de autor."""
        try:
            if hasattr(self, 'author_edit') and self.author_edit is not None:
                self.author_edit.setEnabled(checked)
            if hasattr(self, 'clear_author_btn') and self.clear_author_btn is not None:
                self.clear_author_btn.setEnabled(checked)
            
            if checked:
                self._log_message("👤 Override de autor activado")
                # Mostrar indicador visual
                if hasattr(self, 'author_override_check') and self.author_override_check is not None:
                    self.author_override_check.setStyleSheet("QCheckBox { color: #e67e22; font-weight: bold; }")
                # Enfocar el campo de texto
                if hasattr(self, 'author_edit') and self.author_edit is not None:
                    self.author_edit.setFocus()
            else:
                self._log_message("👤 Override de autor desactivado")
                # Quitar indicador visual
                if hasattr(self, 'author_override_check') and self.author_override_check is not None:
                    self.author_override_check.setStyleSheet("")
        except RuntimeError as e:
            self.logger.warning(f"Error en _on_author_override_toggled: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error inesperado en _on_author_override_toggled: {str(e)}")
    
    def _clear_author_override(self):
        """Limpia el override de autor."""
        try:
            if hasattr(self, 'author_override_check') and self.author_override_check is not None:
                self.author_override_check.setChecked(False)
            if hasattr(self, 'author_edit') and self.author_edit is not None:
                self.author_edit.clear()
            self._log_message("👤 Override de autor limpiado")
        except RuntimeError:
            pass

    def _on_parallel_toggled(self, checked: bool):
        """Maneja el cambio de estado del checkbox de procesamiento paralelo."""
        try:
            if hasattr(self, 'workers_spin') and self.workers_spin is not None:
                self.workers_spin.setEnabled(checked)
            
            if checked:
                workers = self.workers_spin.value() if hasattr(self, 'workers_spin') and self.workers_spin is not None else 4
                self._log_message(f"⚡ Procesamiento paralelo activado ({workers} workers)")
                # Mostrar indicador visual
                if hasattr(self, 'parallel_check') and self.parallel_check is not None:
                    self.parallel_check.setStyleSheet("QCheckBox { color: #27ae60; font-weight: bold; }")
            else:
                self._log_message("🔄 Procesamiento secuencial activado")
                # Quitar indicador visual
                if hasattr(self, 'parallel_check') and self.parallel_check is not None:
                    self.parallel_check.setStyleSheet("")
        except RuntimeError as e:
            self.logger.warning(f"Error en _on_parallel_toggled: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error inesperado en _on_parallel_toggled: {str(e)}")

    def _get_language_code(self) -> Optional[str]:
        """Extrae el código de idioma del texto seleccionado en el combo."""
        try:
            if not hasattr(self, 'language_override_check') or self.language_override_check is None:
                return None
                
            if not self.language_override_check.isChecked():
                return None
            
            if not hasattr(self, 'language_combo') or self.language_combo is None:
                return None
            
            selected_text = self.language_combo.currentText()
            if " - " in selected_text:
                language_code = selected_text.split(" - ")[0]
                # Validar que el código de idioma no esté vacío
                if language_code and len(language_code) >= 2:
                    return language_code
                else:
                    self._log_message("⚠️ Error: Código de idioma inválido")
                    return None
            else:
                self._log_message("⚠️ Error: Formato de idioma inválido")
                return None
        except RuntimeError:
            # Widget eliminado, retornar None silenciosamente
            return None
        except Exception as e:
            self._log_message(f"❌ Error al obtener código de idioma: {str(e)}")
            return None
    
    def _get_author_override(self) -> Optional[str]:
        """Obtiene el autor del override si está activado."""
        try:
            if not hasattr(self, 'author_override_check') or self.author_override_check is None:
                return None
                
            if not self.author_override_check.isChecked():
                return None
            
            if not hasattr(self, 'author_edit') or self.author_edit is None:
                return None
            
            author = self.author_edit.text().strip()
            if author:
                # Validar que el nombre del autor no sea demasiado largo
                if len(author) > 200:
                    self._log_message("⚠️ Error: Nombre de autor demasiado largo (máximo 200 caracteres)")
                    return None
                # Validar que no contenga caracteres especiales problemáticos
                if any(char in author for char in ['<', '>', '|', ':', '*', '?', '"', '\\']):
                    self._log_message("⚠️ Error: Nombre de autor contiene caracteres no válidos")
                    return None
                return author
            else:
                return None
        except RuntimeError:
            # Widget eliminado, retornar None silenciosamente
            return None
        except Exception as e:
            self._log_message(f"❌ Error al obtener autor: {str(e)}")
            return None
    
    def _on_profile_saved(self, profile_name: str):
        """Maneja cuando se guarda un nuevo perfil desde la pestaña de IA."""
        self._log_message(f"🤖 Nuevo perfil generado por IA: {profile_name}")
        
        # Recargar perfiles en el ComboBox
        try:
            if self.profile_manager:
                profiles = self.profile_manager.list_profiles()
                
                # Guardar selección actual
                current_selection = self.profile_combo.currentText()
                
                # Limpiar y recargar
                self.profile_combo.clear()
                self.profile_combo.addItem("Seleccionar perfil...")
                
                for profile in profiles:
                    self.profile_combo.addItem(profile['name'])
                
                # Seleccionar el nuevo perfil si está disponible
                index = self.profile_combo.findText(profile_name)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                    self._log_message(f"✅ Perfil '{profile_name}' seleccionado automáticamente")
                else:
                    # Restaurar selección anterior si el nuevo perfil no está disponible
                    index = self.profile_combo.findText(current_selection)
                    if index >= 0:
                        self.profile_combo.setCurrentIndex(index)
                
        except Exception as e:
            self._log_message(f"❌ Error al recargar perfiles: {str(e)}")
    
    def _load_settings(self):
        """Carga la configuración guardada y la aplica a la UI."""
        try:
            self.logger.info("=== INICIANDO CARGA DE CONFIGURACIÓN ===")
            
            # Cargar rutas
            saved_input = self.settings.value("input_path", "")
            saved_output = self.settings.value("output_path", "")
            self.logger.info(f"Cargado input_path: {saved_input}")
            self.logger.info(f"Cargado output_path: {saved_output}")
            
            if saved_input:
                import os
                if os.path.exists(saved_input):
                    self.input_path = saved_input
                    if hasattr(self, 'input_path_edit'):
                        self.input_path_edit.setText(saved_input)
                        # Determinar si es carpeta o archivo
                        self.input_is_folder = os.path.isdir(saved_input)
            
            if saved_output:
                self.output_path = saved_output
                if hasattr(self, 'output_path_edit'):
                    self.output_path_edit.setText(saved_output)
            
            # Cargar perfil seleccionado
            saved_profile = self.settings.value("selected_profile", "")
            self.logger.info(f"Cargado selected_profile: {saved_profile}")
            if saved_profile and hasattr(self, 'profile_combo'):
                index = self.profile_combo.findText(saved_profile)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                    self.selected_profile = saved_profile
            
            # Cargar overrides de idioma
            language_enabled = self.settings.value("language_override_enabled", False, bool)
            language_value = self.settings.value("language_override", "es")
            self.logger.info(f"Cargado language_override_enabled: {language_enabled}")
            self.logger.info(f"Cargado language_override: {language_value}")
            
            if hasattr(self, 'language_override_check'):
                self.language_override_check.setChecked(language_enabled)
            if hasattr(self, 'language_combo') and language_enabled:
                # Buscar el texto en el combo que corresponda al idioma guardado
                for i in range(self.language_combo.count()):
                    if self.language_combo.itemText(i).startswith(language_value + " - "):
                        self.language_combo.setCurrentIndex(i)
                        break
                self.language_combo.setEnabled(True)
                if hasattr(self, 'clear_language_btn'):
                    self.clear_language_btn.setEnabled(True)
            
            # Cargar overrides de autor
            author_enabled = self.settings.value("author_override_enabled", False, bool)
            author_value = self.settings.value("author_override", "")
            self.logger.info(f"Cargado author_override_enabled: {author_enabled}")
            self.logger.info(f"Cargado author_override: {author_value}")
            
            if hasattr(self, 'author_override_check'):
                self.author_override_check.setChecked(author_enabled)
            if hasattr(self, 'author_edit') and author_enabled:
                self.author_edit.setText(author_value)
                self.author_edit.setEnabled(True)
                if hasattr(self, 'author_clear_btn'):
                    self.author_clear_btn.setEnabled(True)
            
            # Cargar otras configuraciones
            verbose_mode = self.settings.value("verbose_mode", False, bool)
            self.logger.info(f"Cargado verbose_mode: {verbose_mode}")
            if hasattr(self, 'verbose_check'):
                self.verbose_check.setChecked(verbose_mode)
            
            encoding = self.settings.value("encoding", "utf-8")
            self.logger.info(f"Cargado encoding: {encoding}")
            if hasattr(self, 'encoding_combo'):
                index = self.encoding_combo.findText(encoding)
                if index >= 0:
                    self.encoding_combo.setCurrentIndex(index)
            
            # Cargar nuevas opciones de formato
            output_format = self.settings.value("output_format", "NDJSON (líneas JSON)")
            self.logger.info(f"Cargado output_format: {output_format}")
            if hasattr(self, 'output_format_combo'):
                # Compatibilidad con configuración anterior
                if output_format == "JSON (array único)":
                    output_format = "JSON"
                index = self.output_format_combo.findText(output_format)
                if index >= 0:
                    self.output_format_combo.setCurrentIndex(index)
                    self.logger.info(f"output_format_combo configurado a índice {index}")
                else:
                    self.logger.warning(f"No se encontró '{output_format}' en output_format_combo")
            else:
                self.logger.warning("output_format_combo no existe durante la carga")
            
            unify_output = self.settings.value("unify_output", False, bool)
            self.logger.info(f"Cargado unify_output: {unify_output}")
            if hasattr(self, 'unify_output_check'):
                self.unify_output_check.setChecked(unify_output)
                self.logger.info(f"unify_output_check configurado a {unify_output}")
            else:
                self.logger.warning("unify_output_check no existe durante la carga")
                    
            # Cargar nuevas opciones de rendimiento
            import os
            parallel_enabled = self.settings.value("parallel_enabled", True, bool)
            self.logger.info(f"Cargado parallel_enabled: {parallel_enabled}")
            if hasattr(self, 'parallel_check'):
                self.parallel_check.setChecked(parallel_enabled)
                self.logger.info(f"parallel_check configurado a {parallel_enabled}")
            
            workers_count = self.settings.value("workers_count", min(os.cpu_count() or 4, 16), int)
            self.logger.info(f"Cargado workers_count: {workers_count}")
            if hasattr(self, 'workers_spin'):
                self.workers_spin.setValue(workers_count)
                self.workers_spin.setEnabled(parallel_enabled)
                self.logger.info(f"workers_spin configurado a {workers_count}")
            
            timing_enabled = self.settings.value("timing_enabled", True, bool)
            self.logger.info(f"Cargado timing_enabled: {timing_enabled}")
            if hasattr(self, 'timing_check'):
                self.timing_check.setChecked(timing_enabled)
                self.logger.info(f"timing_check configurado a {timing_enabled}")
            
            # Cargar geometría de ventana
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
                self.logger.info(f"Geometría restaurada: {len(geometry)} bytes")
            
            self._log_message("✅ Configuración cargada desde la sesión anterior")
            self.logger.info("=== CONFIGURACIÓN CARGADA EXITOSAMENTE ===")
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _save_settings(self):
        """Guarda la configuración actual."""
        try:
            self.logger.info("=== INICIANDO GUARDADO DE CONFIGURACIÓN ===")
            
            # Guardar rutas
            if self.input_path:
                self.settings.setValue("input_path", self.input_path)
                self.logger.info(f"Guardado input_path: {self.input_path}")
            if self.output_path:
                self.settings.setValue("output_path", self.output_path)
                self.logger.info(f"Guardado output_path: {self.output_path}")
            
            # Guardar perfil seleccionado
            if hasattr(self, 'profile_combo') and self.profile_combo.currentText() != "Seleccionar perfil...":
                profile_text = self.profile_combo.currentText()
                self.settings.setValue("selected_profile", profile_text)
                self.logger.info(f"Guardado selected_profile: {profile_text}")
            
            # Guardar overrides de idioma
            if hasattr(self, 'language_override_check'):
                lang_enabled = self.language_override_check.isChecked()
                self.settings.setValue("language_override_enabled", lang_enabled)
                self.logger.info(f"Guardado language_override_enabled: {lang_enabled}")
            if hasattr(self, 'language_combo'):
                # Extraer solo el código de idioma del combo (ej: "es" de "es - Español")
                current_text = self.language_combo.currentText()
                if " - " in current_text:
                    language_code = current_text.split(" - ")[0]
                    self.settings.setValue("language_override", language_code)
                    self.logger.info(f"Guardado language_override: {language_code}")
                else:
                    self.settings.setValue("language_override", "es")
                    self.logger.info("Guardado language_override: es (default)")
            
            # Guardar overrides de autor
            if hasattr(self, 'author_override_check'):
                author_enabled = self.author_override_check.isChecked()
                self.settings.setValue("author_override_enabled", author_enabled)
                self.logger.info(f"Guardado author_override_enabled: {author_enabled}")
            if hasattr(self, 'author_edit'):
                author_text = self.author_edit.text()
                self.settings.setValue("author_override", author_text)
                self.logger.info(f"Guardado author_override: {author_text}")
            
            # Guardar otras configuraciones
            if hasattr(self, 'verbose_check'):
                verbose_mode = self.verbose_check.isChecked()
                self.settings.setValue("verbose_mode", verbose_mode)
                self.logger.info(f"Guardado verbose_mode: {verbose_mode}")
            if hasattr(self, 'encoding_combo'):
                encoding = self.encoding_combo.currentText()
                self.settings.setValue("encoding", encoding)
                self.logger.info(f"Guardado encoding: {encoding}")
            
            # Guardar nuevas opciones de formato
            if hasattr(self, 'output_format_combo'):
                output_format = self.output_format_combo.currentText()
                self.settings.setValue("output_format", output_format)
                self.logger.info(f"Guardado output_format: {output_format}")
            else:
                self.logger.warning("output_format_combo no existe")
            
            # Guardar unificación
            if hasattr(self, 'unify_output_check'):
                unify_output = self.unify_output_check.isChecked()
                self.settings.setValue("unify_output", unify_output)
                self.logger.info(f"Guardado unify_output: {unify_output}")
            else:
                self.logger.warning("unify_output_check no existe")
            
            # Guardar nuevas opciones de rendimiento
            if hasattr(self, 'parallel_check'):
                parallel_enabled = self.parallel_check.isChecked()
                self.settings.setValue("parallel_enabled", parallel_enabled)
                self.logger.info(f"Guardado parallel_enabled: {parallel_enabled}")
            
            if hasattr(self, 'workers_spin'):
                workers_count = self.workers_spin.value()
                self.settings.setValue("workers_count", workers_count)
                self.logger.info(f"Guardado workers_count: {workers_count}")
            
            if hasattr(self, 'timing_check'):
                timing_enabled = self.timing_check.isChecked()
                self.settings.setValue("timing_enabled", timing_enabled)
                self.logger.info(f"Guardado timing_enabled: {timing_enabled}")
            
            # Guardar geometría de ventana
            geometry = self.saveGeometry()
            self.settings.setValue("geometry", geometry)
            self.logger.info(f"Guardado geometry: {len(geometry)} bytes")
            
            # Forzar sincronización
            self.settings.sync()
            self.logger.info("=== CONFIGURACIÓN GUARDADA Y SINCRONIZADA ===")
            
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _auto_save_settings(self):
        """Guarda la configuración automáticamente con un pequeño retraso."""
        # Usar QTimer para evitar guardar constantemente mientras el usuario escribe
        if not hasattr(self, '_save_timer'):
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self._save_settings)
        
        # Reiniciar el timer (esperar 1 segundo después del último cambio)
        self._save_timer.start(1000)
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        # Guardar configuración antes de cualquier otra acción
        self.logger.info("=== CERRANDO APLICACIÓN - GUARDANDO CONFIGURACIÓN ===")
        self._save_settings()
        
        # Verificar si hay procesamiento en curso
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Procesamiento en curso",
                "Hay un procesamiento en curso. ¿Estás seguro de que quieres salir?\n\nEsto cancelará el procesamiento actual.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Terminar el procesamiento
                if self.processing_thread:
                    self.processing_thread.quit()
                    self.processing_thread.wait(3000)  # Esperar máximo 3 segundos
                event.accept()
            else:
                event.ignore()
        else:
            # Sin procesamiento en curso, salir directamente sin preguntar
            event.accept()
        
        self.logger.info("=== APLICACIÓN CERRADA ===")

    def _manual_save_settings(self):
        """Guarda la configuración manualmente y muestra el resultado en logs."""
        try:
            self._save_settings()
            self._log_message("💾 Configuración guardada manualmente")
        except Exception as e:
            self._log_message(f"❌ Error al guardar configuración: {str(e)}")
            self.logger.error(f"Error en guardado manual: {str(e)}")

    def _log_message(self, message: str):
        """Agrega un mensaje al área de logs."""
        try:
            if hasattr(self, 'logs_text') and self.logs_text is not None:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.logs_text.append(f"[{timestamp}] {message}")
                # Auto-scroll al final
                scrollbar = self.logs_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            else:
                # Fallback a logger si logs_text no está disponible
                self.logger.info(f"LOG: {message}")
        except RuntimeError as e:
            # Widget eliminado, usar logger como fallback
            self.logger.info(f"LOG (fallback): {message}")
        except Exception as e:
            self.logger.error(f"Error en _log_message: {e}")

    def _get_output_format(self):
        """Obtiene el formato de salida seleccionado."""
        selected_text = self.output_format_combo.currentText()
        # Simplificar el formato para uso interno (en minúsculas)
        if selected_text == "JSON":
            return "json"  # ✅ CORREGIDO: minúsculas
        else:  # "NDJSON (líneas JSON)"
            return "ndjson"  # ✅ CORREGIDO: minúsculas

    def _get_unify_output(self):
        """Obtiene la opción de unificación seleccionada."""
        return self.unify_output_check.isChecked()

    def _get_parallel_enabled(self):
        """Obtiene el estado del checkbox de procesamiento paralelo."""
        return self.parallel_check.isChecked()

    def _get_workers_count(self):
        """Obtiene el número de workers seleccionado."""
        return self.workers_spin.value()

    def _get_timing_enabled(self):
        """Obtiene el estado del checkbox de mostrar tiempos."""
        return self.timing_check.isChecked()


def main():
    """Función principal para ejecutar la aplicación."""
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')  # Estilo moderno multiplataforma
    
    # Crear y mostrar la ventana principal
    window = BibliopersonMainWindow()
    window.show()
    
    # Ejecutar el bucle de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 