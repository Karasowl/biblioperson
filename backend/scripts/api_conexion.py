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
import importlib.util
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import subprocess
import socket
import sys
import meilisearch

# Importar API de deduplicación
try:
    # Intentar importar desde el dataset processing
    dataset_path = Path(__file__).parent.parent.parent / 'dataset' / 'processing'
    if dataset_path.exists():
        sys.path.insert(0, str(dataset_path))
        from dedup_api import register_dedup_api
        DEDUP_API_AVAILABLE = True
        print("[INFO] API de deduplicación disponible")
    else:
        DEDUP_API_AVAILABLE = False
        print("[ADVERTENCIA] Directorio dataset/processing no encontrado")
except ImportError as e:
    DEDUP_API_AVAILABLE = False
    print(f"[ADVERTENCIA] No se pudo cargar la API de deduplicación: {e}")

# --- Levantar Meilisearch automáticamente si no está corriendo ---
def is_meilisearch_running(host='127.0.0.1', port=7700):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False

if not is_meilisearch_running():
    meili_script = Path(__file__).parent / 'levantar_meilisearch.py'
    if meili_script.exists():
        print("[INFO] Meilisearch no está corriendo. Iniciando...")
        subprocess.Popen([sys.executable, str(meili_script)])
    else:
        print(f"[ADVERTENCIA] No se encontró {meili_script}. Meilisearch no se levantará automáticamente.")

# --- Inicializar campos filterable y sort en Meilisearch al arrancar el backend ---
def inicializar_meilisearch_indices():
    try:
        client = meilisearch.Client('http://127.0.0.1:7700')
        
        # Configuración para el índice documentos (embeddings)
        try:
            index_doc = client.index('documentos')
            # Asegura que estos campos sean filtrables y ordenables
            index_doc.update_filterable_attributes(['id', 'autor', 'fecha_creacion', 'fecha_importacion', 'fuente_id', 'plataforma_id', 'idioma'])
            index_doc.update_sortable_attributes(['id', 'fecha_creacion', 'fecha_importacion'])
            index_doc.update_searchable_attributes(['contenido_texto', 'autor', 'contexto', 'url_original'])
            # Configurar búsqueda vectorial
            # Es necesario definir el nombre del campo donde están los embeddings
            try:
                # Verificamos si ya existe la configuración
                index_config = index_doc.get_settings()
                print(f"[INFO] Configuración actual del índice: {index_config}")
                
                # Configuramos los embedders
                index_doc.update_embedders({
                    'default': {
                        'source': 'embedding',
                        'dimensions': 768,  # Dimensiones para el modelo 'paraphrase-multilingual-mpnet-base-v2'
                        'distance': 'cosine'  # Usar similitud coseno
                    }
                })
                print(f"[INFO] Meilisearch: Índice 'documentos' configurado con búsqueda vectorial")
                
                # NUEVO: Aumentar el límite de paginationTotalHits a 100000
                index_doc.update_settings({"paginationTotalHits": 100000})
                print(f"[INFO] Meilisearch: paginationTotalHits configurado a 100000 para 'documentos'")
                
                # Verificar que se aplicó correctamente
                updated_config = index_doc.get_settings()
                print(f"[INFO] Nueva configuración del índice: {updated_config}")
            except Exception as e:
                print(f"[ADVERTENCIA] Error configurando embedders: {e}")
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo configurar el índice 'documentos': {e}")
        
        # Mantener compatibilidad con el índice 'contenidos'
        try:
            index = client.index('contenidos')
            # Asegura que estos campos sean filtrables y ordenables
            filterable = ['autor']
            sortable = ['fecha']
            index.update_filterable_attributes(filterable)
            index.update_sortable_attributes(sortable)
            print(f"[INFO] Meilisearch: Campos filterable={filterable}, sortable={sortable} inicializados para 'contenidos'.")
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo inicializar el índice 'contenidos': {e}")
            
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo conectar con Meilisearch: {e}")

# Cargar variables de entorno
load_dotenv()

# Configuración de rutas
BASE_DIR = Path(os.getenv("BASE_DIR", Path(__file__).resolve().parent.parent))
DB_PATH = BASE_DIR / 'data' / 'biblioteca.db'
CONFIG_DIR = BASE_DIR / 'config'
INDICES_DIR = BASE_DIR / 'shared' / 'indices'
CONTENIDO_DIR = BASE_DIR / 'shared' / 'documentation'

