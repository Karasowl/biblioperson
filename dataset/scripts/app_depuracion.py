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
import subprocess # Necesario para llamar a Pandoc

# --- Importaciones locales ---
from converters import (
    convert_docx_to_markdown,
    convert_docx_to_text,
    convert_pdf_to_text,
    # Añadir otras funciones de converters si son necesarias
)
# Importar la función principal de procesamiento
from processors import process_folder 
# (Las funciones de segmentación, ndjson, etc. son llamadas internamente por process_folder)
# Importar funciones de utilidad necesarias para la UI
from utils import (
    unificar_archivos_ndjson, 
    extraer_fecha_json, # Necesaria para process_single_json_entry si se moviera aquí
    extraer_fecha_md,   # Necesaria para procesar MD/TXT si se moviera aquí
    find_prop_recursive, # Necesaria para process_single_json_entry si se moviera aquí
    extract_text_recursive, # Necesaria para process_single_json_entry si se moviera aquí
    reparar_mojibake # Necesaria para process_single_json_entry si se moviera aquí
)

# (Asegúrate de que ijson esté instalado - si no, mover el check aquí)
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
FUENTES_DIR = Path("E:/dev-projects/forIAs/contenido/poemas")  # Actualizado para las pruebas
SALIDAS_DIR = Path(r"C:\Users\adven\OneDrive\Escritorio\Final")  # Actualizado para las pruebas
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

# --- Funciones de utilidad (a mover a utils.py) ---
def find_prop_recursive(data, prop, value=None):
    """Busca recursivamente una propiedad (y opcionalmente un valor) en cualquier estructura anidada."""
    if isinstance(data, dict):
        if prop in data:
            if value is None or data[prop] == value:
                return True
        for v in data.values():
            if find_prop_recursive(v, prop, value):
                return True
    elif isinstance(data, list):
        for item in data:
            if find_prop_recursive(item, prop, value):
                return True
    return False

def extract_text_recursive(data, key):
    """Busca recursivamente una propiedad y extrae su valor como texto."""
    if isinstance(data, dict):
        if key in data:
            val = data[key]
            if isinstance(val, list):
                return ' '.join(str(x) for x in val if x)
            return str(val) if val is not None else ''
        for v in data.values():
            result = extract_text_recursive(v, key)
            if result:
                return result
    elif isinstance(data, list):
        results = []
        for item in data:
            text = extract_text_recursive(item, key)
            if text:
                results.append(text)
        return ' '.join(results) if results else ''
    return ''

def reparar_mojibake(texto):
    """Intenta reparar problemas comunes de codificación (mojibake) en el texto."""
    if not isinstance(texto, str) or not texto:
        return texto
        
    try:
        # Intentar decodificar emojis y otros caracteres Unicode
        # A veces los emojis vienen como ð pero deberían ser UTF-8
        texto = texto.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Si falla, mantener el texto original
        pass
        
    # Mapeo de secuencias mojibake comunes a sus caracteres correctos usando Unicode
    reemplazos = {
        '\u00c3\u00a1': 'á',  # Ã¡
        '\u00c3\u00a9': 'é',  # Ã©
        '\u00c3\u00ad': 'í',  # Ã­
        '\u00c3\u00b3': 'ó',  # Ã³
        '\u00c3\u00ba': 'ú',  # Ãº
        '\u00c3\u00b1': 'ñ',  # Ã±
        '\u00c3\u0081': 'Á',  # Ã
        '\u00c3\u0089': 'É',  # Ã‰
        '\u00c3\u008d': 'Í',  # Ã
        '\u00c3\u0093': 'Ó',  # Ã"
        '\u00c3\u009a': 'Ú',  # Ãš
        '\u00c3\u0091': 'Ñ',  # Ã'
        '\u00c3\u00bc': 'ü',  # Ã¼
        '\u00c3\u009c': 'Ü',  # Ãœ
        '\u00e2\u0080\u0099': "'",  # â€™
        '\u00e2\u0080\u009c': '"',  # â€œ
        '\u00e2\u0080\u009d': '"',  # â€
        '\u00e2\u0080\u0094': '—',  # â€"
        '\u00c2\u00bf': '¿',  # Â¿
        '\u00c2\u00a1': '¡'   # Â¡
    }
    
    # Aplicar reemplazos
    for mojibake, correcto in reemplazos.items():
        texto = texto.replace(mojibake, correcto)
    
    return texto

