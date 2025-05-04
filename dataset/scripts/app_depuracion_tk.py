import os
import json
import re
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading # Añadido para procesamiento en segundo plano
import queue # Movido aquí
import sys
import time # NUEVO: Para medir tiempos en salvage
import multiprocessing # Para aprovechar múltiples núcleos
import concurrent.futures # Para procesamiento paralelo
from dateutil import parser as dateparser

# Verificar que ijson esté instalado
try:
    import ijson
except ImportError:
    print("ERROR: Esta aplicación requiere 'ijson' para procesamiento eficiente de archivos JSON grandes.")
    print("Por favor, instálelo con: pip install ijson")
    print("O ejecute: pip install -r requirements.txt")
    sys.exit(1)

# Variable global para detener el procesamiento
STOP_PROCESSING = threading.Event()

BASE_DIR = Path(__file__).resolve().parent.parent
FUENTES_DIR = BASE_DIR / "fuentes"
# SALIDAS_DIR ya no se usará como directorio por defecto fijo para process_folder
# os.makedirs(SALIDAS_DIR, exist_ok=True) # Eliminado
os.makedirs(FUENTES_DIR, exist_ok=True)

# Categories in English
CATEGORIAS = [
    "Poems and Songs",
    "Messages and Social Networks",
    "Writings and Books"
]

# Modos de filtrado para JSON/NDJSON
FILTER_MODES = [
    "No filter",
    "Keep entries with property",
    "Remove entries with property"
]

# Añadir esta nueva constante
JSON_PROCESSING_OPTIONS = [
    "Auto-detect + Salvage (slower but better)",
    "Fast mode (skip salvage)"
]

# Extract date from JSON metadata
FECHA_KEYS = ["date", "fecha", "created", "timestamp"]

def extraer_fecha_json(obj):
    for key in FECHA_KEYS:
        if key in obj:
            return obj[key]
    return ""

# Extract date from YAML frontmatter in Markdown
YAML_FECHA_KEYS = ["date", "fecha", "created"]
def extraer_fecha_md(texto):
    match = re.match(r"---\n(.*?)---\n", texto, re.DOTALL)
    if match:
        yaml = match.group(1)
        for line in yaml.splitlines():
            for key in YAML_FECHA_KEYS:
                if line.lower().startswith(key+":"):
                    return line.split(":",1)[1].strip()
    return ""

def convertir_md_a_ndjson(archivo_md, archivo_ndjson, fuente, autor=None, segmentar_por_parrafos=True, filtro=None, min_chars=0):
    # Log inicial
    log_msg_start = f"Processing MD/TXT: {archivo_md.name} -> {archivo_ndjson.name}"
    # (Se podría añadir un callback aquí si se pasa log_callback)

    try:
        with open(archivo_md, "r", encoding="utf-8") as infile:
            texto = infile.read()
        fecha = extraer_fecha_md(texto)
        
        entries_written = 0
        entries_filtered = 0
        entries_too_short = 0
        
        with open(archivo_ndjson, "w", encoding="utf-8") as outfile:
            if segmentar_por_parrafos:
                parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
                for idx, parrafo in enumerate(parrafos, 1):
                    # Filtrar por longitud mínima
                    if min_chars > 0 and len(parrafo) < min_chars:
                        entries_too_short += 1
                        continue
                        
                    obj = {
                        "id": idx,
                        "texto": parrafo,
                        "fecha": fecha,
                        "fuente": fuente,
                        "contexto": str(archivo_md),
                        "autor": autor or ""
                    }
                    outfile.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    entries_written += 1
            else:
                if min_chars > 0 and len(texto) < min_chars:
                    entries_too_short += 1
                else:
                    obj = {
                        "id": 1,
                        "texto": texto,
                        "fecha": fecha,
                        "fuente": fuente,
                        "contexto": str(archivo_md),
                        "autor": autor or ""
                    }
                    outfile.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    entries_written += 1
        
        msg = f"Converted to NDJSON: {archivo_ndjson.name}"
        
        if segmentar_por_parrafos:
            total_entries = len(parrafos) if 'parrafos' in locals() else 1 # Handle non-segmented case
            msg += f" ({entries_written}/{total_entries} entries saved)"
            
        if min_chars > 0 and entries_too_short > 0:
            msg += f" [{entries_too_short} entries below {min_chars} chars filtered]"
            
        # Añadir nota sobre la eliminación de propiedad
        if filtro:
            msg += f" [Note: JSON filtering doesn't apply to MD/TXT files]"
            
        # Log final (éxito)
        # (Se podría añadir un callback aquí si se pasa log_callback)
            
        return True, msg
    except Exception as e:
        # Log final (error)
        # (Se podría añadir un callback aquí si se pasa log_callback)
        return False, f"Error converting {archivo_md.name}: {str(e)}"

# --- Inicio: Función recursiva para búsqueda de propiedades ---
def find_prop_recursive(data, prop, value=None):
    """Busca recursivamente una propiedad (y opcionalmente un valor) en dicts/listas anidadas."""
    if isinstance(data, dict):
        if prop in data:
            if value is None or data[prop] == value:
                return True
        for k, v in data.items():
            if find_prop_recursive(v, prop, value):
                return True
    elif isinstance(data, list):
        for item in data:
            if find_prop_recursive(item, prop, value):
                return True
    return False
# --- Fin: Función recursiva ---

# --- NUEVO: Función para extraer el texto (recursiva y lista a texto plano) ---
def extract_text_recursive(data, key):
    """Busca recursivamente la clave 'key' y devuelve su valor como texto plano.
    Si es lista, concatena los textos de los elementos (strings o dicts con 'text')."""
    if not key:
        return None
    if isinstance(data, dict):
        if key in data:
            val = data[key]
            # Si es lista, concatenar textos
            if isinstance(val, list):
                textos = []
                for item in val:
                    if isinstance(item, str):
                        textos.append(item)
                    elif isinstance(item, dict) and 'text' in item:
                        # Si el subobjeto tiene 'text', usarlo (puede ser string o lista)
                        subtext = item['text']
                        if isinstance(subtext, str):
                            textos.append(subtext)
                        elif isinstance(subtext, list):
                            # Concatenar recursivamente si es lista
                            textos.append(''.join(str(x) for x in subtext))
                    # Si es otro tipo, ignorar
                return ''.join(textos)
            elif isinstance(val, str):
                return val
            else:
                # Si es otro tipo (dict, número, etc.), convertir a string
                return str(val)
        for v in data.values():
            res = extract_text_recursive(v, key)
            if res is not None:
                return res
    elif isinstance(data, list):
        for item in data:
            res = extract_text_recursive(item, key)
            if res is not None:
                return res
    return None
# --- Fin: extract_text_recursive ---

# --- NUEVO: Función para procesar UNA entrada JSON --- 
def process_single_json_entry(obj, fuente, contexto_file, autor=None, filter_mode=None, filter_prop=None, filter_value=None, min_chars=0, text_prop=None):
    """Procesa un único objeto JSON (dict). Aplica filtros y devuelve el objeto estandarizado o None.
    Devuelve: (objeto_estandarizado | None, fue_filtrado_prop, fue_filtrado_corto)
    """
    fue_filtrado_prop = False
    fue_filtrado_corto = False

    try:
                    fecha = extraer_fecha_json(obj)

        # Extraer texto principal si se especificó la clave
        texto_extraido = extract_text_recursive(obj, text_prop) if text_prop else None
        # Si no se especificó text_prop, o no se encontró, intentamos usar el objeto entero como texto? No, lo dejamos como None o vacío.
        if texto_extraido is None:
            texto_extraido = "" # Asegurar que sea string vacío si no se encuentra
        # Asegurar que el texto extraído sea string
        if not isinstance(texto_extraido, str):
             texto_extraido = str(texto_extraido)

        # Filtrar por propiedad (usando búsqueda recursiva)
        prop_found = False
        if filter_mode and filter_prop and filter_mode != "No filter":
            prop_found = find_prop_recursive(obj, filter_prop, filter_value)
                        if filter_mode == "Keep entries with property":
                if not prop_found:
                    fue_filtrado_prop = True
                    return None, fue_filtrado_prop, fue_filtrado_corto
                        elif filter_mode == "Remove entries with property":
                if prop_found:
                    fue_filtrado_prop = True
                    return None, fue_filtrado_prop, fue_filtrado_corto

        # Filtrar por longitud (solo si tenemos texto y text_prop está definido)
        if text_prop and min_chars > 0 and len(texto_extraido) < min_chars:
            fue_filtrado_corto = True
            return None, fue_filtrado_prop, fue_filtrado_corto

        # Si pasa los filtros, crear entrada estandarizada
                    entrada = {
            # "id": se asignará después al escribir el archivo final
            "texto": texto_extraido,
                        "fecha": fecha,
                        "fuente": fuente,
            "contexto": str(contexto_file),
                        "autor": autor or ""
                    }
        return entrada, fue_filtrado_prop, fue_filtrado_corto

                except Exception:
        # Error al procesar esta entrada específica
        return None, False, False # O considerarlo filtrado? Dejémoslo como None por ahora

