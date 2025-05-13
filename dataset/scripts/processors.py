import logging
import re
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
import json # Para procesar NDJSON si los datos de entrada son de ese tipo
from dataclasses import dataclass, field # Importar dataclass

# Para parsear fechas de manera flexible
try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    logging.warning("python-dateutil not found. Date parsing will be limited.")

# Para extraer frontmatter de archivos Markdown
try:
    import frontmatter
    FRONTMATTER_AVAILABLE = True
except ImportError:
    FRONTMATTER_AVAILABLE = False
    logging.warning("python-frontmatter not found. Frontmatter parsing from .md files will be skipped.")

# Para metadatos de archivos
from stat import ST_CTIME, ST_MTIME


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. Definir el dataclass ProcessedTextContent
@dataclass
class ProcessedTextContent:
    """
    Dataclass para almacenar los resultados del procesamiento de texto/metadatos.
    """
    markdown_text: str
    title: Optional[str] = None
    publication_date_iso: Optional[str] = None
    source_document_pointer: Optional[str] = None
    additional_metadata_json: Dict[str, Any] = field(default_factory=dict)
    original_content_id: Optional[str] = None


def parse_publication_date(
    raw_date_str: Optional[Any] = None,
    file_path: Optional[str] = None,
    metadata_from_file: Optional[Dict[str, Any]] = None,
    force_null: bool = False
) -> Optional[str]:
    """
    Tries to parse a publication date from various sources and returns it in ISO format.
    Order of preference:
    1. Explicit raw_date_str (e.g., from JSON field).
    2. 'date', 'publish_date', 'created' fields in metadata_from_file.
    3. File system creation/modification time (use with caution).
    If force_null is True, returns None immediately.
    """
    if force_null:
        return None

    date_candidates = []

    if raw_date_str:
        if isinstance(raw_date_str, datetime):
            date_candidates.append(raw_date_str)
        elif isinstance(raw_date_str, str):
            date_candidates.append(raw_date_str)
        # Podría manejar otros tipos como timestamps numéricos aquí

    if metadata_from_file:
        for key in ['date', 'publish_date', 'publication_date', 'created', 'creation_date']:
            if key in metadata_from_file and metadata_from_file[key]:
                val = metadata_from_file[key]
                if isinstance(val, datetime):
                    date_candidates.append(val)
                elif isinstance(val, str):
                    date_candidates.append(val)
                break # Tomar el primer metadato de fecha encontrado

    # Intentar parsear las cadenas de fecha candidatas
    parsed_date: Optional[datetime] = None
    if DATEUTIL_AVAILABLE:
        for candidate_str in date_candidates:
            if isinstance(candidate_str, datetime): # Ya es datetime
                parsed_date = candidate_str
                break
            try:
                # date_parser.parse es muy flexible
                parsed_date = date_parser.parse(str(candidate_str))
                break # Tomar la primera que se pueda parsear
            except (ValueError, TypeError, OverflowError) as e:
                logging.debug(f"Could not parse date string '{candidate_str}' with dateutil: {e}")
    else: # Fallback si dateutil no está (menos flexible)
        for candidate_str in date_candidates:
            if isinstance(candidate_str, datetime):
                parsed_date = candidate_str
                break
            try: # Intentar formatos comunes
                parsed_date = datetime.fromisoformat(str(candidate_str).replace('Z', '+00:00'))
                break
            except ValueError:
                try:
                    parsed_date = datetime.strptime(str(candidate_str), '%Y-%m-%d %H:%M:%S')
                    break
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(str(candidate_str), '%Y-%m-%d')
                        break
                    except ValueError:
                        logging.debug(f"Could not parse date string '{candidate_str}' with strptime.")
    
    # Si no se pudo parsear ninguna fecha de las fuentes primarias, considerar fecha del sistema de archivos
    # ¡PRECAUCIÓN! Esto a menudo NO es la fecha de publicación real.
    # Usar solo como último recurso y si tiene sentido para el tipo de archivo.
    # Por ejemplo, para archivos descargados recientemente, la fecha de creación del archivo
    # podría ser la fecha de "adquisición", no de publicación.
    # if not parsed_date and file_path:
    #     try:
    #         # ST_CTIME puede ser 'creation time' en Unix, 'change time' en Windows.
    #         # ST_MTIME es 'modification time'.
    #         # Usar el más antiguo de los dos como una heurística muy aproximada.
    #         stat_info = os.stat(file_path)
    #         # Convertir a datetime con zona horaria (naive por defecto)
    #         # file_date = datetime.fromtimestamp(min(stat_info[ST_CTIME], stat_info[ST_MTIME]))
    #         # logging.warning(f"Using file system date for {file_path} as a fallback for publication_date. This may not be accurate.")
    #         # parsed_date = file_date # Descomentar con mucha precaución
    #     except Exception as e:
    #         logging.warning(f"Could not get file system date for {file_path}: {e}")


    if parsed_date:
        # Convertir a UTC si tiene zona horaria, o dejar naive
        if parsed_date.tzinfo is not None and parsed_date.tzinfo.utcoffset(parsed_date) is not None:
            parsed_date = parsed_date.astimezone(timezone.utc)
        # Formatear a ISO (sin microsegundos)
        return parsed_date.strftime('%Y-%m-%d')
    return None  # o .isoformat()


