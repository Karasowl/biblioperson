#!/usr/bin/env python3
"""
Script de lanzamiento para la interfaz gráfica de Biblioperson.

Este script permite ejecutar la GUI desde la raíz del proyecto.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path de Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dataset.scripts.ui.main_window import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Error al importar la interfaz gráfica: {e}")
    print("Asegúrate de que PySide6 esté instalado:")
    print("pip install PySide6")
    sys.exit(1)
except Exception as e:
    print(f"Error al ejecutar la aplicación: {e}")
    sys.exit(1) 