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
from typing import List, Dict, Any
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
    level = logging.DEBUG if verbose else logging.INFO
    # Usar cprint para el mensaje de configuración de logging si es relevante,
    # o mantener logging.basicConfig para su propio formato.
    # Por ahora, se mantiene el basicConfig estándar.
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    if verbose:
        cprint("Logging detallado activado.", level="DEBUG")
    
    # Configurar loggers específicos para debug
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

def process_file(manager: ProfileManager, args):
    """Procesa un archivo según los argumentos proporcionados."""
    file_path = Path(args.file)
    if not file_path.exists():
        cprint(f"Archivo no encontrado: {file_path}", level="ERROR")
        return False
    
    cprint(f"Procesando archivo: {file_path.name}", level="INFO", emoji=ConsoleStyle.FILE_EMOJI, bold=True)

    # Si no se especificó un perfil, intentar detectarlo automáticamente
    profile_name = args.profile
    if not profile_name:
        profile_name = manager.get_profile_for_file(file_path)
        if profile_name:
            cprint(f"Perfil detectado automáticamente: {profile_name}", level="INFO", emoji=ConsoleStyle.PROFILE_EMOJI)
        else:
            cprint("No se pudo detectar un perfil adecuado. Especifique uno con --profile", level="ERROR")
            list_profiles(manager) # Mostrar perfiles disponibles para ayudar al usuario
            return False
    else:
        cprint(f"Usando perfil: {profile_name}", level="INFO", emoji=ConsoleStyle.PROFILE_EMOJI)

    # Manejo del archivo de salida
    output_path_arg = args.output
    if not output_path_arg:
        # Generar nombre de archivo de salida por defecto en el CWD
        default_output_filename = f"{file_path.stem}.ndjson"
        output_path_arg = Path.cwd() / default_output_filename
        cprint(f"No se especificó archivo de salida. Usando por defecto: {output_path_arg}", level="INFO", emoji=ConsoleStyle.SAVE_EMOJI)
    else:
        output_path_arg = Path(output_path_arg) # Asegurarse que es un objeto Path
        cprint(f"Archivo de salida: {output_path_arg}", level="INFO", emoji=ConsoleStyle.SAVE_EMOJI)
    
    try:
        # Procesar el archivo
        # Ahora esperamos una tupla de tres elementos: segments, segmenter_stats, document_metadata
        segments, segmenter_stats, document_metadata = manager.process_file(
            file_path=str(file_path),
            profile_name=profile_name,
            output_path=str(output_path_arg),
            encoding=args.encoding,
            force_content_type=args.force_type,
            confidence_threshold=args.confidence_threshold
        )
        
        if isinstance(segments, tuple) and len(segments) == 3:
            segments, segmenter_stats, document_metadata = segments
        elif isinstance(segments, list): # Para compatibilidad si alguna llamada no devuelve stats
            segments = segments
            cprint("No se recibieron estadísticas del segmentador.", level="WARNING")
        else:
            cprint(f"Resultado inesperado del procesamiento: {type(segments)}", level="ERROR")
            return False

        # Mostrar resultados
        if segments:
            cprint(f"{ConsoleStyle.SUCCESS_EMOJI} Se encontraron {len(segments)} unidades en el archivo.", level="SUCCESS")
            
            # Mostrar estadísticas del segmentador si existen
            if segmenter_stats:
                cprint("\nEstadísticas del Segmentador:", level="INFO", emoji=ConsoleStyle.LIST_EMOJI)
                for key, value in segmenter_stats.items():
                    cprint(f"  - {key.replace('_', ' ').capitalize()}: {value}", level="INFO")
            
            # Mostrar metadatos del documento si existen y verbose está activado
            if args.verbose and document_metadata:
                cprint("\nMetadatos del Documento:", level="DEBUG", emoji="📝")
                # Filtrar metadatos que no queremos mostrar o que son muy largos/complejos
                # o que ya se muestran de otra forma (como source_file_path)
                excluded_meta_keys = ['source_file_path', 'original_contexto', 'blocks', 'error']
                for key, value in document_metadata.items():
                    if key not in excluded_meta_keys and value is not None:
                        # Truncar valores largos para la previsualización
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:97] + "..."
                        cprint(f"  - {key.replace('_', ' ').capitalize()}: {value_str}", level="DEBUG")

            # Si está en modo verbose, mostrar los primeros N segmentos para depuración
            if args.verbose:
                cprint("\nEjemplos de segmentos encontrados (primeros 12):", level="DEBUG", emoji="🔬")
                for i, segment in enumerate(segments[:12]):
                    text_preview = ""
                    if 'title' in segment:
                        text_preview = segment['title'][:50]
                    elif 'text' in segment:
                        text_preview = segment['text'][:50]
                    
                    print(f"{ConsoleStyle.BLUE}[{i+1}]{ConsoleStyle.ENDC} {segment.get('type', 'unknown')}: {text_preview}...")
            
            return True
        else:
            cprint("No se encontraron unidades en el archivo.", level="WARNING", bold=True)
            if args.verbose:
                cprint("\nVerifique que el archivo contiene la estructura esperada por el perfil.", level="INFO")
                cprint("Puede probar con otro perfil o ajustar los parámetros de detección.", level="INFO")
            return False
    except Exception as e:
        cprint(f"Ocurrió un error durante el procesamiento: {str(e)}", level="ERROR", bold=True)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description=f"{ConsoleStyle.HEADER}{ConsoleStyle.BOLD}Herramienta de Procesamiento de Archivos v1.0{ConsoleStyle.ENDC}")
    
    # Modo de lista o modo de procesamiento
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-profiles", action="store_true", help="Muestra los perfiles de procesamiento disponibles.")
    group.add_argument("file", nargs="?", help="Ruta al archivo que se desea procesar.")
    
    # Opciones para modo de procesamiento
    processing_options = parser.add_argument_group(f'{ConsoleStyle.GREEN}Opciones de Procesamiento{ConsoleStyle.ENDC}')
    processing_options.add_argument("--profile", "-p", help="Nombre del perfil a utilizar (si se omite, se intentará detectar automáticamente).")
    processing_options.add_argument("--output", "-o", help="Ruta del archivo de salida NDJSON (si se omite, se genera uno por defecto: <nombre_archivo_entrada>.ndjson en el directorio actual).")
    processing_options.add_argument("--force-type", choices=["poemas", "escritos", "canciones", "capitulos"], 
                      help="Forzar un tipo de contenido específico para el loader (ignora la detección automática del loader).")
    processing_options.add_argument("--confidence-threshold", type=float, default=0.5,
                      help="Umbral de confianza para segmentadores que lo soporten (ej. detector de poemas) (0.0-1.0, default: 0.5).")
    
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
        return False # Indica fallo

    # Procesar según el modo
    if args.list_profiles:
        list_profiles(manager)
        return True # Indica éxito
    else:
        if not args.file: # Asegurarse que args.file está presente si no es --list-profiles
            parser.error("el argumento file es obligatorio cuando no se usa --list-profiles")
        return process_file(manager, args)

if __name__ == "__main__":
    # sys.exit(main()) # Línea original comentada
    success = main() # Ejecutar main y obtener su resultado booleano
    sys.exit(0 if success else 1) # Salir con 0 si success es True (éxito), sino con 1 (error) 