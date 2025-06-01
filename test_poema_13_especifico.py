#!/usr/bin/env python3
"""
TEST POEMA 13 ESPECÍFICO
========================

Analizar exactamente el contenido del Poema 13 para entender 
por qué los saltos de línea no se preservan correctamente.
"""

import sys
import os
import json
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.processing.profile_manager import ProfileManager
    
    def test_poema_13_especifico():
        """Analizar el Poema 13 específicamente"""
        
        test_file = "C:/Users/adven/Downloads/Neruda Pablo_20 Poemas De Amor Y Una Cancion Desesperada.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Archivo no encontrado: {test_file}")
            return False
        
        print("🔍 TEST POEMA 13 ESPECÍFICO")
        print("=" * 50)
        
        # Configurar ProfileManager
        profile_manager = ProfileManager()
        
        # Procesar archivo
        result = profile_manager.process_file(
            file_path=test_file,
            profile_name="verso",
            output_format="json"
        )
        
        # El resultado es directamente la lista de segmentos
        if not result:
            print("❌ No se obtuvieron segmentos")
            return False
        
        segments = result
        print(f"📊 Total de segmentos: {len(segments)}")
        
        # Buscar el Poema 13
        poema_13 = None
        for segment in segments:
            # Si es una lista, tomar el primer elemento
            if isinstance(segment, list):
                if not segment:
                    continue
                segment_data = segment[0]
            else:
                segment_data = segment
            
            # Acceder al atributo del ProcessedContentItem
            text = getattr(segment_data, 'texto_segmento', '') or getattr(segment_data, 'content', '')
            if 'Poema 13' in text and 'He ido marcando' in text:
                poema_13 = segment_data
                break
        
        if not poema_13:
            print("❌ No se encontró el Poema 13")
            return False
        
        print(f"\n📄 POEMA 13 ENCONTRADO:")
        print("-" * 40)
        
        texto = getattr(poema_13, 'texto_segmento', '') or getattr(poema_13, 'content', '')
        
        print(f"Longitud total: {len(texto)} caracteres")
        print(f"Saltos de línea: {texto.count(chr(10))} (\\n)")
        literal_newlines = texto.count('\\n')
        print(f"Saltos de línea visibles: {literal_newlines} (literal)")
        
        # Analizar línea por línea
        lines = texto.split('\n')
        print(f"Total de líneas: {len(lines)}")
        
        print(f"\nPrimeras 15 líneas del Poema 13:")
        for i, line in enumerate(lines[:15]):
            print(f"   {i+1:2d}: {repr(line)}")
        
        # ANÁLISIS ESPECÍFICO: ¿Cómo deberían verse los versos?
        print(f"\n🎯 ANÁLISIS DEL PROBLEMA:")
        print("-" * 40)
        
        # Buscar los primeros versos que sabemos que deberían estar separados
        versos_esperados = [
            "He ido marcando con cruces de fuego",
            "el atlas blanco de tu cuerpo.",
            "Mi boca era una araña que cruzaba escondiéndose.",
            "En ti, detrás de ti, temerosa, sedienta.",
        ]
        
        texto_completo = ' '.join(texto.split())  # Normalizar espacios
        
        print("Buscando versos específicos en el texto:")
        for i, verso in enumerate(versos_esperados):
            verso_normalizado = ' '.join(verso.split())
            if verso_normalizado in texto_completo:
                print(f"   ✅ Verso {i+1} encontrado: {verso}")
                
                # Buscar en qué línea está
                for j, line in enumerate(lines):
                    if verso_normalizado in ' '.join(line.split()):
                        print(f"      → En línea {j+1}: {repr(line)}")
                        break
            else:
                print(f"   ❌ Verso {i+1} NO encontrado: {verso}")
        
        # MOSTRAR COMO DEBERÍA VERSE
        print(f"\n📝 COMO DEBERÍA VERSE EL POEMA 13:")
        print("-" * 40)
        expected_format = """Poema 13

He ido marcando con cruces de fuego
el atlas blanco de tu cuerpo.
Mi boca era una araña que cruzaba escondiéndose.
En ti, detrás de ti, temerosa, sedienta.
Historias que contarte la orilla del crepúsculo,
muñeca triste dulce, para que no estuvieras triste.
Un cisne, un árbol, algo lejano alegre.
El tiempo de las uvas, el tiempo maduro frutal."""
        
        print(expected_format)
        
        print(f"\n🔍 COMO APARECE ACTUALMENTE:")
        print("-" * 40)
        print(texto[:500] + "..." if len(texto) > 500 else texto)
        
        # VERIFICAR SI EL PROBLEMA ES EN LA UNIÓN
        print(f"\n🛠️ DIAGNÓSTICO TÉCNICO:")
        print("-" * 40)
        
        # Verificar si hay múltiples líneas o si está todo en una línea
        content_lines = [line.strip() for line in lines if line.strip()]
        
        if len(content_lines) <= 3:
            print("❌ PROBLEMA: Muy pocas líneas - los versos están unidos")
            print(f"   Solo {len(content_lines)} líneas de contenido")
        elif len(content_lines) >= 15:
            print("✅ ESTRUCTURA CORRECTA: Múltiples líneas detectadas")
            print(f"   {len(content_lines)} líneas de contenido")
        else:
            print("⚠️ ESTRUCTURA INTERMEDIA: Verificar manualmente")
            print(f"   {len(content_lines)} líneas de contenido")
        
        return True
    
    if __name__ == "__main__":
        print("🧪 TEST POEMA 13 ESPECÍFICO")
        print("=" * 50)
        
        test_poema_13_especifico()
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("⚠️ Asegúrate de ejecutar desde el directorio raíz del proyecto") 