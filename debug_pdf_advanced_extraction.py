#!/usr/bin/env python3
"""
Extracción avanzada para PDFs protegidos - Implementa métodos para acceder
al contenido real de PDFs con protección/encriptación.
"""

import sys
import os
import re
import fitz
from pathlib import Path

def advanced_pdf_extraction():
    """Métodos avanzados para extraer texto de PDFs protegidos"""
    
    pdf_path = r"C:\Users\adven\Downloads\Mario Benedetti Antologia Poética.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        return
    
    print("🔓 EXTRACCIÓN AVANZADA DE PDF PROTEGIDO")
    print(f"📄 Archivo: {pdf_path}")
    print("=" * 80)
    
    # ESTRATEGIA 1: Forzar autenticación con passwords vacíos y comunes
    print("🧪 ESTRATEGIA 1: AUTENTICACIÓN FORZADA")
    print("-" * 50)
    
    try:
        doc = fitz.open(pdf_path)
        print(f"✅ PDF abierto: {len(doc)} páginas")
        
        # Verificar estado de protección
        print(f"🔒 Necesita password: {doc.needs_pass}")
        print(f"🔑 Permisos: {doc.permissions}")
        print(f"🔐 Encriptado: {doc.is_encrypted}")
        
        # Intentar autenticaciones
        auth_attempts = [
            ("", "Password vacío"),
            ("owner", "Owner"),
            ("user", "User"), 
            ("password", "Password genérico"),
            ("benedetti", "Autor"),
            ("mario", "Nombre autor"),
            ("1944", "Año nacimiento"),
            ("2009", "Año fallecimiento"),
            ("poesia", "Temática"),
            ("uruguay", "País"),
        ]
        
        authenticated = False
        for pwd, desc in auth_attempts:
            try:
                if doc.authenticate(pwd):
                    print(f"✅ AUTENTICACIÓN EXITOSA con '{pwd}' ({desc})")
                    authenticated = True
                    break
            except Exception as e:
                print(f"❌ Error autenticando con '{pwd}': {e}")
        
        if not authenticated:
            print("⚠️ No se logró autenticación - continuando con métodos alternativos")
        
    except Exception as e:
        print(f"❌ Error abriendo PDF: {e}")
        return
    
    # ESTRATEGIA 2: Extracción por páginas específicas con diferentes métodos
    print("\n🧪 ESTRATEGIA 2: EXTRACCIÓN SELECTIVA POR PÁGINAS")
    print("-" * 50)
    
    successful_extractions = []
    
    # Probar páginas específicas (poemas suelen estar en el medio)
    test_pages = [50, 100, 150, 10, 20, 30]  # Páginas de prueba
    
    for page_num in test_pages:
        if page_num >= len(doc):
            continue
            
        page = doc[page_num]
        print(f"\n📄 Analizando página {page_num}:")
        
        # Método 1: get_text() básico
        try:
            text_basic = page.get_text()
            if text_basic and len(text_basic.strip()) > 100:
                # Verificar si contiene texto legible (español)
                readable_chars = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', text_basic))
                if readable_chars > len(text_basic) * 0.3:  # 30% caracteres legibles
                    print(f"  ✅ Texto básico legible: {len(text_basic)} chars")
                    successful_extractions.append(('basic', page_num, text_basic[:500]))
                else:
                    print(f"  ❌ Texto básico corrupto: {readable_chars}/{len(text_basic)} legibles")
            else:
                print(f"  ❌ Texto básico vacío o muy corto")
        except Exception as e:
            print(f"  ❌ Error texto básico: {e}")
        
        # Método 2: get_text("blocks")
        try:
            blocks = page.get_text("blocks")
            all_block_text = ""
            for block in blocks:
                if len(block) >= 5:
                    block_text = str(block[4])
                    all_block_text += block_text + " "
            
            if all_block_text and len(all_block_text.strip()) > 100:
                readable_chars = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', all_block_text))
                if readable_chars > len(all_block_text) * 0.3:
                    print(f"  ✅ Bloques legibles: {len(all_block_text)} chars")
                    successful_extractions.append(('blocks', page_num, all_block_text[:500]))
                else:
                    print(f"  ❌ Bloques corruptos: {readable_chars}/{len(all_block_text)} legibles")
            else:
                print(f"  ❌ Bloques vacíos")
        except Exception as e:
            print(f"  ❌ Error bloques: {e}")
        
        # Método 3: get_text("dict") con análisis de fonts
        try:
            page_dict = page.get_text("dict")
            dict_text = ""
            font_info = {}
            
            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        font = span.get("font", "unknown")
                        size = span.get("size", 0)
                        
                        dict_text += text + " "
                        
                        # Recopilar información de fuentes
                        if font not in font_info:
                            font_info[font] = {"size": size, "count": 0}
                        font_info[font]["count"] += 1
            
            if dict_text and len(dict_text.strip()) > 100:
                readable_chars = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', dict_text))
                if readable_chars > len(dict_text) * 0.3:
                    print(f"  ✅ Dict legible: {len(dict_text)} chars")
                    print(f"    🔤 Fuentes detectadas: {len(font_info)}")
                    successful_extractions.append(('dict', page_num, dict_text[:500]))
                else:
                    print(f"  ❌ Dict corrupto: {readable_chars}/{len(dict_text)} legibles")
            else:
                print(f"  ❌ Dict vacío")
        except Exception as e:
            print(f"  ❌ Error dict: {e}")
    
    # ESTRATEGIA 3: OCR como método de respaldo
    print("\n🧪 ESTRATEGIA 3: OCR DE RESPALDO")
    print("-" * 50)
    
    if successful_extractions:
        print("✅ Se encontró texto legible - OCR no necesario")
    else:
        print("🔍 No hay texto legible - intentando OCR")
        
        try:
            import pytesseract
            from PIL import Image
            import io
            
            # OCR en página central (más probabilidad de contenido)
            middle_page = len(doc) // 2
            page = doc[middle_page]
            
            # Renderizar a alta resolución
            mat = fitz.Matrix(3, 3)  # 3x zoom
            pix = page.get_pixmap(matrix=mat)
            
            # Convertir a imagen PIL
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # OCR con español
            ocr_text = pytesseract.image_to_string(image, lang='spa', config='--psm 6')
            
            if ocr_text and len(ocr_text.strip()) > 200:
                print(f"✅ OCR exitoso: {len(ocr_text)} caracteres")
                print(f"📖 Preview OCR: {ocr_text[:300]}")
                
                # Buscar títulos de poemas en OCR
                lines = ocr_text.split('\n')
                potential_poems = []
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line and len(line) < 100:
                        # Buscar patrones típicos de títulos de poemas
                        if (line.isupper() and len(line) < 50) or \
                           (len(line.split()) <= 5 and not line.endswith('.')):
                            potential_poems.append(line)
                
                if potential_poems:
                    print(f"🎭 Posibles títulos de poemas encontrados: {len(potential_poems)}")
                    for i, title in enumerate(potential_poems[:10]):
                        print(f"  {i+1}. {title}")
                else:
                    print("❌ No se detectaron títulos de poemas en OCR")
                    
            else:
                print(f"❌ OCR sin resultados útiles: {len(ocr_text) if ocr_text else 0} chars")
                
        except ImportError:
            print("⚠️ OCR no disponible - instalar 'pip install pytesseract pillow'")
        except Exception as e:
            print(f"❌ Error en OCR: {e}")
    
    doc.close()
    
    # RESUMEN Y RECOMENDACIONES
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE EXTRACCIÓN AVANZADA")
    print("=" * 80)
    
    if successful_extractions:
        print(f"✅ EXTRACCIÓN EXITOSA: {len(successful_extractions)} métodos funcionaron")
        
        print("\n🔍 TEXTO EXTRAÍDO:")
        for method, page_num, text_sample in successful_extractions[:3]:  # Primeros 3
            print(f"\n📄 Página {page_num} (método: {method}):")
            print(f"📝 {text_sample}")
            
        print("\n💡 RECOMENDACIONES:")
        print("1. ✅ El PDF SÍ tiene contenido extraíble")
        print("2. 🔧 Modificar PDFLoader para usar el método exitoso")
        print("3. 📄 Usar páginas específicas que funcionaron")
        
        # Identificar el mejor método
        method_counts = {}
        for method, _, _ in successful_extractions:
            method_counts[method] = method_counts.get(method, 0) + 1
        
        best_method = max(method_counts, key=method_counts.get)
        print(f"4. 🎯 Mejor método detectado: '{best_method}' ({method_counts[best_method]} páginas exitosas)")
        
    else:
        print("❌ EXTRACCIÓN FALLIDA: Ningún método funcionó")
        print("\n💡 RECOMENDACIONES:")
        print("1. 🔒 El PDF está fuertemente protegido")
        print("2. 📄 Buscar una versión no protegida del documento")
        print("3. 🔧 Considerar herramientas de desprotección externas")
        print("4. 📱 Probar extracción manual de páginas específicas")

if __name__ == "__main__":
    advanced_pdf_extraction() 