# --- Fin: process_single_json_entry ---

# --- MODIFICADO: procesar_ndjson ahora usa process_single_json_entry ---
def procesar_ndjson(archivo_ndjson, archivo_salida, fuente, autor=None, filter_mode=None, filter_prop=None, filter_value=None, min_chars=0, text_prop=None, stop_event=None):
    # Log inicial
    log_msg_start = f"Processing JSON/NDJSON: {archivo_ndjson.name} -> {archivo_salida.name}"
    # (Se podría añadir un callback aquí si se pasa log_callback)

    try:
        entradas_validas = []
        entradas_originales = 0
        entradas_filtradas_prop_count = 0
        entradas_cortas_count = 0
        
        with open(archivo_ndjson, "r", encoding="utf-8") as infile:
            for line in infile:
                # Verificar si se solicitó detener
                if stop_event and stop_event.is_set():
                    break
                    
                entradas_originales += 1
                try:
                    obj = json.loads(line)
                    
                    # Procesar normalmente
                    entrada_procesada, fue_filtrado_prop, fue_filtrado_corto = process_single_json_entry(
                        obj, fuente, archivo_ndjson, autor, filter_mode, filter_prop, filter_value, min_chars, text_prop
                    )
                    if entrada_procesada:
                        entradas_validas.append(entrada_procesada)
                    else:
                        if fue_filtrado_prop:
                            entradas_filtradas_prop_count += 1
                        if fue_filtrado_corto:
                            entradas_cortas_count += 1
                except json.JSONDecodeError:
                    # Línea no es JSON válido, ignorar
                    continue
                except Exception:
                    # Error inesperado procesando la línea
                    continue
                    
        # Si se detuvo el proceso, no seguir escribiendo
        if stop_event and stop_event.is_set():
            return False, "Processing stopped by user", 0, 0

        # Asignar IDs secuenciales y escribir
        with open(archivo_salida, "w", encoding="utf-8") as outfile:
            for idx, entrada in enumerate(entradas_validas, 1):
                entrada["id"] = idx
                outfile.write(json.dumps(entrada, ensure_ascii=False) + "\n")
                
        num_entradas_guardadas = len(entradas_validas)
        msg = f"Processed NDJSON {archivo_ndjson.name}: {num_entradas_guardadas}/{entradas_originales} entries saved to {archivo_salida.name}"
        
        # Resumen de filtrado
        if filter_mode and filter_prop and filter_mode != "No filter":
            filter_desc = f"'{filter_prop}'"
            if filter_value:
                filter_desc += f"='{filter_value}'"
            if filter_mode == "Keep entries with property":
                msg += f" [{entradas_filtradas_prop_count} entries without {filter_desc} filtered]"
            else:
                msg += f" [{entradas_filtradas_prop_count} entries with {filter_desc} filtered]"

        if text_prop and min_chars > 0 and entradas_cortas_count > 0:
             msg += f" [{entradas_cortas_count} entries below {min_chars} chars filtered]"

        return True, msg, entradas_filtradas_prop_count, entradas_cortas_count
    except Exception as e:
        return False, f"Error processing NDJSON {archivo_ndjson.name}: {str(e)}", 0, 0

# --- NUEVO: Función para intentar extraer mensajes de JSON corrupto ---

def salvage_messages_from_corrupt_json_list(texto_raw, log_callback=None, min_id=None, max_id=None, stop_event=None):
    """Intenta extraer objetos JSON dentro de la lista 'messages' incluso si el JSON global está corrupto.
    Estrategia:
      1) Buscar la primera aparición de '[' después de la clave "messages" (si existe) o la primera '[' global.
      2) Recorrer la cadena contando llaves { } para identificar objetos y usar json.JSONDecoder().raw_decode
         para parsear cada objeto. Si falla, se descarta el carácter y continúa.
      3) Para archivos grandes, se procesa en chunks de tamaño manejable.
    Devuelve lista de objetos válidos.
    
    Args:
        texto_raw: Texto JSON a procesar
        log_callback: Función para logs
        min_id: ID mínimo a procesar (None = sin límite)
        max_id: ID máximo a procesar (None = sin límite)
        stop_event: Evento para detener el procesamiento
    """
    msgs = []
    
    # Mostrar info de rango de IDs si hay alguno
    if min_id is not None or max_id is not None:
        if log_callback:
            log_callback(f"  -> Salvaging with ID range: {min_id or 'START'} to {max_id or 'END'}")
    
    # Verificar tamaño total del texto
    total_size_mb = len(texto_raw) / (1024 * 1024)
    if log_callback:
        log_callback(f"  -> Total JSON size: {total_size_mb:.1f}MB")
    
    # Determinar si necesitamos procesar en chunks
    CHUNK_SIZE = 50 * 1024 * 1024  # 50MB por chunk
    if len(texto_raw) <= CHUNK_SIZE:
        # Archivo pequeño, procesarlo directamente
        return process_json_chunk(texto_raw, 0, log_callback, min_id, max_id, stop_event)
    
    # Para archivos grandes, procesar en chunks
    num_chunks = (len(texto_raw) + CHUNK_SIZE - 1) // CHUNK_SIZE
    if log_callback:
        log_callback(f"  -> File will be processed in {num_chunks} chunks of {CHUNK_SIZE/(1024*1024):.1f}MB each")
        # Inicializar progreso
        log_callback(f"  -> Progress: 0.0% (0 objects found)", is_progress=True)
    
    # Verificar stop_event antes de comenzar el procesamiento pesado
    if stop_event and stop_event.is_set():
        if log_callback:
            log_callback(f"  -> Processing stopped by user before starting chunks")
        return []
    
    # Buscar la estructura principal del JSON
    start_idx = -1
    if '"messages"' in texto_raw[:5000]:  # Buscar "messages" en los primeros 5000 caracteres
        start_idx = texto_raw.find('[', texto_raw.find('"messages"'))
    if start_idx == -1:
        start_idx = texto_raw.find('[')
    end_idx = texto_raw.rfind(']')
    
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        # No se encontró lista clara
        if log_callback:
            log_callback(f"  -> Could not find JSON array structure in the file")
        return msgs
    
    # Obtener el contenido de la lista (sin los corchetes principales)
    array_content = texto_raw[start_idx+1:end_idx]
    total_array_size = len(array_content)
    
    # NUEVO: Usar concurrent.futures para procesar chunks en paralelo
    all_msgs = []
    chunks = []
    
    # Determinar número óptimo de workers basado en CPU cores
    cpu_cores = multiprocessing.cpu_count()
    max_workers = max(1, min(cpu_cores - 1, num_chunks, 4))  # Usar hasta CPU cores-1, máximo 4 (reducido para mejorar control)
    
    if log_callback:
        log_callback(f"  -> Using {max_workers} parallel workers (out of {cpu_cores} CPU cores)")
    
    # Preparar los chunks para procesamiento
    for chunk_num in range(num_chunks):
        start_pos = chunk_num * CHUNK_SIZE
        end_pos = min(start_pos + CHUNK_SIZE, total_array_size)
        chunk = array_content[start_pos:end_pos]
        chunks.append((chunk, start_pos, chunk_num, num_chunks))
    
    # Verificar stop_event antes de iniciar el procesamiento paralelo
    if stop_event and stop_event.is_set():
        if log_callback:
            log_callback(f"  -> Processing stopped by user before starting parallel processing")
        return []
    
    # Procesamiento paralelo con progress tracking
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Función para procesar un chunk y mantener el progreso global
        def process_chunk_with_progress(args):
            chunk, offset, chunk_num, total_chunks = args
            
            # Verificar si se ha solicitado detener
            if stop_event and stop_event.is_set():
                return []
                
            # Procesar el chunk
            chunk_start_time = time.time()
            # Enviar log_callback para mostrar progreso dentro de cada chunk
            if log_callback:
                def chunk_log(inner_msg, is_progress=False):
                    """Agrega prefijo con el número de chunk para distinguir en el log principal."""
                    prefixed = f"[Chunk {chunk_num+1}/{total_chunks}] {inner_msg.strip()}"
                    # No propagamos la barra de progreso interna a la global, así que marcamos is_progress=False
                    log_callback(prefixed, is_progress=False)

                chunk_msgs = process_json_chunk(chunk, offset, chunk_log, min_id, max_id, stop_event)
            else:
                chunk_msgs = process_json_chunk(chunk, offset, None, min_id, max_id, stop_event)
            chunk_time = time.time() - chunk_start_time
            
            # Reportar progreso global (basado en chunks completados)
            if log_callback:
                global_progress = ((chunk_num + 1) / total_chunks) * 100
                log_callback(f"  -> Global Progress: {global_progress:.1f}% ({len(chunk_msgs)} objects in chunk {chunk_num+1})", is_progress=True)
                log_callback(f"  -> Completed chunk {chunk_num+1}/{total_chunks} in {chunk_time:.1f}s, extracted {len(chunk_msgs)} objects")
            
            return chunk_msgs
        
        # Enviar todos los chunks a procesar
        future_to_chunk = {executor.submit(process_chunk_with_progress, chunk_args): chunk_args for chunk_args in chunks}
        
        # Recoger resultados a medida que se completan
        for future in concurrent.futures.as_completed(future_to_chunk):
            if stop_event and stop_event.is_set():
                break
            
            try:
                result = future.result()
                all_msgs.extend(result)
            except Exception as e:
                if log_callback:
                    chunk_info = future_to_chunk[future]
                    log_callback(f"  -> Error processing chunk {chunk_info[2]+1}: {str(e)}")
    
    # Al terminar, actualizar progreso a 100%
    if log_callback:
        if not (stop_event and stop_event.is_set()):
            log_callback(f"  -> Global Progress: 100.0% ({len(all_msgs)} objects found)", is_progress=True)
        log_callback(f"  -> Total objects extracted from entire file: {len(all_msgs)}")
    
    return all_msgs

