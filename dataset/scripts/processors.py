import json
import re
from pathlib import Path
import time
import multiprocessing
import concurrent.futures
from datetime import datetime

# Importar funciones de otros módulos locales
from converters import (
    convert_docx_to_markdown, 
    convert_docx_to_text, 
    convert_pdf_to_text,
    extract_docx_metadata
)
# Importar funciones de utils.py
from utils import (
    extraer_fecha_json, 
    extraer_fecha_md, 
    reparar_mojibake, 
    find_prop_recursive, 
    extract_text_recursive
)

# --- Funciones de procesamiento y segmentación ---

# --- Función principal para procesar una carpeta ---
def process_folder(folder, category, output_dir=None, author=None, filter_rules=None, min_chars=0,
                  text_properties=None, log_callback=None, stop_event=None, skip_salvage=False,
                  json_min_id=None, json_max_id=None, idioma=None):
    """
    Procesa todos los archivos de una carpeta según la categoría seleccionada.

    Args:
        folder: Ruta a la carpeta de entrada
        category: Categoría seleccionada ("Poems and Songs", "Messages and Social Networks", "Writings and Books")
        output_dir: Directorio de salida (opcional)
        author: Autor para añadir a los metadatos (opcional)
        filter_rules: Lista de reglas de filtrado para JSON/NDJSON
        min_chars: Mínimo de caracteres para incluir una entrada
        text_properties: Lista de propiedades para extraer texto de JSON
        log_callback: Función para log
        stop_event: Evento para detener el procesamiento
        skip_salvage: Si True, no intentar rescatar JSON corrupto
        json_min_id, json_max_id: Rango de IDs para JSON corrupto
        idioma: Código del idioma para procesar_escritos_egw

    Returns:
        Path: Ruta al último archivo procesado
    """
    # Iniciar temporizador para calcular tiempo total
    start_time = time.time()
    
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise ValueError(f"La carpeta {folder} no existe")

    # Si no se especifica directorio de salida, crear uno
    if not output_dir:
        output_dir = folder_path / "salida"
    else:
        output_dir = Path(output_dir)

    # Crear directorio de salida si no existe
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # NUEVO: Crear subcarpeta para archivos Markdown
    md_output_dir = output_dir / "md"
    md_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Para mensajes de log
    if log_callback:
        log_callback(f"--- Procesando carpeta: {folder_path} ---")
        log_callback(f"Categoría: {category}")
        log_callback(f"Directorio de salida: {output_dir}")
        log_callback(f"Markdown guardados en: {md_output_dir}")

    # Definir si se segmenta por párrafos o no según la categoría
    segmentar_por_parrafos = True # Por defecto para MD/TXT genérico
    if category == "Poems and Songs":
        segmentar_func = segmentar_poema_cancion
        if log_callback:
            log_callback("Modo: Segmentación inteligente para poemas/canciones")
    elif category == "Writings and Books":
        segmentar_func = segmentar_libro
        if log_callback:
            log_callback("Modo: Segmentación inteligente para escritos/libros")
    else:  # "Messages and Social Networks"
        segmentar_por_parrafos = False  # No segmentar, tratar JSON como está
        segmentar_func = None # No aplica función de segmentación específica
        if log_callback:
            log_callback("Modo: Procesamiento JSON para mensajes/redes")

    # Contador de archivos procesados
    total_files = 0
    processed_files = 0
    skipped_files = 0
    last_output_path = None

    # Contadores para estadísticas de JSON/NDJSON
    json_ndjson_total_entries = 0
    json_ndjson_saved_entries = 0
    json_ndjson_files_count = 0

    # Recorrer todos los archivos en la carpeta y subcarpetas
    all_files = list(folder_path.glob("**/*"))  # Incluye archivos en subcarpetas
    total_files = len([f for f in all_files if f.is_file()]) # Contar solo archivos

    if log_callback:
        log_callback(f"Total de archivos encontrados: {total_files}")

    current_file_idx = 0
    for file_path in all_files:
        # Verificar si se solicitó detener
        if stop_event and stop_event.is_set():
            if log_callback:
                log_callback("Procesamiento detenido por el usuario.")
            break

        # Solo procesar archivos, no carpetas
        if not file_path.is_file():
            continue

        current_file_idx += 1
        # Obtener extensión en minúsculas
        extension = file_path.suffix.lower()

        # --- Calcular ruta de salida preservando estructura --- 
        relative_path = file_path.relative_to(folder_path)
        # Cambiar extensión a .ndjson
        output_name = relative_path.with_suffix('.ndjson') 
        
        # Construir ruta de salida incluyendo el autor si está definido
        if author:
            # Si se proporcionó autor, crear estructura author/original_path
            author_folder = Path(author.lower().replace(" ", "_"))
            
            # Preservar la estructura completa dentro de la carpeta del autor
            # Separar el directorio padre y el nombre del archivo
            file_name = relative_path.name
            parent_dirs = str(relative_path.parent) if relative_path.parent and str(relative_path.parent) != '.' else ""
            
            # Log más detallado para depuración
            if log_callback:
                log_callback(f"  -> Path Debug: Original: {file_path}")
                log_callback(f"     Relative: {relative_path}")
                log_callback(f"     Parent dirs: {parent_dirs}")
                log_callback(f"     File name: {file_name}")
            
            # Construir la ruta completa
            if parent_dirs and parent_dirs != ".":
                # Si hay subdirectorios, preservarlos
                output_path = output_dir / author_folder / parent_dirs / file_name.replace(relative_path.suffix, '.ndjson')
            else:
                # Si no hay subdirectorios, colocar directamente en la carpeta del autor
                output_path = output_dir / author_folder / file_name.replace(relative_path.suffix, '.ndjson')
        else:
            # Construir ruta de salida sin autor
            output_path = output_dir / output_name
        
        # Crear directorios padres si no existen ANTES de intentar escribir
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # --- Fin cálculo ruta de salida ---

        # Actualizar progreso
        if log_callback:
            progress_pct = (current_file_idx / total_files) * 100 if total_files > 0 else 0
            log_callback(f"  -> Progress: {progress_pct:.1f}% (File {current_file_idx}/{total_files})", is_progress=True)
            # Usar ruta relativa en el log para claridad
            log_callback(f"Procesando: {relative_path} -> {output_path.relative_to(output_dir)}") 

        # Procesar según extensión y categoría
        try:
            # --- Procesamiento DOCX ---
            if extension == ".docx":
                if log_callback:
                    log_callback(f"  -> Detected DOCX file: {file_path.name}")

                # NUEVO: Crear un archivo Markdown permanente con la misma estructura que el de salida
                md_file_name = file_path.name.replace(file_path.suffix, '.md')
                # Extraer el directorio padre del archivo relativo
                parent_dirs = str(relative_path.parent) if relative_path.parent and str(relative_path.parent) != '.' else ""
                
                if parent_dirs:
                    md_path = md_output_dir / parent_dirs / md_file_name
                    md_path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    md_path = md_output_dir / md_file_name
                
                # Convertir DOCX a Markdown usando Pandoc
                ok, msg = convert_docx_to_markdown(file_path, md_path, log_callback)

                if ok:
                    # Extraer metadatos (incluyendo fecha) del DOCX original
                    docx_metadata = extract_docx_metadata(file_path)
                    fecha_docx = ""
                    if isinstance(docx_metadata, dict) and "error" not in docx_metadata:
                        # SOLO usar fecha de creación original, sin fallbacks
                        fecha_docx = docx_metadata.get("fecha_creacion", "")
                        if log_callback and fecha_docx:
                            log_callback(f"  -> Extracted original creation date from DOCX: {fecha_docx}")
                    
                    # Si la conversión fue exitosa, procesar el Markdown
                    if category in ("Poems and Songs", "Writings and Books"):
                        # Leer el MD generado
                        try:
                            with open(md_path, "r", encoding="utf-8") as md_file:
                                md_content = md_file.read()
                        except Exception as e:
                            if log_callback: log_callback(f"  -> ERROR reading Markdown: {e}")
                            skipped_files += 1
                            continue # Saltar al siguiente archivo

                        # Segmentar según la categoría usando la función correspondiente
                        segments = segmentar_func(md_content)

                        # Escribir los segmentos al NDJSON de salida
                        try:
                            with open(output_path, "w", encoding="utf-8") as out_file:
                                for s_idx, segment in enumerate(segments, 1):
                                    # Extraer fecha del MD, si no está disponible usar la del DOCX
                                    fecha_md = extraer_fecha_md(md_content)
                                    fecha_final = fecha_md or fecha_docx or ""
                                    
                                    entry = {
                                        "id": s_idx,
                                        "contenido_texto": segment,
                                        "fecha": fecha_final,
                                        "fuente": category,
                                        "contexto": str(file_path), # Contexto es el DOCX original
                                        "md_source": str(md_path),  # Referencia al archivo MD
                                        "autor": author or (docx_metadata.get("autor") if isinstance(docx_metadata, dict) else "")
                                    }
                                    # Filtrar por longitud mínima ANTES de escribir
                                    if min_chars > 0 and len(segment) < min_chars:
                                        continue
                                    out_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                                    
                                if log_callback:
                                    log_callback(f"  -> Processed DOCX via Markdown: {len(segments)} segments extracted to {output_path.name}")
                                    log_callback(f"  -> Markdown file saved: {md_path.relative_to(md_output_dir)}")
                                processed_files += 1
                                last_output_path = output_path
                        except Exception as e:
                            if log_callback: log_callback(f"  -> ERROR writing NDJSON for DOCX: {e}")
                            skipped_files += 1

                    else:
                        # Si es "Messages and Social Networks", no lo procesamos (no aplica para docx)
                        if log_callback:
                            log_callback(f"  -> Skipped DOCX: Category {category} not applicable for DOCX files")
                        skipped_files += 1

                else:
                    # Fallback si Pandoc falló
                    if log_callback:
                        log_callback(f"  -> Pandoc failed for {file_path.name}. Attempting fallback: {msg}")
                    # (Aquí podrías añadir lógica para usar convert_docx_to_text si quieres un fallback)
                    skipped_files += 1

            # --- Procesamiento MD/TXT ---
            elif extension in (".md", ".txt"):
                if log_callback:
                    log_callback(f"  -> Detected {extension.upper()} file: {file_path.name}")
                try:
                    if category == "escritos_egw":
                        # Usar el idioma pasado explícitamente
                        idioma_egw = idioma or "es"
                        entries = procesar_escritos_egw(str(file_path), idioma_egw)
                        if entries:
                            with open(output_path, "w", encoding="utf-8") as out_file:
                                for s_idx, entry in enumerate(entries, 1):
                                    entry["id"] = s_idx
                                    json.dump(entry, out_file, ensure_ascii=False)
                                    out_file.write("\n")
                            if log_callback:
                                log_callback(f"  -> Processed EGW TXT: {len(entries)} entries extracted to {output_path.name}")
                            processed_files += 1
                            last_output_path = output_path
                        else:
                            if log_callback:
                                log_callback(f"  -> No valid entries found in EGW TXT: {file_path.name}")
                            skipped_files += 1
                        continue  # Saltar el resto del procesamiento para este archivo
                    # ... resto del procesamiento estándar para MD/TXT ...
                    with open(file_path, "r", encoding="utf-8") as text_file:
                        text_content = text_file.read()
                except Exception as e:
                    if log_callback: log_callback(f"  -> ERROR reading {extension} file: {e}")
                    skipped_files += 1
                    continue

                if category in ("Poems and Songs", "Writings and Books"):
                    # Segmentar según la categoría
                    segments = segmentar_func(text_content)
                    # Escribir los segmentos al NDJSON de salida
                    try:
                        with open(output_path, "w", encoding="utf-8") as out_file:
                            for s_idx, segment in enumerate(segments, 1):
                                entry = {
                                    "id": s_idx,
                                    "contenido_texto": segment,
                                    "fecha": extraer_fecha_md(text_content),
                                    "fuente": category,
                                    "contexto": str(file_path),
                                    "autor": author or ""
                                }
                                # Filtrar por longitud mínima ANTES de escribir
                                if min_chars > 0 and len(segment) < min_chars:
                                    continue
                                out_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        if log_callback:
                            log_callback(f"  -> Processed {extension.upper()} file: {len(segments)} segments extracted to {output_path.name}")
                        processed_files += 1
                        last_output_path = output_path
                    except Exception as e:
                        if log_callback: log_callback(f"  -> ERROR writing NDJSON for {extension.upper()}: {e}")
                        skipped_files += 1
                else:
                    # Para "Messages and Social Networks", tratar MD/TXT como un solo bloque
                    try:
                        with open(output_path, "w", encoding="utf-8") as out_file:
                            entry = {
                                "id": 1,
                                "contenido_texto": text_content,
                                "fecha": extraer_fecha_md(text_content),
                                "fuente": category,
                                "contexto": str(file_path),
                                "autor": author or ""
                            }
                            if min_chars > 0 and len(text_content) < min_chars:
                                if log_callback: log_callback(f"  -> Skipped {extension.upper()}: Content too short ({len(text_content)} < {min_chars} chars)")
                                skipped_files += 1
                            else:
                                out_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                                if log_callback:
                                    log_callback(f"  -> Processed {extension.upper()} file as single entry to {output_path.name}")
                                processed_files += 1
                                last_output_path = output_path
                    except Exception as e:
                         if log_callback: log_callback(f"  -> ERROR writing NDJSON for {extension.upper()} (single entry): {e}")
                         skipped_files += 1

            # --- Procesamiento JSON/NDJSON ---
            elif extension in (".json", ".ndjson") and category == "Messages and Social Networks":
                json_ndjson_files_count += 1
                if log_callback:
                    log_callback(f"  -> Detected {extension.upper()} file: {file_path.name}")

                # Obtener reglas de filtrado (simplificado a la primera regla por ahora)
                filter_mode = None
                filter_prop = None
                filter_value = None
                if filter_rules and len(filter_rules) > 0:
                    rule = filter_rules[0]
                    filter_mode = rule.get('mode')
                    filter_prop = rule.get('property')
                    filter_value = rule.get('value')

                # Determinar si es JSON o NDJSON e invocar la función correcta
                is_ndjson = extension == ".ndjson"
                if is_ndjson:
                    ok, msg, filtered_prop, filtered_short = procesar_ndjson(
                        file_path, output_path, category, autor=author,
                        filter_mode=filter_mode, filter_prop=filter_prop, filter_value=filter_value,
                        min_chars=min_chars, text_prop=text_properties, stop_event=stop_event
                    )
                else: # Es JSON
                    ok, msg, filtered_prop, filtered_short = procesar_json_completo(
                        file_path, output_path, category, autor=author,
                        filter_mode=filter_mode, filter_prop=filter_prop, filter_value=filter_value,
                        min_chars=min_chars, text_prop=text_properties, stop_event=stop_event,
                        skip_salvage=skip_salvage, json_min_id=json_min_id, json_max_id=json_max_id,
                        log_callback=log_callback # Pasar log_callback a salvage
                    )
                
                # Actualizar contadores para estadísticas
                if "saved to" in msg:
                    try:
                        parts = msg.split(": ")[1].split(" ")[0].split("/")
                        if len(parts) == 2:
                            saved = int(parts[0])
                            total = int(parts[1])
                            json_ndjson_saved_entries += saved
                            json_ndjson_total_entries += total
                    except:
                        pass # Si falla el parsing del mensaje, no actualizamos contadores
                
                if ok:
                    processed_files += 1
                    last_output_path = output_path
                    if log_callback:
                        log_callback(f"  -> {msg}")
                else:
                    skipped_files += 1
                    if log_callback:
                        log_callback(f"  -> {msg}")

            # --- Procesamiento PDF ---
            elif extension == ".pdf":
                if log_callback:
                    log_callback(f"  -> Detected PDF file: {file_path.name}")

                texto = convert_pdf_to_text(file_path)
                if texto.startswith("ERROR:"):
                    if log_callback:
                        log_callback(f"  -> Error converting PDF: {texto}")
                    skipped_files += 1
                    continue

                # Procesar el texto extraído según la categoría
                if category in ("Poems and Songs", "Writings and Books"):
                    segments = segmentar_func(texto)
                    try:
                        with open(output_path, "w", encoding="utf-8") as out_file:
                             for s_idx, segment in enumerate(segments, 1):
                                entry = {
                                    "id": s_idx,
                                    "contenido_texto": segment,
                                    "fecha": "", # PDF no tiene fecha estándar fácil de extraer
                                    "fuente": category,
                                    "contexto": str(file_path),
                                    "autor": author or ""
                                }
                                if min_chars > 0 and len(segment) < min_chars:
                                    continue
                                out_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        if log_callback:
                             log_callback(f"  -> Processed PDF: {len(segments)} segments extracted to {output_path.name}")
                        processed_files += 1
                        last_output_path = output_path
                    except Exception as e:
                        if log_callback: log_callback(f"  -> ERROR writing NDJSON for PDF: {e}")
                        skipped_files += 1
                else:
                    # Tratar PDF como bloque único para otras categorías
                     try:
                        with open(output_path, "w", encoding="utf-8") as out_file:
                            entry = {
                                "id": 1,
                                "contenido_texto": texto,
                                "fecha": "",
                                "fuente": category,
                                "contexto": str(file_path),
                                "autor": author or ""
                            }
                            if min_chars > 0 and len(texto) < min_chars:
                                if log_callback: log_callback(f"  -> Skipped PDF: Content too short ({len(texto)} < {min_chars} chars)")
                                skipped_files += 1
                            else:
                                out_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                                if log_callback:
                                     log_callback(f"  -> Processed PDF as single entry to {output_path.name}")
                                processed_files += 1
                                last_output_path = output_path
                     except Exception as e:
                         if log_callback: log_callback(f"  -> ERROR writing NDJSON for PDF (single entry): {e}")
                         skipped_files += 1

            # --- Otros formatos no soportados --- 
            else:
                if log_callback:
                    log_callback(f"  -> Skipped: {file_path.name} (Unsupported format: {extension})")
                skipped_files += 1

        except Exception as e:
            if log_callback:
                log_callback(f"  -> UNEXPECTED ERROR processing {file_path.name}: {str(e)}")
            skipped_files += 1

    # Resumen final
    if log_callback:
        log_callback(f"--- PROCESSING SUMMARY ---")
        log_callback(f"Output folder: {output_dir}")
        log_callback(f"Total files found: {total_files}")
        log_callback(f"• Processed successfully: {processed_files}")
        log_callback(f"• Skipped (unsupported/error): {skipped_files}")
        log_callback(f"File types encountered:")
        log_callback(f"• JSON/NDJSON: {json_ndjson_files_count}")
        log_callback(f"• Markdown: {len([f for f in all_files if f.is_file() and f.suffix.lower() in ('.md', '.txt')])}")
        log_callback(f"• Text: {len([f for f in all_files if f.is_file() and f.suffix.lower() == '.txt'])}")
        log_callback(f"• Unsupported: {total_files - processed_files - skipped_files}")
        
        # Añadir estadísticas de JSON/NDJSON solo si hay archivos de ese tipo
        if json_ndjson_files_count > 0:
            log_callback(f"Entry Summary (JSON/NDJSON files):")
            log_callback(f"• Total original entries found: {json_ndjson_total_entries}")
            log_callback(f"• Total entries saved: {json_ndjson_saved_entries}")
            
        # Duración total
        total_time = int(time.time() - start_time) if 'start_time' in locals() else 0
        minutes = total_time // 60
        seconds = total_time % 60
        log_callback(f"Total processing time: {minutes} min {seconds} sec")

    return last_output_path

