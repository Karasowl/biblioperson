#!/usr/bin/env python3
"""
Test simple y directo del detector de títulos
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_simple_detector():
    print("🧪 TEST SIMPLE DETECTOR DE TÍTULOS")
    print("=" * 50)
    
    try:
        # Importar clases directamente
        from dataset.processing.segmenters.heading_segmenter import TitleDetector
        
        # Crear detector
        detector = TitleDetector()
        print("✅ TitleDetector creado")
        
        # Simular bloques con diferentes características
        test_blocks = [
            {
                'text': 'Introducción | ¿Son todos populistas?',
                'visual_metadata': {
                    'avg_font_size': 16,
                    'is_bold': True,
                    'alignment': 'center',
                    'text_length': 37
                }
            },
            {
                'text': 'Este es un párrafo normal de contenido que debería ser clasificado como texto regular sin ninguna característica especial.',
                'visual_metadata': {
                    'avg_font_size': 12,
                    'is_bold': False,
                    'alignment': 'left',
                    'text_length': 117
                }
            },
            {
                'text': '1. Lo que dicen los populistas',
                'visual_metadata': {
                    'avg_font_size': 14,
                    'is_bold': True,
                    'alignment': 'left',
                    'text_length': 30
                }
            },
            {
                'text': 'Capítulo 2: Las técnicas populistas',
                'visual_metadata': {
                    'avg_font_size': 15,
                    'is_bold': True,
                    'alignment': 'center',
                    'text_length': 35
                }
            }
        ]
        
        # Analizar características visuales
        baseline_stats = detector.analyze_visual_characteristics(test_blocks)
        print(f"📊 Estadísticas baseline: {baseline_stats}")
        
        # Evaluar cada bloque
        print(f"\n🔍 EVALUANDO BLOQUES:")
        title_candidates = []
        
        for i, block in enumerate(test_blocks):
            score = detector.calculate_title_score(block, baseline_stats)
            text = block['text'][:50] + "..." if len(block['text']) > 50 else block['text']
            
            print(f"Bloque {i+1}: Score={score:.2f} | {text}")
            
            if score >= 4.0:
                title_candidates.append((block, score))
                print(f"  ✅ TÍTULO DETECTADO!")
            else:
                print(f"  📄 Párrafo normal")
        
        # Determinar jerarquías
        if title_candidates:
            print(f"\n🏗️ DETERMINANDO JERARQUÍAS:")
            levels = detector.determine_hierarchy_level(title_candidates)
            
            for (block, score), level in zip(title_candidates, levels):
                text = block['text'][:50] + "..." if len(block['text']) > 50 else block['text']
                print(f"  Nivel {level}: {text}")
                
        print(f"\n✅ Test completado. {len(title_candidates)} títulos detectados.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_detector() 