# Modificar también la función log en main() para manejar correctamente el nuevo formato de progreso
def log(msg, is_progress=False):
    # Usar cola para actualizar desde otros hilos
    if is_progress:
        # Si es mensaje de progreso, actualizar barra directamente
        if "Global Progress:" in msg:
            try:
                pct_str = msg.split("Global Progress: ")[1].split("%")[0]
                pct = float(pct_str)
                # Actualizar en el hilo principal
                root.after(0, lambda: progress_var.set(pct))
                # Actualizar texto de progreso
                if "objects" in msg:
                    objects_str = msg.split("(")[1].split(")")[0]
                    root.after(0, lambda: progress_text.set(f"{pct:.1f}% - {objects_str}"))
                else:
                    root.after(0, lambda: progress_text.set(f"{pct:.1f}%"))
            except Exception:
                pass
        elif "Progress:" in msg:
            # Es un progreso de chunk individual, no actualizamos la barra global
            pass
        return
        
    # Para mensajes normales, usar cola
    log_queue.put(msg)

# Modificar process_json_chunk para mejor manejo del progreso y aprovechar todos los cores
def process_json_chunk(chunk_text, offset, log_callback=None, min_id=None, max_id=None, stop_event=None):
    """Procesa un segmento (chunk) de texto JSON y extrae objetos válidos."""
    chunk_msgs = []
    decoder = json.JSONDecoder()
    pos = 0
    total_len = len(chunk_text)
    
    # Límites para este chunk específico - AUMENTADOS
    MAX_OBJECTS_PER_CHUNK = 50000  # Aumentado de 10000 a 50000
    MAX_TRIES = 100000  # Aumentado de 50000 a 100000
    MAX_TIME = 300  # Aumentado de 120s a 300s (5 minutos)
    
    start_time = time.time()
    consecutive_failures = 0
    
    # Variables para reportar progreso
    last_progress_report = time.time()
    progress_interval = 3.0  # Reportar progreso cada 3 segundos (aumentado de 2s)
    
    # Contador para verificar stop_event más frecuentemente
    check_stop_counter = 0
    CHECK_STOP_FREQUENCY = 1000  # Verificar cada 1000 iteraciones
    
    while pos < total_len:
        # NUEVO: Verificar stop_event más frecuentemente
        check_stop_counter += 1
        if stop_event and check_stop_counter >= CHECK_STOP_FREQUENCY:
            check_stop_counter = 0
            if stop_event.is_set():
                if log_callback:
                    log_callback(f"  -> Processing stopped by user (quick check)")
                break
        
        # Verificar tiempo límite para este chunk
        current_time = time.time()
        if current_time - start_time > MAX_TIME:
            if log_callback:
                log_callback(f"  -> Chunk timeout after {MAX_TIME}s. Extracted {len(chunk_msgs)} objects so far.")
            break
            
        # Reportar progreso periódicamente (solo para el log interno del chunk, no para la barra global)
        if log_callback and (current_time - last_progress_report > progress_interval or (len(chunk_msgs) % 1000 == 0 and len(chunk_msgs) > 0)):
            progress_pct = (pos / total_len) * 100
            log_callback(f"Progreso: {progress_pct:.1f}% ({len(chunk_msgs)} objetos extraídos)")
            last_progress_report = current_time
            
            # Verificar stop_event durante el reporte de progreso
            if stop_event and stop_event.is_set():
                if log_callback:
                    log_callback(f"  -> Processing stopped by user (during progress report)")
                break
                
        # Verificar número límite de objetos para este chunk
        if len(chunk_msgs) >= MAX_OBJECTS_PER_CHUNK:
            if log_callback:
                log_callback(f"  -> Reached maximum object limit for this chunk ({MAX_OBJECTS_PER_CHUNK}). Moving to next chunk.")
            break
            
        # Verificar intentos fallidos consecutivos
        if consecutive_failures >= MAX_TRIES:
            if log_callback:
                log_callback(f"  -> Too many consecutive parsing failures ({MAX_TRIES}). Moving to next chunk.")
            break
            
        # Saltar espacios y comas iniciales
        while pos < total_len and chunk_text[pos] in " \n\r\t,":
            pos += 1
        if pos >= total_len:
            break
            
        try:
            obj, new_pos = decoder.raw_decode(chunk_text[pos:])
            
            # Verificar si está dentro del rango de IDs solicitado
            if isinstance(obj, dict) and 'id' in obj:
                obj_id = obj['id']
                if min_id is not None and obj_id < min_id:
                    # Saltamos: ID menor que el mínimo
                    pos += new_pos
                    continue
                if max_id is not None and obj_id > max_id:
                    # Saltamos: ID mayor que el máximo
                    pos += new_pos
                    continue
            
            chunk_msgs.append(obj)
            pos += new_pos
            consecutive_failures = 0  # Resetear contador de fallos
        except json.JSONDecodeError:
            # Si falla, avanzar un carácter y continuar
            pos += 1
            consecutive_failures += 1
        
        # NUEVO: Revisar stop_event en cada iteración
        if stop_event and stop_event.is_set():
            if log_callback:
                log_callback("  -> Processing stopped by user (inside chunk)")
            break
    
    return chunk_msgs

