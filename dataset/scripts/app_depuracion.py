import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

# Importaciones locales (deben estar en el mismo directorio o PYTHONPATH configurado)
from .chunking_strategies import get_chunking_strategy
from .data_models import ProcessedContentItem, BatchContext
from .converters import convert_file_to_markdown
from .processors import process_text_content, parse_publication_date
from .utils import save_to_ndjson, get_nested_value, clean_filename, filter_and_extract_from_json_object

# Para validación de esquemas
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema library not found. Configuration validation will be skipped.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuración (Reemplazar con un sistema de configuración más robusto si es necesario) ---
# Esta configuración ahora se enfoca más en cómo procesar lotes que en definir la estructura
# de salida, ya que eso lo define ProcessedContentItem.
# Las rutas para filtrado y extracción de texto en JSONs complejos se pasarían
# a través de BatchContext o configuraciones específicas por autor/tipo de origen.

DEFAULT_CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_DATASET_CONFIG_FILE = Path(__file__).parent.parent / "config.json" # dataset/config.json

# --- Rutas de Configuración y Esquemas ---
# Directorio base para las configuraciones del dataset
CONFIG_DIR = Path(__file__).parent.parent / "config" # dataset/config/

# Archivos de configuración principales (los que usa la aplicación)
CONTENT_PROFILES_FILE = CONFIG_DIR / "content_profiles.json"
JOBS_CONFIG_FILE = CONFIG_DIR / "jobs_config.json"

# Archivos de esquema para validación
CONTENT_PROFILES_SCHEMA_FILE = CONFIG_DIR / "schema" / "content_profiles.schema.json"
JOBS_CONFIG_SCHEMA_FILE = CONFIG_DIR / "schema" / "jobs_config.schema.json"

RAW_DATA_BASE_DIR = CONFIG_DIR.parent / "raw_data" # dataset/raw_data/