def unificar_archivos_ndjson(archivos, salida, autor=None, remove_duplicates=False):
    """
    Unifica varios archivos NDJSON en uno solo.
    
    Args:
        archivos: Lista de rutas a archivos NDJSON
        salida: Ruta del archivo de salida
        autor: Autor para asignar a todas las entradas (opcional)
        remove_duplicates: Si True, elimina duplicados por campo "texto"

    Returns:
        (bool, str): Tupla con éxito y mensaje
    """
    try:
        # Set para detectar duplicados si se solicita
        textos_vistos = set()

        # Contador total
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
                                
                                # Asignar autor si se especifica
                                if autor:
                                    obj["autor"] = autor

                                # Verificar duplicados si se solicita
                                if remove_duplicates:
                                    texto = obj.get("texto", "")
                                    # Hash del texto para manejar textos largos eficientemente
                                    texto_hash = hash(texto)

                                    if texto_hash in textos_vistos:
                                        duplicates += 1
                                        continue
                                    
                                    textos_vistos.add(texto_hash)

                                # Reasignar ID secuencial
                                obj["id"] = written_entries + 1

                                # Escribir a archivo salida
                                outfile.write(json.dumps(obj, ensure_ascii=False) + "\n")
                                written_entries += 1

                            except json.JSONDecodeError:
                                # Ignorar líneas no JSON
                                continue
                except Exception as e:
                    # Ignorar errores en entradas específicas
                    print(f"Error en entrada: {e}")
                    continue
        
        msg = f"Unified {len(archivos)} NDJSON files into {salida.name}."
        msg += f" Total: {written_entries} entries written"

        if remove_duplicates and duplicates > 0:
            msg += f" ({duplicates} duplicates removed)"

        return True, msg

    except Exception as e:
        return False, f"Error unifying NDJSON files: {str(e)}"

