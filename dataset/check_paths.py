#!/usr/bin/env python3
"""Script para verificar las rutas desde diferentes contextos."""

import sys
from pathlib import Path

print(f"Directorio actual: {Path.cwd()}")
print(f"Directorio del script: {Path(__file__).parent}")

# Probar importación relativa
try:
    from processing.dedup_config import DedupConfigManager
    config = DedupConfigManager()
    print(f"Ruta con importación relativa: {config.get_database_path()}")
except Exception as e:
    print(f"Error con importación relativa: {e}")

# Probar importación directa
try:
    sys.path.insert(0, str(Path(__file__).parent / "processing"))
    from dedup_config import DedupConfigManager as DirectConfig
    config2 = DirectConfig()
    print(f"Ruta con importación directa: {config2.get_database_path()}")
except Exception as e:
    print(f"Error con importación directa: {e}") 