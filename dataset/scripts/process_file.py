#!/usr/bin/env python3
"""
Herramienta de línea de comandos para procesar archivos con el sistema de perfiles.

Uso:
    python process_file.py mi_archivo.docx --profile poem_or_lyrics --output resultados.ndjson
    python process_file.py --list-profiles
"""

import os
import sys
import argparse
import logging
import signal # Nueva importación
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Asegurar que el paquete 'dataset' está en el PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dataset.processing.profile_manager import ProfileManager

# Definiciones para salida de consola mejorada
class ConsoleStyle:
    """Estilos ANSI y emojis para la consola."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    INFO_EMOJI = "ℹ️"
    SUCCESS_EMOJI = "✅"
    WARNING_EMOJI = "⚠️"
    ERROR_EMOJI = "❌"
    DEBUG_EMOJI = "🐞"
    FILE_EMOJI = "📄"
    PROFILE_EMOJI = "⚙️"
    LIST_EMOJI = "📋"
    SAVE_EMOJI = "💾"
    TIMER_EMOJI = "⏱️"
    PERFORMANCE_EMOJI = "🚀"
    PARALLEL_EMOJI = "⚡"

def cprint(message: str, level: str = "INFO", bold: bool = False, emoji: str = None):
    """Imprime mensajes con estilo en la consola."""
    color = ""
    base_emoji = ""

    if level == "INFO":
        color = ConsoleStyle.BLUE
        base_emoji = ConsoleStyle.INFO_EMOJI
    elif level == "SUCCESS":
        color = ConsoleStyle.GREEN
        base_emoji = ConsoleStyle.SUCCESS_EMOJI
    elif level == "WARNING":
        color = ConsoleStyle.YELLOW
        base_emoji = ConsoleStyle.WARNING_EMOJI
    elif level == "ERROR":
        color = ConsoleStyle.RED
        base_emoji = ConsoleStyle.ERROR_EMOJI
    elif level == "DEBUG":
        # Los mensajes de debug del logger ya tienen formato, no aplicar color aquí
        # o hacerlo de forma sutil si se desea.
        # Por ahora, los mensajes de debug directos de cprint sí tendrán emoji.
        base_emoji = ConsoleStyle.DEBUG_EMOJI
        print(f"{base_emoji} DEBUG: {message}")
        return
    elif level == "HEADER":
        color = ConsoleStyle.HEADER
        # No base_emoji for header, emoji can be passed directly
    
    final_emoji = emoji if emoji else base_emoji
    
    styled_message = f"{color}{ConsoleStyle.BOLD if bold else ''}{final_emoji} {message}{ConsoleStyle.ENDC}"
    print(styled_message)

def setup_logging(verbose: bool = False):
    """Configura el sistema de logging."""
    # Configuración del logger principal (raíz)
    root_logger = logging.getLogger()
    # Eliminar handlers preexistentes para evitar duplicados si esta función se llama varias veces
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    base_level = logging.DEBUG if verbose else logging.INFO
    # El logger raíz debería tener el nivel más permisivo que cualquiera de sus handlers.
    # Si queremos que FileHandler capture DEBUG pero ConsoleHandler solo INFO, el raíz debe ser DEBUG.
    root_logger.setLevel(logging.DEBUG) # Establecer en DEBUG para permitir que los handlers filtren

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # Handler para la consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(base_level) # Nivel basado en verbose para la consola
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler para el archivo de errores (processing_errors.log)
    # Capturará WARNING, ERROR, CRITICAL
    error_log_file = Path.cwd() / 'processing_errors.log'
    file_handler = logging.FileHandler(error_log_file, mode='a', encoding='utf-8') # 'a' para append
    file_handler.setLevel(logging.WARNING) # Solo WARNING y superiores en el archivo
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if verbose:
        cprint("Logging detallado activado. Los errores también se guardarán en processing_errors.log", level="DEBUG")
    else:
        # Incluso si no es verbose, informar sobre el archivo de log de errores si se crea/usa.
        # Podríamos verificar si el handler se añadió o si el archivo existe.
        cprint(f"Los warnings y errores se guardarán en: {error_log_file}", level="INFO")

    # Configurar loggers específicos para debug si es verbose (esto ya estaba)
    if verbose:
        logging.getLogger("dataset.processing.segmenters.heading_segmenter").setLevel(logging.DEBUG)
        logging.getLogger("dataset.processing.profile_manager").setLevel(logging.DEBUG)

def list_profiles(manager: ProfileManager):
    """Lista todos los perfiles disponibles."""
    profiles = manager.list_profiles()
    if not profiles:
        cprint("No se encontraron perfiles. Verifique el directorio de perfiles.", level="WARNING")
        return
    
    cprint(f"Perfiles disponibles ({len(profiles)}):", level="HEADER", emoji=ConsoleStyle.LIST_EMOJI, bold=True)
    for profile in profiles:
        print(f"{ConsoleStyle.PROFILE_EMOJI} {ConsoleStyle.BOLD}{profile['name']}{ConsoleStyle.ENDC}: {profile['description']}")
        print(f"  {ConsoleStyle.CYAN}Segmentador:{ConsoleStyle.ENDC} {profile['segmenter']}")
        print(f"  {ConsoleStyle.CYAN}Formatos:{ConsoleStyle.ENDC} {', '.join(profile['file_types'])}")
        print()

# Nueva estructura para las estadísticas
class ProcessingStats:
    def __init__(self):
        self.total_files_attempted = 0
        self.success_with_units = 0
        self.success_no_units = 0 # Casos donde el procesamiento es OK pero no hay segmentos (ej. doc vacío bien manejado)
        self.loader_errors = 0      # Errores específicos del loader (archivo corrupto, no encontrado por loader)
        self.config_errors = 0      # Errores de configuración (perfil no encontrado, etc.)
        self.processing_exceptions = 0 # Otras excepciones durante el pipeline (segmentador, preprocesador)
        self.failed_files_details = [] # Lista de tuplas (filepath, error_type, message)
        
        # Nuevas estadísticas de timing
        self.start_time = None
        self.end_time = None
        self.file_times = {}  # {filepath: {'start': time, 'end': time, 'duration': seconds}}
        self.total_processing_time = 0
        self.average_time_per_file = 0
        self.fastest_file = None
        self.slowest_file = None
        self._lock = threading.Lock()  # Para thread safety

    def add_failure(self, filepath: str, error_type: str, message: str):
        with self._lock:
            self.failed_files_details.append((filepath, error_type, message))

    def start_timing(self):
        """Inicia el cronómetro general"""
        self.start_time = time.time()
        
    def end_timing(self):
        """Termina el cronómetro general y calcula estadísticas"""
        self.end_time = time.time()
        self.total_processing_time = self.end_time - self.start_time
        
        # Calcular estadísticas de archivos
        if self.file_times:
            durations = [info['duration'] for info in self.file_times.values()]
            self.average_time_per_file = sum(durations) / len(durations)
            
            # Encontrar el más rápido y más lento
            fastest_time = min(durations)
            slowest_time = max(durations)
            
            for filepath, info in self.file_times.items():
                if info['duration'] == fastest_time:
                    self.fastest_file = (filepath, fastest_time)
                if info['duration'] == slowest_time:
                    self.slowest_file = (filepath, slowest_time)
    
    def start_file_timing(self, filepath: str):
        """Inicia el cronómetro para un archivo específico"""
        with self._lock:
            self.file_times[filepath] = {'start': time.time()}
    
    def end_file_timing(self, filepath: str):
        """Termina el cronómetro para un archivo específico"""
        with self._lock:
            if filepath in self.file_times:
                end_time = time.time()
                self.file_times[filepath]['end'] = end_time
                self.file_times[filepath]['duration'] = end_time - self.file_times[filepath]['start']

def format_duration(seconds: float) -> str:
    """Formatea una duración en segundos a un formato legible"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"

