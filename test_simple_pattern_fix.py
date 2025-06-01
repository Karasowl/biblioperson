#!/usr/bin/env python3
"""
🔧 TEST SIMPLE: LIMPIEZA DIRECTA DE ELEMENTOS CORRUPTOS
Implementa directamente la limpieza sin depender de detección automática.
"""

import re

def clean_corrupted_elements(text):
    """
    Limpia elementos corruptos directamente del texto.
    """
    if not text:
        return text
    
    # Patrones para detectar elementos corruptos de "Antología Rubén Darío"
    patterns_to_remove = [
        r'\*Antolo\*.*\*[gí]\*.*\*[íi]a\*.*Rub[eé]n.*Dar[íi]o\*?',  # *Antolo* *g* *ía* *Rubén Darío*
        r'Antolo[gí].*Rub[eé]n.*Dar[íi]o',  # Variaciones simples
        r'\*.*Antolo.*\*.*Rub[eé]n.*Dar[íi]o\*?',  # Con asteriscos
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # Limpiar espacios y saltos de línea excesivos
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

def test_direct_cleaning():
    """
    Testa la limpieza directa de elementos corruptos.
    """
    print("🔧 TEST SIMPLE: LIMPIEZA DIRECTA")
    print("=" * 50)
    
    # Casos de test del usuario
    test_cases = [
        # Caso 1: Elemento corrupto al final
        {
            "input": "TARDE DEL TRÓPICO\nEs la tarde gris triste.\nViste el mar de terciopelo\ny el cielo profundo viste\nde duelo.\n*Antolo* *g* *ía* *Rubén Darío*",
            "expected_clean": "TARDE DEL TRÓPICO\nEs la tarde gris triste.\nViste el mar de terciopelo\ny el cielo profundo viste\nde duelo."
        },
        
        # Caso 2: Elemento corrupto en medio  
        {
            "input": "A JOSÉ ENRIQUE RODÓ\nYo soy aquel que ayer no más decía\nel verso azul la canción profana\n*Antolo* *g* *ía* *Rubén Darío*\ny dos cuernos de sátiro en la frente.",
            "expected_clean": "A JOSÉ ENRIQUE RODÓ\nYo soy aquel que ayer no más decía\nel verso azul la canción profana\n\ny dos cuernos de sátiro en la frente."
        },
        
        # Caso 3: Solo elemento corrupto
        {
            "input": "*Antolo* *g* *ía* *Rubén Darío*",
            "expected_clean": ""
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Caso {i}:")
        print(f"   Entrada: '{test_case['input'][:50]}...'")
        
        result = clean_corrupted_elements(test_case['input'])
        
        print(f"   Resultado: '{result[:50]}...'")
        print(f"   Esperado:  '{test_case['expected_clean'][:50]}...'")
        
        # Verificar que no contiene el elemento corrupto
        corrupted_element = "*Antolo* *g* *ía* *Rubén Darío*"
        if corrupted_element not in result:
            print(f"   ✅ Elemento corrupto eliminado")
        else:
            print(f"   ❌ Elemento corrupto AÚN PRESENTE")
            all_passed = False
        
        # Verificar que queda contenido válido (excepto caso 3 que debe quedar vacío)
        if i == 3:  # Caso 3 debe quedar vacío
            if not result:
                print(f"   ✅ Correctamente vacío")
            else:
                print(f"   ❌ Debería estar vacío")
                all_passed = False
        else:  # Casos 1 y 2 deben tener contenido
            if result and len(result) > 10:
                print(f"   ✅ Contenido preservado")
            else:
                print(f"   ❌ Contenido perdido")
                all_passed = False
    
    if all_passed:
        print(f"\n🎉 TODOS LOS TESTS PASARON - LIMPIEZA DIRECTA FUNCIONANDO")
        return True
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON")
        return False

if __name__ == "__main__":
    test_direct_cleaning() 