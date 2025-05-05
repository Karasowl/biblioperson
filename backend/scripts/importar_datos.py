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
import argparse

load_dotenv()

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'biblioteca.db'
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
    
    # Verificar si la tabla temas existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temas'")
    if cursor.fetchone():
        try:
            # Insertar temas principales solo si la tabla existe
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
        except sqlite3.Error as e:
            print(f"Aviso: No se pudieron inicializar temas: {e}")
    else:
        print("Tabla de temas no encontrada, omitiendo inicialización de temas")
    
    conn.commit()

def eliminar_duplicados_por_texto(conn):
    """Elimina duplicados exactos en la tabla contenidos, dejando solo la primera aparición de cada texto."""
    cursor = conn.cursor()
    print("Eliminando duplicados exactos por texto en la tabla 'contenidos'...")
    cursor.execute('''
        DELETE FROM contenidos
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM contenidos
            GROUP BY contenido_texto
        )
    ''')
    conn.commit()
    print("Duplicados eliminados.")

def clasificar_por_temas(conn, contenido_id, texto):
    """Clasifica un contenido por temas basado en palabras clave. 
    Si las tablas de temas no existen, esta función no hace nada."""
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla temas existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temas'")
        if not cursor.fetchone():
            # Si la tabla no existe, salir silenciosamente
            return
        
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
    except sqlite3.Error as e:
        print(f"Aviso: No se pudo clasificar por temas: {e}")
    except Exception as e:
        print(f"Error en clasificación por temas: {e}")

def generar_indices(conn, base_dir):
    """Genera archivos de índices para facilitar el acceso."""
    cursor = conn.cursor()
    indices_dir = base_dir / 'shared' / 'indices'
    
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
    
    # Verificar si la tabla temas existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temas'")
    if cursor.fetchone():
        # Generar índice temático solo si existe la tabla temas
        try:
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
        except sqlite3.Error:
            print("No se pudo generar el índice temático (las tablas de temas podrían estar incompletas)")
    else:
        print("No se generó el índice temático porque no existe la tabla de temas")
    
    # Generar archivo NDJSON con todo el contenido
    cursor.execute('''
        SELECT c.id, c.contenido_texto, c.fecha_creacion, p.nombre as plataforma, f.nombre as fuente,
               c.url_original, c.contexto, c.autor
        FROM contenidos c
        JOIN plataformas p ON c.plataforma_id = p.id
        JOIN fuentes f ON c.fuente_id = f.id
    ''')
    
    with open(indices_dir / 'contenido_completo.ndjson', 'w', encoding='utf-8') as f:
        for row in cursor.fetchall():
            # Crear objeto con los datos básicos
            contenido_obj = {
                'id': row['id'],
                'texto': row['contenido_texto'],
                'fecha': row['fecha_creacion'],
                'plataforma': row['plataforma'],
                'fuente': row['fuente'],
                'url': row['url_original'],
                'contexto': row['contexto'],
                'autor': row['autor'],
                'temas': []
            }
            
            # Intentar obtener temas relacionados solo si la tabla existe
            try:
                cursor2 = conn.cursor()
                cursor2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temas'")
                if cursor2.fetchone():
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
                    
                    contenido_obj['temas'] = temas_contenido
            except:
                pass  # Si hay error, simplemente dejamos la lista de temas vacía
            
            # Escribir como línea NDJSON
            f.write(json.dumps(contenido_obj, ensure_ascii=False) + '\n')
    
    print("Generación de índices completada.")

def importar_contenido(conn, contenido_dir):
    """Importa todo el contenido de forma recursiva, sin importar la estructura de carpetas."""
    cursor = conn.cursor()
    
    print(f"Iniciando importación recursiva desde: {contenido_dir}")
    
    # Recorrer todos los archivos en todas las subcarpetas
    for file_path in Path(contenido_dir).rglob('*'):
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
                         f"Archivo: {file_path.relative_to(contenido_dir)}")
                    )
                    
                    contenido_id = cursor.lastrowid
                    print(f"Importado: {file_path.relative_to(contenido_dir)} (ID: {contenido_id})")
                    
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