def core_process(manager: ProfileManager, input_path: Path, profile_name_override: Optional[str], output_spec: Optional[str], cli_args: argparse.Namespace, output_format: str = "ndjson") -> tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    """Procesa un único archivo y guarda el resultado.
    
    Args:
        manager: Instancia de ProfileManager.
        input_path: Ruta al archivo individual que se está procesando.
        profile_name_override: El nombre del perfil especificado por el usuario, o None si se debe detectar automáticamente.
        output_spec: La ruta de salida especificada por el usuario, que podría ser un archivo o un directorio.
        cli_args: El objeto argparse.Namespace completo que contiene todos los argumentos de la CLI.
        output_format: Formato de salida ("ndjson" o "json")

    Returns:
        Tuple con (result_code: str, message: Optional[str], document_metadata: Optional[Dict], segments: Optional[List], segmenter_stats: Optional[Dict])
    """
    # DEBUG: Imprimir cli_args.input_path y la evaluación de is_input_dir_mode
    resolved_input_path_for_mode_check = Path(cli_args.input_path).resolve()
    is_input_dir_mode_eval = resolved_input_path_for_mode_check.is_dir()
    logging.debug(f"DEBUG_PATH: cli_args.input_path = {cli_args.input_path}")
    logging.debug(f"DEBUG_PATH: resolved_input_path_for_mode_check = {resolved_input_path_for_mode_check}")
    logging.debug(f"DEBUG_PATH: is_input_dir_mode_eval = {is_input_dir_mode_eval}")
    logging.debug(f"DEBUG_PATH: input_path (actual) = {input_path}")
    logging.debug(f"DEBUG_PATH: output_spec = {output_spec}")

    if not input_path.exists() or not input_path.is_file():
        cprint(f"Archivo no encontrado o no es un archivo válido: {input_path}", level="ERROR")
        return 'CONFIG_ERROR', f"Archivo no encontrado o no es un archivo válido: {input_path}", None, None, None
    
    cprint(f"Procesando archivo: {input_path}", level="INFO", emoji=ConsoleStyle.FILE_EMOJI, bold=True)

    profile_name = profile_name_override
    extracted_content_for_detection = None
    
    if not profile_name:
        # Para detección automática, necesitamos extraer el contenido preservando estructura
        if input_path.suffix.lower() == '.pdf':
            cprint(f"Extrayendo contenido de PDF para detección automática...", level="INFO", emoji="🔍")
            try:
                # Extraer contenido del PDF preservando estructura línea por línea
                import fitz  # PyMuPDF
                
                doc = fitz.open(str(input_path))
                text_lines = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # Extraer texto preservando saltos de línea
                    page_text = page.get_text()
                    
                    # Dividir en líneas y preservar estructura
                    lines = page_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:  # Solo agregar líneas no vacías
                            text_lines.append(line)
                
                doc.close()
                
                # Crear texto estructurado preservando saltos de línea individuales
                extracted_content_for_detection = '\n'.join(text_lines)
                cprint(f"Contenido extraído: {len(text_lines)} líneas, {len(extracted_content_for_detection)} caracteres", level="DEBUG")
                
            except Exception as e:
                cprint(f"Error extrayendo contenido para detección: {str(e)}", level="WARNING")
                # Fallback al método anterior
                try:
                    from dataset.processing.loaders.pdf_loader import PDFLoader
                    temp_loader = PDFLoader(str(input_path))
                    temp_data = temp_loader.load()
                    
                    blocks = temp_data.get('blocks', [])
                    if blocks:
                        text_parts = []
                        for block in blocks:
                            block_text = block.get('text', '').strip()
                            if block_text:
                                text_parts.append(block_text)
                        extracted_content_for_detection = '\n\n'.join(text_parts)
                        cprint(f"Usando fallback: {len(extracted_content_for_detection)} caracteres", level="DEBUG")
                except Exception as e2:
                    cprint(f"Error en fallback: {str(e2)}", level="WARNING")
        
        # Detectar perfil con contenido extraído si está disponible
        profile_name = manager.get_profile_for_file(input_path, extracted_content_for_detection)
        if profile_name:
            cprint(f"Perfil detectado automáticamente: {profile_name}", level="INFO", emoji=ConsoleStyle.PROFILE_EMOJI)
        else:
            cprint(f"No se pudo detectar un perfil adecuado para {input_path.name}. Especifique uno con --profile o verifique las extensiones.", level="ERROR")
            # No listamos perfiles aquí para no inundar la consola si son muchos archivos
            return 'CONFIG_ERROR', f"No se pudo detectar un perfil adecuado para {input_path.name}", None, None, None
    else:
        cprint(f"Usando perfil: {profile_name}", level="INFO", emoji=ConsoleStyle.PROFILE_EMOJI)

    # Manejo del archivo de salida
    output_file_path: Path
    is_input_dir_mode = Path(cli_args.input_path).resolve().is_dir() # Verifica si la entrada original a process_path era un dir

    # === NUEVA FUNCIONALIDAD: Calcular información de estructura de carpetas ===
    folder_structure_info = {}
    if is_input_dir_mode:
        # Si estamos procesando un directorio, calcular información de estructura
        base_input_dir = Path(cli_args.input_path).resolve()
        try:
            relative_path = input_path.relative_to(base_input_dir)
            folder_structure_info = {
                "source_base_directory": str(base_input_dir),
                "relative_path": str(relative_path),
                "parent_folders": list(relative_path.parent.parts) if relative_path.parent != Path('.') else [],
                "folder_depth": len(relative_path.parent.parts),
                "is_in_subdirectory": relative_path.parent != Path('.'),
                "immediate_parent_folder": relative_path.parent.name if relative_path.parent != Path('.') else None
            }
        except ValueError:
            # input_path no está dentro de base_input_dir (caso edge)
            folder_structure_info = {
                "source_base_directory": str(base_input_dir),
                "relative_path": str(input_path),
                "parent_folders": [],
                "folder_depth": 0,
                "is_in_subdirectory": False,
                "immediate_parent_folder": None,
                "note": "File outside base directory"
            }

    if output_spec:
        output_arg_path = Path(output_spec).resolve()
        if output_arg_path.is_dir():
            # CASO: --output es un directorio
            output_arg_path.mkdir(parents=True, exist_ok=True)
            if is_input_dir_mode:
                # Entrada original fue un dir, salida es un dir: replicar estructura
                relative_path = input_path.relative_to(Path(cli_args.input_path).resolve())
                # Incluir la extensión original para evitar conflictos de nombres
                base_name = f"{input_path.stem}_{input_path.suffix[1:]}" if input_path.suffix else input_path.stem
                output_file_path = output_arg_path / relative_path.parent / f"{base_name}.{output_format}"
            else:
                # Entrada original fue un archivo, salida es un dir: archivo plano en dir de salida
                # Incluir la extensión original para evitar conflictos de nombres
                base_name = f"{input_path.stem}_{input_path.suffix[1:]}" if input_path.suffix else input_path.stem
                output_file_path = output_arg_path / f"{base_name}.{output_format}"
            output_file_path.parent.mkdir(parents=True, exist_ok=True) # Asegurar que el subdirectorio también exista
        else:
            # CASO: --output es un nombre de archivo explícito
            if is_input_dir_mode:
                # Este caso es manejado como error en process_path, core_process no debería llegar aquí con esta combinación.
                # Si llega, es un error de lógica, pero para evitar un crash, se usa un fallback.
                cprint(f"Advertencia: Se especificó --output como archivo pero la entrada es un directorio. Usando CWD para {input_path.name}", level="WARNING")
                # Incluir la extensión original para evitar conflictos de nombres
                base_name = f"{input_path.stem}_{input_path.suffix[1:]}" if input_path.suffix else input_path.stem
                output_file_path = Path.cwd() / f"{base_name}.{output_format}" 
            else:
                # Entrada original fue archivo, salida es archivo: usar el nombre de archivo de salida provisto
                output_file_path = output_arg_path
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # CASO: --output NO se especificó
        # Siempre guardar en CWD si no hay --output, sin importar si es archivo o dir.
        # Incluir la extensión original para evitar conflictos de nombres
        base_name = f"{input_path.stem}_{input_path.suffix[1:]}" if input_path.suffix else input_path.stem
        output_file_path = Path.cwd() / f"{base_name}.{output_format}"

    cprint(f"Archivo de salida: {output_file_path}", level="INFO", emoji=ConsoleStyle.SAVE_EMOJI)
    
    try:
        # Obtener parámetros de override si están disponibles
        language_override = getattr(cli_args, 'language_override', None)
        author_override = getattr(cli_args, 'author_override', None)
        
        # 🔧 NUEVO: Obtener configuración JSON si está disponible
        job_config_dict = None
        if hasattr(cli_args, 'json_filter_config') and cli_args.json_filter_config is not None:
            job_config_dict = {'json_config': cli_args.json_filter_config}
            cprint(f"Aplicando configuración de filtros JSON al procesamiento...", level="INFO", emoji="🔧")
        
        segments, segmenter_stats, document_metadata = manager.process_file(
            file_path=str(input_path),
            profile_name=profile_name,
            output_file=str(output_file_path),  # ✅ CORREGIDO: output_file en lugar de output_dir
            encoding=cli_args.encoding,
            force_content_type=cli_args.force_type,
            confidence_threshold=cli_args.confidence_threshold,
            language_override=language_override,
            author_override=author_override,
            output_format=output_format,
            folder_structure_info=folder_structure_info,  # Pasar información de estructura
            job_config_dict=job_config_dict  # 🔧 NUEVO: Pasar configuración JSON
        )
        
        if isinstance(segments, tuple) and len(segments) == 3:
            segments, segmenter_stats, document_metadata = segments
        elif isinstance(segments, list):
            cprint(f"No se recibieron estadísticas del segmentador para {input_path.name}.", level="WARNING")
            # No consideramos esto un error fatal para la tupla de retorno, pero el log lo capturará.
        else:
            error_msg = f"Resultado inesperado del procesamiento para {input_path.name}: {type(segments)}"
            cprint(error_msg, level="ERROR")
            return 'PROCESSING_EXCEPTION', error_msg, None, None, None

        if segments:
            cprint(f"Se encontraron {len(segments)} unidades en {input_path.name}.", level="SUCCESS", emoji=ConsoleStyle.SUCCESS_EMOJI)
            if segmenter_stats:
                # No imprimir stats detalladas por archivo en modo directorio para no ser muy verboso
                # A menos que cli_args.verbose esté activado
                if cli_args.verbose or not is_input_dir_mode:
                    cprint(f"Estadísticas del Segmentador ({input_path.name}):", level="INFO", emoji=ConsoleStyle.LIST_EMOJI)
                    for key, value in segmenter_stats.items():
                        cprint(f"  - {key.replace('_', ' ').capitalize()}: {value}", level="INFO")
            
            if cli_args.verbose and document_metadata:
                 cprint(f"Metadatos del Documento ({input_path.name}):", level="DEBUG", emoji="📝")
                 excluded_meta_keys = ['source_file_path', 'original_contexto', 'blocks', 'error']
                 for key, value in document_metadata.items():
                    if key not in excluded_meta_keys and value is not None:
                        value_str = str(value)
                        if len(value_str) > 100: value_str = value_str[:97] + "..."
                        cprint(f"  - {key.replace('_', ' ').capitalize()}: {value_str}", level="DEBUG")

            if cli_args.verbose:
                cprint(f"Ejemplos de segmentos ({input_path.name}, primeros 3):", level="DEBUG", emoji="🔬")
                for i, segment in enumerate(segments[:3]):  # Reducido a solo 3 ejemplos
                    # Los segmentos ahora son instancias de ProcessedContentItem
                    text_preview = segment.texto_segmento[:30] if hasattr(segment, 'texto_segmento') else str(segment)[:30]
                    segment_type = segment.tipo_segmento if hasattr(segment, 'tipo_segmento') else 'unknown'
                    print(f"{ConsoleStyle.BLUE}[{i+1}]{ConsoleStyle.ENDC} {segment_type}: {text_preview}...")
            return 'SUCCESS_WITH_UNITS', None, document_metadata, segments, segmenter_stats
        else:
            # Revisar si el loader reportó un error o advertencia específica
            loader_error = document_metadata.get('error')
            loader_warning = document_metadata.get('warning')

            if loader_error:
                # Si el loader tuvo un error (ej. archivo corrupto), este es el mensaje principal.
                cprint(f"Error del cargador: {loader_error}", level="ERROR", emoji=ConsoleStyle.ERROR_EMOJI)
                return 'LOADER_ERROR', loader_error, document_metadata, None, None
            elif document_metadata.get('error'): # Otro tipo de error en metadata (ej. preprocesador, segmentador)
                # Esto podría ser un error del preprocesador o segmentador capturado en ProfileManager
                processing_error = document_metadata.get('error')
                cprint(f"Error de procesamiento: {processing_error}", level="ERROR", emoji=ConsoleStyle.ERROR_EMOJI)
                return 'PROCESSING_EXCEPTION', processing_error, document_metadata, None, None
            elif loader_warning:
                cprint(f"Advertencia: {loader_warning} (No se encontraron unidades en {input_path.name})", level="WARNING", emoji=ConsoleStyle.WARNING_EMOJI)
                return 'SUCCESS_NO_UNITS', loader_warning, document_metadata, None, segmenter_stats # Considerado un éxito, pero sin unidades debido a una advertencia
            else:
                cprint(f"No se encontraron unidades procesables en {input_path.name} con el perfil '{profile_name}'.", level="WARNING", emoji=ConsoleStyle.WARNING_EMOJI)
                return 'SUCCESS_NO_UNITS', f"No se encontraron unidades con perfil '{profile_name}'", document_metadata, None, segmenter_stats
    except Exception as e:
        # Captura de excepciones generales que ocurran dentro de core_process 
        # (antes o después de la llamada a ProfileManager.process_file si algo más falla aquí)
        error_msg = f"Excepción inesperada en core_process para {input_path.name}: {str(e)}"
        cprint(error_msg, level="ERROR", emoji=ConsoleStyle.ERROR_EMOJI)
        logging.exception(f"Detalles de la excepción inesperada en core_process para {input_path.name}:")
        return 'PROCESSING_EXCEPTION', str(e), None, None, None

