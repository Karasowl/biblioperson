#!/usr/bin/env python3
"""
Debug para PDFs protegidos - Solución para extraer texto de PDFs con protección
"""

import sys
import os
import re
import fitz
from pathlib import Path

def extract_protected_pdf():
    """Extrae texto de PDF protegido usando diferentes estrategias"""
    
    pdf_path = r"C:\Users\adven\Downloads\Mario Benedetti Antologia Poética.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        return
    
    print("🔓 EXTRACCIÓN DE PDF PROTEGIDO/ENCRIPTADO")
    print(f"📄 Archivo: {pdf_path}")
    print("=" * 80)
    
    try:
        doc = fitz.open(pdf_path)
        print(f"✅ PDF abierto: {len(doc)} páginas")
        
        # Verificar si está encriptado
        if doc.needs_pass:
            print("🔒 PDF requiere contraseña")
        else:
            print("🔓 PDF no requiere contraseña explícita")
        
        # Verificar permisos
        if hasattr(doc, 'permissions'):
            print(f"🔑 Permisos: {doc.permissions}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error abriendo PDF: {e}")
        return
    
    # ESTRATEGIA 1: Intentar diferentes passwords comunes
    print("🧪 ESTRATEGIA 1: INTENTAR PASSWORDS COMUNES")
    print("-" * 50)
    
    common_passwords = ["", "password", "123456", "admin", "user", "benedetti", "mario"]
    
    for pwd in common_passwords:
        try:
            if doc.authenticate(pwd):
                print(f"✅ Password encontrado: '{pwd}'")
                break
        except:
            pass
    else:
        print("❌ Ningún password común funcionó")
    
    # ESTRATEGIA 2: Forzar extracción ignorando protección
    print("\n🧪 ESTRATEGIA 2: EXTRACCIÓN FORZADA")
    print("-" * 50)
    
    # Intentar con páginas específicas
    successful_pages = []
    total_text = ""
    
    for page_num in range(min(10, len(doc))):  # Primeras 10 páginas
        page = doc[page_num]
        
        # Método 1: Texto básico
        try:
            text = page.get_text()
            if text and not all(ord(c) < 32 for c in text if c != '\n'):  # No solo caracteres de control
                successful_pages.append(page_num)
                total_text += text
                print(f"✅ Página {page_num}: {len(text)} chars - {text[:50].replace(chr(10), ' ')}")
            else:
                print(f"❌ Página {page_num}: Solo caracteres de control")
        except Exception as e:
            print(f"❌ Página {page_num}: Error - {e}")
    
    print(f"\n📊 Páginas exitosas: {len(successful_pages)}")
    print(f"📝 Texto total extraído: {len(total_text)} caracteres")
    
    # ESTRATEGIA 3: Extracción de imágenes para OCR
    print("\n🧪 ESTRATEGIA 3: EXTRACCIÓN DE IMÁGENES (para OCR)")
    print("-" * 50)
    
    page = doc[1]  # Segunda página (más probabilidad de contenido)
    try:
        # Renderizar página como imagen
        mat = fitz.Matrix(2.0, 2.0)  # Zoom 2x para mejor calidad
        pix = page.get_pixmap(matrix=mat)
        
        print(f"✅ Imagen generada: {pix.width}x{pix.height} píxeles")
        
        # Guardar imagen temporalmente para inspección
        temp_image = "temp_page_benedetti.png"
        pix.save(temp_image)
        print(f"💾 Imagen guardada como: {temp_image}")
        
        # Intentar OCR básico si tesseract está disponible
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(temp_image)
            ocr_text = pytesseract.image_to_string(img, lang='spa')
            
            if ocr_text and len(ocr_text.strip()) > 50:
                print(f"✅ OCR exitoso: {len(ocr_text)} caracteres")
                print(f"📖 Texto OCR: {ocr_text[:200]}")
                
                # Buscar títulos de poemas
                lines = ocr_text.split('\n')
                potential_titles = []
                for line in lines:
                    line = line.strip()
                    if line and len(line) < 100 and not line.endswith('.'):
                        potential_titles.append(line)
                
                print(f"🎭 Posibles títulos encontrados: {len(potential_titles)}")
                for i, title in enumerate(potential_titles[:10]):
                    print(f"  {i+1}. {title}")
                    
            else:
                print("❌ OCR no produjo texto útil")
                
        except ImportError:
            print("⚠️ Tesseract no disponible para OCR")
        except Exception as e:
            print(f"❌ Error en OCR: {e}")
        
        # Limpiar archivo temporal
        if os.path.exists(temp_image):
            os.remove(temp_image)
            
    except Exception as e:
        print(f"❌ Error generando imagen: {e}")
    
    # ESTRATEGIA 4: Análisis de metadata
    print("\n🧪 ESTRATEGIA 4: ANÁLISIS DE METADATA")
    print("-" * 50)
    
    try:
        metadata = doc.metadata
        for key, value in metadata.items():
            if value:
                print(f"📋 {key}: {value}")
                
        # Buscar información sobre protección
        if 'creator' in metadata:
            print(f"🔧 Creador: {metadata['creator']}")
        if 'producer' in metadata:
            print(f"🏭 Productor: {metadata['producer']}")
            
    except Exception as e:
        print(f"❌ Error leyendo metadata: {e}")
    
    doc.close()
    
    print("\n" + "=" * 80)
    print("🏁 ANÁLISIS DE PDF PROTEGIDO COMPLETADO")
    print("\n💡 RECOMENDACIONES:")
    
    if successful_pages:
        print("✅ El PDF tiene texto extraíble en algunas páginas")
        print("🔧 Modificar PDFLoader para manejar protección específica")
    else:
        print("❌ PDF totalmente protegido")
        print("🔧 Necesario OCR o herramientas de desprotección")
        print("📖 Considera usar una versión no protegida del PDF")

if __name__ == "__main__":
    extract_protected_pdf() 