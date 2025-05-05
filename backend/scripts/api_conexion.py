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
CORS(app)

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
    texto = request.args.get('contenido_texto')
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
    
    if texto:
        # Verificar si existe la tabla fts
        if tabla_existe(conn, 'contenidos_fts'):
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
            'contenido': row['contenido_texto'],
            'fecha': row['fecha_creacion'],
            'plataforma': row['plataforma'],
            'fuente': row['fuente'],
            'idioma': row['idioma'] if 'idioma' in row.keys() else 'es',
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
            'contenido': row['contenido_texto'],
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
            }
        ],
        'ejemplos': [
            {'descripcion': 'Obtener información general', 'url': '/api/info'},
            {'descripcion': 'Buscar contenido sobre cristianismo', 'url': '/api/contenido?tema=Cristianismo'},
            {'descripcion': 'Obtener material para generar un artículo sobre política', 'url': '/api/generar?tema=Política&tipo=articulo&longitud=largo'},
            {'descripcion': 'Buscar contenido semánticamente similar a un texto', 'url': '/api/busqueda/semantica?texto=La importancia de la fe&pagina=1&por_pagina=20'}
        ]
    })

# Añadir importación del servicio de embeddings
from embedding_service import EmbeddingService
import json

# Inicializar el servicio
embedding_service = EmbeddingService()

@app.route('/api/busqueda/semantica', methods=['GET'])
def busqueda_semantica():
    """
    Realiza una búsqueda semántica en el contenido
    
    Parámetros:
    - texto: Texto de consulta
    - pagina: Número de página (default: 1)
    - por_pagina: Resultados por página (default: 10, max: 50)
    """
    texto = request.args.get('contenido_texto', '')
    if not texto:
        return jsonify({'error': 'No se proporcionó texto para buscar'}), 400
        
    # Parámetros de paginación
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 10, type=int)
    limite = request.args.get('limite', None, type=int)
    
    # Leer parámetro de similitud mínima
    similitud_min = request.args.get('similitud_min', None, type=float)
    if similitud_min is None:
        similitud_min = 0.0  # Por defecto, sin filtro
    
    # Limitar tamaño máximo por página para evitar sobrecarga
    if por_pagina > 50000:
        por_pagina = 50000
    if limite is not None and limite > 0:
        max_resultados = min(limite, 50000)
    else:
        max_resultados = None
    
    # Generar embedding del texto de consulta
    query_embedding = embedding_service.generar_embedding(texto)
    if not query_embedding:
        return jsonify({'error': 'No se pudo generar embedding para el texto'}), 400
    
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
    if max_resultados is not None:
        resultados = resultados[:max_resultados]
    
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
                'contenido': row['contenido_texto'],
                'fecha': row['fecha_creacion'],
                'plataforma': row['plataforma'],
                'fuente': row['fuente'],
                'idioma': row['idioma'] if 'idioma' in row.keys() else 'es',
                'similitud': round(resultado['similitud'], 4),
                'autor': row['autor']
            })
    
    # Filtrar por autor si se especifica
    autor_param = request.args.get('autor')
    if autor_param:
        autores = [a.strip() for a in autor_param.split(',') if a.strip()]
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
        'consulta': texto
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
        
        # Obtener embeddings
        from embedding_service import get_embedding
        query_embedding = get_embedding(query)
        if not query_embedding:
            return jsonify({"error": "Failed to generate embedding for query"}), 500
        
        # Realizar búsqueda por similitud
        query_embedding_str = json.dumps(query_embedding)
        
        sql = """
        SELECT 
            c.id, 
            c.contenido_texto as contenido, 
            c.fecha_creacion as fecha, 
            p.nombre as plataforma, 
            f.nombre as fuente,
            similarity(e.vector, ?) as similitud
        FROM embeddings e
        JOIN contenidos c ON e.contenido_id = c.id
        JOIN plataformas p ON c.plataforma_id = p.id
        JOIN fuentes f ON c.fuente_id = f.id
        ORDER BY similitud DESC
        LIMIT ?
        """
        
        resultados = []
        try:
            cursor.execute(sql, (query_embedding_str, per_page))
            
            for row in cursor.fetchall():
                # Recuperar temas asociados
                cursor.execute("""
                    SELECT t.id, t.nombre
                    FROM temas t
                    JOIN contenido_tema ct ON t.id = ct.tema_id
                    WHERE ct.contenido_id = ?
                """, (row['id'],))
                
                temas = []
                for tema_row in cursor.fetchall():
                    temas.append({
                        'id': tema_row['id'],
                        'nombre': tema_row['nombre'],
                        'relevancia': 1.0 # Por ahora, asignamos relevancia máxima
                    })
                
                resultados.append({
                    'id': row['id'],
                    'contenido': row['contenido'],
                    'fecha': row['fecha'],
                    'plataforma': row['plataforma'],
                    'fuente': row['fuente'],
                    'similitud': row['similitud'],
                    'temas': temas
                })
        except Exception as e:
            conn.close()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        
        if not resultados:
            conn.close()
            return jsonify({"error": "No se encontraron resultados relevantes para el tema"}), 404
        
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
            conn.close()
            return jsonify({
                "prompt": prompt,
                "fragmentos_recuperados": len(resultados)
            })
        
        # Paso 3: Generar contenido con el LLM seleccionado
        try:
            contenido_generado = llm_providers[proveedor](prompt)
            
            # Paso 4: Devolver resultado
            conn.close()
            return jsonify({
                "contenido": contenido_generado,
                "fragmentos_utilizados": len(resultados),
                "tema": tema,
                "tipo": tipo,
                "estilo": estilo,
                "proveedor": proveedor
            })
            
        except Exception as e:
            conn.close()
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

if __name__ == '__main__':
    # Asegurarse de que existen los directorios necesarios
    os.makedirs(INDICES_DIR, exist_ok=True)
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