# Imprimir información de depuración
print(f"BASE_DIR: {BASE_DIR.absolute()}")
print(f"DB_PATH: {DB_PATH.absolute()}")
print(f"DB_PATH exists: {DB_PATH.exists()}")

# Inicializar aplicación Flask
app = Flask(__name__)
CORS(app, origins=[f"http://localhost:{port}" for port in range(5170, 5180)] + [f"http://127.0.0.1:{port}" for port in range(5170, 5180)])

# Inicializar proveedores de LLM según las claves disponibles
llm_providers = {}

def cargar_llm_providers():
    """Carga los proveedores de LLM disponibles."""
    # Verificar Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            
            def generar_con_gemini(prompt):
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                return response.text
                
            llm_providers["gemini"] = generar_con_gemini
            print("Proveedor LLM: Gemini cargado correctamente")
        except ImportError:
            print("No se pudo cargar el proveedor Gemini. Librería no instalada.")
    
    # Verificar OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            
            def generar_con_openai(prompt):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un asistente que genera contenido basado en los textos proporcionados."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
                
            llm_providers["openai"] = generar_con_openai
            print("Proveedor LLM: OpenAI cargado correctamente")
        except ImportError:
            print("No se pudo cargar el proveedor OpenAI. Librería no instalada.")

# Intentar cargar los proveedores de LLM
cargar_llm_providers()

def conectar_db():
    """Establece conexión con la base de datos SQLite."""
    # Asegurarse que el directorio de datos exista
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def tabla_existe(conn, nombre_tabla):
    """Verifica si una tabla existe en la base de datos."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (nombre_tabla,)
    )
    return cursor.fetchone() is not None

@app.route('/api/info', methods=['GET'])
def get_info():
    """Proporciona información general sobre la biblioteca."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Verificar si existe la tabla contenidos
    total_contenidos = 0
    fechas = {'primera': None, 'ultima': None}
    distribucion = []
    
    if tabla_existe(conn, 'contenidos'):
        # Obtener estadísticas básicas
        cursor.execute('SELECT COUNT(*) as total FROM contenidos')
        total_contenidos = cursor.fetchone()['total']
        
        # Obtener rango de fechas
        cursor.execute('SELECT MIN(fecha_creacion) as primera, MAX(fecha_creacion) as ultima FROM contenidos')
        fechas = cursor.fetchone()
        
        # Obtener distribución por plataforma
        if tabla_existe(conn, 'plataformas'):
            cursor.execute('''
                SELECT p.nombre, COUNT(*) as cantidad
                FROM contenidos c
                JOIN plataformas p ON c.plataforma_id = p.id
                GROUP BY p.nombre
                ORDER BY cantidad DESC
            ''')
            
            for row in cursor.fetchall():
                distribucion.append({
                    'plataforma': row['nombre'],
                    'cantidad': row['cantidad']
                })
    
    # Verificar si la tabla temas existe
    total_temas = 0
    if tabla_existe(conn, 'temas'):
        cursor.execute('SELECT COUNT(*) as total FROM temas')
        total_temas = cursor.fetchone()['total']
    
    # Nuevo: contar autores únicos
    total_autores = 0
    cursor.execute('SELECT COUNT(DISTINCT autor) as total FROM contenidos WHERE autor IS NOT NULL AND autor != ""')
    total_autores = cursor.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'total_contenidos': total_contenidos,
        'total_temas': total_temas,
        'total_autores': total_autores,
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
    
    # Verificar si existe la tabla contenidos
    if not tabla_existe(conn, 'contenidos'):
        conn.close()
        return jsonify([])
    
    # Verificar si existen las tablas relacionadas
    if not tabla_existe(conn, 'plataformas') or not tabla_existe(conn, 'fuentes'):
        conn.close()
        return jsonify([])
    
    # Obtener parámetros
    tema = request.args.get('tema')
    contenido_texto = request.args.get('contenido_texto')
    plataforma = request.args.get('plataforma')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    limite = request.args.get('limite', 100, type=int)
    autor_param = request.args.get('autor')
    
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
        # Verificar si existe la tabla temas
        if tabla_existe(conn, 'temas') and tabla_existe(conn, 'contenido_tema'):
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
        else:
            # Si la tabla temas no existe, ignorar este filtro
            pass
    
    if contenido_texto:
        # Verificar si existe la tabla fts
        if tabla_existe(conn, 'contenidos_fts'):
            conditions.append('''
                c.id IN (
                    SELECT rowid 
                    FROM contenidos_fts 
                    WHERE contenidos_fts MATCH ?
                )
            ''')
            params.append(contenido_texto)
    
    if plataforma:
        conditions.append('p.nombre LIKE ?')
        params.append(f'%{plataforma}%')
    
    if fecha_inicio:
        conditions.append('c.fecha_creacion >= ?')
        params.append(fecha_inicio)
    
    if fecha_fin:
        conditions.append('c.fecha_creacion <= ?')
        params.append(fecha_fin)
    
    if autor_param:
        autores = [a.strip() for a in autor_param.split(',') if a.strip()]
        if autores:
            conditions.append('(' + ' OR '.join(['c.autor = ?' for _ in autores]) + ')')
            params.extend(autores)
    
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
        temas = []
        if tabla_existe(conn, 'temas') and tabla_existe(conn, 'contenido_tema'):
            cursor2 = conn.cursor()
            cursor2.execute('''
                SELECT t.id, t.nombre, ct.relevancia
                FROM temas t
                JOIN contenido_tema ct ON t.id = ct.tema_id
                WHERE ct.contenido_id = ?
                ORDER BY ct.relevancia DESC
            ''', (row['id'],))
            
            for tema_row in cursor2.fetchall():
                temas.append({
                    'id': tema_row['id'],
                    'nombre': tema_row['nombre'],
                    'relevancia': tema_row['relevancia']
                })
        
        resultados.append({
            'id': row['id'],
            'contenido_texto': row['contenido_texto'],
            'fecha': row['fecha_creacion'],
            'plataforma': row['plataforma'],
            'fuente': row['fuente'],
            'idioma': row['idioma'] if 'idioma' in row.keys() else 'es',
            'temas': temas
        })
    
    conn.close()
    return jsonify(resultados)