# --- Funciones para segmentación inteligente ---
def segmentar_poema_cancion(texto):
    """
    Segmenta poemas o canciones completos agrupando versos y estrofas.
    Detecta patrones específicos como:
    - Títulos con formato '# "Título"'
    - Versos cortos (menos de 135 caracteres)
    - Agrupa todos los versos hasta encontrar otro título o final
    """
    if not texto:
        return []

    # Preprocesar: quitar espacios y normalizar saltos
    texto = texto.strip().replace('\r\n', '\n').replace('\r', '\n')
    
    # Caso especial: detectar patrón específico de títulos con '#' (formato Markdown)
    title_pattern = re.compile(r'#\s+"[^"]+"|#\s+\S.*$', re.MULTILINE)
    if title_pattern.search(texto):
        # Si detectamos este patrón, usar lógica específica para títulos Markdown
        poemas = []
        # Dividir el texto por líneas que parezcan títulos
        sections = title_pattern.split(texto)
        titles = title_pattern.findall(texto)
        
        # Si hay más títulos que secciones, ajustar
        if len(titles) > len(sections)-1:
            titles = titles[:len(sections)-1]
        
        # Primera sección puede ser texto antes del primer título - ignorarla si está vacía
        if sections[0].strip():
            poemas.append(sections[0].strip())
            
        # Para cada título y su contenido, crear un poema
        for i, title in enumerate(titles):
            if i+1 < len(sections):
                content = sections[i+1].strip()
                if content:
                    poemas.append(f"{title}\n{content}")
                else:
                    poemas.append(title.strip())  # Solo título si no hay contenido
                    
        if poemas:
            return poemas
    
    # Si no encontramos patrón de títulos Markdown o no hay poemas, usar la lógica original
    lineas = texto.split('\n')
    poemas = []
    actual = []
    versos_cortos = 0
    dentro_poema = False
    titulo = None
    i = 0
    
    while i < len(lineas):
        linea = lineas[i].strip()
        # Saltar líneas vacías
        if not linea:
            if dentro_poema and actual:
                actual.append('')  # Mantener estrofas (doble salto)
            i += 1
            continue
            
        # Detectar posible título (línea corta)
        if not dentro_poema and len(linea) <= 50 and (i+1 < len(lineas)):
            # Verificar si parece un título (primera letra mayúscula, comillas, etc.)
            if (linea.startswith('"') or linea.startswith('#') or 
                linea[0].isupper() or linea.isupper()):
                posible_titulo = linea
                # Verificar si las siguientes líneas son versos
                versos_test = 0
                for j in range(i+1, min(i+4, len(lineas))):
                    if lineas[j].strip() and len(lineas[j].strip()) < 135:
                        versos_test += 1
                if versos_test >= 1:  # Solo necesitamos un verso después del título
                    titulo = posible_titulo
                    i += 1
                    continue
                    
        # Detectar inicio de poema/canción (3 versos cortos seguidos)
        if not dentro_poema:
            # Mirar adelante para detectar 3 versos cortos seguidos
            versos_cortos = 0
            for j in range(i, min(i+4, len(lineas))):
                if lineas[j].strip() and len(lineas[j].strip()) < 135:
                    versos_cortos += 1
                else:
                    break
                    
            # Si encontramos al menos 2 versos cortos seguidos, empezar un poema
            if versos_cortos >= 2:
                dentro_poema = True
                if titulo:
                    actual.append(titulo)
                    titulo = None
                # Añadir los versos iniciales
                for k in range(i, i+versos_cortos):
                    actual.append(lineas[k].strip())
                i += versos_cortos
                continue
                
        # Si estamos dentro de un poema/canción
        if dentro_poema:
            # Terminar si encontramos:
            # 1. Un párrafo largo (>135 caracteres), o
            # 2. Un patrón que parece un título para el siguiente poema
            es_titulo_siguiente = False
            if (linea.startswith('#') or linea.startswith('"')) and len(linea) < 50:
                es_titulo_siguiente = True
                
            if len(linea) >= 135 or es_titulo_siguiente:
                # Guardar el poema actual
                if actual:
                    poemas.append('\n'.join(actual).strip())
                actual = []
                dentro_poema = False
                
                # Si es un título, guardarlo para el siguiente poema
                if es_titulo_siguiente:
                    titulo = linea
                    i += 1
                    continue
            else:
                # Es un verso normal, añadirlo al poema actual
                actual.append(linea)
        # Si no estamos en un poema y la línea no es un título, añadirla como texto normal
        elif linea and not (linea.startswith('#') or (linea.startswith('"') and len(linea) < 50)):
            poemas.append(linea)
            
        i += 1
        
    # Guardar el último poema si quedó algo
    if dentro_poema and actual:
        poemas.append('\n'.join(actual).strip())
        
    # Si no se encontró ningún poema con la lógica avanzada, volver al comportamiento original
    if not poemas:
        # Dividir por líneas vacías (estrofas)
        estrofas = re.split(r'\n\s*\n', texto)
        # Filtrar estrofas vacías y aplicar strip a cada una
        poemas = [e.strip() for e in estrofas if e.strip()]
        
    return poemas

