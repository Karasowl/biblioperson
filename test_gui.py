#!/usr/bin/env python3
"""
Script de prueba para verificar que la GUI de Biblioperson funciona correctamente.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Prueba que todas las importaciones necesarias funcionen."""
    try:
        print("🔍 Probando importación de PySide6...")
        import PySide6
        print(f"✅ PySide6 {PySide6.__version__} importado correctamente")
        
        print("🔍 Probando importación de la GUI...")
        from dataset.scripts.ui.main_window import BibliopersonMainWindow
        print("✅ BibliopersonMainWindow importado correctamente")
        
        print("🔍 Probando creación de la aplicación...")
        from PySide6.QtWidgets import QApplication
        app = QApplication([])
        print("✅ QApplication creado correctamente")
        
        print("🔍 Probando creación de la ventana principal...")
        window = BibliopersonMainWindow()
        print("✅ BibliopersonMainWindow creado correctamente")
        
        print("🔍 Probando configuración inicial...")
        print(f"   - Título: {window.windowTitle()}")
        print(f"   - Tamaño: {window.size().width()}x{window.size().height()}")
        print("✅ Configuración inicial correcta")
        
        # No mostramos la ventana en el test, solo verificamos que se puede crear
        app.quit()
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    """Función principal del test."""
    print("🚀 Iniciando pruebas de la GUI de Biblioperson...")
    print("=" * 50)
    
    if test_imports():
        print("=" * 50)
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("📋 La GUI está lista para usar:")
        print("   - Ejecuta: python launch_gui.py")
        print("   - O: python dataset/scripts/ui/main_window.py")
        return 0
    else:
        print("=" * 50)
        print("💥 Algunas pruebas fallaron.")
        print("🔧 Verifica que PySide6 esté instalado:")
        print("   pip install PySide6==6.6.0")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 