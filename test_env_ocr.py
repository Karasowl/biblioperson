#!/usr/bin/env python3
"""
Script para probar la configuración de variables de entorno OCR
"""

import os
from dataset.processing.loaders.ocr_providers import OCRManager

def test_ocr_configuration():
    """Prueba la configuración de OCR y muestra qué proveedores están disponibles"""
    
    print("🔍 PROBANDO CONFIGURACIÓN OCR...")
    print("=" * 50)
    
    # Mostrar variables de entorno relevantes
    ocr_vars = {
        'OCR_PROVIDER': os.environ.get('OCR_PROVIDER', 'No configurado'),
        'TESSERACT_CMD': os.environ.get('TESSERACT_CMD', 'tesseract (default)'),
        'TESSERACT_LANG': os.environ.get('TESSERACT_LANG', 'spa+eng (default)'),
        'GOOGLE_APPLICATION_CREDENTIALS': os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'No configurado'),
        'AWS_ACCESS_KEY_ID': '***' if os.environ.get('AWS_ACCESS_KEY_ID') else 'No configurado',
        'AWS_SECRET_ACCESS_KEY': '***' if os.environ.get('AWS_SECRET_ACCESS_KEY') else 'No configurado',
        'AZURE_VISION_KEY': '***' if os.environ.get('AZURE_VISION_KEY') else 'No configurado',
        'AZURE_VISION_ENDPOINT': os.environ.get('AZURE_VISION_ENDPOINT', 'No configurado'),
        'MAX_OCR_RETRIES': os.environ.get('MAX_OCR_RETRIES', '3 (default)'),
        'ENABLE_OCR_FALLBACK': os.environ.get('ENABLE_OCR_FALLBACK', 'true (default)')
    }
    
    print("📋 VARIABLES DE ENTORNO:")
    for var, value in ocr_vars.items():
        print(f"   {var}: {value}")
    
    print("\n🧪 INICIALIZANDO OCR MANAGER...")
    
    # Probar OCRManager
    try:
        ocr_manager = OCRManager()
        available_providers = ocr_manager.get_available_providers()
        
        print(f"✅ OCRManager inicializado exitosamente")
        print(f"📦 Proveedores disponibles: {len(available_providers)}")
        
        if available_providers:
            print("🎯 PROVEEDORES DETECTADOS:")
            for i, provider in enumerate(available_providers, 1):
                print(f"   {i}. {provider}")
        else:
            print("⚠️  No se detectaron proveedores OCR")
            print("💡 El sistema usará fallback mejorado")
        
        # Mostrar orden de prioridad
        provider_order = os.environ.get('OCR_PROVIDER', 'tesseract,google_vision,aws_textract,azure_vision')
        print(f"\n📋 ORDEN DE PRIORIDAD CONFIGURADO:")
        for i, provider in enumerate(provider_order.split(','), 1):
            status = "✅ Disponible" if provider.strip() in [p.lower().replace(' ', '_') for p in available_providers] else "❌ No disponible"
            print(f"   {i}. {provider.strip()} - {status}")
        
    except Exception as e:
        print(f"❌ Error inicializando OCRManager: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CONFIGURACIÓN COMPLETA")

if __name__ == "__main__":
    # Cargar variables de entorno desde .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Variables .env cargadas")
    except ImportError:
        print("⚠️  python-dotenv no disponible - usando variables del sistema")
    except Exception as e:
        print(f"⚠️  Error cargando .env: {e}")
    
    test_ocr_configuration() 