def load_config(config_path: Path = DEFAULT_CONFIG_FILE) -> Dict[str, Any]:
    """Carga la configuración JSON."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Configuration file {config_path} not found. Using empty config.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {config_path}. Using empty config.")
        return {}

# Cargar configuraciones
# script_config = load_config() # dataset/scripts/config.json
# dataset_config = load_config(DEFAULT_DATASET_CONFIG_FILE) # dataset/config.json

# output_base_dir = Path(dataset_config.get("paths", {}).get("processed_unified_path", "processed_data/unified"))
# output_base_dir.mkdir(parents=True, exist_ok=True)


# --- Funciones de Carga y Validación de Configuración ---

def load_json_file(file_path: Path, description: str = "JSON file") -> Optional[Any]:
    """Carga un archivo JSON y devuelve su contenido, o None si hay un error."""
    if not file_path.exists():
        logger.error(f"{description.capitalize()} not found at {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"{description.capitalize()} loaded successfully from {file_path}")
        return data
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}. Please ensure it's valid JSON.")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading {file_path}: {e}")
        return None

def validate_config(data: Any, schema: Dict[str, Any], config_name: str) -> bool:
    """Valida los datos de configuración contra un esquema JSON."""
    if not JSONSCHEMA_AVAILABLE:
        logger.warning(f"Skipping validation for {config_name} as jsonschema library is not available.")
        return True # Asumir válido si no se puede validar

    if data is None or schema is None:
        logger.error(f"Cannot validate {config_name}: data or schema is missing.")
        return False

    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.info(f"{config_name} is valid according to the schema.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Validation error in {config_name}: {e.message} (Path: {list(e.path)})")
        # Podrías imprimir e.context para más detalles del error si es necesario
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during {config_name} validation: {e}")
        return False

# --- Lógica de Procesamiento de JSON/NDJSON Complejos ---

def process_single_file(
    file_path: Path,
    profile_cfg: Dict[str, Any],
    batch_ctx: BatchContext,
) -> List[ProcessedContentItem]:
    """
    Convierte el archivo a Markdown, lo trocea con la estrategia indicada
    y transforma cada chunk en ProcessedContentItem.
    (Por ahora cubre archivos normales; json_like se añadirá después.)
    """
    profile_description = profile_cfg.get("description", "Nombre de perfil no encontrado")
    logger.info(f"→ Procesando {file_path.name} con perfil «{profile_description}»")

    path = file_path # Para consistencia con el código nuevo
    specific_source_name = path.name
    items: List[ProcessedContentItem] = []

    # 1) Conversión a Markdown (solo si no es json_like)
    if profile_cfg.get("source_format_group") != "json_like":
        md_text, conv_meta = convert_file_to_markdown(
            str(path),
            profile_cfg.get("converter_config", {}),
        )
        if not md_text:
            logger.warning(f"Conversión vacía; se omite {path.name}")
            return items
        
        # 2) Instanciar estrategia de chunking
        strat_name = profile_cfg.get("chunking_strategy_name")
        if not strat_name:
            logger.error(f"No se encontró 'chunking_strategy_name' en el perfil '{profile_description}' para {path.name}. Se omite archivo.")
            return items
            
        chunk_cfg = profile_cfg.get("chunking_config", {})
        try:
            chunker = get_chunking_strategy(strat_name, chunk_cfg)
        except ValueError as e:
            logger.error(f"Error al instanciar la estrategia de chunking '{strat_name}' para {path.name}: {e}. Se omite archivo.")
            return items

        # 3) Recorrer cada chunk y post‑procesar
        content_to_chunk = md_text
        chunk_iterator = chunker.chunk(content_to_chunk, str(path), profile_cfg) # Pasando profile_cfg al chunker
        
        for i, raw_chunk in enumerate(chunk_iterator):
            text_for_processing = ""
            raw_ndjson_for_processing = None

            if isinstance(raw_chunk, dict) and "text_content" in raw_chunk:
                text_for_processing = raw_chunk["text_content"]
            elif isinstance(raw_chunk, str): # Algunas estrategias de chunking pueden devolver solo texto
                text_for_processing = raw_chunk
            elif isinstance(raw_chunk, dict):
                # Esto podría ser para JsonObjectAsItemStrategy si devuelve el objeto directamente
                # pero el código de reemplazo para json_like ya maneja la iteración de objetos JSON
                # Esta rama podría necesitar ajuste si JsonObjectAsItemStrategy no pone 'text_content'
                logger.warning(f"Chunk {i} para {path.name} es un dict pero no tiene 'text_content'. Dependerá de process_text_content.")
                # Si es json_like, este camino no debería tomarse.
                # Si no es json_like y es un dict sin 'text_content', es un caso no manejado bien.
                raw_ndjson_for_processing = raw_chunk # Asumir que process_text_content lo maneja
            else:
                logger.warning(f"Chunk {i} para {path.name} no es un formato esperado (dict con text_content o str). Saltando chunk. Chunk: {type(raw_chunk)}")
                continue

            content_fields = process_text_content(
                markdown_text=text_for_processing,
                file_path=str(path),
                metadata_from_converter=conv_meta,
                raw_ndjson_object=raw_ndjson_for_processing,
                force_null_publication_date=batch_ctx.force_null_publication_date,
                parser_config=profile_cfg.get("parser_config") # Pasar parser_config
            )

            item = ProcessedContentItem(
                author_name=batch_ctx.author_name,
                origin_type_name=batch_ctx.origin_type_name,
                specific_source_name=specific_source_name,
                original_file_path_or_url=str(path.resolve()),
                acquisition_date=batch_ctx.acquisition_date,
                title=content_fields.title,
                normalized_text_md=content_fields.markdown_text,
                publication_date=content_fields.publication_date_iso,
                language_code=batch_ctx.language_code,
                source_document_pointer=content_fields.source_document_pointer,
                additional_metadata_json=content_fields.additional_metadata,
                original_content_id=content_fields.original_content_id
            )
            items.append(item)
    else:
        # ---- flujo JSON/NDJSON ----
        parser_cfg = profile_cfg.get("parser_config", {})
        text_paths   = parser_cfg.get("text_property_paths", [])
        # filter_rules se llama 'filter_rules_schema' en content_profiles.example.json para el parser_config.
        # Aquí se espera filter_rules directamente. Ajustar según la estructura real o el schema.
        # Asumo que el jobs_config.json o el content_profile puede tener un 'filter_rules' directo.
        # Si no, parser_cfg.get("filter_rules_schema") podría ser lo que se necesita procesar.
        # Por ahora, sigo la instrucción literal.
        json_filter_rules = parser_cfg.get("filter_rules", []) # 'filter_rules' directamente, no 'filter_rules_schema'
        
        # Similar para pointer_path y date_path, deben estar en parser_config directamente
        # o dentro de un sub-diccionario como "metadata_paths" que se ve en el example.json
        # "metadata_paths": { "publication_date": "date", "author_name": "from", "title": "message_id" }
        # Necesitaríamos extraer de metadata_paths si esa es la estructura.
        # Por ahora, se asume que están en el nivel superior de parser_cfg según el código provisto.
        pointer_path = parser_cfg.get("pointer_path") # ej. "id"
        date_path    = parser_cfg.get("date_path")    # ej. "date"

        for json_obj in _iterate_json_objects(path): # path es file_path
            extracted = filter_and_extract_from_json_object(
                json_obj,
                text_property_paths=text_paths,
                filter_rules=json_filter_rules, # Pasando las reglas de filtro
                default_pointer_path=pointer_path,
                default_date_path=date_path,
            )
            if not extracted:
                continue  # filtrado

            # El texto ya está extraído por filter_and_extract_from_json_object
            md_text_from_json = extracted["text"]
            
            # Aquí conv_meta solo indica que vino de JSON, no hay conversión de archivo.
            conv_meta_for_json = {"converter_notes": "from_json_like", "source_title": path.stem}
            if extracted.get("title"): # Si filter_and_extract_from_json_object encontró un título
                 conv_meta_for_json["source_title"] = extracted.get("title")


            # process_text_content procesará el md_text_from_json y usará raw_ndjson_object para metadatos adicionales
            processed_fields = process_text_content( # Cambiado de 'meta' a 'processed_fields' para evitar confusión
                markdown_text=md_text_from_json,
                file_path=str(path), # Path del archivo JSON/NDJSON original
                metadata_from_converter=conv_meta_for_json, # Metadatos básicos de esta etapa
                raw_ndjson_object=json_obj, # El objeto JSON completo para extracción profunda de metadatos
                force_null_publication_date=batch_ctx.force_null_publication_date,
                parser_config=parser_cfg # Pasar el parser_config para que process_text_content sepa cómo extraer metadatos
            )

            # Intentar parsear la fecha candidata extraída por filter_and_extract_from_json_object
            # si process_text_content no pudo obtener una fecha de publicación.
            final_publication_date = processed_fields.publication_date_iso
            if not final_publication_date and extracted.get("date_candidate"):
                final_publication_date = parse_publication_date(
                    str(extracted["date_candidate"]), # Asegurar que es string
                    force_null=batch_ctx.force_null_publication_date
                    )

            # Usar el puntero extraído por filter_and_extract_from_json_object si existe,
            # sino el que pudo encontrar process_text_content.
            final_source_pointer = extracted.get("pointer") or processed_fields.source_document_pointer
            # Podríamos añadir un fallback si ninguno lo encuentra: f"{specific_source_name}_item_{i}" si tuviéramos un índice

            item = ProcessedContentItem(
                author_name=batch_ctx.author_name,
                origin_type_name=batch_ctx.origin_type_name,
                specific_source_name=specific_source_name, # Nombre del archivo JSON/NDJSON
                original_file_path_or_url=str(path.resolve()),
                acquisition_date=batch_ctx.acquisition_date,
                title=processed_fields.title or conv_meta_for_json.get("source_title"), # Usar título de conv_meta si no hay otro
                normalized_text_md=processed_fields.markdown_text, # Este es el md_text_from_json procesado
                publication_date=final_publication_date,
                language_code=batch_ctx.language_code,
                source_document_pointer=final_source_pointer,
                additional_metadata_json=processed_fields.additional_metadata,
                original_content_id=processed_fields.original_content_id # o extracted.get("id_field") si hay uno estándar
            )
            items.append(item)

    if not items:
        logger.info(f"No se generaron items procesables para {path.name} con perfil '{profile_description}'.")

    return items


def process_author_files(
    author_name: str,
    source_directory: Path,
    output_directory: Path,
    batch_context: BatchContext,
    current_content_profile: Dict[str, Any], # <--- Argumento añadido
) -> List[ProcessedContentItem]:
    """
    Procesa todos los archivos de un directorio fuente para un autor dado,
    utilizando un perfil de contenido específico.
    """
    items_for_this_job: List[ProcessedContentItem] = [] # Renombrado de processed_items
    if not source_directory.is_dir():
        logger.error(f"Directorio fuente para {author_name} no encontrado: {source_directory}")
        return items_for_this_job

    logger.info(f"Iniciando procesamiento para autor: {author_name} en dir: {source_directory} usando perfil: {current_content_profile.get('description', 'N/A')}")

    for file_entry in source_directory.rglob("*"):
        if file_entry.is_file():
            # Llamada actualizada a process_single_file
            processed_file_items = process_single_file(
                file_path=file_entry,
                profile_cfg=current_content_profile, # Pasar el perfil completo
                batch_ctx=batch_ctx
            )
            items_for_this_job.extend(processed_file_items)
        
    if items_for_this_job:
        safe_author_name = clean_filename(author_name)
        # El nombre del archivo de salida podría incluir el nombre del perfil o job_id para unicidad si es necesario
        output_file_name_parts = [safe_author_name]
        if batch_context.job_id: # Si tenemos un job_id en el contexto
             output_file_name_parts.append(clean_filename(batch_context.job_id))
        output_file_name_parts.append("unified.ndjson")
        
        output_file = output_directory / "_".join(filter(None,output_file_name_parts))
        
        save_to_ndjson([item.__dict__ for item in items_for_this_job], str(output_file))
        logger.info(f"Procesamiento finalizado para {author_name} (Job: {batch_context.job_id or 'N/A'}). {len(items_for_this_job)} items guardados en {output_file}")
    else:
        logger.info(f"No se encontraron items procesables para {author_name} (Job: {batch_context.job_id or 'N/A'}) en {source_directory} con el perfil aplicado.")
        
    return items_for_this_job


def main():
    """
    Función principal para ejecutar el pipeline de depuración y procesamiento.
    Esto simulará lo que una UI de AppDepuration podría configurar y disparar.
    """
    logger.info("Starting Biblioperson Data Depuration and Processing App...")

    # --- Simulación de configuración de la UI / Lotes de Procesamiento ---
    # Esto vendría de la UI o de un archivo de configuración de lotes.
    
    # Directorio base donde están los datos crudos por autor
    # Asumir una estructura como: raw_data_base_dir/AUTHOR_NAME/files...
    # Esta ruta debería venir de dataset/config.json
    dataset_root_config = load_config(DEFAULT_DATASET_CONFIG_FILE)
    raw_data_base_dir = Path(dataset_root_config.get("paths", {}).get("raw_data_path", "raw_data"))
    processed_unified_output_dir = Path(dataset_root_config.get("paths", {}).get("processed_unified_path", "processed_data/unified"))
    processed_unified_output_dir.mkdir(parents=True, exist_ok=True)

    # Configuración de los lotes a procesar:
    # Cada elemento es un "trabajo" que la UI configuraría.
    processing_jobs = [
        {
            "author_name": "Ismael",
            "language_code": "es",
            "origin_type_name": "Telegram Archive", # Tipo general para estos archivos
            "source_directory_name": "ismael_telegram_json", # Subcarpeta dentro de raw_data_base_dir
            "acquisition_date": "2024-01-15", # Opcional
            "force_null_publication_date": False,
            "json_config": { # Reglas para los JSON de Ismael
                "text_property_paths": ["texto", "message", "data.text"], # Intentar estas rutas en orden
                "filter_rules": [
                    {"path": "autor", "value": "Ismael"}, # Si el JSON tuviera un campo 'autor'
                    # {"path": "from_id", "value": "user12345"} # Ejemplo de Telegram
                ],
                "pointer_path": "id", # Campo para source_document_pointer
                "date_path": "fecha"  # Campo para publication_date
            }
        },
        {
            "author_name": "Ellen G. White",
            "language_code": "es",
            "origin_type_name": "EGW Digital Library TXT",
            "source_directory_name": "egw_txt_files",
            "force_null_publication_date": True, # Para EGW, la fecha del archivo no es la de publicación
             "json_config": { # EGW ejemplo si viniera de NDJSON con estructura particular
                "text_property_paths": ["texto"],
                "pointer_path": "contexto", # Que es la referencia tipo {PVGM 1.2}
                "date_path": None # No hay fecha en sus NDJSON de ejemplo
            }
        },
        {
            "author_name": "Documentos Varios",
            "language_code": "es",
            "origin_type_name": "Local DOCX", # O "Local PDF", etc.
            "source_directory_name": "mis_documentos_docx",
            # No json_config si son archivos DOCX, PDF, etc. directos
        }
    ]

    all_processed_items_count = 0
    for job_config in processing_jobs:
        author = job_config["author_name"]
        lang = job_config["language_code"]
        origin_type = job_config["origin_type_name"]
        source_dir_name = job_config["source_directory_name"]
        
        current_source_path = raw_data_base_dir / source_dir_name
        if not current_source_path.exists() or not current_source_path.is_dir():
            logger.warning(f"Source directory {current_source_path} for author {author} not found. Skipping job.")
            continue

        batch_ctx = BatchContext(
            author_name=author,
            language_code=lang,
            origin_type_name=origin_type,
            acquisition_date=job_config.get("acquisition_date"),
            force_null_publication_date=job_config.get("force_null_publication_date", False)
        )
        
        author_json_cfg = job_config.get("json_config")

        items = process_author_files(
            author_name=author,
            source_directory=current_source_path,
            output_directory=processed_unified_output_dir,
            batch_context=batch_ctx,
            current_content_profile=author_json_cfg
        )
        all_processed_items_count += len(items)

    logger.info(f"All processing jobs finished. Total items processed and saved: {all_processed_items_count}")

def _iterate_json_objects(file_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Iterates over JSON objects in a file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)

if __name__ == '__main__':
    # Crear archivos de configuración vacíos si no existen, para evitar errores en el primer run.
    # Esto es útil para el desarrollo inicial.
    if not CONTENT_PROFILES_FILE.exists():
        logger.info(f"{CONTENT_PROFILES_FILE} not found. Creating an empty JSON object file.")
        with open(CONTENT_PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)

    if not JOBS_CONFIG_FILE.exists():
        logger.info(f"{JOBS_CONFIG_FILE} not found. Creating an empty JSON array file.")
        with open(JOBS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
            
    run_etl_pipeline()