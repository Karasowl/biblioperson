#!/usr/bin/env python3
"""
🔧 TEST DE DETECCIÓN DE TÍTULOS
Test para verificar que títulos como "SOUVENIR" y "CANTARES DE EL CARDÓN" se detecten correctamente.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def test_title_detection():
    """
    Prueba la detección de títulos específicos que estaban fallando.
    """
    print("🔧 PROBANDO DETECCIÓN DE TÍTULOS ESPECÍFICOS")
    print("=" * 60)
    
    segmenter = VerseSegmenter()
    
    # Casos de prueba basados en el problema del usuario
    test_cases = [
        {
            'text': 'SOUVENIR',
            'expected': True,
            'description': 'Título simple en mayúsculas'
        },
        {
            'text': 'CANTARES DE EL CARDÓN',
            'expected': True,
            'description': 'Título con preposiciones en mayúsculas'
        },
        {
            'text': 'Va la vela blanca',
            'expected': False,
            'description': 'Verso normal (no título)'
        },
        {
            'text': 'Para sobrevivirme te forjé como un arma',
            'expected': False,
            'description': 'Verso que anteriormente se detectaba como título'
        },
        {
            'text': 'Poema 1',
            'expected': True,
            'description': 'Título tipo "Poema N"'
        },
        {
            'text': 'I',
            'expected': True,
            'description': 'Título numérico romano'
        },
        {
            'text': 'UNA DIADEMA FLORIDA',
            'expected': True,
            'description': 'Otro título en mayúsculas'
        }
    ]
    
    print("🧪 PROBANDO DETECCIÓN DE TÍTULOS:")
    print("-" * 40)
    
    for i, case in enumerate(test_cases, 1):
        block = {'text': case['text'], 'is_heading': False}
        
        is_title = segmenter._is_title_block(block)
        expected = case['expected']
        status = "✅" if is_title == expected else "❌"
        
        print(f"{status} Test {i}: '{case['text']}'")
        print(f"    {case['description']}")
        print(f"    Esperado: {'TÍTULO' if expected else 'NO TÍTULO'}")
        print(f"    Resultado: {'TÍTULO' if is_title else 'NO TÍTULO'}")
        print()
    
    print("🧪 SIMULANDO SEGMENTACIÓN COMPLETA:")
    print("-" * 40)
    
    # Simular bloques como los del usuario
    blocks = [
        {'text': 'SOUVENIR', 'is_heading': False},
        {'text': '', 'is_heading': False},  # Línea vacía
        {'text': 'Va la vela blanca', 'is_heading': False},
        {'text': 'bajo el cielo azul', 'is_heading': False},
        {'text': 'y en el mar amante', 'is_heading': False},
        {'text': 'de mi mente, tú.', 'is_heading': False},
        {'text': '', 'is_heading': False},  # Línea vacía
        {'text': 'Sople buena brisa', 'is_heading': False},
        {'text': 'brille alegre el sol', 'is_heading': False},
        {'text': 'y que digan aguas', 'is_heading': False},
        {'text': 'y cielos:¡Amor!', 'is_heading': False},
        {'text': '', 'is_heading': False},  # Línea vacía
        {'text': 'CANTARES DE EL CARDÓN', 'is_heading': False},
        {'text': '', 'is_heading': False},  # Línea vacía
        {'text': 'Una diadema florida', 'is_heading': False},
        {'text': 'Te brinda un emperador', 'is_heading': False},
        {'text': 'Emperatriz de mi vida,', 'is_heading': False},
        {'text': 'Emperatriz de mi amor.', 'is_heading': False},
    ]
    
    segments = segmenter.segment(blocks)
    
    print(f"📊 RESULTADOS DE SEGMENTACIÓN:")
    print(f"Segmentos detectados: {len(segments)}")
    print()
    
    for i, segment in enumerate(segments, 1):
        print(f"🎭 Segmento {i}:")
        print(f"   Título: {segment.get('title', 'SIN TÍTULO')}")
        print(f"   Tipo: {segment.get('type', 'unknown')}")
        print(f"   Versos: {segment.get('verse_count', 0)}")
        print(f"   Texto: {segment.get('text', '')[:100]}...")
        print()
    
    print("✅ TEST DE DETECCIÓN DE TÍTULOS COMPLETADO")

if __name__ == "__main__":
    test_title_detection() 