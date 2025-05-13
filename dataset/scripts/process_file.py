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

def setup_logging(verbose: bool = False):
    """Configura el sistema de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Configurar loggers específicos para debug
    if verbose:
        logging.getLogger("dataset.processing.segmenters.heading_segmenter").setLevel(logging.DEBUG)
        logging.getLogger("dataset.processing.profile_manager").setLevel(logging.DEBUG)

def list_profiles(manager: ProfileManager):
    """Lista todos los perfiles disponibles."""
    profiles = manager.list_profiles()
    if not profiles:
        print("No se encontraron perfiles. Verifique el directorio de perfiles.")
        return
    
    print(f"Perfiles disponibles ({len(profiles)}):")
    for profile in profiles:
        print(f"- {profile['name']}: {profile['description']}")
        print(f"  Segmentador: {profile['segmenter']}")
        print(f"  Formatos: {', '.join(profile['file_types'])}")
        print()

def process_file(manager: ProfileManager, args):
    """Procesa un archivo según los argumentos proporcionados."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: Archivo no encontrado: {file_path}")
        return False
    
    # Si no se especificó un perfil, intentar detectarlo automáticamente
    profile_name = args.profile
    if not profile_name:
        profile_name = manager.get_profile_for_file(file_path)
        if profile_name:
            print(f"Perfil detectado automáticamente: {profile_name}")
        else:
            print("ERROR: No se pudo detectar un perfil adecuado. Especifique uno con --profile")
            return False
    
    try:
        # Procesar el archivo
        segments = manager.process_file(
            file_path=str(file_path),
            profile_name=profile_name,
            output_path=args.output,
            encoding=args.encoding,
            force_content_type=args.force_type,
            confidence_threshold=args.confidence_threshold
        )
        
        # Mostrar resultados
        if segments:
            print(f"Procesado completo: {len(segments)} unidades encontradas")
            
            # Mostrar un resumen de las unidades
            types = {}
            for segment in segments:
                segment_type = segment.get('type', 'unknown')
                types[segment_type] = types.get(segment_type, 0) + 1
            
            print("Resumen por tipo:")
            for t, count in types.items():
                print(f"- {t}: {count}")
            
            # Si está en modo verbose, mostrar los primeros 5 segmentos para depuración
            if args.verbose and segments:
                print("\nEjemplos de segmentos encontrados (primeros 5):")
                for i, segment in enumerate(segments[:5]):
                    if 'title' in segment:
                        print(f"[{i+1}] {segment['type']}: {segment['title'][:50]}...")
                    elif 'text' in segment:
                        print(f"[{i+1}] {segment['type']}: {segment['text'][:50]}...")
                    else:
                        print(f"[{i+1}] {segment['type']}: (sin texto)")
            
            return True
        else:
            print("No se encontraron unidades en el archivo.")
            if args.verbose:
                print("\nVerifique que el archivo contiene la estructura esperada por el perfil.")
                print("Puede probar con otro perfil o ajustar los parámetros de detección.")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Procesa archivos usando el sistema de perfiles")
    
    # Modo de lista o modo de procesamiento
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-profiles", action="store_true", help="Lista perfiles disponibles")
    group.add_argument("file", nargs="?", help="Archivo a procesar")
    
    # Opciones para modo de procesamiento
    parser.add_argument("--profile", "-p", help="Perfil a utilizar (opcional, se detectará automáticamente)")
    parser.add_argument("--output", "-o", help="Archivo de salida (NDJSON)")
    parser.add_argument("--force-type", choices=["poemas", "escritos", "canciones", "capitulos"], 
                      help="Forzar tipo de contenido específico (ignora detección automática)")
    parser.add_argument("--confidence-threshold", type=float, default=0.5,
                      help="Umbral de confianza para detección de poemas (0.0-1.0, default: 0.5)")
    
    # Opciones generales
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar información detallada")
    parser.add_argument("--profiles-dir", help="Directorio de perfiles personalizado")
    parser.add_argument("--encoding", default="utf-8", help="Codificación del archivo (default: utf-8)")
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    
    # Inicializar gestor de perfiles
    manager = ProfileManager(args.profiles_dir)
    
    # Procesar según el modo
    if args.list_profiles:
        list_profiles(manager)
        return True
    else:
        return process_file(manager, args)

if __name__ == "__main__":
    sys.exit(main()) 