def _process_single_file(manager: ProfileManager, file_path: Path, args, base_output_path: Path = None, output_format: str = "ndjson", stats: ProcessingStats = None) -> tuple[str, Optional[str]]:
    """Wrapper de compatibilidad para core_process que mantiene la interfaz original.
    
    Args:
        manager: Instancia de ProfileManager.
        file_path: Ruta al archivo a procesar.
        args: Argumentos de línea de comandos.
        base_output_path: Directorio base para la salida si se procesa un directorio (no usado en core_process).
        output_format: Formato de salida ("ndjson" o "json")
        stats: Objeto de estadísticas para timing

    Returns:
        Tuple con (código de resultado: str, mensaje de error/advertencia opcional: str)
    """
    # Iniciar timing para este archivo
    if stats:
        stats.start_file_timing(str(file_path))
    
    try:
        result_code, message, document_metadata, segments, segmenter_stats = core_process(
            manager=manager,
            input_path=file_path,
            profile_name_override=args.profile,
            output_spec=args.output,
            cli_args=args,
            output_format=output_format
        )
        
        return result_code, message
    finally:
        # Terminar timing para este archivo
        if stats:
            stats.end_file_timing(str(file_path))
            # Mostrar tiempo del archivo si es verbose o si es un solo archivo
            if args.verbose or stats.total_files_attempted == 1:
                duration = stats.file_times[str(file_path)]['duration']
                cprint(f"Tiempo de procesamiento: {format_duration(duration)}", 
                      level="INFO", emoji=ConsoleStyle.TIMER_EMOJI)