# --- NUEVO: Función para procesar JSON estándar (con lista de mensajes) ---
def procesar_standard_json(archivo_json, archivo_salida, fuente, autor=None, filter_mode=None, filter_prop=None, filter_value=None, min_chars=0, text_prop=None, log_callback=None, stop_event=None, skip_salvage=False, json_min_id=None, json_max_id=None):
    try:
        entradas_validas = []
        entradas_originales = 0
        entradas_filtradas_prop_count = 0
        entradas_cortas_count = 0
        
        # NUEVO: Verificar tamaño del archivo para decidir estrategia
        file_size = os.path.getsize(archivo_json) / (1024 * 1024)  # tamaño en MB
        if file_size > 50:  # Si es mayor de 50MB, avisar
            if log_callback:
                log_callback(f"  -> Warning: Large JSON file detected ({file_size:.1f}MB). Processing may take time.")
        
        # NUEVO: Verificar stop_event al inicio
        if stop_event and stop_event.is_set():
            if log_callback:
                log_callback(f"  -> Processing stopped by user before starting JSON parsing")
            return False, "Processing stopped by user", 0, 0        
                
        # Limitar tiempo de procesamiento
        start_time = time.time()
        MAX_PARSING_TIME = 30  # segundos máximos para intentar determinar estructura
        
        # Intentamos estrategias para encontrar el iterador adecuado
        file_handle = None
        messages_iterator = None
        
        try:
            # Intentar primero con la estructura "messages.item" (común en exports de redes sociales)
            file_handle = open(archivo_json, "r", encoding="utf-8")
            
            # Primero intentamos leer un poco del archivo para detectar su estructura
            first_chars = file_handle.read(100)
            file_handle.seek(0)  # Volver al comienzo
            
            # Determinar si el archivo JSON es una lista o un objeto
            is_array = first_chars.strip().startswith('[')
            is_object = first_chars.strip().startswith('{')
            
            if is_object:
                # Intentamos los diferentes patrones para mensajes en JSON estructurado
                success = False
                for path in ['messages.item', 'Messages.item', 'data.item', 'posts.item', 'comments.item', 'entries.item']:
                    # NUEVO: Verificar tiempo
                    if time.time() - start_time > MAX_PARSING_TIME:
                        if log_callback:
                            log_callback(f"  -> Structure detection timeout after {MAX_PARSING_TIME}s. Trying salvage mode.")
                        break
                        
                    # NUEVO: Verificar stop_event periódicamente durante la detección de estructura
                    if stop_event and stop_event.is_set():
                        if log_callback:
                            log_callback(f"  -> Processing stopped by user during structure detection")
                        return False, "Processing stopped by user", 0, 0
                        
                    try:
                        # Crear un parser para detectar la ruta 
                        parser = ijson.parse(file_handle)
                        # Buscar la primera aparición del patrón (con límite de tiempo)
                        pattern_timeout = time.time() + 10  # 10s para cada patrón
                        for prefix, event, value in parser:
                            if time.time() > pattern_timeout:
                                if log_callback:
                                    log_callback(f"  -> Pattern '{path}' detection timeout.")
                                break
                                
                            if prefix == path.split('.')[0] and event == 'start_array':
                                success = True
                                break
                        
                        if success:
                            # Reiniciar el archivo y crear un iterador para esa ruta
                            file_handle.seek(0)
                            if log_callback:
                                log_callback(f"  -> Found JSON structure: {path}")
                            messages_iterator = ijson.items(file_handle, path)
                            break
                        else:
                            # Reiniciar para probar el siguiente patrón
                            file_handle.seek(0)
                    except Exception as e:
                        if log_callback:
                            log_callback(f"  -> Error checking pattern '{path}': {str(e)}")
                            
                            # NUEVO: Extraer más contexto del error para ayudar a localizar y reparar manualmente
                            if isinstance(e, ijson.common.JSONError) and hasattr(e, 'position'):
                                try:
                                    # Guardar posición actual
                                    current_pos = file_handle.tell()
                                    
                                    # Ir a la posición del error
                                    error_pos = e.position
                                    
                                    # Retroceder hasta 50 caracteres si es posible para dar contexto
                                    context_start = max(0, error_pos - 50)
                                    file_handle.seek(context_start)
                                    
                                    # Leer 100 caracteres de contexto (50 antes, 50 después)
                                    context = file_handle.read(100)
                                    
                                    # Marcar posición del error en el contexto
                                    pointer_pos = error_pos - context_start
                                    pointer = " " * pointer_pos + "^-- Error aquí"
                                    
                                    # Mostrar línea del error y contexto
                                    context_str = context.replace('\n', '\\n')
                                    log_callback(f"  -> Error context (byte {error_pos}):")
                                    log_callback(f"      {context_str}")
                                    log_callback(f"      {pointer}")
                                    
                                    # Restaurar posición
                                    file_handle.seek(current_pos)
                                except:
                                    # Si falla al intentar mostrar contexto, ignorar
                                    pass
                        
                        # Si falla, reiniciamos para probar el siguiente patrón
                        file_handle.seek(0)
            
            elif is_array:
                # Si es un array, usamos 'item' directamente 
                if log_callback:
                    log_callback(f"  -> Found root JSON array")
                messages_iterator = ijson.items(file_handle, 'item')
                success = True
            
            # Si no encontramos un iterador válido
            if not messages_iterator:
                # Cerrar el archivo e intentar rescate si no está desactivado
                if file_handle:
                    file_handle.close()
                    file_handle = None
                
                if skip_salvage:
                    if log_callback:
                        log_callback(f"  -> Could not parse JSON structure. Salvage mode is disabled.")
                    return False, f"Failed to parse JSON (salvage disabled): {archivo_json.name}", 0, 0
                
                if log_callback:
                    log_callback(f"  -> Could not determine JSON structure. Attempting salvage mode...")
                
                # Intentar salvamento de mensajes
                with open(archivo_json, "r", encoding="utf-8") as f_raw:
                    raw_txt = f_raw.read()
                
                salvaged_msgs = salvage_messages_from_corrupt_json_list(raw_txt, log_callback, json_min_id, json_max_id, stop_event)
                if not salvaged_msgs:
                    return False, f"Failed to identify any messages in JSON file: {archivo_json.name}", 0, 0
                
                # Crear iterador sobre la lista de mensajes rescatados
                messages_iterator = iter(salvaged_msgs)
            
            # Procesar mensajes desde el iterador (cuidando de cerrar el archivo después)
            try:
                for obj in messages_iterator:
                    # Verificar si se solicitó detener
                    if stop_event and stop_event.is_set():
                        if log_callback:
                            log_callback("  -> Processing stopped by user")
                        break
                        
                    if not isinstance(obj, dict):
                        continue
                    
                    entradas_originales += 1
                    
                    # Procesar normalmente
                    entrada_procesada, fue_filtrado_prop, fue_filtrado_corto = process_single_json_entry(
                        obj, fuente, archivo_json, autor, filter_mode, filter_prop, filter_value, min_chars, text_prop
                    )
                    
                    if entrada_procesada:
                        entradas_validas.append(entrada_procesada)
                    else:
                        if fue_filtrado_prop:
                            entradas_filtradas_prop_count += 1
                        if fue_filtrado_corto:
                            entradas_cortas_count += 1
            finally:
                # Asegurarnos de cerrar el archivo si está abierto
                if file_handle:
                    file_handle.close()
                    file_handle = None
            
            # Si se detuvo el proceso, no seguir
            if stop_event and stop_event.is_set():
                return False, "Processing stopped by user", 0, 0
            
            # Escribir salida
            with open(archivo_salida, "w", encoding="utf-8") as outfile:
                for idx, entrada in enumerate(entradas_validas, 1):
                    entrada["id"] = idx
                    outfile.write(json.dumps(entrada, ensure_ascii=False) + "\n")
            
            num_entradas_guardadas = len(entradas_validas)
            msg = f"Processed JSON {archivo_json.name}: {num_entradas_guardadas}/{entradas_originales} messages saved to {archivo_salida.name}"
            
            if filter_mode and filter_prop and filter_mode != "No filter":
                filter_desc = f"'{filter_prop}'"
                if filter_value:
                    filter_desc += f"='{filter_value}'"
            if filter_mode == "Keep entries with property":
                    msg += f" [{entradas_filtradas_prop_count} entries without {filter_desc} filtered]"
            else:
                    msg += f" [{entradas_filtradas_prop_count} entries with {filter_desc} filtered]"
            
            if text_prop and min_chars > 0 and entradas_cortas_count > 0:
                msg += f" [{entradas_cortas_count} messages below {min_chars} chars filtered]"
            
            # Si hay ID range, mostrarlo en el log
            if json_min_id is not None or json_max_id is not None:
                id_range = f"ID range: {json_min_id or 'START'} to {json_max_id or 'END'}"
                if log_callback:
                    log_callback(f"  -> Processing with {id_range}")
            
            return True, msg, entradas_filtradas_prop_count, entradas_cortas_count
        
    except Exception as e:
            # Cerrar el archivo si está abierto
            if file_handle:
                file_handle.close()
            
            if log_callback:
                log_callback(f"  -> Error processing JSON: {str(e)}")
            
            # Intentar salvamento como último recurso si no está desactivado
            if skip_salvage:
                return False, f"Failed to process JSON and salvage mode is disabled: {archivo_json.name}", 0, 0
                
            try:
                with open(archivo_json, "r", encoding="utf-8") as f_raw:
                    raw_txt = f_raw.read()
                
                salvaged_msgs = salvage_messages_from_corrupt_json_list(raw_txt, log_callback, json_min_id, json_max_id, stop_event)
                if not salvaged_msgs:
                    return False, f"Failed to process or salvage messages from {archivo_json.name}: {str(e)}", 0, 0
                
                # Procesar los mensajes rescatados
                for obj in salvaged_msgs:
                    # Verificar si se solicitó detener
                    if stop_event and stop_event.is_set():
                        break
                        
                    if not isinstance(obj, dict):
                        continue
                    
                    entradas_originales += 1
                    
                    # Procesar normalmente
                    entrada_procesada, fue_filtrado_prop, fue_filtrado_corto = process_single_json_entry(
                        obj, fuente, archivo_json, autor, filter_mode, filter_prop, filter_value, min_chars, text_prop
                    )
                    
                    if entrada_procesada:
                        entradas_validas.append(entrada_procesada)
                    else:
                        if fue_filtrado_prop:
                            entradas_filtradas_prop_count += 1
                        if fue_filtrado_corto:
                            entradas_cortas_count += 1
                
                if stop_event and stop_event.is_set():
                    return False, "Processing stopped by user", 0, 0
                
                # Escribir salida
                with open(archivo_salida, "w", encoding="utf-8") as outfile:
                    for idx, entrada in enumerate(entradas_validas, 1):
                        entrada["id"] = idx
                        outfile.write(json.dumps(entrada, ensure_ascii=False) + "\n")
                
                num_entradas_guardadas = len(entradas_validas)
                msg = f"Salvaged JSON {archivo_json.name}: {num_entradas_guardadas}/{entradas_originales} messages saved to {archivo_salida.name}"
                
                return True, msg, entradas_filtradas_prop_count, entradas_cortas_count
            
            except Exception as e2:
                return False, f"Failed to salvage messages from corrupt JSON {archivo_json.name}: {str(e2)}", 0, 0
    
    except Exception as e:
        return False, f"Error processing JSON file {archivo_json.name}: {str(e)}", 0, 0