def segmentar_libro(texto):
    """
    Segmenta un libro o escrito en secciones lógicas, utilizando formatos Markdown.
    Detecta patrones específicos:
    - Títulos: líneas cortas (≤80 caracteres) con formato (# ## etc.)
    - Capítulos: título seguido de párrafos largos (>180 caracteres)
    - Agrupa párrafos bajo el mismo título/capítulo
    """
    if not texto:
        return []

    # Preprocesar: quitar espacios y normalizar saltos
    texto = texto.strip().replace('\r\n', '\n').replace('\r', '\n')
    
    # Detectar formato Markdown (encabezados)
    title_pattern = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)
    has_md_titles = title_pattern.search(texto)
    
    if has_md_titles:
        # Segmentación basada en encabezados Markdown
        segmentos = []
        lineas = texto.split('\n')
        
        # Variables para el seguimiento
        capitulo_actual = None
        contenido_actual = []
        titulo_libro = None
        titulo_nivel = 0
        
        for i, linea in enumerate(lineas):
            # Detectar si es un encabezado 
            encabezado_match = re.match(r'^(#{1,6})\s+(.+)$', linea)
            
            if encabezado_match:
                # Si ya teníamos contenido acumulado, guardarlo
                if capitulo_actual and contenido_actual:
                    contenido_unido = '\n\n'.join(contenido_actual)
                    texto_capitulo = f"{capitulo_actual}\n\n{contenido_unido}"
                    segmentos.append(texto_capitulo.strip())
                    contenido_actual = []
                
                # Extraer nivel de encabezado y texto
                nivel = len(encabezado_match.group(1))  # Cantidad de #
                texto_titulo = encabezado_match.group(2).strip()
                
                # Si es el primer título o un título de nivel superior, puede ser título del libro
                if titulo_libro is None or nivel < titulo_nivel:
                    titulo_libro = texto_titulo
                    titulo_nivel = nivel
                    capitulo_actual = linea
                else:
                    # Es un capítulo o sección
                    capitulo_actual = linea
            
            # Si no es encabezado y tenemos un capítulo activo, añadir al contenido
            elif capitulo_actual and linea.strip():
                contenido_actual.append(linea.strip())
            
            # Línea en blanco dentro de un capítulo
            elif capitulo_actual and not linea.strip() and contenido_actual:
                # Mantener formato de párrafos
                if contenido_actual[-1]:  # Si última línea no es vacía
                    contenido_actual.append('')  # Añadir línea vacía para respetar formato
        
        # No olvidar el último capítulo
        if capitulo_actual and contenido_actual:
            contenido_unido = '\n\n'.join(contenido_actual)
            texto_capitulo = f"{capitulo_actual}\n\n{contenido_unido}"
            segmentos.append(texto_capitulo.strip())
            
        # Si encontramos segmentos, devolverlos
        if segmentos:
            return segmentos
    
    # Si no encontramos encabezados Markdown o preferimos una segmentación diferente
    # Intentar segmentar por patrones de texto (línea corta seguida de párrafo largo)
    lineas = texto.split('\n')
    segmentos = []
    i = 0
    
    # Parámetros para detección
    MAX_TITULO_LONGITUD = 80  # Caracteres máximos para un título
    MIN_PARRAFO_LONGITUD = 180  # Caracteres mínimos para un párrafo
    
    while i < len(lineas):
        linea = lineas[i].strip()
        
        # Buscar patrón de título (línea corta) seguido de párrafo (línea larga)
        if len(linea) <= MAX_TITULO_LONGITUD and linea:
            # Mirar adelante para buscar un párrafo largo
            j = i + 1
            while j < len(lineas) and not lineas[j].strip():
                j += 1  # Saltar líneas vacías
                
            if j < len(lineas) and len(lineas[j].strip()) >= MIN_PARRAFO_LONGITUD:
                # Encontramos un título seguido de párrafo largo
                titulo = linea
                parrafos = []
                parrafos.append(lineas[j].strip())
                
                # Seguir hasta encontrar otro posible título o fin
                k = j + 1
                while k < len(lineas):
                    # Saltar líneas vacías, pero preservar formato
                    if not lineas[k].strip():
                        if parrafos and parrafos[-1]:  # Si último párrafo no es vacío
                            parrafos.append('')  # Añadir marcador de párrafo
                        k += 1
                        continue
                        
                    # Si parece otro título (línea corta), terminar este capítulo
                    if len(lineas[k].strip()) <= MAX_TITULO_LONGITUD:
                        # Verificar si es seguido por párrafo (mirando adelante)
                        next_is_title = False
                        for m in range(k+1, min(k+4, len(lineas))):
                            if lineas[m].strip() and len(lineas[m].strip()) >= MIN_PARRAFO_LONGITUD:
                                next_is_title = True
                                break
                                
                        if next_is_title:
                            break  # Encontramos el siguiente capítulo
                            
                    # Añadir línea como parte del párrafo actual
                    parrafos.append(lineas[k].strip())
                    k += 1
                
                # Guardar capítulo completo
                parrafos_unidos = '\n\n'.join(p for p in parrafos if p)
                capitulo = f"{titulo}\n\n{parrafos_unidos}"
                segmentos.append(capitulo.strip())
                
                # Actualizar índice para continuar desde donde terminamos
                i = k
                continue  # Seguir buscando más capítulos
        
        # Si no encontramos patrón de título, avanzar
        i += 1
    
    # Si no se detectaron capítulos con la lógica de título-párrafo, 
    # caer de nuevo a segmentación por párrafos (comportamiento original)
    if not segmentos:
        # Detectar encabezados Markdown (# Título, ## Subtítulo, etc.)
        # y crear segmentos basados en ellos
        lineas = texto.split('\n')

        # Detectar si hay encabezados markdown
        tiene_headers = False
        for linea in lineas:
            if re.match(r'^#{1,6}\s+\w+', linea):
                tiene_headers = True
                break

        if tiene_headers:
            # Si hay encabezados, segmentar por ellos
            segmento_actual = []
            for linea in lineas:
                # Si es un encabezado y ya tenemos contenido, guardamos el segmento anterior
                if re.match(r'^#{1,6}\s+\w+', linea) and segmento_actual:
                    segmentos.append('\n'.join(segmento_actual))
                    segmento_actual = [linea]
                else:
                    segmento_actual.append(linea)

            # No olvidar el último segmento
            if segmento_actual:
                segmentos.append('\n'.join(segmento_actual))
        else:
            # Si no hay encabezados, dividir por párrafos pero unir párrafos cortos
            parrafos = [p.strip() for p in re.split(r'\n\s*\n', texto) if p.strip()]

            # Detectar si es probable que sea un libro con párrafos largos
            es_libro = False
            umbral_parrafo_largo = 500 # Ajustable
            umbral_union = 200 # Ajustable: párrafos más cortos que esto se unen
            limite_segmento = 1000 # Ajustable: Límite de caracteres para agrupar párrafos cortos

            for p in parrafos:
                if len(p) > umbral_parrafo_largo:
                    es_libro = True
                    break

            if es_libro:
                # Para libros, cada párrafo largo es un segmento
                segmento_actual = []
                for p in parrafos:
                    if len(p) > umbral_union:
                        if segmento_actual:
                            segmentos.append('\n\n'.join(segmento_actual))
                            segmento_actual = []
                        segmentos.append(p)
                    else:
                        segmento_actual.append(p)

                # No olvidar el último grupo de párrafos cortos
                if segmento_actual:
                    segmentos.append('\n\n'.join(segmento_actual))
            else:
                # Para textos cortos, agrupar más agresivamente
                segmento_actual = []
                longitud_actual = 0

                for p in parrafos:
                    # Si añadir el párrafo excede el límite, guardar segmento anterior
                    if segmento_actual and longitud_actual + len(p) > limite_segmento:
                        segmentos.append('\n\n'.join(segmento_actual))
                        segmento_actual = [p]
                        longitud_actual = len(p)
                    else:
                        segmento_actual.append(p)
                        longitud_actual += len(p)

                # No olvidar el último segmento
                if segmento_actual:
                    segmentos.append('\n\n'.join(segmento_actual))

    # Si no se generaron segmentos, devolver el texto completo como único segmento
    if not segmentos and texto:
        segmentos = [texto]

    return segmentos

