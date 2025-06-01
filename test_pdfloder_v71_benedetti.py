"""
🚨 TEST PDLOADER V7.1 BENEDETTI 🚨

Prueba el PDFLoader V7.1 mejorado con limpieza anti-corrupción
en el PDF real de Mario Benedetti.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent))

# Configurar logging detallado
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Forzar recarga del PDFLoader
import importlib
try:
    import dataset.processing.loaders.pdf_loader
    importlib.reload(dataset.processing.loaders.pdf_loader)
    print("✅ PDFLoader recargado")
except Exception as e:
    print(f"⚠️ Error recargando PDFLoader: {e}")

from dataset.processing.loaders.pdf_loader import PDFLoader

def test_pdf_loader_v71():
    """Prueba PDFLoader V7.1 con PDF real de Benedetti"""
    print("🚨🚨🚨 TEST PDLOADER V7.1 - ANTI-CORRUPCIÓN 🚨🚨🚨")
    
    # Buscar el PDF de Mario Benedetti
    possible_paths = [
        "C:/Users/adven/Downloads/Mario Benedetti Antologia Poética.pdf",
        "Mario Benedetti Antologia Poética.pdf",
        "benedetti.pdf",
    ]
    
    pdf_path = None
    for path in possible_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print("❌ No se encontró el PDF de Mario Benedetti")
        return False
    
    print(f"📁 PDF encontrado: {pdf_path}")
    
    try:
        # Inicializar PDFLoader V7.1
        loader = PDFLoader(pdf_path)
        result = loader.load()
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        
        print(f"\n📦 RESULTADO PDFLoader V7.1:")
        print(f"   📄 Bloques extraídos: {len(blocks)}")
        print(f"   📊 Metadatos: {len(metadata)} campos")
        
        if blocks:
            print(f"\n🔍 ANÁLISIS DE BLOQUES EXTRAÍDOS:")
            
            total_chars = 0
            readable_blocks = 0
            potential_titles = 0
            potential_verses = 0
            
            for i, block in enumerate(blocks[:20]):  # Primeros 20 bloques
                text = block.get('text', '').strip()
                if not text:
                    continue
                
                total_chars += len(text)
                
                # Analizar si es legible
                import re
                readable_chars = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡()"\'-]', text))
                if readable_chars / len(text) > 0.8:  # Más del 80% legible
                    readable_blocks += 1
                    
                    # Buscar títulos potenciales
                    if (text.startswith('"') and text.endswith('"')) or text.isupper():
                        potential_titles += 1
                        print(f"   🏷️ TÍTULO POTENCIAL [{i}]: {repr(text)}")
                    
                    # Buscar versos potenciales
                    elif len(text.split('\n')) > 1 and len(text) < 200:
                        potential_verses += 1
                        if potential_verses <= 3:  # Solo mostrar primeros 3
                            print(f"   🎵 VERSO POTENCIAL [{i}]: {repr(text[:100])}")
                
                # Mostrar todos los bloques para debug (primeros 10)
                if i < 10:
                    text_preview = repr(text[:80]) if text else "''"
                    print(f"   [{i}] {text_preview}")
            
            print(f"\n📊 ESTADÍSTICAS DE CALIDAD:")
            print(f"   📝 Total caracteres: {total_chars}")
            print(f"   ✅ Bloques legibles: {readable_blocks}/{len(blocks[:20])}")
            print(f"   🏷️ Títulos potenciales: {potential_titles}")
            print(f"   🎵 Versos potenciales: {potential_verses}")
            
            # Calcular ratio de éxito
            if readable_blocks > 0:
                print(f"\n🎉 ¡MEJORA DETECTADA! PDFLoader V7.1 extrajo texto legible")
                return True
            else:
                print(f"\n❌ PDF sigue siendo ilegible después de limpieza")
                return False
                
        else:
            print("❌ NO SE EXTRAJERON BLOQUES")
            return False
            
    except Exception as e:
        print(f"❌ ERROR en PDFLoader V7.1: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    success = test_pdf_loader_v71()
    
    print("\n" + "="*60)
    print("🏁 RESUMEN")
    print("="*60)
    
    if success:
        print("✅ PDFLoader V7.1 funcionó correctamente")
        print("🎯 El PDF ahora debería funcionar con el perfil verso")
    else:
        print("❌ PDFLoader V7.1 no pudo limpiar el PDF corrupto")
        print("🔧 Puede que necesitemos métodos de extracción aún más avanzados")

if __name__ == "__main__":
    main() 