import logging
import re
import os
import uuid # Importado
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List # List importado por si acaso, aunque no se usa directamente aquí

# Importar el nuevo ProcessedContentItem
from .data_models import ProcessedContentItem

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

# Para metadatos de archivos (si se decide usar como fallback extremo para fechas)
# from stat import ST_CTIME, ST_MTIME

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# El dataclass ProcessedTextContent ha sido eliminado. Usaremos ProcessedContentItem directamente.

def parse_publication_date(
    raw_date_str: Optional[Any] = None,
    metadata_from_file: Optional[Dict[str, Any]] = None, # e.g., source_doc_metadata
    force_null: bool = False
) -> Optional[str]:
    """
    Tries to parse a publication date from various sources and returns it in 'YYYY-MM-DD' or 'YYYY' format.
    Order of preference:
    1. Explicit raw_date_str (e.g., from JSON field, or a specific metadata field).
    2. 'fecha_publicacion_documento', 'date', 'publish_date', 'created' fields in metadata_from_file.
    If force_null is True, returns None immediately.
    """
    if force_null:
        return None

    date_candidates_str: List[str] = []
    
    if raw_date_str:
        if isinstance(raw_date_str, datetime):
            # Si ya es datetime, formatearlo directamente
            try:
                return raw_date_str.strftime('%Y-%m-%d') if raw_date_str.year > 1 else str(raw_date_str.year)
            except ValueError: # En caso de años muy lejanos que strftime no maneje
                return str(raw_date_str.year)
        elif isinstance(raw_date_str, str):
            date_candidates_str.append(raw_date_str)

    if metadata_from_file:
        # Claves ordenadas por preferencia
        for key in ['fecha_publicacion_documento', 'date', 'publish_date', 'publication_date', 'created', 'creation_date']:
            val = metadata_from_file.get(key)
            if val:
                if isinstance(val, datetime):
                    try:
                        return val.strftime('%Y-%m-%d') if val.year > 1 else str(val.year)
                    except ValueError:
                        return str(val.year)
                elif isinstance(val, str):
                    date_candidates_str.append(val)
                break # Tomar el primer metadato de fecha encontrado

    parsed_date: Optional[datetime] = None
    if DATEUTIL_AVAILABLE:
        for candidate_str_item in date_candidates_str:
            try:
                parsed_date = date_parser.parse(str(candidate_str_item))
                if parsed_date: break
            except (ValueError, TypeError, OverflowError) as e:
                logging.debug(f"Could not parse date string '{candidate_str_item}' with dateutil: {e}")
    else: # Fallback si dateutil no está
        for candidate_str_item in date_candidates_str:
            try: 
                parsed_date = datetime.fromisoformat(str(candidate_str_item).replace('Z', '+00:00'))
                if parsed_date: break
            except ValueError:
                # Intentar otros formatos comunes si es necesario
                pass # Por ahora, simplificado

    if parsed_date:
        try:
            # Devolver YYYY-MM-DD si es posible, o solo YYYY como fallback
            return parsed_date.strftime('%Y-%m-%d') if parsed_date.year > 1 else str(parsed_date.year)
        except ValueError: # Para años muy fuera de rango para strftime
            return str(parsed_date.year) if hasattr(parsed_date, 'year') and parsed_date.year > 1 else None
            
    # Si solo se encontró una cadena que parece año (YYYY)
    for candidate in date_candidates_str:
        if re.fullmatch(r'\d{4}', candidate):
            return candidate # Asumir que es un año si es la única info

    return None


