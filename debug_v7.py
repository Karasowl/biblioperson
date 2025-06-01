#!/usr/bin/env python3
import sys
sys.path.append('.')

from dataset.processing.loaders.txt_loader import txtLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor

# Cargar archivo
print("🔄 Cargando archivo...")
loader = txtLoader('test_prosa.txt')
data = loader.load()
print(f"✅ Bloques cargados: {len(data.get('blocks', []))}")

# Mostrar bloques cargados
for i, block in enumerate(data.get('blocks', [])):
    text = block.get('text', '')[:100] + "..." if len(block.get('text', '')) > 100 else block.get('text', '')
    print(f"  Bloque {i+1}: {text}")

# Procesar
print("\n🔄 Procesando...")
preprocessor = CommonBlockPreprocessor()
processed, _ = preprocessor.process(data.get('blocks', []), {})
print(f"✅ Bloques procesados: {len(processed)}")

# Mostrar bloques procesados
for i, block in enumerate(processed):
    text = block.get('text', '')[:100] + "..." if len(block.get('text', '')) > 100 else block.get('text', '')
    print(f"  Procesado {i+1}: {text}") 