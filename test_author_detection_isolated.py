#!/usr/bin/env python3
"""
Test aislado para detectar el problema específico en la detección de autor
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

from processing.author_detection import detect_author_in_segments
from pathlib import Path

def test_author_detection_isolated():
    """Test aislado de detección de autor"""
    
    # Simular segmentos básicos
    segments = [
        {
            'text': 'CANCIÓN DE OTOÑO EN PRIMAVERA\n\nA Gregorio Martinez Sierra\nJuventud, divino tesoro,\nya te vas para no volver!',
            'metadata': {'type': 'verse'}
        },
        {
            'text': 'Cuando quiero llorar, no lloro...\ny a veces lloro sin querer...',
            'metadata': {'type': 'verse'}
        }
    ]
    
    # Información del documento
    document_title = "Dario, Ruben - Antologia"
    source_file_path = r"C:\Users\adven\Downloads\Dario, Ruben - Antologia.pdf"
    
    print("🔍 Iniciando test aislado de detección de autor...")
    print(f"📄 Archivo: {source_file_path}")
    print(f"📝 Título: {document_title}")
    print(f"📊 Segmentos: {len(segments)}")
    
    try:
        # Test con configuración básica
        config = {
            'confidence_threshold': 0.5,
            'debug': True,
            'use_hybrid_detection': True
        }
        
        print("\n🎯 Probando detección híbrida...")
        result = detect_author_in_segments(
            segments=segments,
            profile_type='verso',
            config=config,
            document_title=document_title,
            source_file_path=source_file_path
        )
        
        if result:
            print(f"✅ AUTOR DETECTADO: {result.get('name')}")
            print(f"📊 Confianza: {result.get('confidence', 0) * 100:.1f}%")
            print(f"🔧 Método: {result.get('method', 'unknown')}")
        else:
            print("❌ No se detectó autor")
            
    except Exception as e:
        print(f"💥 ERROR en detección híbrida: {e}")
        import traceback
        traceback.print_exc()
        
        # Intentar con detección básica
        print("\n🔄 Probando detección básica...")
        try:
            config['use_hybrid_detection'] = False
            result = detect_author_in_segments(
                segments=segments,
                profile_type='verso',
                config=config,
                document_title=document_title,
                source_file_path=source_file_path
            )
            
            if result:
                print(f"✅ AUTOR DETECTADO (básico): {result.get('name')}")
                print(f"📊 Confianza: {result.get('confidence', 0) * 100:.1f}%")
            else:
                print("❌ No se detectó autor con método básico")
                
        except Exception as e2:
            print(f"💥 ERROR también en detección básica: {e2}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_author_detection_isolated() 