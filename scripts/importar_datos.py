#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para importar datos desde los archivos existentes a la base de datos
de la Biblioteca de Conocimiento Personal.
"""

import os
import json
import sqlite3
import datetime
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'biblioteca.db'
CONTENIDO_DIR = Path(os.getenv("CONTENIDO_DIR", BASE_DIR / "contenido"))
if not CONTENIDO_DIR.is_absolute():
    CONTENIDO_DIR = BASE_DIR / CONTENIDO_DIR

def conectar_db():
    """Establece conexión con la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_datos_base(conn):
    """Inicializa datos básicos en las tablas de referencia."""
    cursor = conn.cursor()
    
    # Insertar plataformas
    plataformas = [
        (1, 'Facebook', 'red_social'),
        (2, 'Twitter', 'red_social'),
        (3, 'Telegram', 'mensajeria'),
        (4, 'Blog', 'web'),
        (5, 'Escritos', 'documento')
    ]
    cursor.executemany(
        'INSERT OR IGNORE INTO plataformas (id, nombre, tipo) VALUES (?, ?, ?)',
        plataformas
    )
    
    # Insertar fuentes
    fuentes = [
        (1, 'Perfil personal Facebook', 'Publicaciones en perfil personal de Facebook'),
        (2, 'Cuenta Twitter', 'Tweets desde cuenta personal'),
        (3, 'Grupos Telegram', 'Mensajes en grupos de Telegram'),
        (4, 'Canal Telegram', 'Publicaciones en canal de Telegram'),
        (5, 'Escritos personales', 'Documentos y ensayos personales'),
        (6, 'Poesías', 'Textos poéticos'),
        (7, 'Canciones', 'Letras de canciones')
    ]
    cursor.executemany(
        'INSERT OR IGNORE INTO fuentes (id, nombre, descripcion) VALUES (?, ?, ?)',
        fuentes
    )
    
    # Insertar temas principales
    temas = [
        (1, 'Religión', 'Temas relacionados con religión y espiritualidad', None),
        (2, 'Cristianismo', 'Temas específicos del cristianismo', 1),
        (3, 'Judaísmo', 'Temas relacionados con el judaísmo', 1),
        (4, 'Política', 'Temas políticos y de gobierno', None),
        (5, 'Libertarianismo', 'Filosofía política libertaria', 4),
        (6, 'Filosofía', 'Temas filosóficos generales', None),
        (7, 'Arte', 'Expresiones artísticas', None),
        (8, 'Poesía', 'Poesía y expresión lírica', 7),
        (9, 'Música', 'Temas relacionados con música', 7),
        (10, 'Sociedad', 'Temas sociales y culturales', None)
    ]
    cursor.executemany(
        'INSERT OR IGNORE INTO temas (id, nombre, descripcion, tema_padre_id) VALUES (?, ?, ?, ?)',
        temas
    )
    
    conn.commit()

def clasificar_por_temas(conn, contenido_id, texto):
    """Clasifica un contenido por temas basado en palabras clave."""
    cursor = conn.cursor()
    
    # Definir palabras clave para cada tema
    temas_keywords = {
        1: ['religión', 'religioso', 'espiritual', 'fe', 'creencia', 'dios'],
        2: ['cristo', 'jesús', 'biblia', 'evangelio', 'cristiano', 'iglesia'],
        3: ['judaísmo', 'judío', 'torá', 'israel', 'rabino'],
        4: ['política', 'gobierno', 'estado', 'nación', 'democracia'],
        5: ['libertad', 'libertario', 'libre mercado', 'individualismo'],
        6: ['filosofía', 'filósofo', 'pensamiento', 'razón', 'lógica'],
        7: ['arte', 'artístico', 'estética', 'belleza', 'expresión'],
        8: ['poesía', 'poema', 'verso', 'estrofa', 'lírica'],
        9: ['música', 'canción', 'melodía', 'ritmo', 'armonía'],
        10: ['sociedad', 'social', 'cultura', 'comunidad', 'pueblo']
    }
    
    # Texto normalizado para búsqueda
    texto_norm = texto.lower()
    
    # Buscar coincidencias y calcular relevancia
    for tema_id, keywords in temas_keywords.items():
        relevancia = 0
        for keyword in keywords:
            count = texto_norm.count(keyword)
            if count > 0:
                relevancia += count * 0.1  # Ajustar factor según necesidad
        
        if relevancia > 0:
            # Limitar relevancia a un máximo de 1.0
            relevancia = min(relevancia, 1.0)
            
            # Insertar relación contenido-tema
            cursor.execute(
                '''INSERT INTO contenido_tema (contenido_id, tema_id, relevancia)
                   VALUES (?, ?, ?)''',
                (contenido_id, tema_id, relevancia)
            )