def process_path(manager: ProfileManager, args: argparse.Namespace, stats: ProcessingStats) -> None:
    """Procesa un archivo o todos los archivos de un directorio."""
    input_path = Path(args.input_path).resolve()
    
    # Iniciar timing general
    stats.start_timing()
    
    if input_path.is_file():
        files_to_process = [input_path]
        base_output_for_relative_path = None
    elif input_path.is_dir():
        cprint(f"Procesando directorio: {input_path}", level="INFO", bold=True)
        files_to_process = sorted(list(input_path.rglob('*')))
        files_to_process = [f for f in files_to_process if f.is_file()] # Solo archivos
        base_output_for_relative_path = Path(args.input_path).resolve() # Para calcular paths relativos
        if args.output and Path(args.output).is_file():
            cprint(f"Error: La entrada es un directorio ('{args.input_path}') pero la salida ('{args.output}') es un archivo. Use --output con un directorio o no lo especifique.", level="ERROR")
            stats.config_errors += 1 # Contar como error de configuración
            stats.add_failure(str(input_path), "CONFIG_ERROR", "Entrada es directorio, salida es archivo")
            return
    else:
        cprint(f"Ruta de entrada no válida: {input_path}", level="ERROR")
        stats.config_errors += 1
        stats.add_failure(str(input_path), "CONFIG_ERROR", "Ruta de entrada no válida")
        return

    if not files_to_process:
        cprint("No se encontraron archivos para procesar.", level="WARNING")
        return

    cprint(f"Archivos encontrados para procesar: {len(files_to_process)}", level="INFO")
    stats.total_files_attempted = len(files_to_process)

    # Determinar si usar paralelización
    use_parallel = getattr(args, 'parallel', False) and len(files_to_process) > 1
    max_workers = getattr(args, 'max_workers', None)
    
    if use_parallel:
        if max_workers is None:
            max_workers = min(len(files_to_process), os.cpu_count())
        cprint(f"Procesamiento paralelo activado con {max_workers} workers", 
               level="INFO", emoji=ConsoleStyle.PARALLEL_EMOJI, bold=True)
        _process_files_parallel(manager, files_to_process, args, base_output_for_relative_path, stats, max_workers)
    else:
        if len(files_to_process) > 1:
            cprint("Procesamiento secuencial (use --parallel para acelerar)", level="INFO")
        _process_files_sequential(manager, files_to_process, args, base_output_for_relative_path, stats)

    # Terminar timing general
    stats.end_timing()

