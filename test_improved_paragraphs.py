#!/usr/bin/env python3
"""
Script para probar las mejoras del PDFLoader con heurísticas anti-salto de página
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset.processing.loaders.pdf_loader import PDFLoader

def test_improved_paragraphs():
    """Prueba las heurísticas mejoradas del PDFLoader"""
    
    # Archivo de prueba
    pdf_path = r"C:\Users\adven\OneDrive\Escritorio\probando biblioperson\Recopilación de Escritos Propios\escritos\Biblioteca virtual\¿Qué es el populismo_ - Jan-Werner Müller.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ Archivo no encontrado:", pdf_path)
        return
        
    print("🔧 PROBANDO PDLOADER MEJORADO...")
    print(f"📄 Archivo: {os.path.basename(pdf_path)}")
    print("=" * 80)
    
    # Crear PDFLoader y cargar
    loader = PDFLoader(pdf_path)
    
    # Probar casos específicos de las heurísticas
    test_cases = [
        # Caso problemático identificado
        ["Uno tendría que ser muy necio para no ver el atractivo", "de esta idea de cómo dominar colectivamente el propio destino"],
        # Otros casos típicos
        ["La democracia moderna se basa en principios", "de representación y participación ciudadana"],
        ["El texto termina con punto.", "Nueva oración que empieza con mayúscula"],
        ["Línea sin puntuación final", "que continúa en la siguiente línea"],
        ["- Lista con guión", "que no debería unirse"],
        ["Final con coma,", "y continúa la frase normalmente"]
    ]
    
    print("🧪 CASOS DE PRUEBA:")
    print("-" * 40)
    
    for i, (line1, line2) in enumerate(test_cases):
        print(f"\n🔹 CASO {i+1}:")
        print(f"   Línea 1: '{line1}'")
        print(f"   Línea 2: '{line2}'")
        
        # Probar heurística individual
        should_break = loader._is_paragraph_break(line1, line2)
        action = "DIVIDIR" if should_break else "UNIR"
        emoji = "✂️" if should_break else "🔗"
        
        print(f"   {emoji} Decisión: {action}")
        
        # Probar reconstrucción completa
        reconstructed = loader._reconstruct_paragraphs([line1, line2])
        paragraphs = reconstructed.split('\n\n')
        
        print(f"   📄 Resultado ({len(paragraphs)} párrafo/s):")
        for j, paragraph in enumerate(paragraphs):
            print(f"      [{j}] {paragraph}")
    
    print("\n" + "=" * 80)
    print("🏗️ PROBANDO CON ARCHIVO REAL...")
    print("-" * 40)
    
    # Cargar el archivo real
    try:
        result = loader.load()
        blocks = result.get('blocks', [])
        
        print(f"✅ Cargado exitosamente: {len(blocks)} bloques")
        
        # Buscar bloques que contengan el patrón problemático
        target_phrases = ['atractivo', 'necio para no ver', 'de esta idea']
        
        for phrase in target_phrases:
            print(f"\n🔍 Buscando bloques con '{phrase}':")
            found_count = 0
            
            for i, block in enumerate(blocks):
                text = block.get('text', '')
                if phrase.lower() in text.lower():
                    found_count += 1
                    # Mostrar contexto del bloque
                    preview = text[:150] + "..." if len(text) > 150 else text
                    print(f"   Bloque {i}: {repr(preview)}")
                    
                    if found_count >= 3:  # Limitar a 3 ejemplos
                        break
            
            if found_count == 0:
                print(f"   ❌ No encontrado")
    
    except Exception as e:
        print(f"❌ Error cargando archivo: {e}")

if __name__ == "__main__":
    test_improved_paragraphs() 