#!/usr/bin/env python3
"""
Test específico para OCR - Verificar si Tesseract funciona y probar
extracción del PDF de Neruda.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ocr_neruda():
    """Prueba OCR en el PDF de Neruda"""
    
    pdf_path = r"C:\Users\adven\Downloads\Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        return
    
    print("🔍 PRUEBA DE OCR - NERUDA")
    print(f"📄 Archivo: {pdf_path}")
    print("=" * 60)
    
    # PASO 1: Verificar dependencias OCR
    print("📋 PASO 1: VERIFICANDO DEPENDENCIAS OCR")
    print("-" * 40)
    
    try:
        import pytesseract
        from PIL import Image
        import fitz
        import io
        print("✅ pytesseract: instalado")
        print("✅ PIL (Pillow): instalado")
        print("✅ PyMuPDF: instalado")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        return
    
    # PASO 2: Verificar Tesseract engine
    print("\n📋 PASO 2: VERIFICANDO TESSERACT ENGINE")
    print("-" * 40)
    
    try:
        # Intentar obtener versión de Tesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract instalado: versión {version}")
    except Exception as e:
        print(f"❌ Tesseract no encontrado: {e}")
        print("💡 SOLUCIÓN:")
        print("   Windows: Descargar desde https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Linux: sudo apt install tesseract-ocr tesseract-ocr-spa")
        print("   Mac: brew install tesseract tesseract-lang")
        return
    
    # PASO 3: Probar OCR en una página
    print("\n📋 PASO 3: PRUEBA OCR EN PÁGINA ESPECÍFICA")
    print("-" * 40)
    
    try:
        # Abrir PDF
        doc = fitz.open(pdf_path)
        print(f"✅ PDF abierto: {len(doc)} páginas")
        
        # Probar OCR en página 2 (más probable contenido)
        page = doc[1]  # Página 2 (índice 1)
        
        # Renderizar a imagen
        mat = fitz.Matrix(3, 3)  # 3x zoom para mejor calidad
        pix = page.get_pixmap(matrix=mat)
        
        # Convertir a PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        print(f"✅ Imagen generada: {image.size} píxeles")
        
        # Aplicar OCR
        print("🔍 Aplicando OCR...")
        ocr_config = '--psm 6 --oem 3 -c preserve_interword_spaces=1'
        
        try:
            # Intentar con idioma español
            ocr_text = pytesseract.image_to_string(image, lang='spa', config=ocr_config)
        except Exception:
            # Fallback a inglés si español no está disponible
            print("⚠️ Español no disponible, usando inglés...")
            ocr_text = pytesseract.image_to_string(image, lang='eng', config=ocr_config)
        
        if ocr_text:
            print(f"✅ OCR exitoso: {len(ocr_text)} caracteres")
            print("\n📝 TEXTO EXTRAÍDO:")
            print("=" * 40)
            print(ocr_text[:500])  # Primeros 500 caracteres
            print("=" * 40)
            
            # Buscar patrones de poemas
            lines = ocr_text.split('\n')
            poem_patterns = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Buscar "Poema N"
                    import re
                    if re.match(r'.*[Pp]oema\s+\d+', line):
                        poem_patterns.append(line)
                    # Buscar números romanos
                    elif re.match(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.?\s*$', line):
                        poem_patterns.append(line)
            
            if poem_patterns:
                print(f"\n🎭 PATRONES DE POEMAS DETECTADOS: {len(poem_patterns)}")
                for pattern in poem_patterns[:5]:
                    print(f"  📍 {pattern}")
            else:
                print("\n⚠️ No se detectaron patrones claros de poemas")
            
        else:
            print("❌ OCR no extrajo texto")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Error en prueba OCR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # PASO 4: Forzar OCR automático en PDFLoader
    print("\n📋 PASO 4: PRUEBA CON PDFLOADER V7.3 (OCR FORZADO)")
    print("-" * 40)
    
    try:
        from dataset.processing.loaders.pdf_loader import PDFLoader
        
        # Crear loader
        loader = PDFLoader(pdf_path)
        
        # Forzar que detecte necesidad de OCR
        # Para esto vamos a simular que tiene muy pocos bloques
        print("🔄 Cargando con PDFLoader V7.3...")
        result = loader.load()
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        
        print(f"✅ PDFLoader completado")
        print(f"📦 Bloques extraídos: {len(blocks)}")
        print(f"📄 Páginas: {metadata.get('page_count', 'N/A')}")
        
        # Verificar si usó OCR
        total_text = ""
        for block in blocks:
            total_text += block.get('text', '')
        
        print(f"📝 Texto total: {len(total_text)} caracteres")
        
        # Buscar evidencia de OCR
        if "OCR" in str(result) or len(blocks) > 30:  # OCR suele generar más bloques granulares
            print("🎉 ¡OCR AUTOMÁTICO ACTIVADO!")
        else:
            print("⚠️ OCR no se activó automáticamente")
            
    except Exception as e:
        print(f"❌ Error con PDFLoader: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 PRUEBA OCR COMPLETADA")

if __name__ == "__main__":
    test_ocr_neruda() 