def extract_title_from_markdown(markdown_text: str, source_doc_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Extracts a title. Priority:
    1. 'titulo_documento' from source_doc_metadata.
    2. First H1 header in Markdown.
    """
    if source_doc_metadata and isinstance(source_doc_metadata.get('titulo_documento'), str) and source_doc_metadata['titulo_documento'].strip():
        return source_doc_metadata['titulo_documento'].strip()

    h1_match = re.search(r"^\s*#\s+(.+)", markdown_text, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
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
            return {}, markdown_content
    return {}, markdown_content

def process_raw_ndjson_data(
    raw_data: Dict[str, Any],
    parser_config: Optional[Dict[str, Any]] = None 
) -> Tuple[str, Dict[str, Any]]:
    """
    Extracts key fields from a raw NDJSON data object and attempts to structure them
    into markdown_text and a source_doc_metadata dictionary compatible with ProcessedContentItem.

    Returns:
        - markdown_text (str): The main text content.
        - source_doc_metadata (Dict[str, Any]): Metadata dictionary.
    """
    final_text_content = ""
    extracted_meta: Dict[str, Any] = {"metadatos_adicionales_fuente": {}}

    # Lógica para extraer texto (simplificada, asume que hay una clave principal de texto)
    # Debería ser configurable a través de parser_config si es más complejo
    text_keys = parser_config.get("text_property_paths", ["text", "content", "body"]) if parser_config else ["text", "content", "body"]
    for key in text_keys:
        if key in raw_data and isinstance(raw_data[key], str):
            final_text_content = raw_data[key]
            break
    
    # Extraer y mapear otros campos conocidos
    # El ID original del NDJSON podría ser el id_documento_fuente
    id_keys = parser_config.get("id_property_paths", ["id", "_id", "message_id"]) if parser_config else ["id", "_id", "message_id"]
    for key in id_keys:
        if key in raw_data:
            extracted_meta["id_documento_fuente_original_ndjson"] = str(raw_data[key]) # Se usará para id_documento_fuente o en metadatos adicionales
            break

    title_keys = parser_config.get("title_property_paths", ["title", "subject"]) if parser_config else ["title", "subject"]
    for key in title_keys:
        if key in raw_data and isinstance(raw_data[key], str):
            extracted_meta["titulo_documento"] = raw_data[key]
            break

    # Para fecha de publicación y autor, se pueden usar claves comunes o configurables
    date_val = raw_data.get("date") or raw_data.get("timestamp") or raw_data.get("created_at")
    if date_val:
        extracted_meta["fecha_publicacion_documento_raw"] = date_val # parse_publication_date lo procesará

    author_val = raw_data.get("author") or raw_data.get("user") or raw_data.get("from")
    if author_val:
         extracted_meta["autor_documento"] = str(author_val) if not isinstance(author_val, dict) else author_val.get("name")


    # Todos los demás campos del NDJSON van a metadatos_adicionales_fuente
    for key, value in raw_data.items():
        if key not in [text_keys, id_keys, title_keys, "date", "timestamp", "created_at", "author", "user", "from"]: # Evitar duplicados si ya se mapearon
            extracted_meta.setdefault("metadatos_adicionales_fuente", {})[key] = value
            
    return final_text_content, extracted_meta


def process_text_content(
    markdown_text: Optional[str] = None,
    file_path: Optional[str] = None, # Usado principalmente para logs o como fallback
    source_doc_metadata: Optional[Dict[str, Any]] = None, # Metadatos del conversor
    raw_ndjson_object: Optional[Dict[str, Any]] = None, # Si la entrada es un objeto NDJSON
    force_null_publication_date: bool = False,
    parser_config: Optional[Dict[str, Any]] = None, # Para guiar extracción de NDJSON
    pipeline_version: str = "0.1.0-default" # Versión del pipeline
) -> Optional[ProcessedContentItem]:
    """
    Processes Markdown text (or raw NDJSON) to create a ProcessedContentItem.
    Handles frontmatter if present in Markdown.

    Returns:
        An instance of ProcessedContentItem, or None if essential data is missing.
    """
    current_timestamp_iso = datetime.now(timezone.utc).isoformat()
    final_source_metadata = source_doc_metadata.copy() if source_doc_metadata else {}
    final_markdown_content = markdown_text if markdown_text is not None else ""

    # Si la entrada es un objeto NDJSON, procesarlo primero
    if raw_ndjson_object:
        ndjson_text, ndjson_meta = process_raw_ndjson_data(raw_ndjson_object, parser_config)
        final_markdown_content = ndjson_text # Sobrescribir markdown_text
        # Fusionar metadatos, dando preferencia a los del NDJSON si entran en conflicto
        # o decidiendo una estrategia (aquí ndjson_meta puede tener campos más específicos)
        for key, value in ndjson_meta.items():
            if key == "metadatos_adicionales_fuente":
                final_source_metadata.setdefault("metadatos_adicionales_fuente", {}).update(value)
            else:
                final_source_metadata[key] = value


    # Extraer frontmatter del contenido Markdown y fusionar con metadatos existentes
    frontmatter_meta, content_after_frontmatter = extract_frontmatter_and_text(final_markdown_content)
    final_markdown_content = content_after_frontmatter # Actualizar texto sin frontmatter

    if frontmatter_meta:
        for key, value in frontmatter_meta.items():
            # Mapear claves comunes de frontmatter a campos de ProcessedContentItem si es posible
            if key.lower() == "title":
                final_source_metadata["titulo_documento"] = final_source_metadata.get("titulo_documento", value)
            elif key.lower() == "author":
                final_source_metadata["autor_documento"] = final_source_metadata.get("autor_documento", value)
            elif key.lower() in ["date", "published", "creation_date"]:
                 # Dar preferencia a la fecha del frontmatter si no hay una ya de una fuente "superior"
                if "fecha_publicacion_documento_raw" not in final_source_metadata: # O alguna lógica de preferencia
                    final_source_metadata["fecha_publicacion_documento_raw"] = value
            elif key.lower() == "tags" and isinstance(value, list):
                 final_source_metadata.setdefault("metadatos_adicionales_fuente", {})["tags_frontmatter"] = value
            else: # Otros campos del frontmatter van a metadatos adicionales
                final_source_metadata.setdefault("metadatos_adicionales_fuente", {})[f"fm_{key}"] = value

    # --- Construir ProcessedContentItem ---
    item_id_segmento = str(uuid.uuid4())
    
    # Determinar id_documento_fuente (prioridad: hash, luego ruta, luego ID de NDJSON original)
    item_id_documento_fuente = final_source_metadata.get("hash_documento_original")
    if not item_id_documento_fuente:
        item_id_documento_fuente = final_source_metadata.get("id_documento_fuente_original_ndjson")
    if not item_id_documento_fuente and file_path:
        item_id_documento_fuente = str(Path(file_path).resolve()) # Como fallback si no hay hash
    if not item_id_documento_fuente: # Si sigue sin ID (ej. texto puro sin archivo)
        item_id_documento_fuente = str(uuid.uuid4()) # Un UUID como último recurso para el documento
        final_source_metadata.setdefault("metadatos_adicionales_fuente", {})["id_documento_generado"] = True


    item_titulo = extract_title_from_markdown(final_markdown_content, final_source_metadata) or \
                  final_source_metadata.get("titulo_documento") or \
                  (Path(file_path).stem if file_path else "Sin Título")

    item_fecha_pub_str = parse_publication_date(
        raw_date_str=final_source_metadata.pop("fecha_publicacion_documento_raw", None), # Tomar y remover la versión raw
        metadata_from_file=final_source_metadata, # Pasar el resto de metadatos
        force_null=force_null_publication_date
    )

    # Asegurar que los campos principales de metadatos del documento estén en el nivel superior si existen
    item_ruta_original = final_source_metadata.get("ruta_archivo_original", file_path)
    item_hash_original = final_source_metadata.get("hash_documento_original")
    item_autor = final_source_metadata.get("autor_documento")
    item_editorial = final_source_metadata.get("editorial_documento")
    item_isbn = final_source_metadata.get("isbn_documento")
    item_idioma = final_source_metadata.get("idioma_documento", "und")


    # Consolidar metadatos_adicionales_fuente
    additional_meta = final_source_metadata.get("metadatos_adicionales_fuente", {})
    # Mover campos no mapeados directamente de final_source_metadata a additional_meta
    # para no perderlos y evitar redundancia.
    campos_directos_item = [
        "ruta_archivo_original", "hash_documento_original", "titulo_documento", 
        "autor_documento", "fecha_publicacion_documento", "editorial_documento", 
        "isbn_documento", "idioma_documento", "metadatos_adicionales_fuente",
        "id_documento_fuente_original_ndjson", "fecha_publicacion_documento_raw" # Claves temporales o ya usadas
    ]
    for k, v in final_source_metadata.items():
        if k not in campos_directos_item and k not in additional_meta :
            additional_meta[f"orig_{k}"] = v # Prefijo para indicar su origen si hay colisión

    # Placeholder para campos de segmentación (el documento entero es un segmento)
    item_tipo_segmento = "documento_completo"
    item_orden_segmento = 0
    item_jerarquia = {} # Vacío por ahora
    item_notas_procesamiento = additional_meta.pop("converter_notes", None) # Mover notas del conversor

    try:
        content_item = ProcessedContentItem(
            id_segmento=item_id_segmento,
            id_documento_fuente=item_id_documento_fuente,
            
            ruta_archivo_original=item_ruta_original,
            hash_documento_original=item_hash_original,
            titulo_documento=item_titulo,
            autor_documento=item_autor,
            fecha_publicacion_documento=item_fecha_pub_str,
            editorial_documento=item_editorial,
            isbn_documento=item_isbn,
            idioma_documento=item_idioma,
            metadatos_adicionales_fuente=additional_meta,
            
            texto_segmento=final_markdown_content,
            tipo_segmento=item_tipo_segmento, # Placeholder
            orden_segmento_documento=item_orden_segmento, # Placeholder
            jerarquia_contextual=item_jerarquia, # Placeholder
            longitud_caracteres_segmento=len(final_markdown_content),
            embedding_vectorial=None, # Se generará después
            
            timestamp_procesamiento=current_timestamp_iso,
            version_pipeline_etl=pipeline_version,
            nombre_segmentador_usado="ninguno_aplicado_en_procesador", # Placeholder
            notas_procesamiento_segmento=item_notas_procesamiento
        )
        return content_item
    except Exception as e:
        logging.error(f"Error creando ProcessedContentItem para {file_path or 'datos NDJSON'}: {e}", exc_info=True)
        return None


if __name__ == '__main__':
    # --- Ejemplos de prueba ---
    print("--- Test 1: Markdown con Frontmatter ---")
    md_with_fm = """---
title: Título desde Frontmatter
author: Autor FM
date: 2023-03-15
tags: [test, fm]
custom_field: valor_custom
---
Este es el contenido principal del markdown.
# Un subtítulo H1 aquí
Otro párrafo.
"""
    # Simular metadatos del conversor
    mock_converter_meta_fm = {
        "ruta_archivo_original": "/path/to/test_fm.md",
        "hash_documento_original": "fm_hash_123",
        "idioma_documento": "es",
        "metadatos_adicionales_fuente": {"converter_notes": "Conversion OK"}
    }
    processed_fm = process_text_content(markdown_text=md_with_fm, file_path="/path/to/test_fm.md", source_doc_metadata=mock_converter_meta_fm)
    if processed_fm:
        print(f"ID Segmento: {processed_fm.id_segmento}")
        print(f"ID Documento Fuente: {processed_fm.id_documento_fuente}")
        print(f"Título: {processed_fm.titulo_documento}")
        print(f"Autor: {processed_fm.autor_documento}")
        print(f"Fecha Pub: {processed_fm.fecha_publicacion_documento}")
        print(f"Idioma: {processed_fm.idioma_documento}")
        print(f"Texto (primeros 50): {processed_fm.texto_segmento[:50]}...")
        print(f"Metadatos Adicionales Fuente: {processed_fm.metadatos_adicionales_fuente}")
        print(f"Notas Procesamiento: {processed_fm.notas_procesamiento_segmento}")
        print("-" * 20)

    print("\\n--- Test 2: Markdown simple sin Frontmatter ---")
    md_simple = """# Título Principal H1
Este es el contenido.
Proviene de un archivo simple.
"""
    mock_converter_meta_simple = {
        "ruta_archivo_original": "/path/to/simple.md",
        "hash_documento_original": "simple_hash_456",
        "idioma_documento": "en",
        "titulo_documento": "Título desde Conversor", # Conversor ya extrajo un título
        "autor_documento": "Autor del Conversor",
        "fecha_publicacion_documento": "2022" # Conversor pudo extraer solo año
    }
    processed_simple = process_text_content(markdown_text=md_simple, file_path="/path/to/simple.md", source_doc_metadata=mock_converter_meta_simple)
    if processed_simple:
        print(f"Título: {processed_simple.titulo_documento}")
        print(f"Autor: {processed_simple.autor_documento}")
        print(f"Fecha Pub: {processed_simple.fecha_publicacion_documento}")
        print(f"Texto (primeros 50): {processed_simple.texto_segmento[:50]}...")
        print(f"Metadatos Adicionales Fuente: {processed_simple.metadatos_adicionales_fuente}")
        print("-" * 20)

    print("\\n--- Test 3: Objeto NDJSON ---")
    ndjson_obj = {
        "id": "msg123",
        "user": "Usuario NDJSON",
        "text": "Este es un mensaje desde un objeto NDJSON. Contiene información útil.",
        "timestamp": "2023-01-01T12:00:00Z",
        "channel": "general",
        "custom_ndjson_field": "valor_ndjson"
    }
    # Para NDJSON, source_doc_metadata podría estar vacío o tener info general del batch
    processed_ndjson = process_text_content(raw_ndjson_object=ndjson_obj, parser_config={"id_property_paths": ["id"], "text_property_paths": ["text"]})
    if processed_ndjson:
        print(f"ID Documento Fuente: {processed_ndjson.id_documento_fuente}") # Debería ser 'msg123' si se mapea
        print(f"Título: {processed_ndjson.titulo_documento}") # Podría ser None o parte del texto
        print(f"Autor: {processed_ndjson.autor_documento}")
        print(f"Fecha Pub: {processed_ndjson.fecha_publicacion_documento}")
        print(f"Texto: {processed_ndjson.texto_segmento}")
        print(f"Metadatos Adicionales Fuente: {processed_ndjson.metadatos_adicionales_fuente}")
        print("-" * 20)

    print("\\n--- Test 4: Markdown sin info de título ni fecha ---")
    md_no_info = "Solo un párrafo de texto.\nSin mucha estructura."
    mock_converter_meta_no_info = {
        "ruta_archivo_original": "test_no_info.md",
        "hash_documento_original": "no_info_hash",
        "idioma_documento": "es"
    }
    processed_no_info = process_text_content(markdown_text=md_no_info, file_path="test_no_info.md", source_doc_metadata=mock_converter_meta_no_info)
    if processed_no_info:
        print(f"Título: {processed_no_info.titulo_documento}") # Debería ser 'test_no_info'
        print(f"Fecha Pub: {processed_no_info.fecha_publicacion_documento}") # Debería ser None
        print(f"Texto: {processed_no_info.texto_segmento}")
        print("-" * 20)
