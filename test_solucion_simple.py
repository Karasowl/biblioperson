#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la solución simple del usuario: dividir por 3+ espacios consecutivos
"""
import re

def solucion_simple_usuario(texto):
    """
    SOLUCIÓN SIMPLE DEL USUARIO: dividir por 3+ espacios consecutivos
    """
    print(f"💡 APLICANDO SOLUCIÓN SIMPLE: dividir por 3+ espacios")
    
    # Dividir por 3 o más espacios/saltos de línea consecutivos
    parrafos = re.split(r'[\s]{3,}', texto)
    
    # Limpiar y filtrar
    parrafos_limpios = []
    for parrafo in parrafos:
        limpio = parrafo.strip()
        if len(limpio) >= 15:  # Mínimo 15 caracteres
            parrafos_limpios.append(limpio)
    
    print(f"💡 Resultado: {len(parrafos_limpios)} párrafos")
    return parrafos_limpios

def main():
    print("=== PRUEBA DE SOLUCIÓN SIMPLE ===")
    
    # Texto de ejemplo que simula el problema del PDF
    texto_problema = """Los políticos no populistas no utilizan discursos enardecedores para hablar solamente por una


facción (aunque hay quienes lo hacen: al menos en Europa, los nombres de algunos partidos suelen


indicar que éstos sólo se proponen representar a una clientela específica, como a los pequeños


productores agrícolas o a los cristianos).   


En cambio, los populistas persisten en su postulado de representación moral sin importarles nada más.


Esto es lo que hace que el populismo sea una forma particular de hacer política democrática."""

    print("📝 TEXTO ORIGINAL:")
    print(repr(texto_problema))
    print()
    
    print("🔄 APLICANDO SOLUCIÓN SIMPLE...")
    resultado = solucion_simple_usuario(texto_problema)
    
    print("\n📋 RESULTADO:")
    for i, parrafo in enumerate(resultado, 1):
        print(f"  {i}. {parrafo[:80]}..." if len(parrafo) > 80 else f"  {i}. {parrafo}")
        print(f"     📏 Longitud: {len(parrafo)} caracteres")
    
    # Verificar que el problema se resolvió
    if any("facción" in p and "clientela" in p for p in resultado):
        print("\n✅ ÉXITO: La oración cortada se mantuvo junta")
    else:
        print("\n❌ ERROR: La oración sigue cortada")

if __name__ == "__main__":
    main() 