def _process_files_sequential(manager: ProfileManager, files_to_process: List[Path], args, base_output_for_relative_path: Path, stats: ProcessingStats):
    """Procesa archivos secuencialmente (método original)"""
    for i, file_path in enumerate(files_to_process, 1):
        if len(files_to_process) > 1:
            cprint(f"Procesando {i}/{len(files_to_process)}: {file_path.name}", 
                   level="INFO", emoji=ConsoleStyle.FILE_EMOJI)
        
        result_code, message = _process_single_file(manager, file_path, args, base_output_for_relative_path, stats=stats)
        _update_stats_from_result(stats, file_path, result_code, message)

def _process_files_parallel(manager: ProfileManager, files_to_process: List[Path], args, base_output_for_relative_path: Path, stats: ProcessingStats, max_workers: int):
    """Procesa archivos en paralelo usando ThreadPoolExecutor"""
    
    def process_file_wrapper(file_path):
        """Wrapper para procesar un archivo en un thread"""
        try:
            result_code, message = _process_single_file(manager, file_path, args, base_output_for_relative_path, stats=stats)
            return file_path, result_code, message
        except Exception as e:
            return file_path, 'PROCESSING_EXCEPTION', str(e)
    
    completed_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todos los trabajos
        future_to_file = {executor.submit(process_file_wrapper, file_path): file_path 
                         for file_path in files_to_process}
        
        # Procesar resultados conforme se completan
        for future in as_completed(future_to_file):
            file_path, result_code, message = future.result()
            completed_count += 1
            
            cprint(f"Completado {completed_count}/{len(files_to_process)}: {file_path.name}", 
                   level="INFO", emoji=ConsoleStyle.SUCCESS_EMOJI)
            
            _update_stats_from_result(stats, file_path, result_code, message)