@app.route('/api/busqueda', methods=['GET'])
def busqueda_general():
    """
    Búsqueda general de texto usando Meilisearch.
    Parámetros:
    - texto: texto a buscar (obligatorio)
    - pagina: número de página (default: 1)
    - por_pagina: resultados por página (default: 10)
    - autor: filtrar por autor (opcional)
    - ordenar: 'relevancia' (default) o 'fecha'
    """
    contenido_texto = request.args.get('contenido_texto', '').strip() or request.args.get('texto', '').strip()
    if not contenido_texto:
        return jsonify({'error': 'Debe proporcionar un contenido_texto para buscar.'}), 400

    pagina = int(request.args.get('pagina', 1))
    por_pagina = int(request.args.get('por_pagina', 10))
    autor = request.args.get('autor')
    ordenar = request.args.get('ordenar', 'relevancia')

    # Conexión a Meilisearch
    client = meilisearch.Client('http://127.0.0.1:7700')
    index = client.index('documentos')
    offset = (pagina - 1) * por_pagina

    # Construir opciones para Meilisearch
    search_options = {
        'limit': por_pagina,
        'offset': offset,
    }
    if autor:
        search_options['filter'] = f"autor = '{autor}'"
    if ordenar == 'fecha':
        search_options['sort'] = ['fecha_creacion:desc']

    # Realizar búsqueda
    res = index.search(contenido_texto, search_options)
    hits = res.get('hits', [])
    total = res.get('estimatedTotalHits', 0)
    # Formatear resultados
    resultados = []
    for doc in hits:
        resultados.append({
            'id': doc.get('id'),
            'contenido_texto': doc.get('contenido_texto') or doc.get('texto'),
            'fecha': doc.get('fecha'),
            'autor': doc.get('autor'),
        })
    return jsonify({
        'resultados': resultados,
        'paginacion': {
            'pagina_actual': pagina,
            'resultados_por_pagina': por_pagina,
            'total_resultados': total,
            'total_paginas': (total + por_pagina - 1) // por_pagina
        },
        'consulta': contenido_texto
    })

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
    
    # Verificar si existen las tablas necesarias
    if not tabla_existe(conn, 'temas') or not tabla_existe(conn, 'contenido_tema'):
        return jsonify({'error': 'No se han definido temas en el sistema'}), 404
    
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
            'contenido_texto': row['contenido_texto'],
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
            },
            {
                'ruta': '/api/busqueda/semantica',
                'metodo': 'GET',
                'descripcion': 'Búsqueda semántica de contenido similar',
                'parametros': [
                    {'nombre': 'texto', 'tipo': 'string', 'descripcion': 'Texto para buscar similitud semántica (requerido)'},
                    {'nombre': 'pagina', 'tipo': 'integer', 'descripcion': 'Número de página (default: 1)'},
                    {'nombre': 'por_pagina', 'tipo': 'integer', 'descripcion': 'Resultados por página (default: 10, max: 50)'}
                ]
            },
            {
                'ruta': '/api/busqueda',
                'metodo': 'GET',
                'descripcion': 'Búsqueda general de texto usando Meilisearch',
                'parametros': [
                    {'nombre': 'texto', 'tipo': 'string', 'descripcion': 'Texto a buscar (obligatorio)'},
                    {'nombre': 'pagina', 'tipo': 'integer', 'descripcion': 'Número de página (default: 1)'},
                    {'nombre': 'por_pagina', 'tipo': 'integer', 'descripcion': 'Resultados por página (default: 10)'},
                    {'nombre': 'autor', 'tipo': 'string', 'descripcion': 'Filtrar por autor (opcional)'},
                    {'nombre': 'ordenar', 'tipo': 'string', 'descripcion': "'relevancia' (default) o 'fecha'"}
                ]
            }
        ],
        'ejemplos': [
            {'descripcion': 'Obtener información general', 'url': '/api/info'},
            {'descripcion': 'Buscar contenido sobre cristianismo', 'url': '/api/contenido?tema=Cristianismo'},
            {'descripcion': 'Obtener material para generar un artículo sobre política', 'url': '/api/generar?tema=Política&tipo=articulo&longitud=largo'},
            {'descripcion': 'Buscar contenido semánticamente similar a un texto', 'url': '/api/busqueda/semantica?texto=La importancia de la fe&pagina=1&por_pagina=20'},
            {'descripcion': 'Realizar una búsqueda general', 'url': '/api/busqueda?texto=educación&pagina=1&por_pagina=10'}
        ]
    })

