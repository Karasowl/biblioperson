"""
🚨 TEST BENEDETTI FIX V7.0 🚨

Prueba el sistema con la configuración corregida del perfil verso
para verificar que detecta poemas correctamente.
"""

import sys
import os
import logging
from pathlib import Path

# Añadir el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent))

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importaciones del sistema
from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter

def test_full_pipeline():
    """Prueba el pipeline completo con configuración corregida"""
    print("🚨🚨🚨 TEST BENEDETTI FIX V7.0 🚨🚨🚨")
    
    # Simular bloques de PDFLoader V7.0 (cada línea como bloque separado)
    # Esto simula lo que debería generar el markdown-first approach
    pdf_blocks = [
        {'text': '"Poema 1"', 'metadata': {'type': 'heading', 'order': 0}},
        {'text': '', 'metadata': {'type': 'paragraph', 'order': 1}},  # Línea vacía
        {'text': 'Este es el primer verso', 'metadata': {'type': 'paragraph', 'order': 2}},
        {'text': 'de un poema de prueba,', 'metadata': {'type': 'paragraph', 'order': 3}},
        {'text': 'que debería ser detectado', 'metadata': {'type': 'paragraph', 'order': 4}},
        {'text': 'por nuestro sistema.', 'metadata': {'type': 'paragraph', 'order': 5}},
        {'text': '', 'metadata': {'type': 'paragraph', 'order': 6}},  # Línea vacía
        {'text': '', 'metadata': {'type': 'paragraph', 'order': 7}},  # Línea vacía
        {'text': '"Poema 2"', 'metadata': {'type': 'heading', 'order': 8}},
        {'text': '', 'metadata': {'type': 'paragraph', 'order': 9}},  # Línea vacía
        {'text': 'Segundo poema aquí,', 'metadata': {'type': 'paragraph', 'order': 10}},
        {'text': 'con versos más cortos,', 'metadata': {'type': 'paragraph', 'order': 11}},
        {'text': 'para verificar', 'metadata': {'type': 'paragraph', 'order': 12}},
        {'text': 'la detección.', 'metadata': {'type': 'paragraph', 'order': 13}},
        {'text': '', 'metadata': {'type': 'paragraph', 'order': 14}},  # Línea vacía
        {'text': '', 'metadata': {'type': 'paragraph', 'order': 15}},  # Línea vacía
        {'text': '"Poema 3 - Más Largo"', 'metadata': {'type': 'heading', 'order': 16}},
        {'text': '', 'metadata': {'type': 'paragraph', 'order': 17}},  # Línea vacía
        {'text': 'Un poema un poco más extenso', 'metadata': {'type': 'paragraph', 'order': 18}},
        {'text': 'que tiene varios versos', 'metadata': {'type': 'paragraph', 'order': 19}},
        {'text': 'y debería ser procesado', 'metadata': {'type': 'paragraph', 'order': 20}},
        {'text': 'correctamente por el sistema', 'metadata': {'type': 'paragraph', 'order': 21}},
        {'text': 'sin importar su longitud', 'metadata': {'type': 'paragraph', 'order': 22}},
        {'text': 'ni la complejidad del contenido.', 'metadata': {'type': 'paragraph', 'order': 23}},
    ]
    
    metadata = {'source': 'test', 'format': 'PDF'}
    
    print(f"📦 DATOS DE ENTRADA: {len(pdf_blocks)} bloques (simulando PDFLoader V7.0)")
    
    # PASO 1: CommonBlockPreprocessor con configuración del perfil verso
    print("\n" + "="*60)
    print("🔧 PASO 1: COMMONBLOCKPREPROCESSOR (PERFIL VERSO)")
    print("="*60)
    
    # Configuración exacta del perfil verso.yaml
    verso_config = {
        'filter_insignificant_blocks': False,
        'min_block_chars_to_keep': 1,
        'aggressive_merge_for_pdfs': False,
        'merge_cross_page_sentences': False,
        'split_blocks_into_paragraphs': False,  # NUEVA CONFIGURACIÓN CLAVE
        'discard_common_pdf_artifacts': False   # CRUCIAL: NO descartar títulos
    }
    
    preprocessor = CommonBlockPreprocessor(verso_config)
    processed_blocks, processed_metadata = preprocessor.process(pdf_blocks, metadata)
    
    print(f"📊 RESULTADO:")
    print(f"   📄 Bloques entrada: {len(pdf_blocks)}")
    print(f"   📄 Bloques salida: {len(processed_blocks)}")
    print(f"   📊 Cambio: {len(pdf_blocks)} → {len(processed_blocks)}")
    
    if processed_blocks:
        print(f"\n🔍 MUESTRA DE BLOQUES PROCESADOS:")
        for i, block in enumerate(processed_blocks[:10]):
            text = block.get('text', '')
            text_preview = repr(text) if len(text) <= 50 else repr(text[:47] + "...")
            print(f"   [{i}] {text_preview}")
    
    # PASO 2: VerseSegmenter
    print("\n" + "="*60)
    print("🎵 PASO 2: VERSESEGMENTER")
    print("="*60)
    
    if not processed_blocks:
        print("❌ No hay bloques para segmentar")
        return
    
    verso_segmenter_config = {
        'thresholds': {
            'min_consecutive_verses': 2,
            'confidence_threshold': 0.3
        }
    }
    
    segmenter = VerseSegmenter(verso_segmenter_config)
    segments = segmenter.segment(processed_blocks)
    
    print(f"📊 RESULTADO:")
    print(f"   📄 Bloques entrada: {len(processed_blocks)}")
    print(f"   🎵 Poemas detectados: {len(segments)}")
    
    if segments:
        print(f"\n✅ POEMAS ENCONTRADOS:")
        for i, segment in enumerate(segments):
            title = segment.get('title', 'Sin título')
            verse_count = segment.get('verse_count', 0)
            content = segment.get('text', '')[:100]
            print(f"   [{i+1}] '{title}' ({verse_count} versos)")
            print(f"       Contenido: {repr(content)}...")
    else:
        print("❌ NO SE ENCONTRARON POEMAS")
        
        # Análisis de por qué falló
        print("\n🔍 ANÁLISIS DE FALLO:")
        
        possible_titles = []
        possible_verses = []
        
        for block in processed_blocks:
            text = block.get('text', '').strip()
            if not text:
                continue
                
            # Detectar títulos potenciales
            if text.startswith('"') and text.endswith('"'):
                possible_titles.append(text)
            elif len(text) < 120 and len(text.split()) > 1:
                possible_verses.append(text)
        
        print(f"   🏷️ Títulos potenciales: {len(possible_titles)}")
        for title in possible_titles:
            print(f"      - {title}")
            
        print(f"   🎵 Versos potenciales: {len(possible_verses)}")
        for verse in possible_verses[:5]:
            print(f"      - {repr(verse)}")
    
    print("\n" + "="*60)
    print("🏁 TEST COMPLETADO")
    print("="*60)
    
    return len(segments) > 0

if __name__ == "__main__":
    success = test_full_pipeline()
    if success:
        print("🎉 ¡ÉXITO! El sistema detectó poemas correctamente")
    else:
        print("❌ FALLO: El sistema no detectó poemas") 