def _update_stats_from_result(stats: ProcessingStats, file_path: Path, result_code: str, message: str):
    """Actualiza las estadísticas basándose en el resultado del procesamiento"""
    if result_code == 'SUCCESS_WITH_UNITS':
        stats.success_with_units += 1
    elif result_code == 'SUCCESS_NO_UNITS':
        stats.success_no_units += 1
        if message: # Guardar la advertencia si existe
             stats.add_failure(str(file_path), "SUCCESS_NO_UNITS_WARN", message)
    elif result_code == 'LOADER_ERROR':
        stats.loader_errors += 1
        stats.add_failure(str(file_path), "LOADER_ERROR", message)
    elif result_code == 'CONFIG_ERROR':
        stats.config_errors += 1
        stats.add_failure(str(file_path), "CONFIG_ERROR", message)
    elif result_code == 'PROCESSING_EXCEPTION':
        stats.processing_exceptions += 1
        stats.add_failure(str(file_path), "PROCESSING_EXCEPTION", message)

def _print_summary(stats: ProcessingStats):
    """Imprime el resumen del procesamiento."""
    cprint("Resumen del Procesamiento:", level="HEADER", bold=True, emoji="📊")
    cprint(f"Total de archivos intentados: {stats.total_files_attempted}", level="INFO")
    cprint(f"  {ConsoleStyle.SUCCESS_EMOJI} Con unidades: {stats.success_with_units}", level="SUCCESS")
    cprint(f"  {ConsoleStyle.WARNING_EMOJI} Sin unidades (OK): {stats.success_no_units}", level="WARNING")
    cprint(f"  {ConsoleStyle.ERROR_EMOJI} Errores de cargador: {stats.loader_errors}", level="ERROR")
    cprint(f"  {ConsoleStyle.ERROR_EMOJI} Errores de configuración: {stats.config_errors}", level="ERROR")
    cprint(f"  {ConsoleStyle.ERROR_EMOJI} Errores de procesamiento: {stats.processing_exceptions}", level="ERROR")

    # Estadísticas de rendimiento
    if stats.total_processing_time > 0:
        cprint("Estadísticas de Rendimiento:", level="HEADER", bold=True, emoji=ConsoleStyle.PERFORMANCE_EMOJI)
        cprint(f"Tiempo total: {format_duration(stats.total_processing_time)}", 
               level="INFO", emoji=ConsoleStyle.TIMER_EMOJI)
        
        if stats.total_files_attempted > 0:
            cprint(f"Tiempo promedio por archivo: {format_duration(stats.average_time_per_file)}", 
                   level="INFO", emoji=ConsoleStyle.TIMER_EMOJI)
            
            # Calcular archivos por minuto
            files_per_minute = (stats.total_files_attempted / stats.total_processing_time) * 60
            cprint(f"Velocidad de procesamiento: {files_per_minute:.1f} archivos/minuto", 
                   level="INFO", emoji=ConsoleStyle.PERFORMANCE_EMOJI)
        
        if stats.fastest_file and stats.slowest_file:
            fastest_path, fastest_time = stats.fastest_file
            slowest_path, slowest_time = stats.slowest_file
            cprint(f"Archivo más rápido: {Path(fastest_path).name} ({format_duration(fastest_time)})", 
                   level="INFO", emoji="🏃")
            cprint(f"Archivo más lento: {Path(slowest_path).name} ({format_duration(slowest_time)})", 
                   level="INFO", emoji="🐌")

    total_fallos = stats.loader_errors + stats.config_errors + stats.processing_exceptions
    if total_fallos > 0:
        cprint(f"Detalle de archivos con errores/advertencias ({len(stats.failed_files_details)} entradas):", level="HEADER", bold=True, emoji="📋")
        # Imprimir primero errores, luego advertencias de 'no unidades'
        for filepath, err_type, msg in sorted(stats.failed_files_details, key=lambda x: x[1] == 'SUCCESS_NO_UNITS_WARN'):
            if err_type == "SUCCESS_NO_UNITS_WARN":
                cprint(f"- {filepath}: {msg} (No se encontraron unidades)", level="WARNING")
            else:
                cprint(f"- {filepath}: [{err_type}] {msg}", level="ERROR")
    
    if stats.total_files_attempted == 0:
        cprint("No se procesó ningún archivo.", level="INFO")

