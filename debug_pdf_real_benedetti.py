"""
🚨 DEBUG PDF REAL MARIO BENEDETTI 🚨

Script para diagnosticar por qué el PDF real de Mario Benedetti
sigue reportando "No se encontraron segmentos" a pesar de nuestras correcciones.
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

# Forzar la recarga de los módulos para asegurar versiones actualizadas
import importlib
try:
    import dataset.processing.pre_processors.common_block_preprocessor
    importlib.reload(dataset.processing.pre_processors.common_block_preprocessor)
    print("✅ CommonBlockPreprocessor recargado")
except Exception as e:
    print(f"⚠️ Error recargando CommonBlockPreprocessor: {e}")

from dataset.processing.loaders.pdf_loader import PDFLoader
from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
from dataset.processing.segmenters.verse_segmenter import VerseSegmenter
from dataset.processing.profile_manager import ProfileManager

def test_pdf_real():
    """Prueba con el PDF real de Mario Benedetti"""
    print("🚨🚨🚨 DEBUG PDF REAL MARIO BENEDETTI 🚨🚨🚨")
    
    # Buscar el PDF de Mario Benedetti
    possible_paths = [
        "C:/Users/adven/Downloads/Mario Benedetti Antologia Poética.pdf",
        "Mario Benedetti Antologia Poética.pdf",
        "benedetti.pdf",
        # Añadir más rutas posibles aquí
    ]
    
    pdf_path = None
    for path in possible_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print("❌ No se encontró el PDF de Mario Benedetti")
        print("📁 Rutas probadas:")
        for path in possible_paths:
            print(f"   - {path}")
        return False
    
    print(f"📁 PDF encontrado: {pdf_path}")
    
    # PASO 1: Probar PDFLoader V7.0 con el archivo real
    print("\n" + "="*60)
    print("🔍 PASO 1: PROBANDO PDLOADER V7.0 CON PDF REAL")
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
            print(f"\n🔍 PRIMEROS 10 BLOQUES REALES:")
            for i, block in enumerate(blocks[:10]):
                text = block.get('text', '')
                block_type = block.get('metadata', {}).get('type', 'unknown')
                text_preview = repr(text[:80]) if text else "''"
                print(f"   [{i}] {block_type}: {text_preview}")
                
            print(f"\n📏 ESTADÍSTICAS DE TEXTO:")
            total_chars = sum(len(block.get('text', '')) for block in blocks)
            print(f"   📝 Total caracteres: {total_chars}")
            print(f"   📊 Promedio por bloque: {total_chars / len(blocks):.1f}")
            
            # Buscar posibles títulos en los primeros 50 bloques
            print(f"\n🔍 ANÁLISIS DE TÍTULOS POTENCIALES:")
            potential_titles = []
            for i, block in enumerate(blocks[:50]):
                text = block.get('text', '').strip()
                if text and ('"' in text or text.isupper() or len(text) < 50):
                    potential_titles.append((i, text))
            
            print(f"   🏷️ Títulos potenciales encontrados: {len(potential_titles)}")
            for i, (block_idx, title) in enumerate(potential_titles[:5]):
                print(f"      [{block_idx}] {repr(title)}")
                
        else:
            print("❌ NO SE EXTRAJERON BLOQUES DEL PDF")
            return False
            
    except Exception as e:
        print(f"❌ ERROR en PDFLoader: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # PASO 2: Probar CommonBlockPreprocessor con configuración verso
    print("\n" + "="*60)
    print("🔧 PASO 2: PROBANDO COMMONBLOCKPREPROCESSOR V7.0")
    print("="*60)
    
    try:
        # Configuración exacta del perfil verso corregido
        verso_config = {
            'filter_insignificant_blocks': False,
            'min_block_chars_to_keep': 1,
            'aggressive_merge_for_pdfs': False,
            'merge_cross_page_sentences': False,
            'split_blocks_into_paragraphs': False,  # CRUCIAL: NO dividir en párrafos
            'discard_common_pdf_artifacts': False   # CRUCIAL: NO descartar títulos
        }
        
        print(f"⚙️ Configuración aplicada:")
        for key, value in verso_config.items():
            print(f"   {key}: {value}")
        
        preprocessor = CommonBlockPreprocessor(verso_config)
        processed_blocks, processed_metadata = preprocessor.process(blocks, metadata)
        
        print(f"📦 RESULTADO Preprocessor:")
        print(f"   📄 Bloques entrada: {len(blocks)}")
        print(f"   📄 Bloques salida: {len(processed_blocks)}")
        print(f"   📊 Cambio: {len(blocks)} → {len(processed_blocks)}")
        
        if processed_blocks:
            print(f"\n🔍 PRIMEROS 10 BLOQUES PROCESADOS:")
            for i, block in enumerate(processed_blocks[:10]):
                text = block.get('text', '').strip()
                text_preview = repr(text[:80]) if text else "''"
                print(f"   [{i}] {text_preview}")
                
            # Buscar títulos en bloques procesados
            print(f"\n🔍 TÍTULOS EN BLOQUES PROCESADOS:")
            processed_titles = []
            for i, block in enumerate(processed_blocks[:50]):
                text = block.get('text', '').strip()
                if text and text.startswith('"') and text.endswith('"'):
                    processed_titles.append((i, text))
            
            print(f"   🏷️ Títulos entre comillas: {len(processed_titles)}")
            for i, (block_idx, title) in enumerate(processed_titles[:5]):
                print(f"      [{block_idx}] {title}")
                
        else:
            print("❌ NO SE PROCESARON BLOQUES")
            return False
            
    except Exception as e:
        print(f"❌ ERROR en Preprocessor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # PASO 3: Probar VerseSegmenter
    print("\n" + "="*60)
    print("🎵 PASO 3: PROBANDO VERSESEGMENTER")
    print("="*60)
    
    try:
        verso_segmenter_config = {
            'thresholds': {
                'min_consecutive_verses': 2,
                'confidence_threshold': 0.3
            }
        }
        
        segmenter = VerseSegmenter(verso_segmenter_config)
        segments = segmenter.segment(processed_blocks)
        
        print(f"📦 RESULTADO VerseSegmenter:")
        print(f"   📄 Bloques entrada: {len(processed_blocks)}")
        print(f"   🎵 Poemas detectados: {len(segments)}")
        
        if segments:
            print(f"\n✅ POEMAS ENCONTRADOS EN PDF REAL:")
            for i, segment in enumerate(segments[:5]):  # Primeros 5 poemas
                title = segment.get('title', 'Sin título')
                verse_count = segment.get('verse_count', 0)
                content = segment.get('text', '')[:150]
                print(f"   [{i+1}] '{title}' ({verse_count} versos)")
                print(f"       📝 Contenido: {repr(content)}...")
            
            return True
        else:
            print("❌ NO SE DETECTARON POEMAS")
            return False
            
    except Exception as e:
        print(f"❌ ERROR en VerseSegmenter: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_profile_manager_real():
    """Prueba usando ProfileManager con el PDF real"""
    print("\n" + "="*60)
    print("🎭 PASO 4: PROBANDO CON PROFILE MANAGER REAL")
    print("="*60)
    
    # Buscar el PDF
    pdf_path = None
    possible_paths = [
        "C:/Users/adven/Downloads/Mario Benedetti Antologia Poética.pdf",
        "Mario Benedetti Antologia Poética.pdf",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print("❌ PDF no encontrado para ProfileManager")
        return False
    
    try:
        # Forzar recarga del ProfileManager
        import dataset.processing.profile_manager
        importlib.reload(dataset.processing.profile_manager)
        from dataset.processing.profile_manager import ProfileManager
        
        profile_manager = ProfileManager()
        
        # Crear directorio temporal para output
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            result = profile_manager.process_file(
                file_path=pdf_path,
                profile_name='verso',
                output_dir=temp_dir,
                encoding='utf-8',
                output_format='ndjson'
            )
            
            print(f"📦 RESULTADO ProfileManager:")
            print(f"   🎵 Segmentos procesados: {len(result) if result else 0}")
            
            if result and len(result) > 0:
                print(f"✅ ¡ÉXITO! ProfileManager detectó {len(result)} segmentos")
                return True
            else:
                print(f"❌ FALLO: ProfileManager no detectó segmentos")
                return False
                
    except Exception as e:
        print(f"❌ ERROR en ProfileManager: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    success1 = test_pdf_real()
    success2 = test_with_profile_manager_real()
    
    print("\n" + "="*60)
    print("🏁 RESUMEN FINAL")
    print("="*60)
    
    print(f"🔍 Test directo: {'✅ ÉXITO' if success1 else '❌ FALLO'}")
    print(f"🎭 ProfileManager: {'✅ ÉXITO' if success2 else '❌ FALLO'}")
    
    if success1 and not success2:
        print("\n⚠️ PROBLEMA: El test directo funciona pero ProfileManager no")
        print("   Posiblemente hay un problema de caché o configuración en ProfileManager")
    elif not success1 and not success2:
        print("\n❌ PROBLEMA: El PDF real tiene un formato diferente al esperado")
        print("   Necesitamos ajustar el PDFLoader V7.0 para este PDF específico")
    elif success1 and success2:
        print("\n🎉 TODO FUNCIONA: Hay un problema en la aplicación GUI")
        print("   La GUI no está usando las versiones actualizadas del código")

if __name__ == "__main__":
    main() 