#!/usr/bin/env python3
"""
Script de prueba para el algoritmo de detección automática de autores
====================================================================

Prueba diferentes casos de uso y patrones de autoría en textos de verso y prosa.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from author_detection import AutorDetector, detect_author_in_segments, get_author_detection_config

def test_verso_patterns():
    """Prueba patrones específicos de verso/poesía"""
    print("🎭 PROBANDO PATRONES DE VERSO")
    print("=" * 50)
    
    # Casos de prueba para verso
    test_cases = [
        {
            'name': 'Firma al final del poema',
            'segments': [
                {'text': 'Sonatina'},
                {'text': 'La princesa está triste... ¿qué tendrá la princesa?'},
                {'text': 'Los suspiros se escapan de su boca de fresa'},
                {'text': '— Rubén Darío'}
            ]
        },
        {
            'name': 'Atribución con "Por"',
            'segments': [
                {'text': 'Canción de Otoño'},
                {'text': 'Por Federico García Lorca'},
                {'text': 'Verde que te quiero verde'},
                {'text': 'Verde viento. Verdes ramas.'}
            ]
        },
        {
            'name': 'Título con autor incluido',
            'segments': [
                {'text': 'Soneto de Pablo Neruda'},
                {'text': 'Puedo escribir los versos más tristes esta noche'},
                {'text': 'Escribir, por ejemplo: "La noche está estrellada"'}
            ]
        },
        {
            'name': 'Nombre aislado al final',
            'segments': [
                {'text': 'Rima LIII'},
                {'text': 'Volverán las oscuras golondrinas'},
                {'text': 'en tu balcón sus nidos a colgar'},
                {'text': 'Gustavo Adolfo Bécquer'}
            ]
        }
    ]
    
    detector = AutorDetector({'confidence_threshold': 0.5, 'debug': True})
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print("-" * 30)
        
        result = detector.detect_author(case['segments'], 'verso')
        
        if result:
            print(f"✅ Autor detectado: {result['name']}")
            print(f"   Confianza: {result['confidence']:.2f}")
            print(f"   Método: {result['extraction_method']}")
            print(f"   Fuentes: {result['sources']}")
        else:
            print("❌ No se detectó autor")

def test_prosa_patterns():
    """Prueba patrones específicos de prosa"""
    print("\n\n📚 PROBANDO PATRONES DE PROSA")
    print("=" * 50)
    
    # Casos de prueba para prosa
    test_cases = [
        {
            'name': 'Formato académico con año',
            'segments': [
                {'text': 'García Márquez, Gabriel (1967)'},
                {'text': 'Cien años de soledad es una novela del escritor colombiano Gabriel García Márquez'},
                {'text': 'Muchos años después, frente al pelotón de fusilamiento...'}
            ]
        },
        {
            'name': 'Header de artículo con fecha',
            'segments': [
                {'text': 'Mario Vargas Llosa - 15/10/2010'},
                {'text': 'El escritor peruano ha sido galardonado con el Premio Nobel de Literatura'},
                {'text': 'La Academia Sueca destacó su cartografía de las estructuras del poder..'}
            ]
        },
        {
            'name': 'Byline tradicional',
            'segments': [
                {'text': 'Por Isabel Allende'},
                {'text': 'La casa de los espíritus narra la saga de una familia a lo largo de cuatro generaciones'},
                {'text': 'Barrabás llegó a la familia por vía marítima..'}
            ]
        },
        {
            'name': 'Metadatos explícitos',
            'segments': [
                {'text': 'Autor: Jorge Luis Borges'},
                {'text': 'El Aleph es uno de los cuentos más famosos del escritor argentino'},
                {'text': 'En el Aleph vi la tierra en el Aleph..'}
            ]
        },
        {
            'name': 'Formato de libro con editorial',
            'segments': [
                {'text': 'Julio Cortázar'},
                {'text': 'Editorial Sudamericana, Buenos Aires, 1963'},
                {'text': 'Rayuela es una novela del escritor argentino Julio Cortázar'},
                {'text': '¿Encontraría a la Maga?'}
            ]
        }
    ]
    
    detector = AutorDetector({'confidence_threshold': 0.7, 'debug': True})
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print("-" * 30)
        
        result = detector.detect_author(case['segments'], 'prosa')
        
        if result:
            print(f"✅ Autor detectado: {result['name']}")
            print(f"   Confianza: {result['confidence']:.2f}")
            print(f"   Método: {result['extraction_method']}")
            print(f"   Fuentes: {result['sources']}")
        else:
            print("❌ No se detectó autor")

def test_edge_cases():
    """Prueba casos límite y falsos positivos"""
    print("\n\n⚠️ PROBANDO CASOS LÍMITE")
    print("=" * 50)
    
    # Casos que NO deberían detectar autores
    test_cases = [
        {
            'name': 'Palabras comunes (falso positivo)',
            'segments': [
                {'text': 'El Señor de los Anillos'},
                {'text': 'En un agujero en el suelo, vivía un hobbit'},
                {'text': 'La Casa del Tiempo'}
            ]
        },
        {
            'name': 'Preposiciones y artículos',
            'segments': [
                {'text': 'De la vida y la muerte'},
                {'text': 'En el principio era el Verbo'},
                {'text': 'Por el camino del amor'}
            ]
        },
        {
            'name': 'Texto sin autor aparente',
            'segments': [
                {'text': 'Este es un texto anónimo'},
                {'text': 'No contiene información de autoría'},
                {'text': 'Debería retornar None'}
            ]
        }
    ]
    
    detector = AutorDetector({'confidence_threshold': 0.6, 'debug': True})
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print("-" * 30)
        
        result_verso = detector.detect_author(case['segments'], 'verso')
        result_prosa = detector.detect_author(case['segments'], 'prosa')
        
        if result_verso or result_prosa:
            print(f"⚠️ FALSO POSITIVO detectado:")
            if result_verso:
                print(f"   Verso: {result_verso['name']} (confianza: {result_verso['confidence']:.2f})")
            if result_prosa:
                print(f"   Prosa: {result_prosa['name']} (confianza: {result_prosa['confidence']:.2f})")
        else:
            print("✅ Correctamente no detectó autor (como esperado)")

def test_utility_functions():
    """Prueba las funciones de utilidad"""
    print("\n\n🔧 PROBANDO FUNCIONES DE UTILIDAD")
    print("=" * 50)
    
    # Probar función de conveniencia
    segments = [
        {'text': 'Veinte poemas de amor y una canción desesperada'},
        {'text': 'Por Pablo Neruda'},
        {'text': 'Cuerpo de mujer, blancas colinas, muslos blancos'}
    ]
    
    print("1. Función detect_author_in_segments")
    print("-" * 30)
    result = detect_author_in_segments(segments, 'verso')
    if result:
        print(f"✅ Autor: {result['name']} (confianza: {result['confidence']:.2f})")
    else:
        print("❌ No detectado")
    
    print("\n2. Configuraciones por defecto")
    print("-" * 30)
    config_verso = get_author_detection_config('verso')
    config_prosa = get_author_detection_config('prosa')
    
    print(f"Verso: {config_verso}")
    print(f"Prosa: {config_prosa}")

def main():
    """Función principal de pruebas"""
    print("🔍 ALGORITMO AVANZADO DE DETECCIÓN DE AUTORES - PRUEBAS")
    print("=" * 60)
    
    try:
        test_verso_patterns()
        test_prosa_patterns()
        test_edge_cases()
        test_utility_functions()
        
        print("\n\n✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 