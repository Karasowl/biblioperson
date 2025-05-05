import json
import re
from dateutil import parser as dateparser
from pathlib import Path

# --- Funciones de utilidad --- 

# Extract date from JSON metadata
FECHA_KEYS = ["date", "fecha", "created", "timestamp"]

def extraer_fecha_json(obj):
    if not isinstance(obj, dict):
        return ""
    for key in FECHA_KEYS:
        if key in obj:
            return obj[key]
    return ""

# Extract date from YAML frontmatter in Markdown
YAML_FECHA_KEYS = ["date", "fecha", "created"]
def extraer_fecha_md(contenido_texto):
    if not isinstance(contenido_texto, str):
        return None
    match = re.match(r"---\n(.*?)---\n", contenido_texto, re.DOTALL)
    if match:
        yaml = match.group(1)
        for line in yaml.splitlines():
            for key in YAML_FECHA_KEYS:
                if line.lower().startswith(key+":"):
                    try:
                        return line.split(":",1)[1].strip()
                    except IndexError:
                        continue # Linea mal formada
    return None

# --- Función recursiva para búsqueda de propiedades ---
def find_prop_recursive(data, prop, value=None):
    """Busca recursivamente una propiedad (y opcionalmente un valor) en dicts/listas anidadas."""
    if isinstance(data, dict):
        if prop in data:
            if value is None or data[prop] == value:
                return True
        # Cambio: Iterar sobre values para buscar anidado
        for v in data.values(): 
            if find_prop_recursive(v, prop, value):
                return True
    elif isinstance(data, list):
        for item in data:
            if find_prop_recursive(item, prop, value):
                return True
    return False

# --- Función para extraer el texto (recursiva y lista a texto plano) ---
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
                            # Asegurarse que sean strings antes de unir
                            textos.append(''.join(str(x) for x in subtext if isinstance(x, str)))
                    # Si es otro tipo, intentar convertir a string
                    else:
                         try:
                            textos.append(str(item))
                         except: pass # Ignorar si no se puede convertir
                return ''.join(textos)
            elif isinstance(val, dict):
                 # NUEVO: Si el valor es un dict, buscar recursivamente la misma clave dentro
                 recursive_val = extract_text_recursive(val, key)
                 # Si encontramos algo, lo devolvemos, si no, devolvemos el dict como string
                 return str(recursive_val) if recursive_val is not None else str(val) 
            elif isinstance(val, str):
                return val
            else:
                # Si es otro tipo (número, bool, etc.), convertir a string
                try:
                    return str(val)
                except: 
                    return "" # Devolver vacío si falla la conversión
        # Buscar en valores anidados si no se encontró la clave directamente
        for v in data.values():
            res = extract_text_recursive(v, key)
            if res is not None: # Devuelve el primer resultado encontrado
                return res
    elif isinstance(data, list):
        # Buscar en cada item de la lista
        for item in data:
            res = extract_text_recursive(item, key)
            if res is not None: # Devuelve el primer resultado encontrado
                return res
    return None # No encontrado

# --- Función para reparar problemas de codificación ---
def reparar_mojibake(texto):
    """Intenta reparar problemas comunes de codificación (mojibake) en el texto."""
    if not isinstance(texto, str) or not texto:
        return texto

    try:
        # Intentar decodificar Latin-1 asumiendo que era UTF-8 mal interpretado
        texto_reparado = texto.encode('latin1').decode('utf-8')
        # Solo aceptar la reparación si no introduce caracteres de reemplazo (U+FFFD)
        if '\ufffd' not in texto_reparado:
             texto = texto_reparado
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass # Si falla, mantener el texto original

    # Mapeo de secuencias mojibake comunes a sus caracteres correctos usando Unicode
    reemplazos = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú', 'Ã±': 'ñ',
        'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í', 'Ã“': 'Ó', 'Ãš': 'Ú', 'Ã‘': 'Ñ',
        'Ã¼': 'ü', 'Ãœ': 'Ü',
        'â€™': "'", 'â€œ': '"', 'â€': '"', 'â€”': '—',
        'Â¿': '¿', 'Â¡': '¡',
        # Añadir otros reemplazos comunes si es necesario
    }

    # Aplicar reemplazos
    for mojibake, correcto in reemplazos.items():
        texto = texto.replace(mojibake, correcto)

    return texto

