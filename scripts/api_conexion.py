#!/usr/bin/env python3
"""
Servidor Flask API para Biblioperson - Puente entre Frontend y Backend

Este servidor actúa como intermediario entre el frontend Next.js y las
funcionalidades existentes del sistema de procesamiento de datasets.

NO modifica la lógica existente, solo expone las funcionalidades como API REST.
"""

import sys
import os
from pathlib import Path
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from library_manager import LibraryManager

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import argparse

# Agregar el directorio raíz del proyecto al path para importar módulos existentes
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Importar funcionalidades existentes SIN MODIFICARLAS
from dataset.processing.profile_manager import ProfileManager
from dataset.scripts.process_file import core_process, ProcessingStats
from dataset.processing.dedup_api import register_dedup_api
from dataset.scripts.unify_ndjson import NDJSONUnifier

# Variables globales para el estado del procesamiento
processing_jobs = {}  # {job_id: {status, progress, stats, thread}}
job_counter = 0

app = Flask(__name__)
CORS(app)  # Permitir CORS para el frontend

# Registrar el blueprint de deduplicación existente
register_dedup_api(app)

class ProcessingJobManager:
    """Gestor de trabajos de procesamiento que usa las funciones existentes."""
    
    def __init__(self):
        self.jobs = {}
        self.job_counter = 0
        self.lock = threading.Lock()
    
    def create_job(self, job_config: Dict[str, Any]) -> str:
        """Crea un nuevo trabajo de procesamiento."""
        with self.lock:
            self.job_counter += 1
            job_id = f"job_{self.job_counter}"
            
            self.jobs[job_id] = {
                'id': job_id,
                'status': 'pending',
                'progress': 0,
                'message': 'Trabajo creado',
                'config': job_config,
                'stats': {},
                'created_at': datetime.now().isoformat(),
                'started_at': None,
                'finished_at': None,
                'thread': None
            }
            
            return job_id
    
    def start_job(self, job_id: str):
        """Inicia un trabajo de procesamiento usando core_process existente."""
        if job_id not in self.jobs:
            raise ValueError(f"Trabajo {job_id} no encontrado")
        
        job = self.jobs[job_id]
        if job['status'] != 'pending':
            raise ValueError(f"Trabajo {job_id} ya está en estado {job['status']}")
        
        # Crear hilo para ejecutar el procesamiento
        thread = threading.Thread(
            target=self._run_processing_job,
            args=(job_id,),
            daemon=True
        )
        
        job['thread'] = thread
        job['status'] = 'running'
        job['started_at'] = datetime.now().isoformat()
        job['message'] = 'Procesamiento iniciado'
        
        thread.start()
    
    def _check_cancellation(self, job_id: str) -> bool:
        """Verifica si el trabajo ha sido cancelado."""
        return self.jobs.get(job_id, {}).get('status') == 'cancelled'
    
    def _run_processing_job(self, job_id: str):
        """Ejecuta el trabajo de procesamiento automático completo."""
        job = self.jobs[job_id]
        config = job['config']
        temp_dir = None
        
        try:
            start_time = time.time()
            
            # Paso 1: Crear carpeta temporal
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 5
            job['message'] = 'Creando carpeta temporal...'
            
            import tempfile
            import shutil
            
            # Crear carpeta temporal específica para este trabajo
            temp_base = os.path.expanduser('~/AppData/Roaming/Biblioperson/temp')
            os.makedirs(temp_base, exist_ok=True)
            temp_dir = os.path.join(temp_base, job_id)
            os.makedirs(temp_dir, exist_ok=True)
            
            # Guardar temp_dir en stats para limpieza posterior
            if 'stats' not in job:
                job['stats'] = {}
            job['stats']['temp_dir'] = temp_dir
            
            job['logs'] = [f"Carpeta temporal creada: {temp_dir}"]
            
            # Paso 2: Copiar archivos a carpeta temporal
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 10
            job['message'] = 'Copiando archivos...'
            
            input_path = config['input_path']
            if os.path.isfile(input_path):
                shutil.copy2(input_path, temp_dir)
                job['logs'].append(f"Archivo copiado: {os.path.basename(input_path)}")
            elif os.path.isdir(input_path):
                for root, dirs, files in os.walk(input_path):
                    for file in files:
                        if self._check_cancellation(job_id):
                            return
                        src_file = os.path.join(root, file)
                        rel_path = os.path.relpath(src_file, input_path)
                        dst_file = os.path.join(temp_dir, rel_path)
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                job['logs'].append(f"Directorio copiado: {len(os.listdir(temp_dir))} archivos")
            
            # Paso 3: Procesar archivos a NDJSON
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 20
            job['message'] = 'Procesando archivos a NDJSON...'
            
            # Ejecutar el sistema de procesamiento existente
            import subprocess
            import sys
            
            process_script = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'scripts', 'process_file.py')
            output_file = os.path.join(temp_dir, 'processed_output.ndjson')
            
            cmd = [
                sys.executable, process_script,
                temp_dir,
                '--profile', config.get('profile', 'automático'),
                '--output', output_file,
                '--encoding', config.get('encoding', 'utf-8')
            ]
            
            if config.get('verbose'):
                cmd.append('--verbose')
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(process_script))
            
            if result.returncode != 0:
                raise Exception(f"Error en procesamiento NDJSON: {result.stderr}")
            
            job['logs'].append(f"Procesamiento NDJSON completado: {output_file}")
            
            # Paso 4: Generar embeddings
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 50
            job['message'] = 'Generando embeddings...'
            
            embedding_script = os.path.join(os.path.dirname(__file__), 'backend', 'procesar_semantica.py')
            
            cmd_embeddings = [sys.executable, embedding_script]
            
            # Agregar proveedor de embeddings si está especificado
            embedding_provider = config.get('embedding_provider', 'sentence-transformers')
            cmd_embeddings.extend(['--provider', embedding_provider])
            
            # Agregar configuración de API si es necesaria
            if embedding_provider in ['novita-ai', 'openai'] and config.get('api_keys'):
                api_config = {
                    'novita': config['api_keys'].get('novita'),
                    'openai': config['api_keys'].get('openai')
                }
                cmd_embeddings.extend(['--api-config', json.dumps(api_config)])
            
            if config.get('verbose'):
                cmd_embeddings.append('--verbose')
            
            job['logs'].append(f"Generando embeddings con proveedor: {embedding_provider}")
            
            result = subprocess.run(cmd_embeddings, capture_output=True, text=True)
            
            if result.returncode != 0:
                job['logs'].append(f"Advertencia en embeddings: {result.stderr}")
            else:
                job['logs'].append("Embeddings generados exitosamente")
            
            # Paso 5: Indexar en MeiliSearch
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 75
            job['message'] = 'Indexando en MeiliSearch...'
            
            meilisearch_script = os.path.join(os.path.dirname(__file__), 'backend', 'indexar_meilisearch.py')
            
            cmd_meilisearch = [sys.executable, meilisearch_script, '--indexar-nuevos']
            if config.get('verbose'):
                cmd_meilisearch.append('--verbose')
            
            result = subprocess.run(cmd_meilisearch, capture_output=True, text=True)
            
            if result.returncode != 0:
                job['logs'].append(f"Advertencia en MeiliSearch: {result.stderr}")
            else:
                job['logs'].append("Indexación en MeiliSearch completada")
            
            # Paso 6: Guardar en biblioteca
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 85
            job['message'] = 'Guardando en biblioteca...'
            
            try:
                library_manager = LibraryManager()
                documents_saved = library_manager.save_documents_from_ndjson(output_file, job_id)
                job['logs'].append(f"Documentos guardados en biblioteca: {documents_saved}")
                job['stats']['documents_saved'] = documents_saved
            except Exception as e:
                job['logs'].append(f"Advertencia al guardar en biblioteca: {str(e)}")
                job['stats']['documents_saved'] = 0
            
            # Paso 7: Limpiar archivos temporales
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 95
            job['message'] = 'Limpiando archivos temporales...'
            
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                job['logs'].append("Archivos temporales eliminados")
            
            # Completar trabajo
            end_time = time.time()
            total_time = end_time - start_time
            
            job['progress'] = 100
            job['status'] = 'completed'
            job['message'] = 'Procesamiento automático completado exitosamente'
            job['finished_at'] = datetime.now().isoformat()
            job['stats'].update({
                'total_time': f"{total_time:.2f}s",
                'steps_completed': 7,
                'processing_successful': True
            })
            
        except Exception as e:
            # Limpiar en caso de error
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            
            job['status'] = 'error'
            job['message'] = f'Error en procesamiento automático: {str(e)}'
            job['finished_at'] = datetime.now().isoformat()
            
            if 'logs' not in job:
                job['logs'] = []
            job['logs'].append(f"Error: {str(e)}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obtiene el estado de un trabajo."""
        if job_id not in self.jobs:
            raise ValueError(f"Trabajo {job_id} no encontrado")
        
        job = self.jobs[job_id].copy()
        # Remover el thread del resultado (no es serializable)
        job.pop('thread', None)
        return job
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancela un trabajo en ejecución."""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        # Solo se pueden cancelar trabajos en progreso
        if job['status'] != 'running':
            return False
        
        try:
            # Marcar el trabajo como cancelado
            job['status'] = 'cancelled'
            job['message'] = 'Trabajo cancelado por el usuario'
            job['finished_at'] = datetime.now().isoformat()
            
            # Agregar log de cancelación
            if 'logs' not in job:
                job['logs'] = []
            job['logs'].append(f"Trabajo cancelado manualmente a las {datetime.now().strftime('%H:%M:%S')}")
            
            # Intentar limpiar archivos temporales si existen
            if 'temp_dir' in job.get('stats', {}):
                temp_dir = job['stats']['temp_dir']
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        import shutil
                        shutil.rmtree(temp_dir)
                        job['logs'].append("Archivos temporales limpiados tras cancelación")
                    except Exception as e:
                        job['logs'].append(f"Error limpiando archivos temporales: {str(e)}")
            
            return True
            
        except Exception as e:
            job['logs'].append(f"Error durante cancelación: {str(e)}")
            return False
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """Lista todos los trabajos."""
        jobs = []
        for job in self.jobs.values():
            job_copy = job.copy()
            job_copy.pop('thread', None)
            jobs.append(job_copy)
        return jobs

# Instancia global del gestor de trabajos
job_manager = ProcessingJobManager()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de salud del servidor."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """Obtiene la lista de perfiles disponibles usando ProfileManager existente."""
    try:
        manager = ProfileManager()
        profiles = manager.list_profiles()
        return jsonify({
            'success': True,
            'profiles': profiles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/profiles/<profile_name>', methods=['GET'])
def get_profile(profile_name):
    """Obtiene detalles de un perfil específico."""
    try:
        manager = ProfileManager()
        profile = manager.get_profile(profile_name)
        if profile:
            return jsonify({
                'success': True,
                'profile': profile
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Perfil no encontrado'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/processing/start', methods=['POST'])
def start_processing():
    """Inicia un trabajo de procesamiento."""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('input_path'):
            return jsonify({
                'success': False,
                'error': 'input_path es requerido'
            }), 400
        
        # Crear trabajo
        job_id = job_manager.create_job(data)
        
        # Iniciar procesamiento
        job_manager.start_job(job_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Procesamiento iniciado'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/processing/status/<job_id>', methods=['GET'])
def get_processing_status(job_id):
    """Obtiene el estado de un trabajo de procesamiento."""
    try:
        status = job_manager.get_job_status(job_id)
        return jsonify({
            'success': True,
            'job': status
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancela un trabajo en ejecución."""
    try:
        success = job_manager.cancel_job(job_id)
        if success:
            return jsonify({'message': 'Trabajo cancelado exitosamente'})
        else:
            return jsonify({'error': 'No se pudo cancelar el trabajo o no existe'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing/jobs', methods=['GET'])
def list_processing_jobs():
    """Lista todos los trabajos de procesamiento."""
    try:
        jobs = job_manager.list_jobs()
        return jsonify({
            'success': True,
            'jobs': jobs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/browse', methods=['GET'])
def browse_files():
    """Explora archivos y directorios."""
    try:
        path = request.args.get('path', '.')
        path_obj = Path(path)
        
        if not path_obj.exists():
            return jsonify({
                'success': False,
                'error': 'Ruta no encontrada'
            }), 404
        
        items = []
        if path_obj.is_dir():
            for item in path_obj.iterdir():
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'is_directory': item.is_dir(),
                    'size': item.stat().st_size if item.is_file() else None
                })
        
        return jsonify({
            'success': True,
            'path': str(path_obj),
            'items': sorted(items, key=lambda x: (not x['is_directory'], x['name']))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/library/documents', methods=['GET'])
def get_library_documents():
    """Obtiene documentos de la biblioteca."""
    try:
        library_manager = LibraryManager()
        
        # Parámetros de consulta
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search')
        
        # Obtener documentos
        documents = library_manager.get_documents(limit=limit, offset=offset, search=search)
        
        # Obtener estadísticas
        stats = library_manager.get_library_stats()
        
        return jsonify({
            'success': True,
            'documents': documents,
            'stats': stats,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': stats['total_documents']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/library/documents/<int:doc_id>', methods=['GET'])
def get_library_document(doc_id):
    """Obtiene un documento específico de la biblioteca."""
    try:
        library_manager = LibraryManager()
        document = library_manager.get_document_by_id(doc_id)
        
        if not document:
            return jsonify({
                'success': False,
                'error': 'Documento no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'document': document
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/library/stats', methods=['GET'])
def get_library_stats():
    """Obtiene estadísticas de la biblioteca."""
    try:
        library_manager = LibraryManager()
        stats = library_manager.get_library_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/library/documents/<int:doc_id>', methods=['DELETE'])
def delete_library_document(doc_id):
    """Elimina un documento de la biblioteca."""
    try:
        library_manager = LibraryManager()
        success = library_manager.delete_document(doc_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Documento no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Documento eliminado exitosamente'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask API para Biblioperson...")
    print("📁 Sistema de dataset: PRESERVADO (sin modificaciones)")
    print("🔗 Funcionalidad: Puente API entre frontend y backend existente")
    print("")
    print("Endpoints disponibles:")
    print("  GET  /api/health - Estado del servidor")
    print("  GET  /api/profiles - Lista de perfiles")
    print("  GET  /api/profiles/<name> - Detalles de perfil")
    print("  POST /api/processing/start - Iniciar procesamiento")
    print("  GET  /api/processing/status/<job_id> - Estado de trabajo")
    print("  GET  /api/processing/jobs - Lista de trabajos")
    print("  POST /api/jobs/<job_id>/cancel - Cancelar trabajo")
    print("  GET  /api/files/browse - Explorar archivos")
    print("  GET  /api/library/documents - Obtener documentos de biblioteca")
    print("  GET  /api/library/documents/<id> - Obtener documento específico")
    print("  GET  /api/library/stats - Estadísticas de biblioteca")
    print("  DELETE /api/library/documents/<id> - Eliminar documento")
    print("  [Deduplicación] /dedup/* - Endpoints de deduplicación existentes")
    print("")
    print("💾 Base de datos: SQLite (library.db)")
    print("🔍 Búsqueda: MeiliSearch + Biblioteca local")
    print("")
    
    # Configuración del servidor
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Servidor ejecutándose en: http://localhost:{port}")
    print(f"🔧 Modo debug: {debug}")
    print("")
    print("Para detener el servidor: Ctrl+C")
    
    app.run(host='0.0.0.0', port=port, debug=debug)