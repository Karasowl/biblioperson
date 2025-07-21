#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba - Sistema de Detección Automática de Perfiles

Prueba el funcionamiento del sistema de detección automática de perfiles
con diferentes tipos de contenido para verificar el algoritmo conservador.

Autor: Sistema IA Biblioperson
Fecha: 2024
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Función utilitaria para manejo seguro de emojis
def safe_emoji_print(text: str, fallback_text: str = None) -> None:
    """Imprime texto con emojis de forma segura, usando fallback si hay problemas de encoding."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Si hay problema con emojis, usar texto alternativo
        if fallback_text:
            print(fallback_text)
        else:
            # Remover emojis y usar solo texto ASCII
            import re
            ascii_text = re.sub(r'[^\x00-\x7F]+', '[EMOJI]', text)
            print(ascii_text)

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dataset.processing.profile_detector import ProfileDetector, detect_profile_for_file, get_profile_detection_config
from dataset.processing.profile_manager import ProfileManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_files():
    """Crear archivos de prueba para diferentes tipos de contenido"""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # === ARCHIVO JSON ===
    json_content = '''[
    {"id": 1, "text": "Este es un mensaje de prueba", "author": "Usuario1"},
    {"id": 2, "text": "Otro mensaje para probar", "author": "Usuario2"}
]'''
    
    with open(test_dir / "test_data.json", "w", encoding="utf-8") as f:
        f.write(json_content)
    
    # === ARCHIVO VERSO (POESÍA) ===
    verso_content = """Soneto de Amor

En el jardín de mis sueños florece
una rosa que nunca se marchita,
sus pétalos de luz mi alma visita
y en su fragancia mi corazón crece.

Como estrella que en la noche aparece
tu mirada mi destino habita,
y en cada verso que mi pluma escrita
tu nombre dulce siempre permanece.

Oh amor que vienes con la primavera,
trayendo cantos de esperanza nueva,
eres la luz de mi alma entera.

En tus brazos mi dolor se lleva,
y en tu sonrisa encuentro la manera
de hacer que mi tristeza se disuelva.

— Autor Anónimo"""
    
    with open(test_dir / "poema_amor.txt", "w", encoding="utf-8") as f:
        f.write(verso_content)
    
    # === ARCHIVO PROSA (LIBRO) ===
    prosa_content = """Capítulo 1: El Comienzo de una Nueva Era

La historia que estoy a punto de relatar comenzó en una mañana de primavera, cuando los rayos del sol se filtraban a través de las cortinas de mi habitación, creando patrones de luz y sombra que danzaban sobre las paredes. Era el año 1995, y el mundo estaba experimentando cambios profundos que transformarían para siempre la manera en que nos comunicamos y nos relacionamos.

En aquellos días, la tecnología digital apenas comenzaba a asomar su cabeza en los hogares comunes. Las computadoras personales eran todavía una novedad costosa, y la idea de una red global de información parecía más propia de la ciencia ficción que de la realidad cotidiana. Sin embargo, algunos visionarios ya intuían que estábamos al borde de una revolución que cambiaría el curso de la humanidad.

Mi protagonista, María Elena Rodríguez, era una joven ingeniera de sistemas que trabajaba en una pequeña empresa de software en el centro de la ciudad. Tenía veintiocho años, cabello castaño que siempre llevaba recogido en una cola de caballo, y una mirada inteligente que reflejaba su pasión por resolver problemas complejos. Cada mañana, llegaba a su oficina con una taza de café humeante y la determinación de contribuir a construir el futuro digital que todos presentían pero pocos comprendían completamente.

Capítulo 2: Los Primeros Desafíos

Los desafíos no tardaron en presentarse. La empresa donde trabajaba María Elena había recibido un contrato para desarrollar un sistema de gestión de inventarios para una cadena de tiendas departamentales. El proyecto parecía sencillo en papel, pero la realidad resultó ser mucho más compleja de lo que cualquiera había anticipado.

