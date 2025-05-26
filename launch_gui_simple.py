#!/usr/bin/env python3
"""
Script de lanzamiento para la versión simplificada de Biblioperson GUI.

Esta versión elimina los widgets problemáticos y mantiene solo la funcionalidad esencial.
"""

import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Agregar el directorio del proyecto al path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from dataset.scripts.ui.main_window_simple import main
    
    if __name__ == "__main__":
        print("🚀 Iniciando Biblioperson GUI (Versión Simplificada)...")
        print("Esta versión elimina los widgets problemáticos y mantiene solo la funcionalidad esencial.")
        print("Para funcionalidad completa con overrides, usa la línea de comandos.")
        print()
        main()
        
except ImportError as e:
    print(f"❌ Error al importar la aplicación: {e}")
    print("Asegúrate de que todas las dependencias estén instaladas.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    sys.exit(1) 