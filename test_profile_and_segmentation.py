#!/usr/bin/env python3
"""
Test completo para verificar:
1. Detección automática de perfil verso
2. Segmentación correcta según ALGORITMOS_PROPUESTOS.md
3. Extracción de autor
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.profile_detector import ProfileDetector
import json

def test_profile_detection_and_segmentation():
    """Test completo del pipeline con detección automática"""
    
    # Archivo de prueba - Antología de Rubén Darío
    test_file = r"C:\Users\adven\Downloads\Dario, Ruben - Antologia.pdf"
    
    print("=" * 80)
    print("🧪 TEST: DETECCIÓN AUTOMÁTICA DE PERFIL Y SEGMENTACIÓN")
    print("=" * 80)
    
    # === PASO 1: DETECCIÓN AUTOMÁTICA DE PERFIL ===
    print("\n📋 PASO 1: Detectando perfil automáticamente...")
    
    detector = ProfileDetector()
    profile_candidate = detector.detect_profile(test_file)
    
    print(f"🔍 Perfil detectado: {profile_candidate.profile_name}")
    print(f"🎯 Confianza: {profile_candidate.confidence:.2f}")
    print(f"📊 Razones:")
    for reason in profile_candidate.reasons:
        print(f"   • {reason}")
    
    print(f"📈 Métricas estructurales:")
    for key, value in profile_candidate.structural_metrics.items():
        if isinstance(value, float):
            print(f"   • {key}: {value:.3f}")
        else:
            print(f"   • {key}: {value}")
    
    # === PASO 2: PROCESAMIENTO CON PERFIL DETECTADO ===
    print(f"\n📋 PASO 2: Procesando con perfil '{profile_candidate.profile_name}'...")
    
    # Configurar ProfileManager con detección automática
    profile_manager = ProfileManager()
    
    # Procesar archivo con perfil detectado
    try:
        segments, stats, metadata = profile_manager.process_file(
            file_path=test_file,
            profile_name=profile_candidate.profile_name,  # Usar perfil detectado
            output_format="generic",
            output_mode="generic"
        )
        
        print(f"✅ Procesamiento exitoso!")
        print(f"📊 Estadísticas:")
        print(f"   • Total segmentos: {len(segments)}")
        print(f"   • Perfil usado: {metadata.get('profile_used', 'N/A')}")
        print(f"   • Segmentador: {metadata.get('segmenter_used', 'N/A')}")
        
        # === PASO 3: ANÁLISIS DE SEGMENTACIÓN ===
        print(f"\n📋 PASO 3: Analizando calidad de segmentación...")
        
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
        
        # Mostrar primeros segmentos para verificar estructura
        print(f"\n📋 PASO 4: Primeros 5 segmentos:")
        for i, segment in enumerate(segments[:5]):
            text_preview = segment.text[:100].replace('\n', ' ')
            if len(segment.text) > 100:
                text_preview += "..."
            print(f"   {i+1:2d}. [{len(segment.text):4d} chars] {text_preview}")
        
        # === VERIFICACIONES ESPECÍFICAS PARA VERSO ===
        if profile_candidate.profile_name == 'verso':
            print(f"\n📋 PASO 5: Verificaciones específicas de VERSO...")
            
            # Verificar que no hay segmentos gigantes (>2000 chars)
            large_segments = [i for i, s in enumerate(segments) if len(s.text) > 2000]
            if large_segments:
                print(f"⚠️  PROBLEMA: {len(large_segments)} segmentos muy largos:")
                for idx in large_segments[:3]:  # Mostrar solo los primeros 3
                    print(f"      Segmento {idx+1}: {len(segments[idx].text)} chars")
            else:
                print(f"✅ Sin segmentos excesivamente largos")
            
            # Verificar que hay segmentos cortos (versos típicos)
            short_segments = [s for s in segments if len(s.text) < 200]
            print(f"✅ Segmentos cortos (versos): {len(short_segments)}/{len(segments)}")
            
            # Buscar títulos de poemas
            potential_titles = []
            for i, segment in enumerate(segments):
                text = segment.text.strip()
                if (len(text) < 100 and 
                    (text.isupper() or 
                     text.startswith('"') and text.endswith('"') or
                     len(text.split()) <= 8)):
                    potential_titles.append((i+1, text))
            
            print(f"🏷️  Posibles títulos detectados: {len(potential_titles)}")
            for idx, title in potential_titles[:5]:  # Mostrar primeros 5
                print(f"      Segmento {idx}: {title}")
        
        # === RESULTADO FINAL ===
        print(f"\n" + "=" * 80)
        print(f"📊 RESULTADO FINAL:")
        print(f"   🔍 Perfil detectado: {profile_candidate.profile_name} (confianza: {profile_candidate.confidence:.2f})")
        print(f"   📄 Segmentos generados: {len(segments)}")
        print(f"   ✍️  Autor: {document_author or 'NO DETECTADO'}")
        print(f"   📏 Longitud promedio: {avg_length:.1f} chars")
        
        if profile_candidate.profile_name == 'verso':
            if large_segments:
                print(f"   ❌ PROBLEMA: Segmentación incorrecta (segmentos muy largos)")
                return False
            else:
                print(f"   ✅ Segmentación apropiada para verso")
                return True
        else:
            print(f"   ⚠️  ADVERTENCIA: Se esperaba perfil 'verso' para Rubén Darío")
            return False
            
    except Exception as e:
        print(f"❌ Error en procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_profile_detection_and_segmentation()
    if success:
        print(f"\n🎉 TEST EXITOSO!")
    else:
        print(f"\n💥 TEST FALLÓ!")
    
    sys.exit(0 if success else 1) 