# --- Función para estandarizar fecha ---
def estandarizar_fecha_yyyymm(fecha_str):
    if not fecha_str or not isinstance(fecha_str, str):
        return ""
    try:
        # Usar fuzzy=True para intentar parsear formatos variados
        dt = dateparser.parse(fecha_str, fuzzy=True)
        if dt:
            return dt.strftime("%Y-%m")
    except Exception:
        # Ignorar errores de parseo, devolver vacío
        pass
    return ""

# --- Función para unificar archivos NDJSON ---
def unificar_archivos_ndjson(archivos, salida, autor=None, remove_duplicates=False):
    """
    Unifica varios archivos NDJSON en uno solo, normalizando el campo de texto a 'texto'.
    Si una entrada tiene 'contenido_texto', se renombra a 'texto'.
    Si remove_duplicates es True, elimina duplicados por el campo 'texto'.
    """
    try:
        textos_vistos = set()
        total_entries = 0
        written_entries = 0
        duplicates = 0

        with open(salida, "w", encoding="utf-8") as outfile:
            for idx, archivo in enumerate(archivos, 1):
                print(f"Procesando archivo {idx}/{len(archivos)}: {archivo.name}")
                try:
                    with open(archivo, "r", encoding="utf-8") as infile:
                        for line in infile:
                            total_entries += 1
                            try:
                                obj = json.loads(line)
                                # Normalizar campo de texto
                                if 'contenido_texto' in obj:
                                    obj['contenido_texto'] = obj.pop('contenido_texto')
                                # Asignar autor si se especifica
                                if autor:
                                    obj["autor"] = autor
                                # Verificar duplicados si se solicita
                                contenido_texto = obj.get("contenido_texto", "")
                                contenido_texto_hash = hash(contenido_texto)
                                if remove_duplicates:
                                    if contenido_texto_hash in textos_vistos:
                                        duplicates += 1
                                        continue
                                    textos_vistos.add(contenido_texto_hash)
                                # Reasignar ID secuencial
                                obj["id"] = written_entries + 1
                                outfile.write(json.dumps(obj, ensure_ascii=False) + "\n")
                                written_entries += 1
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"Error en entrada: {e}")
                    continue
        msg = f"Unified {len(archivos)} NDJSON files into {salida.name}. Total: {written_entries} entries written"
        if remove_duplicates and duplicates > 0:
            msg += f" ({duplicates} duplicates removed)"
        return True, msg
    except Exception as e:
        return False, f"Error unifying NDJSON files: {str(e)}"

# --- Función para estandarizar fecha ---
def estandarizar_fecha_yyyymm(fecha_str):
    if not fecha_str or not isinstance(fecha_str, str):
        return ""
    try:
        # Usar fuzzy=True para intentar parsear formatos variados
        dt = dateparser.parse(fecha_str, fuzzy=True)
        if dt:
            return dt.strftime("%Y-%m")
    except Exception:
        # Ignorar errores de parseo, devolver vacío
        pass
    return ""

