import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Type, Tuple
from pathlib import Path
import dataclasses
from datetime import datetime, timezone
import uuid
import importlib
import re

from langdetect import detect, LangDetectException
from dataset.scripts.data_models import ProcessedContentItem, BatchContext
from .author_detection import detect_author_in_segments

# RECARGA FORZADA DE MÓDULOS MODIFICADOS - V7.0
import dataset.processing.segmenters.heading_segmenter
importlib.reload(dataset.processing.segmenters.heading_segmenter)

import dataset.processing.loaders.pdf_loader
importlib.reload(dataset.processing.loaders.pdf_loader)

import dataset.processing.pre_processors.common_block_preprocessor
importlib.reload(dataset.processing.pre_processors.common_block_preprocessor)

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
        
        # Registrar MarkdownVerseSegmenter manualmente
        try:
            from .segmenters.markdown_verse_segmenter import MarkdownVerseSegmenter
            self.register_segmenter('markdown_verse', MarkdownVerseSegmenter)
            self.logger.info("✅ MarkdownVerseSegmenter registrado manualmente")
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo registrar MarkdownVerseSegmenter: {e}")
        
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
        
        # Registrar MarkdownPDFLoader manualmente
        try:
            from .loaders.markdown_pdf_loader import MarkdownPDFLoader
            self.register_loader('.pdf_markdown', MarkdownPDFLoader)  # Extensión especial
            self.logger.info("✅ MarkdownPDFLoader registrado manualmente")
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo registrar MarkdownPDFLoader: {e}")
    
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
        
        # SPECIAL CASE: Si es perfil verso y archivo PDF, usar MarkdownPDFLoader
        if profile_name == 'verso' and extension == '.pdf':
            try:
                from .loaders.markdown_pdf_loader import MarkdownPDFLoader
                self.logger.info("🎯 Usando MarkdownPDFLoader para perfil verso")
                loader_class = MarkdownPDFLoader
            except ImportError:
                self.logger.warning("⚠️ MarkdownPDFLoader no disponible, usando PDFLoader tradicional")
                loader_class = self._loader_registry.get(extension)
        else:
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
        
        # IMPORTANTE: Copiar configuración de author_detection
        if 'author_detection' in profile:
            config['author_detection'] = profile['author_detection']
        
        # Crear instancia del segmentador
        try:
            segmenter_class = self._segmenter_registry[segmenter_type]
            return segmenter_class(config)
        except Exception as e:
            self.logger.error(f"Error al crear segmentador '{segmenter_type}': {str(e)}")
            return None
    
    def _create_processed_content_item(self,
                                      processed_document_metadata: Dict[str, Any],
                                      segment_data: Dict[str, Any],
                                      file_path: str,
                                      language_override: Optional[str] = None,
                                      author_override: Optional[str] = None,
                                      detected_lang: Optional[str] = None,
                                      segment_index: int = 0,
                                      job_config_dict: Optional[Dict[str, Any]] = None,
                                      segmenter_name: str = "unknown",
                                      main_document_author_name: Optional[str] = None,
                                      main_author_detection_info: Optional[Dict[str, Any]] = None) -> ProcessedContentItem:
        """
        🔧 FUNCIÓN UNIFICADA SIMPLIFICADA: Crea ProcessedContentItem con estructura limpia en inglés.
        
        Elimina duplicaciones y campos innecesarios. Metadatos consolidados sin redundancia.
        """
        current_timestamp_iso = datetime.now(timezone.utc).isoformat()
        
        # 1. DETERMINAR IDIOMA (con prioridad correcta)
        final_language = None
        if language_override and language_override.strip():
            # Validar código de idioma
            lang_clean = language_override.strip().lower()
            if 2 <= len(lang_clean) <= 5 and lang_clean.replace('-', '').isalpha():
                final_language = lang_clean
                self.logger.info(f"Usando idioma forzado: {final_language}")
            else:
                self.logger.warning(f"Código de idioma inválido: '{language_override}'. Usando detección automática.")
        
        if not final_language:
            final_language = detected_lang or processed_document_metadata.get('language', 'unknown')
            if final_language and final_language != 'unknown':
                self.logger.debug(f"Usando idioma detectado: {final_language}")
        
        if not final_language or final_language == 'unknown':
            final_language = 'unknown'
        
        # 2. DETERMINAR AUTOR (con prioridad correcta: author_override > main_document_author_name > fallback)
        final_author = None
        if author_override and author_override.strip():
            author_clean = author_override.strip()
            if len(author_clean) <= 200:
                # Limpiar caracteres problemáticos
                import re
                final_author = re.sub(r'[<>|:*?"\\\/\n\r\t]', '', author_clean).strip()
                if final_author:
                    self.logger.info(f"Usando autor forzado: {final_author}")
                else:
                    self.logger.warning("Autor forzado quedó vacío después de limpieza")
            else:
                final_author = author_clean[:200].strip()
                self.logger.warning(f"Autor forzado truncado a 200 caracteres: {final_author}")
        
        if not final_author and main_document_author_name:
            final_author = main_document_author_name
            self.logger.debug(f"Usando autor principal del documento: {final_author}")
        
        if not final_author:
            final_author = processed_document_metadata.get('autor_documento') or processed_document_metadata.get('author')
            if final_author:
                self.logger.debug(f"Usando autor de fallback: {final_author}")
        
        # 3. CONSOLIDAR METADATOS ADICIONALES (sin duplicaciones)
        # Campos que YA están como campos principales - NO incluir en additional_metadata
        main_fields = {
            'segment_id', 'document_id', 'document_language', 'text', 'segment_type', 
            'segment_order', 'text_length', 'processing_timestamp', 'source_file_path',
            'document_hash', 'document_title', 'document_author', 'publication_date',
            'publisher', 'isbn', 'pipeline_version', 'segmenter_used',
            # También excluir variantes en español/inglés para evitar duplicación
            'ruta_archivo_original', 'source_file_path', 'ruta_archivo',
            'hash_documento_original', 'titulo_documento', 'author', 'autor_documento',
            'fecha_publicacion_documento', 'editorial_documento', 'isbn_documento', 
            'idioma_documento', 'language', 'file_format', 'extension_archivo',
            'nombre_archivo'
        }
        
        # Construir metadatos adicionales ÚNICAMENTE con campos que no están como principales
        additional_metadata_clean = {}
        
        # Agregar información de job si existe
        if job_config_dict:
            if job_config_dict.get("job_id"):
                additional_metadata_clean["job_id"] = job_config_dict["job_id"]
            if job_config_dict.get("origin_type_name"):
                additional_metadata_clean["job_origin_type"] = job_config_dict["origin_type_name"]
        
        # Agregar información de detección de autor principal para trazabilidad
        if main_author_detection_info:
            additional_metadata_clean["main_author_detection_info"] = main_author_detection_info
        
        # Agregar solo campos verdaderamente adicionales del documento
        for key, value in processed_document_metadata.items():
            if key not in main_fields and key != 'metadatos_adicionales_fuente' and value is not None:
                # Usar nombres más descriptivos para campos del documento
                if key not in ['author', 'language', 'file_format']:  # Skip common duplicates
                    additional_metadata_clean[f"doc_{key}"] = value
        
        # 4. EXTRAER DATOS DEL SEGMENTO (simplificado)
        if isinstance(segment_data, dict):
            text_content = segment_data.get('text', '') or segment_data.get('texto', '')
            segment_type = segment_data.get('type', 'text_block') 
            segment_order = segment_data.get('order_in_document', segment_index + 1)
            
            # Incluir metadata de detección de autor a nivel de segmento (NO para document_author principal)
            segment_metadata = segment_data.get('metadata', {})
            if segment_metadata.get('detected_author'):
                additional_metadata_clean['segment_detected_author'] = segment_metadata['detected_author']
                additional_metadata_clean['segment_author_confidence'] = segment_metadata.get('author_confidence')
                additional_metadata_clean['segment_author_detection_method'] = segment_metadata.get('author_detection_method')
                if segment_metadata.get('author_detection_details'):
                    additional_metadata_clean['segment_author_detection_details'] = segment_metadata['author_detection_details']
        else:
            text_content = str(segment_data) if segment_data else ''
            segment_type = 'text_block'
            segment_order = segment_index + 1
        
        # 5. CREAR ProcessedContentItem CON ESTRUCTURA LIMPIA
        return ProcessedContentItem(
            segment_id=str(uuid.uuid4()),
            document_id=processed_document_metadata.get('hash_documento_original') or processed_document_metadata.get('document_hash') or str(uuid.uuid4()),
            document_language=final_language,
            text=text_content,
            segment_type=segment_type,
            segment_order=segment_order,
            text_length=len(text_content),
            processing_timestamp=current_timestamp_iso,
            source_file_path=str(Path(file_path).absolute()),
            document_hash=processed_document_metadata.get('hash_documento_original') or processed_document_metadata.get('document_hash'),
            document_title=processed_document_metadata.get('titulo_documento') or processed_document_metadata.get('document_title') or Path(file_path).stem,
            document_author=final_author,
            publication_date=processed_document_metadata.get('fecha_publicacion_documento') or processed_document_metadata.get('publication_date'),
            publisher=processed_document_metadata.get('editorial_documento') or processed_document_metadata.get('publisher'),
            isbn=processed_document_metadata.get('isbn_documento') or processed_document_metadata.get('isbn'),
            additional_metadata=additional_metadata_clean,
            pipeline_version="profile_manager_v4.0_english_clean",
            segmenter_used=segmenter_name
        )

    def process_file(self, 
                    file_path: str, 
                    profile_name: str, 
                    output_file: Optional[str] = None,
                    encoding: str = 'utf-8',
                    force_content_type: Optional[str] = None,
                    confidence_threshold: float = 0.5,
                    job_config_dict: Optional[Dict[str, Any]] = None,
                    language_override: Optional[str] = None,
                    author_override: Optional[str] = None,
                    output_format: str = "ndjson",
                    folder_structure_info: Optional[Dict[str, Any]] = None) -> tuple:
        """
        Procesa un archivo completo usando un perfil.
        
        Args:
            file_path: Ruta al archivo a procesar
            profile_name: Nombre del perfil a usar
            output_file: Archivo para guardar resultados (opcional)
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
        
        # 🔍 LOGGING DETALLADO PARA DEBUG DE EXPORTACIÓN
        self.logger.warning(f"🔍 INICIO process_file - output_file recibido: '{output_file}'")
        self.logger.warning(f"🔍 INICIO process_file - output_format: '{output_format}'")
        print(f"🔍 INICIO process_file - output_file recibido: '{output_file}'")
        print(f"🔍 INICIO process_file - output_format: '{output_format}'")
        
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
                
                # 🔧 PRIORIDAD: job_config_dict > perfil
                json_config = None
                
                # Primero, intentar obtener configuración del job_config_dict (desde GUI)
                if job_config_dict and 'json_config' in job_config_dict:
                    json_config = job_config_dict['json_config']
                    self.logger.info(f"📱 Aplicando configuración JSON desde GUI: {len(json_config.get('filter_rules', []))} reglas")
                
                # Si no hay configuración desde GUI, usar la del perfil
                elif profile and 'json_config' in profile:
                    json_config = profile['json_config']
                    self.logger.info(f"⚙️ Aplicando configuración JSON del perfil: {profile_name}")
                
                # Aplicar la configuración JSON encontrada
                if json_config:
                    loader_kwargs.update(json_config)
                    self.logger.debug(f"🔧 Configuración JSON aplicada: {json_config}")
                else:
                    self.logger.info(f"📄 JSONLoader sin configuración específica - usando valores por defecto")
            
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
        
        # Para archivos JSON: procesamiento directo
        if file_path.lower().endswith('.json'):
            # Para JSON: usar bloques directamente del loader, sin preprocessor
            processed_blocks = raw_blocks
            processed_document_metadata = raw_document_metadata
            
            # 🔧 NUEVO: Detectar idioma también para JSON
            detected_lang = None
            if language_override:
                # Validar código de idioma antes de usarlo
                if len(language_override.strip()) < 2 or len(language_override.strip()) > 5:
                    self.logger.warning(f"Código de idioma inválido: '{language_override}' (debe tener 2-5 caracteres). Usando detección automática.")
                elif any(char.isdigit() or not char.isalnum() for char in language_override.strip() if char != '-'):
                    self.logger.warning(f"Código de idioma contiene caracteres inválidos: '{language_override}'. Usando detección automática.")
                else:
                    detected_lang = language_override.strip().lower()
                    self.logger.info(f"Usando idioma forzado para JSON {file_path}: {detected_lang}")
            
            if not detected_lang and processed_blocks:
                try:
                    # Concatenar texto de los primeros bloques para obtener una muestra representativa
                    sample_texts = []
                    total_chars = 0
                    max_chars = 1000
                    max_blocks = 5
                    
                    for i, block in enumerate(processed_blocks[:max_blocks]):
                        if total_chars >= max_chars:
                            break
                        
                        block_text = block.get('text', '') if isinstance(block, dict) else str(block)
                        if block_text.strip():
                            remaining_chars = max_chars - total_chars
                            if len(block_text) > remaining_chars:
                                block_text = block_text[:remaining_chars]
                            sample_texts.append(block_text.strip())
                            total_chars += len(block_text)
                    
                    sample_text = " ".join(sample_texts).strip()
                    
                    # Intentar detectar idioma si hay suficiente texto
                    if len(sample_text) >= 20:
                        detected_lang = detect(sample_text)
                        self.logger.info(f"Idioma detectado automáticamente para JSON {file_path}: {detected_lang}")
                    else:
                        detected_lang = "und"
                        
                except LangDetectException as e:
                    self.logger.debug(f"No se pudo detectar idioma para JSON {file_path}: {str(e)}")
                    detected_lang = "und"
                except Exception as e:
                    self.logger.warning(f"Error inesperado durante detección de idioma para JSON {file_path}: {str(e)}")
                    detected_lang = "und"
            else:
                detected_lang = detected_lang or "und"
            
            segments = []
            
            self.logger.warning(f"🔍 DEBUG: Tenemos {len(processed_blocks)} bloques procesados")
            if processed_blocks:
                self.logger.warning(f"🔍 DEBUG: Estructura del primer bloque: {processed_blocks[0]}")
            
            for i, block in enumerate(processed_blocks):
                # 🔧 USAR FUNCIÓN UNIFICADA: Ahora con detección de idioma
                block_with_type = block.copy() if isinstance(block, dict) else {'text': str(block)}
                block_with_type['type'] = 'json_element'
                
                segment = self._create_processed_content_item(
                    processed_document_metadata,
                    block_with_type,
                    file_path,
                    language_override,
                    author_override,
                    detected_lang,
                    i,
                    job_config_dict,
                    "json_direct_conversion",
                    None,  # main_document_author_name - no aplicable para JSON directo
                    None   # main_author_detection_info - no aplicable para JSON directo
                )
                segments.append(segment)
            
            segmenter_stats = {
                'json_elements_processed': len(segments),
                'processing_method': 'direct_conversion',
                'bypassed_segmenter': True
            }
            
            # Para JSON: retornar directamente sin procesamiento adicional
            self.logger.info(f"✅ JSON procesado directamente: {len(segments)} segmentos creados")
            
            # ✅ CORREGIDO: Exportar si se especificó ruta de salida
            self.logger.warning(f"🔍 VERIFICANDO EXPORTACIÓN - output_file: '{output_file}' (tipo: {type(output_file)})")
            print(f"🔍 VERIFICANDO EXPORTACIÓN - output_file: '{output_file}' (tipo: {type(output_file)})")
            
            if output_file:
                self.logger.warning(f"📤 INICIANDO EXPORTACIÓN - {len(segments)} segmentos JSON a: {output_file}")
                print(f"📤 INICIANDO EXPORTACIÓN - {len(segments)} segmentos JSON a: {output_file}")
                try:
                    self._export_results(segments, output_file, processed_document_metadata, output_format)
                    self.logger.warning(f"✅ EXPORTACIÓN JSON COMPLETADA EXITOSAMENTE")
                    print(f"✅ EXPORTACIÓN JSON COMPLETADA EXITOSAMENTE")
                except Exception as e:
                    self.logger.error(f"❌ ERROR EN EXPORTACIÓN JSON: {str(e)}")
                    print(f"❌ ERROR EN EXPORTACIÓN JSON: {str(e)}")
                    self.logger.exception("Detalles del error de exportación:")
            else:
                self.logger.warning(f"⚠️ NO SE EXPORTARÁ - output_file es None o vacío")
                print(f"⚠️ NO SE EXPORTARÁ - output_file es None o vacío")
            
            return segments, segmenter_stats, processed_document_metadata
            
        else:
            # Para otros archivos: usar CommonBlockPreprocessor normalmente
            profile = self.get_profile(profile_name)  # Obtener perfil para configuración del preprocessor
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
                
            # 2.5. Detectar autor principal del documento usando EnhancedContextualAuthorDetector
            main_document_author_name = None
            main_author_detection_info = {}
            
            try:
                self.logger.info(f"Detectando autor principal del documento: {file_path}")
                
                # Determinar profile_type basado en profile_name
                profile_type = 'poetry' if 'verso' in profile_name.lower() else 'prose'
                
                # Llamar a la función de detección de autor
                author_detection_result = detect_author_in_segments(
                    segments=processed_blocks,
                    profile_type=profile_type,
                    document_title=processed_document_metadata.get('titulo_documento', ''),
                    source_file_path=str(file_path)
                )
                
                if author_detection_result and author_detection_result.get('name'):
                    main_document_author_name = author_detection_result['name']
                    main_author_detection_info = {
                        'confidence': author_detection_result.get('confidence', 0.0),
                        'method': author_detection_result.get('method', 'unknown'),
                        'source': author_detection_result.get('source', 'enhanced_contextual')
                    }
                    self.logger.info(f"Autor principal detectado: '{main_document_author_name}' (confianza: {main_author_detection_info['confidence']:.2f}, método: {main_author_detection_info['method']})")
                else:
                    self.logger.warning(f"No se pudo detectar autor principal para {file_path}")
                    main_document_author_name = None
                    
            except Exception as e:
                self.logger.error(f"Error durante detección de autor principal para {file_path}: {str(e)}")
                main_document_author_name = None
                main_author_detection_info = {'error': str(e)}
                
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
            
            # Para otros archivos: usar segmentador normalmente
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
            # Log de debug para verificar el idioma detectado antes del bucle
            if detected_lang:
                self.logger.debug(f"Idioma detectado disponible para asignación: '{detected_lang}'")
            else:
                self.logger.debug(f"No se detectó idioma válido, detected_lang = {detected_lang}")
            
            # Log de debug para verificar las claves disponibles en processed_document_metadata
            self.logger.debug(f"Claves disponibles en processed_document_metadata: {list(processed_document_metadata.keys())}")

            for i, segment_dict in enumerate(segments):
                # 🔧 USAR FUNCIÓN UNIFICADA para archivos no-JSON también
                item = self._create_processed_content_item(
                    processed_document_metadata,
                    segment_dict,
                    file_path,
                    language_override,
                    author_override,
                    detected_lang,
                    i,
                    job_config_dict,
                    profile.get('segmenter', 'desconocido') if profile else 'desconocido',
                    main_document_author_name,
                    main_author_detection_info
                )
                
                processed_content_items.append(item)
        else: 
            # Si no hay segmentos del segmentador, processed_content_items quedará vacía
            pass
        
        # 5. TODO: Aplicar post-procesador si está configurado
        
        # 6. Exportar si se especificó ruta de salida
        # Usar processed_document_metadata para la parte de metadatos del documento
        # y processed_content_items para los segmentos.
        if output_file: # ✅ CORREGIDO: output_file es la ruta del archivo de salida
            # El primer if es para si manager.process_file devolvió segmentos (ahora processed_content_items)
            if processed_content_items:
                self._export_results(processed_content_items, output_file, processed_document_metadata, output_format)
            # El segundo elif es para cuando no hubo segmentos (lista vacía) pero SÍ hay un output_path
            # y queremos exportar los metadatos del documento (que pueden contener un error o advertencia).
            elif not processed_content_items: 
                self.logger.info(f"No se generaron ProcessedContentItems para {file_path}, pero se exportarán metadatos a {output_file}")
                self._export_results([], output_file, processed_document_metadata, output_format)

        # Devolver la tupla completa como espera process_file.py, usando la nueva lista de dataclasses
        return processed_content_items, segmenter_stats, processed_document_metadata
    
    def _detect_extreme_corruption(self, text: str, corruption_threshold: float = 0.7) -> Tuple[bool, str]:
        """
        🔧 NUEVA FUNCIONALIDAD - Detecta corrupción extrema en texto.
        
        Args:
            text: Texto a analizar
            corruption_threshold: Umbral de corrupción (0.7 = 70% de caracteres corruptos)
            
        Returns:
            Tuple[bool, str]: (is_corrupted, reason)
        """
        if not text or len(text.strip()) < 10:
            return False, ""
        
        text = text.strip()
        total_chars = len(text)
        
        # Contar caracteres problemáticos
        control_chars = sum(1 for c in text if ord(c) < 32 and c not in ['\n', '\r', '\t'])
        replacement_chars = text.count('�')  # Caracteres de reemplazo Unicode
        null_chars = text.count('\x00')
        
        # Contar secuencias repetitivas de caracteres extraños (solo contar si son significativas)
        weird_pattern_matches = re.findall(r'[^\w\s\.,;:!?¡¿\-\(\)\[\]"\'áéíóúñüÁÉÍÓÚÑÜ]+', text)
        weird_patterns = sum(len(match) for match in weird_pattern_matches if len(match) >= 3)
        
        # Calcular porcentaje de corrupción
        corrupted_chars = control_chars + replacement_chars + null_chars + weird_patterns
        corruption_ratio = corrupted_chars / total_chars if total_chars > 0 else 0
        
        # Detectar patrones específicos de corrupción extrema
        extreme_patterns = [
            r'�{10,}',  # 10 o más caracteres de reemplazo consecutivos
            r'[\x00-\x08\x0B\x0C\x0E-\x1F]{5,}',  # 5 o más caracteres de control consecutivos
            r'^[\s�\x00-\x1F]*$',  # Solo espacios, caracteres de reemplazo y control
        ]
        
        has_extreme_pattern = any(re.search(pattern, text) for pattern in extreme_patterns)
        
        # Determinar si está extremadamente corrupto (MUCHO MÁS RESTRICTIVO)
        is_extremely_corrupted = (
            replacement_chars >= 50 or  # Al menos 50 caracteres de reemplazo
            has_extreme_pattern or
            (replacement_chars >= 20 and replacement_chars > (total_chars * 0.5))  # 20+ caracteres Y más del 50%
        )
        
        if is_extremely_corrupted:
            reason = f"Corrupción extrema detectada: {corruption_ratio:.1%} caracteres corruptos"
            if has_extreme_pattern:
                reason += " (patrones extremos detectados)"
            return True, reason
        
        return False, ""

    def _export_results(self, segments: List[Any], output_file: str, document_metadata: Optional[Dict[str, Any]] = None, output_format: str = "ndjson"):
        """
        Exporta los segmentos procesados (ProcessedContentItem) a archivo NDJSON o JSON.
        ACTUALIZADO: Usa estructura limpia en inglés.
        """
        import json
        
        # 🔍 LOGGING DETALLADO PARA DEBUG DE EXPORTACIÓN
        self.logger.warning(f"🔍 _export_results INICIADO")
        self.logger.warning(f"🔍 Parámetros recibidos:")
        self.logger.warning(f"🔍   - segments: {len(segments)} elementos")
        self.logger.warning(f"🔍   - output_file: '{output_file}'")
        self.logger.warning(f"🔍   - output_format: '{output_format}'")
        print(f"🔍 _export_results INICIADO con {len(segments)} segmentos")
        print(f"🔍 Exportando a: {output_file}")
        
        try:
            output_path = Path(output_file)
            # ✅ CORREGIDO: Solo crear el directorio padre, no el archivo como directorio
            self.logger.warning(f"🔍 Creando directorio padre: {output_path.parent}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not document_metadata:
                document_metadata = {}
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            results = []
            corrupted_segments_count = 0
            
            for i, segment in enumerate(segments):
                # ✅ ACTUALIZADO: Detectar si es ProcessedContentItem nuevo o viejo
                if hasattr(segment, 'text'):
                    # Es un ProcessedContentItem nuevo (estructura en inglés)
                    segment_text = segment.text
                    segment_type = segment.segment_type
                    segment_id = segment.segment_id
                    document_id = segment.document_id
                    segment_order = segment.segment_order
                    segment_metadata = segment.additional_metadata or {}
                    
                    # Usar datos del objeto ProcessedContentItem con estructura en inglés
                    segment_data = {
                        "segment_id": segment_id,
                        "document_id": document_id,
                        "document_language": segment.document_language,
                        "text": segment_text,
                        "segment_type": segment_type,
                        "segment_order": segment_order,
                        "text_length": segment.text_length,
                        "processing_timestamp": segment.processing_timestamp,
                        "source_file_path": segment.source_file_path,
                        "document_hash": segment.document_hash,
                        "document_title": segment.document_title,
                        "document_author": segment.document_author,
                        "publication_date": segment.publication_date,
                        "publisher": segment.publisher,
                        "isbn": segment.isbn,
                        "additional_metadata": segment_metadata,
                        "pipeline_version": segment.pipeline_version,
                        "segmenter_used": segment.segmenter_used
                    }
                elif hasattr(segment, 'texto_segmento'):
                    # Es un ProcessedContentItem viejo (compatibilidad hacia atrás)
                    segment_text = segment.texto_segmento
                    segment_type = segment.tipo_segmento
                    segment_id = segment.id_segmento
                    document_id = segment.id_documento_fuente
                    segment_order = segment.orden_segmento_documento
                    processing_notes = segment.notas_procesamiento_segmento
                    segment_metadata = segment.metadatos_adicionales_fuente or {}
                    segment_hierarchy = segment.jerarquia_contextual or {}
                    
                    # Convertir estructura vieja a nueva para exportación
                    segment_data = {
                        "segment_id": segment_id,
                        "document_id": document_id,
                        "document_language": segment.idioma_documento,
                        "text": segment_text,
                        "segment_type": segment_type,
                        "segment_order": segment_order,
                        "text_length": segment.longitud_caracteres_segmento,
                        "processing_timestamp": segment.timestamp_procesamiento,
                        "source_file_path": segment.ruta_archivo_original,
                        "document_hash": segment.hash_documento_original,
                        "document_title": segment.titulo_documento,
                        "document_author": segment.autor_documento,
                        "publication_date": segment.fecha_publicacion_documento,
                        "publisher": segment.editorial_documento,
                        "isbn": segment.isbn_documento,
                        "additional_metadata": segment_metadata,
                        "pipeline_version": segment.version_pipeline_etl,
                        "segmenter_used": segment.nombre_segmentador_usado,
                        # Campos legacy para compatibilidad temporal
                        "_legacy_hierarchy": segment_hierarchy,
                        "_legacy_processing_notes": processing_notes
                    }
                else:
                    # Es un diccionario (compatibilidad hacia atrás)
                    segment_text = segment.get('text', '')
                    segment_type = segment.get('type', 'unknown')
                    segment_id = str(uuid.uuid4())
                    document_id = str(uuid.uuid4())
                    segment_order = i + 1
                    processing_notes = segment.get('notes', None)
                    segment_metadata = segment.get('metadata', {})
                    
                    segment_data = {
                        "segment_id": segment_id,
                        "document_id": document_id,
                        "document_language": document_metadata.get('language', 'es'),
                        "text": segment_text,
                        "segment_type": segment_type,
                        "segment_order": segment_order,
                        "text_length": len(segment_text),
                        "processing_timestamp": timestamp,
                        "source_file_path": document_metadata.get('file_path', ''),
                        "document_hash": document_metadata.get('hash', None),
                        "document_title": document_metadata.get('title', ''),
                        "document_author": document_metadata.get('author', None),
                        "publication_date": document_metadata.get('publication_date', None),
                        "publisher": document_metadata.get('publisher', None),
                        "isbn": document_metadata.get('isbn', None),
                        "additional_metadata": segment_metadata,
                        "pipeline_version": "1.0.0-refactor-ui",
                        "segmenter_used": document_metadata.get('segmenter_name', 'unknown'),
                        "_legacy_processing_notes": processing_notes
                    }
                
                # 🔧 NUEVA FUNCIONALIDAD - Detectar y manejar corrupción extrema
                is_corrupted, corruption_reason = self._detect_extreme_corruption(segment_text)
                
                if is_corrupted:
                    corrupted_segments_count += 1
                    # Reemplazar texto corrupto con mensaje descriptivo
                    segment_data["text"] = f"[CORRUPTED TEXT IN SOURCE FILE]\n\nSegment #{i+1} contains extremely corrupted text that cannot be processed correctly.\n\nReason: {corruption_reason}\n\nRecommendation: Review original PDF or try advanced OCR."
                    segment_data["text_length"] = len(segment_data["text"])
                    
                    # Log del problema
                    self.logger.warning(f"🚨 Corrupción extrema en segmento #{i+1}: {corruption_reason}")
                    
                    # Agregar información específica de corrupción
                    segment_data["additional_metadata"]["corruption_detected"] = True
                    segment_data["additional_metadata"]["corruption_reason"] = corruption_reason
                    segment_data["additional_metadata"]["original_text_length"] = len(segment_text)
                
                # Limpiar campos None/vacíos del output
                cleaned_data = {k: v for k, v in segment_data.items() if v is not None}
                results.append(cleaned_data)
            
            # Log resumen de corrupción
            if corrupted_segments_count > 0:
                self.logger.warning(f"🚨 RESUMEN DE CORRUPCIÓN: {corrupted_segments_count}/{len(segments)} segmentos tenían corrupción extrema y fueron reemplazados")
            
            # Exportar resultados
            if output_format.lower() == "json":
                # Formato JSON: crear un objeto con metadatos y array de segmentos
                output_data = {
                    "document_metadata": document_metadata,
                    "segments": results
                }
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
            else:
                # Formato NDJSON (por defecto): una línea por segmento
                with open(output_path, 'w', encoding='utf-8') as f:
                    for result in results:
                        f.write(json.dumps(result, ensure_ascii=False) + '\n')
            
            self.logger.info(f"Resultados exportados en formato {output_format.upper()}: {output_path}")
            if corrupted_segments_count > 0:
                self.logger.info(f"📊 Estadísticas de corrupción: {corrupted_segments_count} segmentos reemplazados por texto corrupto")
                
        except Exception as e:
            self.logger.error(f"Error al exportar resultados: {str(e)}")
            self.logger.warning(f"✅ EXPORTACIÓN JSON COMPLETADA EXITOSAMENTE")
        print("✅ EXPORTACIÓN JSON COMPLETADA EXITOSAMENTE")

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