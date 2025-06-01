#!/usr/bin/env python3
"""
TEST VERSO SOLUCIÓN FINAL CORREGIDO
===================================

Verificar que el VerseSegmenter corregido agrupe correctamente
los versos bajo un solo título de poema en lugar de crear
poemas separados para cada verso.
"""

import sys
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.profile_manager import ProfileManager
    
    def test_verso_corregido():
        """Probar el perfil verso con corrección de agrupación"""
        
        # Archivo de prueba (ajustar la ruta según sea necesario)
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            print("📝 Ajusta la variable 'test_file' con la ruta correcta del PDF")
            return False
        
        print("🔍 TEST VERSO SOLUCIÓN FINAL CORREGIDO")
        print("=" * 60)
        print(f"📁 Archivo: {test_file}")
        print(f"⚙️ Perfil: verso")
        
        # Crear ProfileManager
        profile_manager = ProfileManager()
        
        # Procesar archivo
        result = profile_manager.process_file(
            file_path=test_file,
            profile_name="verso",
            output_format="json"
        )
        
        # Analizar resultados
        if result and 'segments' in result:
            segments = result['segments']
            
            print(f"\n✅ RESULTADOS DEL PROCESAMIENTO:")
            print(f"📊 Total de segmentos: {len(segments)}")
            
            # Buscar el Poema 13 específicamente
            poema_13_segments = [s for s in segments if 'Poema 13' in s.get('text', '')]
            
            print(f"\n🎭 ANÁLISIS DEL POEMA 13:")
            print(f"📄 Segmentos que contienen 'Poema 13': {len(poema_13_segments)}")
            
            if poema_13_segments:
                for i, segment in enumerate(poema_13_segments):
                    text = segment.get('text', '')
                    line_count = text.count('\n') + 1
                    char_count = len(text)
                    
                    print(f"\n📝 Segmento {i+1} del Poema 13:")
                    print(f"   📏 Longitud: {char_count} caracteres")
                    print(f"   📄 Líneas: {line_count}")
                    print(f"   🔍 Primeras 200 chars: {repr(text[:200])}")
                    
                    if line_count >= 10:  # Si tiene muchas líneas, es un poema completo
                        print(f"   ✅ PARECE POEMA COMPLETO")
                    else:
                        print(f"   ❌ PARECE FRAGMENTO")
                
                # Verificar si tenemos un poema completo
                complete_poems = [s for s in poema_13_segments if s.get('text', '').count('\n') >= 10]
                fragment_poems = [s for s in poema_13_segments if s.get('text', '').count('\n') < 10]
                
                print(f"\n📊 RESUMEN DEL POEMA 13:")
                print(f"   ✅ Poemas completos: {len(complete_poems)}")
                print(f"   ❌ Fragmentos: {len(fragment_poems)}")
                
                if len(complete_poems) == 1 and len(fragment_poems) == 0:
                    print(f"\n🎉 ¡ÉXITO! El Poema 13 está correctamente agrupado como un solo segmento")
                    return True
                else:
                    print(f"\n❌ PROBLEMA: El Poema 13 sigue fragmentado en múltiples segmentos")
                    return False
            else:
                print(f"❌ No se encontró el Poema 13 en los segmentos")
                return False
        else:
            print(f"❌ Error en el procesamiento: {result}")
            return False
    
    if __name__ == "__main__":
        print("🧪 TEST VERSO SOLUCIÓN FINAL CORREGIDO")
        print("=" * 60)
        
        success = test_verso_corregido()
        
        if success:
            print(f"\n🎉 ¡TEST EXITOSO! El problema está solucionado")
        else:
            print(f"\n❌ TEST FALLIDO. El problema persiste")
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("⚠️ Asegúrate de ejecutar desde el directorio raíz del proyecto") 