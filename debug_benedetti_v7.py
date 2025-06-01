"""
🚨 DEBUG MARIO BENEDETTI V7.0 🚨

Script para diagnosticar por qué no se encuentran segmentos
en la Antología Poética de Mario Benedetti.

Prueba cada componente del pipeline paso a paso.
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

# Importaciones del sistema
from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def test_pdf_loader(pdf_path: str):
    """Prueba el PDFLoader V7.0 directamente"""
    print("\n" + "="*60)
    print("🔍 PROBANDO PDLOADER V7.0")
    print("="*60)
    
    try:
        loader = PDFLoader(pdf_path)
        result = loader.load()
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        
        print(f"📦 RESULTADO PDFLoader:")
        print(f"   📄 Bloques extraídos: {len(blocks)}")
        print(f"   📊 Metadatos: {len(metadata)} campos")
        
        if blocks:
            print(f"\n🔍 MUESTRA DE BLOQUES:")
            for i, block in enumerate(blocks[:5]):  # Primeros 5 bloques
                text = block.get('text', '')[:100]
                block_type = block.get('metadata', {}).get('type', 'unknown')
                print(f"   [{i}] {block_type}: {repr(text)}")
                
            print(f"\n📏 ESTADÍSTICAS DE TEXTO:")
            total_chars = sum(len(block.get('text', '')) for block in blocks)
            print(f"   📝 Total caracteres: {total_chars}")
            print(f"   📊 Promedio por bloque: {total_chars / len(blocks):.1f}")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR en PDFLoader: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_preprocessor(blocks, metadata):
    """Prueba el CommonBlockPreprocessor V7.0"""
    print("\n" + "="*60)
    print("🔧 PROBANDO COMMONBLOCKPREPROCESSOR V7.0")
    print("="*60)
    
    if not blocks:
        print("❌ No hay bloques para procesar")
        return None, None
    
    try:
        # Configuración del perfil verso (muy permisiva)
        config = {
            'filter_insignificant_blocks': False,
            'min_block_chars_to_keep': 1,
            'aggressive_merge_for_pdfs': False,
            'merge_cross_page_sentences': False
        }
        
        preprocessor = CommonBlockPreprocessor(config)
        processed_blocks, processed_metadata = preprocessor.process(blocks, metadata)
        
        print(f"📦 RESULTADO Preprocessor:")
        print(f"   📄 Bloques entrada: {len(blocks)}")
        print(f"   📄 Bloques salida: {len(processed_blocks)}")
        print(f"   📊 Cambio: {len(blocks)} → {len(processed_blocks)}")
        
        if processed_blocks:
            print(f"\n🔍 MUESTRA DE BLOQUES PROCESADOS:")
            for i, block in enumerate(processed_blocks[:5]):
                text = block.get('text', '')[:100]
                metadata_info = block.get('metadata', {})
                order = metadata_info.get('order', 'N/A')
                block_type = metadata_info.get('type', 'unknown')
                print(f"   [{i}] orden={order}, tipo={block_type}: {repr(text)}")
        
        return processed_blocks, processed_metadata
        
    except Exception as e:
        print(f"❌ ERROR en Preprocessor: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_verse_segmenter(blocks):
    """Prueba el VerseSegmenter"""
    print("\n" + "="*60)
    print("🎵 PROBANDO VERSESEGMENTER")
    print("="*60)
    
    if not blocks:
        print("❌ No hay bloques para segmentar")
        return None
    
    try:
        # Configuración del perfil verso
        config = {
            'thresholds': {
                'min_consecutive_verses': 2,
                'confidence_threshold': 0.3
            }
        }
        
        segmenter = VerseSegmenter(config)
        segments = segmenter.segment(blocks)
        
        print(f"📦 RESULTADO VerseSegmenter:")
        print(f"   📄 Bloques entrada: {len(blocks)}")
        print(f"   🎵 Segmentos poemas: {len(segments)}")
        
        if segments:
            print(f"\n🔍 SEGMENTOS ENCONTRADOS:")
            for i, segment in enumerate(segments[:3]):  # Primeros 3 segmentos
                content = segment.get('content', '')[:200]
                title = segment.get('title', 'Sin título')
                verse_count = segment.get('metadata', {}).get('verse_count', 0)
                print(f"   [{i}] '{title}' ({verse_count} versos): {repr(content)}")
        else:
            print("⚠️ NO SE ENCONTRARON SEGMENTOS")
            print("🔍 Analizando por qué...")
            
            # Análisis de por qué no se detectaron versos
            verse_blocks = []
            title_blocks = []
            other_blocks = []
            
            for block in blocks:
                text = block.get('text', '').strip()
                if not text:
                    continue
                    
                # Simular detección de título
                if ('"' in text or text.isupper() or 
                    any(keyword in text.lower() for keyword in ['poema', 'verso', 'canción'])):
                    title_blocks.append(text[:50])
                elif len(text.split('\n')) > 1 and len(text) < 200:
                    verse_blocks.append(text[:50])
                else:
                    other_blocks.append(text[:50])
            
            print(f"   🏷️ Posibles títulos: {len(title_blocks)}")
            print(f"   🎵 Posibles versos: {len(verse_blocks)}")
            print(f"   📄 Otros bloques: {len(other_blocks)}")
            
            if title_blocks:
                print("   🏷️ Ejemplos de títulos:")
                for title in title_blocks[:3]:
                    print(f"      - {repr(title)}")
                    
            if verse_blocks:
                print("   🎵 Ejemplos de versos:")
                for verse in verse_blocks[:3]:
                    print(f"      - {repr(verse)}")
        
        return segments
        
    except Exception as e:
        print(f"❌ ERROR en VerseSegmenter: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Función principal de debug"""
    print("🚨🚨🚨 DEBUG MARIO BENEDETTI V7.0 🚨🚨🚨")
    
    # Usar un PDF de prueba primero
    test_pdf = "test_prosa.txt"  # Cambiaremos esto por el PDF real si está disponible
    
    print(f"📁 Archivo de prueba: {test_pdf}")
    
    if not os.path.exists(test_pdf):
        print(f"❌ Archivo {test_pdf} no encontrado")
        print("🔧 Creando archivo de prueba con contenido poético...")
        
        # Crear archivo de prueba con poemas
        test_content = '''
"Poema 1"

Este es el primer verso
de un poema de prueba,
que debería ser detectado
por nuestro sistema.

"Poema 2"

Segundo poema aquí,
con versos más cortos,
para verificar
la detección.

"Poema 3 - Más Largo"

Un poema un poco más extenso
que tiene varios versos
y debería ser procesado
correctamente por el sistema
sin importar su longitud
ni la complejidad del contenido.
'''
        
        with open(test_pdf, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print("✅ Archivo de prueba creado")
    
    # Simular que es un PDF usando el txtLoader
    print("📝 Nota: Usando txtLoader para simular contenido...")
    
    # Para esta prueba, crearemos bloques manualmente
    test_blocks = [
        {'text': '"Poema 1"', 'metadata': {'type': 'heading', 'order': 0}},
        {'text': 'Este es el primer verso\nde un poema de prueba,\nque debería ser detectado\npor nuestro sistema.', 'metadata': {'type': 'paragraph', 'order': 1}},
        {'text': '"Poema 2"', 'metadata': {'type': 'heading', 'order': 2}},
        {'text': 'Segundo poema aquí,\ncon versos más cortos,\npara verificar\nla detección.', 'metadata': {'type': 'paragraph', 'order': 3}},
        {'text': '"Poema 3 - Más Largo"', 'metadata': {'type': 'heading', 'order': 4}},
        {'text': 'Un poema un poco más extenso\nque tiene varios versos\ny debería ser procesado\ncorrectamente por el sistema\nsin importar su longitud\nni la complejidad del contenido.', 'metadata': {'type': 'paragraph', 'order': 5}},
    ]
    
    test_metadata = {'source': 'test', 'format': 'test'}
    
    print(f"🧪 USANDO DATOS DE PRUEBA: {len(test_blocks)} bloques")
    
    # Probar cada componente
    print("\n🔍 INICIANDO PRUEBAS PASO A PASO...")
    
    # 1. Saltar PDFLoader por ahora, usar datos de prueba
    print("⏭️ Saltando PDFLoader, usando datos de prueba")
    
    # 2. Probar Preprocessor
    processed_blocks, processed_metadata = test_preprocessor(test_blocks, test_metadata)
    
    # 3. Probar VerseSegmenter
    if processed_blocks:
        segments = test_verse_segmenter(processed_blocks)
        
        if segments:
            print(f"\n✅ ÉXITO: {len(segments)} segmentos detectados")
        else:
            print(f"\n❌ FALLO: No se detectaron segmentos")
    
    print("\n" + "="*60)
    print("🏁 DEBUG COMPLETADO")
    print("="*60)

if __name__ == "__main__":
    main() 