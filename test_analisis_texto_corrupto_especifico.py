#!/usr/bin/env python3
"""
Test para analizar texto corrupto específico y mejorar la detección
"""

import sys
sys.path.append('.')

import re
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor

def analyze_specific_corrupted_text():
    print("🔍 ANÁLISIS: Texto corrupto específico del usuario")
    
    # El texto corrupto específico que mencionó el usuario
    texto_corrupto = "' ,+ ) ( ,+8 + ( ) 4 A . < 0 *+ !\n& %\n) -+0 6 * 0 ! ) * /8 (\n\" # &' %\n2 & & # ! \"*#%\n' ,+ ( ) -+1 *- ( 0 1 / 1 ! ( * 5+ )! ) 52 ( 01 1 ) A +\n2 ) - \" % / \" \" \" * %\n( ; 0 ) . *+)0 ) . 0 *+ ! ( (7)\n# $ ) - ( & $ / \"& %\n\" (\" ! & ! ! ' - ! \"3#%\n) + 3+ 4 (! ( *+ / * ) * 4 * ) (0 ! G ,+8 .+ (* 1 E C ) 2 D"
    
    print(f"\n1️⃣ PASO 1: Análisis del texto corrupto")
    print(f"   📏 Longitud: {len(texto_corrupto)} caracteres")
    print(f"   📝 Texto: {texto_corrupto[:200]}..." if len(texto_corrupto) > 200 else f"   📝 Texto: {texto_corrupto}")
    
    # Analizar patrones en el texto
    print(f"\n2️⃣ PASO 2: Detectar patrones de corrupción")
    
    # Contar tipos de caracteres
    letras = len(re.findall(r'[a-zA-Z]', texto_corrupto))
    numeros = len(re.findall(r'[0-9]', texto_corrupto))
    espacios = len(re.findall(r'\s', texto_corrupto))
    simbolos = len(re.findall(r'[^\w\s]', texto_corrupto))
    
    print(f"   📊 Composición del texto:")
    print(f"      🔤 Letras: {letras} ({letras/len(texto_corrupto)*100:.1f}%)")
    print(f"      🔢 Números: {numeros} ({numeros/len(texto_corrupto)*100:.1f}%)")
    print(f"      ⚪ Espacios: {espacios} ({espacios/len(texto_corrupto)*100:.1f}%)")
    print(f"      🔣 Símbolos: {simbolos} ({simbolos/len(texto_corrupto)*100:.1f}%)")
    
    # Detectar patrones específicos de corrupción
    patrones_corrupcion = [
        (r'\s[a-zA-Z]\s', "Letras sueltas entre espacios"),
        (r'\d\s[a-zA-Z]\s\d', "Patrón número-letra-número"),
        (r'[^\w\s]{2,}', "Múltiples símbolos consecutivos"),
        (r'\s[+\-*/&%#$@!]{1,2}\s', "Símbolos matemáticos/especiales sueltos"),
        (r'[a-zA-Z]{1}\s[+\-*/&%#$@!]\s', "Letra seguida de símbolo"),
    ]
    
    print(f"\n   🎯 Patrones de corrupción detectados:")
    total_matches = 0
    for patron, descripcion in patrones_corrupcion:
        matches = re.findall(patron, texto_corrupto)
        if matches:
            print(f"      ✅ {descripcion}: {len(matches)} ocurrencias")
            total_matches += len(matches)
        else:
            print(f"      ❌ {descripcion}: 0 ocurrencias")
    
    print(f"   📈 Total de patrones corruptos: {total_matches}")
    
    # Test de limpieza actual
    print(f"\n3️⃣ PASO 3: Test con limpieza actual")
    preprocessor = CommonBlockPreprocessor({'clean_unicode_corruption': True})
    texto_limpio_actual = preprocessor._clean_unicode_corruption(texto_corrupto)
    
    print(f"   📏 Longitud después de limpieza: {len(texto_limpio_actual)} caracteres")
    print(f"   📝 Resultado: {texto_limpio_actual[:200]}..." if len(texto_limpio_actual) > 200 else f"   📝 Resultado: {texto_limpio_actual}")
    
    # Verificar si el texto sigue siendo corrupto
    palabras_reconocibles = len(re.findall(r'\b[a-zA-Z]{3,}\b', texto_limpio_actual))
    print(f"   🔤 Palabras reconocibles (3+ letras): {palabras_reconocibles}")
    
    if palabras_reconocibles < 2 and len(texto_limpio_actual) > 50:
        print(f"   ❌ TEXTO AÚN CORRUPTO: Muy pocas palabras reconocibles")
        es_corrupto = True
    else:
        print(f"   ✅ TEXTO PARECE LIMPIO: Contiene palabras reconocibles")
        es_corrupto = False
    
    # Proponer mejora de limpieza
    print(f"\n4️⃣ PASO 4: Propuesta de limpieza mejorada")
    
    def limpieza_avanzada(texto):
        """Función de limpieza mejorada para texto severamente corrupto"""
        if not texto:
            return texto
        
        # 1. Aplicar limpieza Unicode básica existente
        texto = re.sub(r'\\u[0-9a-fA-F]{4}', ' ', texto)
        texto = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', ' ', texto)
        
        # 2. NUEVA: Detectar texto predominantemente corrupto
        total_chars = len(texto.replace(' ', '').replace('\n', ''))
        if total_chars == 0:
            return ""
        
        # Contar caracteres reconocibles vs corruptos
        letras_validas = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', texto))
        palabras_validas = len(re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]{3,}\b', texto))
        
        # Si menos del 30% son letras válidas y hay menos de 2 palabras, es corrupto
        ratio_letras = letras_validas / total_chars
        if ratio_letras < 0.3 and palabras_validas < 2:
            return "[TEXTO CORRUPTO REMOVIDO]"
        
        # 3. Limpiar patrones específicos de corrupción
        # Remover secuencias de símbolos matemáticos sueltos
        texto = re.sub(r'\s[+\-*/&%#$@!]{1,2}\s', ' ', texto)
        
        # Remover letras sueltas entre espacios (probable corrupción)
        texto = re.sub(r'\s[a-zA-Z]\s', ' ', texto)
        
        # Remover números sueltos de 1-2 dígitos entre espacios
        texto = re.sub(r'\s\d{1,2}\s', ' ', texto)
        
        # 4. Normalizar espacios
        texto = re.sub(r'\s+', ' ', texto)
        texto = re.sub(r'\n\s*\n\s*\n+', '\n\n', texto)
        
        return texto.strip()
    
    # Test de limpieza mejorada
    texto_limpio_mejorado = limpieza_avanzada(texto_corrupto)
    
    print(f"   📏 Longitud con limpieza mejorada: {len(texto_limpio_mejorado)} caracteres")
    print(f"   📝 Resultado mejorado: {texto_limpio_mejorado}")
    
    # Comparar resultados
    print(f"\n5️⃣ PASO 5: Comparación de resultados")
    print(f"   📊 Limpieza actual: {len(texto_limpio_actual)} chars")
    print(f"   📊 Limpieza mejorada: {len(texto_limpio_mejorado)} chars")
    
    if texto_limpio_mejorado == "[TEXTO CORRUPTO REMOVIDO]":
        print(f"   ✅ ÉXITO: Texto corrupto detectado y marcado para remoción")
    elif len(texto_limpio_mejorado) < len(texto_limpio_actual) * 0.5:
        print(f"   ✅ MEJORA: Limpieza más agresiva removió más corrupción")
    else:
        print(f"   ⚠️  SIMILAR: Ambos métodos dieron resultados similares")
    
    return {
        'texto_original': texto_corrupto,
        'limpieza_actual': texto_limpio_actual,
        'limpieza_mejorada': texto_limpio_mejorado,
        'es_corrupto': es_corrupto,
        'total_matches': total_matches
    }

if __name__ == "__main__":
    resultado = analyze_specific_corrupted_text()
    print(f"\n✅ Análisis completado: {resultado['es_corrupto']}") 