# Añadir importación del servicio de embeddings
from scripts.embedding_service import EmbeddingService
import json

# Inicializar el servicio
embedding_service = EmbeddingService()

@app.route('/api/busqueda/semantica', methods=['GET'])
def busqueda_semantica():
    """
    Realiza una búsqueda semántica en el contenido
    
    Parámetros:
    - contenido_texto: Texto de consulta
    - pagina: Número de página (default: 1)
    - por_pagina: Resultados por página (default: 10, max: 50)
    - usar_meilisearch: si es true, usa Meilisearch para búsqueda vectorial (default: true)
    """
    contenido_texto = request.args.get('contenido_texto', '')
    if not contenido_texto:
        return jsonify({'error': 'No se proporcionó contenido_texto para buscar'}), 400
        
    # Parámetros de paginación
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 10, type=int)
    limite = request.args.get('limite', None, type=int)
    
    # Limitar resultados por página
    por_pagina = min(por_pagina, 50)
    
    # Parámetros de filtrado
    filtros = request.args.get('filtros', '')
    similitud_min = request.args.get('similitud_min', 0.2, type=float)
    ordenar_por = request.args.get('ordenar_por', 'similitud')
    
    # Filtrado por autor
    autor_param = request.args.get('autor', '')
    autores = autor_param.split(',') if autor_param else []
    
    # Flag para usar Meilisearch o método tradicional
    usar_meilisearch_str = request.args.get('usar_meilisearch', 'true').lower()
    usar_meilisearch = usar_meilisearch_str in ['true', '1', 'yes', 'y']
    
    # Opción 1: Usar Meilisearch si está habilitado
    if usar_meilisearch:
        try:
            # Conexión a Meilisearch
            client = meilisearch.Client('http://127.0.0.1:7700')
            index = client.index('documentos')
            
            # Ver la configuración actual
            try:
                index_settings = index.get_settings()
                print(f"[INFO] Configuración actual del índice: {index_settings}")
            except Exception as e:
                print(f"[INFO] No se pudo obtener la configuración del índice: {e}")
                
            # Generar embedding del texto de consulta
            query_embedding = embedding_service.generar_embedding(contenido_texto)
            if not query_embedding:
                return jsonify({'error': 'No se pudo generar embedding para el contenido_texto'}), 400
            
            # Construir opciones para Meilisearch
            search_options = {
                'limit': por_pagina,
                'attributesToRetrieve': ['id', 'contenido_texto', 'fecha_creacion', 'autor', 'plataforma_id', 'fuente_id', 'idioma'],
                'vector': query_embedding,
                'hybrid': {
                    'semanticRatio': 0.5  # Un valor entre 0 y 1 que determina cuánto peso se da a la parte semántica vs texto
                }
            }
            
            # Aplicar filtro por autor si se especifica
            if autores:
                autor_filters = []
                for autor in autores:
                    autor_filters.append(f"autor = '{autor}'")
                search_options['filter'] = ' OR '.join(autor_filters)
            
            print(f"Opciones de búsqueda en Meilisearch: {search_options}")
            
            # Realizar búsqueda
            try:
                res = index.search(contenido_texto, search_options)
                hits = res.get('hits', [])
                print(f"[INFO] Resultados de búsqueda: {len(hits)} documentos encontrados")
            except Exception as e:
                print(f"[ERROR] Error al realizar búsqueda en Meilisearch: {type(e).__name__}: {e}")
                print("Revirtiendo al método tradicional de búsqueda...")
                return busqueda_semantica_tradicional(contenido_texto, pagina, por_pagina, limite, filtros, similitud_min, ordenar_por, autores)
                
            # Formatear resultados
            contenidos_detallados = []
            for doc in hits:
                # Si hay un umbral de similitud, filtrar aquí en el código
                score = doc.get('_semanticScore', 0)
                if score >= similitud_min:
                    contenidos_detallados.append({
                        'id': doc.get('id'),
                        'contenido_texto': doc.get('contenido_texto'),
                        'fecha': doc.get('fecha_creacion'),
                        'plataforma': doc.get('plataforma_id', ''),
                        'fuente': doc.get('fuente_id', ''),
                        'idioma': doc.get('idioma', 'es'),
                        'similitud': round(score, 4) if score is not None else 0,
                        'autor': doc.get('autor', '')
                    })
            
            # Calcular paginación basada en resultados filtrados
            total_resultados = len(contenidos_detallados)
            total_paginas = (total_resultados + por_pagina - 1) // por_pagina  # Redondeo hacia arriba
            
            # Aplicar paginación manual después de filtrar por similitud
            inicio = (pagina - 1) * por_pagina
            fin = min(inicio + por_pagina, total_resultados)
            pagina_resultados = contenidos_detallados[inicio:fin]
            
            return jsonify({
                'resultados': pagina_resultados,
                'paginacion': {
                    'pagina_actual': pagina,
                    'resultados_por_pagina': por_pagina,
                    'total_resultados': total_resultados,
                    'total_paginas': total_paginas
                },
                'consulta': contenido_texto,
                'metodo': 'meilisearch'
            })
        
        except Exception as e:
            print(f"Error al usar Meilisearch para búsqueda: {type(e).__name__}. Error message: {e}")
            print("Revirtiendo al método tradicional de búsqueda...")
            
    # Opción 2: Método tradicional de búsqueda por similaridad
    return busqueda_semantica_tradicional(contenido_texto, pagina, por_pagina, limite, filtros, similitud_min, ordenar_por, autores)

