#!/usr/bin/env python3
"""
Análisis simple de patrones de verso y propuestas de mejora
"""

import sys
sys.path.append('.')

import re
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def test_detection_patterns():
    print("🔍 ANÁLISIS: Patrones de detección de inicio de poema")
    
    # Casos típicos del PDF de Benedetti según tu análisis
    test_cases = [
        # 1. Títulos explícitos entre comillas (25 poemas)
        {"text": '"Cementerio"', "expected": True, "category": "Título explícito"},
        {"text": '"La muerte"', "expected": True, "category": "Título explícito"},
        {"text": '"Mi táctica"', "expected": True, "category": "Título explícito"},
        
        # 2. Títulos sin comillas pero claramente títulos (muchos más)
        {"text": "Cementerio", "expected": True, "category": "Título sin comillas"},
        {"text": "País Verde y Herido", "expected": True, "category": "Título compuesto"},
        {"text": "Esperanza", "expected": True, "category": "Título una palabra"},
        
        # 3. Inicios de poema sin título (65 piezas que mencionas)
        {"text": "En el fondo del pozo\nlas estrellas brillan", "expected": True, "category": "Inicio poético"},
        {"text": "Cuando llega la noche\ny todo se silencia", "expected": True, "category": "Inicio poético"},
        {"text": "Hay momentos en que\nla vida se detiene", "expected": True, "category": "Inicio poético"},
        
        # 4. Separadores visuales
        {"text": "***", "expected": True, "category": "Separador visual"},
        {"text": "---", "expected": True, "category": "Separador visual"},
        {"text": "...", "expected": True, "category": "Separador visual"},
        
        # 5. Listas numeradas (43 poemas de listas)
        {"text": "1. Poema de amor", "expected": True, "category": "Lista numerada"},
        {"text": "23. Nocturno", "expected": True, "category": "Lista numerada"},
        {"text": "- Verso libre", "expected": True, "category": "Lista con guión"},
        
        # 6. Números romanos
        {"text": "I", "expected": True, "category": "Número romano"},
        {"text": "XV", "expected": True, "category": "Número romano"},
        {"text": "XXXII", "expected": True, "category": "Número romano"},
        
        # 7. Patrones que NO deben ser títulos
        {"text": "página 125", "expected": False, "category": "Número de página"},
        {"text": "continuación del párrafo anterior que sigue con texto normal", "expected": False, "category": "Texto largo"},
        {"text": "y entonces", "expected": False, "category": "Conectivo"},
    ]
    
    print(f"\n📊 TESTING: {len(test_cases)} casos de prueba")
    
    # Test con segmentador actual
    current_segmenter = VerseSegmenter({})
    
    results = {"correct": 0, "incorrect": 0, "details": []}
    
    for i, case in enumerate(test_cases):
        text = case["text"]
        expected = case["expected"]
        category = case["category"]
        
        # Simular un bloque
        block = {"text": text, "is_heading": False}
        
        # Test con método actual
        is_detected = current_segmenter._is_main_title(block)
        
        is_correct = (is_detected == expected)
        if is_correct:
            results["correct"] += 1
            status = "✅"
        else:
            results["incorrect"] += 1
            status = "❌"
        
        results["details"].append({
            "case": i+1,
            "text": text[:40] + "..." if len(text) > 40 else text,
            "category": category,
            "expected": expected,
            "detected": is_detected,
            "correct": is_correct
        })
        
        print(f"   [{i+1:2d}] {status} {category}: {repr(text[:40])}...")
    
    print(f"\n📈 RESULTADOS:")
    print(f"   ✅ Correctos: {results['correct']} ({results['correct']/len(test_cases)*100:.1f}%)")
    print(f"   ❌ Incorrectos: {results['incorrect']} ({results['incorrect']/len(test_cases)*100:.1f}%)")
    
    # Análisis por categoría
    print(f"\n📋 ANÁLISIS POR CATEGORÍA:")
    categories = {}
    for detail in results["details"]:
        cat = detail["category"]
        if cat not in categories:
            categories[cat] = {"correct": 0, "total": 0}
        categories[cat]["total"] += 1
        if detail["correct"]:
            categories[cat]["correct"] += 1
    
    for cat, stats in categories.items():
        accuracy = stats["correct"] / stats["total"] * 100
        print(f"   {cat}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
    
    return results

def propose_improved_patterns():
    print(f"\n🚀 PROPUESTA: Patrones mejorados para detectar ~140 poemas")
    
    improved_patterns = [
        # 1. Títulos explícitos (mantener actual)
        {"pattern": r'^["""].*["""]$', "description": "Títulos entre comillas", "estimated_matches": 25},
        
        # 2. Títulos sin comillas (NUEVO - muy importante)
        {"pattern": r'^[A-ZÁÉÍÓÚ][a-záéíóú\s]{1,30}$', "description": "Títulos capitalizados cortos", "estimated_matches": 30},
        
        # 3. Números romanos como títulos (NUEVO)
        {"pattern": r'^[IVXLCDM]+$', "description": "Números romanos", "estimated_matches": 15},
        
        # 4. Listas numeradas (NUEVO)
        {"pattern": r'^\d+[\.\)]\s+\w+', "description": "Listas numeradas", "estimated_matches": 43},
        
        # 5. Separadores visuales (NUEVO)
        {"pattern": r'^[\*\-_=\.\s]{3,}$', "description": "Separadores visuales", "estimated_matches": 10},
        
        # 6. Inicios poéticos sin título (NUEVO - detección de estructura)
        {"pattern": "STRUCTURE_DETECTION", "description": "Cambios de estructura/espaciado", "estimated_matches": 20},
        
        # 7. Páginas nuevas (NUEVO)
        {"pattern": "PAGE_BREAK", "description": "Inicios en páginas nuevas", "estimated_matches": 15},
        
        # 8. Después de texto largo (NUEVO)
        {"pattern": "AFTER_LONG_TEXT", "description": "Después de poemas largos", "estimated_matches": 10},
    ]
    
    total_estimated = sum(p["estimated_matches"] for p in improved_patterns)
    
    print(f"   🎯 PATRONES PROPUESTOS ({len(improved_patterns)} tipos):")
    for pattern in improved_patterns:
        matches = pattern["estimated_matches"]
        desc = pattern["description"]
        print(f"      • {desc}: ~{matches} poemas")
    
    print(f"\n   📊 TOTAL ESTIMADO: ~{total_estimated} poemas")
    print(f"   🎯 OBJETIVO USUARIO: 140 poemas")
    print(f"   📈 COBERTURA: {total_estimated/140*100:.1f}%")
    
    if total_estimated >= 120:
        print(f"   ✅ EXCELENTE: Cobertura adecuada")
    elif total_estimated >= 100:
        print(f"   ⚠️  BUENA: Cobertura aceptable")
    else:
        print(f"   ❌ INSUFICIENTE: Necesitamos más patrones")
    
    return improved_patterns

def create_improved_segmenter_code():
    print(f"\n💻 CÓDIGO: VerseSegmenter mejorado")
    
    improved_code = '''
def _is_main_title_improved(self, block: Dict[str, Any], block_index: int = 0, all_blocks: List = None) -> bool:
    """
    Versión mejorada que detecta MUCHOS más patrones de inicio de poema.
    Diseñada para detectar ~140 poemas en lugar de ~60.
    """
    text = block.get('text', '').strip()
    if not text:
        return False
    
    # 1. TÍTULOS EXPLÍCITOS entre comillas (mantener actual)
    if (text.startswith('"') and text.endswith('"')) and len(text) < 80:
        self.logger.debug(f"✅ Título explícito: {text}")
        return True
    
    # 2. NÚMEROS ROMANOS como títulos (NUEVO)
    if re.match(r'^[IVXLCDM]+$', text) and len(text) <= 10:
        self.logger.debug(f"✅ Número romano: {text}")
        return True
    
    # 3. LISTAS NUMERADAS (NUEVO - muy importante para 43 poemas)
    if re.match(r'^\\d+[\\.)\\]\\s+\\w+', text):
        self.logger.debug(f"✅ Lista numerada: {text}")
        return True
    
    # 4. SEPARADORES VISUALES (NUEVO)
    if re.match(r'^[\\*\\-_=\\.\\s]{3,}$', text):
        self.logger.debug(f"✅ Separador visual: {text}")
        return True
    
    # 5. TÍTULOS SIN COMILLAS - capitalizados y cortos (NUEVO - MUY IMPORTANTE)
    if (len(text) <= 50 and 
        text[0].isupper() and 
        not text.endswith(('.', '!', '?')) and
        len(text.split()) <= 6 and
        not text.isdigit() and
        not text.lower().startswith(('página', 'capítulo', 'continúa', 'fin'))):
        self.logger.debug(f"✅ Título sin comillas: {text}")
        return True
    
    # 6. DETECCIÓN POR CONTEXTO (NUEVO)
    if all_blocks and block_index > 0:
        prev_block = all_blocks[block_index - 1]
        prev_text = prev_block.get('text', '').strip()
        
        # Después de separador visual o bloque vacío
        if not prev_text or re.match(r'^[\\*\\-_=\\.\\s]{3,}$', prev_text):
            if len(text) < 100 and text[0].isupper():
                self.logger.debug(f"✅ Después de separador: {text}")
                return True
        
        # Después de texto muy largo (fin de poema anterior)
        if len(prev_text) > 300:
            if len(text) < 80 and text[0].isupper():
                self.logger.debug(f"✅ Después de texto largo: {text}")
                return True
    
    # 7. DETECCIÓN POR PÁGINA (NUEVO)
    if all_blocks and block_index > 0:
        prev_page = all_blocks[block_index - 1].get('page', 0)
        curr_page = block.get('page', 0)
        
        if curr_page > prev_page and len(text) < 100 and text[0].isupper():
            self.logger.debug(f"✅ Nueva página: {text}")
            return True
    
    # 8. HEADINGS detectados por PDF (mantener actual)
    if block.get('is_heading', False):
        self.logger.debug(f"✅ Heading PDF: {text}")
        return True
    
    return False
    '''
    
    print(f"   📝 Código generado para _is_main_title_improved()")
    print(f"   🔧 Incluye 8 tipos de detección diferentes")
    print(f"   🎯 Debería detectar ~120-140 poemas")
    
    return improved_code

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 ANÁLISIS PARA MEJORAR DETECCIÓN DE VERSO")
    print("=" * 60)
    
    # 1. Test con patrones actuales
    current_results = test_detection_patterns()
    
    # 2. Proponer mejoras
    improved_patterns = propose_improved_patterns()
    
    # 3. Generar código mejorado
    improved_code = create_improved_segmenter_code() 