# --- NUEVO: Función para unificar múltiples archivos NDJSON ---

def estandarizar_fecha_yyyymm(fecha_str):
    if not fecha_str or not isinstance(fecha_str, str):
        return ""
    try:
        dt = dateparser.parse(fecha_str, fuzzy=True)
        if dt:
            return dt.strftime("%Y-%m")
    except Exception:
        pass
    return ""

def unificar_archivos_ndjson(files, output_file, author_to_assign=None, remove_duplicates=False):
    """Unifica varias rutas de archivos NDJSON en uno solo.

    Args:
        files (list[pathlib.Path]): lista de rutas a archivos .ndjson.
        output_file (pathlib.Path): ruta del archivo de salida.
        author_to_assign (str|None): si se proporciona, sobreescribe/añade el campo 'autor'.
        remove_duplicates (bool): si es True, elimina entradas con texto duplicado (campo 'texto').

    Returns:
        tuple[bool, str]: (ok, mensaje_resumen)
    """
    total_entries = 0
    saved_entries = 0
    duplicate_count = 0

    seen_texts = set() if remove_duplicates else None

    try:
        # Asegurar directorio de salida
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as outfile:
            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                    for line in infile:
                            if not line.strip():
                                continue  # saltar líneas vacías
                        try:
                            obj = json.loads(line)
                            except json.JSONDecodeError:
                                continue  # ignorar líneas corruptas

                            if not isinstance(obj, dict):
                            continue

                            total_entries += 1

                            # Asignar/reescribir autor si corresponde
                            if author_to_assign is not None:
                                obj["autor"] = author_to_assign
                            # Estandarizar fecha a YYYY-MM
                            fecha_original = obj.get("fecha", "")
                            obj["fecha_estandarizada"] = estandarizar_fecha_yyyymm(fecha_original)

                            # Detección de duplicados
                            if remove_duplicates:
                                texto_key = obj.get("texto")
                                if texto_key is None:
                                    # Si no tiene campo texto, intentamos con 'text'
                                    texto_key = obj.get("text")
                                if texto_key is not None:
                                    # Normalizar: quitar espacios extremos y convertir a string
                                    texto_norm = str(texto_key).strip()
                                    if texto_norm in seen_texts:
                                        duplicate_count += 1
                                        continue  # duplicado -> saltar
                                    seen_texts.add(texto_norm)

                            # Asignar nuevo ID secuencial
                            saved_entries += 1
                            obj["id"] = saved_entries

                            outfile.write(json.dumps(obj, ensure_ascii=False) + "\n")
            except Exception:
                    # Si un archivo falla, continuar con los demás
                continue
        
        msg = (
            f"Unified {len(files)} files: {saved_entries}/{total_entries} entries saved to {output_file.name}"
        )
        if remove_duplicates:
            msg += f" ({duplicate_count} duplicates skipped)"

        return True, msg

    except Exception as e:
        return False, f"Error unifying NDJSON files: {str(e)}"

# --- FIN función unificar_archivos_ndjson ---

