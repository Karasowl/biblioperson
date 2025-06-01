#!/usr/bin/env python3
"""
Test de compatibilidad del PDFLoader V7.4 con ProfileManager
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dataset.processing.loaders.pdf_loader import PDFLoader

def test_profile_manager_compatibility():
    """Simula la llamada del ProfileManager al PDFLoader"""
    
    pdf_path = r"C:\Users\adven\Downloads\Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        print("📝 Ajusta la ruta según tu sistema")
        return
    
    print("🔧 VERIFICANDO COMPATIBILIDAD PDFLOADER V7.4 CON PROFILEMANAGER")
    print("=" * 80)
    
    # Simular las diferentes formas en que ProfileManager puede llamar al constructor
    
    # 1. Como lo hace ProfileManager actualmente: PDFLoader(file_path, **{'encoding': 'utf-8'})
    print("📋 PRUEBA 1: ProfileManager actual - PDFLoader(file_path, **{'encoding': 'utf-8'})")
    try:
        loader_kwargs = {'encoding': 'utf-8'}
        loader1 = PDFLoader(pdf_path, **loader_kwargs)
        print(f"✅ Constructor exitoso")
        print(f"   📝 Encoding: {loader1.encoding}")
        print(f"   📝 Tipo: {loader1.tipo}")
        
        # Probar load rápido
        result1 = loader1.load()
        blocks1 = result1.get('blocks', [])
        print(f"✅ Load exitoso: {len(blocks1)} bloques")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return
    
    # 2. Constructor directo con argumentos posicionales
    print("📋 PRUEBA 2: Constructor directo - PDFLoader(file_path, 'poemas', 'utf-8')")
    try:
        loader2 = PDFLoader(pdf_path, 'poemas', 'utf-8')
        print(f"✅ Constructor exitoso")
        print(f"   📝 Encoding: {loader2.encoding}")
        print(f"   📝 Tipo: {loader2.tipo}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return
    
    # 3. Constructor solo con file_path
    print("📋 PRUEBA 3: Constructor mínimo - PDFLoader(file_path)")
    try:
        loader3 = PDFLoader(pdf_path)
        print(f"✅ Constructor exitoso")
        print(f"   📝 Encoding: {loader3.encoding}")
        print(f"   📝 Tipo: {loader3.tipo}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return
    
    # 4. Constructor con argumentos keyword mezclados
    print("📋 PRUEBA 4: Constructor completo - PDFLoader(file_path, tipo='verso', encoding='latin-1')")
    try:
        loader4 = PDFLoader(pdf_path, tipo='verso', encoding='latin-1')
        print(f"✅ Constructor exitoso")
        print(f"   📝 Encoding: {loader4.encoding}")
        print(f"   📝 Tipo: {loader4.tipo}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return
    
    print("🎯 ANÁLISIS DEL PRIMER RESULTADO:")
    print(f"   📦 Bloques generados: {len(blocks1)}")
    
    metadata = result1.get('metadata', {})
    source_info = result1.get('source_info', {})
    
    print(f"   📄 Páginas: {metadata.get('page_count', 'N/A')}")
    print(f"   📊 Caracteres: {source_info.get('total_chars', 'N/A')}")
    print(f"   🔍 Corrupción: {source_info.get('corruption_percentage', 'N/A')}%")
    print(f"   🤖 Usa OCR: {source_info.get('uses_ocr', 'N/A')}")
    print(f"   📋 Método: {source_info.get('extraction_method', 'N/A')}")
    
    # Mostrar algunos bloques de ejemplo
    print(f"\n🔍 PRIMEROS 3 BLOQUES:")
    for i, block in enumerate(blocks1[:3]):
        text = block.get('text', '')
        print(f"   📄 Bloque {i+1}: {len(text)} chars - {repr(text[:100])}...")
    
    print("\n" + "=" * 80)
    print("✅ TODAS LAS PRUEBAS DE COMPATIBILIDAD EXITOSAS")
    print("🎯 PDFLoader V7.4 es totalmente compatible con ProfileManager")

if __name__ == "__main__":
    test_profile_manager_compatibility() 