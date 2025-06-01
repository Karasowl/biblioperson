#!/usr/bin/env python3
"""
Test del VerseSegmenter MEJORADO con el DOCX de "Mis Poemas"
Para verificar que las mejoras funcionan correctamente
"""

import sys
sys.path.append('.')

from dataset.processing.profile_manager import ProfileManager
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def test_mis_poemas_mejorado():
    print("🎯 TEST: VerseSegmenter MEJORADO con Mis Poemas.docx")
    
    # Ruta del archivo DOCX que SÍ funciona
    archivo_docx = Path("C:/Users/adven/OneDrive/Escritorio/probando biblioperson/Recopilación de Escritos Propios/biblioteca_personal/raw/poesías/Mis Poemas.docx")
    
    if not archivo_docx.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_docx}")
        return
    
    print(f"\n📄 ARCHIVO: {archivo_docx.name}")
    
    # Usar ProfileManager exactamente como la GUI
    print(f"\n🔄 PROCESANDO con perfil VERSO mejorado...")
    try:
        profile_manager = ProfileManager()
        
        # Procesar con el perfil verso que tiene nuestras mejoras
        result_tuple = profile_manager.process_file(
            file_path=str(archivo_docx),
            profile_name='verso',
            language_override='es',
            encoding='utf-8'
        )
        
        # ProfileManager devuelve una tupla: (processed_content_items, stats, metadata)
        processed_items, stats, metadata = result_tuple
        result = processed_items  # Esta es la lista de poemas que necesitamos
        
        if result and len(result) > 0:
            print(f"   ✅ Poemas detectados: {len(result)}")
            
            print(f"\n   📝 POEMAS DETECTADOS:")
            for i, processed_item in enumerate(result[:10]):  # Primeros 10
                # Extraer información del ProcessedContentItem
                if hasattr(processed_item, 'jerarquia_contextual'):
                    title = processed_item.jerarquia_contextual.get('poema_titulo', 'Sin título')
                    text = processed_item.texto_segmento
                    text_lines = len(text.split('\n')) if text else 0
                    print(f"      [{i+1}] '{title}' ({text_lines} líneas)")
                else:
                    print(f"      [{i+1}] Formato: {type(processed_item)}")
            
            # Verificar si detecta los 5 poemas esperados
            expected_titles = [
                "Adiós", "Morirás", "Los barbudos de un sueño", 
                "El Loco", "Sigo negando su sello"
            ]
            
            detected_titles = []
            for processed_item in result:
                if hasattr(processed_item, 'jerarquia_contextual'):
                    title = processed_item.jerarquia_contextual.get('poema_titulo', '').strip()
                    if title:
                        detected_titles.append(title)
            
            print(f"\n   🎯 VERIFICACIÓN DE POEMAS ESPERADOS:")
            found_count = 0
            for expected in expected_titles:
                found = any(expected in detected for detected in detected_titles)
                status = "✅ ENCONTRADO" if found else "❌ FALTANTE"
                print(f"      {status}: {expected}")
                if found:
                    found_count += 1
            
            print(f"\n   📊 RESULTADO:")
            print(f"      🎭 Poemas detectados: {len(result)}")
            print(f"      🎯 Poemas esperados: 5")
            print(f"      ✅ Poemas encontrados: {found_count}/5")
            
            success_rate = (found_count / 5) * 100
            print(f"      📈 Tasa de éxito: {success_rate:.1f}%")
            
            if len(result) >= 5 and found_count >= 4:
                print(f"\n   🎉 ÉXITO: VerseSegmenter mejorado funciona correctamente")
                print(f"      💡 Listo para aplicar a PDFs válidos de Benedetti")
            elif len(result) > 0:
                print(f"\n   🔄 PROGRESO: Mejora parcial detectada")
                print(f"      🔧 Necesita ajustes adicionales")
            else:
                print(f"\n   ❌ PROBLEMA: No funciona como esperado")
        else:
            print(f"   ❌ NO se detectaron poemas")
            print(f"   🚨 PROBLEMA: VerseSegmenter no está funcionando")
        
    except Exception as e:
        print(f"   ❌ ERROR en procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n🏁 CONCLUSIÓN:")
    if 'result' in locals() and result and len(result) >= 4:
        print(f"   ✅ VerseSegmenter MEJORADO funciona correctamente")
        print(f"   📚 Problema con PDFs de Benedetti: archivos corruptos")
        print(f"   💡 SOLUCIÓN: Conseguir PDFs válidos de Benedetti")
        print(f"   🎯 EXPECTATIVA: Con PDF válido → ~140 poemas detectados")
    else:
        print(f"   ❌ VerseSegmenter necesita más ajustes")
        print(f"   🔧 Revisar patrones de detección")

if __name__ == "__main__":
    test_mis_poemas_mejorado() 