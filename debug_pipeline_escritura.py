#!/usr/bin/env python3
"""
Script para debuggear dónde exactamente falla la escritura en el pipeline
"""

import sys
import os
import traceback
from pathlib import Path

# Agregar el path del proyecto
sys.path.insert(0, os.path.abspath('.'))

def debug_pipeline_escritura():
    """Debuggear el problema de escritura en el pipeline completo"""
    
    print("🔍 DEBUGGING PIPELINE DE ESCRITURA")
    print("=" * 60)
    
    try:
        # Importar los módulos correctos
        from dataset.scripts.process_file import _process_single_file, ProcessingStats
        from dataset.processing.profile_manager import ProfileManager
        
        print("✅ Importaciones exitosas")
        
        # Configurar paths
        input_path = Path(r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf")
        output_path = Path(r"C:\Users\adven\Downloads\New folder (13)\fff.ndjson")
        
        print(f"🎯 Configuración:")
        print(f"   - Input: {input_path}")
        print(f"   - Output: {output_path}")
        
        # Verificar que el archivo de entrada existe
        if not input_path.exists():
            print(f"❌ Archivo de entrada no existe: {input_path}")
            return
        print("✅ Archivo de entrada existe")
        
        # Crear ProfileManager
        profile_manager = ProfileManager()
        print("✅ ProfileManager creado")
        
        # Crear args simulando la configuración
        class Args:
            def __init__(self):
                self.profile = 'prosa'
                self.language_override = 'es'
                self.author_override = None
                self.verbose = True
                self.encoding = 'utf-8'
                self.output_format = 'json'
                self.output = str(output_path)
                self.input_path = str(input_path)
                self.force_type = None
                self.confidence_threshold = 0.5
                self.parallel = False
                self.max_workers = None
        
        args = Args()
        print("✅ Args configurados")
        
        # Crear directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear stats
        stats = ProcessingStats()
        print("✅ Stats creados")
        
        # Ejecutar el procesamiento
        print("\n🚀 INICIANDO PROCESAMIENTO...")
        
        result_code, message = _process_single_file(
            manager=profile_manager,
            file_path=input_path,
            args=args,
            base_output_path=output_path.parent,
            output_format="json",
            stats=stats
        )
        
        print(f"\n📊 RESULTADO DEL PROCESAMIENTO:")
        print(f"   - Result code: {result_code}")
        print(f"   - Message: {message}")
        print(f"   - Stats: {stats}")
        
        # Verificar si se creó el archivo
        expected_output = output_path.parent / f"{input_path.stem}.ndjson"
        
        print(f"\n🔍 VERIFICANDO ARCHIVOS:")
        print(f"   - Esperado original: {output_path}")
        print(f"   - Esperado alternativo: {expected_output}")
        
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"✅ ARCHIVO CREADO (original): {output_path} ({size} bytes)")
        elif expected_output.exists():
            size = expected_output.stat().st_size
            print(f"✅ ARCHIVO CREADO (alternativo): {expected_output} ({size} bytes)")
        else:
            print(f"❌ NINGÚN ARCHIVO CREADO")
            
            # Buscar archivos .ndjson en el directorio
            output_dir = output_path.parent
            ndjson_files = list(output_dir.glob("*.ndjson"))
            if ndjson_files:
                print(f"🔍 Archivos .ndjson encontrados en {output_dir}:")
                for file in ndjson_files:
                    size = file.stat().st_size
                    print(f"   - {file.name} ({size} bytes)")
            else:
                print(f"❌ No se encontraron archivos .ndjson en {output_dir}")
        
    except Exception as e:
        print(f"❌ ERROR EN PROCESAMIENTO:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        print(f"\n📋 TRACEBACK COMPLETO:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_pipeline_escritura() 