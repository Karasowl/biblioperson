#!/usr/bin/env python3
"""Demo script for deduplication CLI.

This script demonstrates all the functionality of the deduplication CLI
by creating sample data and running various commands.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

def run_command(cmd_args, description=""):
    """Run a CLI command and display results."""
    script_path = Path(__file__).parent / "dedup.py"
    cmd = [sys.executable, str(script_path)] + cmd_args
    
    print(f"\n{'='*60}")
    if description:
        print(f"DEMO: {description}")
    print(f"Comando: python dedup.py {' '.join(cmd_args)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("Salida:")
        print(result.stdout)
    
    if result.stderr:
        print("Errores:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"⚠️  Código de salida: {result.returncode}")
    
    return result.returncode == 0

def create_demo_files():
    """Create demo files for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    
    demo_files = [
        ("novela_clasica.txt", "En un lugar de la Mancha, de cuyo nombre no quiero acordarme..."),
        ("poesia_moderna.txt", "Versos libres que danzan\nen el viento de la tarde\nsin métrica ni rima"),
        ("ensayo_filosofico.txt", "La existencia precede a la esencia, como diría Sartre..."),
        ("novela_clasica_copia.txt", "En un lugar de la Mancha, de cuyo nombre no quiero acordarme..."),  # Duplicado
        ("cuento_corto.txt", "Había una vez en un reino muy lejano..."),
    ]
    
    created_files = []
    for filename, content in demo_files:
        file_path = temp_dir / filename
        file_path.write_text(content, encoding='utf-8')
        created_files.append(file_path)
    
    return temp_dir, created_files

def populate_demo_data(demo_files):
    """Populate the database with demo data."""
    # Import here to avoid path issues
    sys.path.insert(0, str(Path(__file__).parent.parent / "processing"))
    from deduplication import get_dedup_manager
    
    dedup_manager = get_dedup_manager()
    
    titles = [
        "Don Quijote de la Mancha",
        "Poesía Contemporánea",
        "Ensayo sobre el Existencialismo",
        "Don Quijote (Copia)",
        "Cuentos Tradicionales"
    ]
    
    print("\n📁 Creando datos de demostración...")
    for file_path, title in zip(demo_files, titles):
        file_hash = dedup_manager.compute_sha256(file_path)
        if dedup_manager.register_document(file_hash, file_path, title):
            print(f"✅ Registrado: {title}")
        else:
            print(f"⚠️  Duplicado detectado: {title}")

def main():
    """Main demo function."""
    print("🎯 DEMOSTRACIÓN DEL CLI DE DEDUPLICACIÓN")
    print("="*60)
    print("Este script demuestra todas las funcionalidades del CLI de deduplicación.")
    print("Se crearán archivos de prueba y se ejecutarán varios comandos.")
    
    try:
        # Create demo files
        temp_dir, demo_files = create_demo_files()
        print(f"\n📂 Archivos de prueba creados en: {temp_dir}")
        
        # Populate database
        populate_demo_data(demo_files)
        
        # Demo 1: Show configuration
        run_command(["config"], "Mostrar configuración del sistema")
        
        # Demo 2: Show statistics
        run_command(["stats"], "Mostrar estadísticas de la base de datos")
        
        # Demo 3: List all documents
        run_command(["list"], "Listar todos los documentos")
        
        # Demo 4: List with JSON format
        run_command(["list", "--format", "json"], "Listar documentos en formato JSON")
        
        # Demo 5: Search documents
        run_command(["list", "--search", "Don"], "Buscar documentos que contengan 'Don'")
        
        # Demo 6: Limit results
        run_command(["list", "--limit", "2"], "Mostrar solo 2 documentos")
        
        # Demo 7: Show statistics with JSON
        run_command(["stats", "--format", "json"], "Estadísticas en formato JSON")
        
        # Demo 8: Show help for remove command
        run_command(["remove", "--help"], "Mostrar ayuda del comando remove")
        
        # Demo 9: Show what would be removed (dry run)
        print(f"\n{'='*60}")
        print("DEMO: Simulación de eliminación (sin ejecutar)")
        print("="*60)
        print("Los siguientes comandos eliminarían documentos:")
        print("• python dedup.py remove --hash <hash>")
        print("• python dedup.py remove --search 'Copia'")
        print("• python dedup.py prune --before 2025-01-01")
        print("• python dedup.py clear")
        print("(No ejecutados para preservar los datos de demostración)")
        
        # Final stats
        run_command(["stats"], "Estadísticas finales")
        
        print(f"\n{'='*60}")
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("="*60)
        print("El CLI de deduplicación está funcionando correctamente.")
        print("Los datos de prueba permanecen en la base de datos.")
        print("Para limpiar: python dedup.py clear --force")
        print(f"Archivos temporales: {temp_dir}")
        
        # Clean up temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"🗑️  Archivos temporales eliminados")
        
    except Exception as e:
        print(f"❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 