# --- MODIFICADO: process_folder para detectar tipo de JSON --- 
def process_folder(folder, category, output_dir, author=None, filter_mode=None, filter_prop=None, filter_value=None, min_chars=0, text_prop=None, log_callback=None, stop_event=None, skip_salvage=False, json_min_id=None, json_max_id=None):
    """Procesa archivos en una carpeta y los guarda en output_dir."""
    # Iniciar contador de tiempo total
    process_start_time = time.time()
    
    folder_path = Path(folder)
    # Usar el directorio de salida proporcionado
    output_folder = Path(output_dir)
    # Crear subcarpeta por autor si se proporciona
    author_subfolder = author.lower().replace(" ", "_") if author else "general"
    output_folder_final = output_folder / author_subfolder / folder_path.name # Añade subcarpeta de autor y nombre de carpeta original
    os.makedirs(output_folder_final, exist_ok=True)

    # Mensaje inicial indicando dónde se guardarán los archivos
    if log_callback:
        log_callback(f"--- Starting Processing ---")
        log_callback(f"Input folder: {folder_path}")
        log_callback(f"Outputting processed files to: {output_folder_final}")
        log_callback(f"Category: {category}, Author: {author if author else 'N/A'}")
        log_callback(f"Segmentation: {'Paragraphs' if category == 'Writings and Books' else 'Whole file'}")
        log_callback(f"Filtering mode: {filter_mode}")
        if filter_mode != "No filter" and filter_prop:
             filter_desc = f"Property='{filter_prop}'"
             if filter_value:
                 filter_desc += f", Value='{filter_value}'"
             log_callback(f"Filter details: {filter_desc}")
        log_callback(f"Minimum characters: {min_chars if min_chars > 0 else 'None'}")
        log_callback(f"JSON processing mode: {'Fast (no salvage)' if skip_salvage else 'Auto-detect + Salvage'}")
        if json_min_id is not None or json_max_id is not None:
            id_range = f"ID range: {json_min_id or 'START'} to {json_max_id or 'END'}"
            log_callback(f"JSON {id_range}")
        log_callback("-" * 20) # Separador
        
    segment_by_paragraphs = category == "Writings and Books"
    
    # Contadores para el resumen
    stats = {
        'total': 0,
        'processed': 0, # Archivos procesados exitosamente
        'skipped': 0,   # Archivos saltados (formato no soportado o error)
        'json': 0,
        'md': 0,
        'txt': 0,
        'unsupported': 0,
        'total_entries_original': 0, # Suma de entradas originales (aproximado para MD/TXT)
        'filtered_prop_entries': 0,  # Suma de filtrados por propiedad
        'short_entries': 0,          # Suma de filtrados por cortos/vacíos
        'saved_entries': 0           # Suma de entradas guardadas final
    }

    files_to_process = list(folder_path.glob("**/*"))
    total_files = len([f for f in files_to_process if f.is_file()])
    files_processed_count = 0

    # Verificación inicial de detención
    if stop_event and stop_event.is_set():
        if log_callback:
            log_callback("Processing stopped by user.")
        return output_folder_final

    for file in files_to_process:
        # Verificar si se solicitó detener el proceso
        if stop_event and stop_event.is_set():
            if log_callback:
                log_callback("Processing stopped by user.")
            break
            
        # Verificar nuevamente el stop_event en cada iteración del archivo
        if stop_event and stop_event.is_set():
            if log_callback:
                log_callback(f"  -> Processing stopped before handling file: {file.name}")
            break
            
        if file.is_file():
            stats['total'] += 1
            files_processed_count += 1
            # Usar el nombre de la carpeta padre como fuente, si no, el nombre de la carpeta raíz
            source = file.parent.name if file.parent != folder_path else folder_path.name
            # Usar output_folder_final calculado antes
            output_file = output_folder_final / f"{file.stem}.ndjson"

            # Log antes de procesar cada archivo
            if log_callback:
                log_callback(f"[{files_processed_count}/{total_files}] Processing: {file.relative_to(folder_path)} -> {output_file.relative_to(output_folder)}")

            ok = False
            msg = ""
            filtered = 0
            short = 0
            entries_before = 0 # Para loguear entradas antes/después

            try:
            if file.suffix.lower() == ".md":
                stats['md'] += 1
                ok, msg = convertir_md_a_ndjson(file, output_file, source, author, segment_by_paragraphs, filter_mode, min_chars)
                    # Estimación de entradas originales para MD/TXT (1 si no segmentado, párrafos si segmentado)
                    # Esto es impreciso si hay filtro min_chars en convertir_md_a_ndjson
                    # if ok: stats['total_entries_original'] += len(msg.split('(')[1].split('/')[1].split(' ')[0]) if segment_by_paragraphs else 1 # Muy complejo extraer ahora
            elif file.suffix.lower() == ".txt":
                stats['txt'] += 1
                ok, msg = convertir_md_a_ndjson(file, output_file, source, author, segment_by_paragraphs, filter_mode, min_chars)
                    # Estimación similar a MD
                    # if ok: stats['total_entries_original'] += ...
                elif file.suffix.lower() in [".json", ".ndjson"]:
                    stats['json'] += 1
                    is_ndjson = False
                    # Detección rápida: si la extensión es .ndjson, asumimos que lo es.
                    if file.suffix.lower() == ".ndjson":
                        is_ndjson = True
                    else: # Si es .json, necesitamos comprobar
                        try:
                            with open(file, 'r', encoding='utf-8') as f_check:
                                first_line = f_check.readline().strip()
                                # Si la primera línea es un objeto JSON válido, probablemente es NDJSON
                                if first_line.startswith('{') and first_line.endswith('}'):
                                    try:
                                        json.loads(first_line)
                                        is_ndjson = True
                                    except json.JSONDecodeError:
                                        is_ndjson = False # No es un objeto JSON válido
                                # Si empieza con [ o { pero no es un objeto válido en una línea, es JSON estándar
                                elif first_line.startswith('[') or first_line.startswith('{'):
                                    is_ndjson = False
                                # Si está vacío o no parece JSON, podría ser NDJSON vacío o erróneo?
                                # Asumimos JSON estándar si no estamos seguros de que sea NDJSON.
                        except Exception:
                            # Error al leer/comprobar, asumimos estándar por seguridad
                            is_ndjson = False

                    # Llamar a la función apropiada con el nuevo parámetro
                    if is_ndjson:
                        if log_callback: log_callback(f"  -> Detected as NDJSON format.")
                        ok, msg, filtered, short = procesar_ndjson(file, output_file, source, author, filter_mode, filter_prop, filter_value, min_chars, text_prop, stop_event)
                    else:
                        if log_callback: log_callback(f"  -> Detected as Standard JSON format (loading full file).")
                        ok, msg, filtered, short = procesar_standard_json(file, output_file, source, author, filter_mode, filter_prop, filter_value, min_chars, text_prop, log_callback, stop_event, skip_salvage, json_min_id, json_max_id)

                    # Actualizar contadores globales
                    if ok:
                        stats['filtered_prop_entries'] += filtered
                        stats['short_entries'] += short
                        # Extraer entradas guardadas del mensaje (simplificado)
                        try:
                           saved_part = msg.split(':')[1].split(' ')[1]
                           saved = int(saved_part.split('/')[0])
                           original = int(saved_part.split('/')[1])
                           stats['saved_entries'] += saved
                           stats['total_entries_original'] += original # Actualizar con originales reales
                        except Exception:
                           pass # Ignorar si falla la extracción
            else:
                stats['unsupported'] += 1
                ok, msg = False, f"Unsupported format: {file.name}"
                
            except Exception as e_proc:
                ok = False
                msg = f"Error processing file {file.name}: {str(e_proc)}"


            if ok:
                 stats['processed'] += 1
                 # Si es JSON/NDJSON, el mensaje ya tiene detalles. Si es MD/TXT, también.
            if log_callback:
                     log_callback(f"  -> OK: {msg}")
            else:
                stats['skipped'] += 1
                if log_callback:
                    log_callback(f"  -> FAILED/SKIPPED: {msg}")


    # Al final de la función, justo antes de retornar, calcular el tiempo transcurrido
    process_elapsed_time = time.time() - process_start_time
    total_minutes = int(process_elapsed_time // 60)
    seconds = int(process_elapsed_time % 60)
    
    # Mostrar resumen final
    if log_callback:
        log_callback("--- PROCESSING SUMMARY ---")
        log_callback(f"Output folder: {output_folder_final}")
        log_callback(f"Total files found: {stats['total']}")
        log_callback(f"  • Processed successfully: {stats['processed']}")
        log_callback(f"  • Skipped (unsupported/error): {stats['skipped']}")
        log_callback(f"File types encountered:")
        log_callback(f"  • JSON/NDJSON: {stats['json']}")
        log_callback(f"  • Markdown: {stats['md']}")
        log_callback(f"  • Text: {stats['txt']}")
        log_callback(f"  • Unsupported: {stats['unsupported']}")

        # Resumen de entradas (solo relevante si se procesaron JSON/NDJSON)
        if stats['json'] > 0:
             log_callback(f"Entry Summary (JSON/NDJSON files):")
             log_callback(f"  • Total original entries found: {stats['total_entries_original']}") # Suma de entradas leídas
        
        if filter_mode and filter_mode != "No filter" and filter_prop:
            filter_desc = f"'{filter_prop}'"
            if filter_value:
                filter_desc += f"='{filter_value}'"
                 log_callback(f"  • Entries filtered by property ({filter_mode} {filter_desc}): {stats['filtered_prop_entries']}")

             if min_chars > 0 or stats['short_entries'] > stats['filtered_prop_entries'] : # Mostrar si hay filtro o si hubo filtrados por vacío/cortos
                 min_chars_text = f"< {min_chars} chars" if min_chars > 0 else "empty/whitespace"
                 log_callback(f"  • Entries filtered (too short: {min_chars_text}): {stats['short_entries']}")

             log_callback(f"  • Total entries saved: {stats['saved_entries']}") # Suma de entradas guardadas
        elif stats['md'] > 0 or stats['txt'] > 0:
             log_callback(f"Entry Summary (MD/TXT files):")
             log_callback(f"  • Entries were processed based on segmentation settings.")
        if min_chars > 0:
                  log_callback(f"  • Entries shorter than {min_chars} characters were filtered.")
             if filter_mode and filter_mode != 'No filter':
                  log_callback(f"  • Note: Property filtering does not apply to MD/TXT.")
        
        # Añadir información de tiempo total
        log_callback(f"Total processing time: {total_minutes} min {seconds} sec")

    return output_folder_final # Devolver la ruta final donde se guardaron los archivos

def seleccionar_carpeta(initial_dir=None):
    """Abre diálogo para seleccionar carpeta, opcionalmente desde un directorio inicial."""
    return filedialog.askdirectory(initialdir=initial_dir if initial_dir else None)

def main():
    root = tk.Tk()
    root.title("Data Cleaning and Standardization")
    root.geometry("850x700") # Ajustar tamaño para nuevos campos/log más grande

    # Variables
    folder_var = tk.StringVar()
    category_var = tk.StringVar(value=CATEGORIAS[0])
    author_var = tk.StringVar()
    processing_output_dir_var = tk.StringVar() # Nueva variable para salida de procesamiento
    
    # Variables de filtrado
    filter_mode_var = tk.StringVar(value=FILTER_MODES[0])
    filter_prop_var = tk.StringVar()
    filter_value_var = tk.StringVar()
    min_chars_var = tk.StringVar(value="0") # Inicializar a 0
    
    # Variables de unificación
    unify_input_dir_var = tk.StringVar() # Carpeta de entrada para unificar (puede ser la salida del paso anterior)
    unified_file_var = tk.StringVar(value="final_dataset.ndjson")

    text_prop_var = tk.StringVar() # Nueva variable
    
    # NUEVO: Variable para modo de procesamiento JSON
    json_processing_mode_var = tk.StringVar(value=JSON_PROCESSING_OPTIONS[0])

    # NUEVO: Variable para modo de procesamiento JSON avanzado
    json_min_id_var = tk.StringVar()
    json_max_id_var = tk.StringVar()
    
    # Nueva variable para búsqueda de texto específico
    search_text_var = tk.StringVar()
    
    # Variables para barra de progreso
    progress_var = tk.DoubleVar()
    progress_text = tk.StringVar(value="Ready")

    # Log y scrollbar
    log_text = tk.Text(root, height=20, width=100, wrap=tk.WORD) # Aumentar tamaño y wrap
    log_scrollbar = tk.Scrollbar(root, command=log_text.yview)
    log_text.config(yscrollcommand=log_scrollbar.set)

    # Usar queue para comunicación thread-safe con UI
    log_queue = queue.Queue()

    def log(msg, is_progress=False):
        # Usar cola para actualizar desde otros hilos
        if is_progress:
            # Si es mensaje de progreso, actualizar barra directamente
            if "Progress:" in msg:
                try:
                    pct_str = msg.split("Progress: ")[1].split("%")[0]
                    pct = float(pct_str)
                    # Actualizar en el hilo principal
                    root.after(0, lambda: progress_var.set(pct))
                    # Actualizar texto de progreso
                    if "objects found" in msg:
                        objects_str = msg.split("(")[1].split(")")[0]
                        root.after(0, lambda: progress_text.set(f"{pct:.1f}% - {objects_str}"))
                    else:
                        root.after(0, lambda: progress_text.set(f"{pct:.1f}%"))
                except Exception:
                    pass
            return
            
        # Para mensajes normales, usar cola
        log_queue.put(msg)

    def check_log_queue():
        """Revisa la cola y actualiza el widget Text en el hilo principal."""
        while not log_queue.empty():
            try:
                msg = log_queue.get_nowait()
        log_text.insert(tk.END, msg + "\n")
        log_text.see(tk.END)
                log_queue.task_done()
            except queue.Empty:
                pass
        # Volver a programar la revisión
        root.after(100, check_log_queue)

    # Función para detener el procesamiento actual
    def stop_processing():
        if messagebox.askyesno("Confirm", "¿Detener el procesamiento actual?"):
            log("Stopping processing (please wait)...")
            STOP_PROCESSING.set()
            stop_button.config(state="disabled")
            stop_all_button.config(state="normal")

    # En la interfaz, añadir botón Stop All Tasks
    def stop_all_tasks():
        if messagebox.askyesno("Confirm", "¿Detener TODOS los procesos de forma forzada?\nEsto puede interrumpir operaciones y es más agresivo que el Stop normal."):
            log("FORCING stop of ALL tasks...")
            STOP_PROCESSING.set()  # Establecer evento stop
            stop_button.config(state="disabled")
            stop_all_button.config(state="disabled")
            
            # Desactivar todos los botones durante el cierre forzado
            process_button.config(state="disabled")
            
            # Si el proceso no se detiene en 3 segundos, ofrecer restaurar interfaz
            def enable_interface_if_needed():
                log("Forzando cierre de procesos pendientes...")
                # Independientemente del resultado, reactivar la interfaz
                process_button.config(state="normal", text="Start Processing")
                progress_text.set("Stopped forcefully")
                
            # Programar la verificación
            root.after(3000, enable_interface_if_needed)
    
    # Función para actualizar estado de campos según modo de filtrado
    def update_filter_fields(*args):
        mode = filter_mode_var.get()
        if mode == "No filter":
            filter_prop_entry.config(state="disabled")
            filter_value_entry.config(state="disabled")
            text_prop_entry.config(state="disabled")
        else:
            filter_prop_entry.config(state="normal")
            filter_value_entry.config(state="normal")
            text_prop_entry.config(state="normal")

    # Panel de procesamiento
    frame1 = tk.LabelFrame(root, text="1. Process Files", padx=10, pady=10)
    frame1.pack(fill="x", padx=10, pady=5)
    
    # --- Fila 0: Carpeta de Entrada ---
    tk.Label(frame1, text="Input Folder:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    folder_entry = tk.Entry(frame1, textvariable=folder_var, width=50)
    folder_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
    tk.Button(frame1, text="Select...", command=lambda: folder_var.set(seleccionar_carpeta())).grid(row=0, column=3, padx=5, pady=2)

    # --- Fila 1: Carpeta de Salida (Procesamiento) --- NUEVO ---
    tk.Label(frame1, text="Output Folder:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    tk.Entry(frame1, textvariable=processing_output_dir_var, width=50).grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
    tk.Button(frame1, text="Select...", command=lambda: processing_output_dir_var.set(seleccionar_carpeta())).grid(row=1, column=3, padx=5, pady=2)


    # --- Fila 2: Categoría y Autor ---
    tk.Label(frame1, text="Category:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    cat_combo = ttk.Combobox(frame1, textvariable=category_var, values=CATEGORIAS, width=25, state="readonly")
    cat_combo.grid(row=2, column=1, sticky="w", padx=5, pady=2)

    tk.Label(frame1, text="Author (Optional):").grid(row=2, column=2, sticky="e", padx=5, pady=2)
    author_entry = tk.Entry(frame1, textvariable=author_var, width=20)
    author_entry.grid(row=2, column=3, sticky="w", padx=5, pady=2) # Ajustado a columna 3


    # --- Fila 3: Separador ---
    ttk.Separator(frame1, orient="horizontal").grid(row=3, column=0, columnspan=4, sticky="ew", pady=10)

    # --- Fila 4: Frame de Filtrado ---
    filter_frame = tk.LabelFrame(frame1, text="Entry Filtering Options", padx=5, pady=5)
    filter_frame.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
    
    # Filtrado por propiedad (dentro de filter_frame)
    tk.Label(filter_frame, text="Filter Mode (JSON only):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    filter_mode_combo = ttk.Combobox(filter_frame, textvariable=filter_mode_var, values=FILTER_MODES, width=25, state="readonly")
    filter_mode_combo.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=2) # Expandido
    filter_mode_combo.bind("<<ComboboxSelected>>", update_filter_fields)
    
    tk.Label(filter_frame, text="Property Key:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    filter_prop_entry = tk.Entry(filter_frame, textvariable=filter_prop_var, width=20, state="disabled")
    filter_prop_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

    tk.Label(filter_frame, text="Value (optional):").grid(row=1, column=2, sticky="e", padx=5, pady=2)
    filter_value_entry = tk.Entry(filter_frame, textvariable=filter_value_var, width=20, state="disabled")
    filter_value_entry.grid(row=1, column=3, sticky="w", padx=5, pady=2)

    # Filtrado por longitud (dentro de filter_frame)
    tk.Label(filter_frame, text="Min. Characters (0=off):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    min_chars_entry = tk.Entry(filter_frame, textvariable=min_chars_var, width=8)
    min_chars_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
    tk.Label(filter_frame, text="(Applies to 'texto' or 'text' field)").grid(row=2, column=2, columnspan=2, sticky="w", padx=5, pady=2)

    # Filtrado por texto (dentro de filter_frame)
    tk.Label(filter_frame, text="Text property (JSON):").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    text_prop_entry = tk.Entry(filter_frame, textvariable=text_prop_var, width=20, state="disabled")
    text_prop_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)
    tk.Label(filter_frame, text="(leave blank to keep full obj)").grid(row=3, column=2, columnspan=2, sticky="w", padx=5, pady=2)

    # NUEVO: Añadir opción procesamiento JSON
    tk.Label(filter_frame, text="JSON Process Mode:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
    json_mode_combo = ttk.Combobox(filter_frame, textvariable=json_processing_mode_var, values=JSON_PROCESSING_OPTIONS, width=35, state="readonly")
    json_mode_combo.grid(row=4, column=1, columnspan=3, sticky="w", padx=5, pady=2)

    # NUEVO: Opciones avanzadas para JSON
    adv_frame = tk.LabelFrame(filter_frame, text="Advanced JSON Options", padx=5, pady=5)
    adv_frame.grid(row=5, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
    
    tk.Label(adv_frame, text="Min ID (if known):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    tk.Entry(adv_frame, textvariable=json_min_id_var, width=12).grid(row=0, column=1, sticky="w", padx=5, pady=2)
    
    tk.Label(adv_frame, text="Max ID (if known):").grid(row=0, column=2, sticky="e", padx=5, pady=2)
    tk.Entry(adv_frame, textvariable=json_max_id_var, width=12).grid(row=0, column=3, sticky="w", padx=5, pady=2)
    
    # Info tooltip
    tk.Label(adv_frame, text="(Use these fields to target specific message ID ranges in corrupted JSON files)", fg="gray").grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=2)

    # --- Fila 5: Botones de Procesar y Stop ---
    buttons_frame = tk.Frame(frame1)
    buttons_frame.grid(row=7, column=0, columnspan=4, pady=15)
    
    process_button = tk.Button(buttons_frame, text="Start Processing", command=lambda: start_processing_thread())
    process_button.pack(side=tk.LEFT, padx=10)
    
    # Nuevo botón Stop
    stop_button = tk.Button(buttons_frame, text="Stop", command=stop_processing, state="disabled", bg="#ffaaaa")
    stop_button.pack(side=tk.LEFT, padx=10)

    # En la interfaz, añadir botón Stop All Tasks
    stop_all_button = tk.Button(buttons_frame, text="Stop All Tasks", command=lambda: stop_all_tasks(), state="normal", bg="#ff5555")
    stop_all_button.pack(side=tk.LEFT, padx=10)

    def start_processing_thread():
        """Inicia el procesamiento en un hilo separado para no bloquear la UI."""
        # Validaciones previas
        input_folder = folder_var.get()
        output_folder = processing_output_dir_var.get()
        if not input_folder or not Path(input_folder).is_dir():
             messagebox.showerror("Error", "Please select a valid Input Folder.")
             return
        if not output_folder:
             messagebox.showerror("Error", "Please select an Output Folder for processed files.")
             return
        # Crear directorio de salida si no existe (ahora se hace dentro de process_folder, pero verificar aquí es bueno)
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create output folder: {output_folder}\n{e}")
            return

        min_chars = 0
        if min_chars_var.get().strip():
            try:
                min_chars = int(min_chars_var.get())
                if min_chars < 0:
                    messagebox.showerror("Error", "Minimum characters must be a non-negative number (0 to disable).")
                    return
            except ValueError:
                messagebox.showerror("Error", "Minimum characters must be a number.")
                return
        
        # Ya no hay módulo de búsqueda
        search_text = None

        # Deshabilitar botón de procesamiento
        process_button.config(state="disabled", text="Processing...")
        # Habilitar botón de Stop
        stop_button.config(state="normal")
        stop_all_button.config(state="normal")
        
        # Resetear evento de parada
        STOP_PROCESSING.clear()
        
        # Resetear barra de progreso
        reset_progress()
        progress_text.set("Starting...")
        
        log_text.delete('1.0', tk.END) # Limpiar log anterior

        # Pasar el modo de procesamiento JSON
        json_mode = json_processing_mode_var.get()
        skip_salvage = json_mode == JSON_PROCESSING_OPTIONS[1]  # True si es Fast mode
        
        # NUEVO: Obtener rangos de IDs si se proporcionaron
        json_min_id = None
        json_max_id = None
        
        if json_min_id_var.get().strip():
            try:
                json_min_id = int(json_min_id_var.get())
            except ValueError:
                messagebox.showerror("Error", "Min ID must be a number or empty.")
                return
        
        if json_max_id_var.get().strip():
            try:
                json_max_id = int(json_max_id_var.get())
            except ValueError:
                messagebox.showerror("Error", "Max ID must be a number or empty.")
                return
                
        # Verificar que min_id <= max_id si ambos están especificados
        if json_min_id is not None and json_max_id is not None and json_min_id > json_max_id:
            messagebox.showerror("Error", "Min ID must be less than or equal to Max ID.")
            return
        
        # Crear y empezar el hilo
        thread = threading.Thread(target=run_processing, args=(
            input_folder, output_folder, min_chars, skip_salvage, json_min_id, json_max_id, None
        ), daemon=True)
        thread.start()

    def run_processing(input_folder, output_folder, min_chars, skip_salvage=False, json_min_id=None, json_max_id=None, search_text=None):
        """Función que se ejecuta en el hilo."""
        try:
            # Iniciar contador de tiempo total (incluyendo inicialización)
            thread_start_time = time.time()
            
            final_output_path = process_folder(
                folder=input_folder,
                category=category_var.get(),
                output_dir=output_folder, 
            author=author_var.get() if author_var.get() else None,
            filter_mode=filter_mode_var.get(),
            filter_prop=filter_prop_var.get() if filter_prop_var.get() else None,
            filter_value=filter_value_var.get() if filter_value_var.get() else None,
            min_chars=min_chars,
                text_prop=text_prop_var.get() if text_prop_var.get() else None,
                log_callback=log,
                stop_event=STOP_PROCESSING,
                skip_salvage=skip_salvage,
                json_min_id=json_min_id,
                json_max_id=json_max_id
            )
            
            # Calcular el tiempo total incluyendo la inicialización del thread
            thread_elapsed_time = time.time() - thread_start_time
            total_minutes = int(thread_elapsed_time // 60)
            seconds = int(thread_elapsed_time % 60)
            
            if STOP_PROCESSING.is_set():
                log("--- Processing Stopped By User ---")
            else:
                log(f"--- Processing Finished (Total time: {total_minutes}m {seconds}s) ---")
                # Actualizar barra de progreso a 100%
                log("  -> Progress: 100.0% (Complete)", is_progress=True)
                
                # Sugerir la carpeta de salida para el paso de unificación solo si terminó normalmente
                unify_input_dir_var.set(str(final_output_path.parent if final_output_path else "")) 
                
                # Intentar pre-rellenar el nombre del archivo unificado basado en el autor
                author = author_var.get().lower().replace(" ", "_") if author_var.get() else "general"
                unified_file_var.set(f"unified_{author}_dataset.ndjson")

        except Exception as e:
            log("--- PROCESSING FAILED ---")
            log(f"An unexpected error occurred: {str(e)}")

        finally:
            # Actualizar barra a estado completo o fallido
            if not STOP_PROCESSING.is_set():
                progress_text.set("Completed")
            else:
                progress_text.set("Stopped")
                
            # Habilitar botón de nuevo (asegurarse de hacerlo en el hilo principal)
            root.after(0, lambda: process_button.config(state="normal", text="Start Processing"))
            # Deshabilitar botón Stop
            root.after(0, lambda: stop_button.config(state="disabled"))
            # Deshabilitar botón Stop All
            root.after(0, lambda: stop_all_button.config(state="disabled"))

    # Panel de unificación
    frame2 = tk.LabelFrame(root, text="2. Unify NDJSON Files", padx=10, pady=10)
    frame2.pack(fill="x", padx=10, pady=5)

    # --- Fila 0 (Unify): Carpeta de Entrada ---
    tk.Label(frame2, text="Input Folder (contains .ndjson):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    tk.Entry(frame2, textvariable=unify_input_dir_var, width=50).grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
    # Botón para seleccionar carpeta para unificar, empezando desde la sugerida si existe
    tk.Button(frame2, text="Select...", command=lambda: unify_input_dir_var.set(seleccionar_carpeta(initial_dir=unify_input_dir_var.get()))).grid(row=0, column=3, padx=5, pady=2)

    # --- Fila 1 (Unify): Nombre de archivo y Autor (para nombre y contenido) ---
    tk.Label(frame2, text="Unified File Name:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    tk.Entry(frame2, textvariable=unified_file_var, width=30).grid(row=1, column=1, sticky="w", padx=5, pady=2)
    # Re-usar la variable author_var para asignar autor durante la unificación si está presente
    tk.Label(frame2, text="Assign Author (if specified above):").grid(row=1, column=2, sticky="e", padx=5, pady=2)
    tk.Label(frame2, textvariable=author_var, fg="blue").grid(row=1, column=3, sticky="w", padx=5, pady=2) # Mostrar autor seleccionado arriba

    # --- Fila 2 (Unify): Remove duplicates checkbox ---
    remove_dups_var = tk.BooleanVar(value=False)
    tk.Checkbutton(frame2, text="Remove duplicates (by texto)", variable=remove_dups_var).grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=2)

    # --- Definición de la función unify (debe ir antes del botón) ---
    def unify():
        unify_folder_str = unify_input_dir_var.get()
        unified_filename = unified_file_var.get()

        if not unify_folder_str or not Path(unify_folder_str).is_dir():
             messagebox.showerror("Error", "Please select a valid Input Folder containing the .ndjson files to unify.")
             return
        if not unified_filename:
             messagebox.showerror("Error", "Please specify a name for the unified output file.")
             return
        if not unified_filename.endswith(".ndjson"):
             unified_filename += ".ndjson"
             unified_file_var.set(unified_filename) # Actualizar la variable

        folder = Path(unify_folder_str)
        files = list(folder.glob("**/*.ndjson")) # Buscar recursivamente
        if not files:
            messagebox.showerror("Error", f"No .ndjson files found recursively in: {folder}")
            return

        # Usar el autor del campo de procesamiento, si existe, para *asignarlo* a las entradas
        author_to_assign = author_var.get() if author_var.get() else None
        # El archivo de salida se guarda DENTRO de la carpeta 'folder' seleccionada
        output_file = folder / unified_filename

        log("--- Starting Unification ---")
        log(f"Source folder: {folder}")
        log(f"Found {len(files)} .ndjson files.")
        log(f"Output file: {output_file}")
        if author_to_assign:
             log(f"Assigning author '{author_to_assign}' to all entries.")

        ok, msg = unificar_archivos_ndjson(files, output_file, author_to_assign, remove_duplicates=remove_dups_var.get())
        log(msg) # Loguear el resultado
        log("--- Unification Finished ---")

        if ok:
            messagebox.showinfo("Success", f"Files unified successfully.\nFinal file: {output_file}")
        else:
            messagebox.showerror("Error", msg)

    # --- Fila 3 (Unify): Botón de Unificar ---
    tk.Button(frame2, text="Unify Files", command=unify).grid(row=3, column=1, columnspan=2, pady=10) # Centrado


    # Panel de logs y progreso
    log_frame = tk.LabelFrame(root, text="Processing Log", padx=10, pady=10)
    log_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    # Añadir barra de progreso encima del log
    progress_frame = tk.Frame(log_frame)
    progress_frame.pack(fill="x", padx=5, pady=5)
    
    tk.Label(progress_frame, textvariable=progress_text, width=30, anchor="w").pack(side=tk.LEFT, padx=5)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, length=400)
    progress_bar.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
    
    # Log text debajo de la barra de progreso
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.pack(side=tk.LEFT, fill="both", expand=True)
    
    # Función para reiniciar el progreso
    def reset_progress():
        progress_var.set(0)
        progress_text.set("Ready")

    # Establecer estado inicial y empezar chequeo de cola de logs
    update_filter_fields()
    check_log_queue() # Iniciar el chequeo periódico de la cola de logs
    
    root.mainloop()

if __name__ == "__main__":
    # Necesitamos importar queue al inicio del script
    # import queue # Añadido aquí, idealmente mover al inicio del archivo # Eliminado de aquí
    main() 