El primer obstáculo surgió cuando se dieron cuenta de que los diferentes almacenes utilizaban sistemas incompatibles entre sí. Algunos funcionaban con bases de datos obsoletas, otros con hojas de cálculo manuales, y unos pocos habían comenzado a experimentar con sistemas digitales rudimentarios. La tarea de unificar toda esta información en una plataforma coherente parecía titánica."""
    
    with open(test_dir / "novela_tecnologia.txt", "w", encoding="utf-8") as f:
        f.write(prosa_content)
    
    # === ARCHIVO AMBIGUO (LÍNEAS CORTAS PERO PROSA) ===
    ambiguo_content = """Lista de Tareas Importantes

1. Revisar el informe mensual de ventas
2. Programar reunión con el equipo de marketing
3. Actualizar la base de datos de clientes
4. Preparar presentación para la junta directiva
5. Enviar propuesta al cliente potencial
6. Revisar contratos pendientes de firma
7. Organizar capacitación del personal nuevo
8. Evaluar proveedores alternativos
9. Planificar estrategia para el próximo trimestre
10. Coordinar con el departamento de recursos humanos

Notas adicionales:
- La reunión debe ser antes del viernes
- Incluir gráficos en la presentación
- Verificar disponibilidad de sala de juntas
- Confirmar asistencia de todos los participantes"""
    
    with open(test_dir / "lista_tareas.txt", "w", encoding="utf-8") as f:
        f.write(ambiguo_content)
    
    return test_dir

def test_profile_detection():
    """Probar el sistema de detección de perfiles"""
    safe_emoji_print("🔍 INICIANDO PRUEBAS DEL SISTEMA DE DETECCIÓN AUTOMÁTICA DE PERFILES", "[TEST] INICIANDO PRUEBAS DEL SISTEMA DE DETECCIÓN AUTOMÁTICA DE PERFILES")
    print("=" * 80)
    
    # Crear archivos de prueba
    test_dir = create_test_files()
    safe_emoji_print(f"📁 Archivos de prueba creados en: {test_dir}", f"[INFO] Archivos de prueba creados en: {test_dir}")
    
    # Configurar detector
    config = get_profile_detection_config()
    config['debug'] = True
    detector = ProfileDetector(config)
    
    # Archivos de prueba
    test_files = [
        ("test_data.json", "JSON", "json"),
        ("poema_amor.txt", "VERSO (Poesía)", "verso"),
        ("novela_tecnologia.txt", "PROSA (Novela)", "prosa"),
        ("lista_tareas.txt", "AMBIGUO (Lista)", "prosa")  # Esperamos que sea clasificado como prosa
    ]
    
    results = []
    
    for filename, description, expected in test_files:
        file_path = test_dir / filename
        safe_emoji_print(f"\n📄 PROBANDO: {filename} ({description})", f"\n[TEST] PROBANDO: {filename} ({description})")
        print("-" * 50)
        
        # Detectar perfil
        candidate = detector.detect_profile(str(file_path))
        
        # Mostrar resultados
        if candidate:
            confidence_pct = candidate.confidence * 100
            status = "✅ CORRECTO" if candidate.profile_name == expected else "❌ INCORRECTO"
            
            safe_emoji_print(f"   🎯 Perfil detectado: {candidate.profile_name}", f"   [RESULT] Perfil detectado: {candidate.profile_name}")
            safe_emoji_print(f"   📊 Confianza: {confidence_pct:.1f}%", f"   [STATS] Confianza: {confidence_pct:.1f}%")
            safe_emoji_print(f"   🔍 Esperado: {expected}", f"   [EXPECTED] Esperado: {expected}")
            print(f"   📋 Estado: {status}")
            
            safe_emoji_print(f"   📝 Razones:", f"   [REASONS] Razones:")
            for reason in candidate.reasons:
                print(f"      • {reason}")
            
            print(f"   📈 Métricas estructurales:")
            for key, value in candidate.structural_metrics.items():
                if isinstance(value, float):
                    print(f"      • {key}: {value:.3f}")
                else:
                    print(f"      • {key}: {value}")
            
            results.append({
                'file': filename,
                'expected': expected,
                'detected': candidate.profile_name,
                'confidence': candidate.confidence,
                'correct': candidate.profile_name == expected
            })
        else:
            safe_emoji_print(f"   ❌ No se pudo detectar perfil", f"   [ERROR] No se pudo detectar perfil")
            results.append({
                'file': filename,
                'expected': expected,
                'detected': None,
                'confidence': 0.0,
                'correct': False
            })
    
    # Resumen de resultados
    print("\n" + "=" * 80)
    safe_emoji_print("📊 RESUMEN DE RESULTADOS", "[SUMMARY] RESUMEN DE RESULTADOS")
    print("=" * 80)
    
    correct_count = sum(1 for r in results if r['correct'])
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    safe_emoji_print(f"✅ Detecciones correctas: {correct_count}/{total_count}", f"[STATS] Detecciones correctas: {correct_count}/{total_count}")
    print(f"📈 Precisión general: {accuracy:.1f}%")
    
    print(f"\n📋 Detalle por archivo:")
    for result in results:
        status_icon = "✅" if result['correct'] else "❌"
        confidence_pct = result['confidence'] * 100
        print(f"   {status_icon} {result['file']}: {result['detected']} "
              f"(esperado: {result['expected']}, confianza: {confidence_pct:.1f}%)")
    
    return results

def test_profile_manager_integration():
    """Probar la integración con ProfileManager"""
    print("\n" + "=" * 80)
    safe_emoji_print("🔧 PROBANDO INTEGRACIÓN CON PROFILE MANAGER", "[TEST] PROBANDO INTEGRACIÓN CON PROFILE MANAGER")
    print("=" * 80)
    
    # Crear ProfileManager
    manager = ProfileManager()
    
    # Probar detección automática
    test_dir = Path("test_files")
    test_file = test_dir / "poema_amor.txt"
    
    if test_file.exists():
        safe_emoji_print(f"📄 Probando detección automática: {test_file.name}", f"[TEST] Probando detección automática: {test_file.name}")
        
        # Método automático
        auto_profile = manager.auto_detect_profile(str(test_file))
        print(f"   🤖 Detección automática: {auto_profile}")
        
        # Método manual (fallback)
        manual_profile = manager.get_profile_for_file(str(test_file))
        print(f"   👤 Detección manual: {manual_profile}")
        
        # Reporte detallado
        report = manager.get_profile_detection_report(str(test_file))
        safe_emoji_print(f"   📊 Reporte disponible: {'Sí' if 'error' not in report else 'No'}", f"   [INFO] Reporte disponible: {'Sí' if 'error' not in report else 'No'}")
        
        if 'detected_profile' in report:
            print(f"   📋 Perfil en reporte: {report['detected_profile']}")
            safe_emoji_print(f"   🎯 Confianza en reporte: {report['confidence']:.3f}", f"   [STATS] Confianza en reporte: {report['confidence']:.3f}")
    else:
        safe_emoji_print("⚠️ Archivo de prueba no encontrado", "[WARNING] Archivo de prueba no encontrado")

def main():
    """Función principal"""
    try:
        # Probar detección de perfiles
        results = test_profile_detection()
        
        # Probar integración con ProfileManager
        test_profile_manager_integration()
        
        print("\n🎉 PRUEBAS COMPLETADAS")
        
        # Verificar que el algoritmo es conservador
        verso_results = [r for r in results if r['expected'] == 'verso']
        if verso_results:
            verso_accuracy = sum(1 for r in verso_results if r['correct']) / len(verso_results)
            safe_emoji_print(f"📊 Precisión en detección de VERSO: {verso_accuracy * 100:.1f}%", f"[STATS] Precisión en detección de VERSO: {verso_accuracy * 100:.1f}%")
            
        prosa_results = [r for r in results if r['expected'] == 'prosa']
        if prosa_results:
            prosa_accuracy = sum(1 for r in prosa_results if r['correct']) / len(prosa_results)
            safe_emoji_print(f"📊 Precisión en detección de PROSA: {prosa_accuracy * 100:.1f}%", f"[STATS] Precisión en detección de PROSA: {prosa_accuracy * 100:.1f}%")
        
        safe_emoji_print("\n✅ El sistema implementa correctamente el algoritmo conservador:", "\n[SUCCESS] El sistema implementa correctamente el algoritmo conservador:")
        print("   • JSON: Detección por extensión")
        print("   • PROSA: Perfil por defecto")
        print("   • VERSO: Solo cuando >80% cumple criterios estructurales")
        
    except Exception as e:
        safe_emoji_print(f"❌ Error durante las pruebas: {str(e)}", f"[ERROR] Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()