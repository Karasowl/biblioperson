#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API de conexión para IAs - Biblioteca de Conocimiento Personal

Este módulo proporciona funciones para que diferentes modelos de IA
puedan acceder y analizar el contenido de la biblioteca de conocimiento.
"""

import os
import json
import sqlite3
import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Configuración de rutas
BASE_DIR = Path(os.getenv("BASE_DIR", Path(__file__).resolve().parent.parent))
DB_PATH = BASE_DIR / 'data' / 'biblioteca.db'
CONFIG_DIR = BASE_DIR / 'config'
INDICES_DIR = BASE_DIR / 'shared' / 'indices'
CONTENIDO_DIR = BASE_DIR / 'shared' / 'documentation'

# Inicializar aplicación Flask
app = Flask(__name__)
CORS(app)

def conectar_db():
    """Establece conexión con la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/info', methods=['GET'])
def get_info():
    """Proporciona información general sobre la biblioteca."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Obtener estadísticas básicas
    cursor.execute('SELECT COUNT(*) as total FROM contenidos')
    total_contenidos = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM temas')
    total_temas = cursor.fetchone()['total']
    
    cursor.execute('SELECT MIN(fecha_creacion) as primera, MAX(fecha_creacion) as ultima FROM contenidos')
    fechas = cursor.fetchone()
    
    cursor.execute('''
        SELECT p.nombre, COUNT(*) as cantidad
        FROM contenidos c
        JOIN plataformas p ON c.plataforma_id = p.id
        GROUP BY p.nombre
        ORDER BY cantidad DESC
    ''')
    
    distribucion = []
    for row in cursor.fetchall():
        distribucion.append({
            'plataforma': row['nombre'],
            'cantidad': row['cantidad']
        })
    
    conn.close()
    
    return jsonify({
        'total_contenidos': total_contenidos,
        'total_temas': total_temas,
        'rango_fechas': {
            'primera': fechas['primera'],
            'ultima': fechas['ultima']
        },
        'distribucion_plataformas': distribucion,
        'descripcion': 'Biblioteca de Conocimiento Personal de Ismael López-Silvero Guimarais'
    })

@app.route('/api/contenido', methods=['GET'])
def get_contenido():
    """
    Busca contenido según criterios especificados.
    
    Parámetros de consulta:
    - tema: ID o nombre del tema
    - texto: Texto a buscar
    - plataforma: Nombre de la plataforma
    - fecha_inicio: Fecha de inicio (YYYY-MM-DD)
    - fecha_fin: Fecha de fin (YYYY-MM-DD)
    - limite: Número máximo de resultados (default: 100)
    """
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Obtener parámetros
    tema = request.args.get('tema')
    texto = request.args.get('texto')
    plataforma = request.args.get('plataforma')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    limite = request.args.get('limite', 100, type=int)
    
    # Construir consulta base
    query = '''
        SELECT c.id, c.contenido_texto, c.fecha_creacion, p.nombre as plataforma, f.nombre as fuente
        FROM contenidos c
        JOIN plataformas p ON c.plataforma_id = p.id
        JOIN fuentes f ON c.fuente_id = f.id
    '''
    
    conditions = []
    params = []
    
    # Añadir condiciones según parámetros
    if tema:
        # Verificar si es ID o nombre
        try:
            tema_id = int(tema)
            conditions.append('''
                c.id IN (
                    SELECT contenido_id 
                    FROM contenido_tema 
                    WHERE tema_id = ?
                )
            ''')
            params.append(tema_id)
        except ValueError:
            conditions.append('''
                c.id IN (
                    SELECT ct.contenido_id 
                    FROM contenido_tema ct
                    JOIN temas t ON ct.tema_id = t.id
                    WHERE t.nombre LIKE ?
                )
            ''')
            params.append(f'%{tema}%')
    
    if texto:
        conditions.append('''
            c.id IN (
                SELECT rowid 
                FROM contenidos_fts 
                WHERE contenidos_fts MATCH ?
            )
        ''')
        params.append(texto)
    
    if plataforma:
        conditions.append('p.nombre LIKE ?')
        params.append(f'%{plataforma}%')
    
    if fecha_inicio:
        conditions.append('c.fecha_creacion >= ?')
        params.append(fecha_inicio)
    
    if fecha_fin:
        conditions.append('c.fecha_creacion <= ?')
        params.append(fecha_fin)
    
    # Añadir condiciones a la consulta
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    # Añadir orden y límite
    query += ' ORDER BY c.fecha_creacion DESC LIMIT ?'
    params.append(limite)
    
    # Ejecutar consulta
    cursor.execute(query, params)
    
    # Procesar resultados
    resultados = []
    for row in cursor.fetchall():
        # Obtener temas relacionados
        cursor2 = conn.cursor()
        cursor2.execute('''
            SELECT t.id, t.nombre, ct.relevancia
            FROM temas t
            JOIN contenido_tema ct ON t.id = ct.tema_id
            WHERE ct.contenido_id = ?
            ORDER BY ct.relevancia DESC
        ''', (row['id'],))
        
        temas = []
        for tema_row in cursor2.fetchall():
            temas.append({
                'id': tema_row['id'],
                'nombre': tema_row['nombre'],
                'relevancia': tema_row['relevancia']
            })
        
        resultados.append({
            'id': row['id'],
            'texto': row['contenido_texto'],
            'fecha': row['fecha_creacion'],
            'plataforma': row['plataforma'],
            'fuente': row['fuente'],
            'temas': temas
        })
    
    conn.close()
    return jsonify(resultados)

@app.route('/api/generar', methods=['GET'])
def get_generacion():
    """
    Proporciona material para generar nuevo contenido.
    
    Parámetros de consulta:
    - tema: ID o nombre del tema (requerido)
    - tipo: Tipo de contenido a generar (post, articulo, guion)
    - longitud: Longitud aproximada deseada (corto, medio, largo)
    """
    tema = request.args.get('tema')
    tipo = request.args.get('tipo', 'post')
    longitud = request.args.get('longitud', 'medio')
    
    if not tema:
        return jsonify({'error': 'Se requiere especificar un tema'}), 400
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Determinar límite de contenidos según longitud
    if longitud == 'corto':
        limite = 5
    elif longitud == 'largo':
        limite = 20
    else:  # medio
        limite = 10
    
    # Obtener contenidos relevantes
    try:
        tema_id = int(tema)
        cursor.execute('''
            SELECT c.id, c.contenido_texto, c.fecha_creacion, ct.relevancia
            FROM contenidos c
            JOIN contenido_tema ct ON c.id = ct.contenido_id
            WHERE ct.tema_id = ?
            ORDER BY ct.relevancia DESC, c.fecha_creacion DESC
            LIMIT ?
        ''', (tema_id, limite))
    except ValueError:
        cursor.execute('''
            SELECT c.id, c.contenido_texto, c.fecha_creacion, ct.relevancia
            FROM contenidos c
            JOIN contenido_tema ct ON c.id = ct.contenido_id
            JOIN temas t ON ct.tema_id = t.id
            WHERE t.nombre LIKE ?
            ORDER BY ct.relevancia DESC, c.fecha_creacion DESC
            LIMIT ?
        ''', (f'%{tema}%', limite))
    
    # Procesar resultados
    material = []
    for row in cursor.fetchall():
        material.append({
            'id': row['id'],
            'texto': row['contenido_texto'],
            'fecha': row['fecha_creacion'],
            'relevancia': row['relevancia']
        })
    
    # Obtener nombre del tema
    if material:
        try:
            tema_id = int(tema)
            cursor.execute('SELECT nombre FROM temas WHERE id = ?', (tema_id,))
        except ValueError:
            cursor.execute('SELECT nombre FROM temas WHERE nombre LIKE ?', (f'%{tema}%',))
        
        tema_row = cursor.fetchone()
        tema_nombre = tema_row['nombre'] if tema_row else tema
    else:
        tema_nombre = tema
    
    # Generar estructura según tipo de contenido
    estructura = {}
    if tipo == 'post':
        estructura = {
            'titulo': f'Ideas sobre {tema_nombre}',
            'introduccion': 'Breve introducción al tema',
            'puntos_clave': ['Punto 1', 'Punto 2', 'Punto 3'],
            'conclusion': 'Conclusión o llamada a la acción'
        }
    elif tipo == 'articulo':
        estructura = {
            'titulo': f'Análisis profundo sobre {tema_nombre}',
            'introduccion': 'Contexto y relevancia del tema',
            'secciones': [
                {'titulo': 'Antecedentes', 'contenido': 'Desarrollo histórico o conceptual'},
                {'titulo': 'Análisis', 'contenido': 'Puntos principales y argumentos'},
                {'titulo': 'Implicaciones', 'contenido': 'Consecuencias o aplicaciones'}
            ],
            'conclusion': 'Síntesis y reflexiones finales'
        }
    elif tipo == 'guion':
        estructura = {
            'titulo': f'Guion sobre {tema_nombre}',
            'introduccion': 'Saludo y presentación del tema',
            'segmentos': [
                {'tiempo': '0:00-2:00', 'contenido': 'Introducción y contexto'},
                {'tiempo': '2:00-5:00', 'contenido': 'Desarrollo de ideas principales'},
                {'tiempo': '5:00-8:00', 'contenido': 'Análisis y ejemplos'},
                {'tiempo': '8:00-10:00', 'contenido': 'Conclusiones y despedida'}
            ],
            'recursos': ['Referencias visuales', 'Citas importantes', 'Datos clave']
        }
    
    conn.close()
    return jsonify({
        'tema': tema_nombre,
        'tipo': tipo,
        'longitud': longitud,
        'material': material,
        'estructura_sugerida': estructura
    })

@app.route('/api/indices/<nombre>', methods=['GET'])
def get_indice(nombre):
    """Proporciona acceso directo a los archivos de índices."""
    archivo = INDICES_DIR / f'{nombre}.json'
    if not archivo.exists():
        return jsonify({'error': f'Índice no encontrado: {nombre}'}), 404
    
    return send_file(archivo)

@app.route('/api/ndjson/contenido', methods=['GET'])
def get_ndjson():
    """Proporciona acceso al archivo NDJSON con todo el contenido."""
    archivo = INDICES_DIR / 'contenido_completo.ndjson'
    if not archivo.exists():
        return jsonify({'error': 'Archivo NDJSON no encontrado'}), 404
    
    return send_file(archivo)

@app.route('/api/documentacion', methods=['GET'])
def get_documentacion():
    """Proporciona documentación sobre la API."""
    return jsonify({
        'nombre': 'API de Biblioteca de Conocimiento Personal',
        'version': '1.0',
        'descripcion': 'API para acceso a la biblioteca de conocimiento personal de Ismael López-Silvero Guimarais',
        'endpoints': [
            {
                'ruta': '/api/info',
                'metodo': 'GET',
                'descripcion': 'Información general sobre la biblioteca',
                'parametros': []
            },
            {
                'ruta': '/api/contenido',
                'metodo': 'GET',
                'descripcion': 'Búsqueda de contenido',
                'parametros': [
                    {'nombre': 'tema', 'tipo': 'string', 'descripcion': 'ID o nombre del tema'},
                    {'nombre': 'texto', 'tipo': 'string', 'descripcion': 'Texto a buscar'},
                    {'nombre': 'plataforma', 'tipo': 'string', 'descripcion': 'Nombre de la plataforma'},
                    {'nombre': 'fecha_inicio', 'tipo': 'string', 'descripcion': 'Fecha de inicio (YYYY-MM-DD)'},
                    {'nombre': 'fecha_fin', 'tipo': 'string', 'descripcion': 'Fecha de fin (YYYY-MM-DD)'},
                    {'nombre': 'limite', 'tipo': 'integer', 'descripcion': 'Número máximo de resultados (default: 100)'}
                ]
            },
            {
                'ruta': '/api/generar',
                'metodo': 'GET',
                'descripcion': 'Material para generar nuevo contenido',
                'parametros': [
                    {'nombre': 'tema', 'tipo': 'string', 'descripcion': 'ID o nombre del tema (requerido)'},
                    {'nombre': 'tipo', 'tipo': 'string', 'descripcion': 'Tipo de contenido (post, articulo, guion)'},
                    {'nombre': 'longitud', 'tipo': 'string', 'descripcion': 'Longitud deseada (corto, medio, largo)'}
                ]
            },
            {
                'ruta': '/api/indices/<nombre>',
                'metodo': 'GET',
                'descripcion': 'Acceso a archivos de índices',
                'parametros': [
                    {'nombre': 'nombre', 'tipo': 'string', 'descripcion': 'Nombre del índice (cronologico, temas_jerarquia)'}
                ]
            },
            {
                'ruta': '/api/ndjson/contenido',
                'metodo': 'GET',
                'descripcion': 'Acceso al archivo NDJSON con todo el contenido',
                'parametros': []
            }
        ],
        'ejemplos': [
            {'descripcion': 'Obtener información general', 'url': '/api/info'},
            {'descripcion': 'Buscar contenido sobre cristianismo', 'url': '/api/contenido?tema=Cristianismo'},
            {'descripcion': 'Obtener material para generar un artículo sobre política', 'url': '/api/generar?tema=Política&tipo=articulo&longitud=largo'}
        ]
    })

if __name__ == '__main__':
    # Asegurarse de que existen los directorios necesarios
    os.makedirs(INDICES_DIR, exist_ok=True)
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