def busqueda_semantica_tradicional(contenido_texto, pagina, por_pagina, limite, filtros, similitud_min, ordenar_por, autores):
    """Función para realizar búsqueda semántica usando el método tradicional SQLite"""
    print("[INFO] Ejecutando búsqueda semántica con método tradicional")
    
    # Generar embedding del texto de consulta
    query_embedding = embedding_service.generar_embedding(contenido_texto)
    if not query_embedding:
        return jsonify({'error': 'No se pudo generar embedding para el contenido_texto'}), 400
    
    # Conectar a la base de datos
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Primero verificar si hay embeddings almacenados
    cursor.execute('SELECT COUNT(*) as total FROM contenido_embeddings')
    total_embeddings = cursor.fetchone()['total']
    
    if total_embeddings == 0:
        conn.close()
        return jsonify({
            'error': 'No hay embeddings generados', 
            'mensaje': 'Ejecute primero el script de procesamiento semántico'
        }), 400
    
    # Buscar contenidos con embeddings
    cursor.execute('''
        SELECT ce.contenido_id, ce.embedding
        FROM contenido_embeddings ce
    ''')
    
    resultados = []
    for row in cursor.fetchall():
        contenido_id = row['contenido_id']
        embedding = json.loads(row['embedding'])
        
        # Calcular similitud
        similitud = embedding_service.calcular_similitud(query_embedding, embedding)
        
        if similitud >= similitud_min:
            resultados.append({
                'contenido_id': contenido_id,
                'similitud': similitud
            })
    
    # Ordenar por similitud
    resultados.sort(key=lambda x: x['similitud'], reverse=True)
    
    # Aplicar límite total si se especifica
    if limite is not None and limite > 0:
        resultados = resultados[:limite]
    
    # Calcular paginación
    total_resultados = len(resultados)
    total_paginas = (total_resultados + por_pagina - 1) // por_pagina  # Redondeo hacia arriba
    
    if pagina < 1:
        pagina = 1
    elif pagina > total_paginas and total_paginas > 0:
        pagina = total_paginas
    
    # Obtener resultados de la página actual
    inicio = (pagina - 1) * por_pagina
    fin = min(inicio + por_pagina, total_resultados)
    resultados_pagina = resultados[inicio:fin]
    
    # Obtener detalles completos de los contenidos
    contenidos_detallados = []
    for resultado in resultados_pagina:
        cursor.execute('''
            SELECT c.id, c.contenido_texto, c.fecha_creacion, p.nombre as plataforma, f.nombre as fuente, c.autor
            FROM contenidos c
            JOIN plataformas p ON c.plataforma_id = p.id
            JOIN fuentes f ON c.fuente_id = f.id
            WHERE c.id = ?
        ''', (resultado['contenido_id'],))
        
        row = cursor.fetchone()
        if row:
            contenidos_detallados.append({
                'id': row['id'],
                'contenido_texto': row['contenido_texto'],
                'fecha': row['fecha_creacion'],
                'plataforma': row['plataforma'],
                'fuente': row['fuente'],
                'idioma': row['idioma'] if 'idioma' in row.keys() else 'es',
                'similitud': round(resultado['similitud'], 4),
                'autor': row['autor']
            })
    
    # Filtrar por autor si se especifica
    if autores:
        contenidos_detallados = [c for c in contenidos_detallados if c.get('autor') in autores]
    
    conn.close()
    
    # Devolver resultados con metadatos de paginación
    return jsonify({
        'resultados': contenidos_detallados,
        'paginacion': {
            'pagina_actual': pagina,
            'resultados_por_pagina': por_pagina,
            'total_resultados': total_resultados,
            'total_paginas': total_paginas
        },
        'consulta': contenido_texto,
        'metodo': 'tradicional'
    })

