#!/usr/bin/env python3
"""
🚀 TEST DE ESTRATEGIA OCR ULTRA-RESTRICTIVA
Verifica que el PDFLoader V7.5 no aplique OCR innecesariamente.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

def test_ocr_strategy():
    """
    Simula diferentes escenarios para verificar cuándo se activa OCR.
    """
    print("🚀 PROBANDO ESTRATEGIA OCR ULTRA-RESTRICTIVA")
    print("=" * 60)
    
    # Simular casos de prueba
    test_cases = [
        {
            'name': 'Mario Benedetti (243 páginas, ~60 poemas)',
            'page_count': 243,
            'segment_count': 60,
            'corruption_percentage': 5.0,
            'corrupted_blocks': 10,
            'total_blocks': 500,
            'expected_ocr': False,
            'reason': 'Documento funcional con segmentos suficientes'
        },
        {
            'name': 'Pablo Neruda (25 páginas, 22 poemas)',
            'page_count': 25,
            'segment_count': 22,
            'corruption_percentage': 2.0,
            'corrupted_blocks': 5,
            'total_blocks': 150,
            'expected_ocr': False,
            'reason': 'Documento perfecto'
        },
        {
            'name': 'PDF completamente corrupto',
            'page_count': 10,
            'segment_count': 0,
            'corruption_percentage': 85.0,
            'corrupted_blocks': 80,
            'total_blocks': 100,
            'expected_ocr': True,
            'reason': 'Corrupción extrema + 0 segmentos'
        },
        {
            'name': 'PDF con falla total (solo 2 segmentos)',
            'page_count': 50,
            'segment_count': 2,
            'corruption_percentage': 10.0,
            'corrupted_blocks': 5,
            'total_blocks': 100,
            'expected_ocr': True,
            'reason': 'Falla completa de extracción'
        },
        {
            'name': 'PDF grande con ratio bajo pero funcional',
            'page_count': 100,
            'segment_count': 30,
            'corruption_percentage': 15.0,
            'corrupted_blocks': 20,
            'total_blocks': 200,
            'expected_ocr': False,
            'reason': 'Aunque ratio bajo (0.3), tiene suficientes segmentos'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {case['name']}")
        print("-" * 40)
        
        # Simular evaluación PRE-segmentación
        pre_ocr_needed = evaluate_pre_segmentation_ocr(
            case['corruption_percentage'],
            case['corrupted_blocks'],
            case['total_blocks'],
            case['page_count']
        )
        
        # Simular evaluación POST-segmentación
        post_ocr_needed = evaluate_post_segmentation_ocr(
            case['segment_count'],
            case['page_count']
        )
        
        final_ocr_needed = pre_ocr_needed or post_ocr_needed
        
        ratio = case['segment_count'] / case['page_count']
        
        print(f"   📄 Páginas: {case['page_count']}")
        print(f"   🎭 Segmentos: {case['segment_count']}")
        print(f"   📊 Ratio: {ratio:.3f}")
        print(f"   🚨 Corrupción: {case['corruption_percentage']:.1f}%")
        print(f"   🔍 OCR Pre-segmentación: {'SÍ' if pre_ocr_needed else 'NO'}")
        print(f"   🔍 OCR Post-segmentación: {'SÍ' if post_ocr_needed else 'NO'}")
        print(f"   🎯 Decisión final: {'ACTIVAR OCR' if final_ocr_needed else 'NO USAR OCR'}")
        
        status = "✅" if final_ocr_needed == case['expected_ocr'] else "❌"
        print(f"   {status} Esperado: {'OCR' if case['expected_ocr'] else 'NO OCR'}")
        print(f"   💡 Razón: {case['reason']}")

def evaluate_pre_segmentation_ocr(corruption_percentage, corrupted_blocks, total_blocks, page_count):
    """
    Simula la lógica PRE-segmentación del PDFLoader V7.5
    """
    reasons = []
    
    # Criterio 1: SOLO corrupción extrema (≥70%)
    if corruption_percentage >= 70:
        reasons.append("Corrupción extrema")
    
    # Criterio 2: SOLO cuando >80% de bloques están corruptos
    if corrupted_blocks > total_blocks * 0.8:
        reasons.append("Mayoría de bloques corruptos")
    
    # Criterio 3: SOLO fallas extremas de extracción (≤10 bloques en documentos grandes)
    if page_count > 20 and total_blocks <= 10:
        reasons.append("Falla extrema de extracción")
    
    return len(reasons) > 0

def evaluate_post_segmentation_ocr(segment_count, page_count):
    """
    Simula la lógica POST-segmentación del PDFLoader V7.5
    """
    reasons = []
    ratio = segment_count / page_count if page_count > 0 else 0
    
    # Criterio 1: SOLO documentos con ≤3 segmentos totales (falla completa)
    if segment_count <= 3:
        reasons.append("Falla completa de extracción")
    
    # Criterio 2: SOLO documentos largos (≥20 páginas) con ratio extremadamente bajo (< 0.1)
    elif page_count >= 20 and ratio < 0.1:
        reasons.append("Documento muy largo con ratio extremo")
    
    # Criterio 3: SOLO cuando no hay segmentos útiles (0 segmentos)
    elif segment_count == 0:
        reasons.append("Extracción completamente fallida")
    
    return len(reasons) > 0

if __name__ == "__main__":
    test_ocr_strategy() 