"""
🚨 TEST PDLOADER V7.1 CON OCR - BENEDETTI 🚨

Prueba el PDFLoader V7.1 con OCR en el PDF corrupto de Mario Benedetti.
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

# Forzar recarga completa del PDFLoader
import importlib
try:
    import dataset.processing.loaders.pdf_loader
    importlib.reload(dataset.processing.loaders.pdf_loader)
    print("✅ PDFLoader V7.1 con OCR recargado")
except Exception as e:
    print(f"⚠️ Error recargando PDFLoader: {e}")

from dataset.processing.loaders.pdf_loader import PDFLoader

def test_pdf_loader_v71_ocr():
    """Prueba PDFLoader V7.1 con OCR"""
    print("🚨🚨🚨 TEST PDLOADER V7.1 + OCR - MARIO BENEDETTI 🚨🚨🚨")
    
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
    print("🔍 Nota: Este test puede tomar varios minutos debido al OCR...")
    
    try:
        # Inicializar PDFLoader V7.1 con OCR
        loader = PDFLoader(pdf_path)
        result = loader.load()
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        
        print(f"\n📦 RESULTADO PDFLoader V7.1 + OCR:")
        print(f"   📄 Bloques extraídos: {len(blocks)}")
        print(f"   📊 Metadatos: {len(metadata)} campos")
        
        if not blocks:
            print("❌ NO SE EXTRAJERON BLOQUES")
            return False
        
        # Análisis de calidad del texto extraído
        print(f"\n🔍 ANÁLISIS DE CALIDAD:")
        
        total_chars = 0
        readable_blocks = 0
        potential_titles = 0
        potential_verses = 0
        poem_indicators = 0
        
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            if not text:
                continue
            
            total_chars += len(text)
            
            # Analizar legibilidad
            import re
            readable_chars = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡()"\'-]', text))
            legibility_ratio = readable_chars / len(text) if len(text) > 0 else 0
            
            if legibility_ratio > 0.8:  # Más del 80% legible
                readable_blocks += 1
                
                # Buscar indicadores de poesía
                poetry_keywords = ['poema', 'verso', 'estrofa', 'rima', 'mario', 'benedetti']
                if any(keyword in text.lower() for keyword in poetry_keywords):
                    poem_indicators += 1
                
                # Buscar títulos potenciales (entre comillas, mayúsculas, cortos)
                if ((text.startswith('"') and text.endswith('"')) or 
                    text.isupper() or 
                    (len(text) < 50 and not text.endswith('.'))):
                    potential_titles += 1
                    if potential_titles <= 5:  # Solo mostrar primeros 5
                        print(f"   🏷️ TÍTULO POTENCIAL: {repr(text)}")
                
                # Buscar versos potenciales (múltiples líneas, longitud media)
                elif '\n' in text and 50 < len(text) < 300:
                    potential_verses += 1
                    if potential_verses <= 3:  # Solo mostrar primeros 3
                        preview = text.replace('\n', ' | ')[:100]
                        print(f"   🎵 VERSO POTENCIAL: {repr(preview)}")
            
            # Mostrar progreso cada 20 bloques
            if i % 20 == 0 and i > 0:
                print(f"   📊 Procesados {i} bloques...")
        
        print(f"\n📊 ESTADÍSTICAS FINALES:")
        print(f"   📝 Total caracteres: {total_chars:,}")
        print(f"   ✅ Bloques legibles: {readable_blocks}/{len(blocks)}")
        print(f"   🎭 Indicadores de poesía: {poem_indicators}")
        print(f"   🏷️ Títulos potenciales: {potential_titles}")
        print(f"   🎵 Versos potenciales: {potential_verses}")
        
        # Calcular ratio de éxito
        success_score = 0
        if total_chars > 1000:  # Al menos 1K caracteres
            success_score += 1
        if readable_blocks > 10:  # Al menos 10 bloques legibles
            success_score += 1
        if poem_indicators > 0:  # Hay indicadores de poesía
            success_score += 1
        if potential_titles > 0:  # Hay títulos potenciales
            success_score += 1
        
        print(f"\n🎯 PUNTUACIÓN DE ÉXITO: {success_score}/4")
        
        if success_score >= 2:
            print("🎉 ¡ÉXITO! PDFLoader V7.1 + OCR extrajo contenido útil")
            print("✅ El PDF ahora debería funcionar con el perfil verso")
            return True
        else:
            print("❌ El PDF sigue siendo problemático")
            print("💡 Puede necesitar limpieza manual o es un formato muy específico")
            return False
            
    except Exception as e:
        print(f"❌ ERROR en PDFLoader V7.1 + OCR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    success = test_pdf_loader_v71_ocr()
    
    print("\n" + "="*60)
    print("🏁 RESUMEN FINAL")
    print("="*60)
    
    if success:
        print("✅ PDFLoader V7.1 + OCR funcionó correctamente")
        print("🎯 Ahora puedes probar con la GUI de nuevo")
        print("💡 El sistema debería detectar poemas de Mario Benedetti")
    else:
        print("❌ PDFLoader V7.1 + OCR no pudo extraer contenido útil")
        print("🔧 Recomendaciones:")
        print("   - Verificar que el PDF no esté encriptado")
        print("   - Intentar con un PDF diferente de Mario Benedetti")
        print("   - Considerar conversión manual del PDF")

if __name__ == "__main__":
    main() 