# --- Interfaz Gráfica (Tkinter) --- 
def main():
    # Crear ventana principal
    root = tk.Tk()
    root.title("Procesador y Depurador de Textos v1.2 (Refactored)")
    root.geometry("1200x700")  # Más ancho para la columna de logs

    # --- NUEVO: Frame principal con dos columnas ---
    main_container = tk.Frame(root)
    main_container.pack(fill="both", expand=True)

    # Frame izquierdo para paneles de procesamiento y unificación
    left_frame = tk.Frame(main_container)
    left_frame.pack(side=tk.LEFT, fill="both", expand=True)

    # Frame derecho para logs y progreso
    right_frame = tk.Frame(main_container, width=400)
    right_frame.pack(side=tk.RIGHT, fill="y")
    right_frame.pack_propagate(False)  # Mantener ancho fijo

    # Variables Tkinter
    folder_var = tk.StringVar(value=str(FUENTES_DIR))  # Inicializar con la ruta de prueba
    processing_output_dir_var = tk.StringVar(value=str(SALIDAS_DIR))  # Inicializar con la ruta de prueba
    category_var = tk.StringVar(value="Poems and Songs")  # Establecer "Poems and Songs" por defecto
    author_var = tk.StringVar()
    min_chars_var = tk.StringVar(value="0")
    json_processing_mode_var = tk.StringVar(value=JSON_PROCESSING_OPTIONS[0])
    json_min_id_var = tk.StringVar()
    json_max_id_var = tk.StringVar()
    unify_input_dir_var = tk.StringVar()
    unified_file_var = tk.StringVar()
    
    # Log Text Widget y Scrollbar
    log_text = tk.Text(right_frame, height=15, wrap="word", state="normal")
    log_queue = queue.Queue()
    
    # Barra de progreso
    progress_var = tk.DoubleVar()
    progress_text = tk.StringVar(value="Ready")

    # Inicializar la lista de widgets de propiedades de texto
    text_prop_widgets = []
    # Inicializar la lista de widgets de filtros de propiedad
    filter_widgets = []

    # --- Funciones auxiliares de la UI ---
    def seleccionar_carpeta(initial_dir=None):
        if not initial_dir:
            initial_dir = FUENTES_DIR
        folder_selected = filedialog.askdirectory(initialdir=initial_dir)
        return folder_selected

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
                    pass # Restaurado para corregir linter error
            elif "Progress:" in msg:
                # Es un progreso de chunk individual, no actualizamos la barra global
                # pero actualizamos el texto para mostrar el progreso del archivo actual
                try:
                    pct_str = msg.split("Progress: ")[1].split("%")[0]
                    pct = float(pct_str)
                    file_info = msg.split("(")[1].split(")")[0]
                    root.after(0, lambda: progress_text.set(f"File: {pct:.1f}% ({file_info})"))
                    root.after(0, lambda: progress_var.set(pct))
                except:
                     pass # Evitar errores si el formato del mensaje cambia
            return
        
        # Resaltar mensajes importantes
        if msg.startswith("---"):
            # Mensajes de sección/encabezado
            log_queue.put(f"\n{msg}")
        elif msg.startswith("->"):
            # Mensajes con información detallada del procesamiento
            log_queue.put(f"  {msg}")
        elif msg.startswith("Procesando:"):
            # Destacar información de archivos que se están procesando
            log_queue.put(f"\n[PROCESANDO] {msg}")
        elif "ERROR" in msg.upper():
            # Resaltar errores
            log_queue.put(f"⚠️ {msg}")
        else:
            # Mensajes normales
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
            except Exception as e: # Asegurarse que cualquier otro error no detenga el chequeo
                print(f"Error updating log: {e}")
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
        # Ya no tenemos estos widgets únicos - en cambio tenemos widgets dinámicos
        # Podemos eliminar esta función o modificarla si necesitamos otra lógica
        pass

    # Panel de procesamiento
    frame1 = tk.LabelFrame(left_frame, text="1. Process Files", padx=10, pady=10)
    frame1.pack(fill="x", padx=10, pady=5)

    # --- Funciones placeholder para botones de UI avanzada ---
    def add_filter():
        # Esta función está vacía porque la UI avanzada está comentada
        # messagebox.showinfo("Info", "Advanced filter UI is currently disabled.")
        pass 

    def add_text_property():
        prop_var = tk.StringVar()
        frame = tk.Frame(text_props_container)
        entry = tk.Entry(frame, textvariable=prop_var, width=30)
        entry.pack(side=tk.LEFT, padx=2)
        # Botón para eliminar el campo si se desea
        def remove():
            frame.destroy()
            text_prop_widgets.remove(widget_group)
        remove_btn = tk.Button(frame, text="X", command=remove, fg="red", width=2)
        remove_btn.pack(side=tk.LEFT, padx=2)
        frame.pack(fill="x", pady=2)
        widget_group = {'prop': prop_var, 'frame': frame}
        text_prop_widgets.append(widget_group)
    # -------------------------------------------------------
    
    # --- Fila 0: Carpeta de Entrada ---
    tk.Label(frame1, text="Input Folder:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    folder_entry = tk.Entry(frame1, textvariable=folder_var, width=50)
    folder_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
    tk.Button(frame1, text="Select...", command=lambda: folder_var.set(seleccionar_carpeta())).grid(row=0, column=3, padx=5, pady=2)

    # --- Fila 1: Carpeta de Salida (Procesamiento) ---
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

    # --- Fila 4: Frame de Filtrado --- (UI Avanzada comentada)
    filter_frame = tk.LabelFrame(frame1, text="Entry Filtering Options", padx=5, pady=5) # Ajustar texto
    filter_frame.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
    
    # --- Widgets de filtros/propiedades (Necesitamos referencias para habilitar/deshabilitar) ---
    # Frame para filtros de propiedad
    property_filters_frame = tk.Frame(filter_frame)
    property_filters_frame.grid(row=0, column=0, columnspan=4, sticky="ew")
    tk.Label(property_filters_frame, text="Property Filters (JSON only):", font=("", 10, "bold")).pack(anchor="w", padx=5)
    filters_container = tk.Frame(property_filters_frame)
    filters_container.pack(fill="x", expand=True, padx=5)
    add_filter_btn = tk.Button(property_filters_frame, text="Add Property Filter", command=add_filter)
    add_filter_btn.pack(pady=5)
    
    # Separador
    ttk.Separator(filter_frame, orient="horizontal").grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
    
    # Frame para propiedades de texto
    text_props_frame = tk.Frame(filter_frame)
    text_props_frame.grid(row=2, column=0, columnspan=4, sticky="ew")
    tk.Label(text_props_frame, text="Text Properties (where to find text):", font=("", 10, "bold")).pack(anchor="w", padx=5)
    text_props_container = tk.Frame(text_props_frame)
    text_props_container.pack(fill="x", expand=True, padx=5)
    add_text_prop_btn = tk.Button(text_props_frame, text="Add Text Property", command=add_text_property)
    add_text_prop_btn.pack(pady=5)
    tk.Label(text_props_frame, text="(Leave empty to use full JSON object as text)", fg="gray").pack(anchor="w", padx=5)
    
    # Separador
    ttk.Separator(filter_frame, orient="horizontal").grid(row=3, column=0, columnspan=4, sticky="ew", pady=5)

    # Frame para otras opciones (Min Chars, JSON Mode, Adv JSON)
    other_options_frame = tk.Frame(filter_frame)
    other_options_frame.grid(row=4, column=0, columnspan=4, sticky="ew")
    
    tk.Label(other_options_frame, text="Min. Characters (0=off):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    min_chars_entry = tk.Entry(other_options_frame, textvariable=min_chars_var, width=8)
    min_chars_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
    tk.Label(other_options_frame, text="(Applies to extracted text)").grid(row=0, column=2, sticky="w", padx=5)

    tk.Label(other_options_frame, text="JSON Process Mode:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    json_mode_combo = ttk.Combobox(other_options_frame, textvariable=json_processing_mode_var, values=JSON_PROCESSING_OPTIONS, width=35, state="readonly")
    json_mode_combo.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=2)

    # Opciones avanzadas JSON
    adv_frame = tk.LabelFrame(other_options_frame, text="Advanced JSON Options", padx=5, pady=5)
    adv_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    tk.Label(adv_frame, text="Min ID:").grid(row=0, column=0, sticky="e", padx=2)
    min_id_entry = tk.Entry(adv_frame, textvariable=json_min_id_var, width=10)
    min_id_entry.grid(row=0, column=1, sticky="w", padx=2)
    tk.Label(adv_frame, text="Max ID:").grid(row=0, column=2, sticky="e", padx=2)
    max_id_entry = tk.Entry(adv_frame, textvariable=json_max_id_var, width=10)
    max_id_entry.grid(row=0, column=3, sticky="w", padx=2)
    tk.Label(adv_frame, text="(Use for corrupted JSON)", fg="gray").grid(row=1, column=0, columnspan=4, sticky="w", padx=2)

    # --- Fila 5: Botones de Procesar y Stop ---
    process_buttons_frame = tk.Frame(frame1) # Renombrado para evitar colisión
    # Ajustar la fila donde se colocan los botones de procesar/stop
    process_buttons_frame.grid(row=6, column=0, columnspan=4, pady=15) 
    
    process_button = tk.Button(process_buttons_frame, text="Start Processing", command=lambda: start_processing_thread())
    process_button.pack(side=tk.LEFT, padx=10)
    
    # Nuevo botón Stop
    stop_button = tk.Button(process_buttons_frame, text="Stop", command=stop_processing, state="disabled", bg="#ffaaaa")
    stop_button.pack(side=tk.LEFT, padx=10)

    # En la interfaz, añadir botón Stop All Tasks
    stop_all_button = tk.Button(process_buttons_frame, text="Stop All Tasks", command=lambda: stop_all_tasks(), state="normal", bg="#ff5555")
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
        
        # Recopilar las reglas de filtrado
        filter_rules = []
        for widget_group in filter_widgets:
            mode = widget_group['mode'].get()
            prop = widget_group['prop'].get().strip()
            value = widget_group['value'].get().strip()
            
            if prop:  # Solo añadir si hay una propiedad especificada
                filter_rules.append({
                    'mode': mode,
                    'property': prop,
                    'value': value or None
                })
        
        # Recopilar propiedades de texto
        text_properties = []
        for widget_group in text_prop_widgets:
            prop = widget_group['prop'].get().strip()
            if prop:
                text_properties.append(prop)
        
        # --- DESACTIVAR FILTROS SI ES 'Poems and Songs' o 'Writings and Books' ---
        current_category = category_var.get()
        if current_category in ("Poems and Songs", "Writings and Books"):
            log(f"INFO: Disabling filters for category: {current_category}")
            filter_rules = []
            text_properties = []
            min_chars = 0
            # Asegurarse de que las variables de ID también se ignoren si no aplican
            json_min_id = None
            json_max_id = None
        
        # Crear y empezar el hilo
        thread = threading.Thread(target=run_processing, args=(
            input_folder, output_folder, min_chars, skip_salvage, json_min_id, json_max_id, None,
            filter_rules, text_properties
        ), daemon=True)
        thread.start()

    def run_processing(input_folder, output_folder, min_chars, skip_salvage=False, json_min_id=None, json_max_id=None, search_text=None, filter_rules=None, text_properties=None):
        """Función que se ejecuta en el hilo."""
        try:
            # Iniciar contador de tiempo total (incluyendo inicialización)
            thread_start_time = time.time()
            
            final_output_path = process_folder(
                folder=input_folder,
                category=category_var.get(),
                output_dir=output_folder, 
            author=author_var.get() if author_var.get() else None,
                filter_rules=filter_rules,
            min_chars=min_chars,
                text_properties=text_properties,
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
    frame2 = tk.LabelFrame(left_frame, text="2. Unify NDJSON Files", padx=10, pady=10)
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
    def unify_logic():
        unify_folder_str = unify_input_dir_var.get()
        unified_filename = unified_file_var.get()

        if not unify_folder_str or not Path(unify_folder_str).is_dir():
             # Corregido: Añadir llamada a root.after para reactivar botón
             messagebox.showerror("Error", "Please select a valid Input Folder containing .ndjson files."); root.after(0, lambda: unify_button.config(state="normal", text="Unify Files")); return
        if not unified_filename:
             # Corregido: Añadir llamada a root.after para reactivar botón
             messagebox.showerror("Error", "Please specify a name for the unified output file."); root.after(0, lambda: unify_button.config(state="normal", text="Unify Files")); return
        if not unified_filename.endswith(".ndjson"):
             unified_filename += ".ndjson"; unified_file_var.set(unified_filename)

        folder = Path(unify_folder_str)
        
        # NUEVO: Función para contar y analizar archivos NDJSON recursivamente
        def contar_analizar_archivos(carpeta):
            # Contador de archivos por carpeta
            conteo_carpetas = {}
            # Lista de todos los archivos encontrados
            todos_archivos = []
            
            # Recorrer recursivamente
            for ruta, subcarpetas, archivos in os.walk(carpeta):
                ruta_path = Path(ruta)
                archivos_ndjson = [f for f in archivos if f.lower().endswith('.ndjson')]
                if archivos_ndjson:
                    conteo_carpetas[str(ruta_path)] = len(archivos_ndjson)
                    todos_archivos.extend([ruta_path / f for f in archivos_ndjson])
            
            return conteo_carpetas, todos_archivos
        
        # Ejecutar análisis
        log("--- Analyzing Directory Structure ---")
        carpetas_conteo, todos_archivos_ndjson = contar_analizar_archivos(folder)
        total_carpetas = len(carpetas_conteo)
        total_archivos = len(todos_archivos_ndjson)
        
        # Mostrar estructura
        log(f"Found {total_carpetas} folders containing NDJSON files")
        log(f"Total NDJSON files found: {total_archivos}")
        for carpeta, conteo in sorted(carpetas_conteo.items()):
            log(f"• {carpeta}: {conteo} files")
        
        # MODIFICADO: Siempre buscar de forma recursiva en todas las subcarpetas y sus anidaciones
        files = todos_archivos_ndjson  # Usar la lista completa que generamos
        
        if not files:
            # Corregido: Añadir llamada a root.after para reactivar botón
            messagebox.showerror("Error", f"No .ndjson files found in {folder} or any of its subfolders"); root.after(0, lambda: unify_button.config(state="normal", text="Unify Files")); return
        else:
            log(f"Preparing to process {len(files)} .ndjson files")

        author_to_assign = author_var.get() if author_var.get() else None
        # Guardar archivo unificado en la CARPETA DE SALIDA PRINCIPAL (no dentro de la carpeta de entrada de unificación)
        main_output_folder = processing_output_dir_var.get() or folder.parent # Usar salida principal o padre de entrada si no hay
        # Corregido: Asegurarse que main_output_folder sea Path
        output_file = Path(main_output_folder) / unified_filename 

        log("--- Starting Unification ---")
        log(f"Source folder: {folder} (including all subfolders)")
        log(f"Found {len(files)} .ndjson files to process.")
        log(f"Output file: {output_file}")
        if author_to_assign: log(f"Assigning author '{author_to_assign}' to all entries.")
        
        # NUEVO: Redirigir la salida estándar para capturar logs detallados
        import sys
        from io import StringIO
        
        # Guardar la salida estándar original
        original_stdout = sys.stdout
        
        # Crear un buffer para capturar la salida
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            # Llamar a la función de unificación importada
            ok, msg = unificar_archivos_ndjson(files, output_file, author_to_assign, remove_duplicates=remove_dups_var.get())
            
            # Restaurar la salida estándar
            sys.stdout = original_stdout
            
            # Procesar la salida capturada línea por línea y enviarla al log
            captured_logs = captured_output.getvalue().splitlines()
            for line in captured_logs:
                if line.strip():  # Solo enviar líneas no vacías
                    # NUEVO: Resaltar líneas de duplicados con más claridad
                    if "DUPLICADO ENCONTRADO" in line:
                        # Formato especial para duplicados
                        formatted_line = line.replace("DUPLICADO ENCONTRADO => ", "")
                        log(f"🔄 DUPLICADO: {formatted_line}")
                    elif "Archivo:" in line and "Texto:" in line:
                        log(f"DUPLICADO: {line}")
                    else:
                        log(line)
            
            log(msg)
            log("--- Unification Finished ---")
        except Exception as e:
            # Restaurar la salida en caso de error
            sys.stdout = original_stdout
            log(f"Error during unification: {str(e)}")
            log("--- Unification Failed ---")
            ok = False
            msg = str(e)

        # Reactivar botón en hilo principal
        root.after(0, lambda: unify_button.config(state="normal", text="Unify Files"))

        if ok:
            messagebox.showinfo("Success", f"Files unified successfully.\nFinal file: {output_file}")
        else:
            messagebox.showerror("Error", msg)

    # --- Fila 3 (Unify): Botón de Unificar --- (Llama al wrapper del thread)
    unify_button = tk.Button(frame2, text="Unify Files", command=unify_logic)
    unify_button.grid(row=3, column=1, columnspan=2, pady=10)

    # --- Panel de logs y progreso en la derecha ---
    log_frame = tk.LabelFrame(right_frame, text="Processing Log", padx=10, pady=10)
    log_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Barra de progreso encima del log
    progress_frame = tk.Frame(log_frame)
    progress_frame.pack(fill="x", padx=5, pady=5)
    tk.Label(progress_frame, textvariable=progress_text, width=30, anchor="w").pack(side=tk.LEFT, padx=5)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, length=250)
    progress_bar.pack(side=tk.LEFT, fill="x", expand=True, padx=5)

    # Log text debajo de la barra de progreso
    log_scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=log_scrollbar.set)
    log_text.pack(side=tk.LEFT, fill="both", expand=True)
    
    # Función para reiniciar el progreso
    def reset_progress():
        progress_var.set(0)
        progress_text.set("Ready")

    # Establecer estado inicial y empezar chequeo de cola de logs
    # update_filter_fields() # La UI avanzada está comentada, no es necesario llamarlo
    check_log_queue() # Iniciar el chequeo periódico de la cola de logs
    
    # --- Lógica para habilitar/deshabilitar filtros (Reactivada y Ajustada) ---
    def on_category_change(event=None):
        is_messages_category = category_var.get() == "Messages and Social Networks"
        state = "normal" if is_messages_category else "disabled"

        # Habilitar/deshabilitar botones y entradas principales de filtros/propiedades
        add_filter_btn.config(state=state)
        add_text_prop_btn.config(state=state)
        
        # Deshabilitar los widgets dentro de los frames contenedores (si existen y tienen hijos)
        if filters_container.winfo_exists():
            for widget in filters_container.winfo_children():
                try: widget.config(state=state) 
                except tk.TclError: pass
        if text_props_container.winfo_exists():
            for widget in text_props_container.winfo_children():
                try: widget.config(state=state) 
                except tk.TclError: pass

        # Habilitar/deshabilitar opciones avanzadas de JSON
        json_mode_combo.config(state=state)
        min_id_entry.config(state=state)
        max_id_entry.config(state=state)

        # Limpiar valores si se deshabilita (opcional, pero buena práctica)
        if not is_messages_category:
            json_min_id_var.set("")
            json_max_id_var.set("")

    cat_combo.bind("<<ComboboxSelected>>", on_category_change)
    on_category_change() # llamada inicial para establecer estado correcto
    
    root.mainloop()

# --- Código para ejecutar solo si es el script principal ---
if __name__ == "__main__":
    main() 

# --- Aquí empezaban las funciones movidas a converters.py y process_folder, segmentar, etc. ---

# --- Funciones de segmentación inteligente ---
# (Estas funciones (segmentar_...) y process_folder, unificar_... 
#  deberían moverse a processors.py y utils.py respectivamente)

# (Las funciones de conversión ya se movieron a converters.py)

# --- NUEVO: segmentación para libros / escritos ---------------