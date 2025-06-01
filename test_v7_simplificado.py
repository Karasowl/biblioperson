#!/usr/bin/env python3
"""
🚨 TEST V7.0 SIMPLIFICADO 🚨

Prueba específica para verificar que el nuevo algoritmo simple
funciona correctamente y extrae más segmentos que antes.
"""

import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.WARNING)

# Importar componentes directamente
sys.path.append('.')
from dataset.processing.loaders.txt_loader import txtLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor

def test_direct_processing():
    """Probar el procesamiento directo con el nuevo sistema V7.0."""
    
    print("🚨🚨🚨 TEST V7.0 DIRECTO - SIN PROFILE MANAGER 🚨🚨🚨")
    
    # Buscar archivo de prueba
    test_file = "test_prosa.txt"
    if not Path(test_file).exists():
        print(f"❌ Archivo {test_file} no encontrado")
        return
    
    print(f"📄 Procesando {test_file}")
    
    # PASO 1: Cargar con txtLoader
    print("🔄 PASO 1: Cargando archivo...")
    loader = txtLoader(test_file)
    loaded_data = loader.load()
    
    print(f"✅ Cargado: {len(loaded_data.get('blocks', []))} bloques iniciales")
    
    # PASO 2: Procesar con CommonBlockPreprocessor V7.0
    print("🔄 PASO 2: Procesando con CommonBlockPreprocessor V7.0...")
    preprocessor = CommonBlockPreprocessor()
    
    processed_blocks, metadata = preprocessor.process(
        loaded_data.get('blocks', []),
        loaded_data.get('document_metadata', {})
    )
    
    print(f"✅ Procesado: {len(processed_blocks)} bloques finales")
    
    # PASO 3: Mostrar resultados
    print(f"\n🎯 RESULTADOS V7.0:")
    print(f"   📊 Bloques iniciales: {len(loaded_data.get('blocks', []))}")
    print(f"   📊 Bloques finales: {len(processed_blocks)}")
    
    if len(processed_blocks) > 0:
        print(f"\n🔍 PRIMEROS 3 BLOQUES:")
        for i, block in enumerate(processed_blocks[:3]):
            text = block.get('text', '')[:100] + "..." if len(block.get('text', '')) > 100 else block.get('text', '')
            print(f"   [{i+1}] {text}")
    
    # EVALUACIÓN
    if len(processed_blocks) >= 20:
        print(f"\n🎯 ÉXITO: V7.0 extrae {len(processed_blocks)} bloques (excelente granularidad)")
    elif len(processed_blocks) >= 10:
        print(f"\n✅ BUENO: V7.0 extrae {len(processed_blocks)} bloques (buena granularidad)")
    elif len(processed_blocks) >= 3:
        print(f"\n⚠️ MEJORABLE: V7.0 extrae {len(processed_blocks)} bloques")
    else:
        print(f"\n❌ PROBLEMA: Solo {len(processed_blocks)} bloques extraídos")
    
    return processed_blocks

def test_algorithm_comparison():
    """Comparar algoritmo simple vs fallback."""
    
    print("\n🔬 COMPARACIÓN DE ALGORITMOS:")
    
    test_text = """Primer párrafo de ejemplo.
Este es el contenido del primer párrafo.


Segundo párrafo separado por dobles saltos.
Contenido del segundo párrafo.


Tercer párrafo también separado.
Con más contenido aquí."""
    
    preprocessor = CommonBlockPreprocessor()
    
    # Simular bloque de entrada
    test_block = [{'text': test_text, 'metadata': {}}]
    
    processed, _ = preprocessor.process(test_block, {})
    
    print(f"   📝 Texto de entrada: {len(test_text)} caracteres")
    print(f"   🎯 Párrafos extraídos: {len(processed)}")
    
    for i, block in enumerate(processed):
        preview = block.get('text', '')[:50] + "..." if len(block.get('text', '')) > 50 else block.get('text', '')
        print(f"      [{i+1}] {preview}")

if __name__ == "__main__":
    test_direct_processing()
    test_algorithm_comparison() 