#!/usr/bin/env python3
"""
🔧 TEST DE DETECCIÓN DE CORRUPCIÓN EXTREMA
Test para verificar que la nueva funcionalidad detecta y maneja texto corrupto correctamente.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

from dataset.processing.profile_manager import ProfileManager

def test_corruption_detection():
    """
    Prueba la detección de corrupción extrema con diferentes tipos de texto.
    """
    print("🔧 PROBANDO DETECCIÓN DE CORRUPCIÓN EXTREMA")
    print("=" * 60)
    
    manager = ProfileManager()
    
    # Test 1: Texto normal (no corrupto)
    normal_text = """Poema 1

Para sobrevivirme te forjé como un arma,
como una flecha en mi aljaba,
como una moneda en mi bolsa,
como una poción en mi pecho."""
    
    is_corrupted, reason = manager._detect_extreme_corruption(normal_text)
    print(f"✅ Texto normal: {'CORRUPTO' if is_corrupted else 'NORMAL'}")
    if is_corrupted:
        print(f"   Razón: {reason}")
    print()
    
    # Test 2: Texto extremadamente corrupto (como el del usuario)
    corrupted_text = """94
���������������
�����������
���������������
����������������������
������������
*�������������������������������������*
*�����������������������������*
����������������������������
�����������
��������
��
��������������������������������������������������
��������
��������������������������������������
��������������������������������������������������
��
��������
��������������������������������������������������
��������������������������������������������������
��
��������������������������������������������������
��������������������������������������������������
������������������������������������
��
�������������������������������������������������
��������������������������������������������������
��
�������
��������������������������������������������������
��������������������������������������������������
��
������������������
��������������������������������������������������
������������������������������
��������������������������������������������������
��������������������������������������������������"""
    
    is_corrupted, reason = manager._detect_extreme_corruption(corrupted_text)
    print(f"🚨 Texto corrupto: {'CORRUPTO' if is_corrupted else 'NORMAL'}")
    if is_corrupted:
        print(f"   Razón: {reason}")
    print()
    
    # Test 3: Texto con algunos caracteres corruptos pero no extremo
    mixed_text = """Poema 2
 
Este es un texto que tiene algunos caracteres � corruptos
pero no es extremadamente corrupto como para ser reemplazado.
La mayoría del contenido es legible."""
    
    is_corrupted, reason = manager._detect_extreme_corruption(mixed_text)
    print(f"⚠️ Texto mixto: {'CORRUPTO' if is_corrupted else 'NORMAL'}")
    if is_corrupted:
        print(f"   Razón: {reason}")
    print()
    
    # Test 4: Simulación de procesamiento completo
    print("🧪 SIMULANDO PROCESAMIENTO COMPLETO")
    print("-" * 40)
    
    # Simular segmentos como los del usuario
    segments = [
        {
            'text': normal_text,
            'type': 'poem',
            'metadata': {}
        },
        {
            'text': corrupted_text,
            'type': 'poem', 
            'metadata': {}
        },
        {
            'text': mixed_text,
            'type': 'poem',
            'metadata': {}
        }
    ]
    
    # Simular el procesamiento
    corrupted_count = 0
    for i, segment in enumerate(segments):
        is_corrupted, reason = manager._detect_extreme_corruption(segment['text'])
        if is_corrupted:
            corrupted_count += 1
            print(f"📄 Segmento {i+1}: REEMPLAZADO POR CORRUPCIÓN")
            print(f"   Razón: {reason}")
        else:
            print(f"📄 Segmento {i+1}: Procesado normalmente")
    
    print(f"\n📊 RESUMEN: {corrupted_count}/{len(segments)} segmentos corruptos detectados")
    
    print("\n✅ TEST DE DETECCIÓN DE CORRUPCIÓN COMPLETADO")

if __name__ == "__main__":
    test_corruption_detection() 