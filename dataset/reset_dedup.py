#!/usr/bin/env python3
"""Script para resetear la instancia global del dedup manager."""

import processing.deduplication as dedup_module

def main():
    print(f"Instancia global antes: {dedup_module._global_dedup_manager}")
    dedup_module._global_dedup_manager = None
    print(f"Instancia global después: {dedup_module._global_dedup_manager}")
    
    # Probar que ahora usa la configuración
    manager = dedup_module.get_dedup_manager()
    print(f"Nueva instancia con ruta: {manager.db_path}")

if __name__ == "__main__":
    main() 