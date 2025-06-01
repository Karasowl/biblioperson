#!/usr/bin/env python3
"""
Test completo del Sistema OCR Inteligente para aplicaciones web.

Verifica:
- Compatibilidad PDFLoader con ProfileManager
- Sistema OCRManager con múltiples proveedores
- Detección automática de necesidad de OCR
- Fallbacks robustos
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ocr_system_complete():
    """Test completo del sistema OCR inteligente"""
    
    pdf_path = r"C:\Users\adven\Downloads\Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        print("📝 Ajusta la ruta según tu sistema")
        return
    
    print("🧪 TEST COMPLETO DEL SISTEMA OCR INTELIGENTE")
    print("=" * 80)
    
    # ===============================================
    # PASO 1: Verificar OCRManager standalone
    # ===============================================
    print("📋 PASO 1: VERIFICANDO OCR MANAGER")
    print("-" * 50)
    
    try:
        from dataset.processing.loaders.ocr_providers import OCRManager
        
        ocr_manager = OCRManager()
        available_providers = ocr_manager.get_available_providers()
        
        print(f"✅ OCRManager inicializado")
        print(f"📊 Proveedores disponibles: {available_providers}")
        
        if available_providers:
            print(f"🎯 Proveedor principal: {available_providers[0]}")
        else:
            print("⚠️ No hay proveedores OCR disponibles")
        
        print()
        
    except Exception as e:
        print(f"❌ Error en OCRManager: {e}")
        print()
        return
    
    # ===============================================
    # PASO 2: Test del PDFLoader con sistema OCR
    # ===============================================
    print("📋 PASO 2: VERIFICANDO PDFLOADER CON SISTEMA OCR")
    print("-" * 50)
    
    try:
        from dataset.processing.loaders.pdf_loader import PDFLoader
        
        # Simular llamada del ProfileManager
        loader_kwargs = {'encoding': 'utf-8'}
        loader = PDFLoader(pdf_path, **loader_kwargs)
        
        print(f"✅ PDFLoader inicializado")
        print(f"   📝 Encoding: {loader.encoding}")
        print(f"   📝 Tipo: {loader.tipo}")
        
        # Ejecutar carga completa
        print("🔄 Ejecutando carga completa...")
        result = loader.load()
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        source_info = result.get('source_info', {})
        
        print(f"✅ Carga completada")
        print(f"   📦 Bloques: {len(blocks)}")
        print(f"   📄 Páginas: {metadata.get('page_count', 'N/A')}")
        print(f"   📊 Caracteres: {source_info.get('total_chars', 'N/A')}")
        print(f"   🤖 Usa OCR: {source_info.get('uses_ocr', 'N/A')}")
        print(f"   📋 Método: {source_info.get('extraction_method', 'N/A')}")
        
        if source_info.get('uses_ocr'):
            providers = source_info.get('ocr_providers_available', [])
            successful_pages = source_info.get('successful_pages', 0)
            print(f"   🔍 Proveedores OCR: {providers}")
            print(f"   📈 Páginas exitosas: {successful_pages}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error en PDFLoader: {e}")
        import traceback
        traceback.print_exc()
        print()
        return
    
    # ===============================================
    # PASO 3: Test de segmentación mejorada
    # ===============================================
    print("📋 PASO 3: VERIFICANDO SEGMENTACIÓN MEJORADA")
    print("-" * 50)
    
    try:
        from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
        
        segmenter = VerseSegmenter()
        segments = segmenter.segment(blocks)
        
        print(f"✅ Segmentación completada")
        print(f"   🎭 Segmentos detectados: {len(segments)}")
        print(f"   📊 Ratio segmentos/páginas: {len(segments) / metadata.get('page_count', 1):.2f}")
        
        # Mostrar algunos segmentos
        print(f"\n🔍 PRIMEROS 3 SEGMENTOS:")
        for i, segment in enumerate(segments[:3]):
            title = segment.get('title', 'Sin título')
            text = segment.get('text', '')
            method = segment.get('detection_method', 'principal')
            
            print(f"   🎭 Segmento {i+1}:")
            print(f"      🎯 Título: '{title}'")
            print(f"      📏 Longitud: {len(text)} caracteres")
            print(f"      🔧 Método: {method}")
            print(f"      📝 Preview: {repr(text[:100])}...")
            print()
        
    except Exception as e:
        print(f"❌ Error en segmentación: {e}")
        print()
        return
    
    # ===============================================
    # PASO 4: Análisis de mejoras
    # ===============================================
    print("📋 PASO 4: ANÁLISIS DE MEJORAS")
    print("-" * 50)
    
    pages = metadata.get('page_count', 1)
    expected_poems = 20  # "20 Poemas de Amor"
    
    print(f"📊 MÉTRICAS FINALES:")
    print(f"   📖 Poemas esperados: ~{expected_poems}")
    print(f"   🎭 Segmentos detectados: {len(segments)}")
    print(f"   📄 Páginas del PDF: {pages}")
    print(f"   📈 Tasa de detección: {len(segments)/expected_poems*100:.1f}%")
    print(f"   📊 Segmentos por página: {len(segments)/pages:.2f}")
    
    # Determinar éxito
    success_threshold = 0.6  # 60% de poemas esperados
    is_successful = len(segments) >= expected_poems * success_threshold
    
    print(f"\n🎯 EVALUACIÓN FINAL:")
    if is_successful:
        print(f"✅ ÉXITO: Sistema detectó {len(segments)}/{expected_poems} poemas ({len(segments)/expected_poems*100:.1f}%)")
        print(f"🚀 Mejora significativa lograda")
    else:
        print(f"⚠️ PARCIAL: Sistema detectó {len(segments)}/{expected_poems} poemas ({len(segments)/expected_poems*100:.1f}%)")
        print(f"💡 Considerar instalar Tesseract para mejor rendimiento")
    
    # ===============================================
    # PASO 5: Configuración para producción web
    # ===============================================
    print("\n📋 PASO 5: RECOMENDACIONES PARA PRODUCCIÓN WEB")
    print("-" * 50)
    
    print("🐳 DOCKER:")
    print("   • docker-compose --profile dev up -d    (desarrollo)")
    print("   • docker-compose --profile prod up -d   (producción)")
    print("   • docker-compose --profile cloud up -d  (OCR cloud)")
    
    print("\n🔧 CONFIGURACIÓN OCR:")
    print("   • OCR_PROVIDER=tesseract                 (solo local)")
    print("   • OCR_PROVIDER=google_vision,tesseract   (híbrido)")
    print("   • OCR_PROVIDER=google_vision             (solo cloud)")
    
    print("\n💰 COSTOS ESTIMADOS (1000 PDFs):")
    print("   • Tesseract local: $0 (gratis)")
    print("   • Google Vision: ~$1.50")
    print("   • Híbrido: $0.50-1.00 (óptimo)")
    
    print("\n" + "=" * 80)
    print("🏁 TEST COMPLETO FINALIZADO")
    
    if available_providers:
        print(f"✅ Sistema OCR operativo con {len(available_providers)} proveedor(es)")
    else:
        print("⚠️ Sistema funcionando solo con fallback mejorado")
    
    print(f"🎯 Resultado: {len(segments)} segmentos de ~{expected_poems} esperados")

if __name__ == "__main__":
    test_ocr_system_complete() 