def importar_desde_ndjson(conn, archivo_ndjson):
    """Importa datos desde un archivo NDJSON unificado."""
    cursor = conn.cursor()
    
    if not Path(archivo_ndjson).exists():
        print(f"Error: El archivo {archivo_ndjson} no existe.")
        return
        
    print(f"Importando desde archivo NDJSON: {archivo_ndjson}")
    
    # Contador de entradas
    total_entradas = 0
    entradas_importadas = 0
    
    try:
        with open(archivo_ndjson, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_entradas += 1
                
                try:
                    # Convertir la línea JSON a un objeto Python
                    entrada = json.loads(line)
                    
                    if not isinstance(entrada, dict):
                        continue
                    
                    # Extraer datos relevantes
                    texto = entrada.get('texto', '')
                    fecha = entrada.get('fecha', '')
                    plataforma = entrada.get('plataforma', 'Desconocida')
                    fuente = entrada.get('fuente', 'Desconocida')
                    autor = entrada.get('autor', 'Ismael')  # Valor por defecto: 'Ismael'
                    
                    # Normalizar la fecha
                    if fecha:
                        try:
                            # Verificar si es un entero (timestamp Unix)
                            if isinstance(fecha, int):
                                dt = datetime.datetime.fromtimestamp(fecha)
                                fecha_db = dt.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                # Intentar parsear la fecha (formato flexible)
                                dt = datetime.datetime.strptime(fecha, '%Y-%m-%d')
                                fecha_db = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                # Segundo intento con formato más flexible
                                dt = datetime.datetime.strptime(fecha, '%Y-%m')
                                fecha_db = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                # Si no se puede parsear, usar fecha actual
                                fecha_db = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        fecha_db = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Determinar ID de plataforma
                    cursor.execute('SELECT id FROM plataformas WHERE nombre LIKE ?', (f'%{plataforma}%',))
                    plataforma_row = cursor.fetchone()
                    if plataforma_row:
                        plataforma_id = plataforma_row['id']
                    else:
                        # Insertar nueva plataforma
                        cursor.execute(
                            'INSERT INTO plataformas (nombre, tipo) VALUES (?, ?)',
                            (plataforma, 'desconocido')
                        )
                        plataforma_id = cursor.lastrowid
                    
                    # Determinar ID de fuente
                    cursor.execute('SELECT id FROM fuentes WHERE nombre LIKE ?', (f'%{fuente}%',))
                    fuente_row = cursor.fetchone()
                    if fuente_row:
                        fuente_id = fuente_row['id']
                    else:
                        # Insertar nueva fuente
                        cursor.execute(
                            'INSERT INTO fuentes (nombre, descripcion) VALUES (?, ?)',
                            (fuente, f'Fuente importada: {fuente}')
                        )
                        fuente_id = cursor.lastrowid
                    
                    # Insertar en la base de datos (añadiendo el campo autor)
                    cursor.execute(
                        '''INSERT INTO contenidos 
                           (contenido_texto, fecha_creacion, fecha_importacion, 
                            fuente_id, plataforma_id, url_original, contexto, autor)
                           VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)''',
                        (texto, 
                         fecha_db,
                         fuente_id,
                         plataforma_id,
                         entrada.get('url', ''),
                         entrada.get('contexto', f'Importado de {archivo_ndjson}'),
                         autor)
                    )
                    
                    contenido_id = cursor.lastrowid
                    
                    # Clasificar por temas
                    clasificar_por_temas(conn, contenido_id, texto)
                    
                    entradas_importadas += 1
                    
                    # Informar progreso cada 1000 entradas
                    if entradas_importadas % 1000 == 0:
                        print(f"Importadas {entradas_importadas} entradas de {total_entradas} procesadas.")
                    
                except json.JSONDecodeError:
                    print(f"Error: Línea {line_num} no es un JSON válido. Omitiendo.")
                    continue
                except Exception as e:
                    print(f"Error al procesar entrada {line_num}: {e}")
                    continue
                
                # Hacer commit cada cierto número de entradas
                if entradas_importadas % 5000 == 0:
                    conn.commit()
        
        # Hacer commit final
        conn.commit()
        print(f"Importación completada: {entradas_importadas} entradas importadas de {total_entradas} procesadas.")
        
    except Exception as e:
        print(f"Error durante la importación desde NDJSON: {e}")

def agregar_contenido(conn, texto, fecha_creacion, fuente_id=None, plataforma_id=None, url_original=None, contexto=None, autor=None, idioma='es'):
    """Agrega un nuevo contenido a la base de datos, incluyendo el idioma."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contenidos (contenido_texto, fecha_creacion, fuente_id, plataforma_id, url_original, contexto, autor, idioma)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (texto, fecha_creacion, fuente_id, plataforma_id, url_original, contexto, autor, idioma))
    return cursor.lastrowid

def main():
    """Función principal para ejecutar la importación de datos."""
    # Añadir parser de argumentos
    parser = argparse.ArgumentParser(description='Importar datos a la Biblioteca de Conocimiento Personal')
    parser.add_argument('--base-dir', default=str(BASE_DIR), help='Directorio base del proyecto')
    parser.add_argument('--contenido-dir', default=None, help='Directorio que contiene los archivos a importar')
    parser.add_argument('--db-path', default=str(DB_PATH), help='Ruta a la base de datos SQLite')
    parser.add_argument('--ndjson-file', default=None, help='Ruta al archivo NDJSON unificado para importar (opcional)')
    
    args = parser.parse_args()
    
    # Actualizar rutas con argumentos
    base_dir = Path(args.base_dir)
    contenido_dir = Path(args.contenido_dir) if args.contenido_dir else None
    db_path = Path(args.db_path)
    
    # Directorio de importación
    import_dir = base_dir / 'data' / 'import'
    
    # Determinar los archivos NDJSON a utilizar
    ndjson_files = []
    if args.ndjson_file:
        # Si se especificó un archivo, usar solo ese
        ndjson_files = [args.ndjson_file]
    else:
        # Buscar TODOS los archivos NDJSON en el directorio de importación
        ndjson_files_found = list(import_dir.glob('*.ndjson'))
        if ndjson_files_found:
            ndjson_files = [str(f) for f in ndjson_files_found]
            print(f"Se encontraron {len(ndjson_files)} archivos NDJSON en {import_dir}:")
            for i, f in enumerate(ndjson_files_found, 1):
                print(f"  {i}. {f.name}")
        else:
            print(f"Error: No se encontraron archivos NDJSON en {import_dir}")
            print("Por favor, copie sus archivos NDJSON a esta ubicación antes de importar.")
            return
    
    print(f"Iniciando importación de datos a la Biblioteca de Conocimiento Personal...")
    print(f"Base Dir: {base_dir}")
    if contenido_dir:
        print(f"Contenido Dir: {contenido_dir}")
    print(f"DB Path: {db_path}")
    
    # Verificar existencia de los archivos NDJSON
    for ndjson_file in ndjson_files:
        if not Path(ndjson_file).exists():
            print(f"Error: El archivo NDJSON especificado no existe: {ndjson_file}")
            print(f"Por favor, asegúrese de que el archivo existe en la ubicación correcta.")
            return
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Inicializar datos base
        inicializar_datos_base(conn)
        # Eliminar duplicados antes de importar (opcional, puedes moverlo después de importar si prefieres)
        eliminar_duplicados_por_texto(conn)
        # Importar desde todos los archivos NDJSON encontrados
        for ndjson_file in ndjson_files:
            print(f"\n=== Procesando archivo: {Path(ndjson_file).name} ===")
            importar_desde_ndjson(conn, ndjson_file)
        # Eliminar duplicados después de importar (más seguro)
        eliminar_duplicados_por_texto(conn)
        # Generar índices
        generar_indices(conn, base_dir)
        
        print("Importación de datos completada con éxito.")
    except Exception as e:
        print(f"Error durante la importación: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
