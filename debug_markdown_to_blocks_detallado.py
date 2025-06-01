#!/usr/bin/env python3
"""
DEBUG MARKDOWN TO BLOCKS DETALLADO
==================================

Trace ultra-detallado de la función _markdown_to_blocks
para entender por qué solo detecta el primer verso del Poema 13.
"""

import sys
import os
import re
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import pymupdf4llm
    
    def debug_markdown_to_blocks_detailed():
        """Debug ultra-detallado del procesamiento línea por línea"""
        
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            return False
        
        print("🔍 DEBUG MARKDOWN TO BLOCKS DETALLADO")
        print("=" * 60)
        
        # PASO 1: Obtener markdown crudo
        raw_markdown = pymupdf4llm.to_markdown(test_file)
        lines = raw_markdown.split('\n')
        
        # Encontrar el Poema 13
        poema_13_start = None
        for i, line in enumerate(lines):
            if 'Poema 13' in line and poema_13_start is None:
                poema_13_start = i
                break
        
        if poema_13_start is None:
            print("❌ No se encontró Poema 13")
            return False
        
        # Tomar las líneas del Poema 13 (título + versos + hasta encontrar el siguiente)
        poema_13_lines = []
        for i in range(poema_13_start, min(poema_13_start + 30, len(lines))):
            line = lines[i]
            # Parar si encontramos el siguiente poema
            if i > poema_13_start and ('Poema 14' in line or 'Poema' in line and line.strip() != lines[poema_13_start].strip()):
                break
            poema_13_lines.append(line)
        
        print(f"📍 Poema 13 líneas extraídas: {len(poema_13_lines)}")
        print("Líneas del Poema 13:")
        for i, line in enumerate(poema_13_lines[:15]):  # Primeras 15
            print(f"   {i:2d}: {repr(line)}")
        
        # PASO 2: Simular la función _markdown_to_blocks con debug
        print(f"\n2️⃣ SIMULANDO _markdown_to_blocks LÍNEA POR LÍNEA:")
        print("-" * 60)
        
        blocks = []
        current_section = None
        current_content = []
        block_id = 0
        
        # Funciones auxiliares (copiadas del MarkdownPDFLoader)
        def is_poem_title(line):
            line = line.strip()
            if not line or len(line) > 100:
                return False
            
            patterns = [
                r'^Poema\s+\d+',
                r'^[IVX]+\.?\s*$',
                r'^\d+\.?\s*$',
                r'.*[Cc]anción.*',
                r'^[A-Z][A-Z\s]{10,50}$',
            ]
            
            for pattern in patterns:
                if re.match(pattern, line):
                    return True
            
            if (len(line) < 60 and 
                not line.endswith('.') and 
                not line.endswith(',') and
                (line.isupper() or line.istitle())):
                return True
            
            return False
        
        def looks_like_verse_line(line):
            line = line.strip()
            
            if not line or len(line) < 5 or len(line) > 150:
                return False
            
            non_verse_patterns = [
                r'^Página\s+\d+',
                r'^#',
                r'^\d+\s*$',
                r'^[IVX]+\s*$',
            ]
            
            for pattern in non_verse_patterns:
                if re.match(pattern, line):
                    return False
            
            title_patterns = [
                r'^Poema\s+\d+',
                r'^[A-Z][A-Z\s]{5,}$',
                r'^".*"$',
            ]
            
            for pattern in title_patterns:
                if re.match(pattern, line):
                    return False
            
            return True
        
        def create_block(block_id, section, content, block_type):
            if content:
                text_content = '\n'.join(content).strip()
            else:
                text_content = section
            
            return {
                'id': block_id,
                'text': text_content,
                'metadata': {
                    'type': block_type,
                    'section': section,
                }
            }
        
        # PROCESAMIENTO LÍNEA POR LÍNEA
        for line_num, line in enumerate(poema_13_lines):
            line_rstrip = line.rstrip()
            
            print(f"\n📝 Línea {line_num}: {repr(line_rstrip)}")
            print(f"   Longitud: {len(line_rstrip.strip())} chars")
            
            # DETECTAR TÍTULOS PRINCIPALES
            if line_rstrip.startswith('# '):
                print(f"   → TÍTULO PRINCIPAL detectado")
                if current_section and current_content:
                    new_block = create_block(block_id, current_section, current_content, 'section')
                    blocks.append(new_block)
                    print(f"   → Bloque {block_id} creado (section): {repr(new_block['text'][:50])}")
                    block_id += 1
                
                current_section = line_rstrip[2:].strip()
                current_content = []
                
                new_block = create_block(block_id, line_rstrip[2:].strip(), [], 'title')
                blocks.append(new_block)
                print(f"   → Bloque {block_id} creado (title): {repr(new_block['text'])}")
                block_id += 1
                
            # DETECTAR SUBTÍTULOS (POEMAS)
            elif line_rstrip.startswith('## '):
                print(f"   → SUBTÍTULO detectado")
                if current_content:
                    new_block = create_block(block_id, current_section or 'unknown', current_content, 'content')
                    blocks.append(new_block)
                    print(f"   → Bloque {block_id} creado (content): {repr(new_block['text'][:50])}")
                    block_id += 1
                    current_content = []
                
                poem_title = line_rstrip[3:].strip()
                new_block = create_block(block_id, poem_title, [], 'poem_title')
                blocks.append(new_block)
                print(f"   → Bloque {block_id} creado (poem_title): {repr(new_block['text'])}")
                block_id += 1
                
            # DETECTAR OTROS PATRONES DE TÍTULOS
            elif is_poem_title(line_rstrip):
                print(f"   → TÍTULO DE POEMA detectado")
                if current_content:
                    new_block = create_block(block_id, current_section or 'unknown', current_content, 'content')
                    blocks.append(new_block)
                    print(f"   → Bloque {block_id} creado (content): {repr(new_block['text'][:50])}")
                    block_id += 1
                    current_content = []
                
                new_block = create_block(block_id, line_rstrip.strip(), [], 'poem_title')
                blocks.append(new_block)
                print(f"   → Bloque {block_id} creado (poem_title): {repr(new_block['text'])}")
                block_id += 1
                
            # CONTENIDO REGULAR
            elif line_rstrip.strip():
                print(f"   → CONTENIDO REGULAR")
                
                # Verificar si es verso
                is_verse = looks_like_verse_line(line_rstrip)
                print(f"   → ¿Es verso? {is_verse}")
                
                if is_verse:
                    print(f"   → VERSO DETECTADO - Creando bloque individual")
                    
                    # Guardar contenido anterior si existe
                    if current_content:
                        new_block = create_block(block_id, current_section or 'unknown', current_content, 'content')
                        blocks.append(new_block)
                        print(f"   → Bloque {block_id} creado (content prev): {repr(new_block['text'][:50])}")
                        block_id += 1
                        current_content = []
                    
                    # Crear bloque individual para el verso
                    new_block = create_block(block_id, current_section or 'unknown', [line_rstrip], 'verse')
                    blocks.append(new_block)
                    print(f"   → Bloque {block_id} creado (verse): {repr(new_block['text'])}")
                    block_id += 1
                else:
                    print(f"   → NO es verso - Agregando a current_content")
                    current_content.append(line_rstrip)
                    print(f"   → current_content ahora tiene {len(current_content)} líneas")
                    
            # LÍNEA VACÍA
            else:
                print(f"   → LÍNEA VACÍA")
                if current_content and line_num + 1 < len(poema_13_lines):
                    next_line = poema_13_lines[line_num + 1].strip()
                    should_save = (next_line.startswith('#') or 
                                 is_poem_title(next_line) or 
                                 len(current_content) > 5)
                    print(f"   → ¿Guardar current_content? {should_save}")
                    print(f"   → Siguiente línea: {repr(next_line)}")
                    
                    if should_save:
                        new_block = create_block(block_id, current_section or 'unknown', current_content, 'content')
                        blocks.append(new_block)
                        print(f"   → Bloque {block_id} creado (content): {repr(new_block['text'][:50])}")
                        block_id += 1
                        current_content = []
        
        # Guardar último bloque
        if current_content:
            new_block = create_block(block_id, current_section or 'unknown', current_content, 'content')
            blocks.append(new_block)
            print(f"   → Bloque FINAL {block_id} creado (content): {repr(new_block['text'][:50])}")
        
        # PASO 3: Analizar resultados
        print(f"\n3️⃣ RESULTADOS DEL PROCESAMIENTO:")
        print("-" * 60)
        print(f"📊 Bloques totales creados: {len(blocks)}")
        
        verse_blocks = [b for b in blocks if b['metadata']['type'] == 'verse']
        poem_title_blocks = [b for b in blocks if b['metadata']['type'] == 'poem_title']
        
        print(f"📄 Bloques de tipo 'verse': {len(verse_blocks)}")
        print(f"📄 Bloques de tipo 'poem_title': {len(poem_title_blocks)}")
        
        print(f"\nBloques creados:")
        for i, block in enumerate(blocks):
            block_type = block['metadata']['type']
            text = block['text']
            print(f"   {i:2d}: [{block_type}] {repr(text[:60])}")
        
        # PASO 4: Conclusión
        print(f"\n4️⃣ DIAGNÓSTICO:")
        print("-" * 60)
        
        if len(verse_blocks) == 1:
            print("❌ PROBLEMA CONFIRMADO: Solo se detectó 1 verso")
            print("   Posibles causas:")
            print("   1. La función looks_like_verse_line() es demasiado restrictiva")
            print("   2. Hay un problema de flujo en el algoritmo")
            print("   3. Las líneas posteriores no se están procesando correctamente")
        else:
            print(f"✅ CORRECCIÓN EXITOSA: Se detectaron {len(verse_blocks)} versos")
        
        return True
    
    if __name__ == "__main__":
        print("🧪 DEBUG MARKDOWN TO BLOCKS DETALLADO")
        print("=" * 60)
        
        debug_markdown_to_blocks_detailed()
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("⚠️ Asegúrate de ejecutar desde el directorio raíz del proyecto") 