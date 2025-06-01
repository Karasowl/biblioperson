#!/usr/bin/env python3
"""
TEST VERIFICACIÓN ESTRUCTURA FINAL
===================================

Verificar exactamente cómo están estructurados los bloques
y poemas después de las correcciones del MarkdownPDFLoader.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.profile_manager import ProfileManager
except ImportError as e:
    print(f"❌ Error importando ProfileManager: {e}")
    sys.exit(1)

def test_estructura_final():
        """Verificar estructura de bloques y poemas"""
        
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            return False
        
        print("🔍 VERIFICACIÓN ESTRUCTURA FINAL")
        print("=" * 50)
        
        # Procesar con perfil verso
        profile_manager = ProfileManager()
        result = profile_manager.process_file(test_file, 'verso')
        
        if not result.get('success', False):
            print(f"❌ Error en procesamiento: {result.get('error', 'Desconocido')}")
            return False
        
        segments = result.get('segments', [])
        
        print(f"\n📊 ESTADÍSTICAS GENERALES:")
        print(f"   - Total de segmentos: {len(segments)}")
        
        # Buscar específicamente el Poema 13
        poema_13 = None
        for seg in segments:
            texto = seg.get('texto_segmento', '')
            if 'Poema 13' in texto:
                poema_13 = seg
                break
        
        if not poema_13:
            print("❌ Poema 13 no encontrado")
            return False
        
        print(f"\n🎯 ANÁLISIS DEL POEMA 13:")
        print("-" * 40)
        
        texto_completo = poema_13['texto_segmento']
        lineas = texto_completo.split('\n')
        
        print(f"📊 Estadísticas:")
        print(f"   - Saltos de línea: {texto_completo.count(chr(10))}")
        print(f"   - Líneas totales: {len(lineas)}")
        print(f"   - Longitud total: {len(texto_completo)} caracteres")
        
        print(f"\n📝 CONTENIDO DEL POEMA 13:")
        print("-" * 40)
        for i, linea in enumerate(lineas):
            print(f"   {i+1:2d}: {repr(linea)}")
        
        # Verificar si es realmente un poema completo
        if len(lineas) < 5:
            print(f"\n⚠️ ADVERTENCIA: El Poema 13 parece estar fragmentado")
            print(f"   - Solo tiene {len(lineas)} líneas")
            print(f"   - Se esperaban al menos 20 versos")
            
            # Buscar otros segmentos relacionados
            print(f"\n🔍 BUSCANDO OTROS FRAGMENTOS DEL POEMA 13:")
            print("-" * 40)
            
            fragmentos_encontrados = []
            for i, seg in enumerate(segments):
                texto = seg.get('texto_segmento', '')
                
                # Buscar versos típicos del Poema 13
                if any(frase in texto.lower() for frase in [
                    'atlas blanco', 'cruces de fuego', 'araña que cruzaba', 
                    'temerosa sedienta', 'crepúsculo', 'muñeca triste',
                    'cisne árbol', 'tiempo de las uvas', 'puerto desde donde'
                ]):
                    fragmentos_encontrados.append((i, texto))
                    print(f"   Fragmento {len(fragmentos_encontrados)}: Segmento #{i}")
                    print(f"      {repr(texto[:80])}...")
            
            print(f"\n📊 FRAGMENTOS ENCONTRADOS: {len(fragmentos_encontrados)}")
            
            if fragmentos_encontrados:
                print(f"\n🔧 DIAGNÓSTICO:")
                print(f"   ✅ Cada verso individual está preservado")
                print(f"   ❌ Los versos están en segmentos separados")
                print(f"   🎯 Solución: Mejorar agrupación en VerseSegmenter")
            
        else:
            print(f"\n✅ ESTRUCTURA CORRECTA:")
            print(f"   ✅ Poema completo en un solo segmento")
            print(f"   ✅ Saltos de línea preservados")
        
        # Análisis de títulos de poemas
        print(f"\n📋 ANÁLISIS DE TÍTULOS DE POEMAS:")
        print("-" * 40)
        
        titulos_poemas = []
        for i, seg in enumerate(segments):
            texto = seg.get('texto_segmento', '').strip()
            if texto.startswith('Poema ') and len(texto) < 50:
                titulos_poemas.append((i, texto))
        
        print(f"   Títulos encontrados: {len(titulos_poemas)}")
        for i, titulo in enumerate(titulos_poemas[:5]):  # Mostrar primeros 5
            print(f"   {i+1}: {repr(titulo[1])}")
        
        if len(titulos_poemas) > 5:
            print(f"   ... y {len(titulos_poemas) - 5} más")
        
        print(f"\n🎭 RESUMEN FINAL:")
        print("-" * 40)
        print(f"   📊 Total de segmentos: {len(segments)}")
        print(f"   🎵 Títulos de poemas: {len(titulos_poemas)}")
        print(f"   📏 Estructura de Poema 13: {len(lineas)} líneas")
        
        if len(lineas) < 5:
            print(f"   ❌ PROBLEMA: Fragmentación excesiva")
            print(f"   🔧 ACCIÓN: Ajustar agrupación en VerseSegmenter")
        else:
            print(f"   ✅ ÉXITO: Estructura correcta preservada")
        
        return True

if __name__ == "__main__":
    print("🧪 TEST VERIFICACIÓN ESTRUCTURA FINAL")
    print("=" * 50)
    
    test_estructura_final() 