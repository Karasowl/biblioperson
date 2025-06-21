#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas de importación en api_conexion.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Configurar el path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

def log_result(message, log_file):
    """Escribir resultado al archivo de log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def test_import(module_name, import_statement, log_file):
    """Probar una importación específica"""
    try:
        exec(import_statement)
        log_result(f"✅ SUCCESS: {module_name} - {import_statement}", log_file)
        return True
    except Exception as e:
        log_result(f"❌ FAILED: {module_name} - {import_statement}", log_file)
        log_result(f"   Error: {str(e)}", log_file)
        return False

def main():
    log_file = "backend_diagnosis.log"
    
    # Limpiar log anterior
    if os.path.exists(log_file):
        os.remove(log_file)
    
    log_result("=== DIAGNÓSTICO DEL BACKEND BIBLIOPERSON ===", log_file)
    log_result(f"Python version: {sys.version}", log_file)
    log_result(f"Working directory: {os.getcwd()}", log_file)
    log_result(f"Project root: {project_root}", log_file)
    log_result("", log_file)
    
    # Lista de importaciones a probar (en el orden que aparecen en api_conexion.py)
    imports_to_test = [
        ("sys", "import sys"),
        ("os", "import os"),
        ("pathlib", "from pathlib import Path"),
        ("json", "import json"),
        ("threading", "import threading"),
        ("time", "import time"),
        ("datetime", "from datetime import datetime"),
        ("typing", "from typing import Dict, Any, Optional, List"),
        ("flask", "from flask import Flask, request, jsonify, send_file"),
        ("flask_cors", "from flask_cors import CORS"),
        ("argparse", "import argparse"),
        ("library_manager", "from scripts.library_manager import LibraryManager"),
        ("ProfileManager", "from dataset.processing.profile_manager import ProfileManager"),
        ("process_file", "from dataset.scripts.process_file import core_process, ProcessingStats"),
        ("dedup_api", "from dataset.processing.dedup_api import register_dedup_api"),
        ("unify_ndjson", "from dataset.scripts.unify_ndjson import NDJSONUnifier"),
    ]
    
    success_count = 0
    total_count = len(imports_to_test)
    
    log_result("=== PROBANDO IMPORTACIONES ===", log_file)
    
    for module_name, import_statement in imports_to_test:
        if test_import(module_name, import_statement, log_file):
            success_count += 1
        log_result("", log_file)
    
    log_result("=== RESUMEN ===", log_file)
    log_result(f"Importaciones exitosas: {success_count}/{total_count}", log_file)
    
    if success_count == total_count:
        log_result("✅ Todas las importaciones funcionan. El problema puede estar en otro lugar.", log_file)
        
        # Probar Flask básico
        log_result("", log_file)
        log_result("=== PROBANDO FLASK BÁSICO ===", log_file)
        try:
            from flask import Flask
            app = Flask(__name__)
            
            @app.route('/test')
            def test():
                return 'Flask funciona'
            
            log_result("✅ Flask básico configurado correctamente", log_file)
            log_result("Problema puede estar en la lógica de inicio del servidor", log_file)
        except Exception as e:
            log_result(f"❌ Error en Flask básico: {str(e)}", log_file)
    else:
        log_result(f"❌ {total_count - success_count} importaciones fallaron. Revisar dependencias.", log_file)
    
    log_result("", log_file)
    log_result(f"Diagnóstico completo guardado en: {log_file}", log_file)

if __name__ == '__main__':
    main()