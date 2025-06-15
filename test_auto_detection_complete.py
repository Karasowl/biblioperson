#!/usr/bin/env python3
"""
Test completo de detección automática usando ProfileManager
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

from dataset.processing.profile_manager import ProfileManager

def test_auto_detection_complete():
    """Test completo usando detección automática del ProfileManager"""
    
    test_file = r"C:\Users\adven\Downloads\Dario, Ruben - Antologia.pdf"
    
    print("=" * 80)
    print("🧪 TEST: DETECCIÓN AUTOMÁTICA COMPLETA CON PROFILEMANAGER")
    print("=" * 80)
    
    # === PASO 1: DETECCIÓN AUTOMÁTICA ===
    print("\n📋 PASO 1: Usando detección automática...")
    
    profile_manager = ProfileManager()
    
    # Usar "automático" para activar la detección automática
    try:
        segments, stats, metadata = profile_manager.process_file(
            file_path=test_file,
            profile_name="automático",  # ¡CLAVE! Esto activa la detección automática
            output_format="generic",
            output_mode="generic"
        )
        
        print(f"✅ Procesamiento exitoso!")
        print(f"📊 Estadísticas:")
        print(f"   • Total segmentos: {len(segments)}")
        print(f"   • Perfil usado: {metadata.get('profile_used', 'N/A')}")
        print(f"   • Segmentador: {metadata.get('segmenter_used', 'N/A')}")
        
        # === PASO 2: ANÁLISIS DE RESULTADOS ===
        print(f"\n📋 PASO 2: Analizando resultados...")
        
        # Verificar que se detectó autor
        document_author = None
        if segments:
            document_author = getattr(segments[0], 'document_author', None)
        
        print(f"✍️  Autor detectado: {document_author or 'NO DETECTADO'}")
        
        # Analizar longitudes de segmentos
        lengths = [len(segment.text) for segment in segments]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        print(f"📏 Longitud promedio: {avg_length:.1f} caracteres")
        print(f"📏 Rango: {min(lengths) if lengths else 0} - {max(lengths) if lengths else 0}")
        
        # Mostrar primeros segmentos
        print(f"\n📋 PASO 3: Primeros 5 segmentos:")
        for i, segment in enumerate(segments[:5]):
            text_preview = segment.text[:100].replace('\n', ' ')
            if len(segment.text) > 100:
                text_preview += "..."
            print(f"   {i+1:2d}. [{len(segment.text):4d} chars] {text_preview}")
        
        # === VERIFICACIONES ESPECÍFICAS ===
        print(f"\n📋 PASO 4: Verificaciones...")
        
        profile_used = metadata.get('profile_used', 'N/A')
        print(f"🔍 Perfil detectado y usado: {profile_used}")
        
        # Verificar que se detectó verso
        if profile_used == 'verso':
            print(f"✅ CORRECTO: Se detectó y usó perfil VERSO")
            
            # Verificar segmentación apropiada para verso
            large_segments = [i for i, s in enumerate(segments) if len(s.text) > 2000]
            if large_segments:
                print(f"⚠️  ADVERTENCIA: {len(large_segments)} segmentos muy largos para verso:")
                for idx in large_segments[:3]:
                    print(f"      Segmento {idx+1}: {len(segments[idx].text)} chars")
            else:
                print(f"✅ Segmentación apropiada para verso (sin segmentos excesivamente largos)")
            
            # Verificar que hay segmentos cortos típicos de verso
            short_segments = [s for s in segments if len(s.text) < 500]
            print(f"✅ Segmentos cortos (versos): {len(short_segments)}/{len(segments)}")
            
            return True
            
        elif profile_used == 'prosa':
            print(f"❌ ERROR: Se detectó PROSA cuando debería ser VERSO")
            return False
        else:
            print(f"❌ ERROR: Perfil inesperado: {profile_used}")
            return False
            
    except Exception as e:
        print(f"❌ Error en procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auto_detection_complete()
    if success:
        print(f"\n🎉 TEST EXITOSO!")
    else:
        print(f"\n💥 TEST FALLÓ!")
    
    sys.exit(0 if success else 1) 