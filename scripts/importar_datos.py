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

# Configuración de rutas
BASE_DIR = Path('/home/ubuntu/biblioteca_conocimiento')
DB_PATH = BASE_DIR / 'biblioteca.db'
SOURCE_DIR = Path('/home/ubuntu/staging/staging')
TARGET_DIR = BASE_DIR / 'contenido'

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

def importar_facebook(conn):
    """Importa datos de Facebook a la base de datos."""
    cursor = conn.cursor()
    source_file = SOURCE_DIR / 'facebook' / 'facebookIsmaGuimarais.json'
    target_dir = TARGET_DIR / 'redes_sociales' / 'facebook'
    
    if not source_file.exists():
        print(f"Archivo no encontrado: {source_file}")
        return
    
    # Crear directorio destino si no existe
    os.makedirs(target_dir, exist_ok=True)
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for i, post in enumerate(data):
            # Extraer texto del post (estructura simplificada, ajustar según estructura real)
            if 'data' in post and post['data']:
                texto = json.dumps(post['data'])
            else:
                texto = "Contenido no disponible"
            
            # Fecha de creación (usar fecha actual si no está disponible)
            fecha_creacion = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insertar en la base de datos
            cursor.execute(
                '''INSERT INTO contenidos 
                   (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                   VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                (texto, fecha_creacion, 1, 1, "", "Importado de Facebook")
            )
            
            # Guardar también como archivo individual
            post_id = cursor.lastrowid
            with open(target_dir / f"post_{post_id}.json", 'w', encoding='utf-8') as f:
                json.dump(post, f, ensure_ascii=False, indent=2)
        
        conn.commit()
        print(f"Importación de Facebook completada.")
    except Exception as e:
        print(f"Error al importar datos de Facebook: {e}")
        conn.rollback()

def importar_telegram(conn):
    """Importa datos de Telegram a la base de datos."""
    cursor = conn.cursor()
    source_files = [
        SOURCE_DIR / 'telegram' / 'debates_ismael_filtrado.ndjson',
        SOURCE_DIR / 'telegram' / 'telegramChanelIsmaelGuimarais.json',
        SOURCE_DIR / 'telegram' / '1000mensajesIsmaelDebatesGrupoTelegram.json',
        SOURCE_DIR / 'telegram' / 'datosbiblicoscanaladministradopormi.json'
    ]
    target_dir = TARGET_DIR / 'redes_sociales' / 'telegram'
    
    # Crear directorio destino si no existe
    os.makedirs(target_dir, exist_ok=True)
    
    for source_file in source_files:
        if not source_file.exists():
            print(f"Archivo no encontrado: {source_file}")
            continue
        
        try:
            # Determinar si es NDJSON o JSON
            if source_file.name.endswith('.ndjson'):
                # Procesar NDJSON línea por línea
                with open(source_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f):
                        try:
                            message = json.loads(line)
                            
                            # Solo importar mensajes del autor (Ismael)
                            if message.get('author') == 'Ismael' and message.get('text'):
                                texto = message.get('text', '')
                                fecha_str = message.get('date', '')
                                
                                try:
                                    fecha_creacion = datetime.datetime.fromisoformat(fecha_str).strftime('%Y-%m-%d %H:%M:%S')
                                except:
                                    fecha_creacion = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                # Insertar en la base de datos
                                cursor.execute(
                                    '''INSERT INTO contenidos 
                                       (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                                       VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                                    (texto, fecha_creacion, 3, 3, "", f"Mensaje ID: {message.get('id', '')}")
                                )
                                
                                # Guardar también como archivo individual
                                msg_id = cursor.lastrowid
                                with open(target_dir / f"mensaje_{msg_id}.json", 'w', encoding='utf-8') as f:
                                    json.dump(message, f, ensure_ascii=False, indent=2)
                        except json.JSONDecodeError:
                            print(f"Error al decodificar JSON en línea {line_num+1} de {source_file}")
                            continue
            else:
                # Procesar JSON regular
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Determinar si es un array o tiene otra estructura
                    if isinstance(data, list):
                        for message in data:
                            # Adaptar según la estructura real de los datos
                            if isinstance(message, dict):
                                texto = message.get('text', '')
                                if not texto:
                                    continue
                                
                                fecha_str = message.get('date', '')
                                try:
                                    fecha_creacion = datetime.datetime.fromisoformat(fecha_str).strftime('%Y-%m-%d %H:%M:%S')
                                except:
                                    fecha_creacion = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                # Determinar fuente (canal o grupo)
                                fuente_id = 4 if 'Chanel' in source_file.name else 3
                                
                                # Insertar en la base de datos
                                cursor.execute(
                                    '''INSERT INTO contenidos 
                                       (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                                       VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                                    (texto, fecha_creacion, fuente_id, 3, "", source_file.name)
                                )
                                
                                # Guardar también como archivo individual
                                msg_id = cursor.lastrowid
                                with open(target_dir / f"mensaje_{msg_id}.json", 'w', encoding='utf-8') as f:
                                    json.dump(message, f, ensure_ascii=False, indent=2)
            
            conn.commit()
            print(f"Importación de {source_file.name} completada.")
        except Exception as e:
            print(f"Error al importar datos de {source_file}: {e}")
            conn.rollback()

def importar_twitter(conn):
    """Importa datos de Twitter a la base de datos."""
    cursor = conn.cursor()
    source_file = SOURCE_DIR / 'twitter' / 'tweetsPlus250IsmaelGuimarais.json'
    target_dir = TARGET_DIR / 'redes_sociales' / 'twitter'
    
    if not source_file.exists():
        print(f"Archivo no encontrado: {source_file}")
        return
    
    # Crear directorio destino si no existe
    os.makedirs(target_dir, exist_ok=True)
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Adaptar según la estructura real de los datos
        if isinstance(data, list):
            for tweet in data:
                texto = tweet.get('text', '')
                if not texto:
                    continue
                
                # Intentar extraer fecha si está disponible
                fecha_creacion = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Insertar en la base de datos
                cursor.execute(
                    '''INSERT INTO contenidos 
                       (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                       VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                    (texto, fecha_creacion, 2, 2, "", "Tweet importado")
                )
                
                # Guardar también como archivo individual
                tweet_id = cursor.lastrowid
                with open(target_dir / f"tweet_{tweet_id}.json", 'w', encoding='utf-8') as f:
                    json.dump(tweet, f, ensure_ascii=False, indent=2)
        
        conn.commit()
        print(f"Importación de Twitter completada.")
    except Exception as e:
        print(f"Error al importar datos de Twitter: {e}")
        conn.rollback()

def importar_escritos(conn):
    """Importa escritos personales a la base de datos."""
    cursor = conn.cursor()
    source_dir = SOURCE_DIR / 'escritos'
    target_dir = TARGET_DIR / 'escritos'
    
    if not source_dir.exists():
        print(f"Directorio no encontrado: {source_dir}")
        return
    
    # Crear directorios destino si no existen
    os.makedirs(target_dir / 'ensayos', exist_ok=True)
    os.makedirs(target_dir / 'articulos', exist_ok=True)
    os.makedirs(target_dir / 'blogs', exist_ok=True)
    
    # Función para procesar un archivo markdown
    def procesar_archivo_md(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Extraer título del nombre del archivo o del contenido
            titulo = file_path.stem
            
            # Determinar categoría basada en longitud o contenido
            longitud = len(contenido)
            if longitud > 5000:
                categoria = 'ensayos'
            elif longitud > 1000:
                categoria = 'articulos'
            else:
                categoria = 'blogs'
            
            # Fecha de creación (usar fecha de modificación del archivo como aproximación)
            fecha_creacion = datetime.datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            # Insertar en la base de datos
            cursor.execute(
                '''INSERT INTO contenidos 
                   (contenido_texto, fecha_creacion, fecha_importacion, fuente_id, plataforma_id, url_original, contexto)
                   VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)''',
                (contenido, fecha_creacion, 5, 5, "", f"Archivo: {file_path.name}")
            )
            
            # Obtener ID del contenido insertado
            contenido_id = cursor.lastrowid
            
            # Copiar archivo al directorio correspondiente
            target_file = target_dir / categoria / f"{titulo}_{contenido_id}.md"
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            # Intentar clasificar por temas basado en palabras clave
            clasificar_por_temas(conn, contenido_id, contenido)
            
            return contenido_id
        except Exception as e:
            print(f"Error al procesar archivo {file_path}: {e}")
            return None
    
    # Recorrer archivos markdown en el directorio de escritos
    for file_path in source_dir.glob('**/*.md'):
        try:
            contenido_id = procesar_archivo_md(file_path)
            if contenido_id:
                print(f"Importado: {file_path.name} (ID: {contenido_id})")
        except Exception as e:
            print(f"Error al importar {file_path}: {e}")
    
    conn.commit()
    print(f"Importación de escritos completada.")

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

def main():
    """Función principal para ejecutar la importación de datos."""
    print("Iniciando importación de datos a la Biblioteca de Conocimiento Personal...")
    
    # Conectar a la base de datos
    conn = conectar_db()
    
    try:
        # Inicializar datos base
        inicializar_datos_base(conn)
        
        # Importar datos de diferentes fuentes
        importar_facebook(conn)
        importar_telegram(conn)
        importar_twitter(conn)
        importar_escritos(conn)
        
        # Generar índices
        generar_indices(conn)
        
        print("Importación de datos completada con éxito.")
    except Exception as e:
        print(f"Error durante la importación: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