def generar_indices(conn):
    """Genera archivos de índices para facilitar el acceso."""
    cursor = conn.cursor()
    indices_dir = BASE_DIR / 'indices'
    
    # Crear directorio si no existe
    os.makedirs(indices_dir, exist_ok=True)
    
    # Generar índice cronológico
    cursor.execute('''
        SELECT c.id, c.contenido_texto, c.fecha_creacion, p.nombre as plataforma, f.nombre as fuente
        FROM contenidos c
        JOIN plataformas p ON c.plataforma_id = p.id
        JOIN fuentes f ON c.fuente_id = f.id
        ORDER BY c.fecha_creacion
    ''')
    
    cronologia = []
    for row in cursor.fetchall():
        cronologia.append({
            'id': row['id'],
            'texto': row['contenido_texto'][:200] + '...' if len(row['contenido_texto']) > 200 else row['contenido_texto'],
            'fecha': row['fecha_creacion'],
            'plataforma': row['plataforma'],
            'fuente': row['fuente']
        })
    
    with open(indices_dir / 'cronologico.json', 'w', encoding='utf-8') as f:
        json.dump(cronologia, f, ensure_ascii=False, indent=2)
    
    # Generar índice temático
    cursor.execute('''
        SELECT t.id, t.nombre, t.descripcion, t.tema_padre_id
        FROM temas t
        ORDER BY t.tema_padre_id NULLS FIRST, t.nombre
    ''')
    
    temas = {}
    for row in cursor.fetchall():
        tema_id = row['id']
        temas[tema_id] = {
            'id': tema_id,
            'nombre': row['nombre'],
            'descripcion': row['descripcion'],
            'padre_id': row['tema_padre_id'],
            'contenidos': []
        }
    
    # Añadir contenidos a cada tema
    for tema_id in temas:
        cursor.execute('''
            SELECT c.id, c.contenido_texto, c.fecha_creacion, ct.relevancia
            FROM contenidos c
            JOIN contenido_tema ct ON c.id = ct.contenido_id
            WHERE ct.tema_id = ?
            ORDER BY ct.relevancia DESC
        ''', (tema_id,))
        
        for row in cursor.fetchall():
            temas[tema_id]['contenidos'].append({
                'id': row['id'],
                'texto': row['contenido_texto'][:200] + '...' if len(row['contenido_texto']) > 200 else row['contenido_texto'],
                'fecha': row['fecha_creacion'],
                'relevancia': row['relevancia']
            })
    
    # Convertir a estructura jerárquica
    jerarquia_temas = []
    for tema_id, tema in temas.items():
        if tema['padre_id'] is None:
            # Es un tema raíz
            tema_jerarquico = {
                'id': tema['id'],
                'nombre': tema['nombre'],
                'descripcion': tema['descripcion'],
                'contenidos': tema['contenidos'],
                'subtemas': []
            }
            
            # Añadir subtemas
            for subtema_id, subtema in temas.items():
                if subtema['padre_id'] == tema_id:
                    tema_jerarquico['subtemas'].append({
                        'id': subtema['id'],
                        'nombre': subtema['nombre'],
                        'descripcion': subtema['descripcion'],
                        'contenidos': subtema['contenidos']
                    })
            
            jerarquia_temas.append(tema_jerarquico)
    
    with open(indices_dir / 'temas_jerarquia.json', 'w', encoding='utf-8') as f:
        json.dump(jerarquia_temas, f, ensure_ascii=False, indent=2)
    
    # Generar archivo NDJSON con todo el contenido
    cursor.execute('''
        SELECT c.id, c.contenido_texto, c.fecha_creacion, p.nombre as plataforma, f.nombre as fuente,
               c.url_original, c.contexto
        FROM contenidos c
        JOIN plataformas p ON c.plataforma_id = p.id
        JOIN fuentes f ON c.fuente_id = f.id
    ''')
    
    with open(indices_dir / 'contenido_completo.ndjson', 'w', encoding='utf-8') as f:
        for row in cursor.fetchall():
            # Obtener temas relacionados
            cursor2 = conn.cursor()
            cursor2.execute('''
                SELECT t.nombre, ct.relevancia
                FROM temas t
                JOIN contenido_tema ct ON t.id = ct.tema_id
                WHERE ct.contenido_id = ?
            ''', (row['id'],))
            
            temas_contenido = []
            for tema_row in cursor2.fetchall():
                temas_contenido.append({
                    'nombre': tema_row['nombre'],
                    'relevancia': tema_row['relevancia']
                })
            
            # Crear objeto completo
            contenido_obj = {
                'id': row['id'],
                'texto': row['contenido_texto'],
                'fecha': row['fecha_creacion'],
                'plataforma': row['plataforma'],
                'fuente': row['fuente'],
                'url': row['url_original'],
                'contexto': row['contexto'],
                'temas': temas_contenido
            }
            
            # Escribir como línea NDJSON
            f.write(json.dumps(contenido_obj, ensure_ascii=False) + '\n')
    
    print("Generación de índices completada.")

