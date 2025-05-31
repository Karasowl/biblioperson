from typing import List, Dict, Tuple, Optional, Union, Any
from pathlib import Path
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CommonBlockPreprocessor:
    """Pre-procesador común para bloques de texto y metadatos.

    Este pre-procesador realiza operaciones agnósticas al formato de archivo
    después de que los datos han sido cargados por un Loader y antes de
    ser pasados a un Segmenter.

    Operaciones configurables:
    - Extracción de fecha desde el nombre del archivo.
    - Limpieza de texto (normalización de saltos de línea, eliminación de NULs).
    - Filtrado agresivo de fragmentos insignificantes (especialmente para PDFs).
    """

    DEFAULT_CONFIG = {
        'remove_nul_bytes': True,
        'normalize_line_endings': True,
        'extract_date_from_filename': True,
        'split_blocks_into_paragraphs': True,
        'min_chars_for_paragraph_split': 100,  # Umbral principal para dividir por \\n\\n
        'max_vertical_gap_for_merge_pt': 10,
        'min_block_area_for_split': 1000,
        'try_single_newline_split_if_block_longer_than': 500, 
        'min_chars_for_single_newline_paragraph': 75,
        # Nuevo filtrado agresivo para PDFs
        'filter_insignificant_blocks': True,
        'min_block_chars_to_keep': 15,  # Bloques menores a esto se descartan
        'max_single_word_length': 50,  # Palabras solas mayores a esto se descartan
        'discard_only_numbers': True,  # Descartar bloques que solo contienen números
        'discard_common_pdf_artifacts': True,  # Descartar artefactos comunes de PDF
        'aggressive_merge_for_pdfs': True,  # Fusión más agresiva para PDFs
        'max_vertical_gap_aggressive_pt': 20,  # Gap más grande para fusión agresiva
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el CommonBlockPreprocessor.

        Args:
            config: Configuración opcional para el pre-procesador.
                    Sobrescribe los valores de DEFAULT_CONFIG.
        """
        # PRINT VISIBLE PARA CONFIRMAR QUE SE EJECUTA NUESTRO CÓDIGO
        print("🚨🚨🚨 COMMONBLOCKPREPROCESSOR MODIFICADO SE ESTÁ EJECUTANDO 🚨🚨🚨")
        print(f"🚨🚨🚨 CONFIG RECIBIDA: {config} 🚨🚨🚨")
        
        self.config = {**CommonBlockPreprocessor.DEFAULT_CONFIG, **(config if config else {})}
        
        # LOGGING DETALLADO PARA DEBUG - ver qué configuración recibe realmente
        logger.warning(f"🔧 CommonBlockPreprocessor inicializado")
        logger.warning(f"   📥 Config recibida: {config}")
        logger.warning(f"   ⚙️  Config final: {self.config}")
        logger.warning(f"   🔗 Fusión agresiva: {self.config.get('aggressive_merge_for_pdfs', 'NO DEFINIDA')}")
        logger.warning(f"   🛡️  Filtrado activo: {self.config.get('filter_insignificant_blocks', 'NO DEFINIDA')}")
        logger.warning(f"   📏 Gap máximo: {self.config.get('max_vertical_gap_aggressive_pt', 'NO DEFINIDA')}")
        
        logger.debug(f"CommonBlockPreprocessor inicializado con config: {self.config}")

    def _is_insignificant_block(self, text: str) -> bool:
        """
        Determina si un bloque de texto es insignificante y debe descartarse.
        
        Args:
            text: Texto del bloque ya limpiado
            
        Returns:
            True si el bloque debe descartarse, False en caso contrario
        """
        if not self.config.get('filter_insignificant_blocks', True):
            return False
            
        # Filtro por longitud mínima
        min_chars = self.config.get('min_block_chars_to_keep', 15)
        if len(text) < min_chars:
            return True
            
        # Filtro de solo números (números de página, etc.)
        if self.config.get('discard_only_numbers', True):
            if text.isdigit() or re.match(r'^\d+[.\-]*\d*$', text):
                return True
                
        # Filtro de palabras solas muy largas (probablemente errores de OCR)
        words = text.split()
        if len(words) == 1:
            max_single_word = self.config.get('max_single_word_length', 50)
            if len(words[0]) > max_single_word:
                return True
                
        # Filtro de artefactos comunes de PDF
        if self.config.get('discard_common_pdf_artifacts', True):
            # Preposiciones y artículos sueltos
            if text.lower() in ['del', 'de', 'la', 'el', 'los', 'las', 'un', 'una', 'y', 'o', 'a', 'en', 'con', 'por', 'para', 'que']:
                return True
                
            # Letras solas o combinaciones muy cortas
            if len(text) <= 3 and not text.isdigit():
                return True
                
            # Patrones típicos de headers/footers
            if re.match(r'^[IVXivx]+$', text):  # Numeración romana sola
                return True
                
            if re.match(r'^[a-zA-Z]$', text):  # Letras solas
                return True
                
            # Fechas aisladas que probablemente son headers/footers
            if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', text):
                return True
                
        return False

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        # Implementación placeholder, ya que la lógica principal se movió
        # pero la opción de config existe.
        if self.config.get('extract_date_from_filename', True):
            # Ejemplo: Intenta encontrar YYYY-MM-DD o YYYYMMDD
            match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{8})', filename)
            if match:
                date_str = match.group(1)
                try:
                    # Validar y normalizar si es necesario
                    if '-' in date_str:
                        datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        datetime.strptime(date_str, '%Y%m%d')
                        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                    return date_str
                except ValueError:
                    logger.warning(f"Formato de fecha inválido '{date_str}' encontrado en el nombre de archivo '{filename}'.")
        return None

    def _clean_block_text(self, text: str) -> str:
        """Limpia el texto de un bloque de forma conservadora según la configuración."""
        if text is None:
            return None
        
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        if self.config.get('remove_nul_bytes', True):
            text = text.replace('\x00', '')
        
        return text.strip() # Strip al final para quitar espacios/saltos al inicio/fin

    def _split_text_into_paragraphs(self, text: str, base_order: float, original_coordinates: Optional[Dict] = None) -> List[Tuple[str, float, Optional[Dict]]]:
        """
        SOLUCIÓN MEJORADA: Aprovechar párrafos reconstruidos por PDFLoader inteligente
        """
        print(f"💡 APLICANDO SOLUCIÓN PDFLoader INTELIGENTE")
        logger.warning(f"💡 SOLUCIÓN V7.0: Procesando texto de {len(text)} chars con heurísticas PDFLoader")
        
        # DIAGNÓSTICO ESPECÍFICO para texto que contiene "atractivo"
        if "atractivo" in text.lower():
            print(f"🚨 DIAGNÓSTICO TEXTO ATRACTIVO EN COMMONBLOCKPREPROCESSOR:")
            print(f"   Texto completo ({len(text)} chars): '{text}'")
            logger.warning(f"🚨 TEXTO ATRACTIVO DETECTADO: '{text[:200]}...'")
            
            # Verificar si ya tiene el formato correcto
            if "atractivo de esta idea" in text.lower():
                print("✅ TEXTO YA UNIDO CORRECTAMENTE!")
                logger.warning("✅ TEXTO ATRACTIVO YA UNIDO CORRECTAMENTE")
            else:
                print("❌ TEXTO TODAVÍA SEPARADO - PROBLEMA PERSISTE")
                logger.warning("❌ TEXTO ATRACTIVO SEPARADO - PROBLEMA PERSISTE")
        
        paragraphs_data = []
        
        # PRIMERA PRIORIDAD: Párrafos ya reconstruidos por PDFLoader (separados por \n\n)
        raw_paragraphs = re.split(r'\n\n+', text)
        
        # Si no hay párrafos múltiples, intentar con espacios múltiples como fallback
        if len(raw_paragraphs) <= 1:
            raw_paragraphs = re.split(r'[\s]{2,}', text)
        
        # Si aún no hay división y el texto es largo, aplicar heurísticas inteligentes
        if len(raw_paragraphs) <= 1 and len(text) > 400:
            print("💡 Aplicando heurísticas inteligentes para texto largo")
            raw_paragraphs = self._smart_split_long_text(text)
        
        sub_order = 0
        for paragraph_text in raw_paragraphs:
            cleaned_paragraph = paragraph_text.strip()
            
            # Solo mantener párrafos con contenido significativo
            if len(cleaned_paragraph) >= 15:  # Mínimo 15 caracteres
                new_coords = None
                if original_coordinates:
                    new_coords = original_coordinates.copy()
                
                final_order = base_order + (sub_order * 0.001)
                paragraphs_data.append((cleaned_paragraph, final_order, new_coords))
                sub_order += 1
        
        # Si no se dividió nada, devolver el texto original
        if not paragraphs_data and len(text.strip()) >= 15:
            paragraphs_data.append((text.strip(), base_order, original_coordinates))
        
        print(f"💡 Dividido en {len(paragraphs_data)} párrafos (PDFLoader inteligente)")
        logger.warning(f"💡 RESULTADO V5.0: {len(paragraphs_data)} párrafos generados con PDFLoader inteligente")
        return paragraphs_data
    
    def _smart_split_long_text(self, text: str) -> List[str]:
        """
        División inteligente para textos largos usando heurísticas semánticas.
        """
        # Dividir por saltos de línea y reconstruir párrafos inteligentemente
        lines = text.split('\n')
        if len(lines) <= 1:
            return [text]
            
        paragraphs = []
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if not current_paragraph:
                current_paragraph = [line]
                continue
                
            # Heurísticas para detectar nuevo párrafo
            prev_line = current_paragraph[-1]
            should_break = False
            
            # 1. Si la línea anterior termina con punto y la actual empieza con mayúscula
            if (prev_line.endswith('.') or prev_line.endswith('!') or prev_line.endswith('?')) and \
               line and line[0].isupper():
                should_break = True
                
            # 2. Si la línea actual empieza con numeración o guión
            if re.match(r'^\d+[\.\)]\s+|^[-•]\s+|^[A-Z][a-z]*:', line):
                should_break = True
            
            if should_break:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = [line]
            else:
                current_paragraph.append(line)
        
        # Agregar último párrafo
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
            
        return paragraphs if len(paragraphs) > 1 else [text]

    def _merge_contiguous_fitz_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """
        Fusiona bloques contiguos aplicando heurísticas de separación vertical
        y detección de párrafos divididos artificialmente.
        """
        if not blocks:
            return blocks

        merged_blocks = []
        current_block = None

        for i, block in enumerate(blocks):
            if current_block is None:
                current_block = block.copy()
                continue

            # Fusión especial para oraciones divididas por saltos de página
            if self._should_merge_split_sentences(current_block, block):
                self.logger.info(f"🔗 FUSIONANDO ORACIÓN DIVIDIDA: '{current_block.get('text', '')[-30:]}' + '{block.get('text', '')[:30]}'")
                current_block['text'] = self._get_merge_separator(current_block['text'], block['text'])
                current_block['order'] = min(current_block.get('order', 0), block.get('order', 0))
                continue

            # Lógica de fusión normal existente
            curr_text = current_block.get('text', '').strip()
            next_text = block.get('text', '').strip()
            
            if not curr_text or not next_text:
                merged_blocks.append(current_block)
                current_block = block.copy()
                continue

            curr_page = current_block.get('page', 0)
            next_page = block.get('page', 0)
            
            vertical_gap = abs(block.get('bbox', [0, 0, 0, 0])[1] - current_block.get('bbox', [0, 0, 0, 0])[3])
            max_gap = self.config.get('max_vertical_gap_for_merge', 20)
            
            if self._should_merge_blocks(curr_text, next_text, curr_page, next_page, vertical_gap, max_gap):
                current_block['text'] = self._get_merge_separator(curr_text, next_text)
                current_block['order'] = min(current_block.get('order', 0), block.get('order', 0))
            else:
                merged_blocks.append(current_block)
                current_block = block.copy()

        if current_block:
            merged_blocks.append(current_block)

        return merged_blocks

    def _should_merge_split_sentences(self, block1: Dict, block2: Dict) -> bool:
        """
        Detecta si dos bloques representan una oración dividida artificialmente.
        
        Casos típicos:
        - Bloque 1 termina sin puntuación final
        - Bloque 2 empieza con minúscula o continuación lógica
        - Son de páginas consecutivas o la misma página
        """
        text1 = block1.get('text', '').strip()
        text2 = block2.get('text', '').strip()
        
        if not text1 or not text2:
            return False
        
        page1 = block1.get('page', 0)
        page2 = block2.get('page', 0)
        
        # Solo fusionar si están en la misma página o páginas consecutivas
        if abs(page2 - page1) > 1:
            return False
        
        # Detectar patrones de división artificial
        last_word = text1.split()[-1] if text1.split() else ""
        first_word = text2.split()[0] if text2.split() else ""
        
        # Caso 1: El primer bloque termina sin puntuación fuerte
        ends_without_punctuation = not text1.endswith(('.', '!', '?', ':', ';'))
        
        # Caso 2: El segundo bloque empieza con minúscula (continuación)
        starts_lowercase = text2[0].islower() if text2 else False
        
        # Caso 3: Patrones específicos de división
        specific_patterns = [
            # "atractivo" + "de esta idea"
            (last_word.lower() in ['atractivo', 'hermoso', 'interesante', 'importante'] and 
             first_word.lower() in ['de', 'del', 'que', 'para']),
            # Palabras que claramente continúan
            (last_word.lower() in ['muy', 'más', 'tan', 'poco'] and 
             first_word.lower() not in ['pero', 'sin', 'embargo', 'aunque']),
            # Preposiciones al final que requieren continuación
            (last_word.lower() in ['para', 'por', 'en', 'con', 'sin', 'de', 'del', 'al'] and 
             not starts_lowercase == False)  # No empezar con mayúscula
        ]
        
        should_merge = (
            ends_without_punctuation and 
            (starts_lowercase or any(specific_patterns))
        )
        
        if should_merge:
            self.logger.info(f"🔍 DETECTADA DIVISIÓN ARTIFICIAL:")
            self.logger.info(f"   Bloque 1: '{text1[-50:]}'")
            self.logger.info(f"   Bloque 2: '{text2[:50]}'")
            self.logger.info(f"   Sin puntuación: {ends_without_punctuation}, Minúscula: {starts_lowercase}")
        
        return should_merge

    def _should_merge_blocks(self, prev_text: str, curr_text: str, prev_page: int, curr_page: int, 
                           vertical_gap: float, max_gap: float) -> bool:
        """
        FUSIÓN ULTRA CONSERVADORA - SOLO PALABRAS CLARAMENTE CORTADAS
        """
        print(f"🔗 FUSIÓN ULTRA CONSERVADORA: gap={vertical_gap}pt")
        
        # No fusionar entre páginas diferentes
        if prev_page != curr_page:
            print("❌ Páginas diferentes")
            return False
            
        # SÚPER CONSERVADOR: Solo fusionar gaps MUY pequeños (palabras realmente cortadas)
        # Gap menor a 3pt = palabra cortada obvia, fusionar
        # Todo lo demás = NO fusionar para preservar estructura
        if vertical_gap < 3.0:
            print("✅ FUSIONAR: gap minúsculo (palabra cortada)")
            return True
            
        print("❌ NO FUSIONAR: preservar separación")
        return False
    
    def _is_obviously_incomplete_sentence(self, prev_text: str, curr_text: str) -> bool:
        """
        Determina si es obviamente una oración incompleta que necesita fusión.
        Más conservador que la lógica general.
        """
        prev_stripped = prev_text.strip().lower()
        curr_stripped = curr_text.strip().lower()
        
        # Casos muy obvios de palabras cortadas
        obvious_incomplete = ['un ', 'una ', 'el ', 'la ', 'los ', 'las ', 'de ', 'del ', 'en ', 'por ', 'para ']
        
        # Solo fusionar si el anterior termina con artículo/preposición Y el actual empieza con minúscula
        if any(prev_stripped.endswith(ending.strip()) for ending in obvious_incomplete):
            if curr_stripped and curr_stripped[0].islower():
                return True
                
        # Caso específico: palabras cortadas con guión
        if prev_stripped.endswith('-') and curr_stripped and curr_stripped[0].islower():
            return True
            
        return False

    def _get_merge_separator(self, prev_text: str, curr_text: str) -> str:
        """
        Determina el separador apropiado para fusionar dos bloques de texto.
        
        Args:
            prev_text: Texto del bloque anterior
            curr_text: Texto del bloque actual
            
        Returns:
            Separador apropiado (' ', '', etc.)
        """
        prev_stripped = prev_text.strip()
        curr_stripped = curr_text.strip()
        
        # Sin separador si el anterior termina con guión (palabra cortada)
        if prev_stripped.endswith('-') and curr_stripped and curr_stripped[0].islower():
            return ''
            
        # Sin separador si el actual empieza con puntuación
        if curr_stripped.startswith((',', '.', ';', ':', '!', '?', ')', ']', '»', '"')):
            return ''
            
        # Espacio en todos los demás casos
        return ' '

    def process(self, blocks: List[Dict], document_metadata: Dict[str, Any]) -> List[Dict]:
        """
        Procesa una lista de bloques aplicando las transformaciones configuradas.
        
        Args:
            blocks: Lista de bloques de texto con metadatos.
            document_metadata: Metadatos del documento.
            
        Returns:
            Lista de bloques procesados.
        """
        # ===== IDENTIFICADOR ÚNICO DE VERSIÓN =====
        logger.warning("🚨🚨🚨 COMMONBLOCKPREPROCESSOR V9.0 - CORREGIDO HEADINGSEGMENTER 🚨🚨🚨")
        logger.warning("🔄 VERSIÓN ACTIVA: 31-MAY-2025 02:00 - HEADINGSEGMENTER SIN FILTROS EN MODO PÁRRAFOS")
        print("🚨🚨🚨 COMMONBLOCKPREPROCESSOR V9.0 - CORREGIDO HEADINGSEGMENTER 🚨🚨🚨")
        print("🔄 VERSIÓN ACTIVA: 31-MAY-2025 02:00 - HEADINGSEGMENTER SIN FILTROS EN MODO PÁRRAFOS")
        
        if not blocks:
            logger.info("No hay bloques para procesar.")
            return []
        
        logger.info(f"Iniciando procesamiento de {len(blocks)} bloques.")
        
        processed_document_metadata = document_metadata.copy()

        # 1. Fusionar bloques si son nativos de Fitz y la configuración lo permite
        should_merge = (
            processed_document_metadata.get('blocks_are_fitz_native', False) and \
            self.config.get('split_blocks_into_paragraphs', True)
        )
        if should_merge:
            logger.info(f"Detectados bloques nativos de Fitz ({len(blocks)}), intentando fusionar bloques contiguos.")
            blocks = self._merge_contiguous_fitz_blocks(blocks)
            logger.info(f"Número de bloques después de la fusión inicial de Fitz: {len(blocks)}")

        final_processed_blocks: List[Dict] = []
        filtered_count = 0
        
        for i, block_data in enumerate(blocks):
            current_block_metadata = block_data.copy()
            
            block_text_content = current_block_metadata.pop('text', None) or \
                                 current_block_metadata.pop('content', None)
            
            original_block_coordinates = current_block_metadata.get('coordinates')

            if block_text_content is not None:
                cleaned_text = self._clean_block_text(block_text_content)

                if not cleaned_text:
                    continue

                # Aplicar filtrado adicional aquí también (doble seguridad)
                if self._is_insignificant_block(cleaned_text):
                    filtered_count += 1
                    continue

                # Configuración para división de párrafos
                should_split_paragraphs_config = self.config.get('split_blocks_into_paragraphs', True)
                min_area_config = self.config.get('min_block_area_for_split', 0)
                
                block_has_sufficient_area_eval = True
                if original_block_coordinates:
                    width = original_block_coordinates['x1'] - original_block_coordinates['x0']
                    height = original_block_coordinates['y1'] - original_block_coordinates['y0']
                    calculated_area = width * height
                    if calculated_area < min_area_config:
                        block_has_sufficient_area_eval = False

                if should_split_paragraphs_config and block_has_sufficient_area_eval:
                    paragraphs_with_order = self._split_text_into_paragraphs(
                        cleaned_text,
                        float(current_block_metadata.get('order_in_document', i)),
                        original_block_coordinates
                    )
                    for sub_text, sub_order, sub_coords in paragraphs_with_order:
                        new_sub_block = current_block_metadata.copy()
                        new_sub_block['text'] = sub_text
                        new_sub_block['order_in_document'] = sub_order
                        if sub_coords:
                            new_sub_block['coordinates'] = sub_coords
                        new_sub_block['type'] = current_block_metadata.get('type', 'text_block')
                        final_processed_blocks.append(new_sub_block)
                else:
                    # No se divide, se añade el bloque limpiado tal cual
                    processed_block_metadata = current_block_metadata.copy()
                    processed_block_metadata['text'] = cleaned_text
                    processed_block_metadata['type'] = processed_block_metadata.get('type', 'text_block')
                    final_processed_blocks.append(processed_block_metadata)
            
            elif current_block_metadata:
                current_block_metadata['type'] = current_block_metadata.get('type', 'unknown_empty_block')
                final_processed_blocks.append(current_block_metadata)
        
        if filtered_count > 0:
            logger.info(f"CommonBlockPreprocessor: Filtrados {filtered_count} bloques insignificantes.")
        
        logger.info(f"CommonBlockPreprocessor: Finalizado procesamiento, {len(final_processed_blocks)} bloques resultantes.")
        return final_processed_blocks, processed_document_metadata

if __name__ == '__main__':
    # Ejemplo de uso básico
    logging.basicConfig(level=logging.DEBUG)
    
    print("--- Ejemplo 1: Configuración por defecto ---")
    preprocessor_default = CommonBlockPreprocessor()
    sample_metadata_1 = {
        'source_file_path': '/path/to/my_document_2023-10-25.txt',
        'author': 'Test Author'
    }
    sample_blocks_1 = [
        {'text': 'Bloque 1.\r\nSalto Windows. \x00 NUL char.\n\nEste es otro párrafo en el mismo bloque.', 'order_in_document': 0, 'source_page_number': 1},
        {'text': 'Bloque 2\rSalto Mac.', 'order_in_document': 1, 'source_page_number': 2}
    ]
    processed_blocks_1, processed_metadata_1 = preprocessor_default.process(sample_blocks_1, sample_metadata_1)
    print("Metadata 1:", processed_metadata_1)
    print("Blocks 1:")
    for b in processed_blocks_1: print(b)

    print("\n--- Ejemplo 2: Sin extracción de fecha del nombre de archivo y sin división de párrafos ---")
    config_no_split = {
        'extract_filename_date': False, 
        'normalize_line_endings': True, 
        'remove_nul_chars': True,
        'split_blocks_into_paragraphs': False
    }
    preprocessor_no_split = CommonBlockPreprocessor(config=config_no_split)
    sample_metadata_2 = {
        'source_file_path': '/path/to/another_doc_2024_01_15.md',
        'detected_date': '2024-01-01' # Fecha preexistente de propiedades del doc
    }
    sample_blocks_2 = [
        {'text': 'Párrafo único.\nAunque tenga saltos.\n\nY una línea vacía en medio.', 'order_in_document': 'A'}
    ]
    processed_blocks_2, processed_metadata_2 = preprocessor_no_split.process(sample_blocks_2, sample_metadata_2)
    print("Metadata 2:", processed_metadata_2)
    print("Blocks 2:")
    for b in processed_blocks_2: print(b)

    print("\n--- Ejemplo 3: Texto corto, no se divide ---")
    preprocessor_short_text = CommonBlockPreprocessor(config={'min_chars_for_paragraph_split': 100})
    sample_blocks_short = [
        {'text': 'Texto corto.\nNo se divide.', 'order_in_document': 0}
    ]
    processed_blocks_short, processed_metadata_short = preprocessor_short_text.process(sample_blocks_short, {})
    print("Blocks Short:")
    for b in processed_blocks_short: print(b)

    print("\n--- Ejemplo 4: Bloque sin texto ---")
    sample_blocks_no_text = [
        {'order_in_document': 0, 'source_page_number': 1, 'type': 'image_placeholder'}
    ]
    processed_blocks_no_text, processed_metadata_no_text = preprocessor_default.process(sample_blocks_no_text, {})
    print("Blocks No Text:")
    for b in processed_blocks_no_text: print(b) 