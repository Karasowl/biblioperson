#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API REST para gestión de duplicados en el sistema de deduplicación de Biblioperson.

Este módulo proporciona endpoints REST para:
- Listar documentos procesados con filtros
- Eliminar documentos específicos por hash
- Limpiar todos los documentos
- Eliminar documentos anteriores a una fecha
"""

import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
try:
    from .deduplication import DeduplicationManager
except ImportError:
    from deduplication import DeduplicationManager

# Crear blueprint para los endpoints de deduplicación
dedup_bp = Blueprint('dedup', __name__, url_prefix='/api/dedup')

def get_dedup_manager():
    """Obtiene una instancia del DeduplicationManager."""
    try:
        from .dedup_config import DedupConfigManager
    except ImportError:
        from dedup_config import DedupConfigManager
    
    # Usar la configuración para obtener la ruta de la base de datos
    config_manager = DedupConfigManager()
    db_path = config_manager.get_database_path()
    return DeduplicationManager(str(db_path))

@dedup_bp.route('', methods=['GET'])
def list_documents():
    """
    Lista documentos procesados con filtros opcionales.
    
    Query parameters:
    - search: Búsqueda en título o ruta de archivo
    - date_from: Fecha desde (YYYY-MM-DD)
    - date_to: Fecha hasta (YYYY-MM-DD)
    - limit: Número máximo de resultados (default: 100)
    - offset: Desplazamiento para paginación (default: 0)
    """
    try:
        # Obtener parámetros de consulta
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Validar límite
        if limit > 1000:
            limit = 1000
        
        # Construir filtros
        filters = {}
        if search:
            filters['search'] = search
        if date_from:
            try:
                datetime.strptime(date_from, '%Y-%m-%d')
                filters['date_from'] = date_from
            except ValueError:
                return jsonify({'error': 'Formato de fecha inválido para date_from. Use YYYY-MM-DD'}), 400
        if date_to:
            try:
                datetime.strptime(date_to, '%Y-%m-%d')
                filters['date_to'] = date_to
            except ValueError:
                return jsonify({'error': 'Formato de fecha inválido para date_to. Use YYYY-MM-DD'}), 400
        
        # Obtener documentos
        dedup_manager = get_dedup_manager()
        
        # Convertir filtros al formato esperado por DeduplicationManager
        search_param = filters.get('search')
        before_param = filters.get('date_to')  # date_to se convierte en before
        after_param = filters.get('date_from')  # date_from se convierte en after
        
        # Obtener todos los documentos que coincidan con los filtros
        all_documents = dedup_manager.list_documents(
            search=search_param,
            before=before_param,
            after=after_param,
            limit=None  # Obtenemos todos para hacer paginación manual
        )
        
        # Aplicar paginación manual
        total_count = len(all_documents)
        start_idx = offset
        end_idx = offset + limit
        documents = all_documents[start_idx:end_idx]
        
        # Obtener estadísticas
        stats = dedup_manager.get_stats()
        
        return jsonify({
            'documents': documents,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total_count  # Total de documentos que coinciden con los filtros
            },
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al listar documentos: {str(e)}'}), 500

@dedup_bp.route('/<document_hash>', methods=['DELETE'])
def delete_document(document_hash):
    """
    Elimina un documento específico por su hash.
    
    Args:
        document_hash: Hash SHA-256 del documento a eliminar
    """
    try:
        if not document_hash or len(document_hash) != 64:
            return jsonify({'error': 'Hash de documento inválido'}), 400
        
        dedup_manager = get_dedup_manager()
        success = dedup_manager.remove_document(document_hash)
        
        if success:
            return jsonify({'message': 'Documento eliminado exitosamente'})
        else:
            return jsonify({'error': 'Documento no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error al eliminar documento: {str(e)}'}), 500

@dedup_bp.route('/path', methods=['DELETE'])
def delete_by_path():
    """
    Elimina un documento específico por su ruta de archivo.
    
    JSON body:
    - file_path: Ruta del archivo a eliminar
    """
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({'error': 'Se requiere file_path en el cuerpo de la petición'}), 400
        
        file_path = data['file_path'].strip()
        if not file_path:
            return jsonify({'error': 'file_path no puede estar vacío'}), 400
        
        dedup_manager = get_dedup_manager()
        success = dedup_manager.remove_by_path(file_path)
        
        if success:
            return jsonify({'message': 'Documento eliminado exitosamente'})
        else:
            return jsonify({'error': 'Documento no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error al eliminar documento: {str(e)}'}), 500

@dedup_bp.route('/clear', methods=['POST'])
def clear_all_documents():
    """
    Elimina todos los documentos de la base de datos de deduplicación.
    
    JSON body (opcional):
    - confirm: true (para confirmar la operación)
    """
    try:
        data = request.get_json() or {}
        
        # Verificar confirmación
        if not data.get('confirm', False):
            return jsonify({
                'error': 'Se requiere confirmación explícita',
                'message': 'Envíe {"confirm": true} para confirmar la eliminación de todos los documentos'
            }), 400
        
        dedup_manager = get_dedup_manager()
        
        # Obtener estadísticas antes de limpiar
        stats_before = dedup_manager.get_stats()
        
        # Limpiar todos los documentos
        dedup_manager.clear_all()
        
        return jsonify({
            'message': 'Todos los documentos han sido eliminados exitosamente',
            'documents_removed': stats_before['total_documents']
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al limpiar documentos: {str(e)}'}), 500

@dedup_bp.route('/prune', methods=['POST'])
def prune_documents():
    """
    Elimina documentos anteriores a una fecha específica.
    
    JSON body:
    - before_date: Fecha límite en formato YYYY-MM-DD
    - confirm: true (para confirmar la operación)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Se requiere cuerpo JSON'}), 400
        
        # Verificar confirmación
        if not data.get('confirm', False):
            return jsonify({
                'error': 'Se requiere confirmación explícita',
                'message': 'Envíe {"confirm": true} para confirmar la eliminación'
            }), 400
        
        # Verificar fecha
        before_date = data.get('before_date')
        if not before_date:
            return jsonify({'error': 'Se requiere before_date'}), 400
        
        try:
            datetime.strptime(before_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        
        dedup_manager = get_dedup_manager()
        
        # Obtener documentos que serán eliminados (para estadísticas)
        filters = {'date_to': before_date}
        docs_to_remove = dedup_manager.list_documents(filters=filters)
        
        # Eliminar documentos
        removed_count = len(docs_to_remove)
        for doc in docs_to_remove:
            dedup_manager.remove_document(doc['hash'])
        
        return jsonify({
            'message': f'Documentos anteriores a {before_date} eliminados exitosamente',
            'documents_removed': removed_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al eliminar documentos: {str(e)}'}), 500

@dedup_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    Obtiene estadísticas de la base de datos de deduplicación.
    """
    try:
        dedup_manager = get_dedup_manager()
        stats = dedup_manager.get_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500

@dedup_bp.route('/batch', methods=['DELETE'])
def delete_batch():
    """
    Elimina múltiples documentos por sus hashes.
    
    JSON body:
    - hashes: Lista de hashes SHA-256 a eliminar
    - confirm: true (para confirmar la operación)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Se requiere cuerpo JSON'}), 400
        
        # Verificar confirmación
        if not data.get('confirm', False):
            return jsonify({
                'error': 'Se requiere confirmación explícita',
                'message': 'Envíe {"confirm": true} para confirmar la eliminación'
            }), 400
        
        # Verificar hashes
        hashes = data.get('hashes', [])
        if not isinstance(hashes, list) or not hashes:
            return jsonify({'error': 'Se requiere una lista no vacía de hashes'}), 400
        
        # Validar formato de hashes
        invalid_hashes = [h for h in hashes if not isinstance(h, str) or len(h) != 64]
        if invalid_hashes:
            return jsonify({'error': f'Hashes inválidos encontrados: {len(invalid_hashes)}'}), 400
        
        dedup_manager = get_dedup_manager()
        
        # Eliminar documentos
        removed_count = 0
        errors = []
        
        for document_hash in hashes:
            try:
                if dedup_manager.remove_document(document_hash):
                    removed_count += 1
                else:
                    errors.append(f'Hash no encontrado: {document_hash}')
            except Exception as e:
                errors.append(f'Error eliminando {document_hash}: {str(e)}')
        
        response = {
            'message': f'{removed_count} documentos eliminados exitosamente',
            'documents_removed': removed_count,
            'total_requested': len(hashes)
        }
        
        if errors:
            response['errors'] = errors
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'Error en eliminación por lotes: {str(e)}'}), 500

# Función para registrar el blueprint en una aplicación Flask
def register_dedup_api(app):
    """
    Registra el blueprint de deduplicación en una aplicación Flask.
    
    Args:
        app: Instancia de Flask donde registrar los endpoints
    """
    app.register_blueprint(dedup_bp)
    print("[INFO] API de deduplicación registrada en /api/dedup") 