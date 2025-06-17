#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del procesamiento del Don Quijote.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del dataset al path
sys.path.insert(0, str(Path(__file__).parent / "dataset"))

from dataset.processing.profile_manager import ProfileManager
import logging

# Configurar logging para ver el progreso
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_quijote_processing():
    """
    Prueba el procesamiento de un PDF del Don Quijote para verificar que ya no se corta prematuramente.
    """
    print("🚀 INICIANDO PRUEBA DE CORRECCIÓN DEL DON QUIJOTE")
    print("=" * 60)
    
    # Inicializar ProfileManager
    manager = ProfileManager()
    
    # Configurar parámetros de prueba
    # NOTA: Cambia esta ruta por la ruta real de tu PDF del Don Quijote
    test_pdf_path = input("Ingresa la ruta completa al PDF del Don Quijote: ").strip()
    
    if not test_pdf_path or not Path(test_pdf_path).exists():
        print("❌ Error: Archivo no encontrado. Por favor proporciona una ruta válida.")
        return False
    
    # Configurar archivos de salida
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "quijote_test.ndjson"
    
    print(f"📁 Archivo de entrada: {test_pdf_path}")
    print(f"📁 Archivo de salida: {output_file}")
    print()
    
    try:
        # Procesar con el perfil de prosa corregido
        print("🔄 Procesando con perfil 'prosa' corregido...")
        
        processed_content_items, segmenter_stats, document_metadata = manager.process_file(
            file_path=test_pdf_path,
            profile_name="prosa",
            output_file=str(output_file),
            output_format="ndjson",
            language_override="es",  # Español
            author_override="Miguel de Cervantes Saavedra"
        )
        
        # Verificar resultados
        num_segments = len(processed_content_items)
        print()
        print("📊 RESULTADOS DEL PROCESAMIENTO:")
        print(f"   • Segmentos generados: {num_segments}")
        print(f"   • Archivo de salida: {output_file}")
        
        if segmenter_stats:
            print("   • Estadísticas del segmentador:")
            for key, value in segmenter_stats.items():
                print(f"     - {key}: {value}")
        
        if document_metadata:
            print("   • Metadatos del documento:")
            for key, value in document_metadata.items():
                if key in ['titulo_documento', 'author', 'error']:
                    print(f"     - {key}: {value}")
        
        # Verificar que tenemos más segmentos que antes (debería ser mucho más que ~12)
        if num_segments > 50:  # Esperamos muchos más segmentos para un libro completo
            print()
            print("✅ ¡CORRECCIÓN EXITOSA!")
            print(f"   Se generaron {num_segments} segmentos (antes eran ~12)")
            print("   El procesamiento ya no se corta prematuramente.")
            
            # Mostrar algunos segmentos de ejemplo
            print()
            print("📄 PRIMEROS 5 SEGMENTOS:")
            for i, item in enumerate(processed_content_items[:5]):
                text_preview = item.text[:100] + "..." if len(item.text) > 100 else item.text
                print(f"   {i+1}. {text_preview}")
            
            print()
            print("📄 ÚLTIMOS 5 SEGMENTOS:")
            for i, item in enumerate(processed_content_items[-5:], len(processed_content_items)-4):
                text_preview = item.text[:100] + "..." if len(item.text) > 100 else item.text
                print(f"   {i}. {text_preview}")
            
            return True
        else:
            print()
            print("⚠️  POSIBLE PROBLEMA:")
            print(f"   Solo se generaron {num_segments} segmentos.")
            print("   Esto podría indicar que el problema persiste.")
            return False
            
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_quijote_processing()
    
    if success:
        print()
        print("🎉 ¡PRUEBA COMPLETADA EXITOSAMENTE!")
        print("   Las correcciones han resuelto el problema del corte prematuro.")
    else:
        print()
        print("❌ La prueba no fue completamente exitosa.")
        print("   Puede ser necesario realizar ajustes adicionales.") 