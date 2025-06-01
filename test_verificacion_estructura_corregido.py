#!/usr/bin/env python3
"""
TEST VERIFICACIÓN ESTRUCTURA CORREGIDO
======================================

Verificar exactamente cómo están estructurados los bloques
y poemas después de las correcciones del MarkdownPDFLoader.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.profile_manager import ProfileManager
except ImportError as e:
    print(f"❌ Error importando ProfileManager: {e}")
    sys.exit(1)

def test_estructura_corregida():
    """Verificar estructura de bloques y poemas (CORREGIDO)"""
    
    test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return False
    
    print("🔍 VERIFICACIÓN ESTRUCTURA FINAL")
    print("=" * 50)
    
    try:
        # Configurar ProfileManager
        profile_manager = ProfileManager()
        
        # Procesar con perfil verso corregido
        print(f"📄 Procesando: {os.path.basename(test_file)}")
        print(f"🎯 Perfil: verso")
        
        result = profile_manager.process_file(
            file_path=test_file,
            profile_name="verso",
            output_format="json"
        )
        
        # CORREGIR: Manejar resultado como tuple
        if isinstance(result, tuple):
            success, data = result
        else:
            success = result.get('success', False)
            data = result.get('data', [])
        
        if not success:
            print(f"❌ Error en el procesamiento")
            return False
        
        print(f"✅ Procesamiento exitoso: {len(data)} segmentos")
        
        # Verificar estructura específica del Poema 13
        poema_13_segments = [s for s in data if "Poema 13" in s.get('texto_segmento', '')]
        
        if poema_13_segments:
            print(f"\n🎯 ANÁLISIS POEMA 13:")
            print(f"📊 Segmentos encontrados: {len(poema_13_segments)}")
            
            for i, segment in enumerate(poema_13_segments):
                text = segment.get('texto_segmento', '')
                print(f"\n📝 Segmento {i+1}:")
                print(f"🔤 Longitud: {len(text)} caracteres")
                print(f"📄 Texto:")
                # Mostrar las primeras 5 líneas para verificar saltos
                lines = text.split('\n')
                for j, line in enumerate(lines[:10]):  # Primeras 10 líneas
                    print(f"   Línea {j+1}: {repr(line)}")
                    if j >= 4:  # Limitar para no saturar
                        break
                if len(lines) > 10:
                    print(f"   ... y {len(lines)-10} líneas más")
        else:
            print("❌ No se encontró el Poema 13")
        
        # Verificar otros poemas para detectar patrón
        print(f"\n📊 RESUMEN GENERAL:")
        print(f"✅ Total segmentos: {len(data)}")
        
        # Buscar poemas cortos para verificar estructura
        poemas_cortos = [s for s in data if len(s.get('texto_segmento', '')) < 500][:3]
        print(f"🔍 Analizando {len(poemas_cortos)} poemas cortos:")
        
        for i, segment in enumerate(poemas_cortos):
            text = segment.get('texto_segmento', '')
            lines = text.split('\n')
            print(f"   Poema {i+1}: {len(lines)} líneas, {len(text)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_estructura_corregida() 