def importar_contenido(conn):
    """Importa todo el contenido de forma recursiva, sin importar la estructura de carpetas."""
    cursor = conn.cursor()
    
    print(f"Iniciando importación recursiva desde: {CONTENIDO_DIR}")
    
    # Recorrer todos los archivos en todas las subcarpetas
    for file_path in Path(CONTENIDO_DIR).rglob('*'):
        try:
            if file_path.is_file():  # Solo procesar archivos, no carpetas
                # Procesar archivos según su extensión
                if file_path.suffix.lower() == '.md':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    
                    # Determinar fuente_id y plataforma_id según el contexto
                    fuente_id = 5  # Por defecto, escritos personales
                    plataforma_id = 5  # Por defecto, Escritos
                    
                    # Determinar tipo según la ruta
                    path_str = str(file_path).lower()
                    if 'poesias' in path_str or 'poesía' in path_str or 'poemas' in path_str:
                        fuente_id = 6  # Poesías
                    elif 'canciones' in path_str or 'letras' in path_str:
                        fuente_id = 7  # Canciones
                    
                    # Insertar en la base de datos
                    cursor.execute(
                        '''INSERT INTO contenidos 
                           (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                           VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                        (contenido, 
                         datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                         fuente_id,
                         plataforma_id,
                         "",
                         f"Archivo: {file_path.relative_to(CONTENIDO_DIR)}")
                    )
                    
                    contenido_id = cursor.lastrowid
                    print(f"Importado: {file_path.relative_to(CONTENIDO_DIR)} (ID: {contenido_id})")
                    
                    # Clasificar por temas
                    clasificar_por_temas(conn, contenido_id, contenido)
                
                elif file_path.suffix.lower() == '.json':
                    # Procesar archivos JSON (Facebook, Twitter, Telegram)
                    if 'facebook' in str(file_path).lower():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        texto = json.dumps(item.get('data', item))
                                        cursor.execute(
                                            '''INSERT INTO contenidos 
                                               (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                                               VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                                            (texto,
                                             datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                             1, 1, "", "Importado de Facebook")
                                        )
                    elif 'twitter' in str(file_path).lower():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for tweet in data:
                                    if isinstance(tweet, dict) and 'text' in tweet:
                                        cursor.execute(
                                            '''INSERT INTO contenidos 
                                               (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                                               VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                                            (tweet['text'],
                                             datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                             2, 2, "", "Importado de Twitter")
                                        )
                    elif 'telegram' in str(file_path).lower():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for msg in data:
                                    if isinstance(msg, dict) and 'text' in msg:
                                        cursor.execute(
                                            '''INSERT INTO contenidos 
                                               (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                                               VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                                            (msg['text'],
                                             datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                             3, 3, "", "Importado de Telegram")
                                        )
                
                elif file_path.suffix.lower() == '.ndjson':
                    # Procesar archivos NDJSON
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                msg = json.loads(line)
                                if isinstance(msg, dict) and 'text' in msg:
                                    cursor.execute(
                                        '''INSERT INTO contenidos 
                                           (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                                           VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                                        (msg['text'],
                                         datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                         3, 3, "", "Importado de Telegram NDJSON")
                                    )
                            except json.JSONDecodeError:
                                continue
                
                # Hacer commit cada cierto número de archivos para evitar transacciones muy largas
                conn.commit()
                
        except Exception as e:
            print(f"Error al procesar {file_path}: {e}")
            continue
    
    conn.commit()
    print("Importación de contenido completada.")

def main():
    """Función principal para ejecutar la importación de datos."""
    print("Iniciando importación de datos a la Biblioteca de Conocimiento Personal...")
    
    # Conectar a la base de datos
    conn = conectar_db()
    
    try:
        # Inicializar datos base
        inicializar_datos_base(conn)
        
        # Importar todo el contenido de forma recursiva
        importar_contenido(conn)
        
        # Generar índices
        generar_indices(conn)
        
        print("Importación de datos completada con éxito.")
    except Exception as e:
        print(f"Error durante la importación: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
