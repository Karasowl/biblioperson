#!/usr/bin/env python3
"""
Script para probar el ProfileDetector directamente con el contenido extraído
"""

import sys
import os
sys.path.append('dataset')

from dataset.processing.profile_detector import ProfileDetector

def test_detector_with_content():
    """Probar el detector con el contenido extraído"""
    
    # Leer el contenido extraído
    try:
        with open("debug_extracted_content.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ No se encontró debug_extracted_content.txt")
        return
    
    print("🔍 TESTING PROFILE DETECTOR DIRECTAMENTE")
    print("=" * 60)
    
    # Crear detector
    detector = ProfileDetector()
    
    # Detectar perfil
    result = detector.detect_profile(content, "Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf")
    
    print(f"\n📊 RESULTADO:")
    print(f"  - Perfil detectado: {result.profile_name}")
    print(f"  - Confianza: {result.confidence:.1%}")
    print(f"  - Razones: {result.reasons}")
    print(f"  - Métricas: {result.structural_metrics}")
    
    # Mostrar detalles del análisis si están disponibles
    if hasattr(result, 'content_sample') and result.content_sample:
        print(f"  - Muestra de contenido: {len(result.content_sample)} caracteres")
    else:
        print(f"\n⚠️ No hay muestra de contenido en el resultado")
    
    # Mostrar primeras líneas analizadas
    lines = content.split('\n')[:10]
    print(f"\n📝 PRIMERAS 10 LÍNEAS ANALIZADAS:")
    for i, line in enumerate(lines):
        if line.strip():
            print(f"  {i+1:2d}: [{len(line):3d}] {line}")

if __name__ == "__main__":
    test_detector_with_content() 