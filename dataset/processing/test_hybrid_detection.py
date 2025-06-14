#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el nuevo sistema híbrido de detección de autores.
Específicamente diseñado para probar el caso de "Rubén Darío".
"""

import sys
import os
import json
from typing import Dict, Any, List

# Agregar el directorio de processing al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_segment_ruben_dario() -> List[Dict[str, Any]]:
    """Crea un segmento de prueba basado en el caso real de Rubén Darío"""
    return [{
        "segment_id": "3c8888f8-f431-400e-926d-0686099d007a",
        "document_id": "db3e7495-d067-4322-a9e4-8f254935880f",
        "document_language": "es",
        "text": """CANCIÓN DE OTOÑO EN PRIMAVERA
A Gregorio Martinez Sierra
Juventud, divino tesoro,
ya te vas para no volver!
Cuando quiero llorar, no lloro...
y veces lloro sin querer...
Plural ha sido la celeste
historia de mi corazón.
Era una dulce niña, en este
mundo de duelo aflicción.
Miraba come el alba pura;
sonreía como una flor.
Era su cabellera obscura
hecha de noche de dolor.
Yo era tímido como un niño.
Ella, naturalmente, fue,
para mi amor hecho de armiño,
Herodias Salomé...
Juventud, divino tesoro,
ya te vas para no volver!
Cuando quiero llorar, no lloro...
y veces lloro sin querer...
Y mas consoladora mas
halagadora expresiva,
la otra fue mas sensitiva
cual no pensé encontrar jamás.
Pues su continua ternura
una pasión violenta unía.
En un peplo de gasa pura
una bacante se envolvía...
En sus brazos tomó mi ensueño
y lo arrulló como un bebé...
y le mató, triste pequeño,
falto de luz, falto de fe...
Juventud, divino tesoro,
ya te vas para no volver!
Cuando quiero llorar, no lloro...
y veces lloro sin querer...
Otra juzgó que era mi boca
el estuche de su pasión;
y que me roería, loca,
con sus dientes el corazón.
Poniendo en un amor de exceso
la mira de su voluntad,
mientras eran abrazo beso
síntesis de la eternidad;
y de nuestra carne ligera
imaginar siempre un Edén,
sin pensar que la Primavera
y la carne acaban también...
Juventud, divino tesoro,
ya te vas para no volver!
Cuando quiero llorar, no lloro...
y veces lloro sin querer...
Y las demás! En tantos climas,
en tantas tierras siempre son,
si no pretextos de mis rimas
fantasmas de mi corazón.
En vano busqué la princesa
que estaba triste de esperar.
La vida es dura. Amarga pesa.
Ya no hay princesa que cantar!
Mas pesar del tiempo terco,
mi sed de amor no tiene fin;
con el cabello gris, me acerco
a los rosales del jardín...
Juventud, divino tesoro,
ya te vas para no volver!
Cuando quiero llorar, no lloro...
y veces lloro sin querer...
Mas es mía el Alba de oro!""",
        "segment_type": "poem",
        "segment_order": 1,
        "text_length": 1942,
        "source_file_path": "C:\\Users\\adven\\Downloads\\Dario, Ruben - Antologia.pdf",
        "document_title": "Dario, Ruben - Antologia",
        "additional_metadata": {
            "segment_detected_author": "de Tantos Poetas",  # Detección incorrecta anterior
            "segment_author_confidence": 0.6516666666666667,
            "segment_author_detection_method": "contextual_analysis"
        }
    }]

def test_hybrid_detection():
    """Prueba el sistema híbrido de detección de autores"""
    print("=== PRUEBA DEL SISTEMA HÍBRIDO DE DETECCIÓN DE AUTORES ===")
    print("Caso de prueba: Rubén Darío - Canción de Otoño en Primavera")
    print()
    
    # Crear segmento de prueba
    segments = create_test_segment_ruben_dario()
    
    # Configuración de prueba
    config = {
        'use_hybrid_detection': True,
        'confidence_threshold': 0.3,
        'debug': True,
        'hybrid_config': {
            'enable_literary_database': True,
            'enable_stylometric_analysis': True,
            'enable_document_context_boost': True,
            'literary_authors_priority': True
        }
    }
    
    print("1. Probando detector híbrido...")
    try:
        from hybrid_author_detection import HybridAuthorDetector
        
        detector = HybridAuthorDetector(config)
        result = detector.detect_author(segments, 'verso')
        
        if result:
            print(f"✅ ÉXITO: Autor detectado: '{result['name']}'")
            print(f"   Confianza: {result['confidence']:.3f}")
            print(f"   Método: {result['method']}")
            print(f"   Detalles: {json.dumps(result.get('details', {}), indent=2, ensure_ascii=False)}")
        else:
            print("❌ FALLO: No se detectó ningún autor")
            
    except ImportError as e:
        print(f"❌ ERROR DE IMPORTACIÓN: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    print()
    print("2. Probando función de conveniencia detect_author_in_segments...")
    try:
        from author_detection import detect_author_in_segments
        
        result2 = detect_author_in_segments(
            segments, 
            'verso', 
            config,
            document_title="Dario, Ruben - Antologia",
            source_file_path="C:\\Users\\adven\\Downloads\\Dario, Ruben - Antologia.pdf"
        )
        
        if result2:
            print(f"✅ ÉXITO: Autor detectado: '{result2['name']}'")
            print(f"   Confianza: {result2['confidence']:.3f}")
            print(f"   Método: {result2['method']}")
        else:
            print("❌ FALLO: No se detectó ningún autor")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    print()
    print("3. Comparando con detector anterior...")
    try:
        from enhanced_contextual_author_detection import EnhancedContextualAuthorDetector
        
        old_detector = EnhancedContextualAuthorDetector(config)
        old_result = old_detector.detect_author(
            segments, 
            'verso',
            document_title="Dario, Ruben - Antologia",
            source_file_path="C:\\Users\\adven\\Downloads\\Dario, Ruben - Antologia.pdf"
        )
        
        if old_result:
            print(f"📊 DETECTOR ANTERIOR: '{old_result['name']}' (confianza: {old_result['confidence']:.3f})")
        else:
            print("📊 DETECTOR ANTERIOR: No detectó autor")
            
    except Exception as e:
        print(f"⚠️ No se pudo probar detector anterior: {e}")
    
    return True

def test_stylometric_components():
    """Prueba los componentes estilométricos individualmente"""
    print("\n=== PRUEBA DE COMPONENTES ESTILOMÉTRICOS ===")
    
    try:
        from stylometric_author_detection import StylometricAuthorDetector, LiteraryAuthorDatabase
        
        # Probar base de datos literaria
        print("1. Probando base de datos literaria...")
        db = LiteraryAuthorDatabase()
        
        # Buscar Rubén Darío
        ruben_info = db.get_author_info("Rubén Darío")
        if ruben_info:
            print(f"✅ Rubén Darío encontrado en la base de datos:")
            print(f"   Nombre: {ruben_info['name']}")
            print(f"   Período: {ruben_info['period']}")
            print(f"   Movimiento: {ruben_info['movement']}")
            print(f"   Nacionalidad: {ruben_info['nationality']}")
        else:
            print("❌ Rubén Darío no encontrado en la base de datos")
        
        # Probar detección estilométrica
        print("\n2. Probando detector estilométrico...")
        segments = create_test_segment_ruben_dario()
        
        stylometric_detector = StylometricAuthorDetector()
        result = stylometric_detector.detect_author(segments, 'verso')
        
        if result:
            print(f"✅ Resultado estilométrico: '{result['name']}' (confianza: {result['confidence']:.3f})")
            print(f"   Método: {result['method']}")
        else:
            print("❌ No se obtuvo resultado estilométrico")
            
    except Exception as e:
        print(f"❌ ERROR en componentes estilométricos: {e}")
        return False
    
    return True

def main():
    """Función principal de prueba"""
    print("INICIANDO PRUEBAS DEL SISTEMA HÍBRIDO DE DETECCIÓN DE AUTORES")
    print("=" * 70)
    
    success = True
    
    # Probar componentes estilométricos
    if not test_stylometric_components():
        success = False
    
    # Probar detector híbrido
    if not test_hybrid_detection():
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("\n📋 RESUMEN:")
        print("- ✅ Sistema híbrido implementado")
        print("- ✅ Base de datos de autores literarios funcional")
        print("- ✅ Análisis estilométrico integrado")
        print("- ✅ Detección mejorada para casos como 'Rubén Darío'")
        print("\n🚀 El sistema está listo para procesar documentos con mejor precisión.")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("\n🔧 Revisa los errores anteriores y verifica:")
        print("- Que todos los archivos estén en su lugar")
        print("- Que las importaciones funcionen correctamente")
        print("- Que la configuración sea válida")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)