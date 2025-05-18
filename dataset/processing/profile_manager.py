import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Type
from pathlib import Path

from .segmenters.base import BaseSegmenter
from .segmenters.verse_segmenter import VerseSegmenter
from .segmenters.heading_segmenter import HeadingSegmenter
from .loaders import BaseLoader, MarkdownLoader, NDJSONLoader, DocxLoader, txtLoader, PDFLoader, ExcelLoader, CSVLoader
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
    
    def register_default_components(self):
        """Registra los componentes por defecto del sistema."""
        # Registrar segmentadores
        self.register_segmenter('verse', VerseSegmenter)
        self.register_segmenter('heading', HeadingSegmenter)
        
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
        """Carga todos los perfiles YAML del directorio configurado."""
        if not os.path.exists(self.profiles_dir):
            self.logger.warning(f"Directorio de perfiles no encontrado: {self.profiles_dir}")
            return
        
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(('.yaml', '.yml')):
                profile_path = os.path.join(self.profiles_dir, filename)
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile = yaml.safe_load(f)
                    
                    if 'name' in profile:
                        self.profiles[profile['name']] = profile
                        self.logger.info(f"Cargado perfil: {profile['name']}")
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
        
        # Copiar thresholds del perfil
        if 'thresholds' in profile:
            config['thresholds'] = profile['thresholds']
        
        # Copiar patrones específicos
        for key in ['title_patterns', 'paragraph_patterns', 'section_patterns']:
            if key in profile:
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
                    output_path: Optional[str] = None,
                    encoding: str = 'utf-8',
                    force_content_type: Optional[str] = None,
                    confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Procesa un archivo completo usando un perfil.
        
        Args:
            file_path: Ruta al archivo a procesar
            profile_name: Nombre del perfil a usar
            output_path: Ruta para guardar resultados (opcional)
            encoding: Codificación para abrir el archivo (por defecto utf-8)
            force_content_type: Forzar un tipo específico de contenido (ignora detección automática)
            confidence_threshold: Umbral de confianza para detección de poemas (0.0-1.0)
            
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
            loader = loader_class(file_path, encoding=encoding)
            
            loaded_data = loader.load()
            
            # Asegurar que las claves existan, incluso si están vacías
            raw_blocks = loaded_data.get('blocks', [])
            raw_document_metadata = loaded_data.get('document_metadata', {})
            raw_document_metadata.setdefault('source_file_path', str(Path(file_path).absolute()))
            raw_document_metadata.setdefault('file_format', Path(file_path).suffix.lower())

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
        # TODO: Considerar si la config del preprocesador debe venir del perfil YAML
        preprocessor_config = self.get_profile(profile_name).get('common_preprocessor_config') if self.get_profile(profile_name) else None
        common_preprocessor = CommonBlockPreprocessor(config=preprocessor_config)
        try:
            self.logger.info(f"Aplicando CommonBlockPreprocessor a {len(raw_blocks)} bloques.")
            processed_blocks, processed_document_metadata = common_preprocessor.process(raw_blocks, raw_document_metadata)
            self.logger.debug(f"CommonBlockPreprocessor finalizado. Bloques resultantes: {len(processed_blocks)}.")
        except Exception as e:
            self.logger.error(f"Excepción durante CommonBlockPreprocessor para archivo {file_path}: {str(e)}", exc_info=True)
            # Si el preprocesador falla, usamos los datos crudos del loader pero añadimos un error
            raw_document_metadata['error'] = (raw_document_metadata.get('error', '') + 
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
            processed_document_metadata['error'] = (processed_document_metadata.get('error', '') + 
                                                 f"; No se pudo crear el segmentador '{profile.get('segmenter') if profile else 'desconocido'}' para el perfil '{profile_name}'.").strip('; ')
            return processed_blocks, {}, processed_document_metadata
        
        # Configurar umbral de confianza si el segmentador lo soporta
        if hasattr(segmenter, 'set_confidence_threshold'):
            segmenter.set_confidence_threshold(confidence_threshold)
            self.logger.debug(f"Umbral de confianza establecido a: {confidence_threshold}")
        
        # 4. Segmentar contenido (usando los bloques pre-procesados)
        self.logger.info(f"Segmentando archivo: {file_path} con {len(processed_blocks)} bloques pre-procesados.")
        segments = segmenter.segment(processed_blocks)
        segmenter_stats = segmenter.get_stats() if hasattr(segmenter, 'get_stats') else {}
        
        # 5. TODO: Aplicar post-procesador si está configurado
        
        # 6. Exportar si se especificó ruta de salida
        # Usar processed_document_metadata para la exportación
        if output_path and segments:
            self._export_results(segments, output_path, processed_document_metadata)
        elif output_path and not segments: # También exportar si no hay segmentos pero sí un output_path
            self.logger.info(f"No se encontraron segmentos para {file_path}, pero se exportarán metadatos a {output_path}")
            self._export_results([], output_path, processed_document_metadata) # Asegurar que se exporta metadata con error/warning

        # Devolver la tupla completa como espera process_file.py
        return segments, segmenter_stats, processed_document_metadata
    
    def _export_results(self, segments: List[Dict[str, Any]], output_path: str, document_metadata: Optional[Dict[str, Any]] = None):
        """
        Exporta los resultados al formato especificado.
        Si segments está vacío, exporta document_metadata con un campo segments: [].
        
        Args:
            segments: Lista de segmentos a exportar
            output_path: Ruta donde guardar los resultados
            document_metadata: Metadatos del documento
        """
        import json
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if segments: # Si hay segmentos, escribir cada uno como una línea (NDJSON)
                    for segment in segments:
                        f.write(json.dumps(segment, ensure_ascii=False) + '\n')
                else: # Si no hay segmentos, escribir los metadatos del documento y segments: []
                    output_data = document_metadata.copy() if document_metadata else {}
                    output_data['segments'] = [] # Asegurar que el campo segments exista
                    f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
            self.logger.info(f"Resultados guardados en: {output_path}")
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


if __name__ == "__main__":
    # Configuración básica de logging
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    manager = ProfileManager()
    print("Perfiles disponibles:")
    for profile in manager.list_profiles():
        print(f"- {profile['name']}: {profile['description']}") 