# --- Funciones para procesar JSON/NDJSON --- 

def process_single_json_entry(obj, fuente, contexto_file, autor=None, filter_mode=None, filter_prop=None, filter_value=None, min_chars=0, text_prop=None):
    """Procesa un único objeto JSON (dict). Aplica filtros y devuelve el objeto estandarizado o None.
    Devuelve: (objeto_estandarizado | None, fue_filtrado_prop, fue_filtrado_corto)
    """
    fue_filtrado_prop = False
    fue_filtrado_corto = False
    try:
        fecha = extraer_fecha_json(obj)
        contenido_texto_extraido = ""
        text_properties = text_prop if isinstance(text_prop, (list, tuple)) else ([text_prop] if text_prop else [])

        if text_properties:
            for prop in text_properties:
                contenido_texto_tmp = extract_text_recursive(obj, prop)
                if contenido_texto_tmp:
                    contenido_texto_extraido = contenido_texto_tmp
                    break
        else:
            # Si no hay text_prop, intentar convertir el objeto entero a string
            try:
                contenido_texto_extraido = json.dumps(obj, ensure_ascii=False)
            except:
                contenido_texto_extraido = str(obj)

        if not isinstance(contenido_texto_extraido, str):
            contenido_texto_extraido = str(contenido_texto_extraido)
        contenido_texto_extraido = contenido_texto_extraido.strip()
        contenido_texto_extraido = reparar_mojibake(contenido_texto_extraido)

        # Filtrar por propiedad
        if filter_mode and filter_prop and filter_mode != "No filter":
            prop_found = find_prop_recursive(obj, filter_prop, filter_value)
            if (filter_mode == "Keep entries with property" and not prop_found) or \
               (filter_mode == "Remove entries with property" and prop_found):
                fue_filtrado_prop = True
                return None, fue_filtrado_prop, fue_filtrado_corto

        # Filtrar por longitud
        if min_chars > 0 and len(contenido_texto_extraido) < min_chars:
            fue_filtrado_corto = True
            return None, fue_filtrado_prop, fue_filtrado_corto

        entrada = {
            "contenido_texto": contenido_texto_extraido,
            "fecha": fecha,
            "fuente": fuente,
            "contexto": str(contexto_file),
            "autor": autor or ""
        }
        return entrada, fue_filtrado_prop, fue_filtrado_corto

    except Exception as e:
        print(f"Error procesando entrada JSON: {e}")
        return None, False, False

