#!/usr/bin/env python3
"""
Test que simula exactamente el flujo de la GUI
"""

import sys
sys.path.append('.')

from dataset.processing.profile_manager import ProfileManager
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

def test_gui_simulation():
    print("🎯 TEST: Simulación exacta del flujo de la GUI")
    
    # Ruta del archivo del usuario
    archivo_poemas = Path("C:/Users/adven/OneDrive/Escritorio/probando biblioperson/Recopilación de Escritos Propios/biblioteca_personal/raw/poesías/Mis Poemas.docx")
    archivo_salida = Path("C:/Users/adven/OneDrive/Escritorio/New folder (3)/test_debug.ndjson")
    
    if not archivo_poemas.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_poemas}")
        return
    
    print(f"\n📁 Archivo entrada: {archivo_poemas.name}")
    print(f"📁 Archivo salida: {archivo_salida}")
    
    # PASO 1: Cargar ProfileManager como en la GUI
    print(f"\n1️⃣ PASO 1: ProfileManager")
    profile_manager = ProfileManager()
    
    # Verificar que el perfil verso esté disponible
    profiles = profile_manager.list_profiles()
    verso_profiles = [p for p in profiles if p.get('name') == 'verso']
    
    if not verso_profiles:
        print(f"❌ Error: Perfil 'verso' no encontrado")
        return
    
    print(f"   ✅ Perfil 'verso' encontrado: {verso_profiles[0].get('description', 'Sin descripción')}")
    
    # PASO 2: Verificar configuración del perfil
    print(f"\n2️⃣ PASO 2: Verificar configuración del perfil")
    # No necesitamos cargar la configuración específica, solo verificar que funcione el procesamiento
    
    # PASO 3: Procesar con ProfileManager directamente como en la GUI
    print(f"\n3️⃣ PASO 3: Procesamiento con ProfileManager")
    
    # Configuración exacta como en la GUI
    config = {
        'profile_name': 'verso',
        'language_override': 'es',
        'author_override': None,
        'verbose': True,
        'output_format': 'ndjson',  # El ProfileManager usa ndjson interno
        'encoding': 'utf-8'
    }
    
    print(f"   ✅ Configuración ProfileManager:")
    for key, value in config.items():
        print(f"      {key}: {value}")
    
    # PASO 4: Procesar archivo exactamente como en la GUI
    print(f"\n4️⃣ PASO 4: Procesamiento")
    
    try:
        resultado = profile_manager.process_file(
            file_path=str(archivo_poemas),
            profile_name=config['profile_name'],
            output_dir=str(archivo_salida.parent),  # Directorio de salida
            encoding=config.get('encoding', 'utf-8'),
            language_override=config.get('language_override'),
            author_override=config.get('author_override'),
            output_format=config.get('output_format', 'ndjson')
        )
        
        print(f"   ✅ Procesamiento completado")
        
        # El resultado de ProfileManager.process_file es una tupla: (segments, segmenter_stats, document_metadata)
        if isinstance(resultado, tuple) and len(resultado) == 3:
            segments, segmenter_stats, document_metadata = resultado
            print(f"   📊 Segmentos generados: {len(segments) if segments else 0}")
            print(f"   📊 Stats del segmentador: {segmenter_stats}")
            print(f"   📊 Metadatos del documento: {document_metadata.get('titulo_documento', 'N/A') if document_metadata else 'N/A'}")
            
            if segments:
                print(f"   🎯 SEGMENTOS DETECTADOS:")
                for i, segmento in enumerate(segments, 1):
                    if hasattr(segmento, 'metadatos_segmento'):
                        metadatos = segmento.metadatos_segmento
                        titulo = metadatos.get('title', 'Sin título') if metadatos else 'Sin metadatos'
                    else:
                        titulo = 'Formato desconocido'
                    
                    print(f"      [{i}] {titulo}")
            else:
                print(f"   ❌ NO SE GENERARON SEGMENTOS - Este es el problema!")
        else:
            print(f"   📊 Resultado: {resultado}")
            print(f"   ❌ Formato de resultado inesperado")
            
    except Exception as e:
        print(f"   ❌ Error durante procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gui_simulation() 