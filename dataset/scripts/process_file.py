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

    def add_failure(self, filepath: str, error_type: str, message: str):
        self.failed_files_details.append((filepath, error_type, message))

def core_process(manager: ProfileManager, input_path: Path, profile_name_override: Optional[str], output_spec: Optional[str], cli_args: argparse.Namespace) -> tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    """Procesa un único archivo y guarda el resultado.
    
    Args:
        manager: Instancia de ProfileManager.
        input_path: Ruta al archivo individual que se está procesando.
        profile_name_override: El nombre del perfil especificado por el usuario, o None si se debe detectar automáticamente.
        output_spec: La ruta de salida especificada por el usuario, que podría ser un archivo o un directorio.
        cli_args: El objeto argparse.Namespace completo que contiene todos los argumentos de la CLI.

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
    if not profile_name:
        profile_name = manager.get_profile_for_file(input_path)
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

    if output_spec:
        output_arg_path = Path(output_spec).resolve()
        if output_arg_path.is_dir():
            # CASO: --output es un directorio
            output_arg_path.mkdir(parents=True, exist_ok=True)
            if is_input_dir_mode:
                # Entrada original fue un dir, salida es un dir: replicar estructura
                relative_path = input_path.relative_to(Path(cli_args.input_path).resolve())
                output_file_path = output_arg_path / relative_path.parent / f"{input_path.stem}.ndjson"
            else:
                # Entrada original fue un archivo, salida es un dir: archivo plano en dir de salida
                output_file_path = output_arg_path / f"{input_path.stem}.ndjson"
            output_file_path.parent.mkdir(parents=True, exist_ok=True) # Asegurar que el subdirectorio también exista
        else:
            # CASO: --output es un nombre de archivo explícito
            if is_input_dir_mode:
                # Este caso es manejado como error en process_path, core_process no debería llegar aquí con esta combinación.
                # Si llega, es un error de lógica, pero para evitar un crash, se usa un fallback.
                cprint(f"Advertencia: Se especificó --output como archivo pero la entrada es un directorio. Usando CWD para {input_path.name}", level="WARNING")
                output_file_path = Path.cwd() / f"{input_path.stem}.ndjson" 
            else:
                # Entrada original fue archivo, salida es archivo: usar el nombre de archivo de salida provisto
                output_file_path = output_arg_path
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # CASO: --output NO se especificó
        # Siempre guardar en CWD si no hay --output, sin importar si es archivo o dir.
        output_file_path = Path.cwd() / f"{input_path.stem}.ndjson"

    cprint(f"Archivo de salida: {output_file_path}", level="INFO", emoji=ConsoleStyle.SAVE_EMOJI)
    
    try:
        # Obtener parámetros de override si están disponibles
        language_override = getattr(cli_args, 'language_override', None)
        author_override = getattr(cli_args, 'author_override', None)
        
        segments, segmenter_stats, document_metadata = manager.process_file(
            file_path=str(input_path),
            profile_name=profile_name,
            output_dir=str(output_file_path),
            encoding=cli_args.encoding,
            force_content_type=cli_args.force_type,
            confidence_threshold=cli_args.confidence_threshold,
            language_override=language_override,
            author_override=author_override
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
                cprint(f"Ejemplos de segmentos ({input_path.name}, primeros 12):", level="DEBUG", emoji="🔬")
                for i, segment in enumerate(segments[:12]):
                    # Los segmentos ahora son instancias de ProcessedContentItem
                    text_preview = segment.texto_segmento[:50] if hasattr(segment, 'texto_segmento') else str(segment)[:50]
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

def _process_single_file(manager: ProfileManager, file_path: Path, args, base_output_path: Path = None) -> tuple[str, Optional[str]]:
    """Wrapper de compatibilidad para core_process que mantiene la interfaz original.
    
    Args:
        manager: Instancia de ProfileManager.
        file_path: Ruta al archivo a procesar.
        args: Argumentos de línea de comandos.
        base_output_path: Directorio base para la salida si se procesa un directorio (no usado en core_process).

    Returns:
        Tuple con (código de resultado: str, mensaje de error/advertencia opcional: str)
    """
    result_code, message, document_metadata, segments, segmenter_stats = core_process(
        manager=manager,
        input_path=file_path,
        profile_name_override=args.profile,
        output_spec=args.output,
        cli_args=args
    )
    
    return result_code, message

def process_path(manager: ProfileManager, args: argparse.Namespace, stats: ProcessingStats) -> None:
    """Procesa un archivo o todos los archivos de un directorio."""
    input_path = Path(args.input_path).resolve()
    
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

    for file_path in files_to_process:
        # Aquí no incrementamos total_files_attempted porque ya se hizo con len(files_to_process)
        # _process_single_file se encarga de la lógica de un archivo
        result_code, message = _process_single_file(manager, file_path, args, base_output_for_relative_path)
        
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
        # No hay 'else' explícito; si se añade un nuevo código, se ignoraría aquí hasta que se maneje.

    # El resumen se imprimirá en main después de que esto termine.

def _print_summary(stats: ProcessingStats):
    """Imprime el resumen del procesamiento."""
    cprint("Resumen del Procesamiento:", level="HEADER", bold=True, emoji="📊")
    cprint(f"Total de archivos intentados: {stats.total_files_attempted}", level="INFO")
    cprint(f"  {ConsoleStyle.SUCCESS_EMOJI} Con unidades: {stats.success_with_units}", level="SUCCESS")
    cprint(f"  {ConsoleStyle.WARNING_EMOJI} Sin unidades (OK): {stats.success_no_units}", level="WARNING")
    cprint(f"  {ConsoleStyle.ERROR_EMOJI} Errores de cargador: {stats.loader_errors}", level="ERROR")
    cprint(f"  {ConsoleStyle.ERROR_EMOJI} Errores de configuración: {stats.config_errors}", level="ERROR")
    cprint(f"  {ConsoleStyle.ERROR_EMOJI} Errores de procesamiento: {stats.processing_exceptions}", level="ERROR")

    total_fallos = stats.loader_errors + stats.config_errors + stats.processing_exceptions
    if total_fallos > 0:
        cprint(f"Detalle de archivos con errores/advertencias ({len(stats.failed_files_details)} entradas):", level="HEADER", bold=True, emoji=" 목록")
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