def procesar_ndjson(archivo_ndjson, archivo_salida, fuente, autor=None, filter_mode=None, filter_prop=None, filter_value=None, min_chars=0, text_prop=None, stop_event=None):
    """Procesa un archivo NDJSON línea por línea."""
    entradas_originales = 0
    entradas_validas = []
    entradas_filtradas_prop_count = 0
    entradas_cortas_count = 0
    try:
        with open(archivo_ndjson, "r", encoding="utf-8") as infile:
            for line in infile:
                if stop_event and stop_event.is_set(): break
                entradas_originales += 1
                try:
                    obj = json.loads(line)
                    entrada_procesada, prop_f, short_f = process_single_json_entry(
                        obj, fuente, archivo_ndjson, autor, filter_mode, filter_prop, filter_value, min_chars, text_prop
                    )
                    if entrada_procesada:
                        entradas_validas.append(entrada_procesada)
                    else:
                        if prop_f: entradas_filtradas_prop_count += 1
                        if short_f: entradas_cortas_count += 1
                except json.JSONDecodeError: continue
                except Exception: continue

        if stop_event and stop_event.is_set():
            return False, "Processing stopped by user", 0, 0

        with open(archivo_salida, "w", encoding="utf-8") as outfile:
            for idx, entrada in enumerate(entradas_validas, 1):
                entrada["id"] = idx
                outfile.write(json.dumps(entrada, ensure_ascii=False) + "\n")

        msg = f"Processed NDJSON {archivo_ndjson.name}: {len(entradas_validas)}/{entradas_originales} entries saved to {archivo_salida.name}"
        # Añadir resumen de filtros si aplica
        # ... (código de resumen omitido por brevedad, similar al original)
        return True, msg, entradas_filtradas_prop_count, entradas_cortas_count

    except Exception as e:
        return False, f"Error processing NDJSON {archivo_ndjson.name}: {str(e)}", 0, 0

