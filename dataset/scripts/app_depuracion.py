import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

# Importaciones locales
from dataset.processing.profile_manager import ProfileManager 
from .data_models import ProcessedContentItem, BatchContext 
from .utils import get_nested_value, clean_filename, filter_and_extract_from_json_object 


# Para validación de esquemas
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema library not found. Configuration validation will be skipped.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Rutas de Configuración y Esquemas ---
project_root = Path(__file__).resolve().parents[2]
config_dir = project_root / "dataset" / "config"
schema_dir = config_dir / "schema"
profiles_dir = config_dir / "profiles"
RAW_DATA_BASE_DIR = project_root / "dataset" / "raw_data"
OUTPUT_BASE_DIR = project_root / "dataset" / "output"
CONTENT_PROFILES_FILE = config_dir / "content_profiles.json"
JOBS_CONFIG_FILE = config_dir / "jobs_config.json"
CONTENT_PROFILES_SCHEMA_FILE = schema_dir / "content_profiles.schema.json"
JOBS_CONFIG_SCHEMA_FILE = schema_dir / "jobs_config.schema.json"


# --- Funciones de Carga y Validación de Configuración ---
def load_config(config_path: Path = Path(__file__).parent / "config.json") -> Dict[str, Any]:
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
        return True 

    if data is None or schema is None:
        logger.error(f"Cannot validate {config_name}: data or schema is missing.")
        return False

    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.info(f"{config_name} is valid according to the schema.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Validation error in {config_name}: {e.message} (Path: {list(e.path)})")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during {config_name} validation: {e}")
        return False


# --- Lógica de Procesamiento Principal Refactorizada ---
def main():
    """
    Función principal para ejecutar el pipeline de procesamiento utilizando ProfileManager.
    """
    logger.info("Iniciando el proceso de depuración y datos...")
    
    content_profiles_schema = load_json_file(CONTENT_PROFILES_SCHEMA_FILE, "Content Profiles Schema")
    jobs_config_schema = load_json_file(JOBS_CONFIG_SCHEMA_FILE, "Jobs Config Schema")
    
    content_profiles_data = load_json_file(CONTENT_PROFILES_FILE, "Content Profiles")
    jobs_config_data = load_json_file(JOBS_CONFIG_FILE, "Jobs Config")

    if jobs_config_data is None:
        return

    profile_manager = ProfileManager(profiles_dir)

    jobs_to_process = [job for job in jobs_config_data if job.get("enabled", True)]

    if not jobs_to_process:
        logger.info("No hay trabajos configurados o habilitados para procesar en jobs_config.json.")
        return

    for job_config in jobs_to_process:
        job_id = job_config.get("job_id")
        author_name = job_config.get("author_name")
        origin_type_name = job_config.get("origin_type_name")
        source_directory_name = job_config.get("source_directory_name") 
        profile_name_from_job = job_config.get("content_profile_name") 

        if not all([job_id, author_name, origin_type_name, source_directory_name is not None, profile_name_from_job]):
            logger.error(f"Configuración de job incompleta para job_id '{job_id}'. Faltan campos clave (author_name, origin_type_name, source_directory_name, content_profile_name). Saltando job.")
            continue

        logger.info(f"Procesando job: {job_id} - Perfil: {profile_name_from_job}")

        input_dir = RAW_DATA_BASE_DIR / source_directory_name
        output_subdir = OUTPUT_BASE_DIR / author_name / origin_type_name / job_id
        output_subdir.mkdir(parents=True, exist_ok=True)

        if not input_dir.is_dir():
            logger.warning(f"Directorio de entrada no encontrado para el job '{job_id}': {input_dir}. Saltando job.")
            continue

        processed_files_count = 0
        for input_file_path in input_dir.glob("*"):
            if input_file_path.is_file():
                logger.info(f"Procesando archivo: {input_file_path.name} para el job {job_id}")
                try:
                    profile_manager.process_file(
                        file_path=str(input_file_path),
                        profile_name=profile_name_from_job,
                        job_config_dict=job_config,
                        output_dir=str(output_subdir) 
                    )
                    processed_files_count += 1
                except Exception as e:
                    logger.error(f"Error procesando el archivo {input_file_path.name} para el job {job_id}: {e}", exc_info=True)
            
        if processed_files_count == 0:
            logger.info(f"No se encontraron archivos para procesar en {input_dir} para el job {job_id}.")
        else:
            logger.info(f"Job {job_id} completado. {processed_files_count} archivo(s) procesado(s).")

    logger.info("Todos los jobs han finalizado.")

if __name__ == "__main__":
    for config_file_path in [CONTENT_PROFILES_FILE, JOBS_CONFIG_FILE, CONTENT_PROFILES_SCHEMA_FILE, JOBS_CONFIG_SCHEMA_FILE]:
        if not config_file_path.exists():
            config_file_path.parent.mkdir(parents=True, exist_ok=True)
            if "schema" in config_file_path.name: 
                 config_file_path.write_text("{}", encoding='utf-8')
            elif "jobs_config" in config_file_path.name: 
                 config_file_path.write_text("{\"jobs\": []}", encoding='utf-8')
            else: 
                 config_file_path.write_text("{}", encoding='utf-8') 
            logger.info(f"Creado archivo de configuración vacío: {config_file_path}")
    
    OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True) 

    main()