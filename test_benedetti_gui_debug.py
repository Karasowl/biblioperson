#!/usr/bin/env python3
"""
Test para verificar si el VerseSegmenter actualizado y la limpieza Unicode 
funcionan correctamente con el PDF de Benedetti en el flujo GUI.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.profile_manager import ProfileManager
import logging

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_benedetti_gui_flow():
    """Test del flujo GUI completo con PDF de Benedetti"""
    
    # Archivo PDF de Benedetti que falló en la GUI
    pdf_path = "C:/Users/adven/Downloads/Mario Benedetti Antologia Poética.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return False
    
    print(f"📖 Procesando con flujo GUI: {pdf_path}")
    
    # 1. Usar ProfileManager como lo hace la GUI
    profile_manager = ProfileManager()
    
    # 2. Configurar para modo verbose
    print(f"\n🔍 ACTIVANDO DEBUG LOGGING...")
    logging.getLogger('dataset.processing').setLevel(logging.DEBUG)
    
    # 3. Procesar usando perfil 'verso' como en la GUI
    try:
        print(f"\n⚙️ Procesando con perfil 'verso'...")
        result = profile_manager.process_file(
            file_path=pdf_path,
            profile_name='verso',
            language_override='es'  # Como está configurado en la GUI
        )
        
        print(f"\n📋 RESULTADO DEL PROCESAMIENTO:")
        print(f"   Tipo de resultado: {type(result)}")
        
        if isinstance(result, tuple) and len(result) >= 3:
            content_items, stats, metadata = result[:3]
            print(f"   Items procesados: {len(content_items)}")
            print(f"   Stats: {stats}")
            print(f"   Metadata: {metadata}")
            
            if content_items:
                print(f"\n📝 Primeros 3 items:")
                for i, item in enumerate(content_items[:3]):
                    print(f"   {i+1}. Tipo: {type(item)}")
                    if hasattr(item, 'content'):
                        preview = item.content[:50].replace('\n', ' ')
                        print(f"      Contenido: '{preview}...'")
                    if hasattr(item, 'title'):
                        print(f"      Título: '{item.title}'")
                
                success = len(content_items) > 0
                if success:
                    print(f"\n✅ ÉXITO: {len(content_items)} elementos detectados")
                else:
                    print(f"\n❌ FALLO: No se detectaron elementos")
                    
                return success
            else:
                print(f"\n❌ FALLO: Lista de contenido vacía")
                return False
                
        else:
            print(f"   Resultado inesperado: {result}")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR en procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST: Flujo GUI completo con PDF de Benedetti")
    print("=" * 60)
    
    success = test_benedetti_gui_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASADO: El flujo GUI funciona correctamente")
    else:
        print("💥 TEST FALLIDO: Hay problemas en el flujo GUI")
    print("=" * 60) 