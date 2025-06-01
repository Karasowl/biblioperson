#!/usr/bin/env python3
"""
DEBUG MARKDOWN LOADER BLOQUES
=============================

Debuggear específicamente cómo el MarkdownPDFLoader está 
convirtiendo el markdown crudo a bloques y por qué se 
pierden los saltos de línea en el proceso.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.loaders.markdown_pdf_loader import MarkdownPDFLoader
    import pymupdf4llm
    
    def debug_markdown_loader_blocks():
        """Debug del proceso de conversión markdown → bloques"""
        
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            return False
        
        print("🔍 DEBUG MARKDOWN LOADER BLOQUES")
        print("=" * 50)
        
        # PASO 1: Obtener markdown crudo
        print("\n1️⃣ OBTENIENDO MARKDOWN CRUDO:")
        print("-" * 40)
        
        raw_markdown = pymupdf4llm.to_markdown(test_file)
        
        # Encontrar el Poema 13 en el markdown crudo
        lines = raw_markdown.split('\n')
        poema_13_start = None
        poema_13_end = None
        
        for i, line in enumerate(lines):
            if 'Poema 13' in line and poema_13_start is None:
                poema_13_start = i
            elif poema_13_start is not None and 'Poema 14' in line:
                poema_13_end = i
                break
        
        if poema_13_start is None:
            print("❌ No se encontró Poema 13 en markdown crudo")
            return False
        
        if poema_13_end is None:
            poema_13_end = min(poema_13_start + 30, len(lines))
        
        print(f"📍 Poema 13 encontrado: líneas {poema_13_start} a {poema_13_end}")
        print(f"Líneas del Poema 13 en markdown crudo:")
        
        poema_13_raw_lines = lines[poema_13_start:poema_13_end]
        for i, line in enumerate(poema_13_raw_lines[:10]):  # Primeras 10 líneas
            print(f"   {poema_13_start + i:3d}: {repr(line)}")
        
        # PASO 2: Procesar con MarkdownPDFLoader
        print(f"\n2️⃣ PROCESANDO CON MARKDOWNPDFLOADER:")
        print("-" * 40)
        
        loader = MarkdownPDFLoader(test_file)
        result = loader.load()
        blocks = result.get('blocks', [])
        
        print(f"📊 Bloques generados: {len(blocks)}")
        
        # Buscar bloques que contengan Poema 13
        poema_13_blocks = []
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            if 'Poema 13' in text or 'He ido marcando' in text:
                poema_13_blocks.append((i, block))
        
        print(f"📄 Bloques relacionados con Poema 13: {len(poema_13_blocks)}")
        
        for i, (block_idx, block) in enumerate(poema_13_blocks):
            print(f"\nBloque {block_idx} (relacionado {i+1}):")
            print(f"   Tipo: {block.get('metadata', {}).get('type', 'unknown')}")
            text = block.get('text', '')
            print(f"   Longitud: {len(text)} caracteres")
            print(f"   Saltos de línea: {text.count(chr(10))}")
            print(f"   Texto (primeros 200 chars): {repr(text[:200])}")
            
            # Mostrar estructura completa si es pequeño
            if len(text) < 500:
                print(f"   Texto completo:")
                lines_in_block = text.split('\n')
                for j, line in enumerate(lines_in_block[:15]):  # Primeras 15 líneas
                    print(f"      {j+1:2d}: {repr(line)}")
        
        # PASO 3: Análisis del problema
        print(f"\n3️⃣ ANÁLISIS DEL PROBLEMA:")
        print("-" * 40)
        
        # Comparar entrada vs salida para Poema 13
        raw_poema_13 = '\n'.join(poema_13_raw_lines)
        
        # Buscar el bloque procesado más relevante
        processed_poema_13 = None
        for _, block in poema_13_blocks:
            text = block.get('text', '')
            if 'He ido marcando' in text:
                processed_poema_13 = text
                break
        
        if processed_poema_13:
            print(f"📊 Comparación entrada vs salida:")
            print(f"   RAW - Saltos de línea: {raw_poema_13.count(chr(10))}")
            print(f"   RAW - Longitud: {len(raw_poema_13)}")
            print(f"   PROCESADO - Saltos de línea: {processed_poema_13.count(chr(10))}")
            print(f"   PROCESADO - Longitud: {len(processed_poema_13)}")
            
            # Verificar dónde se perdieron los saltos
            raw_lines = [line.strip() for line in raw_poema_13.split('\n') if line.strip()]
            processed_lines = [line.strip() for line in processed_poema_13.split('\n') if line.strip()]
            
            print(f"   RAW - Líneas de contenido: {len(raw_lines)}")
            print(f"   PROCESADO - Líneas de contenido: {len(processed_lines)}")
            
            # Mostrar diferencias específicas
            print(f"\n🔍 DIFERENCIAS DETECTADAS:")
            if len(raw_lines) != len(processed_lines):
                print(f"   ❌ Diferente número de líneas: {len(raw_lines)} → {len(processed_lines)}")
            
            # Comparar primeras líneas
            print(f"   Comparación línea por línea (primeras 8):")
            for i in range(min(8, len(raw_lines), len(processed_lines))):
                raw_line = raw_lines[i] if i < len(raw_lines) else "[FALTANTE]"
                proc_line = processed_lines[i] if i < len(processed_lines) else "[FALTANTE]"
                
                if raw_line == proc_line:
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"      {status} {i+1}: RAW: {repr(raw_line[:50])}")
                print(f"         PROC: {repr(proc_line[:50])}")
        
        # PASO 4: Identificar el punto exacto del problema
        print(f"\n4️⃣ IDENTIFICANDO PUNTO DEL PROBLEMA:")
        print("-" * 40)
        
        # Verificar si el problema está en _markdown_to_blocks
        print(f"🔧 Analizando función _markdown_to_blocks...")
        
        # Verificar si las líneas individuales se están uniendo incorrectamente
        sample_lines = poema_13_raw_lines[1:6]  # Excluir título
        print(f"Líneas de entrada al procesador:")
        for i, line in enumerate(sample_lines):
            print(f"   {i+1}: {repr(line)}")
        
        # Simular el procesamiento
        print(f"Procesamiento esperado:")
        for i, line in enumerate(sample_lines):
            if line.strip():
                print(f"   → Bloque {i+1}: {repr(line)}")
        
        return True
    
    if __name__ == "__main__":
        print("🧪 DEBUG MARKDOWN LOADER BLOQUES")
        print("=" * 50)
        
        debug_markdown_loader_blocks()
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("⚠️ Asegúrate de ejecutar desde el directorio raíz del proyecto") 