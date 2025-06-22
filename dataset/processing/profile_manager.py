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

# Importar detector de perfiles automático
try:
    from .profile_detector import ProfileDetector, detect_profile_for_file, get_profile_detection_config
    PROFILE_DETECTION_AVAILABLE = True
except ImportError:
    ProfileDetector = None
    detect_profile_for_file = None
    get_profile_detection_config = None
    PROFILE_DETECTION_AVAILABLE = False

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

# Importar módulos de deduplicación y modos de salida (opcional)
try:
    from .deduplication import get_dedup_manager
    from .output_modes import create_serializer, OutputMode
    from .dedup_config import get_config_manager, is_deduplication_enabled_for_mode
    DEDUPLICATION_AVAILABLE = True
except ImportError as e:
    get_dedup_manager = None
    create_serializer = None
    OutputMode = None
    get_config_manager = None
    is_deduplication_enabled_for_mode = None
    DEDUPLICATION_AVAILABLE = False

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
        
        # Registrar MarkdownSegmenter manualmente
        try:
            from .segmenters.markdown_segmenter import MarkdownSegmenter
            self.register_segmenter('markdown', MarkdownSegmenter)
            self.logger.info("[OK] MarkdownSegmenter registrado manualmente")
        except Exception as e:
            self.logger.warning(f"[WARN] No se pudo registrar MarkdownSegmenter: {e}")
        
        # Registrar MarkdownVerseSegmenter manualmente
        try:
            from .segmenters.markdown_verse_segmenter import MarkdownVerseSegmenter
            self.register_segmenter('markdown_verse', MarkdownVerseSegmenter)
            self.logger.info("[OK] MarkdownVerseSegmenter registrado manualmente")
        except Exception as e:
            self.logger.warning(f"[WARN] No se pudo registrar MarkdownVerseSegmenter: {e}")
        
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
            self.logger.info("[OK] MarkdownPDFLoader registrado manualmente")
        except Exception as e:
            self.logger.warning(f"[WARN] No se pudo registrar MarkdownPDFLoader: {e}")
    
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
        
        # SPECIAL CASE: Si es perfil verso O prosa y archivo PDF, usar MarkdownPDFLoader
        if profile_name in ['verso', 'prosa'] and extension == '.pdf':
            try:
                from .loaders.markdown_pdf_loader import MarkdownPDFLoader
                self.logger.info(f"[PDF] Usando MarkdownPDFLoader para perfil {profile_name}")
                loader_class = MarkdownPDFLoader
            except ImportError:
                self.logger.warning("[WARN] MarkdownPDFLoader no disponible, usando PDFLoader tradicional")
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
    
    def create_segmenter(self, profile_name: str, file_path: str = None) -> Optional[BaseSegmenter]:
        """
        Crea una instancia de segmentador según el perfil.
        
        Args:
            profile_name: Nombre del perfil a usar
            file_path: Ruta del archivo (para detectar si usar MarkdownSegmenter)
            
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
        
        # [OK] CORREGIDO: El segmentador se determina por el TIPO DE CONTENIDO (prosa/verso)
        # NO por el formato de archivo. La conversión PDF → Markdown es solo para preservar estructura visual.
        # Cada perfil debe especificar su segmentador correcto en su configuración.
        
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
                                      main_author_detection_info: Optional[Dict[str, Any]] = None,
                                      file_document_id: Optional[str] = None) -> ProcessedContentItem:
        """
        [CONFIG] FUNCIÓN UNIFICADA SIMPLIFICADA: Crea ProcessedContentItem con estructura limpia en inglés.
        
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
            
            # NUEVO: Incluir información de página original si está disponible
            if segment_metadata.get('page'):
                additional_metadata_clean['originalPage'] = segment_metadata['page']
            elif segment_data.get('page'):
                additional_metadata_clean['originalPage'] = segment_data['page']
        else:
            text_content = str(segment_data) if segment_data else ''
            segment_type = 'text_block'
            segment_order = segment_index + 1
        
        # 5. CREAR ProcessedContentItem CON ESTRUCTURA LIMPIA
        # [CONFIG] CORREGIDO: Usar file_document_id consistente para todos los segmentos del mismo archivo
        final_document_id = file_document_id or processed_document_metadata.get('hash_documento_original') or processed_document_metadata.get('document_hash')
        if not final_document_id:
            # Generar ID consistente basado en la ruta del archivo (mismo ID para el mismo archivo)
            final_document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(Path(file_path).absolute())))
        
        return ProcessedContentItem(
            segment_id=str(uuid.uuid4()),
            document_id=final_document_id,
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
                    folder_structure_info: Optional[Dict[str, Any]] = None,
                    output_mode: str = "biblioperson") -> tuple:
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
            output_mode: Modo de salida ("generic" o "biblioperson")
            
        Returns:
            Tuple con: (Lista de unidades procesadas, Estadísticas del segmentador, Metadatos del documento)
        """
        
        # [DEBUG] LOGGING DETALLADO PARA DEBUG DE EXPORTACIÓN
        self.logger.warning(f"[DEBUG] INICIO process_file - output_file recibido: '{output_file}'")
        self.logger.warning(f"[DEBUG] INICIO process_file - output_format: '{output_format}'")
        print(f"[DEBUG] INICIO process_file - output_file recibido: '{output_file}'")
        print(f"[DEBUG] INICIO process_file - output_format: '{output_format}'")
        
        if not os.path.exists(file_path):
            self.logger.error(f"Archivo no encontrado: {file_path}")
            # Devolver la estructura de tupla esperada por process_file.py
            return [], {}, {'error': f"Archivo no encontrado: {file_path}"}
        
        # [CONFIG] GENERAR DOCUMENT_ID ÚNICO PARA TODO EL ARCHIVO
        # Este ID será compartido por todos los segmentos del mismo archivo
        file_document_id = None
        
        # [CONFIG] SISTEMA DE DEDUPLICACIÓN (opcional y configurable)
        document_hash = None
        if DEDUPLICATION_AVAILABLE and is_deduplication_enabled_for_mode(output_mode.lower()):
            try:
                config_manager = get_config_manager()
                dedup_config = config_manager.get_deduplication_config()
                
                # Verificar compatibilidad del perfil y formato de archivo
                if (config_manager.is_profile_supported(profile_name) and 
                    config_manager.is_file_format_supported(file_path)):
                    
                    dedup_manager = get_dedup_manager()
                    document_hash, is_new_document = dedup_manager.check_and_register(file_path)
                    
                    if not is_new_document:
                        # Documento duplicado detectado
                        duplicate_info = dedup_manager.get_duplicate_info(document_hash)
                        self.logger.warning(f"[RETRY] Documento duplicado detectado: {Path(file_path).name}")
                        self.logger.warning(f"   Original procesado: {duplicate_info['first_seen']}")
                        self.logger.warning(f"   Ruta original: {duplicate_info['file_path']}")
                        
                        # Devolver información del duplicado en lugar de procesar
                        return [], {}, {
                            'duplicate_detected': True,
                            'document_hash': document_hash,
                            'original_file_path': duplicate_info['file_path'],
                            'first_seen': duplicate_info['first_seen'],
                            'current_file_path': str(Path(file_path).absolute()),
                            'message': f"Documento duplicado. Original procesado el {duplicate_info['first_seen']}"
                        }
                    else:
                        self.logger.info(f"[OK] Documento nuevo registrado: {document_hash[:8]}...")
                        # Usar el hash de deduplicación como document_id
                        file_document_id = document_hash
                else:
                    if dedup_config.warn_when_disabled:
                        self.logger.info(f"[INFO] Deduplicación no aplicable para perfil '{profile_name}' o formato '{Path(file_path).suffix}'")
                    
            except Exception as e:
                config_manager = get_config_manager() if get_config_manager else None
                dedup_config = config_manager.get_deduplication_config() if config_manager else None
                
                if dedup_config and dedup_config.log_errors:
                    self.logger.error(f"Error en sistema de deduplicación: {str(e)}")
                
                if not dedup_config or dedup_config.continue_on_error:
                    # Continuar procesamiento sin deduplicación en caso de error
                    document_hash = None
                    if dedup_config and dedup_config.log_errors:
                        self.logger.info("Continuando procesamiento sin deduplicación debido al error")
                else:
                    # Re-lanzar el error si la configuración no permite continuar
                    raise
        elif not DEDUPLICATION_AVAILABLE:
            self.logger.debug("Sistema de deduplicación no disponible (módulos no importados)")
        else:
            self.logger.debug(f"Deduplicación deshabilitada para modo '{output_mode}'")
            config_manager = get_config_manager() if get_config_manager else None
            if config_manager:
                dedup_config = config_manager.get_deduplication_config()
                if dedup_config.warn_when_disabled:
                    self.logger.info(f"[INFO] Deduplicación deshabilitada para modo '{output_mode}'")
        
        # [DEBUG] DETECCIÓN AUTOMÁTICA DE PERFIL
        if profile_name == "automático":
            self.logger.info(f"[DEBUG] INICIANDO DETECCIÓN AUTOMÁTICA DE PERFIL: {Path(file_path).name}")
            
            # Para PDFs, extraer contenido preservando estructura original con pymupdf
            content_sample = None
            if file_path.lower().endswith('.pdf'):
                try:
                    # Usar pymupdf para extraer markdown preservando estructura visual
                    import fitz  # pymupdf
                    
                    self.logger.debug(f"[DEBUG] Extrayendo contenido con pymupdf para preservar estructura original...")
                    
                    doc = fitz.open(file_path)
                    markdown_content = ""
                    
                    # Extraer las primeras páginas para análisis (suficiente para detección)
                    max_pages = min(5, len(doc))
                    
                    for page_num in range(max_pages):
                        page = doc.load_page(page_num)
                        
                        # Extraer como markdown preservando estructura visual
                        page_markdown = page.get_text("markdown")
                        
                        if page_markdown.strip():
                            # Verificar corrupción en el contenido de la página
                            corruption_ratio = self._detect_text_corruption(page_markdown)
                            
                            if corruption_ratio > 0.3:
                                self.logger.debug(f"[SKIP] Saltando página {page_num + 1} (corrupción: {corruption_ratio:.1%})")
                                continue
                            
                            markdown_content += page_markdown + "\n\n"
                    
                    doc.close()
                    
                    # Usar el contenido markdown como muestra para detección
                    content_sample = markdown_content.strip()
                    
                    self.logger.debug(f"[DEBUG] Contenido markdown extraído: {len(content_sample)} caracteres")
                    
                    # DEBUG: Mostrar muestra del contenido markdown
                    if content_sample:
                        lines = content_sample.split('\n')
                        self.logger.debug(f"[DEBUG] DEBUG MARKDOWN: {len(lines)} líneas totales")
                        self.logger.debug(f"[DEBUG] DEBUG PRIMERAS 3 LÍNEAS:")
                        for i, line in enumerate(lines[:3]):
                            self.logger.debug(f"[DEBUG]   [{i+1}]: '{line}'")
                    
                except Exception as e:
                    self.logger.warning(f"[WARN] Error extrayendo contenido markdown para detección: {str(e)}")
            
            # Detectar perfil automáticamente
            detected_profile = self.get_profile_for_file(file_path, content_sample)
            if detected_profile:
                profile_name = detected_profile
                self.logger.info(f"[OK] PERFIL AUTO-DETECTADO: '{profile_name}' para {Path(file_path).name}")
            else:
                # Fallback a prosa si no se puede detectar
                profile_name = "prosa"
                self.logger.warning(f"[WARN] No se pudo detectar perfil, usando fallback: '{profile_name}'")
        
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
                
                # [CONFIG] PRIORIDAD: job_config_dict > perfil
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
                    self.logger.debug(f"[CONFIG] Configuración JSON aplicada: {json_config}")
                else:
                    self.logger.info(f"📄 JSONLoader sin configuración específica - usando valores por defecto")
            
            loader = loader_class(file_path, **loader_kwargs)
            loaded_data = loader.load()
            
            # Asegurar que las claves existan, incluso si están vacías
            raw_blocks = loaded_data.get('blocks', [])
            raw_document_metadata = loaded_data.get('document_metadata', {})
            raw_document_metadata.setdefault('source_file_path', str(Path(file_path).absolute()))
            raw_document_metadata.setdefault('file_format', Path(file_path).suffix.lower())
            raw_document_metadata.setdefault('profile_used', profile_name)
            
            # Añadir hash del documento si está disponible (modo biblioperson)
            if document_hash:
                raw_document_metadata['document_hash'] = document_hash

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
        
        # Para archivos JSON: aplicar pre-procesador para limpieza de caracteres de control
        if file_path.lower().endswith('.json'):
            # CORREGIDO: Los archivos JSON también necesitan pre-procesamiento para limpieza de caracteres
            profile = self.get_profile(profile_name)
            preprocessor_config = profile.get('pre_processor_config') if profile else None
            
            # Crear pre-procesador con configuración por defecto que incluye limpieza Unicode
            from dataset.processing.pre_processors.common_block_preprocessor import CommonBlockPreprocessor
            common_preprocessor = CommonBlockPreprocessor(config=preprocessor_config)
            
            try:
                self.logger.info(f"🧹 Aplicando limpieza de caracteres de control a archivo JSON: {file_path}")
                processed_blocks, processed_document_metadata = common_preprocessor.process(raw_blocks, raw_document_metadata)
                self.logger.info(f"[OK] Limpieza completada para JSON: {len(processed_blocks)} bloques procesados")
            except Exception as e:
                self.logger.error(f"Error durante limpieza de JSON {file_path}: {str(e)}")
                # En caso de error, usar bloques sin procesar pero registrar el problema
                processed_blocks = raw_blocks
                processed_document_metadata = raw_document_metadata
                processed_document_metadata['preprocessing_error'] = str(e)
            
            # [CONFIG] NUEVO: Detectar idioma también para JSON
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
            
            self.logger.warning(f"[DEBUG] DEBUG: Tenemos {len(processed_blocks)} bloques procesados")
            if processed_blocks:
                self.logger.warning(f"[DEBUG] DEBUG: Estructura del primer bloque: {processed_blocks[0]}")
            
            for i, block in enumerate(processed_blocks):
                # [CONFIG] USAR FUNCIÓN UNIFICADA: Ahora con detección de idioma
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
                    None,  # main_author_detection_info - no aplicable para JSON directo
                    file_document_id  # [CONFIG] CORREGIDO: Pasar file_document_id consistente
                )
                segments.append(segment)
            
            segmenter_stats = {
                'json_elements_processed': len(segments),
                'processing_method': 'direct_conversion',
                'bypassed_segmenter': True
            }
            
            # Para JSON: retornar directamente sin procesamiento adicional
            self.logger.info(f"[OK] JSON procesado directamente: {len(segments)} segmentos creados")
            
            # [OK] CORREGIDO: Exportar si se especificó ruta de salida
            self.logger.warning(f"[DEBUG] VERIFICANDO EXPORTACIÓN - output_file: '{output_file}' (tipo: {type(output_file)})")
            print(f"[DEBUG] VERIFICANDO EXPORTACIÓN - output_file: '{output_file}' (tipo: {type(output_file)})")
            
            if output_file:
                self.logger.warning(f"📤 INICIANDO EXPORTACIÓN - {len(segments)} segmentos JSON a: {output_file}")
                print(f"📤 INICIANDO EXPORTACIÓN - {len(segments)} segmentos JSON a: {output_file}")
                try:
                    self._export_results(segments, output_file, processed_document_metadata, output_format, output_mode)
                    self.logger.warning(f"[OK] EXPORTACIÓN JSON COMPLETADA EXITOSAMENTE")
                    print(f"[OK] EXPORTACIÓN JSON COMPLETADA EXITOSAMENTE")
                except Exception as e:
                    self.logger.error(f"❌ ERROR EN EXPORTACIÓN JSON: {str(e)}")
                    print(f"❌ ERROR EN EXPORTACIÓN JSON: {str(e)}")
                    self.logger.exception("Detalles del error de exportación:")
            else:
                self.logger.warning(f"[WARN] NO SE EXPORTARÁ - output_file es None o vacío")
                print(f"[WARN] NO SE EXPORTARÁ - output_file es None o vacío")
            
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
                    # Log prominente para mostrar autor detectado por documento
                    filename = Path(file_path).name
                    confidence_pct = main_author_detection_info['confidence'] * 100
                    self.logger.info(f"[TARGET] ===== AUTOR DETECTADO AUTOMÁTICAMENTE =====")
                    self.logger.info(f"📄 Documento: {filename}")
                    self.logger.info(f"✍️  Autor: {main_document_author_name}")
                    self.logger.info(f"📊 Confianza: {confidence_pct:.1f}% ({main_author_detection_info['confidence']:.3f})")
                    self.logger.info(f"[DEBUG] Método: {main_author_detection_info['method']}")
                    self.logger.info(f"[TARGET] ============================================")
                    self.logger.info(f"")
                    # --- COPIAR INMEDIATAMENTE A processed_document_metadata ---
                    processed_document_metadata['author'] = main_document_author_name
                    processed_document_metadata['author_confidence'] = main_author_detection_info.get('confidence', 0.0)
                    processed_document_metadata['author_detection_method'] = main_author_detection_info.get('method', 'unknown')
                    processed_document_metadata['author_detection_source'] = main_author_detection_info.get('source', 'enhanced_contextual')
                else:
                    filename = Path(file_path).name
                    self.logger.warning(f"❌ No se pudo detectar autor automáticamente para: {filename}")
                    main_document_author_name = None
                    
            except Exception as e:
                filename = Path(file_path).name
                self.logger.error(f"❌ Error durante detección de autor automático para {filename}: {str(e)}")
                main_document_author_name = None
                main_author_detection_info = {'error': str(e)}
                
            # 3. Crear segmentador según perfil
            profile = self.get_profile(profile_name) # Recargar perfil por si se modificó
            segmenter = self.create_segmenter(profile_name, file_path)
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
            
            # NUEVO: Implementar fallback verso → prosa si no hay segmentos
            if profile_name == 'verso' and len(segments) == 0 and len(processed_blocks) > 0:
                self.logger.warning(f"⚠️ VerseSegmenter produjo 0 segmentos para {file_path}")
                self.logger.warning(f"🔄 Aplicando fallback: cambiando a perfil 'prosa'")
                
                # Crear segmentador de prosa
                prosa_segmenter = self.create_segmenter('prosa', file_path)
                if prosa_segmenter:
                    segments = prosa_segmenter.segment(blocks=processed_blocks)
                    segmenter_stats = prosa_segmenter.get_stats() if hasattr(prosa_segmenter, 'get_stats') else {}
                    
                    # Actualizar el nombre del segmentador usado
                    if profile:
                        profile['_actual_segmenter'] = 'prosa_fallback'
                    
                    self.logger.info(f"✅ Fallback exitoso: {len(segments)} segmentos generados con perfil 'prosa'")
                else:
                    self.logger.error(f"❌ No se pudo crear segmentador de prosa para fallback")
        
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
                # [CONFIG] USAR FUNCIÓN UNIFICADA para archivos no-JSON también
                item = self._create_processed_content_item(
                    processed_document_metadata,
                    segment_dict,
                    file_path,
                    language_override,
                    author_override,
                    detected_lang,
                    i,
                    job_config_dict,
                    profile.get('_actual_segmenter', profile.get('segmenter', 'desconocido')) if profile else 'desconocido',
                    main_document_author_name,
                    main_author_detection_info,
                    file_document_id  # [CONFIG] CORREGIDO: Pasar file_document_id consistente
                )
                
                processed_content_items.append(item)
        else: 
            # Si no hay segmentos del segmentador, processed_content_items quedará vacía
            pass
        
        # 5. TODO: Aplicar post-procesador si está configurado
        
        # 6. Agregar información del autor detectado al processed_document_metadata para la UI
        if main_document_author_name:
            processed_document_metadata['author'] = main_document_author_name
            processed_document_metadata['author_confidence'] = main_author_detection_info.get('confidence', 0.0) if main_author_detection_info else 0.0
            processed_document_metadata['author_detection_method'] = main_author_detection_info.get('method', 'unknown') if main_author_detection_info else 'unknown'
            processed_document_metadata['author_detection_source'] = main_author_detection_info.get('source', 'enhanced_contextual') if main_author_detection_info else 'unknown'
        
        # 7. Exportar si se especificó ruta de salida
        # Usar processed_document_metadata para la parte de metadatos del documento
        # y processed_content_items para los segmentos.
        if output_file: # [OK] CORREGIDO: output_file es la ruta del archivo de salida
            # El primer if es para si manager.process_file devolvió segmentos (ahora processed_content_items)
            if processed_content_items:
                self._export_results(processed_content_items, output_file, processed_document_metadata, output_format, output_mode)
            # El segundo elif es para cuando no hubo segmentos (lista vacía) pero SÍ hay un output_path
            # y queremos exportar los metadatos del documento (que pueden contener un error o advertencia).
            elif not processed_content_items: 
                self.logger.info(f"No se generaron ProcessedContentItems para {file_path}, pero se exportarán metadatos a {output_file}")
                self._export_results([], output_file, processed_document_metadata, output_format, output_mode)

        # Devolver la tupla completa como espera process_file.py, usando la nueva lista de dataclasses
        return processed_content_items, segmenter_stats, processed_document_metadata
    
    def _detect_text_corruption(self, text: str) -> float:
        """
        Detecta la ratio de corrupción en un texto basado en caracteres duplicados consecutivos.
        
        Args:
            text: Texto a analizar
            
        Returns:
            float: Ratio de corrupción (0.0 = sin corrupción, 1.0 = completamente corrupto)
        """
        if not text or len(text) < 10:
            return 0.0
        
        # Contar caracteres duplicados consecutivos
        duplicated_chars = 0
        total_chars = len(text)
        
        i = 0
        while i < len(text) - 1:
            if text[i] == text[i + 1] and text[i].isalpha():
                # Encontrar cuántos caracteres consecutivos son iguales
                consecutive_count = 1
                j = i + 1
                while j < len(text) and text[j] == text[i]:
                    consecutive_count += 1
                    j += 1
                
                # Si hay más de 1 carácter consecutivo igual, es probable corrupción
                if consecutive_count > 1:
                    duplicated_chars += consecutive_count - 1  # Solo contar los extras
                
                i = j
            else:
                i += 1
        
        corruption_ratio = duplicated_chars / total_chars if total_chars > 0 else 0.0
        return corruption_ratio

    def _detect_extreme_corruption(self, text: str, corruption_threshold: float = 0.7) -> Tuple[bool, str]:
        """
        [CONFIG] NUEVA FUNCIONALIDAD - Detecta corrupción extrema en texto.
        
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

    def _clean_for_json_serialization(self, obj):
        """
        Limpia recursivamente un objeto para asegurar serialización JSON segura.
        Remueve o reemplaza caracteres de control que pueden causar errores de JSON.
        """
        if isinstance(obj, str):
            # Limpiar caracteres de control problemáticos para JSON
            import re
            # Remover caracteres de control ASCII (0x00-0x1F) excepto \n, \r, \t
            cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', ' ', obj)
            # Remover caracteres de control extendidos (0x7F-0x9F)
            cleaned = re.sub(r'[\x7F-\x9F]', ' ', cleaned)
            # Remover caracteres Unicode problemáticos para JSON
            cleaned = re.sub(r'[\uFEFF\u200B-\u200F\u2028\u2029]', ' ', cleaned)
            # Filtrar cualquier carácter que no sea seguro para JSON
            safe_chars = []
            for char in cleaned:
                if (ord(char) >= 32 and ord(char) != 127) or char in '\n\r\t':
                    safe_chars.append(char)
                else:
                    safe_chars.append(' ')
            return ''.join(safe_chars).strip()
        elif isinstance(obj, dict):
            return {key: self._clean_for_json_serialization(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json_serialization(item) for item in obj]
        else:
            return obj

    def _export_results(self, segments: List[Any], output_file: str, document_metadata: Optional[Dict[str, Any]] = None, output_format: str = "ndjson", output_mode: str = "biblioperson"):
        """
        Exporta los segmentos procesados usando el sistema de modos de salida.
        
        Args:
            segments: Lista de segmentos procesados
            output_file: Archivo de salida
            document_metadata: Metadatos del documento
            output_format: Formato de salida ("ndjson" o "json")
            output_mode: Modo de salida ("generic" o "biblioperson")
        """
        # [DEBUG] LOGGING DETALLADO PARA DEBUG DE EXPORTACIÓN
        self.logger.warning(f"[DEBUG] _export_results INICIADO")
        self.logger.warning(f"[DEBUG] Parámetros recibidos:")
        self.logger.warning(f"[DEBUG]   - segments: {len(segments)} elementos")
        self.logger.warning(f"[DEBUG]   - output_file: '{output_file}'")
        self.logger.warning(f"[DEBUG]   - output_format: '{output_format}'")
        self.logger.warning(f"[DEBUG]   - output_mode: '{output_mode}'")
        print(f"[DEBUG] _export_results INICIADO con {len(segments)} segmentos")
        print(f"[DEBUG] Exportando a: {output_file} en modo {output_mode}")
        
        try:
            # Verificar disponibilidad del sistema de modos de salida
            if not DEDUPLICATION_AVAILABLE or not create_serializer:
                # Fallback al método de exportación original
                self.logger.warning("Sistema de modos de salida no disponible, usando exportación tradicional")
                self._export_results_fallback(segments, output_file, document_metadata, output_format)
                return
            
            # Crear serializador según el modo
            serializer = create_serializer(output_mode)
            
            # Procesar segmentos corruptos antes de la serialización
            processed_segments = []
            corrupted_segments_count = 0
            
            self.logger.info("🧹 INICIANDO EXPORTACIÓN CON LIMPIEZA MEJORADA DE CARACTERES DE CONTROL")
            
            for i, segment in enumerate(segments):
                # Extraer texto para verificación de corrupción
                if hasattr(segment, 'text'):
                    segment_text = segment.text
                elif hasattr(segment, 'texto_segmento'):
                    segment_text = segment.texto_segmento
                else:
                    segment_text = segment.get('text', '') if isinstance(segment, dict) else str(segment)
                
                # [CONFIG] DETECTAR Y MANEJAR CORRUPCIÓN EXTREMA
                is_corrupted, corruption_reason = self._detect_extreme_corruption(segment_text)
                
                if is_corrupted:
                    corrupted_segments_count += 1
                    
                    # Crear copia del segmento con texto corregido
                    if hasattr(segment, 'text'):
                        # ProcessedContentItem nuevo
                        corrected_segment = segment
                        corrected_segment.text = f"[CORRUPTED TEXT IN SOURCE FILE]\n\nSegment #{i+1} contains extremely corrupted text that cannot be processed correctly.\n\nReason: {corruption_reason}\n\nRecommendation: Review original PDF or try advanced OCR."
                        corrected_segment.text_length = len(corrected_segment.text)
                    
                        # Añadir información de corrupción a metadatos
                        if not corrected_segment.additional_metadata:
                            corrected_segment.additional_metadata = {}
                        corrected_segment.additional_metadata["corruption_detected"] = True
                        corrected_segment.additional_metadata["corruption_reason"] = corruption_reason
                        corrected_segment.additional_metadata["original_text_length"] = len(segment_text)
                        
                    elif hasattr(segment, 'texto_segmento'):
                        # ProcessedContentItem viejo
                        corrected_segment = segment
                        corrected_segment.texto_segmento = f"[CORRUPTED TEXT IN SOURCE FILE]\n\nSegment #{i+1} contains extremely corrupted text that cannot be processed correctly.\n\nReason: {corruption_reason}\n\nRecommendation: Review original PDF or try advanced OCR."
                        corrected_segment.longitud_caracteres_segmento = len(corrected_segment.texto_segmento)
                    
                        # Añadir información de corrupción a metadatos
                        if not corrected_segment.metadatos_adicionales_fuente:
                            corrected_segment.metadatos_adicionales_fuente = {}
                        corrected_segment.metadatos_adicionales_fuente["corruption_detected"] = True
                        corrected_segment.metadatos_adicionales_fuente["corruption_reason"] = corruption_reason
                        corrected_segment.metadatos_adicionales_fuente["original_text_length"] = len(segment_text)
                
                    else:
                        # Diccionario
                        corrected_segment = segment.copy() if isinstance(segment, dict) else {"text": str(segment)}
                        corrected_segment["text"] = f"[CORRUPTED TEXT IN SOURCE FILE]\n\nSegment #{i+1} contains extremely corrupted text that cannot be processed correctly.\n\nReason: {corruption_reason}\n\nRecommendation: Review original PDF or try advanced OCR."
                        
                        if "metadata" not in corrected_segment:
                            corrected_segment["metadata"] = {}
                        corrected_segment["metadata"]["corruption_detected"] = True
                        corrected_segment["metadata"]["corruption_reason"] = corruption_reason
                        corrected_segment["metadata"]["original_text_length"] = len(segment_text)
                    
                    # Log del problema
                    self.logger.warning(f"🚨 Corrupción extrema en segmento #{i+1}: {corruption_reason}")
                    processed_segments.append(corrected_segment)
                else:
                    processed_segments.append(segment)
            
            # Log resumen de corrupción
            if corrupted_segments_count > 0:
                self.logger.warning(f"🚨 RESUMEN DE CORRUPCIÓN: {corrupted_segments_count}/{len(segments)} segmentos tenían corrupción extrema y fueron reemplazados")
            
            # Usar el serializador para exportar
            serializer.export_segments(
                processed_segments, 
                output_file, 
                document_metadata, 
                output_format
            )
            
            self.logger.info(f"Resultados exportados en modo {output_mode.upper()} formato {output_format.upper()}: {output_file}")
            if corrupted_segments_count > 0:
                self.logger.info(f"📊 Estadísticas de corrupción: {corrupted_segments_count} segmentos reemplazados por texto corrupto")
                
        except Exception as e:
            self.logger.error(f"Error al exportar resultados: {str(e)}")
            raise
        
        self.logger.warning(f"[OK] EXPORTACIÓN COMPLETADA EXITOSAMENTE")
        print("[OK] EXPORTACIÓN COMPLETADA EXITOSAMENTE")
    
    def _export_results_fallback(self, segments: List[Any], output_file: str, document_metadata: Optional[Dict[str, Any]] = None, output_format: str = "ndjson"):
        """
        Método de fallback para exportación cuando el sistema de modos no está disponible.
        
        Args:
            segments: Lista de segmentos procesados
            output_file: Archivo de salida
            document_metadata: Metadatos del documento
            output_format: Formato de salida ("ndjson" o "json")
        """
        self.logger.info("[RETRY] Usando exportación tradicional (fallback)")
        
        try:
            # Asegurar que el directorio de salida existe
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Procesar segmentos para limpieza básica
            processed_segments = []
            for segment in segments:
                # Limpiar caracteres de control básicos
                if hasattr(segment, 'text'):
                    segment.text = self._clean_control_characters(segment.text)
                elif hasattr(segment, 'texto_segmento'):
                    segment.texto_segmento = self._clean_control_characters(segment.texto_segmento)
                elif isinstance(segment, dict) and 'text' in segment:
                    segment['text'] = self._clean_control_characters(segment['text'])
                
                processed_segments.append(segment)
            
            # Exportar según el formato
            if output_format.lower() == "json":
                # Exportar como JSON array
                with open(output_file, 'w', encoding='utf-8') as f:
                    import json
                    json_data = []
                    for segment in processed_segments:
                        if hasattr(segment, '__dict__'):
                            json_data.append(self._clean_for_json_serialization(segment.__dict__))
                        else:
                            json_data.append(self._clean_for_json_serialization(segment))
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
            else:
                # Exportar como NDJSON (por defecto)
                with open(output_file, 'w', encoding='utf-8') as f:
                    import json
                    for segment in processed_segments:
                        if hasattr(segment, '__dict__'):
                            segment_dict = self._clean_for_json_serialization(segment.__dict__)
                        else:
                            segment_dict = self._clean_for_json_serialization(segment)
                        f.write(json.dumps(segment_dict, ensure_ascii=False) + '\n')
            
            self.logger.info(f"Exportación tradicional completada: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error en exportación tradicional: {str(e)}")
            raise
    
    def _clean_control_characters(self, text: str) -> str:
        """
        Limpia caracteres de control básicos del texto.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remover caracteres de control comunes
        import re
        # Mantener saltos de línea y tabulaciones, remover otros caracteres de control
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return cleaned

    def get_profile_for_file(self, file_path: str, content_sample: Optional[str] = None) -> Optional[str]:
        """
        Sugiere el perfil más adecuado para un archivo usando detección automática avanzada.
        
        Args:
            file_path: Ruta al archivo
            content_sample: Contenido extraído del archivo (opcional, para mejor detección)
            
        Returns:
            Nombre del perfil sugerido o None si no hay sugerencia
        """
        # Intentar detección automática primero
        detected_profile = self.auto_detect_profile(file_path, content_sample)
        if detected_profile:
            self.logger.info(f"[TARGET] Perfil detectado automáticamente: {detected_profile}")
            return detected_profile
        
        # Fallback al método manual si la detección automática falla
        self.logger.debug("[RETRY] Usando detección manual como fallback")
        return self._get_manual_profile_fallback(file_path)

    def auto_detect_profile(self, file_path: str, content_sample: Optional[str] = None) -> Optional[str]:
        """
        [DEBUG] DETECCIÓN AUTOMÁTICA DE PERFILES - ALGORITMO CONSERVADOR
        
        Detecta automáticamente el perfil más adecuado para un archivo usando análisis estructural.
        
        ALGORITMO CONSERVADOR:
        - JSON: Detección por extensión (fácil)
        - PROSA: Por defecto para todo contenido
        - VERSO: Solo cuando >80% del texto cumple criterios estructurales puros
        
        Args:
            file_path: Ruta al archivo
            content_sample: Muestra del contenido (opcional, se leerá si no se proporciona)
            
        Returns:
            Nombre del perfil detectado o None si no se puede detectar
        """
        if not PROFILE_DETECTION_AVAILABLE:
            self.logger.warning("[WARN] Sistema de detección automática de perfiles no disponible")
            return self.get_profile_for_file(file_path)  # Fallback al método manual
        
        try:
            self.logger.info(f"[DEBUG] INICIANDO DETECCIÓN AUTOMÁTICA DE PERFIL: {Path(file_path).name}")
            
            # Configuración conservadora
            config = get_profile_detection_config()
            config['debug'] = self.logger.isEnabledFor(logging.DEBUG)
            
            # Detectar perfil usando el algoritmo conservador
            candidate = detect_profile_for_file(file_path, config, content_sample)
            
            if candidate and candidate.confidence >= 0.35:  # Umbral mínimo de confianza ajustado
                confidence_pct = candidate.confidence * 100
                self.logger.info(f"[OK] PERFIL AUTO-DETECTADO: '{candidate.profile_name}' "
                               f"(confianza: {confidence_pct:.1f}%)")
                
                # Log de las razones de la detección
                for reason in candidate.reasons:
                    self.logger.debug(f"   📋 {reason}")
                
                # Verificar que el perfil detectado existe en el sistema
                if candidate.profile_name in self.profiles:
                    return candidate.profile_name
                else:
                    self.logger.warning(f"[WARN] Perfil detectado '{candidate.profile_name}' no existe en el sistema")
                    # Fallback al método manual si el perfil detectado no existe
                    self.logger.info("[RETRY] Usando método manual como fallback")
                    return self._get_manual_profile_fallback(file_path)
            else:
                confidence_pct = candidate.confidence * 100 if candidate else 0
                self.logger.warning(f"[WARN] Confianza insuficiente para detección automática: {confidence_pct:.1f}%")
                # Fallback al método manual cuando la confianza es muy baja
                self.logger.info("[RETRY] Usando método manual como fallback")
                return self._get_manual_profile_fallback(file_path)
                
        except Exception as e:
            self.logger.error(f"❌ Error en detección automática de perfil: {str(e)}")
            # Fallback al método manual en caso de error
            self.logger.info("[RETRY] Usando método manual como fallback por error")
            return self._get_manual_profile_fallback(file_path)

    def _get_manual_profile_fallback(self, file_path: str) -> Optional[str]:
        """
        Método de fallback que usa detección manual sin llamar a auto_detect_profile.
        Evita bucles infinitos.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Nombre del perfil sugerido o None si no hay sugerencia
        """
        self.logger.debug("[RETRY] Ejecutando detección manual como fallback")
        
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        filename = file_path.stem.lower()
        
        # Detección por extensión JSON
        if extension == '.json':
            if 'json' in self.profiles:
                self.logger.debug("Perfil json detectado por extensión")
                return 'json'
        
        # Palabras clave que sugieren tipos de contenido
        poem_keywords = ['poema', 'poemas', 'poesía', 'poesías', 'versos', 'verso', 'estrofa', 'poeta', 
                         'poem', 'poetry', 'lyric', 'lyrics', 'canción', 'canciones']
        book_keywords = ['libro', 'capitulo', 'capítulos', 'book', 'chapter', 'section', 'manual', 
                        'guía', 'documento', 'texto', 'escrito']
        
        # Comprobar primero en el nombre del archivo
        for keyword in poem_keywords:
            if keyword in filename:
                if 'verso' in self.profiles:
                    self.logger.debug(f"Perfil verso detectado por palabra clave en el nombre: {keyword}")
                    return 'verso'
                
        for keyword in book_keywords:
            if keyword in filename:
                if 'prosa' in self.profiles:
                    self.logger.debug(f"Perfil prosa detectado por palabra clave en el nombre: {keyword}")
                    return 'prosa'
                
        # Verificar si algún perfil tiene configuración específica para esta extensión
        for profile_name, profile in self.profiles.items():
            if 'file_types' in profile and extension in profile['file_types']:
                self.logger.debug(f"Perfil {profile_name} sugerido por tipo de archivo: {extension}")
                return profile_name
        
        # Fallback por defecto: prosa para la mayoría de documentos de texto
        if extension in ['.pdf', '.txt', '.md', '.docx', '.doc']:
            if 'prosa' in self.profiles:
                self.logger.debug(f"Perfil prosa sugerido por defecto para: {extension}")
                return 'prosa'
        
        # Si todo lo demás falla, devolver None
        self.logger.debug("No se pudo determinar perfil con método manual")
        return None

    def get_profile_detection_report(self, file_path: str, content_sample: Optional[str] = None) -> Dict[str, Any]:
        """
        Generar reporte detallado de detección de perfil para debugging.
        
        Args:
            file_path: Ruta al archivo
            content_sample: Muestra del contenido (opcional)
            
        Returns:
            Reporte detallado con métricas y análisis
        """
        if not PROFILE_DETECTION_AVAILABLE:
            return {
                'error': 'Sistema de detección automática no disponible',
                'fallback_used': True,
                'manual_suggestion': self.get_profile_for_file(file_path)
            }
        
        try:
            detector = ProfileDetector(get_profile_detection_config())
            return detector.get_detection_report(file_path, content_sample)
        except Exception as e:
            return {
                'error': f'Error generando reporte: {str(e)}',
                'file_path': str(file_path)
            }

    def validate_pipeline_compatibility(self) -> Dict[str, Any]:
        """
        Valida la compatibilidad del pipeline con el sistema de deduplicación.
        
        Returns:
            Diccionario con información de compatibilidad
        """
        compatibility_info = {
            'deduplication_available': DEDUPLICATION_AVAILABLE,
            'config_loaded': False,
            'supported_profiles': [],
            'supported_formats': [],
            'errors': [],
            'warnings': []
        }
        
        if DEDUPLICATION_AVAILABLE:
            try:
                config_manager = get_config_manager()
                compatibility_info['config_loaded'] = True
                
                compat_config = config_manager.get_compatibility_config()
                compatibility_info['supported_profiles'] = compat_config.supported_profiles
                compatibility_info['supported_formats'] = compat_config.supported_file_formats
                
                # Validar que los perfiles existan
                available_profiles = list(self.profiles.keys())
                for profile in compat_config.supported_profiles:
                    if profile not in available_profiles and profile != 'automático':
                        compatibility_info['warnings'].append(f"Perfil configurado '{profile}' no está disponible")
                
                self.logger.info("[OK] Validación de compatibilidad completada exitosamente")
                
            except Exception as e:
                compatibility_info['errors'].append(f"Error validando compatibilidad: {str(e)}")
                self.logger.error(f"Error en validación de compatibilidad: {str(e)}")
        else:
            compatibility_info['warnings'].append("Sistema de deduplicación no disponible")
        
        return compatibility_info
    
    def get_deduplication_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del sistema de deduplicación.
        
        Returns:
            Diccionario con el estado del sistema
        """
        status = {
            'available': DEDUPLICATION_AVAILABLE,
            'enabled': False,
            'database_path': None,
            'modes': {},
            'stats': None
        }
        
        if DEDUPLICATION_AVAILABLE:
            try:
                config_manager = get_config_manager()
                dedup_config = config_manager.get_deduplication_config()
                
                status['enabled'] = dedup_config.enabled
                status['database_path'] = str(config_manager.get_database_path())
                
                # Estado de los modos
                for mode in ['generic', 'biblioperson']:
                    mode_config = config_manager.get_output_mode_config(mode)
                    if mode_config:
                        status['modes'][mode] = {
                            'description': mode_config.description,
                            'deduplication_enabled': mode_config.enable_deduplication,
                            'include_hash': mode_config.include_document_hash
                        }
                
                # Estadísticas de la base de datos si está disponible
                if dedup_config.enabled:
                    try:
                        dedup_manager = get_dedup_manager()
                        status['stats'] = dedup_manager.get_stats()
                    except Exception as e:
                        status['stats'] = {'error': str(e)}
                
            except Exception as e:
                status['error'] = str(e)
        
        return status

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
        print(f"[CONFIG][CONFIG][CONFIG] CREANDO PRE-PROCESADOR: {pre_processor_type} [CONFIG][CONFIG][CONFIG]")
        print(f"[CONFIG][CONFIG][CONFIG] PERFIL RECIBIDO: {profile.get('name') if profile else 'None'} [CONFIG][CONFIG][CONFIG]")
        
        preprocessor_config = profile.get('pre_processor_config') if profile else None
        print(f"[CONFIG][CONFIG][CONFIG] CONFIG DEL PRE-PROCESADOR: {preprocessor_config} [CONFIG][CONFIG][CONFIG]")
        
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