#!/usr/bin/env python3
"""
Test específico para la detección mejorada de autor contextual
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'dataset'))

from processing.enhanced_contextual_author_detection import EnhancedContextualAuthorDetector, DocumentContext

def test_enhanced_author_detection():
    """Test específico del detector mejorado"""
    
    print("🔍 Test del Enhanced Contextual Author Detector")
    
    # Configuración
    config = {
        'confidence_threshold': 0.5,
        'debug': True,
        'strict_mode': False  # Modo permisivo para ver si detecta
    }
    
    detector = EnhancedContextualAuthorDetector(config)
    
    # Crear contexto del documento
    doc_context = DocumentContext(
        title="Dario, Ruben - Antologia",
        filename="Dario, Ruben - Antologia.pdf",
        metadata={}
    )
    
    print(f"📄 Título: {doc_context.title}")
    print(f"📁 Archivo: {doc_context.filename}")
    
    # Test 1: Extracción desde contexto del documento
    print("\n🎯 Test 1: Extracción desde contexto del documento")
    author_from_context = detector.extract_author_from_document_context(doc_context)
    
    if author_from_context:
        print(f"✅ Autor extraído del contexto: '{author_from_context}'")
    else:
        print("❌ No se extrajo autor del contexto")
    
    # Test 2: Extracción manual de título
    print("\n🎯 Test 2: Extracción manual de título")
    title_candidates = detector._extract_from_title("Dario, Ruben - Antologia")
    print(f"📋 Candidatos del título: {title_candidates}")
    
    # Test 3: Extracción manual de filename
    print("\n🎯 Test 3: Extracción manual de filename")
    filename_candidates = detector._extract_from_title("Dario, Ruben - Antologia.pdf")
    print(f"📋 Candidatos del filename: {filename_candidates}")
    
    # Test 4: Validación de nombres
    print("\n🎯 Test 4: Validación de nombres")
    test_names = [
        "Dario, Ruben",
        "Ruben Dario", 
        "Rubén Darío",
        "Dario Ruben"
    ]
    
    for name in test_names:
        is_valid = detector._is_valid_author_name(name)
        print(f"   '{name}' -> {'✅ Válido' if is_valid else '❌ Inválido'}")
    
    # Test 5: Segmentos simulados
    print("\n🎯 Test 5: Detección con segmentos simulados")
    segments = [
        {
            'text': 'CANCIÓN DE OTOÑO EN PRIMAVERA\n\nA Gregorio Martinez Sierra\nJuventud, divino tesoro,\nya te vas para no volver!',
            'metadata': {'type': 'verse'}
        }
    ]
    
    try:
        result = detector.detect_author_enhanced(segments, 'poetry', doc_context)
        if result:
            print(f"✅ RESULTADO FINAL: {result.get('name')}")
            print(f"📊 Confianza: {result.get('confidence', 0) * 100:.1f}%")
            print(f"🔧 Método: {result.get('method', 'unknown')}")
            if result.get('details'):
                print(f"📝 Detalles: {result.get('details')}")
        else:
            print("❌ No se detectó autor con segmentos")
    except Exception as e:
        print(f"💥 ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_author_detection() 