@app.route('/api/generar_rag', methods=['POST'])
def generar_rag():
    """
    Genera contenido utilizando el patrón RAG (Retrieval-Augmented Generation).
    
    Parámetros JSON:
    - tema: Tema sobre el que generar contenido (requerido)
    - tipo: Tipo de contenido (post, articulo, guion, resumen, analisis)
    - estilo: Estilo de escritura
    - num_resultados: Número de resultados a recuperar
    - proveedor: Proveedor de LLM (gemini, openai)
    - solo_prompt: Si solo se quiere obtener el prompt sin generar contenido
    """
    # Verificar que la solicitud contenga datos JSON
    if not request.is_json:
        return jsonify({"error": "La solicitud debe ser en formato JSON"}), 400
    
    # Obtener parámetros
    data = request.json
    tema = data.get('tema')
    tipo = data.get('tipo', 'post')
    estilo = data.get('estilo')
    num_resultados = data.get('num_resultados', 5)
    proveedor = data.get('proveedor', 'gemini')
    solo_prompt = data.get('solo_prompt', False)
    
    # Verificar parámetros requeridos
    if not tema:
        return jsonify({"error": "El tema es obligatorio"}), 400
    
    # Verificar tipo válido
    tipos_validos = ["post", "articulo", "guion", "resumen", "analisis"]
    if tipo not in tipos_validos:
        return jsonify({"error": f"Tipo de contenido no válido. Opciones: {', '.join(tipos_validos)}"}), 400
    
    # Verificar proveedor válido y disponible
    if not solo_prompt and (proveedor not in llm_providers or not llm_providers[proveedor]):
        proveedores_disponibles = list(llm_providers.keys())
        if not proveedores_disponibles:
            return jsonify({"error": "No hay proveedores de LLM disponibles. Configura las claves API en .env"}), 500
        else:
            return jsonify({
                "error": f"Proveedor '{proveedor}' no disponible. Opciones: {', '.join(proveedores_disponibles)}"
            }), 400
    
    # Paso 1: Recuperar contenido relevante
    try:
        # Realizar búsqueda semántica
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Usar la misma lógica de la función busqueda_semantica
        query = data.get('tema', '')
        page = 1
        per_page = num_resultados
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Determinar si usar Meilisearch o método tradicional
        usar_meilisearch_str = data.get('usar_meilisearch', 'true')
        usar_meilisearch = usar_meilisearch_str.lower() in ('true', '1', 't', 'y', 'yes')
        
        # Primero intentar usar Meilisearch
        if usar_meilisearch and is_meilisearch_running():
            print(f"[INFO] RAG: Usando Meilisearch para búsqueda de: {query}")
            resultados = buscar_contenido_meilisearch(query, conn, per_page)
        else:
            # Método tradicional como fallback
            print(f"[INFO] RAG: Usando método tradicional para búsqueda de: {query}")
            resultados = buscar_contenido_tradicional(query, conn, per_page)
        
        conn.close()
            
        if not resultados:
            return jsonify({
                "error": "No se encontraron contenidos relevantes para este tema"
            }), 404
        
        # Paso 2: Construir prompt
        # Extracción de textos
        textos_contexto = [f"Fragmento {i+1}:\n\"{item['contenido']}\"\n" 
                          for i, item in enumerate(resultados)]
        
        # Instrucciones según tipo
        instrucciones_tipo = {
            "post": "Escribe un post para redes sociales",
            "articulo": "Escribe un artículo detallado",
            "guion": "Escribe un guion para un video o presentación",
            "resumen": "Crea un resumen conciso de las ideas principales",
            "analisis": "Realiza un análisis profundo del tema"
        }.get(tipo.lower(), "Escribe un texto")
        
        # Instrucciones de estilo
        instrucciones_estilo = ""
        if estilo:
            instrucciones_estilo = f"Utiliza un estilo {estilo}. "
        
        # Prompt completo
        prompt = f"""
# TAREA
Actúa como un asistente de escritura experto. {instrucciones_tipo} sobre el tema: "{tema}".

# CONTEXTO
Los siguientes son fragmentos de texto auténticos relacionados con el tema. Utiliza EXCLUSIVAMENTE la información de estos fragmentos como base para tu respuesta:

{chr(10).join(textos_contexto)}

# INSTRUCCIONES ESPECÍFICAS
- Utiliza ÚNICAMENTE la información proporcionada en los fragmentos.
- Mantén el tono y perspectiva que se refleja en los textos originales.
- {instrucciones_estilo}Sé conciso pero informativo.
- No añadas información que no esté presente en los fragmentos proporcionados.
- No menciones que estás basándote en fragmentos o que tienes limitaciones.
- Finaliza con una reflexión o pregunta que invite a la interacción.

# RESPUESTA
"""
        
        # Si solo se quiere el prompt
        if solo_prompt:
            return jsonify({
                "prompt": prompt,
                "fragmentos_recuperados": len(resultados)
            })
        
        # Paso 3: Generar contenido con el LLM seleccionado
        try:
            contenido_generado = llm_providers[proveedor](prompt)
            
            # Paso 4: Devolver resultado
            return jsonify({
                "contenido": contenido_generado,
                "fragmentos_utilizados": len(resultados),
                "tema": tema,
                "tipo": tipo,
                "estilo": estilo,
                "proveedor": proveedor
            })
            
        except Exception as e:
            return jsonify({"error": f"Error del proveedor LLM: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Error en el proceso RAG: {str(e)}"}), 500

