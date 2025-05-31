import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
import dataclasses
from datetime import datetime, timezone
import uuid
import importlib

from langdetect import detect, LangDetectException
from dataset.scripts.data_models import ProcessedContentItem, BatchContext

# RECARGA FORZADA DE MÓDULOS MODIFICADOS
import dataset.processing.segmenters.heading_segmenter
importlib.reload(dataset.processing.segmenters.heading_segmenter)

from .segmenters.base import BaseSegmenter
from .segmenters.verse_segmenter import VerseSegmenter
from .segmenters.heading_segmenter import HeadingSegmenter
from .loaders import BaseLoader, MarkdownLoader, NDJSONLoader, JSONLoader, DocxLoader, txtLoader, PDFLoader, ExcelLoader, CSVLoader
from .pre_processors import CommonBlockPreprocessor

# A medida que se implementen, importar otros componentes:
# from .loaders.base import BaseLoader
# from .exporters.base import BaseExporter
# etc.

class ProfileManager:
    """
    Gestor del sistema de perfiles de procesamiento.
    
    Esta clase coordina todo el pipeline de procesamiento:
    - Carga de perfiles YAML
    - Selección del loader adecuado
    - Inicialización de segmentadores con sus configuraciones
    - Ejecución de post-procesadores
    - Exportación de resultados
    """
    
    def __init__(self, profiles_dir: str = None):
        """
        Inicializa el gestor de perfiles.
        
        Args:
            profiles_dir: Directorio donde se encuentran los perfiles YAML
        """
        self.logger = logging.getLogger(__name__)
        
        # Directorio de perfiles por defecto
        if profiles_dir is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            profiles_dir = os.path.join(os.path.dirname(module_dir), 'config', 'profiles')
        
        self.profiles_dir = profiles_dir
        self.profiles = {}
        self._segmenter_registry = {}
        self._loader_registry = {}
        
        # Registrar componentes disponibles
        self.register_default_components()
        
        # Cargar perfiles desde directorio
        self.load_profiles()
    
    def reload_custom_segmenters(self):
        """Recarga los segmentadores personalizados. Útil después de generar nuevos segmentadores."""
        self.logger.info("Recargando segmentadores personalizados...")
        self._load_custom_segmenters()
    
    def register_default_components(self):
        """Registra los componentes por defecto del sistema."""
        # Registrar segmentadores
        self.register_segmenter('verse', VerseSegmenter)
        self.register_segmenter('heading', HeadingSegmenter)
        
        # Cargar segmentadores personalizados dinámicamente
        self._load_custom_segmenters()
        
        # Registrar loaders
        self.register_loader('.md', MarkdownLoader)
        self.register_loader('.markdown', MarkdownLoader)
        self.register_loader('.ndjson', NDJSONLoader)
        self.register_loader('.docx', DocxLoader)
        self.register_loader('.txt', txtLoader)
        self.register_loader('.pdf', PDFLoader)
        self.register_loader('.xls', ExcelLoader)
        self.register_loader('.xlsx', ExcelLoader)
        self.register_loader('.xlsm', ExcelLoader)
        self.register_loader('.csv', CSVLoader)  # Usando CSVLoader específico para CSV
        self.register_loader('.tsv', CSVLoader)  # También para archivos TSV (valores separados por tabulaciones)
        self.register_loader('.json', JSONLoader)
    
    def register_segmenter(self, name: str, segmenter_class: Type[BaseSegmenter]):
        """
        Registra un segmentador en el sistema.
        
        Args:
            name: Nombre para referencia en perfiles
            segmenter_class: Clase del segmentador
        """
        self._segmenter_registry[name] = segmenter_class
        self.logger.debug(f"Registrado segmentador '{name}'")
    
    def register_loader(self, extension: str, loader_class: Type[BaseLoader]):
        """
        Registra un loader para una extensión de archivo.
        
        Args:
            extension: Extensión del archivo (con punto)
            loader_class: Clase del loader
        """
        self._loader_registry[extension.lower()] = loader_class
        self.logger.debug(f"Registrado loader para {extension}")
    
    def _load_custom_segmenters(self):
        """Carga dinámicamente segmentadores personalizados desde el directorio de segmentadores."""
        import importlib.util
        import inspect
        
        # Directorio donde se guardan los segmentadores personalizados
        segmenters_dir = os.path.join(os.path.dirname(__file__), 'segmenters')
        
        if not os.path.exists(segmenters_dir):
            return
        
        # Buscar archivos Python que terminen en '_segmenter.py'
        for filename in os.listdir(segmenters_dir):
            if filename.endswith('_segmenter.py') and filename not in ['base.py', 'verse_segmenter.py', 'heading_segmenter.py']:
                module_path = os.path.join(segmenters_dir, filename)
                module_name = filename[:-3]  # Remover .py
                
                try:
                    # Cargar el módulo dinámicamente
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Buscar clases que hereden de BaseSegmenter
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if (obj != BaseSegmenter and 
                                issubclass(obj, BaseSegmenter) and 
                                hasattr(obj, '__module__') and 
                                obj.__module__ == module_name):
                                
                                # Registrar el segmentador usando el nombre del archivo sin '_segmenter'
                                segmenter_name = module_name.replace('_segmenter', '')
                                self.register_segmenter(segmenter_name, obj)
                                self.logger.info(f"Cargado segmentador personalizado: {segmenter_name} -> {name}")
                                
                except Exception as e:
                    self.logger.warning(f"No se pudo cargar segmentador personalizado {filename}: {str(e)}")
    
    def get_loader_for_file(self, file_path: str, profile_name: str = None) -> Optional[tuple]:
        """
        Obtiene el loader apropiado para un archivo y determina el tipo de contenido.
        
        Args:
            file_path: Ruta al archivo
            profile_name: Nombre del perfil (opcional)
            
        Returns:
            Tuple con (clase del loader, tipo de contenido) o None si no hay loader registrado
        """
        extension = Path(file_path).suffix.lower()
        loader_class = self._loader_registry.get(extension)
        
        if not loader_class:
            self.logger.error(f"No hay loader registrado para extensión: {extension}")
            return None
        
        # Determinar el tipo de contenido basado en el perfil si está disponible
        content_type = 'escritos'  # Valor por defecto
        
        if profile_name and profile_name in self.profiles:
            profile = self.profiles[profile_name]
            
            # Si el perfil especifica un tipo de contenido por defecto, usarlo
            if 'default_content_type' in profile:
                content_type = profile['default_content_type']
            
            # Si el perfil tiene mapeo de extensiones a tipos, usarlo
            elif 'extension_types' in profile and extension in profile['extension_types']:
                content_type = profile['extension_types'][extension]
            
            # O inferir basado en el nombre del perfil
            elif 'poem' in profile_name or 'lyric' in profile_name:
                content_type = 'poemas' if 'poem' in profile_name else 'canciones'
        
        # También podemos intentar inferir del nombre del archivo
        filename = Path(file_path).stem.lower()
        if not profile_name or content_type == 'escritos':
            if any(word in filename for word in ['poema', 'poem', 'verso']):
                content_type = 'poemas'
            elif any(word in filename for word in ['cancion', 'song', 'lyric']):
                content_type = 'canciones'
        
        self.logger.debug(f"Loader para {extension}: {loader_class.__name__}, tipo: {content_type}")
        return (loader_class, content_type)
        
    def load_profiles(self):
        """Carga todos los perfiles YAML del directorio configurado y subcarpetas."""
        if not os.path.exists(self.profiles_dir):
            self.logger.warning(f"Directorio de perfiles no encontrado: {self.profiles_dir}")
            return

        # Cargar perfiles del directorio raíz (compatibilidad)
        self._load_profiles_from_directory(self.profiles_dir)
        
        # Cargar perfiles de subcarpetas (core, special)
        for subdir in ['core', 'special']:
            subdir_path = os.path.join(self.profiles_dir, subdir)
            if os.path.exists(subdir_path):
                self._load_profiles_from_directory(subdir_path, category=subdir)
    
    def _load_profiles_from_directory(self, directory: str, category: str = None):
        """Carga perfiles de un directorio específico."""
        for filename in os.listdir(directory):
            if filename.endswith(('.yaml', '.yml')):
                profile_path = os.path.join(directory, filename)
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile = yaml.safe_load(f)
                    
                    if 'name' in profile:
                        # Agregar categoría al perfil para organización
                        if category:
                            profile['_category'] = category
                        self.profiles[profile['name']] = profile
                        category_info = f" ({category})" if category else ""
                        self.logger.info(f"Cargado perfil: {profile['name']}{category_info}")
                    else:
                        self.logger.warning(f"Perfil sin nombre en {filename}")
                except Exception as e:
                    self.logger.error(f"Error al cargar perfil {filename}: {str(e)}")
    
    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un perfil por su nombre.
        
        Args:
            profile_name: Nombre del perfil
            
        Returns:
            Diccionario con la configuración del perfil o None si no existe
        """
        return self.profiles.get(profile_name)
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        Lista todos los perfiles disponibles.
        
        Returns:
            Lista con información básica de cada perfil
        """
        return [
            {
                'name': profile['name'],
                'description': profile.get('description', ''),
                'segmenter': profile.get('segmenter', 'unknown'),
                'file_types': profile.get('file_types', [])
            }
            for profile in self.profiles.values()
        ]
    
    def create_segmenter(self, profile_name: str) -> Optional[BaseSegmenter]:
        """
        Crea una instancia de segmentador según el perfil.
        
        Args:
            profile_name: Nombre del perfil a usar
            
        Returns:
            Instancia del segmentador configurada o None si hay error
        """
        profile = self.get_profile(profile_name)
        if not profile:
            self.logger.error(f"Perfil no encontrado: {profile_name}")
            return None
        
        segmenter_type = profile.get('segmenter')
        if not segmenter_type:
            self.logger.error(f"Tipo de segmentador no especificado en perfil: {profile_name}")
            return None
        
        if segmenter_type not in self._segmenter_registry:
            self.logger.error(f"Segmentador '{segmenter_type}' no registrado")
            return None
        
        # Configuración para el segmentador
        config = {}
        
        # Usar configuración específica del segmentador si existe
        if 'segmenter_config' in profile:
            config.update(profile['segmenter_config'])
        
        # Mantener compatibilidad con configuración legacy
        # Copiar thresholds del perfil (si no están en segmenter_config)
        if 'thresholds' in profile and 'thresholds' not in config:
            config['thresholds'] = profile['thresholds']
        
        # Copiar patrones específicos (si no están en segmenter_config)
        for key in ['title_patterns', 'paragraph_patterns', 'section_patterns']:
            if key in profile and key not in config:
                config[key] = profile[key]
        
        # Crear instancia del segmentador
        try:
            segmenter_class = self._segmenter_registry[segmenter_type]
            return segmenter_class(config)
        except Exception as e:
            self.logger.error(f"Error al crear segmentador '{segmenter_type}': {str(e)}")
            return None
    
    def process_file(self, 
                    file_path: str, 
                    profile_name: str, 
                    output_dir: Optional[str] = None,
                    encoding: str = 'utf-8',
                    force_content_type: Optional[str] = None,
                    confidence_threshold: float = 0.5,
                    job_config_dict: Optional[Dict[str, Any]] = None,
                    language_override: Optional[str] = None,
                    author_override: Optional[str] = None,
                    output_format: str = "ndjson",
                    folder_structure_info: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Procesa un archivo completo usando un perfil.
        
        Args:
            file_path: Ruta al archivo a procesar
            profile_name: Nombre del perfil a usar
            output_dir: Directorio para guardar resultados (opcional)
            encoding: Codificación para abrir el archivo (por defecto utf-8)
            force_content_type: Forzar un tipo específico de contenido (ignora detección automática)
            confidence_threshold: Umbral de confianza para detección de poemas (0.0-1.0)
            job_config_dict: Diccionario con la configuración del job actual (opcional)
            language_override: Código de idioma para override (opcional)
            author_override: Nombre del autor para override (opcional)
            output_format: Formato de salida ("ndjson" o "json")
            folder_structure_info: Información sobre la estructura de carpetas del archivo (opcional)
            
        Returns:
            Tuple con: (Lista de unidades procesadas, Estadísticas del segmentador, Metadatos del documento)
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Archivo no encontrado: {file_path}")
            # Devolver la estructura de tupla esperada por process_file.py
            return [], {}, {'error': f"Archivo no encontrado: {file_path}"}
        
        # 1. Obtener loader apropiado y tipo de contenido
        loader_result = self.get_loader_for_file(file_path, profile_name)
        if not loader_result:
            return [], {}, {'error': f"No se pudo obtener el loader para: {file_path}"}
            
        loader_class, content_type = loader_result
        
        # Si el usuario forzó un tipo específico, usarlo
        if force_content_type:
            self.logger.info(f"Forzando tipo de contenido: {force_content_type}")
            content_type = force_content_type
            
        # 2. Crear loader e intentar cargar el archivo
        raw_blocks: List[Dict[str, Any]] = []
        raw_document_metadata: Dict[str, Any] = {}
        try:
            self.logger.info(f"Usando loader: {loader_class.__name__}")
            
            # Si es JSONLoader y el perfil tiene configuración JSON, usarla
            loader_kwargs = {'encoding': encoding}
            if loader_class.__name__ == 'JSONLoader':
                profile = self.get_profile(profile_name)
                if profile and 'json_config' in profile:
                    json_config = profile['json_config']
                    self.logger.info(f"Aplicando configuración JSON del perfil: {profile_name}")
                    loader_kwargs.update(json_config)
            
            loader = loader_class(file_path, **loader_kwargs)
            loaded_data = loader.load()
            
            # Asegurar que las claves existan, incluso si están vacías
            raw_blocks = loaded_data.get('blocks', [])
            raw_document_metadata = loaded_data.get('document_metadata', {})
            raw_document_metadata.setdefault('source_file_path', str(Path(file_path).absolute()))
            raw_document_metadata.setdefault('file_format', Path(file_path).suffix.lower())

            # === AGREGAR INFORMACIÓN DE ESTRUCTURA DE CARPETAS ===
            if folder_structure_info:
                # Agregar información de estructura de carpetas a los metadatos del documento
                raw_document_metadata.update({
                    "folder_structure": folder_structure_info
                })
                self.logger.debug(f"Información de estructura de carpetas agregada a metadatos: {folder_structure_info}")

            # Si el loader reportó un error, lo propagamos antes del pre-procesamiento
            if raw_document_metadata.get('error'):
                self.logger.error(f"Error reportado por loader {loader_class.__name__} para {file_path}: {raw_document_metadata['error']}")
                return [], {}, raw_document_metadata

            if not raw_blocks and not raw_document_metadata.get('warning'): # Si no hay bloques y no es una advertencia de archivo vacío
                self.logger.info(f"Loader {loader_class.__name__} no devolvió bloques para {file_path} y no hay advertencia de archivo vacío.")

        except Exception as e:
            self.logger.error(f"Excepción al instanciar o usar loader {loader_class.__name__} para archivo {file_path}: {str(e)}", exc_info=True)
            error_metadata = {
                'source_file_path': str(Path(file_path).absolute()),
                'file_format': Path(file_path).suffix.lower(),
                'error': f"Excepción en ProfileManager durante la carga con loader: {str(e)}"
            }
            return [], {}, error_metadata
        
        # 2.5 Aplicar Pre-procesador Común
        # Obtener configuración del preprocesador desde el perfil YAML
        profile = self.get_profile(profile_name)
        
        # ===== IDENTIFICADOR ÚNICO ProfileManager V2.0 =====
        self.logger.warning("💥💥💥 PROFILE MANAGER V2.0 - SOLUCIÓN ESPACIOS MÚLTIPLES ACTIVA 💥💥💥")
        print("💥💥💥 PROFILE MANAGER V2.0 - SOLUCIÓN ESPACIOS MÚLTIPLES ACTIVA 💥💥💥")
        
        preprocessor_config = profile.get('pre_processor_config') if profile else None
        self.logger.warning(f"💥 CONFIG PARA CREAR PREPROCESSOR: {preprocessor_config}")
        print(f"💥 CONFIG PARA CREAR PREPROCESSOR: {preprocessor_config}")
        
        # FORZAR RECARGA DE COMMONBLOCKPREPROCESSOR PARA EVITAR CACHE
        import importlib
        import dataset.processing.pre_processors.common_block_preprocessor
        importlib.reload(dataset.processing.pre_processors.common_block_preprocessor)
        from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
        
        common_preprocessor = CommonBlockPreprocessor(config=preprocessor_config)
        try:
            # Debug: verificar que el hash esté presente antes del preprocessor
            hash_before_preprocessor = raw_document_metadata.get("hash_documento_original")
            self.logger.debug(f"hash_documento_original antes del preprocessor: '{hash_before_preprocessor}' (tipo: {type(hash_before_preprocessor)})")
            self.logger.info(f"Aplicando CommonBlockPreprocessor a {len(raw_blocks)} bloques.")
            processed_blocks, processed_document_metadata = common_preprocessor.process(raw_blocks, raw_document_metadata)
            self.logger.debug(f"CommonBlockPreprocessor finalizado. Bloques resultantes: {len(processed_blocks)}.")
            # Debug: verificar que el hash se preserve después del preprocessor
            hash_after_preprocessor = processed_document_metadata.get("hash_documento_original")
            self.logger.debug(f"hash_documento_original después del preprocessor: '{hash_after_preprocessor}' (tipo: {type(hash_after_preprocessor)})")
        except Exception as e:
            self.logger.error(f"Excepción durante CommonBlockPreprocessor para archivo {file_path}: {str(e)}", exc_info=True)
            # Si el preprocesador falla, usamos los datos crudos del loader pero añadimos un error
            existing_error = raw_document_metadata.get('error', '') or ''
            raw_document_metadata['error'] = (existing_error + 
                                             f"; Excepción en CommonBlockPreprocessor: {str(e)}").strip('; ')
            # Devolver datos crudos del loader con el error del preprocesador añadido
            return raw_blocks, {}, raw_document_metadata 

        # Si el preprocesador marcó un error, lo propagamos.
        # Los errores del loader ya se manejaron, así que esto sería un error del preprocesador.
        if processed_document_metadata.get('error'):
            self.logger.error(f"Error reportado por CommonBlockPreprocessor para {file_path}: {processed_document_metadata['error']}")
            return [], {}, processed_document_metadata
            
        # 3. Crear segmentador según perfil
        profile = self.get_profile(profile_name) # Recargar perfil por si se modificó
        segmenter = self.create_segmenter(profile_name)
        if not segmenter:
            # Si no se pudo crear el segmentador, devolver los bloques pre-procesados con un error.
            existing_error = processed_document_metadata.get('error', '') or ''
            processed_document_metadata['error'] = (existing_error + 
                                                 f"; No se pudo crear el segmentador '{profile.get('segmenter') if profile else 'desconocido'}' para el perfil '{profile_name}'").strip('; ')
            return processed_blocks, {}, processed_document_metadata
        
        # Configurar umbral de confianza si el segmentador lo soporta
        if hasattr(segmenter, 'set_confidence_threshold'):
            segmenter.set_confidence_threshold(confidence_threshold)
            self.logger.debug(f"Umbral de confianza establecido a: {confidence_threshold}")
        
        # 4. Segmentar contenido (usando los bloques pre-procesados)
        self.logger.info(f"Segmentando archivo: {file_path} con {len(processed_blocks)} bloques pre-procesados.")
        segments = segmenter.segment(blocks=processed_blocks)
        segmenter_stats = segmenter.get_stats() if hasattr(segmenter, 'get_stats') else {}
        
        # 4.1. Detectar idioma del documento (o usar override)
        detected_lang = None
        if language_override:
            # Validar código de idioma antes de usarlo
            if len(language_override.strip()) < 2 or len(language_override.strip()) > 5:
                self.logger.warning(f"Código de idioma inválido: '{language_override}' (debe tener 2-5 caracteres). Usando detección automática.")
                # No asignar detected_lang, continuar con detección automática
            elif any(char.isdigit() or not char.isalnum() for char in language_override.strip() if char != '-'):
                self.logger.warning(f"Código de idioma contiene caracteres inválidos: '{language_override}'. Usando detección automática.")
                # No asignar detected_lang, continuar con detección automática  
            else:
                detected_lang = language_override.strip().lower()
                self.logger.info(f"Usando idioma forzado para {file_path}: {detected_lang}")
        elif processed_blocks:
            try:
                # Concatenar texto de los primeros bloques para obtener una muestra representativa
                sample_texts = []
                total_chars = 0
                max_chars = 1000  # Límite de caracteres para la muestra
                max_blocks = 5    # Máximo número de bloques a usar
                
                for i, block in enumerate(processed_blocks[:max_blocks]):
                    if total_chars >= max_chars:
                        break
                    
                    block_text = ""
                    if isinstance(block, dict):
                        # Extraer texto del bloque según su estructura
                        block_text = block.get('text', '') or block.get('content', '') or str(block.get('cleaned_text', ''))
                    else:
                        block_text = str(block)
                    
                    if block_text.strip():
                        remaining_chars = max_chars - total_chars
                        if len(block_text) > remaining_chars:
                            block_text = block_text[:remaining_chars]
                        sample_texts.append(block_text.strip())
                        total_chars += len(block_text)
                
                sample_text = " ".join(sample_texts).strip()
                
                # Intentar detectar idioma si hay suficiente texto
                if len(sample_text) >= 20:  # Mínimo de caracteres para detección confiable
                    detected_lang = detect(sample_text)
                    self.logger.info(f"Idioma detectado automáticamente para {file_path}: {detected_lang}")
                else:
                    self.logger.debug(f"Texto insuficiente para detección de idioma en {file_path} (solo {len(sample_text)} caracteres)")
                    detected_lang = "und"
                    
            except LangDetectException as e:
                self.logger.debug(f"No se pudo detectar idioma para {file_path}: {str(e)}")
                detected_lang = "und"
            except Exception as e:
                self.logger.warning(f"Error inesperado durante detección de idioma para {file_path}: {str(e)}")
                detected_lang = "und"
        else:
            self.logger.debug(f"No hay bloques procesados para detectar idioma en {file_path}")
            detected_lang = "und"
        
        # 4.5. Transformar segmentos (diccionarios) en instancias de ProcessedContentItem
        processed_content_items: List[ProcessedContentItem] = []
        if segments:
            # Extraer información general del job_config_dict si existe
            # y de processed_document_metadata (que ya contiene info del loader y preprocessor)
            
            # Crear un objeto BatchContext (si job_config_dict está disponible)
            batch_context_obj = None
            if job_config_dict:
                batch_context_obj = BatchContext(
                    author_name=job_config_dict.get("author_name", processed_document_metadata.get("autor_documento", "Desconocido")),
                    language_code=job_config_dict.get("language_code", processed_document_metadata.get("idioma_documento", "und")),
                    origin_type_name=job_config_dict.get("origin_type_name", "Desconocido"),
                    acquisition_date=job_config_dict.get("acquisition_date"),
                    force_null_publication_date=job_config_dict.get("force_null_publication_date", False)
                )

            # Información común a todos los segmentos de este documento
            id_doc_fuente = processed_document_metadata.get("hash_documento_original") or str(processed_document_metadata.get("ruta_archivo_original", uuid.uuid4()))
            titulo_doc = processed_document_metadata.get("titulo_documento", Path(file_path).stem)
            
            # Aplicar override de autor si está presente
            if author_override:
                # Validar nombre de autor antes de usarlo
                author_clean = author_override.strip()
                if len(author_clean) == 0:
                    self.logger.warning(f"Nombre de autor vacío. Usando detección automática.")
                    # No cambiar autor_doc, mantener detección automática
                elif len(author_clean) > 200:
                    self.logger.warning(f"Nombre de autor muy largo ({len(author_clean)} caracteres). Truncando a 200 caracteres.")
                    autor_doc = author_clean[:200].strip()
                    self.logger.info(f"Usando autor forzado (truncado) para {file_path}: '{autor_doc}'")
                elif any(char in author_clean for char in ['<', '>', '|', ':', '*', '?', '"', '\\', '/', '\n', '\r', '\t']):
                    self.logger.warning(f"Nombre de autor contiene caracteres problemáticos: '{author_clean}'. Limpiando caracteres especiales.")
                    # Limpiar caracteres problemáticos
                    import re
                    autor_doc = re.sub(r'[<>|:*?"\\\/\n\r\t]', '', author_clean).strip()
                    if len(autor_doc) > 0:
                        self.logger.info(f"Usando autor forzado (limpiado) para {file_path}: '{autor_doc}'")
                    else:
                        self.logger.warning(f"Nombre de autor quedó vacío después de limpiar. Usando detección automática.")
                        # No cambiar autor_doc, mantener detección automática
                else:
                    autor_doc = author_clean
                    self.logger.info(f"Usando autor forzado para {file_path}: '{autor_doc}'")
            else:
                autor_doc = batch_context_obj.author_name if batch_context_obj else processed_document_metadata.get("autor_documento")
                if autor_doc:
                    self.logger.info(f"Usando autor detectado para {file_path}: '{autor_doc}'")
                else:
                    self.logger.debug(f"No se detectó autor para {file_path}")
            
            fecha_pub_doc = processed_document_metadata.get("fecha_publicacion_documento") # Ya debería estar parseada por el loader o preprocessor
            
            ruta_original_doc = str(processed_document_metadata.get("ruta_archivo_original", processed_document_metadata.get("source_file_path", file_path)))
            
            # Metadatos adicionales de la fuente (del loader/preprocessor)
            meta_adicionales_fuente = processed_document_metadata.get("metadatos_adicionales_fuente", {})
            if batch_context_obj: # Añadir info del job a los metadatos adicionales
                meta_adicionales_fuente["job_id"] = job_config_dict.get("job_id", "N/A")
                meta_adicionales_fuente["job_origin_type_name"] = batch_context_obj.origin_type_name
                if batch_context_obj.acquisition_date:
                    meta_adicionales_fuente["job_acquisition_date"] = batch_context_obj.acquisition_date

            current_timestamp_iso = datetime.now(timezone.utc).isoformat()

            # Log de debug para verificar el idioma detectado antes del bucle
            if detected_lang:
                self.logger.debug(f"Idioma detectado disponible para asignación: '{detected_lang}'")
            else:
                self.logger.debug(f"No se detectó idioma válido, detected_lang = {detected_lang}")
            
            # Log de debug para verificar las claves disponibles en processed_document_metadata
            self.logger.debug(f"Claves disponibles en processed_document_metadata: {list(processed_document_metadata.keys())}")
            self.logger.debug(f"Valor de hash_documento_original en metadata: '{processed_document_metadata.get('hash_documento_original')}'")
            self.logger.debug(f"Valor de ruta_archivo_original en metadata: '{processed_document_metadata.get('ruta_archivo_original')}'")
            self.logger.debug(f"Valor de source_file_path en metadata: '{processed_document_metadata.get('source_file_path')}'")
            self.logger.debug(f"Valor de idioma_documento en metadata: '{processed_document_metadata.get('idioma_documento')}'")
            
            # Log de debug para verificar variables locales críticas
            self.logger.debug(f"Variable detected_lang: '{detected_lang}' (tipo: {type(detected_lang)})")
            self.logger.debug(f"Variable batch_context_obj: {batch_context_obj}")
            if batch_context_obj:
                self.logger.debug(f"batch_context_obj.language_code: '{batch_context_obj.language_code}'")

            for i, segment_dict in enumerate(segments):
                # segment_dict es el diccionario devuelto por el segmentador (ej. {'type': 'poem', 'title': '...', 'verses': [...]})
                # Necesitamos mapear esto a ProcessedContentItem

                texto_segmento_final = ""
                tipo_segmento_final = segment_dict.get("type", "desconocido")
                jerarquia_final = segment_dict.get("jerarquia_contextual", {}) # Los segmentadores deberían empezar a popular esto

                if tipo_segmento_final == "poem" and "numbered_verses" in segment_dict:
                    # Reconstruir el texto del poema desde los versos numerados si es necesario
                    # o usar un campo 'full_text' si el segmentador ya lo provee.
                    # VerseSegmenter.get_full_text_from_numbered_verses() podría ser útil aquí.
                    # Por ahora, asumimos que el segmentador provee 'text' o se puede tomar 'title' + 'verses'
                    # Esto necesita refinamiento según la salida EXACTA de cada segmentador.
                    # Ejemplo simple:
                    temp_text_parts = []
                    if segment_dict.get("title"):
                        temp_text_parts.append(segment_dict["title"])
                    if "numbered_verses" in segment_dict and isinstance(segment_dict["numbered_verses"], list):
                         # Asumimos que VerseSegmenter fue modificado para añadir 'text' a cada verso en numbered_verses
                        temp_text_parts.extend([v_dict.get("text", "") for v_dict in segment_dict["numbered_verses"] if v_dict.get("text","").strip()])
                    elif "verses" in segment_dict and isinstance(segment_dict["verses"], list): # Fallback si no hay numbered_verses
                        temp_text_parts.extend(segment_dict["verses"])

                    texto_segmento_final = "\n".join(filter(None,temp_text_parts)).strip()
                    # La jerarquía podría ser el título del poema o la estrofa
                    if segment_dict.get("title"):
                        jerarquia_final.setdefault("poema_titulo", segment_dict.get("title"))
                    # Aquí podrías añadir info de estrofa/verso si el segmentador lo desglosa a ese nivel para cada CHUNK.
                    # Actualmente, el segmentador devuelve el poema ENTERO como un chunk.

                elif tipo_segmento_final == "section" and "content" in segment_dict:
                    # Para HeadingSegmenter, 'content' puede ser una lista de párrafos o ya un string.
                    # Y 'title' es el título de la sección.
                    content_data = segment_dict.get("content")
                    if isinstance(content_data, list):
                        texto_segmento_final = "\n\n".join(p.get("text") if isinstance(p, dict) else str(p) for p in content_data if (p.get("text") if isinstance(p,dict) else str(p)).strip())
                    elif isinstance(content_data, str):
                        texto_segmento_final = content_data
                    else: # Fallback si 'content' no está o es inesperado
                        texto_segmento_final = segment_dict.get("text", segment_dict.get("title", ""))

                    jerarquia_final.setdefault(f"nivel_{segment_dict.get('level', 'desconocido')}", segment_dict.get("title", "Sin Título"))
                    # Aquí se podría construir una jerarquía más rica si el segmentador devuelve info de parent_id, etc.

                elif "text" in segment_dict: # Para párrafos u otros tipos simples
                    texto_segmento_final = str(segment_dict["text"])
                
                if not texto_segmento_final.strip(): # Omitir segmentos vacíos
                    self.logger.debug(f"Omitiendo segmento vacío o sin texto procesable: {segment_dict}")
                    continue

                # Lógica de precedencia para idioma del documento (corregida)
                final_idioma_doc = "und"  # Valor por defecto

                # Log detallado de la lógica de precedencia (solo para el primer segmento)
                if i == 0:
                    self.logger.debug(f"=== INICIO LÓGICA DE PRECEDENCIA IDIOMA ===")
                    self.logger.debug(f"batch_context_obj existe: {batch_context_obj is not None}")
                    if batch_context_obj:
                        self.logger.debug(f"batch_context_obj.language_code: '{batch_context_obj.language_code}'")
                        self.logger.debug(f"batch_context_obj.language_code válido: {batch_context_obj.language_code and batch_context_obj.language_code.lower() != 'und'}")
                    self.logger.debug(f"detected_lang: '{detected_lang}'")
                    self.logger.debug(f"detected_lang válido: {detected_lang and str(detected_lang).lower() != 'und'}")
                    self.logger.debug(f"idioma_documento en metadata: '{processed_document_metadata.get('idioma_documento')}'")

                # 1. Intentar con batch_context si existe y tiene un idioma válido
                if batch_context_obj and batch_context_obj.language_code and batch_context_obj.language_code.lower() != "und":
                    final_idioma_doc = batch_context_obj.language_code
                    if i == 0:  # Solo log en el primer segmento para evitar spam
                        self.logger.debug(f"✓ Usando idioma del job config: {final_idioma_doc}")
                # 2. Si no, intentar con el idioma detectado (variable definida ANTES del bucle) si es válido
                elif detected_lang and str(detected_lang).lower() != "und":
                    final_idioma_doc = str(detected_lang)
                    if i == 0:  # Solo log en el primer segmento para evitar spam
                        self.logger.debug(f"✓ Usando idioma detectado automáticamente: {final_idioma_doc}")
                # 3. Si no, intentar con el idioma de los metadatos del documento (del loader) si es válido
                elif processed_document_metadata.get("idioma_documento") and str(processed_document_metadata.get("idioma_documento")).lower() != "und":
                    final_idioma_doc = str(processed_document_metadata.get("idioma_documento"))
                    if i == 0:  # Solo log en el primer segmento para evitar spam
                        self.logger.debug(f"✓ Usando idioma de metadatos del loader: {final_idioma_doc}")
                # Si todo lo anterior falla, se queda con "und"
                else:
                    if i == 0:  # Solo log en el primer segmento para evitar spam
                        self.logger.debug(f"✗ Usando idioma por defecto 'und' para todos los segmentos")
                        self.logger.debug(f"=== FIN LÓGICA DE PRECEDENCIA IDIOMA ===")

                # Log de verificación para el primer segmento
                if i == 0:
                    self.logger.debug(f"final_idioma_doc determinado para todos los segmentos: '{final_idioma_doc}'")
                    # Debug adicional para rastrear el problema
                    hash_value = processed_document_metadata.get("hash_documento_original")
                    self.logger.debug(f"hash_documento_original en processed_document_metadata: '{hash_value}' (tipo: {type(hash_value)})")
                    self.logger.debug(f"detected_lang variable: '{detected_lang}' (tipo: {type(detected_lang)})")
                    self.logger.debug(f"final_idioma_doc variable: '{final_idioma_doc}' (tipo: {type(final_idioma_doc)})")

                # Log adicional justo antes de crear el ProcessedContentItem
                if i == 0:
                    hash_for_item = processed_document_metadata.get("hash_documento_original")
                    self.logger.debug(f"Valores para ProcessedContentItem - hash_documento_original: '{hash_for_item}', idioma_documento: '{final_idioma_doc}'")

                # Asignaciones explícitas para mayor claridad
                hash_documento_para_item = processed_document_metadata.get("hash_documento_original")
                idioma_documento_para_item = final_idioma_doc
                
                # Log adicional para verificar las asignaciones explícitas
                if i == 0:
                    self.logger.debug(f"=== VERIFICACIÓN ASIGNACIONES EXPLÍCITAS ===")
                    self.logger.debug(f"hash_documento_para_item: '{hash_documento_para_item}' (tipo: {type(hash_documento_para_item)})")
                    self.logger.debug(f"idioma_documento_para_item: '{idioma_documento_para_item}' (tipo: {type(idioma_documento_para_item)})")
                    self.logger.debug(f"¿hash_documento_para_item es None?: {hash_documento_para_item is None}")
                    self.logger.debug(f"¿hash_documento_para_item es cadena vacía?: {hash_documento_para_item == ''}")
                    self.logger.debug(f"¿idioma_documento_para_item es None?: {idioma_documento_para_item is None}")
                    self.logger.debug(f"¿idioma_documento_para_item es 'und'?: {idioma_documento_para_item == 'und'}")

                item = ProcessedContentItem(
                    id_segmento=str(uuid.uuid4()),
                    id_documento_fuente=id_doc_fuente,
                    ruta_archivo_original=ruta_original_doc,
                    hash_documento_original=hash_documento_para_item,
                    titulo_documento=titulo_doc,
                    autor_documento=autor_doc,
                    fecha_publicacion_documento=fecha_pub_doc,
                    editorial_documento=processed_document_metadata.get("editorial_documento"), # Tomar del doc si existe
                    isbn_documento=processed_document_metadata.get("isbn_documento"), # Tomar del doc si existe
                    idioma_documento=idioma_documento_para_item,
                    metadatos_adicionales_fuente=meta_adicionales_fuente,
                    texto_segmento=texto_segmento_final,
                    tipo_segmento=tipo_segmento_final,
                    orden_segmento_documento=segment_dict.get("order_in_document", i), # Usar orden del segmentador si existe
                    jerarquia_contextual=jerarquia_final,
                    longitud_caracteres_segmento=len(texto_segmento_final),
                    embedding_vectorial=None, # Se generará después
                    timestamp_procesamiento=current_timestamp_iso,
                    version_pipeline_etl="1.0.0-refactor-ui", # Actualizar según sea necesario
                    nombre_segmentador_usado=profile.get('segmenter', 'desconocido') if profile else 'desconocido',
                    notas_procesamiento_segmento=segment_dict.get("processing_notes") # Si el segmentador añade notas
                )
                
                # Log adicional después de crear el ProcessedContentItem
                if i == 0:
                    self.logger.debug(f"ProcessedContentItem creado - hash_documento_original: '{item.hash_documento_original}', idioma_documento: '{item.idioma_documento}'")
                    self.logger.debug(f"Verificación de variables explícitas - hash_documento_para_item: '{hash_documento_para_item}', idioma_documento_para_item: '{idioma_documento_para_item}'")
                
                processed_content_items.append(item)
        else: # No hay segmentos del segmentador
            # Si no hay segmentos pero el loader/preprocessor generó metadatos (ej. archivo vacío o error manejado),
            # podríamos crear un ProcessedContentItem "placeholder" o simplemente devolver la lista vacía.
            # Por ahora, si no hay segmentos del segmentador, processed_content_items quedará vacía.
            pass
        
        # 5. TODO: Aplicar post-procesador si está configurado
        
        # 6. Exportar si se especificó ruta de salida
        # Usar processed_document_metadata para la parte de metadatos del documento
        # y processed_content_items para los segmentos.
        if output_dir: # output_dir aquí es en realidad el output_file_path
            # El primer if es para si manager.process_file devolvió segmentos (ahora processed_content_items)
            if processed_content_items:
                self._export_results(processed_content_items, output_dir, processed_document_metadata, output_format)
            # El segundo elif es para cuando no hubo segmentos (lista vacía) pero SÍ hay un output_path
            # y queremos exportar los metadatos del documento (que pueden contener un error o advertencia).
            elif not processed_content_items: 
                self.logger.info(f"No se generaron ProcessedContentItems para {file_path}, pero se exportarán metadatos a {output_dir}")
                self._export_results([], output_dir, processed_document_metadata, output_format)

        # Devolver la tupla completa como espera process_file.py, usando la nueva lista de dataclasses
        return processed_content_items, segmenter_stats, processed_document_metadata
    
    def _export_results(self, segments: List[Any], output_dir: str, document_metadata: Optional[Dict[str, Any]] = None, output_format: str = "ndjson"):
        """
        Exporta los resultados al formato especificado.
        Si segments está vacío, exporta document_metadata con un campo segments: [].
        
        Args:
            segments: Lista de segmentos a exportar (ahora List[ProcessedContentItem] o similar)
            output_dir: Directorio donde guardar los resultados
            document_metadata: Metadatos del documento
            output_format: Formato de salida ("ndjson" o "json")
        """
        import json
        
        try:
            with open(output_dir, 'w', encoding='utf-8') as f:
                if output_format.lower() == "json":
                    # Formato JSON: crear un objeto con metadatos y array de segmentos
                    if segments:
                        # Convertir segmentos a diccionarios
                        segments_data = [dataclasses.asdict(segment) for segment in segments]
                        output_data = {
                            "document_metadata": document_metadata or {},
                            "segments": segments_data
                        }
                    else:
                        # Sin segmentos, solo metadatos
                        output_data = {
                            "document_metadata": document_metadata or {},
                            "segments": []
                        }
                    
                    # Escribir como JSON con formato bonito
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                    
                else:
                    # Formato NDJSON (por defecto): una línea por objeto
                    if segments:
                        for segment in segments:
                            f.write(json.dumps(dataclasses.asdict(segment), ensure_ascii=False) + '\n')
                    else:
                        # Si no hay segmentos, escribir los metadatos del documento y segments: []
                        output_data = document_metadata.copy() if document_metadata else {}
                        output_data['segments'] = []
                        f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
                        
            self.logger.info(f"Resultados guardados en formato {output_format.upper()}: {output_dir}")
        except Exception as e:
            self.logger.error(f"Error al exportar resultados: {str(e)}")

    def get_profile_for_file(self, file_path: str) -> Optional[str]:
        """
        Sugiere el perfil más adecuado para un archivo basado en su nombre y extensión.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Nombre del perfil sugerido o None si no hay sugerencia
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        filename = file_path.stem.lower()
        
        # Palabras clave que sugieren tipos de contenido
        poem_keywords = ['poema', 'poemas', 'poesía', 'poesías', 'versos', 'verso', 'estrofa', 'poeta', 
                         'poem', 'poetry', 'lyric', 'lyrics', 'canción', 'canciones']
        book_keywords = ['libro', 'capitulo', 'capítulos', 'book', 'chapter', 'section', 'manual', 
                        'guía', 'documento', 'texto', 'escrito']
        
        # Comprobar primero en el nombre del archivo
        for keyword in poem_keywords:
            if keyword in filename:
                self.logger.debug(f"Perfil poem_or_lyrics detectado por palabra clave en el nombre: {keyword}")
                return 'poem_or_lyrics'
                
        for keyword in book_keywords:
            if keyword in filename:
                self.logger.debug(f"Perfil book_structure detectado por palabra clave en el nombre: {keyword}")
                return 'book_structure'
                
        # Verificar si algún perfil tiene configuración específica para esta extensión
        for profile_name, profile in self.profiles.items():
            if 'file_types' in profile and extension in profile['file_types']:
                # Si ambos perfiles soportan el tipo, poem_or_lyrics tiene preferencia para documentos personales
                if extension in ['.txt', '.md', '.docx']:
                    if 'poem_or_lyrics' in self.profiles:
                        self.logger.debug(f"Perfil poem_or_lyrics sugerido para extensión personal: {extension}")
                        return 'poem_or_lyrics'
                
                self.logger.debug(f"Perfil {profile_name} sugerido por tipo de archivo: {extension}")
                return profile_name
        
        # Si todo lo demás falla, poem_or_lyrics es una buena opción predeterminada para archivos personales
        if extension in ['.txt', '.md', '.docx']:
            if 'poem_or_lyrics' in self.profiles:
                self.logger.debug(f"Perfil poem_or_lyrics sugerido por defecto para archivos personales")
                return 'poem_or_lyrics'
        
        return None

    def create_pre_processor(self, pre_processor_type: str, profile: Optional[Dict] = None) -> 'BasePreProcessor':
        """
        Crea una instancia del pre-procesador especificado.
        
        Args:
            pre_processor_type: Tipo de pre-procesador a crear
            profile: Perfil opcional para configuración específica
            
        Returns:
            Instancia del pre-procesador
        """
        # LOGGING DETALLADO PARA DEBUG
        print(f"🔧🔧🔧 CREANDO PRE-PROCESADOR: {pre_processor_type} 🔧🔧🔧")
        print(f"🔧🔧🔧 PERFIL RECIBIDO: {profile.get('name') if profile else 'None'} 🔧🔧🔧")
        
        preprocessor_config = profile.get('pre_processor_config') if profile else None
        print(f"🔧🔧🔧 CONFIG DEL PRE-PROCESADOR: {preprocessor_config} 🔧🔧🔧")
        
        # Obtener configuración del pre-procesador desde el perfil
        if pre_processor_type == 'common_block':
            return CommonBlockPreprocessor(config=preprocessor_config)
        # Agregar otros tipos según sea necesario
        else:
            raise ValueError(f"Tipo de pre-procesador no soportado: {pre_processor_type}")

if __name__ == "__main__":
    # Configuración básica de logging
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    manager = ProfileManager()
    print("Perfiles disponibles:")
    for profile in manager.list_profiles():
        print(f"- {profile['name']}: {profile['description']}")