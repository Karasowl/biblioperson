#!/usr/bin/env python3
"""
Test que replica EXACTAMENTE lo que hace la GUI
"""

import sys
sys.path.append('.')

from dataset.scripts.process_file import core_process
from pathlib import Path
import argparse
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

def test_gui_exacto_benedetti():
    print("🎯 TEST: Replicación EXACTA de la GUI")
    
    # Ruta del archivo PDF del usuario
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    archivo_salida = Path("C:/Users/adven/OneDrive/Escritorio/New folder (3)/xs.ndjson")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n1️⃣ PASO 1: Simular argumentos de la GUI")
    
    # Crear argumentos simulados EXACTAMENTE como en la GUI
    args = argparse.Namespace()
    args.input_path = str(archivo_pdf)  # Mantener la ruta original
    args.profile = 'verso'
    args.verbose = True
    args.encoding = 'utf-8'
    args.force_type = None  # force_content_type
    args.confidence_threshold = 0.5
    args.language_override = 'es'
    args.author_override = None
    args.output = str(archivo_salida)  # Para archivos, usar output_path tal como está
    
    print(f"   ✅ Argumentos configurados:")
    print(f"      input_path: {args.input_path}")
    print(f"      profile: {args.profile}")
    print(f"      output: {args.output}")
    print(f"      verbose: {args.verbose}")
    print(f"      language_override: {args.language_override}")
    
    print(f"\n2️⃣ PASO 2: Llamar core_process EXACTAMENTE como la GUI")
    
    try:
        # Importar y crear ProfileManager como hace la GUI
        from dataset.processing.profile_manager import ProfileManager
        profile_manager = ProfileManager()
        
        # Esta es la llamada EXACTA que hace la GUI
        result_code, message, document_metadata, segments, segmenter_stats = core_process(
            manager=profile_manager,  # Pasar el manager como hace la GUI
            input_path=archivo_pdf,
            profile_name_override='verso',
            output_spec=str(archivo_salida),
            cli_args=args,
            output_format='JSON'  # La GUI usa 'JSON' por defecto
        )
        
        print(f"   ✅ core_process completado")
        print(f"   📊 result_code: {result_code}")
        print(f"   📝 message: {message}")
        print(f"   📋 document_metadata keys: {list(document_metadata.keys()) if document_metadata else 'None'}")
        print(f"   🎯 segments: {len(segments) if segments else 0}")
        print(f"   📈 segmenter_stats: {segmenter_stats}")
        
        if result_code.startswith('SUCCESS'):
            if segments:
                print(f"   ✅ ÉXITO: {len(segments)} segmentos encontrados")
                for i, segment in enumerate(segments[:5], 1):
                    # Analizar el tipo de segment
                    if hasattr(segment, 'title'):
                        title = segment.title
                        content_len = len(getattr(segment, 'content', ''))
                        print(f"      [{i}] '{title}' ({content_len} caracteres)")
                    else:
                        print(f"      [{i}] {type(segment)} - {str(segment)[:100]}...")
            else:
                print(f"   ❌ PROBLEMA: No se encontraron segmentos (result_code: {result_code})")
        else:
            print(f"   ❌ ERROR: {result_code} - {message}")
        
        # Verificar archivo de salida
        if archivo_salida.exists():
            with open(archivo_salida, 'r', encoding='utf-8') as f:
                contenido = f.read()
                lineas = contenido.strip().split('\n')
                print(f"   ✅ Archivo creado: {len(lineas)} líneas")
                
                if lineas and lineas[0].strip():
                    print(f"   📝 Primera línea: {lineas[0][:100]}...")
                else:
                    print(f"   ❌ Archivo está vacío")
        else:
            print(f"   ❌ Archivo de salida no se creó")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gui_exacto_benedetti() 