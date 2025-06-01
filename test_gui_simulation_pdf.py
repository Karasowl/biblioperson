#!/usr/bin/env python3
"""
Test de simulación GUI específico para PDF Benedetti
"""

import sys
sys.path.append('.')

from dataset.processing.profile_manager import ProfileManager
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

def test_gui_pdf_benedetti():
    print("🎯 TEST: Simulación GUI para PDF Benedetti")
    
    # Ruta del archivo PDF del usuario
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    archivo_salida = Path("C:/Users/adven/OneDrive/Escritorio/New folder (3)/test_benedetti.ndjson")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    # PASO 1: Inicializar ProfileManager como en la GUI
    print(f"\n1️⃣ PASO 1: ProfileManager")
    profile_manager = ProfileManager()
    print(f"   ✅ ProfileManager inicializado")
    
    # PASO 2: Procesar archivo exactamente como en la GUI
    print(f"\n2️⃣ PASO 2: Procesamiento con ProfileManager")
    
    try:
        resultado = profile_manager.process_file(
            file_path=str(archivo_pdf),
            profile_name='verso',
            output_dir=str(archivo_salida),
            language_override='es',
            author_override=None,
            encoding='utf-8'
        )
        
        print(f"   ✅ Procesamiento completado")
        print(f"   📊 Resultado tipo: {type(resultado)}")
        
        # Analizar el resultado
        if isinstance(resultado, tuple) and len(resultado) >= 3:
            segments, segmenter_stats, document_metadata = resultado[:3]
            print(f"   🎯 Segmentos generados: {len(segments)}")
            print(f"   📈 Stats: {segmenter_stats}")
            print(f"   📋 Metadata: {document_metadata}")
            
            if segments:
                print(f"   ✅ ÉXITO: {len(segments)} segmentos detectados")
                for i, segment in enumerate(segments[:5], 1):
                    title = getattr(segment, 'title', 'Sin título')
                    content_len = len(getattr(segment, 'content', ''))
                    print(f"      [{i}] '{title}' ({content_len} caracteres)")
            else:
                print(f"   ❌ PROBLEMA: Lista de segmentos vacía")
                
        else:
            print(f"   ❌ PROBLEMA: Resultado en formato inesperado: {resultado}")
        
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
    test_gui_pdf_benedetti() 