@app.route('/api/autores', methods=['GET'])
def get_autores():
    """Devuelve la lista de autores únicos en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT autor FROM contenidos WHERE autor IS NOT NULL AND autor != "" ORDER BY autor ASC')
    autores = [row['autor'] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'autores': autores})

@app.route('/api/estadisticas/autores', methods=['GET'])
def estadisticas_autores():
    """Devuelve la cantidad de contenidos, primer y último registro, y cantidad de temas por autor."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            c.autor, 
            COUNT(*) as cantidad, 
            MIN(c.fecha_creacion) as primer_registro, 
            MAX(c.fecha_creacion) as ultimo_registro,
            (SELECT COUNT(DISTINCT ct.tema_id) FROM contenido_tema ct WHERE ct.contenido_id IN (SELECT id FROM contenidos WHERE autor = c.autor)) as temas
        FROM contenidos c
        WHERE c.autor IS NOT NULL AND c.autor != ""
        GROUP BY c.autor
        ORDER BY cantidad DESC
    ''')
    data = [
        {
            'autor': row['autor'],
            'cantidad': row['cantidad'],
            'primer_registro': row['primer_registro'],
            'ultimo_registro': row['ultimo_registro'],
            'temas': row['temas']
        } for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(data)

def buscar_contenido_meilisearch(query, conn, per_page):
    """Busca contenido usando Meilisearch y embeddings vectoriales para RAG"""
    try:
        # Generar embedding para la consulta
        query_embedding = embedding_service.generar_embedding(query)
        if not query_embedding:
            print(f"[ADVERTENCIA] No se pudo generar embedding para: {query}")
            return []
        
        # Conexión a Meilisearch
        client = meilisearch.Client('http://127.0.0.1:7700')
        index = client.index('documentos')
        
        # Construir opciones para Meilisearch
        search_options = {
            'limit': per_page,
            'attributesToRetrieve': ['id', 'contenido_texto', 'fecha_creacion', 'autor', 'plataforma_id', 'fuente_id', 'idioma'],
            'vector': query_embedding,
            'hybrid': {
                'semanticRatio': 0.5  # Un valor entre 0 y 1 que determina cuánto peso se da a la parte semántica vs texto
            }
        }
        
        try:
            # Realizar búsqueda
            res = index.search(query, search_options)
            hits = res.get('hits', [])
            print(f"[INFO] RAG: Resultados de búsqueda: {len(hits)} documentos encontrados")
            
            # Formatear resultados
            resultados = []
            for doc in hits:
                score = doc.get('_semanticScore', 0)
                resultados.append({
                    'id': doc.get('id'),
                    'contenido': doc.get('contenido_texto'),
                    'fecha': doc.get('fecha_creacion', ''),
                    'plataforma': doc.get('plataforma_id', ''),
                    'fuente': doc.get('fuente_id', ''),
                    'idioma': doc.get('idioma', 'es'),
                    'similitud': round(score, 4) if score is not None else 0,
                    'autor': doc.get('autor', '')
                })
            
            return resultados
        except Exception as e:
            print(f"[ERROR] Error en búsqueda RAG con Meilisearch: {type(e).__name__}: {e}")
            # Si hay error, devolvemos lista vacía para que pueda continuar con método tradicional
            return []
    
    except Exception as e:
        print(f"[ERROR] Error general en búsqueda RAG Meilisearch: {e}")
        return []

# Función auxiliar para buscar contenido con método tradicional (para RAG)
def buscar_contenido_tradicional(query, conn, per_page):
    """Realiza una búsqueda por similitud vectorial usando el método tradicional"""
    try:
        cursor = conn.cursor()
        
        # Obtener embedding para la consulta
        query_embedding = embedding_service.generar_embedding(query)
        if not query_embedding:
            return []
        
        # Convertir a string para SQL
        query_embedding_str = json.dumps(query_embedding)
        
        # Buscar en la base de datos
        sql = """
        SELECT 
            c.id, 
            c.contenido_texto as contenido, 
            c.fecha_creacion as fecha, 
            p.nombre as plataforma, 
            f.nombre as fuente,
            ce.embedding
        FROM contenido_embeddings ce
        JOIN contenidos c ON ce.contenido_id = c.id
        JOIN plataformas p ON c.plataforma_id = p.id
        JOIN fuentes f ON c.fuente_id = f.id
        LIMIT ?
        """
        
        cursor.execute(sql, (per_page * 3,))  # Buscamos más para luego filtrar por similitud
        
        resultados = []
        for row in cursor.fetchall():
            embedding = json.loads(row['embedding']) if row['embedding'] else None
            
            if embedding:
                # Calcular similitud
                similitud = embedding_service.calcular_similitud(query_embedding, embedding)
                
                resultados.append({
                    'id': row['id'],
                    'contenido': row['contenido'],
                    'fecha': row['fecha'],
                    'plataforma': row['plataforma'],
                    'fuente': row['fuente'],
                    'similitud': similitud,
                })
        
        # Ordenar por similitud y limitar
        resultados.sort(key=lambda x: x['similitud'], reverse=True)
        return resultados[:per_page]
        
    except Exception as e:
        print(f"Error en búsqueda tradicional: {str(e)}")
        return []

# Registrar API de deduplicación si está disponible
if DEDUP_API_AVAILABLE:
    try:
        register_dedup_api(app)
    except Exception as e:
        print(f"[ERROR] No se pudo registrar la API de deduplicación: {e}")

if __name__ == '__main__':
    # Asegurarse de que existen los directorios necesarios
    os.makedirs(INDICES_DIR, exist_ok=True)
    
    # Inicializar Meilisearch indices
    inicializar_meilisearch_indices()
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
