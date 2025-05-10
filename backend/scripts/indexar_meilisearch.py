#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import threading
import queue
import json
import logging
import sqlite3
import argparse
import concurrent.futures
import signal
import sys
from datetime import datetime
from dotenv import load_dotenv
import meilisearch
import requests

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("indexacion_meilisearch.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Configuración de Meilisearch
MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_API_KEY = os.getenv("MEILISEARCH_API_KEY", "")  # Por defecto sin clave
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5000"))
DOCS_PER_REQUEST = int(os.getenv("DOCS_PER_REQUEST", "1000"))
NUM_THREADS = int(os.getenv("NUM_THREADS", "8"))
TIMEOUT = int(os.getenv("TIMEOUT", "60"))  # timeout en segundos
INDEX_NAME = os.getenv("INDEX_NAME", "documentos")

# Parámetros de configuración optimizados para alto rendimiento
WAIT_TIME_BETWEEN_BATCHES = 0.5  # Reducido a 0.5 segundos
MAX_WAIT_TIME = 30  # 30 segundos máximo de espera
MAX_RETRY_ATTEMPTS = 3  # 3 intentos si falla

def listar_tablas(db_path):
    """
    Lista todas las tablas disponibles en la base de datos
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Consulta para obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [tabla[0] for tabla in tablas]
    except Exception as e:
        logger.error(f"Error al listar tablas: {str(e)}")
        return []

class MeilisearchIndexer:
    def __init__(self, table_name="contenidos"):
        # Si la clave API está vacía, no la usamos
        if MEILISEARCH_API_KEY:
            self.client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_API_KEY, timeout=TIMEOUT)
        else:
            self.client = meilisearch.Client(MEILISEARCH_URL, timeout=TIMEOUT)
            
        self.index = self.client.index(INDEX_NAME)
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.documents_indexed = 0
        self.total_documents = 0
        self.failed_documents = []
        self.table_name = table_name
        self.running = True
        
        # Ruta a la base de datos SQLite
        self.db_path = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "biblioteca.db"))
        
    def obtener_total_documentos(self):
        """
        Consulta cuántos documentos hay que indexar en total desde la base de datos SQLite
        """
        try:
            # Conectar a la base de datos SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ejecutar consulta para contar documentos
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            # Cerrar conexión
            cursor.close()
            conn.close()
            
            self.total_documents = count
            logger.info(f"Total de documentos a indexar (desde tabla '{self.table_name}'): {self.total_documents}")
            return self.total_documents
        except Exception as e:
            logger.error(f"Error al obtener el total de documentos de la tabla '{self.table_name}': {str(e)}")
            # En caso de error, podemos usar un valor predeterminado
            logger.warning("Usando valor predeterminado para total de documentos")
            self.total_documents = 0
            return self.total_documents
    
    def obtener_documentos(self, offset, limit):
        """
        Obtiene un lote de documentos para indexar desde la base de datos SQLite
        incluyendo sus embeddings
        """
        try:
            # Conectar a la base de datos SQLite
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
            cursor = conn.cursor()
            
            # Ejecutar consulta paginada para obtener los documentos
            cursor.execute(
                f"SELECT * FROM {self.table_name} ORDER BY id LIMIT ? OFFSET ?",
                (limit, offset)
            )
            
            # Convertir resultados a lista de diccionarios
            documentos = []
            for row in cursor.fetchall():
                # Convertir objeto Row a diccionario
                doc = {key: row[key] for key in row.keys()}
                
                # Obtener el embedding para este documento si existe
                cursor_embed = conn.cursor()
                cursor_embed.execute(
                    "SELECT embedding FROM contenido_embeddings WHERE contenido_id = ?",
                    (doc['id'],)
                )
                embedding_row = cursor_embed.fetchone()
                
                if embedding_row and embedding_row['embedding']:
                    # Convertir el embedding a vector si está en formato texto
                    embedding = embedding_row['embedding']
                    if isinstance(embedding, str):
                        try:
                            # Intentar convertir de texto a lista de números
                            import ast
                            embedding = ast.literal_eval(embedding)
                        except (ValueError, SyntaxError):
                            # Si falla, mantenerlo como string
                            pass
                    
                    doc['embedding'] = embedding
                
                documentos.append(doc)
            
            # Cerrar conexión
            cursor.close()
            conn.close()
            
            logger.debug(f"Obtenidos {len(documentos)} documentos desde la tabla '{self.table_name}' (offset {offset})")
            return documentos
        except Exception as e:
            logger.error(f"Error al obtener documentos de la tabla '{self.table_name}' (offset={offset}, limit={limit}): {str(e)}")
            return []
    
    def configurar_indice(self):
        """
        Configura el índice de Meilisearch con la configuración correcta
        """
        try:
            # Crear índice si no existe
            try:
                self.client.create_index(INDEX_NAME, {"primaryKey": "id"})
                logger.info(f"Índice '{INDEX_NAME}' creado con clave primaria 'id'")
            except Exception as e:
                if "index_already_exists" in str(e):
                    logger.info(f"El índice '{INDEX_NAME}' ya existe")
                else:
                    raise

            # Configurar ajustes del índice
            self.index.update_settings({
                "searchableAttributes": [
                    "contenido_texto",
                    "autor",
                    "contexto",
                    "url_original"
                ],
                "filterableAttributes": [
                    "id",
                    "autor",
                    "fecha_creacion",
                    "fecha_importacion",
                    "fuente_id",
                    "plataforma_id",
                    "idioma"
                ],
                "sortableAttributes": [
                    "id",
                    "fecha_creacion",
                    "fecha_importacion"
                ],
                "displayedAttributes": [
                    "id",
                    "contenido_texto",
                    "fecha_creacion",
                    "fecha_importacion",
                    "fuente_id",
                    "plataforma_id",
                    "url_original",
                    "contexto",
                    "autor",
                    "idioma"
                ],
                "typoTolerance": {
                    "enabled": True
                }
            })
            logger.info(f"Configuración del índice '{INDEX_NAME}' actualizada")
            
            # Configurar búsqueda vectorial
            try:
                self.index.update_vector_config({
                    'embeddings': {
                        'dimensions': 768,  # Dimensiones para el modelo 'paraphrase-multilingual-mpnet-base-v2'
                        'distance': 'cosine'  # Usar similitud coseno
                    }
                })
                logger.info(f"Configuración vectorial actualizada")
            except Exception as e:
                logger.warning(f"Error al configurar vectores (esto es normal en versiones antiguas): {str(e)}")
            
            # Esperar a que la tarea se complete
            time.sleep(1)
            
            return True
        except Exception as e:
            logger.error(f"Error al configurar el índice: {str(e)}")
            return False
    
    def transform_document(self, doc):
        """
        Transforma un documento para que sea compatible con Meilisearch
        """
        # Crear una copia para no modificar el original
        transformed = {}
        
        # Copiar todos los campos
        for key, value in doc.items():
            # Gestionar el campo embedding especialmente para vectores
            if key == 'embedding':
                if value is not None:
                    # Renombrar embedding para cumplir con el formato de Meilisearch
                    transformed['_vectors'] = {
                        'embeddings': value
                    }
            # Convertir campos None a cadenas vacías o valores predeterminados
            elif value is None:
                if key in ['contenido_texto', 'url_original', 'contexto', 'autor']:
                    transformed[key] = ""
                elif key == 'idioma':
                    transformed[key] = "es"
                else:
                    transformed[key] = None
            else:
                transformed[key] = value
        
        # Asegurar que el id sea entero
        if 'id' in transformed:
            try:
                transformed['id'] = int(transformed['id'])
            except (ValueError, TypeError):
                # Si no se puede convertir, dejarlo como está
                pass
        
        return transformed
    
    def indexar_lote_documentos(self, documentos):
        """
        Indexa un lote de documentos en Meilisearch con reintentos
        """
        if not documentos:
            return 0
        
        # Transformar documentos para Meilisearch
        documentos_transformados = [self.transform_document(doc) for doc in documentos]
            
        for intento in range(MAX_RETRY_ATTEMPTS):
            try:
                # Enviar el lote completo a Meilisearch de una vez
                inicio_request = time.time()
                resultado = self.index.add_documents(documentos_transformados)
                tiempo_request = time.time() - inicio_request
                
                num_docs = len(documentos)
                with self.lock:
                    self.documents_indexed += num_docs
                    progreso = (self.documents_indexed / self.total_documents) * 100
                    logger.info(f"Lote de {num_docs} documentos indexado en {tiempo_request:.2f}s. Progreso: {self.documents_indexed}/{self.total_documents} ({progreso:.2f}%)")
                
                # Esperar un poco entre lotes (no entre documentos individuales)
                time.sleep(WAIT_TIME_BETWEEN_BATCHES)
                return num_docs
            except Exception as e:
                logger.warning(f"Error al indexar lote de {len(documentos)} documentos (intento {intento+1}/{MAX_RETRY_ATTEMPTS}): {str(e)}")
                # Si es el último intento, dividir el lote a la mitad y reintentar
                if intento == MAX_RETRY_ATTEMPTS - 1 and len(documentos) > 10:
                    mitad = len(documentos) // 2
                    logger.warning(f"Dividiendo lote de {len(documentos)} en dos partes de {mitad} y {len(documentos)-mitad}")
                    
                    # Procesar la primera mitad
                    primera_mitad = documentos[:mitad]
                    self.indexar_lote_documentos(primera_mitad)
                    
                    # Procesar la segunda mitad
                    segunda_mitad = documentos[mitad:]
                    return self.indexar_lote_documentos(segunda_mitad)
                else:
                    # Esperar antes de reintentar, con tiempo exponencial
                    wait_time = min(2 ** intento, MAX_WAIT_TIME)
                    time.sleep(wait_time)
        
        # Si llegamos aquí, fallaron todos los intentos
        with self.lock:
            self.failed_documents.extend([doc.get('id', 'unknown') for doc in documentos])
        logger.error(f"Falló la indexación del lote de {len(documentos)} documentos después de {MAX_RETRY_ATTEMPTS} intentos")
        return 0
    
    def watchdog(self):
        """
        Función de vigilancia para detectar y reportar bloqueos
        """
        last_progress = 0
        last_time = time.time()
        
        while self.running:
            time.sleep(30)  # Verificar cada 30 segundos
            
            current_progress = self.documents_indexed
            current_time = time.time()
            elapsed = current_time - last_time
            
            if current_progress == last_progress and elapsed > 120:  # Sin progreso por 2 minutos
                logger.warning(f"⚠️ POSIBLE BLOQUEO DETECTADO: Sin progreso en {elapsed:.1f} segundos")
                logger.warning(f"Último progreso: {last_progress}/{self.total_documents}")
            
            last_progress = current_progress
            last_time = current_time
    
    def indexar_todos(self):
        """
        Indexa todos los documentos utilizando múltiples hilos
        """
        try:
            # Iniciar el watchdog
            watchdog_thread = threading.Thread(target=self.watchdog)
            watchdog_thread.daemon = True
            watchdog_thread.start()
            
            # Obtener el total de documentos
            self.obtener_total_documentos()
            
            # Verificar si hay documentos para indexar
            if self.total_documents == 0:
                logger.info("No hay documentos para indexar")
                return
            
            # Configurar el índice de Meilisearch
            if not self.configurar_indice():
                logger.error("No se pudo configurar el índice de Meilisearch. Abortando.")
                return
            
            # Indexar documentos en lotes grandes
            start_time = time.time()
            
            try:
                for offset in range(0, self.total_documents, BATCH_SIZE):
                    # Imprimir marcador de tiempo para monitorear posibles bloqueos
                    logger.info(f"Iniciando procesamiento del lote con offset {offset} a las {datetime.now().strftime('%H:%M:%S')}")
                    
                    documentos = self.obtener_documentos(offset, BATCH_SIZE)
                    
                    if not documentos:
                        logger.warning(f"No se pudieron obtener documentos para el lote con offset {offset}")
                        continue
                    
                    logger.info(f"Procesando lote de {len(documentos)} documentos (offset {offset})")
                    
                    # Dividir documentos en sublotes más pequeños para los hilos
                    sublotes = []
                    for i in range(0, len(documentos), DOCS_PER_REQUEST):
                        sublote = documentos[i:i+DOCS_PER_REQUEST]
                        if sublote:
                            sublotes.append(sublote)
                    
                    # Procesar sublotes con un pool de hilos para mejor gestión
                    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                        futures = [executor.submit(self.indexar_lote_documentos, sublote) for sublote in sublotes]
                        
                        # Esperar a que se completen todos o hasta que haya timeout
                        for future in concurrent.futures.as_completed(futures, timeout=300):  # 5 minutos máximo
                            try:
                                result = future.result()
                            except concurrent.futures.TimeoutError:
                                logger.error("Timeout al procesar sublote")
                            except Exception as e:
                                logger.error(f"Error al procesar sublote: {str(e)}")
                    
                    # Calcular estadísticas de rendimiento
                    elapsed = time.time() - start_time
                    documents_per_second = self.documents_indexed / elapsed if elapsed > 0 else 0
                    
                    logger.info(f"Lote completado (offset {offset}). Progreso: {self.documents_indexed}/{self.total_documents} ({(self.documents_indexed/self.total_documents)*100:.2f}%)")
                    logger.info(f"Velocidad: {documents_per_second:.2f} documentos/segundo. Tiempo transcurrido: {elapsed:.2f} segundos")
                    
            except KeyboardInterrupt:
                logger.warning("Interrupción del usuario. Finalizando proceso...")
            
            # Resultados finales
            self.running = False  # Detener el watchdog
            total_elapsed = time.time() - start_time
            final_speed = self.documents_indexed / total_elapsed if total_elapsed > 0 else 0
            
            logger.info(f"Tiempo total de indexación: {total_elapsed:.2f} segundos")
            logger.info(f"Velocidad promedio: {final_speed:.2f} documentos/segundo")
            
            if self.failed_documents:
                logger.error(f"Indexación completada con errores. {len(self.failed_documents)} documentos fallaron.")
                logger.error(f"Primeros 10 documentos fallidos: {self.failed_documents[:10]}")
            else:
                logger.info(f"Indexación completada exitosamente. {self.documents_indexed} documentos indexados.")
            
        except Exception as e:
            logger.error(f"Error durante la indexación: {str(e)}")
            raise
        finally:
            self.running = False  # Asegurar que el watchdog se detenga

def signal_handler(sig, frame):
    print("Ctrl+C detectado. Finalizando proceso...")
    sys.exit(0)

if __name__ == "__main__":
    try:
        # Registrar manejador de señales para Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        
        # Configurar parser de argumentos
        parser = argparse.ArgumentParser(description='Indexa documentos en Meilisearch desde una base de datos SQLite')
        parser.add_argument('--tabla', type=str, help='Nombre de la tabla que contiene los documentos')
        parser.add_argument('--listar', action='store_true', help='Listar todas las tablas disponibles')
        parser.add_argument('--db-path', type=str, default="E:\\dev-projects\\biblioperson\\backend\\data\\biblioteca.db", 
                          help='Ruta a la base de datos SQLite')
        parser.add_argument('--hilos', type=int, default=NUM_THREADS, help='Número de hilos a utilizar')
        parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Tamaño del lote de la base de datos')
        parser.add_argument('--docs-per-request', type=int, default=DOCS_PER_REQUEST, help='Documentos por solicitud a Meilisearch')
        parser.add_argument('--timeout', type=int, default=TIMEOUT, help='Timeout para solicitudes HTTP en segundos')
        args = parser.parse_args()
        
        # Actualizar configuración desde argumentos
        if args.hilos:
            NUM_THREADS = args.hilos
        if args.batch_size:
            BATCH_SIZE = args.batch_size
        if args.docs_per_request:
            DOCS_PER_REQUEST = args.docs_per_request
            
        # Usar la ruta proporcionada por el usuario
        db_path = args.db_path
        
        print(f"\nConfiguración:")
        print(f"- Base de datos: {db_path}")
        print(f"- Hilos: {NUM_THREADS}")
        print(f"- Tamaño de lote DB: {BATCH_SIZE}")
        print(f"- Documentos por solicitud: {DOCS_PER_REQUEST}")
        
        # Verificar si la base de datos existe
        if not os.path.exists(db_path):
            print(f"❌ La base de datos no existe en la ruta: {db_path}")
            exit(1)
        
        # Intentar abrir la base de datos para ver si funciona
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Consulta para obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tablas = cursor.fetchall()
            tablas = [tabla[0] for tabla in tablas]
            
            # Cerrar conexión
            cursor.close()
            conn.close()
            
            # Mostrar todas las tablas independientemente del parámetro --listar
            print("\nTablas disponibles en la base de datos:")
            if tablas:
                for tabla in tablas:
                    print(f"  - {tabla}")
                print("\nPara indexar una tabla específica, ejecuta:")
                print(f"  python {os.path.basename(__file__)} --tabla NOMBRE_TABLA\n")
            else:
                print("  No se encontraron tablas en la base de datos.")
                
            # Si se pidió explícitamente listar, terminar aquí
            if args.listar:
                exit(0)
            
            # Si no hay tablas, no podemos continuar
            if not tablas:
                print("No hay tablas disponibles en la base de datos. No se puede continuar.")
                exit(1)
                
            # Si no se especificó una tabla, usar la primera disponible
            tabla_elegida = args.tabla or tablas[0]
            print(f"Usando tabla: {tabla_elegida}")
            
        except Exception as e:
            print(f"\n❌ Error al intentar abrir la base de datos: {str(e)}")
            print("Asegúrate de que la ruta es correcta y que la base de datos existe.")
            logger.error(f"Error al abrir la base de datos: {str(e)}")
            exit(1)
        
        # Iniciar indexación
        logger.info(f"Iniciando proceso de indexación en Meilisearch usando base de datos: {db_path}")
        indexer = MeilisearchIndexer(table_name=tabla_elegida)
        indexer.db_path = db_path  # Actualizar la ruta de la base de datos
        indexer.indexar_todos()
        logger.info("Proceso de indexación finalizado")
    except Exception as e:
        logger.error(f"Error fatal durante la indexación: {str(e)}") 