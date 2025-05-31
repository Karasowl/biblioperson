#!/usr/bin/env python3
"""
Script para debuggear por qué no se está creando el archivo de salida
a pesar de que el procesamiento dice ser exitoso
"""

import os
import sys
import json
from pathlib import Path

def debug_escritura_archivo():
    """Debuggear el problema de escritura de archivo"""
    
    print("🔍 DEBUGGING ESCRITURA DE ARCHIVO")
    print("=" * 50)
    
    # Verificar la ruta de salida reportada
    output_path = r"C:\Users\adven\Downloads\New folder (13)\fff.ndjson"
    
    print(f"🎯 Ruta objetivo: {output_path}")
    
    # Verificar si el directorio existe
    directory = os.path.dirname(output_path)
    print(f"📁 Directorio padre: {directory}")
    print(f"📁 ¿Directorio existe?: {os.path.exists(directory)}")
    
    if not os.path.exists(directory):
        print("❌ ¡EL DIRECTORIO NO EXISTE!")
        print("💡 Creando directorio...")
        try:
            os.makedirs(directory, exist_ok=True)
            print("✅ Directorio creado exitosamente")
        except Exception as e:
            print(f"❌ Error creando directorio: {e}")
            return
    
    # Verificar si el archivo existe
    print(f"📄 ¿Archivo existe?: {os.path.exists(output_path)}")
    
    # Verificar permisos de escritura
    try:
        # Intentar crear un archivo de prueba
        test_file = os.path.join(directory, "test_write.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Permisos de escritura: OK")
    except Exception as e:
        print(f"❌ Error de permisos: {e}")
    
    # Buscar archivos similares en el directorio
    if os.path.exists(directory):
        files = os.listdir(directory)
        print(f"📋 Archivos en directorio ({len(files)}):")
        for file in files:
            print(f"   - {file}")
    
    # Buscar archivos .ndjson en directorios comunes
    common_dirs = [
        r"C:\Users\adven\Downloads",
        r"C:\Users\adven\Desktop", 
        r"C:\Users\adven\OneDrive\Desktop",
        ".",  # directorio actual
        "dataset/output",
    ]
    
    print("\n🔍 BUSCANDO ARCHIVOS .ndjson EN DIRECTORIOS COMUNES:")
    for dir_path in common_dirs:
        if os.path.exists(dir_path):
            try:
                ndjson_files = [f for f in os.listdir(dir_path) if f.endswith('.ndjson')]
                if ndjson_files:
                    print(f"📁 {dir_path}:")
                    for file in ndjson_files:
                        full_path = os.path.join(dir_path, file)
                        size = os.path.getsize(full_path)
                        print(f"   - {file} ({size} bytes)")
            except Exception as e:
                pass
    
    # Probar escritura de archivo de prueba
    print("\n🧪 PRUEBA DE ESCRITURA:")
    try:
        test_data = {
            "id_segmento": "test-123",
            "texto_segmento": "Esto es una prueba",
            "tipo_segmento": "test"
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(test_data, ensure_ascii=False) + '\n')
        
        print(f"✅ Archivo de prueba creado: {output_path}")
        print(f"📊 Tamaño: {os.path.getsize(output_path)} bytes")
        
        # Leer de vuelta para verificar
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"📄 Contenido: {content[:100]}...")
        
    except Exception as e:
        print(f"❌ Error en prueba de escritura: {e}")

if __name__ == "__main__":
    debug_escritura_archivo() 