def procesar_json_completo(archivo_json, archivo_salida, fuente, autor=None, filter_mode=None, filter_prop=None, filter_value=None, min_chars=0, text_prop=None, stop_event=None, skip_salvage=False, json_min_id=None, json_max_id=None, log_callback=None):
    """Procesa un archivo JSON que contiene una lista de objetos (posiblemente en 'messages')."""
    entradas_originales = 0
    entradas_validas = []
    entradas_filtradas_prop_count = 0
    entradas_cortas_count = 0
    processed_ok = False
    msg = f"Processing JSON {archivo_json.name}"

    try:
        # Intentar parseo normal primero
        if not skip_salvage:
            try:
                with open(archivo_json, "r", encoding="utf-8") as infile:
                    data = json.load(infile)

                # Determinar si los datos son una lista o un dict con una lista (ej. "messages")
                lista_objetos = []
                if isinstance(data, list):
                    lista_objetos = data
                    if log_callback: log_callback(f"  -> Detected as JSON array format ({len(lista_objetos)} items)")
                elif isinstance(data, dict):
                    # Buscar claves comunes que contengan listas
                    keys_to_check = ["messages", "entries", "records", "data", "comments_v2"]
                    for key in keys_to_check:
                        if key in data and isinstance(data[key], list):
                            lista_objetos = data[key]
                            if log_callback: log_callback(f"  -> Found list in key: '{key}' ({len(lista_objetos)} items)")
                            break # Usar la primera lista encontrada
                    # Si no se encontró una lista conocida, y el dict solo tiene UNA clave y su valor es una lista, usarla
                    if not lista_objetos and len(data) == 1:
                         first_key = list(data.keys())[0]
                         if isinstance(data[first_key], list):
                              lista_objetos = data[first_key]
                              if log_callback: log_callback(f"  -> Found list in single key: '{first_key}' ({len(lista_objetos)} items)")
                              
                    # Si AÚN no se encontró una lista, tratar el dict como objeto único
                    if not lista_objetos: 
                         if log_callback: log_callback(f"  -> No known list key found, treating top-level object as single entry.")
                         lista_objetos = [data]
                else:
                    # Si no es lista ni diccionario, tratar como objeto único
                     if log_callback: log_callback(f"  -> Input is not list or dict, treating as single entry.")
                     lista_objetos = [data]

                entradas_originales = len(lista_objetos)
                if log_callback: log_callback(f"  -> Detected as Standard JSON format (processing {entradas_originales} entries)")
                
                for obj in lista_objetos:
                    if stop_event and stop_event.is_set(): break
                    entrada_procesada, prop_f, short_f = process_single_json_entry(
                        obj, fuente, archivo_json, autor, filter_mode, filter_prop, filter_value, min_chars, text_prop
                    )
                    if entrada_procesada:
                        entradas_validas.append(entrada_procesada)
                    else:
                        if prop_f: entradas_filtradas_prop_count += 1
                        if short_f: entradas_cortas_count += 1
                processed_ok = True # Si llegamos aquí, el parseo normal funcionó

            except json.JSONDecodeError as e:
                if log_callback: log_callback(f"  -> JSONDecodeError: {e}. Attempting salvage...")
                processed_ok = False # Marcar para intentar salvage
            except Exception as e:
                 if log_callback: log_callback(f"  -> Error reading/parsing JSON {archivo_json.name}: {e}. Attempting salvage...")
                 processed_ok = False

        # Si el parseo normal falló o se omitió, intentar salvage
        if not processed_ok:
            if log_callback: log_callback(f"  -> Starting salvage process for {archivo_json.name}")
            try:
                with open(archivo_json, "r", encoding="utf-8") as infile:
                    raw_text = infile.read()
                lista_objetos = salvage_messages_from_corrupt_json_list(
                    raw_text, log_callback, json_min_id, json_max_id, stop_event
                )
                entradas_originales = len(lista_objetos) # Actualizar contador
                if log_callback: log_callback(f"  -> Salvage found {entradas_originales} potential entries")
                
                for obj in lista_objetos:
                     if stop_event and stop_event.is_set(): break
                     # Re-aplicar filtros al procesar objetos rescatados
                     entrada_procesada, prop_f, short_f = process_single_json_entry(
                         obj, fuente, archivo_json, autor, filter_mode, filter_prop, filter_value, min_chars, text_prop
                     )
                     if entrada_procesada:
                         entradas_validas.append(entrada_procesada)
                     else:
                         if prop_f: entradas_filtradas_prop_count += 1
                         if short_f: entradas_cortas_count += 1
                processed_ok = True # Salvage completado (puede no haber encontrado nada)
            except Exception as e:
                 if log_callback: log_callback(f"  -> Salvage failed for {archivo_json.name}: {e}")
                 processed_ok = False
                 msg = f"Failed to process JSON {archivo_json.name}: Salvage error: {e}"

        # Escribir resultados si el procesamiento (normal o salvage) fue ok
        if processed_ok:
            if stop_event and stop_event.is_set():
                return False, "Processing stopped by user during JSON processing", 0, 0

            with open(archivo_salida, "w", encoding="utf-8") as outfile:
                for idx, entrada in enumerate(entradas_validas, 1):
                    entrada["id"] = idx
                    outfile.write(json.dumps(entrada, ensure_ascii=False) + "\n")

            # Resumen detallado
            filtros_info = ""
            if entradas_filtradas_prop_count > 0:
                filtros_info += f" ({entradas_filtradas_prop_count} filtered by properties)"
            if entradas_cortas_count > 0:
                filtros_info += f" ({entradas_cortas_count} too short)"
            
            if not skip_salvage:
                msg = f"{'Salvaged' if not processed_ok else 'Processed'} JSON {archivo_json.name}: {len(entradas_validas)}/{entradas_originales} entries saved to {archivo_salida.name}{filtros_info}"
            else:
                msg = f"Processed JSON {archivo_json.name}: {len(entradas_validas)}/{entradas_originales} entries saved to {archivo_salida.name}{filtros_info}"
            
            # Log detallado
            if log_callback:
                log_callback(f"  -> OK: {'Salvaged' if not processed_ok else 'Processed'} JSON {archivo_json.name}: {len(entradas_validas)}/{entradas_originales} entries saved to {archivo_salida.name}")
                if entradas_filtradas_prop_count > 0 or entradas_cortas_count > 0:
                    log_callback(f"  -> Entries filtered out: {entradas_filtradas_prop_count + entradas_cortas_count} total")
                    if entradas_filtradas_prop_count > 0:
                        log_callback(f"     - {entradas_filtradas_prop_count} by property filter")
                    if entradas_cortas_count > 0:
                        log_callback(f"     - {entradas_cortas_count} too short (< {min_chars} chars)")
            
            return True, msg, entradas_filtradas_prop_count, entradas_cortas_count
        else:
            # Si ni el parseo normal ni el salvage funcionaron
            return False, msg, 0, 0

    except Exception as e:
        return False, f"Unexpected error processing JSON {archivo_json.name}: {str(e)}", 0, 0