# --- Función para unificar archivos NDJSON ---
def unificar_archivos_ndjson(archivos, salida, autor=None, remove_duplicates=False):
    """
    Unifica varios archivos NDJSON en uno solo, estandarizando fecha y opcionalmente quitando duplicados.
    Las entradas se ordenan jerárquicamente: por directorio, por archivo y por fecha.

    Args:
        archivos: Lista de rutas a archivos NDJSON
        salida: Ruta del archivo de salida
        autor: Autor para asignar a todas las entradas (opcional)
        remove_duplicates: Si True, elimina duplicados por campo "contenido_texto"

    Returns:
        (bool, str): Tupla con éxito y mensaje
    """
    if not isinstance(archivos, list): 
        return False, "El argumento 'archivos' debe ser una lista de rutas."
    if not isinstance(salida, Path):
        salida = Path(salida)
        
    try:
        # Asegurar que el directorio de salida exista
        salida.parent.mkdir(parents=True, exist_ok=True)
        
        # Set para detectar duplicados si se solicita
        textos_vistos = set() if remove_duplicates else None
 
        # NUEVO: Registrar carpetas y archivos procesados
        carpetas_procesadas = set()
        archivos_por_carpeta = {}
        
        # NUEVO: Lista para almacenar información sobre duplicados si es necesario
        duplicados_info = [] if remove_duplicates else None

        # Contador total
        total_entries_read = 0
        written_entries = 0
        duplicates_skipped = 0
        errors_reading = 0
        errors_processing = 0
        
        # NUEVO: Almacenar todas las entradas en memoria para ordenar después
        todas_las_entradas = []

        # NUEVO: Recolectar información sobre carpetas primero
        for archivo_path in archivos:
            if not isinstance(archivo_path, Path):
                archivo_path = Path(archivo_path)
            
            # Registrar carpeta contenedora
            carpeta = archivo_path.parent
            carpetas_procesadas.add(str(carpeta))
            
            # Registrar archivo en su carpeta
            if str(carpeta) not in archivos_por_carpeta:
                archivos_por_carpeta[str(carpeta)] = []
            archivos_por_carpeta[str(carpeta)].append(archivo_path.name)

        print(f"Procesando archivos de {len(carpetas_procesadas)} carpetas diferentes.")
        for carpeta in carpetas_procesadas:
            print(f"Carpeta: {carpeta} - {len(archivos_por_carpeta[carpeta])} archivos")

        # FASE 1: Lectura de archivos y procesamiento de entradas
        for idx_file, archivo_path in enumerate(archivos, 1):
            if not isinstance(archivo_path, Path):
                archivo_path = Path(archivo_path)
            
            if not archivo_path.is_file():
                print(f"Warning: Archivo no encontrado, omitiendo: {archivo_path}")
                continue
                
            print(f"Unificando archivo {idx_file}/{len(archivos)}: {archivo_path.name}")
            
            # NUEVO: Extraer directorio y nombre de archivo para ordenar
            directorio = str(archivo_path.parent)
            nombre_archivo = archivo_path.name
            
            try:
                with open(archivo_path, "r", encoding="utf-8") as infile:
                    for line_num, line in enumerate(infile, 1):
                        if not line.strip():
                            continue  # saltar líneas vacías
                        
                        total_entries_read += 1
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            print(f"Warning: Línea JSON inválida en {archivo_path.name}, línea {line_num}. Omitiendo.")
                            errors_processing += 1
                            continue

                        if not isinstance(obj, dict):
                            errors_processing += 1
                            continue # Solo procesar objetos diccionario

                        # Asignar/reescribir autor si corresponde
                        if autor is not None:
                            obj["autor"] = autor
                        
                        # Estandarizar fecha a YYYY-MM
                        fecha_original = obj.get("fecha", "")
                        fecha_estandarizada = estandarizar_fecha_yyyymm(fecha_original)
                        obj["fecha_estandarizada"] = fecha_estandarizada

                        # NUEVO: Añadir metadatos para ordenamiento
                        obj["_directorio_origen"] = directorio
                        obj["_archivo_origen"] = nombre_archivo

                        # Detección de duplicados
                        if remove_duplicates:
                            contenido_texto_key = obj.get("contenido_texto")
                            # Si no tiene campo contenido_texto, intentamos con 'text' o usamos el objeto como string
                            if contenido_texto_key is None:
                                contenido_texto_key = obj.get("text", str(obj)) 
                            
                            # Normalizar: quitar espacios extremos y convertir a string
                            contenido_texto_norm = str(contenido_texto_key).strip()
                            
                            # NUEVO: Obtener las primeras 3 palabras (o menos) para el log
                            palabras = contenido_texto_norm.split()
                            primeras_palabras = " ".join(palabras[:3]) if palabras else "(contenido_texto vacío)"
                            
                            # Usar hash para eficiencia con textos largos
                            contenido_texto_hash = hash(contenido_texto_norm) 
                            
                            if contenido_texto_hash in textos_vistos:
                                # NUEVO: Imprimir INMEDIATAMENTE cada duplicado para garantizar que se vea
                                print(f"DUPLICADO ENCONTRADO => Archivo: {archivo_path.name}, Línea: {line_num}, Texto: \"{primeras_palabras}...\"")
                                
                                # NUEVO: Guardar información sobre este duplicado
                                duplicados_info.append({
                                    "archivo": str(archivo_path.name),
                                    "inicio_contenido_texto": primeras_palabras,
                                    "linea": line_num
                                })
                                duplicates_skipped += 1
                                continue  # duplicado -> saltar
                            textos_vistos.add(contenido_texto_hash)

                        # Añadir la entrada a la lista para ordenar después
                        todas_las_entradas.append(obj)
                        
            except Exception as e_read:
                print(f"Error leyendo archivo {archivo_path.name}: {e_read}")
                errors_reading += 1
                continue # Continuar con el siguiente archivo

        # NUEVO: Ordenamiento jerárquico
        print(f"Ordenando {len(todas_las_entradas)} entradas...")
        
        # Función de ordenamiento para fechas (maneja fechas inválidas o vacías)
        def fecha_clave(fecha_str):
            if not fecha_str:
                return "0000-00"  # Las entradas sin fecha aparecen primero
            return fecha_str
        
        # Ordenar por directorio > archivo > fecha
        todas_las_entradas.sort(key=lambda x: (
            x.get("_directorio_origen", ""),
            x.get("_archivo_origen", ""),
            fecha_clave(x.get("fecha_estandarizada", ""))
        ))
        
        print(f"Escritura ordenada de {len(todas_las_entradas)} entradas...")
        
        # FASE 2: Escritura ordenada de las entradas
        with open(salida, "w", encoding="utf-8") as outfile:
            for idx, obj in enumerate(todas_las_entradas, 1):
                # Asignar nuevo ID secuencial global
                obj["id_global"] = idx
                written_entries += 1
                
                # Eliminar campos temporales de ordenamiento
                obj.pop("_directorio_origen", None)
                obj.pop("_archivo_origen", None)
                
                # Escribir objeto procesado
                outfile.write(json.dumps(obj, ensure_ascii=False) + "\n")

        # NUEVO: Generar resumen detallado para los duplicados
        if remove_duplicates and duplicados_info:
            print(f"\n--- DETALLE DE DUPLICADOS ELIMINADOS ({duplicates_skipped} total) ---")
            # Asegurarse de mostrar TODOS los duplicados, no solo los primeros 20
            print(f"Lista completa de duplicados:")
            for idx, dup in enumerate(duplicados_info, 1):
                print(f"{idx}. Archivo: {dup['archivo']}, Línea: {dup['linea']}, Texto: \"{dup['inicio_contenido_texto']}...\"")

            # NUEVO: Análisis estadístico de duplicados por archivo
            print("\n--- ANÁLISIS DE DUPLICADOS POR ARCHIVO ---")
            duplicados_por_archivo = {}
            for dup in duplicados_info:
                archivo = dup["archivo"]
                if archivo not in duplicados_por_archivo:
                    duplicados_por_archivo[archivo] = 0
                duplicados_por_archivo[archivo] += 1
            
            # Mostrar los 10 archivos con más duplicados
            print("Archivos con mayor cantidad de duplicados:")
            for i, (archivo, cantidad) in enumerate(sorted(duplicados_por_archivo.items(), key=lambda x: x[1], reverse=True)[:10], 1):
                print(f"{i}. {archivo}: {cantidad} duplicados")

        # NUEVO: Resumen de carpetas
        print(f"\n--- RESUMEN DE CARPETAS PROCESADAS ({len(carpetas_procesadas)}) ---")
        for carpeta in sorted(carpetas_procesadas):
            archivos_count = len(archivos_por_carpeta[carpeta])
            print(f"• {carpeta}: {archivos_count} archivos")
            
        # NUEVO: Resumen del ordenamiento
        print(f"\n--- RESUMEN DE ORDENAMIENTO ---")
        print(f"Las entradas fueron ordenadas jerárquicamente por:")
        print(f"1. Directorio de origen")
        print(f"2. Archivo fuente dentro del directorio")
        print(f"3. Fecha (donde esté disponible)")

        msg = f"Unified {len(archivos)} NDJSON files into {salida.name}."
        msg += f" Total: {written_entries} entries written"
        msg += f" (ordered by directory > file > date)"

        if remove_duplicates and duplicates_skipped > 0:
            msg += f" ({duplicates_skipped} duplicates removed)"

        return True, msg

    except Exception as e_main:
        return False, f"Error principal durante la unificación: {str(e_main)}" 