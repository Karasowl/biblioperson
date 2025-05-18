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
        'min_chars_for_single_newline_paragraph': 75 
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el CommonBlockPreprocessor.

        Args:
            config: Configuración opcional para el pre-procesador.
                    Sobrescribe los valores de DEFAULT_CONFIG.
        """
        self.config = {**CommonBlockPreprocessor.DEFAULT_CONFIG, **(config if config else {})}
        logger.debug(f"CommonBlockPreprocessor inicializado con config: {self.config}")

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
        paragraphs_data = []
        min_chars_for_split = self.config.get('min_chars_for_paragraph_split', 100)
        try_single_newline_split_threshold = self.config.get('try_single_newline_split_if_block_longer_than', 500)
        min_chars_for_single_newline_para = self.config.get('min_chars_for_single_newline_paragraph', 75)

        logger.debug(f"[_split_text_into_paragraphs] Texto original (primeros 300 chars): '{text[:300]}'")
        logger.debug(f"[_split_text_into_paragraphs] Longitud total del texto original: {len(text)}")
        logger.debug(f"[_split_text_into_paragraphs] min_chars_for_split (config): {min_chars_for_split}")
        logger.debug(f"[_split_text_into_paragraphs] try_single_newline_split_threshold (config): {try_single_newline_split_threshold}")
        logger.debug(f"[_split_text_into_paragraphs] min_chars_for_single_newline_para (config): {min_chars_for_single_newline_para}")

        # Intento primario: dividir por dos o más saltos de línea
        # Usar una expresión regular para capturar dos o más saltos de línea como delimitador
        raw_paragraphs = re.split(r'\n{2,}', text)
        logger.debug(f"[_split_text_into_paragraphs] Intento con r'\n{{2,}}': {len(raw_paragraphs)} párrafos crudos.")
        for i, p_text in enumerate(raw_paragraphs):
            # Corregido: Escapar la barra invertida en \\n dentro del replace
            log_text_preview = p_text[:100].replace('\n', '<NL>') 
            logger.debug(f"  Raw para (doble \\\\n) #{i}: '{log_text_preview}{'...' if len(p_text) > 100 else ''}' (len: {len(p_text)})")

        current_paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]
        logger.debug(f"[_split_text_into_paragraphs] Párrafos después de strip y filtro de vacíos (doble \\\\n): {len(current_paragraphs)}")

        # Si la división por \\n\\n no funcionó bien (pocos párrafos o uno muy largo)
        # Y el texto original es suficientemente largo, intentar dividir por un solo \\n
        # Condición para intentar división por \\n simple:
        # 1. El bloque de texto original es más largo que 'try_single_newline_split_if_block_longer_than'
        # 2. Y ( (la división por \\n\\n resultó en 1 solo párrafo Y ese párrafo es más largo que min_chars_for_split)
        #      O (la división por \\n\\n resultó en más de 1 párrafo PERO la mayoría son muy cortos) )
        # Esta segunda parte de la condición es difícil de cuantificar con precisión sin más heurísticas,
        # por ahora, simplificaremos: si el texto es largo y la división por \\n\\n resultó en <=1 párrafo significativo.

        should_try_single_newline_split = False
        if len(text) > try_single_newline_split_threshold:
            if len(current_paragraphs) == 1 and len(current_paragraphs[0]) > min_chars_for_split:
                should_try_single_newline_split = True
                logger.debug(f"[_split_text_into_paragraphs] Condición para split por \\\\n simple CUMPLIDA (1 párrafo largo después de \\\\n\\\\n).")
            elif not current_paragraphs: # Si \\n\\n no produjo nada (raro si hay texto)
                should_try_single_newline_split = True
                logger.debug(f"[_split_text_into_paragraphs] Condición para split por \\\\n simple CUMPLIDA (ningún párrafo después de \\\\n\\\\n).")
        
        if should_try_single_newline_split:
            logger.info(f"[_split_text_into_paragraphs] Texto largo y r'\n\n' no dividió bien. Intentando con un solo r'\n'.")
            # Usar una expresión regular para capturar un solo salto de línea como delimitador
            raw_paragraphs_single_nl = re.split(r'\n', text)
            logger.debug(f"[_split_text_into_paragraphs] Intento con r'\n': {len(raw_paragraphs_single_nl)} párrafos crudos.")
            for i, p_text in enumerate(raw_paragraphs_single_nl):
                # Corregido: Escapar la barra invertida en \\n dentro del replace
                log_text_preview_single = p_text[:100].replace('\n', '<NL>')
                logger.debug(f"  Raw para (simple \\\\n) #{i}: '{log_text_preview_single}{'...' if len(p_text) > 100 else ''}' (len: {len(p_text)})")

            current_paragraphs = [p.strip() for p in raw_paragraphs_single_nl if p.strip()]
            min_chars_for_split = min_chars_for_single_newline_para # Usar el umbral específico para \\n
            logger.debug(f"[_split_text_into_paragraphs] Párrafos después de strip y filtro de vacíos (simple \\\\n): {len(current_paragraphs)}. Usando min_chars_for_split: {min_chars_for_split}")


        if not current_paragraphs or (len(current_paragraphs) == 1 and len(current_paragraphs[0]) < min_chars_for_split):
            # Si no hay párrafos o solo uno que es demasiado corto, devolver el texto original como un solo bloque
            # (siempre que el texto original en sí mismo supere el umbral mínimo, de lo contrario se descarta)
            if len(text.strip()) >= min_chars_for_split: # Comparar con el umbral activo
                logger.debug(f"[_split_text_into_paragraphs] Devolviendo texto original como único párrafo (longitud: {len(text.strip())} >= umbral: {min_chars_for_split}).")
                paragraphs_data.append((text.strip(), base_order, original_coordinates))
            else:
                logger.debug(f"[_split_text_into_paragraphs] Texto original no cumple umbral ({len(text.strip())} < {min_chars_for_split}), no se devuelve nada.")
        else:
            sub_order = 0
            for i, paragraph_text in enumerate(current_paragraphs):
                # logger.debug(f"  Procesando párrafo candidato #{i}: '{paragraph_text[:100].replace('\\n','<NL>')}{'...' if len(paragraph_text) > 100 else ''}' (len: {len(paragraph_text)})")
                if len(paragraph_text) >= min_chars_for_split:
                    # Crear nuevas coordenadas si las originales existen (simplificado, podría mejorarse)
                    new_coords = None
                    if original_coordinates:
                        # Esta es una simplificación. Una mejor aproximación requeriría
                        # recalcular las coordenadas del párrafo dentro del bloque original.
                        # Por ahora, simplemente propagamos las coordenadas del bloque original.
                        new_coords = original_coordinates.copy() 
                        # Podríamos añadir un offset o un identificador de sub-bloque aquí
                        # new_coords['paragraph_index'] = sub_order 
                    
                    final_order = base_order + (sub_order * 0.001) # Asegurar orden incremental
                    paragraphs_data.append((paragraph_text, final_order, new_coords))
                    # Corregido: Crear variable para el texto del log
                    log_paragraph_preview = paragraph_text[:80].replace('\n','<NL>')
                    logger.debug(f"    PÁRRAFO AÑADIDO #{sub_order} (orig idx {i}): orden {final_order:.3f}, len {len(paragraph_text)}, texto: '{log_paragraph_preview}{'...' if len(paragraph_text) > 80 else ''}'")
                    sub_order += 1
                else:
                    # Corregido: Escapar la barra invertida en \\n dentro del replace
                    log_text_preview_discarded = paragraph_text[:80].replace('\n','<NL>')
                    logger.debug(f"    Párrafo DESCARTADO (orig idx {i}) por longitud: {len(paragraph_text)} < {min_chars_for_split}. Texto: '{log_text_preview_discarded}{'...' if len(paragraph_text) > 80 else ''}'")
        
        logger.debug(f"[_split_text_into_paragraphs] Finalizado. Total párrafos generados: {len(paragraphs_data)}")
        return paragraphs_data

    def _merge_contiguous_fitz_blocks(self, blocks: List[Dict]) -> List[Dict]:
        if not blocks:
            return []

        merged_blocks: List[Dict] = []
        current_merged_block: Optional[Dict] = None
        max_gap = self.config.get('max_vertical_gap_for_merge_pt', CommonBlockPreprocessor.DEFAULT_CONFIG['max_vertical_gap_for_merge_pt'])

        for block_idx, block in enumerate(blocks):
            block_text_content = block.get('text') or block.get('content')
            block_type = block.get('type', 'unknown_block')
            
            if block_type == 'text_block' and block_text_content and 'coordinates' in block and 'source_page_number' in block:
                cleaned_current_text = self._clean_block_text(block_text_content) # Limpiar texto antes de decidir
                if not cleaned_current_text: # Saltar si el texto limpiado está vacío
                    if current_merged_block is not None: # Guardar el anterior si existe
                        merged_blocks.append(current_merged_block)
                        current_merged_block = None
                    # No añadir este bloque vacío, pero sí mantener su lugar si es un bloque no textual importante
                    # OJO: esta lógica puede necesitar refinar si los bloques vacíos deben mantenerse
                    continue


                if current_merged_block is None:
                    current_merged_block = block.copy()
                    current_merged_block['text'] = cleaned_current_text
                else:
                    prev_coords = current_merged_block['coordinates']
                    curr_coords = block['coordinates']
                    
                    vertical_gap = curr_coords['y0'] - prev_coords['y1']
                    
                    # logger.debug(f"Merging? Block {block_idx}: prev_y1={prev_coords['y1']:.2f}, curr_y0={curr_coords['y0']:.2f}, gap={vertical_gap:.2f}, max_gap={max_gap}, same_page={current_merged_block.get('source_page_number') == block.get('source_page_number')}")

                    if current_merged_block.get('source_page_number') == block.get('source_page_number') and vertical_gap <= max_gap and vertical_gap >= -max_gap/2: # Permitir pequeña superposición también
                        current_merged_block['text'] += f" {cleaned_current_text}" # Unir con espacio
                        current_merged_block['coordinates']['y1'] = max(prev_coords['y1'], curr_coords['y1'])
                        current_merged_block['coordinates']['x0'] = min(prev_coords['x0'], curr_coords['x0'])
                        current_merged_block['coordinates']['x1'] = max(prev_coords['x1'], curr_coords['x1'])
                        # Conservar metadatos del primer bloque del grupo
                    else:
                        merged_blocks.append(current_merged_block)
                        current_merged_block = block.copy()
                        current_merged_block['text'] = cleaned_current_text
            else: # Bloque no textual o sin info para fusionar
                if current_merged_block is not None:
                    merged_blocks.append(current_merged_block)
                    current_merged_block = None
                merged_blocks.append(block) 

        if current_merged_block is not None:
            merged_blocks.append(current_merged_block)

        # logger.debug(f"Bloques después de _merge_contiguous_fitz_blocks: {len(merged_blocks)}")
        # if merged_blocks and len(merged_blocks) < 15:
        #     for i, mb in enumerate(merged_blocks[:15]):
        #         logger.debug(f"  Merged Block {i}: page={mb.get('source_page_number')}, order={mb.get('order_in_document')} text='{mb.get('text', '')[:100]}...'")
        return merged_blocks

    def process(self, blocks: List[Dict], document_metadata: Dict[str, Any]) -> List[Dict]:
        logger.debug(f"CommonBlockPreprocessor: Iniciando procesamiento de {len(blocks)} bloques para {document_metadata.get('source_file_path', 'archivo desconocido')}.")
        
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
        for i, block_data in enumerate(blocks):
            current_block_metadata = block_data.copy()
            
            block_text_content = current_block_metadata.pop('text', None) or \
                                 current_block_metadata.pop('content', None)
            
            original_block_coordinates = current_block_metadata.get('coordinates')

            if block_text_content is not None:
                cleaned_text = self._clean_block_text(block_text_content)

                if not cleaned_text:
                    continue

                # DEBUG logs que añadimos para cleaned_text (los mantenemos por ahora)
                if i < 5:
                    logger.debug(f"POST-MERGE Bloque {i} - cleaned_text (primeros 200 chars): '{cleaned_text[:200] if cleaned_text else ''}'")
                    logger.debug(f"POST-MERGE Bloque {i} - len(cleaned_text): {len(cleaned_text) if cleaned_text else 0}")

                # Aquí está la condición clave:
                should_split_paragraphs_config = self.config.get('split_blocks_into_paragraphs', True)
                min_area_config = self.config.get('min_block_area_for_split', 0)
                
                block_has_sufficient_area_eval = True # Asumimos True por ahora si no hay 'coordinates'
                calculated_area = -1 # Valor por defecto si no hay coords o no se calcula

                if original_block_coordinates:
                    width = original_block_coordinates['x1'] - original_block_coordinates['x0']
                    height = original_block_coordinates['y1'] - original_block_coordinates['y0']
                    calculated_area = width * height
                    if calculated_area < min_area_config:
                        block_has_sufficient_area_eval = False
                
                # LOGS DE DEPURACIÓN PARA LA CONDICIÓN DE DIVISIÓN
                logger.debug(f"PRE-SPLIT Bloque {i} (después de fusión y limpieza):")
                logger.debug(f"  should_split_paragraphs_config: {should_split_paragraphs_config}")
                logger.debug(f"  original_block_coordinates: {original_block_coordinates is not None}")
                if original_block_coordinates:
                    logger.debug(f"    coords: x0={original_block_coordinates['x0']:.2f}, y0={original_block_coordinates['y0']:.2f}, x1={original_block_coordinates['x1']:.2f}, y1={original_block_coordinates['y1']:.2f}")
                    logger.debug(f"    calculated_area: {calculated_area:.2f}")
                    logger.debug(f"    min_area_config: {min_area_config}")
                logger.debug(f"  block_has_sufficient_area_eval: {block_has_sufficient_area_eval}")
                logger.debug(f"  Texto (primeros 50 chars): '{cleaned_text[:50] if cleaned_text else ''}'")
                logger.debug(f"  Longitud texto: {len(cleaned_text) if cleaned_text else 0}")

                if should_split_paragraphs_config and block_has_sufficient_area_eval:
                    logger.debug(f"  ENTRANDO a _split_text_into_paragraphs para bloque {i}.")
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
                    logger.debug(f"  SALTANDO _split_text_into_paragraphs para bloque {i}. Razón: should_split_config={should_split_paragraphs_config}, has_sufficient_area={block_has_sufficient_area_eval}")
                    # No se divide, se añade el bloque limpiado tal cual
                    processed_block_metadata = current_block_metadata.copy()
                    processed_block_metadata['text'] = cleaned_text
                    processed_block_metadata['type'] = processed_block_metadata.get('type', 'text_block')
                    final_processed_blocks.append(processed_block_metadata)
            
            elif current_block_metadata:
                current_block_metadata['type'] = current_block_metadata.get('type', 'unknown_empty_block')
                final_processed_blocks.append(current_block_metadata)
        
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
    processed_blocks_short, _ = preprocessor_short_text.process(sample_blocks_short, {})
    print("Blocks Short:")
    for b in processed_blocks_short: print(b)

    print("\n--- Ejemplo 4: Bloque sin texto ---")
    sample_blocks_no_text = [
        {'order_in_document': 0, 'source_page_number': 1, 'type': 'image_placeholder'}
    ]
    processed_blocks_no_text, _ = preprocessor_default.process(sample_blocks_no_text, {})
    print("Blocks No Text:")
    for b in processed_blocks_no_text: print(b) 