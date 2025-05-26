#!/usr/bin/env python3
"""
Módulo para unificar múltiples archivos NDJSON de forma recursiva.

Este script busca todos los archivos .ndjson en una carpeta de entrada
y los unifica en un solo archivo NDJSON de salida, manteniendo la integridad
de cada archivo original (no mezclando entradas entre archivos).
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class NDJSONUnifier:
    """Clase para unificar múltiples archivos NDJSON."""
    
    def __init__(self, input_dir: str, output_file: str, recursive: bool = True):
        """
        Inicializa el unificador de NDJSON.
        
        Args:
            input_dir: Directorio de entrada con archivos NDJSON
            output_file: Archivo de salida unificado
            recursive: Si buscar archivos de forma recursiva
        """
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.recursive = recursive
        
        # Estadísticas
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_skipped': 0,
            'total_entries': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Validaciones
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Directorio de entrada no existe: {input_dir}")
        
        if not self.input_dir.is_dir():
            raise NotADirectoryError(f"La ruta de entrada no es un directorio: {input_dir}")
        
        # Crear directorio de salida si no existe
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
    
    def find_ndjson_files(self) -> List[Path]:
        """
        Encuentra todos los archivos NDJSON en el directorio de entrada.
        
        Returns:
            Lista de rutas a archivos NDJSON
        """
        logger.info(f"Buscando archivos NDJSON en: {self.input_dir}")
        
        if self.recursive:
            pattern = "**/*.ndjson"
            logger.info("Búsqueda recursiva activada")
        else:
            pattern = "*.ndjson"
            logger.info("Búsqueda solo en directorio raíz")
        
        files = list(self.input_dir.glob(pattern))
        files.sort()  # Ordenar para procesamiento consistente
        
        self.stats['files_found'] = len(files)
        logger.info(f"Encontrados {len(files)} archivos NDJSON")
        
        if files:
            logger.info("Archivos encontrados:")
            for i, file_path in enumerate(files, 1):
                relative_path = file_path.relative_to(self.input_dir)
                logger.info(f"  {i:3d}. {relative_path}")
        
        return files
    
    def validate_ndjson_file(self, file_path: Path) -> bool:
        """
        Valida que un archivo sea NDJSON válido.
        
        Args:
            file_path: Ruta al archivo a validar
            
        Returns:
            True si el archivo es válido, False en caso contrario
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                line_count = 0
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:  # Ignorar líneas vacías
                        json.loads(line)  # Validar que sea JSON válido
                        line_count += 1
                
                if line_count == 0:
                    logger.warning(f"Archivo vacío: {file_path.relative_to(self.input_dir)}")
                    return False
                
                return True
                
        except json.JSONDecodeError as e:
            logger.error(f"Error JSON en {file_path.relative_to(self.input_dir)}, línea {line_num}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error leyendo {file_path.relative_to(self.input_dir)}: {e}")
            return False
    
    def count_entries_in_file(self, file_path: Path) -> int:
        """
        Cuenta las entradas en un archivo NDJSON.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Número de entradas en el archivo
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                count = 0
                for line in f:
                    line = line.strip()
                    if line:  # Ignorar líneas vacías
                        count += 1
                return count
        except Exception:
            return 0
    
    def unify_files(self, files: List[Path]) -> bool:
        """
        Unifica los archivos NDJSON en un solo archivo.
        
        Args:
            files: Lista de archivos a unificar
            
        Returns:
            True si la unificación fue exitosa, False en caso contrario
        """
        logger.info(f"Iniciando unificación en: {self.output_file}")
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as output_f:
                # Escribir metadatos de inicio
                metadata = {
                    "_unification_metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "source_directory": str(self.input_dir.absolute()),
                        "total_source_files": len(files),
                        "recursive_search": self.recursive,
                        "tool": "biblioperson-ndjson-unifier"
                    }
                }
                output_f.write(json.dumps(metadata, ensure_ascii=False) + '\n')
                
                for i, file_path in enumerate(files, 1):
                    relative_path = file_path.relative_to(self.input_dir)
                    logger.info(f"Procesando {i}/{len(files)}: {relative_path}")
                    
                    # Validar archivo antes de procesar
                    if not self.validate_ndjson_file(file_path):
                        logger.warning(f"Saltando archivo inválido: {relative_path}")
                        self.stats['files_skipped'] += 1
                        continue
                    
                    # Contar entradas antes de procesar
                    entry_count = self.count_entries_in_file(file_path)
                    logger.info(f"  → {entry_count} entradas encontradas")
                    
                    # Escribir separador de archivo
                    file_separator = {
                        "_file_separator": {
                            "source_file": str(relative_path),
                            "absolute_path": str(file_path.absolute()),
                            "file_size_bytes": file_path.stat().st_size,
                            "entry_count": entry_count,
                            "file_index": i
                        }
                    }
                    output_f.write(json.dumps(file_separator, ensure_ascii=False) + '\n')
                    
                    # Copiar contenido del archivo
                    try:
                        with open(file_path, 'r', encoding='utf-8') as input_f:
                            entries_copied = 0
                            for line_num, line in enumerate(input_f, 1):
                                line = line.strip()
                                if line:  # Ignorar líneas vacías
                                    # Validar que la línea sea JSON válido
                                    try:
                                        json.loads(line)  # Validar JSON
                                        output_f.write(line + '\n')
                                        entries_copied += 1
                                        self.stats['total_entries'] += 1
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Error JSON en {relative_path}, línea {line_num}: {e}")
                                        self.stats['errors'] += 1
                            
                            logger.info(f"  → {entries_copied} entradas copiadas")
                            self.stats['files_processed'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error procesando {relative_path}: {e}")
                        self.stats['files_skipped'] += 1
                        self.stats['errors'] += 1
                        continue
                
                # Escribir metadatos finales
                final_metadata = {
                    "_unification_summary": {
                        "completion_timestamp": datetime.now().isoformat(),
                        "files_processed": self.stats['files_processed'],
                        "files_skipped": self.stats['files_skipped'],
                        "total_entries": self.stats['total_entries'],
                        "errors_encountered": self.stats['errors']
                    }
                }
                output_f.write(json.dumps(final_metadata, ensure_ascii=False) + '\n')
                
            logger.info(f"✅ Unificación completada: {self.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error durante la unificación: {e}")
            return False
    
    def run(self) -> bool:
        """
        Ejecuta el proceso completo de unificación.
        
        Returns:
            True si el proceso fue exitoso, False en caso contrario
        """
        self.stats['start_time'] = datetime.now()
        
        try:
            # Buscar archivos
            files = self.find_ndjson_files()
            
            if not files:
                logger.warning("No se encontraron archivos NDJSON para unificar")
                return False
            
            # Unificar archivos
            success = self.unify_files(files)
            
            self.stats['end_time'] = datetime.now()
            self._print_summary()
            
            return success
            
        except Exception as e:
            logger.error(f"Error durante la ejecución: {e}")
            return False
    
    def _print_summary(self):
        """Imprime un resumen de la operación."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*60)
        print("RESUMEN DE UNIFICACIÓN")
        print("="*60)
        print(f"Directorio de entrada:    {self.input_dir}")
        print(f"Archivo de salida:        {self.output_file}")
        print(f"Búsqueda recursiva:       {'Sí' if self.recursive else 'No'}")
        print(f"Duración:                 {duration}")
        print()
        print(f"Archivos encontrados:     {self.stats['files_found']}")
        print(f"Archivos procesados:      {self.stats['files_processed']}")
        print(f"Archivos saltados:        {self.stats['files_skipped']}")
        print(f"Total de entradas:        {self.stats['total_entries']}")
        print(f"Errores encontrados:      {self.stats['errors']}")
        print()
        
        if self.stats['files_processed'] > 0:
            avg_entries = self.stats['total_entries'] / self.stats['files_processed']
            print(f"Promedio entradas/archivo: {avg_entries:.1f}")
        
        if self.output_file.exists():
            size_mb = self.output_file.stat().st_size / (1024 * 1024)
            print(f"Tamaño archivo salida:    {size_mb:.2f} MB")
        
        print("="*60)


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Unifica múltiples archivos NDJSON en uno solo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python unify_ndjson.py input_folder output.ndjson
  python unify_ndjson.py input_folder output.ndjson --no-recursive
  python unify_ndjson.py /path/to/ndjsons unified_dataset.ndjson --verbose
        """
    )
    
    parser.add_argument(
        'input_dir',
        help='Directorio de entrada con archivos NDJSON'
    )
    
    parser.add_argument(
        'output_file',
        help='Archivo de salida unificado (.ndjson)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='No buscar archivos de forma recursiva (solo directorio raíz)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar información detallada'
    )
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validar argumentos
    if not args.output_file.endswith('.ndjson'):
        logger.warning("El archivo de salida no tiene extensión .ndjson")
    
    try:
        # Crear unificador
        unifier = NDJSONUnifier(
            input_dir=args.input_dir,
            output_file=args.output_file,
            recursive=not args.no_recursive
        )
        
        # Ejecutar unificación
        success = unifier.run()
        
        if success:
            print(f"\n✅ Unificación exitosa: {args.output_file}")
            sys.exit(0)
        else:
            print(f"\n❌ Error en la unificación")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 