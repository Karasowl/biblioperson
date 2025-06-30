#!/usr/bin/env python3
"""
Script para actualizar a all-mpnet-base-v2 (modelo más potente)
"""

import os
import shutil
import sqlite3
import subprocess
import sys

def check_requirements():
    """Verificar que sentence-transformers esté instalado"""
    try:
        import sentence_transformers
        print("✅ sentence-transformers disponible")
        return True
    except ImportError:
        print("❌ Instalando sentence-transformers...")
        subprocess.run([sys.executable, "-m", "pip", "install", "sentence-transformers"])
        return True

def backup_database():
    """Hacer backup de la base de datos"""
    source = "data.ms/documents.db"
    backup = "data.ms/documents.db.backup"
    
    if os.path.exists(source):
        shutil.copy2(source, backup)
        print(f"✅ Backup creado: {backup}")
        return True
    else:
        print(f"⚠️ Base de datos no encontrada: {source}")
        return False

def clean_existing_embeddings():
    """Limpiar embeddings existentes"""
    db_path = "data.ms/documents.db"
    
    if not os.path.exists(db_path):
        print("⚠️ Base de datos no encontrada")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si existe tabla embeddings
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='embeddings'
        """)
        
        if cursor.fetchone():
            cursor.execute("DROP TABLE embeddings")
            print("✅ Embeddings anteriores eliminados")
        else:
            print("ℹ️ No había embeddings anteriores")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando embeddings: {e}")
        return False

def setup_processing_database():
    """Configurar base de datos para procesamiento"""
    # Crear directorio
    os.makedirs("dataset/data", exist_ok=True)
    
    # Copiar base de datos
    source = "data.ms/documents.db"
    target = "dataset/data/biblioperson.db"
    
    if os.path.exists(source):
        shutil.copy2(source, target)
        print(f"✅ Base de datos copiada a {target}")
        return True
    else:
        print(f"❌ No se pudo copiar {source}")
        return False

def generate_embeddings():
    """Generar embeddings con el modelo potente"""
    print("\n🚀 Generando embeddings con all-mpnet-base-v2...")
    print("⏳ Primera vez descargará ~1.1GB (modelo)")
    print("⏳ Procesamiento tomará 5-10 minutos...")
    
    cmd = [
        sys.executable,
        "scripts/backend/procesar_semantica.py",
        "--model=all-mpnet-base-v2",
        "--provider=sentence-transformers",
        "--batch-size=16",
        "--verbose"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Embeddings generados exitosamente")
            print("📊 Output:", result.stdout[-500:])  # Últimas 500 chars
            return True
        else:
            print("❌ Error generando embeddings:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando script: {e}")
        return False

def copy_back_database():
    """Copiar base de datos actualizada de vuelta"""
    source = "dataset/data/biblioperson.db"
    target = "data.ms/documents.db"
    
    if os.path.exists(source):
        shutil.copy2(source, target)
        print(f"✅ Base de datos actualizada copiada a {target}")
        return True
    else:
        print(f"❌ No se encontró {source}")
        return False

def verify_embeddings():
    """Verificar que los embeddings se generaron correctamente"""
    db_path = "data.ms/documents.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT model FROM embeddings LIMIT 1")
        model = cursor.fetchone()
        
        conn.close()
        
        if count > 0:
            print(f"✅ {count} embeddings generados")
            print(f"🤖 Modelo: {model[0] if model else 'Desconocido'}")
            return True
        else:
            print("❌ No se encontraron embeddings")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando embeddings: {e}")
        return False

def main():
    """Proceso completo de actualización"""
    print("🚀 ACTUALIZACIÓN A MODELO POTENTE: all-mpnet-base-v2")
    print("=" * 60)
    
    steps = [
        ("Verificar dependencias", check_requirements),
        ("Hacer backup", backup_database),
        ("Limpiar embeddings anteriores", clean_existing_embeddings),
        ("Configurar BD para procesamiento", setup_processing_database),
        ("Generar embeddings (esto toma tiempo)", generate_embeddings),
        ("Copiar BD actualizada", copy_back_database),
        ("Verificar resultado", verify_embeddings)
    ]
    
    for i, (description, func) in enumerate(steps, 1):
        print(f"\n📋 Paso {i}/7: {description}")
        if not func():
            print(f"❌ Falló en paso {i}: {description}")
            print("\n🔧 Solución manual:")
            print("1. Verificar que el backend esté corriendo")
            print("2. Verificar que sentence-transformers esté instalado")
            print("3. Verificar espacio en disco (necesita ~2GB)")
            return False
    
    print("\n🎉 ¡ACTUALIZACIÓN COMPLETADA!")
    print("\n📋 Próximos pasos:")
    print("1. Reiniciar el backend (Ctrl+C y volver a ejecutar)")
    print("2. Abrir http://localhost:11986")
    print("3. Ir a Biblioteca → Advanced Search")
    print("4. Probar búsqueda semántica: 'amor que trasciende la muerte'")
    print("\n⚡ El modelo potente dará resultados mucho más precisos!")

if __name__ == "__main__":
    main() 