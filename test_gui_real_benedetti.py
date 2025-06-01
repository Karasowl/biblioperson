#!/usr/bin/env python3
"""
Test usando el flujo EXACTO de la GUI para verificar las mejoras del VerseSegmenter
"""

import sys
sys.path.append('.')

from dataset.processing.profile_manager import ProfileManager
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def test_gui_real_benedetti():
    print("🎯 TEST: VerseSegmenter MEJORADO usando flujo GUI real")
    
    # Ruta del archivo PDF
    archivo_pdf = Path("C:/Users/adven/Downloads/benedetti-mario-obra-completa.pdf")
    
    if not archivo_pdf.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_pdf}")
        return
    
    print(f"\n1️⃣ PASO 1: Usar ProfileManager exactamente como la GUI")
    
    # Configurar ProfileManager exactamente como la GUI
    profile_manager = ProfileManager()
    
    print(f"   📋 Parámetros configurados:")
    print(f"      - Archivo: {archivo_pdf.name}")
    print(f"      - Perfil: verso")
    print(f"      - Idioma: es")
    
    print(f"\n2️⃣ PASO 2: Procesar con ProfileManager")
    
    try:
        # Usar ProfileManager con la API correcta
        result = profile_manager.process_file(
            file_path=str(archivo_pdf),
            profile_name='verso',
            language_override='es',
            encoding='utf-8'
        )
        
        if result and len(result) > 0:
            # result es una lista de segmentos
            segments = result
            total_segments = len(segments)
            
            print(f"   🎯 POEMAS DETECTADOS: {total_segments}")
            print(f"   🎯 OBJETIVO USUARIO: 140 poemas")
            
            # Calcular cobertura
            coverage = (total_segments / 140) * 100
            
            if total_segments >= 120:
                print(f"   ✅ EXCELENTE: Cobertura muy buena ({total_segments}/140 = {coverage:.1f}%)")
            elif total_segments >= 100:
                print(f"   ✅ BUENA: Cobertura aceptable ({total_segments}/140 = {coverage:.1f}%)")
            elif total_segments >= 80:
                print(f"   ⚠️  MEJORABLE: Progreso pero insuficiente ({total_segments}/140 = {coverage:.1f}%)")
            elif total_segments >= 60:
                print(f"   👍 PROGRESO: Mejora respecto a versión anterior ({total_segments}/140 = {coverage:.1f}%)")
            else:
                print(f"   ❌ INSUFICIENTE: Necesitamos más mejoras ({total_segments}/140 = {coverage:.1f}%)")
            
            print(f"\n3️⃣ PASO 3: Análisis de primeros poemas detectados")
            
            # Mostrar primeros 10 poemas detectados
            print(f"   📝 PRIMEROS 10 POEMAS DETECTADOS:")
            for i, segment in enumerate(segments[:10]):
                # Obtener el título del texto (primera línea)
                text = segment.get('text', '') if isinstance(segment, dict) else str(segment)
                lines = text.split('\n')
                title = lines[0][:50] if lines else 'Sin título'
                
                # Contar versos aproximados
                verse_count = len([line for line in lines if line.strip()])
                
                print(f"      [{i+1:2d}] '{title}' ({verse_count} líneas)")
            
            # Analizar distribución de tamaños
            print(f"\n4️⃣ PASO 4: Análisis de distribución")
            sizes = []
            for segment in segments:
                text = segment.get('text', '') if isinstance(segment, dict) else str(segment)
                lines = len([line for line in text.split('\n') if line.strip()])
                sizes.append(lines)
            
            if sizes:
                avg_size = sum(sizes) / len(sizes)
                min_size = min(sizes)
                max_size = max(sizes)
                
                print(f"   📏 Tamaño promedio: {avg_size:.1f} líneas")
                print(f"   📏 Tamaño mínimo: {min_size} líneas")
                print(f"   📏 Tamaño máximo: {max_size} líneas")
                
                # Detectar poemas muy largos (posibles fusiones incorrectas)
                large_poems = [i for i, size in enumerate(sizes) if size > 50]
                if large_poems:
                    print(f"   ⚠️  Poemas muy largos detectados: {len(large_poems)} (posibles fusiones)")
            
            return {
                'total_poems': total_segments,
                'coverage': coverage,
                'first_poems': segments[:5],
                'avg_size': avg_size if sizes else 0
            }
        
        else:
            print(f"   ❌ ERROR: No se pudo procesar el archivo o no se encontraron segmentos")
            return None
            
    except Exception as e:
        print(f"   ❌ ERROR en ProfileManager: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    resultado = test_gui_real_benedetti()
    
    if resultado:
        print(f"\n✅ TEST COMPLETADO")
        print(f"   🎯 Resultado: {resultado['total_poems']} poemas detectados")
        print(f"   📈 Cobertura: {resultado['coverage']:.1f}%")
        print(f"   📏 Tamaño promedio: {resultado['avg_size']:.1f} líneas")
        
        if resultado['coverage'] >= 85:
            print(f"   🎉 ¡OBJETIVO ALCANZADO! Excelente mejora")
        elif resultado['coverage'] >= 70:
            print(f"   👍 PROGRESO SIGNIFICATIVO - Casi llegamos")
        elif resultado['coverage'] >= 45:
            print(f"   📈 MEJORA NOTABLE - Buen progreso")
        else:
            print(f"   🔧 NECESITAMOS MÁS AJUSTES")
    else:
        print(f"\n❌ TEST FALLÓ - No se pudo procesar el archivo") 