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
import sqlite3
import logging

from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import argparse
import subprocess
import requests
import atexit
import signal
import tarfile
from urllib.parse import urlparse

# Agregar el directorio raíz del proyecto al path para importar módulos existentes
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Importar funcionalidades existentes SIN MODIFICARLAS
from dataset.processing.profile_manager import ProfileManager
from dataset.scripts.process_file import core_process, ProcessingStats
from dataset.processing.dedup_api import register_dedup_api
from dataset.scripts.unify_ndjson import NDJSONUnifier
from dataset.processing.deduplication import DeduplicationManager

# Variables globales para el estado del procesamiento
processing_jobs = {}  # {job_id: {status, progress, stats, thread}}
job_counter = 0

# Configuración de base de datos
DATABASE_PATH = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Biblioperson', 'library.db')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir CORS para el frontend

# Registrar el blueprint de deduplicación existente
register_dedup_api(app)

# Asegurar salida UTF-8 en Windows para permitir emojis en consola
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Para versiones de Python <3.7 donde reconfigure no existe
        import io, msvcrt
        sys.stdout = io.TextIOWrapper(msvcrt.get_osfhandle(sys.stdout.fileno()), encoding="utf-8", buffering=1)
        sys.stderr = io.TextIOWrapper(msvcrt.get_osfhandle(sys.stderr.fileno()), encoding="utf-8", buffering=1)

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
            
            # Debug: Verificar configuración recibida
            job['logs'].append(f"Configuración recibida: {config}")
            
            # Paso 2: Copiar archivos a carpeta temporal
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 10
            job['message'] = 'Copiando archivos...'
            
            input_path = config.get('input_path')
            if not input_path:
                raise Exception("No se especificó input_path en la configuración")
            
            job['logs'].append(f"Ruta de entrada: {input_path}")
            
            if not os.path.exists(input_path):
                raise Exception(f"La ruta especificada no existe: {input_path}")
            
            if os.path.isfile(input_path):
                shutil.copy2(input_path, temp_dir)
                job['logs'].append(f"Archivo copiado: {os.path.basename(input_path)}")
            elif os.path.isdir(input_path):
                files_copied = 0
                for root, dirs, files in os.walk(input_path):
                    for file in files:
                        if self._check_cancellation(job_id):
                            return
                        src_file = os.path.join(root, file)
                        rel_path = os.path.relpath(src_file, input_path)
                        dst_file = os.path.join(temp_dir, rel_path)
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        files_copied += 1
                job['logs'].append(f"Directorio copiado: {files_copied} archivos")
                
                # Verificar que se copiaron archivos
                temp_files = os.listdir(temp_dir)
                job['logs'].append(f"Archivos en directorio temporal: {temp_files}")
            else:
                raise Exception(f"La ruta no es ni archivo ni directorio: {input_path}")
            
            # Paso 3: Procesar archivos a NDJSON
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 20
            job['message'] = 'Procesando archivos a NDJSON...'
            
            # Ejecutar el sistema de procesamiento existente
            import subprocess
            import sys
            
            process_script = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'scripts', 'process_file.py')
            
            # Obtener perfil con validación y corrección
            profile = config.get('profile', 'prosa')
            
            # Corregir perfil automático (frontend envía 'auto' o 'automatico', sistema espera 'automático')
            if profile in ['auto', 'automatico']:
                profile = 'automático'
                job['logs'].append(f"Perfil corregido de '{config.get('profile')}' a '{profile}'")
            
            job['logs'].append(f"Perfil configurado: '{profile}'")
            
            # Decidir si la entrada es directorio o archivo
            is_dir_mode = os.path.isdir(temp_dir)

            if is_dir_mode:
                # Cuando procesamos un directorio, pasamos --output como directorio para que process_file genere NDJSONs dentro
                output_file = None  # Se determinará luego buscándolo en temp_dir
            else:
                output_file = os.path.join(temp_dir, 'processed_output.ndjson')
            
            cmd = [
                sys.executable, '-X', 'utf8', process_script,
                temp_dir,
                '--profile', profile,
            ]

            if is_dir_mode:
                # Salida como directorio
                cmd.extend(['--output', temp_dir])
            else:
                cmd.extend(['--output', output_file])
            
            cmd.extend([
                '--encoding', config.get('encoding', 'utf-8'),
                '--verbose'  # Siempre usar verbose para debug
            ])
            
            job['logs'].append(f"Comando a ejecutar: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=os.path.dirname(process_script), env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            
            # Agregar logs de debug para diagnosticar el problema
            job['logs'].append(f"Return code: {result.returncode}")
            job['logs'].append(f"STDOUT: {result.stdout}")
            if result.stderr:
                job['logs'].append(f"STDERR: {result.stderr}")
            
            if result.returncode != 0:
                raise Exception(f"Error en procesamiento NDJSON: {result.stderr}")
            
            # Verificar si el archivo realmente se generó
            if output_file and os.path.exists(output_file):
                job['logs'].append(f"Procesamiento NDJSON completado: {output_file}")
            else:
                job['logs'].append(f"ADVERTENCIA: El archivo NDJSON no se generó en la ruta esperada: {output_file if output_file else temp_dir}")
                # Buscar archivos NDJSON en el directorio temporal
                ndjson_files = [f for f in os.listdir(temp_dir) if f.endswith('.ndjson')]
                if ndjson_files:
                    job['logs'].append(f"Archivos NDJSON encontrados en temp_dir: {ndjson_files}")
                    # Usar el primer archivo encontrado
                    output_file = os.path.join(temp_dir, ndjson_files[0])
                    job['logs'].append(f"Usando archivo: {output_file}")
                else:
                    job['logs'].append("No se encontraron archivos NDJSON en el directorio temporal")
            
            # Paso 4: Generar embeddings
            if self._check_cancellation(job_id):
                return
            
            job['progress'] = 50
            job['message'] = 'Generando embeddings...'
            
            embedding_script = os.path.join(os.path.dirname(__file__), 'backend', 'procesar_semantica.py')
            
            cmd_embeddings = [sys.executable, '-X', 'utf8', embedding_script]
            
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
            
            result = subprocess.run(cmd_embeddings, capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            
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
            
            cmd_meilisearch = [sys.executable, '-X', 'utf8', meilisearch_script, '--indexar-nuevos']
            if config.get('verbose'):
                cmd_meilisearch.append('--verbose')
            
            result = subprocess.run(cmd_meilisearch, capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            
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
            
            # Limpiar directorio temporal de archivos subidos si existe
            temp_upload_dir = config.get('temp_upload_dir')
            if temp_upload_dir and os.path.exists(temp_upload_dir):
                shutil.rmtree(temp_upload_dir, ignore_errors=True)
                job['logs'].append("Archivos subidos temporales eliminados")
            
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
            
            # Limpiar directorio temporal de archivos subidos si existe
            temp_upload_dir = config.get('temp_upload_dir')
            if temp_upload_dir and os.path.exists(temp_upload_dir):
                try:
                    shutil.rmtree(temp_upload_dir)
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

# === NUEVOS ENDPOINTS DEDUPLICACIÓN ===

dedup_manager = DeduplicationManager()

@app.route("/api/dedup/duplicates", methods=["GET"])
def api_list_duplicates():
    """Devuelve la lista de documentos registrados en el deduplicador."""
    search = request.args.get("search") or None
    before = request.args.get("before") or None
    after = request.args.get("after") or None
    limit = request.args.get("limit", type=int) or 100

    docs = dedup_manager.list_documents(search=search, before=before, after=after, limit=limit)
    return jsonify({"success": True, "duplicates": docs})

@app.route("/api/dedup/<string:file_hash>", methods=["DELETE"])
def api_delete_duplicate(file_hash: str):
    """Elimina un registro del deduplicador por hash."""
    removed = dedup_manager.remove_by_hash(file_hash)
    if not removed:
        return jsonify({"success": False, "error": "Hash no encontrado"}), 404
    return jsonify({"success": True, "message": "Registro eliminado"})

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

@app.route('/api/processing/start-with-files', methods=['POST'])
def start_processing_with_files():
    """Inicia un trabajo de procesamiento con archivos enviados desde el navegador."""
    try:
        # Obtener configuración del FormData
        config_json = request.form.get('config')
        if not config_json:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó configuración'
            }), 400
        
        import json
        config = json.loads(config_json)
        
        # Obtener archivos enviados
        files = request.files.getlist('files')
        if not files:
            return jsonify({
                'success': False,
                'error': 'No se enviaron archivos'
            }), 400
        
        # Crear directorio temporal para los archivos
        import tempfile
        temp_upload_dir = tempfile.mkdtemp(prefix='biblioperson_upload_')
        
        # Guardar archivos en el directorio temporal
        saved_files = []
        for file in files:
            if file.filename:
                safe_filename = file.filename.replace('..', '').replace('/', '_').replace('\\', '_')
                file_path = os.path.join(temp_upload_dir, safe_filename)
                file.save(file_path)
                saved_files.append(file_path)
        
        if not saved_files:
            return jsonify({
                'success': False,
                'error': 'No se pudieron guardar los archivos'
            }), 400
        
        # Modificar configuración para usar el directorio temporal
        config['input_path'] = temp_upload_dir
        config['temp_upload_dir'] = temp_upload_dir  # Para limpieza posterior
        
        # Crear trabajo
        job_id = job_manager.create_job(config)
        
        # Iniciar procesamiento
        job_manager.start_job(job_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Procesamiento iniciado exitosamente con {len(saved_files)} archivo(s)'
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


@app.route('/api/documents/<string:doc_id>/segments', methods=['GET'])
def get_document_segments(doc_id):
    """Obtiene todos los segmentos de un documento específico."""
    try:
        # Primero intentar buscar en la base de datos de segments (process_and_import)
        segments_db_path = os.path.join(project_root, 'data.ms', 'documents.db')
        
        if os.path.exists(segments_db_path):
            try:
                with sqlite3.connect(segments_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    # Buscar segmentos en la tabla segments
                    cursor = conn.execute('''
                        SELECT * FROM segments 
                        WHERE document_id = ?
                        ORDER BY segment_order ASC
                    ''', (doc_id,))
                    
                    segments_rows = cursor.fetchall()
                    
                    if segments_rows:
                        # Obtener información del documento
                        doc_cursor = conn.execute('''
                            SELECT * FROM documents WHERE id = ?
                        ''', (doc_id,))
                        doc_info = doc_cursor.fetchone()
                        
                        segments = []
                        for row in segments_rows:
                            # Parsear metadata
                            metadata = {}
                            if row['metadata']:
                                try:
                                    metadata = json.loads(row['metadata'])
                                except:
                                    metadata = {}
                            
                            segment = {
                                'id': row['id'],
                                'doc_id': row['document_id'],
                                'segment_id': row['id'],
                                'text': row['text'],
                                'type': row['segment_type'] or 'text',
                                'segment_order': row['segment_order'],
                                'text_length': row['text_length'],
                                'document_title': doc_info['title'] if doc_info else 'Unknown',
                                'document_author': doc_info['author'] if doc_info else 'Unknown',
                                'document_language': doc_info['language'] if doc_info else 'unknown',
                                'original_page': row['original_page'],
                                'metadata': metadata,
                                'processing_timestamp': row['created_at']
                            }
                            segments.append(segment)
                        
                        return jsonify({
                            'segments': segments,
                            'total': len(segments),
                            'title': doc_info['title'] if doc_info else 'Unknown',
                            'author': doc_info['author'] if doc_info else 'Unknown',
                            'language': doc_info['language'] if doc_info else 'unknown'
                        })
            except Exception as e:
                logger.warning(f"Error reading from segments DB: {str(e)}")
        
        # Si no se encontró en segments DB, intentar con library DB
        library_db_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Biblioperson', 'library.db')
        
        with sqlite3.connect(library_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Obtener el documento
            cursor = conn.execute('''
                SELECT * FROM documents WHERE id = ?
            ''', (doc_id,))
            
            doc = cursor.fetchone()
            if not doc:
                return jsonify({'error': 'Document not found'}), 404
            
            # Parsear metadatos
            metadata = {}
            if doc['metadata']:
                try:
                    metadata = json.loads(doc['metadata'])
                except:
                    metadata = {}
            
            # Dividir el contenido completo en segmentos para simular la estructura esperada
            full_content = doc['full_content'] or ''
            
            # Dividir por párrafos dobles (esto es una aproximación)
            paragraphs = [p.strip() for p in full_content.split('\n\n') if p.strip()]
            
            segments = []
            for i, paragraph in enumerate(paragraphs):
                segment = {
                    'id': i + 1,
                    'doc_id': doc_id,
                    'segment_id': f"{doc_id}_{i+1}",
                    'text': paragraph,
                    'type': 'paragraph',
                    'segment_order': i,
                    'text_length': len(paragraph),
                    'document_title': doc['title'],
                    'document_author': doc['author'],
                    'document_language': doc['language'],
                    'original_page': None,  # No tenemos páginas originales en library DB
                    'metadata': {
                        'source_file': doc['source_file'],
                        'processed_date': doc['processed_date'],
                        **metadata
                    },
                    'processing_timestamp': doc['processed_date']
                }
                segments.append(segment)
            
            # Si no hay párrafos, crear un solo segmento con todo el contenido
            if not segments and full_content:
                segments = [{
                    'id': 1,
                    'doc_id': doc_id,
                    'segment_id': f"{doc_id}_1",
                    'text': full_content,
                    'type': 'document',
                    'segment_order': 0,
                    'text_length': len(full_content),
                    'document_title': doc['title'],
                    'document_author': doc['author'],
                    'document_language': doc['language'],
                    'original_page': None,
                    'metadata': {
                        'source_file': doc['source_file'],
                        'processed_date': doc['processed_date'],
                        **metadata
                    },
                    'processing_timestamp': doc['processed_date']
                }]
            
            return jsonify({
                'segments': segments,
                'total': len(segments),
                'title': doc['title'],
                'author': doc['author'],
                'language': doc['language']
            })
        
    except Exception as e:
        logger.error(f"Error getting document segments: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/semantic', methods=['POST'])
def semantic_search():
    """Búsqueda semántica usando embeddings."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        limit = min(data.get('limit', 10), 50)  # Máximo 50 resultados
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Verificar si existe la base de datos de embeddings
        segments_db_path = os.path.join(project_root, 'data.ms', 'documents.db')
        
        if not os.path.exists(segments_db_path):
            return jsonify({'error': 'No embeddings database found'}), 404
        
        try:
            # Importar el generador de embeddings
            sys.path.append(os.path.join(project_root, 'scripts'))
            from backend.generate_embeddings import EmbeddingGenerator
            
            # Crear generador para la consulta
            generator = EmbeddingGenerator(
                provider="sentence-transformers",
                model_name="hiiamsid/sentence_similarity_spanish_es"
            )
            
            # Generar embedding de la consulta
            query_embedding = generator.generate_embedding(query)
            
            # Buscar segmentos similares
            with sqlite3.connect(segments_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Obtener todos los embeddings
                cursor = conn.execute("""
                    SELECT e.segment_id, e.embedding, s.text, s.document_id, s.original_page,
                           d.title as document_title, d.author as document_author
                    FROM embeddings e
                    JOIN segments s ON e.segment_id = s.id
                    JOIN documents d ON s.document_id = d.id
                    WHERE e.model LIKE 'sentence-transformers:%'
                """)
                
                results = []
                for row in cursor.fetchall():
                    # Convertir embedding de bytes a numpy array
                    stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                    
                    # Calcular similitud coseno
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )
                    
                    results.append({
                        'segment_id': row['segment_id'],
                        'text': row['text'],
                        'document_id': row['document_id'],
                        'document_title': row['document_title'],
                        'document_author': row['document_author'],
                        'original_page': row['original_page'],
                        'similarity': float(similarity)
                    })
                
                # Ordenar por similitud y tomar los mejores resultados
                results.sort(key=lambda x: x['similarity'], reverse=True)
                results = results[:limit]
                
                return jsonify({
                    'query': query,
                    'results': results,
                    'total': len(results)
                })
                
        except ImportError:
            return jsonify({
                'error': 'Sentence-transformers not available. Install with: pip install sentence-transformers'
            }), 500
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return jsonify({'error': f'Search error: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in semantic search endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


_MEILI_PROC = None

def _ensure_meilisearch():
    """Inicia MeiliSearch en segundo plano si no está ya corriendo."""
    global _MEILI_PROC
    # Evitar múltiples instancias cuando el reloader de Flask crea procesos hijo
    if os.environ.get("WERKZEUG_RUN_MAIN") and _MEILI_PROC is not None:
        return
    # ¿Ya responde? -> Nada que hacer
    try:
        requests.get("http://127.0.0.1:7700/health", timeout=2)
        print("[MEILI] MeiliSearch ya está ejecutándose en :7700")
        return
    except Exception:
        pass

    exe = os.environ.get("MEILI_EXEC", "meilisearch")
    try:
        print(f"[MEILI] Iniciando MeiliSearch con ejecutable '{exe}'…")
        # Master key simple solo para desarrollo
        _MEILI_PROC = subprocess.Popen([exe, "--http-addr", "127.0.0.1:7700", "--master-key", "masterKey"],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    except FileNotFoundError:
        # Primer intento: descargar automáticamente el binario apropiado
        print("[MEILI] ⚠️  Ejecutable 'meilisearch' no encontrado. Intentando descarga automática…")
        bin_dir = Path(__file__).parent / "bin"
        auto_exe = bin_dir / ("meilisearch.exe" if os.name == "nt" else "meilisearch")

        if not auto_exe.exists():
            ok = _download_meilisearch(auto_exe)
            if not ok:
                print("[MEILI] ❌ No se pudo descargar MeiliSearch automáticamente. Define MEILI_EXEC o instala manualmente.")
                _MEILI_PROC = None
                return
        else:
            print("[MEILI] Binario ya presente, evitando descarga.")

        try:
            print(f"[MEILI] Lanzando MeiliSearch desde {auto_exe}…")
            _MEILI_PROC = subprocess.Popen([str(auto_exe), "--http-addr", "127.0.0.1:7700", "--master-key", "masterKey"],
                                           stdout=subprocess.DEVNULL,
                                           stderr=subprocess.STDOUT,
                                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
            # Esperar brevemente a que el puerto responda
            for _ in range(10):
                try:
                    requests.get("http://127.0.0.1:7700/health", timeout=1)
                    print("[MEILI] ✅ MeiliSearch disponible en http://127.0.0.1:7700")
                    break
                except Exception:
                    time.sleep(0.5)
        except Exception as e2:
            print(f"[MEILI] ❌ Falló el lanzamiento incluso tras descarga automática: {e2}")
            _MEILI_PROC = None
            return

    def _stop_meili(*_):
        if _MEILI_PROC and _MEILI_PROC.poll() is None:
            print("[MEILI] Deteniendo MeiliSearch…")
            try:
                _MEILI_PROC.terminate()
                _MEILI_PROC.wait(timeout=5)
            except Exception:
                _MEILI_PROC.kill()
    # Registrar limpieza
    atexit.register(_stop_meili)
    signal.signal(signal.SIGINT, _stop_meili)
    signal.signal(signal.SIGTERM, _stop_meili)

# === Utilidad: descarga automática de MeiliSearch ============================

def _download_meilisearch(dest_path: Path, version: str = "v1.7.5") -> bool:
    """Descarga el binario oficial de MeiliSearch para la plataforma actual.
    Devuelve True si se descargó correctamente.
    """
    import shutil
    import tempfile

    system = sys.platform
    arch = "amd64" if (platform_machine := os.getenv("PROCESSOR_ARCHITECTURE", "amd64")).endswith("64") else "386"

    if system.startswith("win"):
        # Los builds oficiales para Windows no llevan el número de versión en el nombre
        asset_name = f"meilisearch-windows-{arch}.exe"
        url = f"https://github.com/meilisearch/meilisearch/releases/download/{version}/{asset_name}"
        is_archive = False
    elif system == "darwin":
        asset_name = f"meilisearch-macos-{arch}.tar.gz"
        url = f"https://github.com/meilisearch/meilisearch/releases/download/{version}/{asset_name}"
        is_archive = True
    else:  # linux
        asset_name = f"meilisearch-linux-{arch}.tar.gz"
        url = f"https://github.com/meilisearch/meilisearch/releases/download/{version}/{asset_name}"
        is_archive = True

    print(f"[MEILI] Descargando {asset_name}…")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / asset_name
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(tmp_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except Exception as err:
            print(f"[MEILI] ❌ Error al descargar MeiliSearch: {err}")
            return False

        try:
            if is_archive:
                # Extraer y mover binario
                with tarfile.open(tmp_file, "r:gz") as tar:
                    for member in tar.getmembers():
                        if member.name.endswith("meilisearch") or member.name.endswith("meilisearch.exe"):
                            tar.extract(member, path=tmpdir)
                            bin_path = Path(tmpdir) / member.name
                            shutil.move(str(bin_path), dest_path)
                            break
            else:
                shutil.move(str(tmp_file), dest_path)
            if not dest_path.exists():
                raise RuntimeError("Binario no encontrado tras la extracción")
            if not dest_path.name.endswith(".exe"):
                dest_path.chmod(0o755)
            print(f"[MEILI] Binario descargado en {dest_path}")
            return True
        except Exception as err:
            print(f"[MEILI] ❌ Error al extraer MeiliSearch: {err}")
            return False

if __name__ == '__main__':
    # Arrancar MeiliSearch solo en el proceso hijo definitivo (WERKZEUG_RUN_MAIN=="true") o cuando debug=False
    if os.environ.get('FLASK_DEBUG', 'True').lower() != 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        _ensure_meilisearch()
    print("[INICIO] Iniciando servidor Flask API para Biblioperson...")
    print("[DATASET] Sistema de dataset: PRESERVADO (sin modificaciones)")
    print("[API] Funcionalidad: Puente API entre frontend y backend existente")
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
    print("[DB] Base de datos: SQLite (library.db)")
    print("[SEARCH] Búsqueda: MeiliSearch + Biblioteca local")
    print("")
    
    # Configuración del servidor
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"[SERVER] Servidor ejecutándose en: http://localhost:{port}")
    print(f"[DEBUG] Modo debug: {debug}")
    print("")
    print("Para detener el servidor: Ctrl+C")
    
    app.run(host='0.0.0.0', port=port, debug=debug)