def signal_handler(sig, frame):
    """Manejador para la señal SIGINT (Ctrl+C)."""
    cprint("\nProcesamiento interrumpido por el usuario (Ctrl+C). Saliendo...", level="WARNING", bold=True)
    # Intentar imprimir un resumen parcial si las estadísticas están disponibles y tienen datos
    # Esto es un 'mejor esfuerzo' y puede que no siempre funcione dependiendo de dónde se interrumpió.
    # Necesitaríamos que 'processing_stats' sea accesible globalmente o pasada aquí, lo cual complica.
    # Por ahora, solo salimos limpiamente.
    # Alternativamente, se podría levantar una excepción personalizada que el bucle principal capture.
    sys.exit(130) # Código de salida común para interrupción por Ctrl+C

def main():
    # Registrar el manejador de señal para SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="Procesa archivos usando perfiles de segmentación.")
    parser.add_argument("input_path", nargs='?', help="Ruta al archivo o directorio a procesar.")
    parser.add_argument("--list-profiles", action="store_true", help="Muestra los perfiles de procesamiento disponibles.")
        
    processing_options = parser.add_argument_group(f'{ConsoleStyle.GREEN}Opciones de Procesamiento{ConsoleStyle.ENDC}')
    processing_options.add_argument("--profile", "-p", help="Nombre del perfil a utilizar (si se omite, se intentará detectar automáticamente).")
    processing_options.add_argument("--output", "-o", 
                                    help="Ruta del archivo de salida NDJSON (si la entrada es un archivo) o directorio de salida (si la entrada es un directorio). "
                                         "Si se omite, la salida se genera junto al archivo de entrada o en el directorio de entrada respectivo.")
    processing_options.add_argument("--force-type", choices=["poemas", "escritos", "canciones", "capitulos"], 
                      help="Forzar un tipo de contenido específico para el loader (ignora la detección automática del loader).")
    processing_options.add_argument("--confidence-threshold", type=float, default=0.5,
                      help="Umbral de confianza para segmentadores que lo soporten (ej. detector de poemas) (0.0-1.0, default: 0.5).")
    processing_options.add_argument("--language-override", 
                      help="Forzar un idioma específico para todos los documentos (ej. 'es', 'en', 'fr'). Ignora la detección automática.")
    processing_options.add_argument("--author-override", 
                      help="Forzar un autor específico para todos los documentos. Ignora la detección automática.")
    
    # Opciones generales
    general_options = parser.add_argument_group(f'{ConsoleStyle.YELLOW}Opciones Generales{ConsoleStyle.ENDC}')
    general_options.add_argument("--verbose", "-v", action="store_true", help="Muestra información de depuración detallada durante el procesamiento.")
    general_options.add_argument("--profiles-dir", help="Ruta a un directorio de perfiles personalizado.")
    general_options.add_argument("--encoding", default="utf-8", help="Codificación de caracteres del archivo de entrada (default: utf-8).")
    
    # Opciones de rendimiento
    performance_options = parser.add_argument_group(f'{ConsoleStyle.CYAN}Opciones de Rendimiento{ConsoleStyle.ENDC}')
    performance_options.add_argument("--parallel", action="store_true", 
                      help="Procesar múltiples archivos en paralelo para mejorar el rendimiento.")
    performance_options.add_argument("--max-workers", type=int, 
                      help="Número máximo de workers paralelos (default: número de CPUs disponibles).")
    performance_options.add_argument("--show-timing", action="store_true", 
                      help="Mostrar tiempos de procesamiento detallados para cada archivo.")
    
    args = parser.parse_args()
    
    # Configurar logging
    # setup_logging se encarga de los mensajes de logging, cprint para mensajes directos del script.
    setup_logging(args.verbose) 
    
    # Inicializar gestor de perfiles
    try:
        manager = ProfileManager(args.profiles_dir)
    except Exception as e:
        cprint(f"Error al inicializar ProfileManager: {e}", level="ERROR", bold=True)
        sys.exit(1) # Indica fallo

    if args.list_profiles:
        list_profiles(manager)
        sys.exit(0)

    if not args.input_path:
        parser.print_help()
        cprint("Error: Debe especificar una ruta de entrada o usar --list-profiles.", level="ERROR")
        sys.exit(1)
    
    # Inicializar estadísticas
    processing_stats = ProcessingStats()

    # Procesar el archivo o directorio
    # La función process_path ahora actualizará processing_stats directamente
    process_path(manager, args, processing_stats)

    # Imprimir el resumen
    _print_summary(processing_stats)

    # Código de salida basado en si hubo errores graves
    if processing_stats.loader_errors > 0 or \
       processing_stats.config_errors > 0 or \
       processing_stats.processing_exceptions > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()