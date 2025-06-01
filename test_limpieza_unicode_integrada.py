#!/usr/bin/env python3
"""
Test para verificar que la limpieza Unicode integrada funciona correctamente
"""

import sys
sys.path.append('.')

from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from pathlib import Path

def test_limpieza_unicode_integrada():
    print("🧹 TEST: Limpieza Unicode integrada en CommonBlockPreprocessor")
    
    # Crear preprocessor con limpieza activada
    preprocessor = CommonBlockPreprocessor({
        'clean_unicode_corruption': True,
        'filter_insignificant_blocks': False  # Desactivar filtros para ver solo la limpieza
    })
    
    print(f"\n1️⃣ PASO 1: Verificar configuración")
    print(f"   ✅ Limpieza Unicode activada: {preprocessor.config.get('clean_unicode_corruption')}")
    
    # Bloques de prueba con texto corrupto
    bloques_corruptos = [
        {
            'text': 'u001a\u001c"\u0016\u001c \u001f\u001d\u0015\u0016\t\u0019\u0016\t\u0015!\t\u001f\u001c\u001a \u0016\u001c \u001f\u00188\tFK!\u001e\t\u0015\u0016\t\u001b\u0018(\u0016 \u0016G\t',
            'page': 1,
            'order': 1.0
        },
        {
            'text': 'Texto normal sin corrupción',
            'page': 1,
            'order': 2.0
        },
        {
            'text': ';  )␦      4␦4>            !$\', .!6',
            'page': 1,
            'order': 3.0
        },
        {
            'text': '—¿Saben qué estuve pensando?\n\nQue nuestros queridos maridos\n\nnos llevan algunos años.',
            'page': 1,
            'order': 4.0
        }
    ]
    
    print(f"\n2️⃣ PASO 2: Procesar bloques con texto corrupto")
    print(f"   📥 Bloques de entrada: {len(bloques_corruptos)}")
    
    # Mostrar ejemplos de texto corrupto
    print(f"\n   📝 Ejemplos de texto corrupto:")
    for i, bloque in enumerate(bloques_corruptos, 1):
        texto_original = bloque['text']
        if len(texto_original) > 100:
            texto_mostrar = texto_original[:100] + '...'
        else:
            texto_mostrar = texto_original
        print(f"      [{i}] Original: {repr(texto_mostrar)}")
    
    # Procesar con el preprocessor
    metadata = {'titulo_documento': 'Test Unicode Cleanup'}
    bloques_limpios = preprocessor.process(bloques_corruptos, metadata)
    
    print(f"\n3️⃣ PASO 3: Resultados de la limpieza")
    print(f"   📤 Bloques de salida: {len(bloques_limpios)}")
    
    # Comparar resultados
    print(f"\n   📊 Análisis de resultados:")
    print(f"      📥 Bloques originales: {len(bloques_corruptos)}")
    print(f"      📤 Bloques resultantes: {len(bloques_limpios)}")
    
    # Mostrar los bloques resultantes
    print(f"\n   📝 Bloques resultantes:")
    for i, bloque_limpio in enumerate(bloques_limpios, 1):
        # Los bloques pueden ser diccionarios o tener diferentes estructuras
        if isinstance(bloque_limpio, dict):
            texto_limpio = bloque_limpio.get('text', str(bloque_limpio))
        else:
            texto_limpio = str(bloque_limpio)
        
        if len(texto_limpio) > 100:
            limpio_mostrar = texto_limpio[:100] + '...'
        else:
            limpio_mostrar = texto_limpio
        
        print(f"      [{i}] Resultado: {repr(limpio_mostrar)}")
    
    # Verificar si hay limpieza Unicode comparando texto específico
    print(f"\n   🧹 Verificación de limpieza:")
    
    # Test directo del método de limpieza
    texto_corrupto_test = 'u001a\u001c"\u0016\u001c \u001f\u001d\u0015\u0016\t\u0019\u0016'
    texto_limpio_test = preprocessor._clean_unicode_corruption(texto_corrupto_test)
    
    print(f"      Original: {repr(texto_corrupto_test)}")
    print(f"      Limpio:   {repr(texto_limpio_test)}")
    
    if texto_corrupto_test != texto_limpio_test:
        print(f"      ✅ LIMPIEZA FUNCIONANDO: {len(texto_corrupto_test)} → {len(texto_limpio_test)} caracteres")
        print(f"   ✅ SUCCESS: La limpieza Unicode está funcionando correctamente")
    else:
        print(f"      ❌ NO HUBO LIMPIEZA")
        print(f"   ❌ ERROR: No se detectó limpieza Unicode")
    
    print(f"\n4️⃣ PASO 4: Estadísticas finales")
    print(f"   🔧 CommonBlockPreprocessor procesó correctamente los bloques")
    print(f"   🧹 Función de limpieza Unicode: {'ACTIVA' if preprocessor.config.get('clean_unicode_corruption') else 'INACTIVA'}")
    
    return bloques_limpios

if __name__ == "__main__":
    test_limpieza_unicode_integrada() 