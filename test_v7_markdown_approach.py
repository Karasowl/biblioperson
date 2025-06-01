#!/usr/bin/env python3
"""
🚨 TEST V7.0 - ENFOQUE MARKDOWN PRIMERO 🚨

Test del nuevo sistema que convierte PDF a markdown primero,
preservando la estructura original, y luego procesa ese markdown.

Este enfoque debería volver a funcionar como cuando extraíamos
60 poemas de Mario Benedetti.
"""

import sys
import logging
from pathlib import Path

# Configurar logging para ver todo el proceso
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importar el sistema
sys.path.append('.')
from dataset.processing.profile_manager import ProfileManager

def test_v7_system():
    """Probar el sistema V7.0 con enfoque markdown."""
    
    print("🚨🚨🚨 INICIANDO TEST V7.0 - MARKDOWN FIRST 🚨🚨🚨")
    
    # Inicializar ProfileManager (esto forzará la recarga de módulos)
    pm = ProfileManager()
    print("✅ ProfileManager inicializado con recargas forzadas")
    
    # Buscar un PDF de prueba
    test_files = [
        "test_prosa.txt",  # Fallback si no hay PDF
        "Alfonso Reyes, _un hijo menor de la palabra_ - Javier Garciadiego y Alfonso Reyes.ndjson",
    ]
    
    # Buscar archivos PDF en el directorio
    pdf_files = list(Path('.').glob('*.pdf'))
    if pdf_files:
        test_file = str(pdf_files[0])
        print(f"📄 Encontrado PDF: {test_file}")
    else:
        # Usar archivo de texto como fallback
        for test_file in test_files:
            if Path(test_file).exists():
                print(f"📄 Usando archivo fallback: {test_file}")
                break
        else:
            print("❌ No se encontraron archivos de prueba")
            return
    
    # Procesar con perfil 'prosa' (el core profile)
    try:
        print(f"🔄 Procesando {test_file} con perfil 'prosa'...")
        
        results = pm.process_file(
            file_path=test_file,
            profile_name='prosa',
            output_dir='dataset/output/test_v7/',
            force_content_type='prosa'
        )
        
        print(f"✅ PROCESAMIENTO COMPLETADO:")
        print(f"   📊 Segmentos generados: {len(results)}")
        
        # Mostrar algunos ejemplos
        if results:
            print(f"🔍 PRIMEROS 3 SEGMENTOS:")
            for i, segment in enumerate(results[:3]):
                if hasattr(segment, 'content_text'):
                    preview = segment.content_text[:100] + "..." if len(segment.content_text) > 100 else segment.content_text
                    print(f"   [{i+1}] {preview}")
                else:
                    print(f"   [{i+1}] {str(segment)[:100]}...")
        
        # Verificar si extrae suficientes segmentos
        if len(results) >= 10:
            print(f"🎯 ÉXITO: Sistema V7.0 extrae {len(results)} segmentos (buena granularidad)")
        elif len(results) >= 3:
            print(f"⚠️ PARCIAL: Sistema extrae {len(results)} segmentos (mejorable)")
        else:
            print(f"❌ PROBLEMA: Solo {len(results)} segmentos extraídos")
            
    except Exception as e:
        print(f"❌ ERROR durante procesamiento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_v7_system() 