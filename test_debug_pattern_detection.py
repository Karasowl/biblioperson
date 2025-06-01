#!/usr/bin/env python3
"""
🔧 DEBUG: DETECCIÓN DE PATRONES
Test simple para debuggear por qué no se detecta "*Antolo* *g* *ía* *Rubén Darío*"
"""

import re

def test_pattern_detection():
    print("🔧 DEBUG: DETECCIÓN DE PATRONES")
    print("=" * 50)
    
    # Texto problemático del usuario
    test_text = "*Antolo* *g* *ía* *Rubén Darío*"
    print(f"📝 Texto a detectar: '{test_text}'")
    
    # Patrones que estoy usando (CORREGIDOS)
    patterns = [
        r'\*Antolo\*.*\*[gí]\*.*\*[íi]a\*.*Rub[eé]n.*Dar[íi]o',  # *Antolo* *g* *ía* *Rubén Darío*
        r'Antolo.*Rub[eé]n.*Dar[íi]o',  # Variaciones simples de "Antología Rubén Darío"
        r'\*.*Antolo.*\*.*Rub[eé]n.*Dar[íi]o',  # Cualquier cosa con asteriscos, Antolo, Rubén, Darío
    ]
    
    print(f"\n🎯 PROBANDO PATRONES:")
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPatrón {i}: {pattern}")
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"  ✅ MATCH: '{match.group()}'")
        else:
            print(f"  ❌ NO MATCH")
    
    # Intentemos patrones más simples
    print(f"\n🔧 PROBANDO PATRONES SIMPLES:")
    simple_patterns = [
        r'\*Antolo\*',           # Solo *Antolo*
        r'\*g\*',                # Solo *g*
        r'\*ía\*',               # Solo *ía*
        r'\*Rubén\*',            # Solo *Rubén*
        r'\*Darío\*',            # Solo *Darío*
        r'Antolo.*Darío',        # Antolo...Darío (sin asteriscos)
        r'\*.*Antolo.*\*',       # Cualquier cosa con asteriscos y Antolo
    ]
    
    for i, pattern in enumerate(simple_patterns, 1):
        print(f"\nPatrón simple {i}: {pattern}")
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"  ✅ MATCH: '{match.group()}'")
        else:
            print(f"  ❌ NO MATCH")
    
    # Analizar carácter por carácter
    print(f"\n🔍 ANÁLISIS CARÁCTER POR CARÁCTER:")
    for i, char in enumerate(test_text):
        print(f"  [{i:2d}] '{char}' (ord: {ord(char)})")
    
    return True

if __name__ == "__main__":
    test_pattern_detection() 