def extract_title_from_markdown(markdown_text: str, metadata_from_file: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Extracts a title. Priority:
    1. 'title' from metadata_from_file (e.g., from DOCX properties, HTML title tag).
    2. First H1 header in Markdown.
    3. First line of text if it's short and seems like a title.
    """
    if metadata_from_file and isinstance(metadata_from_file.get('title'), str) and metadata_from_file['title'].strip():
        return metadata_from_file['title'].strip()

    # Buscar H1 (línea que empieza con '# ')
    h1_match = re.search(r"^\s*#\s+(.+)", markdown_text, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()

    # Como último recurso, tomar la primera línea si es corta y no es un simple párrafo largo.
    # lines = markdown_text.strip().split('\n', 1)
    # if lines:
    #     first_line = lines[0].strip()
    #     if 0 < len(first_line) < 150 and not first_line.endswith('.'): # Heurística simple
    #         # Evitar tomar la primera línea de un poema o código como título
    #         if not first_line.startswith(('    ', '```', '>')):
    #             return first_line
    return None

def extract_frontmatter_and_text(markdown_content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extracts frontmatter (if present) from Markdown content.
    Returns (frontmatter_dict, text_content_without_frontmatter).
    """
    if FRONTMATTER_AVAILABLE:
        try:
            post = frontmatter.loads(markdown_content)
            return post.metadata, post.content
        except Exception as e:
            logging.debug(f"Could not parse frontmatter: {e}. Treating content as plain markdown.")
            return {}, markdown_content # Tratar todo como contenido si el frontmatter es inválido
    return {}, markdown_content # Sin frontmatter, todo es contenido

def process_raw_ndjson_data(
    raw_data: Dict[str, Any],
    parser_config: Optional[Dict[str, Any]] = None # Añadido para extraer title y id
    ) -> Tuple[Optional[str], Optional[str], Any, Dict[str, Any], Optional[str], Optional[str]]:
    """
    Extracts key fields from a raw NDJSON data object.
    Returns:
        - text_content (str): The main text.
        - source_document_pointer (str): The original ID or context reference.
        - publication_date_candidate (Any): Candidate for publication date.
        - remaining_metadata (dict): Other fields to be included in additional_metadata_json.
        - title (Optional[str]): Title extracted based on parser_config.
        - original_content_id (Optional[str]): Original ID extracted based on parser_config.
    """
    text_content: Optional[str] = None
    source_document_pointer: Optional[str] = None
    publication_date_candidate: Any = None
    title_from_ndjson: Optional[str] = None
    original_id_from_ndjson: Optional[str] = None
    
    # Usar text_property_paths de parser_config si está disponible para extraer texto
    # Esta lógica ya está en filter_and_extract_from_json_object, así que aquí nos centramos
    # en lo que raw_ndjson_object podría tener directamente (ej. si el texto ya fue extraído y esto es para metadatos)
    # O si el parser_config guía la extracción aquí mismo.
    
    # Asumimos que el texto principal (si este es el lugar para extraerlo) se maneja ANTES
    # o con una lógica más explícita usando parser_config.text_property_paths
    # Por ahora, nos basamos en campos comunes si no hay parser_config o si el texto ya está.
    
    if 'text' in raw_data and isinstance(raw_data['text'], str): # Campo de texto principal
        text_content = str(raw_data.pop('text'))
    elif 'texto' in raw_data and isinstance(raw_data['texto'], str): # Alternativa
        text_content = str(raw_data.pop('texto'))
    # Si no hay 'text' o 'texto', text_content permanecerá None, y la lógica aguas arriba debe haberlo llenado.

    # Extracción de metadatos usando parser_config si existe
    metadata_paths = parser_config.get("metadata_paths", {}) if parser_config else {}

    # Título
    title_path = metadata_paths.get("title")
    if title_path:
        title_val = raw_data.get(title_path) # No hacemos pop aquí, puede que se quiera en additional_metadata
        if isinstance(title_val, str) and title_val.strip():
            title_from_ndjson = title_val.strip()
        elif isinstance(title_val, list) and title_val and isinstance(title_val[0], str): # Tomar el primer string de una lista
            title_from_ndjson = title_val[0].strip()

    # Source Document Pointer
    sdp_path = metadata_paths.get("source_document_pointer") # Nuevo path configurable
    if sdp_path:
        sdp_val = raw_data.get(sdp_path)
        if sdp_val is not None: source_document_pointer = str(sdp_val)
    # Fallbacks para SDP
    if not source_document_pointer and 'id' in raw_data: source_document_pointer = str(raw_data.get('id'))
    if not source_document_pointer and 'message_id' in raw_data: source_document_pointer = str(raw_data.get('message_id')) # Común en chats
    if not source_document_pointer and 'contexto' in raw_data: # EGW
        context_val = raw_data.get('contexto')
        if isinstance(context_val, str) and not (context_val.startswith(('/', '\\\\')) or '.' in context_val.split('/')[-1]): # No es ruta
            source_document_pointer = context_val
            
    # Publication Date Candidate
    pub_date_path = metadata_paths.get("publication_date")
    if pub_date_path:
        publication_date_candidate = raw_data.get(pub_date_path)
    # Fallbacks para fecha
    if not publication_date_candidate and 'date' in raw_data: publication_date_candidate = raw_data.get('date')
    if not publication_date_candidate and 'fecha' in raw_data: publication_date_candidate = raw_data.get('fecha')
    
    # Original Content ID (si existe un campo específico en el JSON para ello)
    # Este es diferente del source_document_pointer; podría ser un UUID del contenido original.
    original_id_path = metadata_paths.get("original_content_id")
    if original_id_path:
        id_val = raw_data.get(original_id_path)
        if id_val is not None: original_id_from_ndjson = str(id_val)

    # Los campos extraídos (o que se intentaron extraer) no se deben duplicar en remaining_metadata
    # Hacemos una copia para no modificar el raw_data original si se usa después.
    remaining_metadata = dict(raw_data)
    
    # Campos a no incluir explícitamente en additional_metadata si ya se usaron o son manejados por BatchContext
    # (esto es una simplificación, la limpieza de metadatos puede ser más compleja)
    fields_handled_elsewhere = {
        text_content_key for text_content_key in parser_config.get("text_property_paths", []) if parser_config
    } if parser_config else set()
    if title_path: fields_handled_elsewhere.add(title_path)
    if sdp_path: fields_handled_elsewhere.add(sdp_path)
    if pub_date_path: fields_handled_elsewhere.add(pub_date_path)
    if original_id_path: fields_handled_elsewhere.add(original_id_path)
    # Añadir campos comunes que ya se mapearon o no se quieren
    fields_handled_elsewhere.update(['text', 'texto', 'id', 'message_id', 'contexto', 'date', 'fecha'])
    # Campos de BatchContext (si estuvieran en el NDJSON por error)
    fields_handled_elsewhere.update(['author_name', 'language_code', 'origin_type_name', 'acquisition_date'])


    final_remaining_metadata = {k: v for k, v in remaining_metadata.items() if k not in fields_handled_elsewhere}
    
    return text_content, source_document_pointer, publication_date_candidate, final_remaining_metadata, title_from_ndjson, original_id_from_ndjson

# 2. Modificar process_text_content
def process_text_content(
    markdown_text: str,
    file_path: Optional[str] = None,
    metadata_from_converter: Optional[Dict[str, Any]] = None,
    raw_ndjson_object: Optional[Dict[str, Any]] = None,
    force_null_publication_date: bool = False,
    parser_config: Optional[Dict[str, Any]] = None # Añadido para guiar extracción de NDJSON
) -> ProcessedTextContent: # Cambiado el tipo de retorno
    """
    Processes Markdown text or raw NDJSON to extract title, publication date, and other metadata.
    Handles frontmatter if present in Markdown.

    Returns:
        An instance of ProcessedTextContent.
    """
    text_to_process = markdown_text
    frontmatter_meta: Dict[str, Any] = {}
    final_title: Optional[str] = None
    final_sdp: Optional[str] = None
    final_pub_date: Optional[str] = None
    final_additional_meta: Dict[str, Any] = {}
    final_original_id: Optional[str] = None

    metadata_from_file_or_converter = metadata_from_converter or {}

    if raw_ndjson_object:
        # Procesa el objeto NDJSON directamente usando parser_config
        # process_raw_ndjson_data ahora también puede extraer title y original_content_id
        (   ndjson_text_content, 
            source_doc_pointer_from_ndjson, 
            pub_date_candidate_from_ndjson, 
            additional_meta_from_ndjson,
            title_from_ndjson, # Nuevo valor de retorno
            original_id_from_ndjson # Nuevo valor de retorno
        ) = process_raw_ndjson_data(raw_ndjson_object, parser_config)

        # El texto principal para NDJSON es el que se extrajo o el markdown_text pasado (si es un chunk ya procesado)
        text_to_process = ndjson_text_content or markdown_text # Priorizar texto de ndjson si existe
        
        final_title = title_from_ndjson # Título directamente del NDJSON si se mapeó
        final_sdp = source_doc_pointer_from_ndjson
        final_original_id = original_id_from_ndjson
        final_additional_meta.update(additional_meta_from_ndjson)
        
        # Intentar parsear la fecha candidata del NDJSON
        if pub_date_candidate_from_ndjson:
            final_pub_date = parse_publication_date(
                raw_date_str=pub_date_candidate_from_ndjson,
                force_null=force_null_publication_date
            )
        # El título también podría venir de metadata_from_converter si se pasó (ej. nombre de archivo)
        if not final_title and metadata_from_file_or_converter.get('source_title'):
            final_title = metadata_from_file_or_converter.get('source_title')

    else: # Flujo para Markdown (no NDJSON)
        # Extraer frontmatter si es contenido Markdown
        if text_to_process: # Solo si hay texto (podría ser None si el conversor falló)
             frontmatter_meta, text_without_frontmatter = extract_frontmatter_and_text(text_to_process)
             text_to_process = text_without_frontmatter # Usar texto sin frontmatter para el resto
        else: # Si no hay texto inicial (ej. conversor falló), no hay nada que procesar
            return ProcessedTextContent(markdown_text="")


        # Combinar metadatos: frontmatter tiene precedencia sobre los del convertidor
        # excepto para campos específicos como 'source_title' que el convertidor podría haber obtenido mejor.
        combined_meta_for_extraction = {**metadata_from_file_or_converter, **frontmatter_meta}
        
        final_title = extract_title_from_markdown(text_to_process, combined_meta_for_extraction)
        if not final_title and metadata_from_file_or_converter.get('source_title'): # Fallback al título del conversor
            final_title = metadata_from_file_or_converter.get('source_title')
            
        # Fecha de publicación: buscar en frontmatter, luego en metadatos del conversor
        final_pub_date = parse_publication_date(
            raw_date_str=frontmatter_meta.get('date') or frontmatter_meta.get('publication_date'), # Prioridad frontmatter
            metadata_from_file=metadata_from_file_or_converter, # Luego del conversor (si 'date' no estaba en frontmatter)
            file_path=file_path, # Para fallback a fecha de sistema (con precaución)
            force_null=force_null_publication_date
        )
        
        # SDP: Buscar en frontmatter
        final_sdp = str(frontmatter_meta.get('id', frontmatter_meta.get('slug', frontmatter_meta.get('source_document_pointer')))) if \
                    frontmatter_meta.get('id') or frontmatter_meta.get('slug') or frontmatter_meta.get('source_document_pointer') else None

        # Original Content ID: Buscar en frontmatter
        final_original_id = str(frontmatter_meta.get('original_content_id')) if frontmatter_meta.get('original_content_id') else None

        # Metadatos adicionales son el frontmatter restante (que no se mapeó a campos principales)
        # y cualquier nota del conversor.
        final_additional_meta.update(frontmatter_meta) # Empezar con todo el frontmatter
        # Remover campos ya usados para evitar redundancia en additional_metadata_json
        keys_to_remove = ['title', 'date', 'publish_date', 'publication_date', 'created', 'creation_date', 'id', 'slug', 'source_document_pointer', 'original_content_id']
        for key in keys_to_remove:
            final_additional_meta.pop(key, None)
        
        if metadata_from_file_or_converter.get('converter_notes'):
            final_additional_meta['converter_notes'] = metadata_from_file_or_converter['converter_notes']

    # Limpieza final del texto (ej. espacios extra)
    final_markdown_text = text_to_process.strip() if text_to_process else ""

    return ProcessedTextContent(
        markdown_text=final_markdown_text,
        title=final_title,
        publication_date_iso=final_pub_date,
        source_document_pointer=final_sdp,
        additional_metadata_json=final_additional_meta,
        original_content_id=final_original_id
    )


if __name__ == '__main__':
    # --- Ejemplos de prueba ---
    print("--- Test 1: Markdown con Frontmatter ---")
    md_with_fm = """---
title: My Test Document
date: 2023-01-15T10:00:00Z
author_extra: John Doe
tags: [test, example]
original_id: fm_id_123
---
# Actual H1 Title (ignored if title in frontmatter)
This is the main content.
"""
    if FRONTMATTER_AVAILABLE:
        text, title, pub_date, sdp, add_meta = process_text_content(md_with_fm, file_path="test.md")
        print(f"Text: '{text[:30]}...'")
        print(f"Title: {title}")
        print(f"Publication Date: {pub_date}")
        print(f"Source Doc Pointer: {sdp}")
        print(f"Additional Metadata: {add_meta}")
    else:
        print("Skipping frontmatter test: python-frontmatter not installed.")

    print("\n--- Test 2: Markdown sin Frontmatter, con H1 ---")
    md_plain_h1 = """
# This is the Real Title
Some content here.
Another paragraph.
"""
    text, title, pub_date, sdp, add_meta = process_text_content(md_plain_h1, file_path="test_plain.md")
    print(f"Text: '{text[:30]}...'")
    print(f"Title: {title}")
    print(f"Publication Date: {pub_date}") # Será None o de archivo si se habilita
    print(f"Source Doc Pointer: {sdp}")
    print(f"Additional Metadata: {add_meta}")

    print("\n--- Test 3: Con metadatos del conversor y fecha de archivo (si se habilita) ---")
    converter_meta = {'title': 'Title From Converter', 'creation_date': '2022-11-20'}
    text_from_converter = "Just plain text from a converted file."
    # Crear un archivo temporal para simular fecha de sistema
    temp_file_for_date_test = "temp_date_test_file.txt"
    with open(temp_file_for_date_test, "w") as f:
        f.write("test")
    
    text, title, pub_date, sdp, add_meta = process_text_content(
        text_from_converter,
        file_path=temp_file_for_date_test,
        metadata_from_converter=converter_meta
    )
    print(f"Text: '{text[:30]}...'")
    print(f"Title: {title}")
    print(f"Publication Date: {pub_date}") # Debería ser 2022-11-20
    print(f"Source Doc Pointer: {sdp}")
    print(f"Additional Metadata: {add_meta}")
    os.remove(temp_file_for_date_test)

    print("\n--- Test 4: Datos de un NDJSON parseado ---")
    ndjson_obj_ismael_like = {
        "texto": "Este es el contenido principal del NDJSON.",
        "fecha": "2020-09-16T15:19:35", # Ismael-like
        "fuente": "debate_cristiano_group", # Irá a additional_metadata o se descarta
        "contexto": "E:\\path\\to\\file.json", # Podría ser original_file_path si no lo tenemos ya
        "autor": "Ismael", # Se manejará por BatchContext
        "id": 18971, # Será source_document_pointer
        "custom_field": "some_value"
    }
    # El 'markdown_text' inicial para process_text_content sería irrelevante aquí si NDJSON tiene 'texto'
    text, title, pub_date, sdp, add_meta = process_text_content(
        markdown_text="", # El texto vendrá del NDJSON
        raw_ndjson_object=ndjson_obj_ismael_like,
        file_path="source_file.ndjson" # El path del archivo NDJSON en sí
    )
    print(f"Text: '{text[:40]}...'")
    print(f"Title: {title}") # Probablemente None a menos que el NDJSON tenga un campo de título
    print(f"Publication Date: {pub_date}") # Debería ser de 'fecha'
    print(f"Source Doc Pointer: {sdp}") # Debería ser de 'id'
    print(f"Additional Metadata: {add_meta}") # Debería incluir 'fuente', 'contexto', 'custom_field'

    print("\n--- Test 5: Forzar fecha de publicación a NULL ---")
    text, title, pub_date, sdp, add_meta = process_text_content(
        md_with_fm, # Usamos el que tiene fecha en frontmatter
        file_path="test.md",
        force_null_publication_date=True
    )
    print(f"Text: '{text[:30]}...'")
    print(f"Title: {title}")
    print(f"Publication Date (forced NULL): {pub_date}") # Debería ser None
    print(f"Source Doc Pointer: {sdp}")
    print(f"Additional Metadata: {add_meta}")