# --- Función de Salvamento (Corregida para usar la implementación de app_depuracion_tk.py) ---
def salvage_messages_from_corrupt_json_list(texto_raw, log_callback=None, min_id=None, max_id=None, stop_event=None):
    """Intenta extraer objetos JSON dentro de la lista 'messages' incluso si el JSON global está corrupto."""
    msgs = []

    if log_callback:
        log_callback(f"  -> Starting JSON salvage...")
        if min_id is not None or max_id is not None:
            log_callback(f"  -> Salvaging with ID range: {min_id or 'START'} to {max_id or 'END'}")

    total_size_mb = len(texto_raw) / (1024 * 1024)
    if log_callback:
        log_callback(f"  -> Total JSON size: {total_size_mb:.1f}MB")

    CHUNK_SIZE = 50 * 1024 * 1024
    if len(texto_raw) <= CHUNK_SIZE:
        return process_json_chunk(texto_raw, 0, log_callback, min_id, max_id, stop_event)
    else:
        num_chunks = (len(texto_raw) + CHUNK_SIZE - 1) // CHUNK_SIZE
        if log_callback:
            log_callback(f"  -> File will be processed in {num_chunks} chunks of {CHUNK_SIZE/(1024*1024):.1f}MB each")
            log_callback(f"  -> Progress: 0.0% (0 objects found)", is_progress=True)

        if stop_event and stop_event.is_set():
            if log_callback: log_callback(f"  -> Processing stopped by user before starting chunks")
            return []
            
        # --- Encontrar estructura principal (similar a app_depuracion_tk.py) ---
        start_idx = -1
        messages_key = '"messages"'
        key_pos = texto_raw.find(messages_key, 0, 5000)
        if key_pos != -1:
             start_idx = texto_raw.find('[', key_pos + len(messages_key))
        if start_idx == -1:
             start_idx = texto_raw.find('[') # Buscar el primer '['
        end_idx = texto_raw.rfind(']')
        
        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            if log_callback: log_callback(f"  -> Could not find JSON array structure ([...]) in the file for salvage.")
            # Podríamos intentar buscar objetos {} sueltos aquí como fallback, pero es menos fiable
            return [] # Devolver lista vacía si no se encuentra estructura de array
        
        array_content = texto_raw[start_idx+1:end_idx]
        total_array_size = len(array_content)
        all_msgs = []
        chunks_data = []

        for chunk_num in range(num_chunks):
            start_pos = chunk_num * CHUNK_SIZE
            end_pos = min(start_pos + CHUNK_SIZE, total_array_size)
            chunk = array_content[start_pos:end_pos]
            chunks_data.append((chunk, start_pos, chunk_num, num_chunks))

        if stop_event and stop_event.is_set():
            if log_callback: log_callback(f"  -> Processing stopped by user before parallel processing")
            return []
            
        cpu_cores = multiprocessing.cpu_count()
        max_workers = max(1, min(cpu_cores - 1, num_chunks, 4))
        if log_callback: log_callback(f"  -> Using {max_workers} parallel workers (out of {cpu_cores} CPU cores)")

        # --- Procesamiento paralelo (similar a app_depuracion_tk.py) ---
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {}
            for chunk_args in chunks_data:
                future = executor.submit(process_chunk_with_progress_wrapper, chunk_args, log_callback, min_id, max_id, stop_event)
                future_to_chunk[future] = chunk_args

            for future in concurrent.futures.as_completed(future_to_chunk):
                if stop_event and stop_event.is_set(): break
                try:
                    result = future.result()
                    all_msgs.extend(result)
                except Exception as exc:
                     chunk_info = future_to_chunk[future]
                     if log_callback: log_callback(f'  -> Chunk {chunk_info[2]+1} generated an exception: {exc}')

        if log_callback:
             if not (stop_event and stop_event.is_set()):
                 log_callback(f"  -> Global Progress: 100.0% ({len(all_msgs)} objects found)", is_progress=True)
             log_callback(f"  -> Total objects extracted from entire file: {len(all_msgs)}")
        return all_msgs

