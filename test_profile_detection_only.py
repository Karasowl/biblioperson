#!/usr/bin/env python3
"""
Test específico para debuggear la detección de perfiles
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

from dataset.processing.profile_detector import ProfileDetector
from dataset.processing.loaders.pdf_loader import PDFLoader

def test_profile_detection_debug():
    """Test específico para debuggear detección de perfiles"""
    
    test_file = r"C:\Users\adven\Downloads\Dario, Ruben - Antologia.pdf"
    
    print("=" * 80)
    print("🔍 DEBUG: DETECCIÓN DE PERFIL VERSO")
    print("=" * 80)
    
    # === PASO 1: EXTRAER CONTENIDO ORIGINAL ===
    print("\n📋 PASO 1: Extrayendo contenido original...")
    
    loader = PDFLoader(test_file)
    result = loader.load()
    blocks = result.get('blocks', [])
    
    print(f"📄 Bloques extraídos: {len(blocks)}")
    
    # Mostrar primeras 20 líneas del contenido original
    if blocks:
        first_block_text = blocks[0].get('text', '')
        lines = first_block_text.split('\n')[:20]
        print(f"\n📝 Primeras 20 líneas del contenido original:")
        for i, line in enumerate(lines, 1):
            line_clean = line.strip()
            if line_clean:
                print(f"   {i:2d}. [{len(line_clean):3d} chars] {line_clean}")
            else:
                print(f"   {i:2d}. [VACÍA]")
    
    # === PASO 2: ANÁLISIS MANUAL DE ESTRUCTURA ===
    print(f"\n📋 PASO 2: Análisis manual de estructura...")
    
    if blocks:
        all_text = '\n'.join(block.get('text', '') for block in blocks)
        lines = all_text.split('\n')
        
        # Contar líneas por longitud
        short_lines = [line for line in lines if line.strip() and len(line.strip()) <= 120]
        long_lines = [line for line in lines if line.strip() and len(line.strip()) > 120]
        empty_lines = [line for line in lines if not line.strip()]
        
        print(f"📊 Análisis de líneas:")
        print(f"   • Total líneas: {len(lines)}")
        print(f"   • Líneas cortas (≤120): {len(short_lines)} ({len(short_lines)/len(lines)*100:.1f}%)")
        print(f"   • Líneas largas (>120): {len(long_lines)} ({len(long_lines)/len(lines)*100:.1f}%)")
        print(f"   • Líneas vacías: {len(empty_lines)} ({len(empty_lines)/len(lines)*100:.1f}%)")
        
        # Mostrar ejemplos de líneas cortas
        print(f"\n📝 Ejemplos de líneas cortas (primeras 10):")
        for i, line in enumerate(short_lines[:10], 1):
            print(f"   {i:2d}. [{len(line):3d}] {line}")
        
        # Buscar patrones de verso
        verse_patterns = 0
        for line in short_lines:
            line_clean = line.strip()
            # Patrones típicos de verso
            if (line_clean.endswith(',') or 
                line_clean.endswith(';') or 
                line_clean.endswith('!') or 
                line_clean.endswith('?') or
                len(line_clean.split()) <= 8):
                verse_patterns += 1
        
        print(f"\n🎭 Patrones de verso detectados: {verse_patterns}/{len(short_lines)} ({verse_patterns/len(short_lines)*100:.1f}%)")
    
    # === PASO 3: DETECCIÓN AUTOMÁTICA ===
    print(f"\n📋 PASO 3: Detección automática...")
    
    detector = ProfileDetector()
    
    # Usar el contenido extraído directamente
    content_sample = all_text if blocks else None
    
    profile_candidate = detector.detect_profile(test_file, content_sample)
    
    print(f"🔍 Perfil detectado: {profile_candidate.profile_name}")
    print(f"🎯 Confianza: {profile_candidate.confidence:.2f}")
    print(f"📊 Razones:")
    for reason in profile_candidate.reasons:
        print(f"   • {reason}")
    
    print(f"📈 Métricas estructurales:")
    for key, value in profile_candidate.structural_metrics.items():
        if isinstance(value, float):
            print(f"   • {key}: {value:.3f}")
        else:
            print(f"   • {key}: {value}")
    
    # === PASO 4: VERIFICACIÓN MANUAL ===
    print(f"\n📋 PASO 4: Verificación manual...")
    
    # Verificar si cumple criterios de verso manualmente
    if blocks:
        total_non_empty = len([line for line in lines if line.strip()])
        short_ratio = len(short_lines) / total_non_empty if total_non_empty > 0 else 0
        very_short_lines = [line for line in short_lines if len(line.strip()) <= 100]
        very_short_ratio = len(very_short_lines) / total_non_empty if total_non_empty > 0 else 0
        
        print(f"✅ Verificación manual de criterios de verso:")
        print(f"   • Líneas cortas (<180): {short_ratio:.1%} (necesita ≥80%)")
        print(f"   • Bloques muy cortos (<100): {very_short_ratio:.1%} (necesita ≥60%)")
        print(f"   • Patrones de verso: {verse_patterns/len(short_lines)*100:.1f}% de líneas cortas")
        
        # Determinar si debería ser verso
        should_be_verse = (short_ratio >= 0.8 and very_short_ratio >= 0.6)
        print(f"   • ¿Debería ser VERSO?: {'SÍ' if should_be_verse else 'NO'}")
        
        if should_be_verse and profile_candidate.profile_name != 'verso':
            print(f"   ❌ ERROR: Debería detectarse como VERSO pero se detectó como {profile_candidate.profile_name}")
            return False
        elif profile_candidate.profile_name == 'verso':
            print(f"   ✅ CORRECTO: Detectado como VERSO")
            return True
        else:
            print(f"   ⚠️  AMBIGUO: Criterios no cumplen verso, detectado como {profile_candidate.profile_name}")
            return True

if __name__ == "__main__":
    success = test_profile_detection_debug()
    if success:
        print(f"\n🎉 DETECCIÓN CORRECTA!")
    else:
        print(f"\n💥 DETECCIÓN INCORRECTA!")
    
    sys.exit(0 if success else 1) 