# --- Wrapper para llamar a process_json_chunk en paralelo --- 
def process_chunk_with_progress_wrapper(args, log_callback, min_id, max_id, stop_event):
    """Wrapper para facilitar la llamada en ThreadPoolExecutor."""
    chunk, offset, chunk_num, total_chunks = args
    if stop_event and stop_event.is_set(): return []

    chunk_start_time = time.time()
    # Crear un logger específico para este chunk si log_callback existe
    chunk_logger = None
    if log_callback:
        def chunk_log(inner_msg, is_progress=False):
            prefixed = f"[Chunk {chunk_num+1}/{total_chunks}] {inner_msg.strip()}"
            log_callback(prefixed, is_progress=False) # No propagar progreso interno
        chunk_logger = chunk_log

    chunk_msgs = process_json_chunk(chunk, offset, chunk_logger, min_id, max_id, stop_event)
    chunk_time = time.time() - chunk_start_time

    # Reportar progreso global del chunk completado
    if log_callback:
        global_progress = ((chunk_num + 1) / total_chunks) * 100
        log_callback(f"  -> Global Progress: {global_progress:.1f}% ({len(chunk_msgs)} objects in chunk {chunk_num+1})", is_progress=True)
        log_callback(f"  -> Completed chunk {chunk_num+1}/{total_chunks} in {chunk_time:.1f}s, extracted {len(chunk_msgs)} objects")

    return chunk_msgs

# --- Función para procesar un chunk JSON (Implementación de app_depuracion_tk.py) ---
def process_json_chunk(chunk_text, offset, log_callback=None, min_id=None, max_id=None, stop_event=None):
    """Procesa un segmento (chunk) de texto JSON y extrae objetos válidos."""
    # (Esta es la implementación encontrada en app_depuracion_tk.py)
    chunk_msgs = []
    decoder = json.JSONDecoder()
    pos = 0
    total_len = len(chunk_text)
    
    # Límites para este chunk específico - AUMENTADOS
    MAX_OBJECTS_PER_CHUNK = 50000
    MAX_TRIES = 100000
    MAX_TIME = 300 # 5 minutos
    
    start_time = time.time()
    consecutive_failures = 0
    last_progress_report = time.time()
    progress_interval = 3.0
    check_stop_counter = 0
    CHECK_STOP_FREQUENCY = 1000
    
    while pos < total_len:
        check_stop_counter += 1
        if stop_event and check_stop_counter >= CHECK_STOP_FREQUENCY:
            check_stop_counter = 0
            if stop_event.is_set():
                if log_callback: log_callback(f"Processing stopped by user (quick check)")
                break
        
        current_time = time.time()
        if current_time - start_time > MAX_TIME:
            if log_callback: log_callback(f"Chunk timeout after {MAX_TIME}s. Extracted {len(chunk_msgs)} objects so far.")
            break
            
        if log_callback and (current_time - last_progress_report > progress_interval or (len(chunk_msgs) % 1000 == 0 and len(chunk_msgs) > 0)):
            progress_pct = (pos / total_len) * 100 if total_len > 0 else 0
            log_callback(f"Progreso: {progress_pct:.1f}% ({len(chunk_msgs)} objetos extraídos)")
            last_progress_report = current_time
            if stop_event and stop_event.is_set():
                if log_callback: log_callback(f"Processing stopped by user (during progress report)")
                break
                
        if len(chunk_msgs) >= MAX_OBJECTS_PER_CHUNK:
            if log_callback: log_callback(f"Reached maximum object limit ({MAX_OBJECTS_PER_CHUNK}). Moving to next chunk.")
            break
            
        if consecutive_failures >= MAX_TRIES:
            if log_callback: log_callback(f"Too many consecutive parsing failures ({MAX_TRIES}). Moving to next chunk.")
            break
            
        # Saltar espacios y comas iniciales
        while pos < total_len and chunk_text[pos] in " \n\r\t,":
            pos += 1
        if pos >= total_len: break
            
        # Intentar decodificar, buscando el inicio de un objeto '{'
        if chunk_text[pos] == '{':
            try:
                obj, end_idx = decoder.raw_decode(chunk_text, pos)
                obj_id = obj.get('id') if isinstance(obj, dict) else None
                
                # Filtrar por ID si aplica
                if obj_id is not None: 
                    if (min_id is not None and obj_id < min_id) or (max_id is not None and obj_id > max_id):
                        pos = end_idx # Saltar objeto fuera de rango
                        consecutive_failures = 0
                        continue 
                        
                chunk_msgs.append(obj)
                pos = end_idx
                consecutive_failures = 0  # Resetear contador de fallos
            except json.JSONDecodeError:
                # Si falla, avanzar un carácter y continuar
                pos += 1
                consecutive_failures += 1
            except Exception as e_inner:
                 # Otro error inesperado durante el parseo del objeto
                 if log_callback: log_callback(f"Unexpected error parsing object at offset {offset+pos}: {e_inner}")
                 pos += 1 # Avanzar para intentar recuperarse
                 consecutive_failures += 1
        else:
            # Si no empieza con '{', avanzar hasta el próximo posible inicio
            next_brace = chunk_text.find('{', pos + 1)
            if next_brace != -1:
                pos = next_brace
            else:
                pos = total_len # No hay más inicios de objeto, terminar chunk
            consecutive_failures += 1 # Considerar esto como un fallo de parseo
        
        # Revisar stop_event en cada iteración
        if stop_event and stop_event.is_set():
            if log_callback: log_callback("Processing stopped by user (inside chunk)")
            break
    
    return chunk_msgs 

def procesar_escritos_egw(file_path, idioma):
    """
    Procesa archivos TXT de Ellen G. White, segmentando el contenido
    basado en las citas de referencia y extrayendo el contexto.

    El patrón de cita esperado es como {CodigoLibro Pagina.Parrafo}
    con variaciones, pero siempre conteniendo numero.numero.

    Args:
        file_path (str): Ruta al archivo TXT.
        idioma (str): Código del idioma ('es' o 'en').

    Returns:
        list: Lista de diccionarios, cada uno representando una entrada.
    """
    entries = []
    citation_pattern = re.compile(r"(\{.*?\d+\.\d+.*?})")

    try:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()

        matches = list(citation_pattern.finditer(content))

        if not matches:
            print(f"Advertencia: No se encontraron citas válidas en {file_path}. Se devolverá el contenido completo como una sola entrada sin contexto.")
            return [{
                'contenido_texto': content.strip(),
                'contexto': None,
                'autor': 'Ellen G. White',
                'idioma': idioma,
                'fecha_creacion': None,
                'url_original': None,
                'plataforma_id': None,
                'fuente_id': None,
            }]

        for i in range(len(matches) - 1):
            start_index = matches[i].end()
            end_index = matches[i+1].start()
            contenido_texto_entrada = content[start_index:end_index].strip()
            contexto = matches[i+1].group(1).strip()
            if contenido_texto_entrada:
                entries.append({
                    'contenido_texto': contenido_texto_entrada,
                    'contexto': contexto,
                    'autor': 'Ellen G. White',
                    'idioma': idioma,
                    'fecha_creacion': None,
                    'url_original': None,
                    'plataforma_id': None,
                    'fuente_id': None,
                })
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {file_path}")
        return []
    except Exception as e:
        print(f"Error procesando archivo {file_path}: {e}")
        return []

    return entries 