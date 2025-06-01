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
        # NUEVA FUNCIONALIDAD: Limpieza automática de corrupción Unicode
        'clean_unicode_corruption': True,  # Limpiar caracteres Unicode corruptos automáticamente
        # NUEVA FUNCIONALIDAD: Detección de elementos estructurales repetitivos
        'filter_structural_elements': True,  # Filtrar headers/footers repetitivos
        'structural_frequency_threshold': 0.9,  # 90% de páginas = elemento estructural
        'min_pages_for_structural_detection': 5,  # Mínimo de páginas para activar detección
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
        
        # NUEVA FUNCIONALIDAD: Limpieza de corrupción Unicode
        if self.config.get('clean_unicode_corruption', True):
            text = self._clean_unicode_corruption(text)
        
        return text.strip() # Strip al final para quitar espacios/saltos al inicio/fin

    def _clean_unicode_corruption(self, text: str) -> str:
        """
        Limpia texto corrupto con caracteres Unicode de escape y caracteres de control.
        
        Esta función elimina automáticamente texto corrupto común en PDFs:
        - Secuencias backslash-u seguidas de 4 caracteres hex
        - Caracteres de control ASCII (0x00-0x1F excepto salto de línea, retorno de carro, tabulador)
        - Caracteres de control Unicode extendidos (0x7F-0x9F)
        - Detecta y remueve texto predominantemente corrupto
        """
        if not text:
            return text
        
        # 1. Remover secuencias \u seguidas de 4 caracteres hex
        text = re.sub(r'\\u[0-9a-fA-F]{4}', ' ', text)
        
        # 2. Remover caracteres de control (0x00-0x1F excepto \n=0x0A, \r=0x0D, \t=0x09)
        # y caracteres de control extendidos (0x7F-0x9F)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', ' ', text)
        
        # 3. NUEVA FUNCIONALIDAD: Detectar texto predominantemente corrupto
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        if total_chars > 0:
            # Contar caracteres reconocibles vs corruptos
            letras_validas = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', text))
            palabras_validas = len(re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]{3,}\b', text))
            
            # Si menos del 30% son letras válidas y hay menos de 2 palabras, es corrupto
            ratio_letras = letras_validas / total_chars
            if ratio_letras < 0.3 and palabras_validas < 2 and total_chars > 50:
                # Marcar como corrupto para filtrado posterior
                return ""  # Retornar vacío para que el filtro lo elimine
        
        # 4. Limpiar patrones específicos de corrupción en texto parcialmente corrupto
        # Remover secuencias de símbolos matemáticos sueltos
        text = re.sub(r'\s[+\-*/&%#$@!]{1,2}\s', ' ', text)
        
        # Remover letras sueltas entre espacios (probable corrupción)
        text = re.sub(r'\s[a-zA-Z]\s', ' ', text)
        
        # Remover números sueltos de 1-2 dígitos entre espacios
        text = re.sub(r'\s\d{1,2}\s', ' ', text)
        
        # 5. Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # 6. Limpiar líneas vacías excesivas (mantener máximo 2 saltos consecutivos)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()

    def _split_text_into_paragraphs(self, text: str, base_order: float, original_coordinates: Optional[Dict] = None) -> List[Tuple[str, float, Optional[Dict]]]:
        """
        🚨 VERSIÓN 7.0 - ALGORITMO SIMPLE PRIMERO 🚨
        
        Prioriza el algoritmo simple (doble salto de línea) como hacía antes
        cuando extraíamos 60 poemas de Mario Benedetti.
        
        Solo usa fallback si obtiene muy pocos segmentos (≤ 3).
        
        Args:
            text: Texto completo a dividir
            base_order: Orden base para los párrafos
            original_coordinates: Coordenadas del bloque original
            
        Returns:
            Lista de tuplas (texto_párrafo, orden, coordenadas)
        """
        print("🚨🚨🚨 COMMONBLOCK V7.0 - ALGORITMO SIMPLE PRIMERO 🚨🚨🚨")
        logger.warning("🚨🚨🚨 COMMONBLOCK V7.0 - ALGORITMO SIMPLE PRIMERO 🚨🚨🚨")
        
        if not text or len(text.strip()) < 10:
            return []
        
        # ======= ALGORITMO PRINCIPAL: DOBLE SALTO DE LÍNEA =======
        # Este es el que funcionaba antes para extraer los 60 poemas
        
        paragraphs = []
        
        # Dividir por doble salto de línea (como antes)
        raw_paragraphs = re.split(r'\n\s*\n', text)
        
        for i, paragraph in enumerate(raw_paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Limpiar el párrafo
            paragraph = re.sub(r'\s+', ' ', paragraph)  # Normalizar espacios
            
            if len(paragraph) >= 20:  # Filtro mínimo
                order = base_order + (i * 0.001)
                paragraphs.append((paragraph, order, original_coordinates))
        
        print(f"🎯 ALGORITMO SIMPLE: {len(paragraphs)} párrafos extraídos")
        logger.warning(f"🎯 ALGORITMO SIMPLE: {len(paragraphs)} párrafos extraídos")
        
        # ======= FALLBACK: SOLO SI HAY MUY POCOS SEGMENTOS =======
        # Solo aplicar si obtenemos ≤ 3 segmentos (como sugirió el usuario)
        
        if len(paragraphs) <= 3:
            print("⚠️ MUY POCOS SEGMENTOS: Aplicando algoritmo fallback")
            logger.warning("⚠️ MUY POCOS SEGMENTOS: Aplicando algoritmo fallback")
            
            # Fallback 1: Intentar con espacios múltiples (como sugerencia del usuario)
            fallback_paragraphs = []
            
            # Buscar patrones de 2 o más espacios consecutivos
            space_split = re.split(r'  +', text)  # 2 o más espacios
            
            for i, segment in enumerate(space_split):
                segment = segment.strip()
                if segment and len(segment) >= 20:
                    order = base_order + (i * 0.001)
                    fallback_paragraphs.append((segment, order, original_coordinates))
            
            if len(fallback_paragraphs) > len(paragraphs):
                print(f"✅ FALLBACK ESPACIOS: {len(fallback_paragraphs)} párrafos (mejor que {len(paragraphs)})")
                logger.warning(f"✅ FALLBACK ESPACIOS: {len(fallback_paragraphs)} párrafos")
                return fallback_paragraphs
            
            # Fallback 2: Solo si sigue siendo muy poco, usar single newline
            if len(paragraphs) <= 1:
                print("🔧 APLICANDO FALLBACK SINGLE NEWLINE")
                logger.warning("🔧 APLICANDO FALLBACK SINGLE NEWLINE")
                
                single_newline_split = text.split('\n')
                single_paragraphs = []
                
                for i, line in enumerate(single_newline_split):
                    line = line.strip()
                    if line and len(line) >= 30:  # Un poco más estricto
                        order = base_order + (i * 0.001)
                        single_paragraphs.append((line, order, original_coordinates))
                
                if len(single_paragraphs) > len(paragraphs):
                    print(f"✅ FALLBACK SINGLE: {len(single_paragraphs)} párrafos")
                    logger.warning(f"✅ FALLBACK SINGLE: {len(single_paragraphs)} párrafos")
                    return single_paragraphs
        
        # Retornar el resultado del algoritmo principal
        print(f"🎯 RESULTADO FINAL: {len(paragraphs)} párrafos del algoritmo simple")
        logger.warning(f"🎯 RESULTADO FINAL: {len(paragraphs)} párrafos del algoritmo simple")
        
        return paragraphs

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
        🚨 VERSIÓN 7.0 - PROCESS SIMPLIFICADO 🚨
        
        Procesa bloques de manera simple, priorizando el algoritmo que funcionaba
        antes para extraer los 60 poemas de Mario Benedetti.
        
        Args:
            blocks: Lista de bloques de texto con metadatos.
            document_metadata: Metadatos del documento.
            
        Returns:
            Lista de bloques procesados.
        """
        print("🚨🚨🚨 COMMONBLOCKPREPROCESSOR V7.0 - PROCESS SIMPLIFICADO 🚨🚨🚨")
        logger.warning("🚨🚨🚨 COMMONBLOCKPREPROCESSOR V7.0 - PROCESS SIMPLIFICADO 🚨🚨🚨")
        
        if not blocks:
            logger.info("No hay bloques para procesar.")
            return []
        
        logger.info(f"Iniciando procesamiento de {len(blocks)} bloques.")
        
        # 🆕 PASO 1: Detectar y filtrar elementos estructurales
        structural_elements = self._detect_structural_elements(blocks)
        if structural_elements:
            blocks = self._filter_structural_elements(blocks, structural_elements)
            logger.info(f"✅ Filtrado estructural aplicado: {len(structural_elements)} elementos eliminados")
        
        processed_blocks = []
        
        for i, block in enumerate(blocks):
            # Extraer texto del bloque
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # Limpieza básica
            text = self._clean_block_text(text)
            if not text:
                continue
            
            # Filtrar bloques insignificantes
            if self._is_insignificant_block(text):
                continue
            
            # ✅ RESPETA CONFIGURACIÓN: split_blocks_into_paragraphs
            if self.config.get('split_blocks_into_paragraphs', True):
                # Dividir el bloque en párrafos usando el algoritmo simple
                paragraphs = self._split_text_into_paragraphs(
                    text, 
                    i, 
                    block.get('metadata', {})
                )
                
                # Agregar cada párrafo como un bloque separado
                for paragraph_text, order, coords in paragraphs:
                    new_block = {
                        'text': paragraph_text,
                        'metadata': {
                            'order': order,
                            'source_block': i,
                            'type': block.get('metadata', {}).get('type', 'paragraph'),
                            **block.get('metadata', {})
                        }
                    }
                    processed_blocks.append(new_block)
            else:
                # 🎵 MODO VERSO: Mantener bloque original sin dividir
                print(f"🎵 MODO VERSO: Manteniendo bloque sin dividir: {repr(text[:50])}")
                logger.warning(f"🎵 MODO VERSO: Manteniendo bloque sin dividir: {repr(text[:50])}")
                
                new_block = {
                    'text': text,
                    'metadata': {
                        'order': i,
                        'source_block': i,
                        'type': block.get('metadata', {}).get('type', 'paragraph'),
                        **block.get('metadata', {})
                    }
                }
                processed_blocks.append(new_block)
        
        print(f"✅ PROCESO COMPLETADO: {len(blocks)} → {len(processed_blocks)} bloques")
        logger.warning(f"✅ PROCESO COMPLETADO: {len(blocks)} → {len(processed_blocks)} bloques")
        
        return processed_blocks, document_metadata

    def _normalize_text_for_structural_detection(self, text: str) -> str:
        """
        🔧 MEJORADO: Normaliza texto para detección de elementos estructurales.
        
        Maneja variaciones corruptas/formateadas del mismo texto usando normalización agresiva:
        - "*Antolo* *g* *ía* *Rubén Darío*" → "antologia ruben dario"
        - "A n t o l o g í a   R u b é n   D a r í o" → "antologia ruben dario"
        - "ANTOLOGÍA RUBÉN DARÍO" → "antologia ruben dario"
        
        Args:
            text: Texto original (posiblemente corrupto)
            
        Returns:
            Texto normalizado para comparación
        """
        if not text:
            return ""
        
        import unicodedata
        
        # 1. Remover asteriscos y caracteres de formato especiales
        normalized = re.sub(r'[*_`~\[\]{}()]+', '', text)
        
        # 2. Remover caracteres de puntuación, mantener solo letras, números y espacios
        normalized = re.sub(r'[^\w\s\-áéíóúüñÁÉÍÓÚÜÑ]', ' ', normalized)
        
        # 3. Normalizar acentos Unicode (NFD = descomponer, luego filtrar solo ASCII)
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # 4. Todo a minúsculas
        normalized = normalized.lower()
        
        # 5. AGRESIVO: Unir fragmentos cortos que probablemente son palabras divididas
        # "antolo g ia" → "antologia"
        words = normalized.split()
        merged_words = []
        i = 0
        
        while i < len(words):
            current_word = words[i]
            
            # Si la palabra actual es muy corta (≤ 3 chars), intentar unir con siguientes
            if len(current_word) <= 3 and i + 1 < len(words):
                # Unir hasta encontrar una palabra más larga o llegar al final
                merged = current_word
                j = i + 1
                
                while j < len(words) and len(words[j]) <= 3:
                    merged += words[j]
                    j += 1
                
                # Si la siguiente palabra también existe y es parte del título, agregarla
                if j < len(words):
                    # Palabras como "ruben", "dario" son parte del nombre
                    next_word = words[j]
                    if next_word in ['ruben', 'dario', 'rubén', 'darío'] or len(merged) + len(next_word) <= 15:
                        merged += next_word
                        j += 1
                
                merged_words.append(merged)
                i = j
            else:
                merged_words.append(current_word)
                i += 1
        
        # 6. Unir palabras y normalizar espacios finales
        normalized = ' '.join(merged_words)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def _detect_structural_elements(self, blocks: List[Dict]) -> List[str]:
        """
        🔧 MEJORADO: Detecta elementos estructurales repetitivos con normalización robusta.
        
        Ahora maneja variaciones corruptas del mismo texto:
        - "*Antolo* *g* *ía* *Rubén Darío*" se detecta como "Antología Rubén Darío"
        """
        if not self.config.get('filter_structural_elements', True):
            return []
            
        # Recopilar información de páginas y textos CON NORMALIZACIÓN
        text_to_pages = {}  # {texto_normalizado: {'pages': set(), 'original_texts': set()}}
        all_pages = set()
        
        for block in blocks:
            original_text = block.get('text', '').strip()
            if not original_text or len(original_text) < 3:
                continue
                
            # NORMALIZAR texto para detección
            normalized_text = self._normalize_text_for_structural_detection(original_text)
            if not normalized_text or len(normalized_text) < 3:
                continue
                
            # Obtener número de página del metadata
            page_num = None
            metadata = block.get('metadata', {})
            
            # Intentar múltiples formas de obtener el número de página
            if 'page_number' in metadata:
                page_num = metadata['page_number']
            elif 'source_page_number' in metadata:
                page_num = metadata['source_page_number']
            elif 'page' in metadata:
                page_num = metadata['page']
            
            if page_num is not None:
                all_pages.add(page_num)
                
                if normalized_text not in text_to_pages:
                    text_to_pages[normalized_text] = {
                        'pages': set(),
                        'original_texts': set()
                    }
                
                text_to_pages[normalized_text]['pages'].add(page_num)
                text_to_pages[normalized_text]['original_texts'].add(original_text)
        
        total_pages = len(all_pages)
        min_pages = self.config.get('min_pages_for_structural_detection', 5)
        
        # Solo analizar si hay suficientes páginas
        if total_pages < min_pages:
            logger.debug(f"📄 Solo {total_pages} páginas, omitiendo detección estructural (mínimo: {min_pages})")
            return []
        
        # Detectar elementos estructurales
        structural_elements = []
        threshold = self.config.get('structural_frequency_threshold', 0.9)
        
        logger.info(f"🔍 Analizando elementos estructurales en {total_pages} páginas (umbral: {threshold*100}%)")
        
        # MÉTODO 1: Detección por normalización (como antes)
        for normalized_text, data in text_to_pages.items():
            pages = data['pages']
            original_texts = data['original_texts']
            frequency = len(pages) / total_pages
            
            # Si aparece en más del umbral de páginas, es estructural
            if frequency >= threshold:
                # Agregar TODAS las variaciones originales del texto
                for original_text in original_texts:
                    structural_elements.append(original_text)
                
                # Log con ejemplo de variaciones detectadas
                examples = list(original_texts)[:3]  # Mostrar máximo 3 ejemplos
                logger.warning(f"🚫 Elemento estructural detectado ({frequency*100:.1f}%): '{normalized_text}'")
                logger.warning(f"   📝 Variaciones encontradas: {examples}")
        
        # MÉTODO 2: Detección por patrones específicos conocidos (NUEVO)
        # Buscar patrones como "*Antolo*" que claramente son corrupción de "Antología"
        pattern_pages = {}  # {pattern: set(pages)}
        
        for block in blocks:
            original_text = block.get('text', '').strip()
            if not original_text or len(original_text) < 5:
                continue
                
            page_num = None
            metadata = block.get('metadata', {})
            if 'page_number' in metadata:
                page_num = metadata['page_number']
            elif 'source_page_number' in metadata:
                page_num = metadata['source_page_number']
            elif 'page' in metadata:
                page_num = metadata['page']
                
            if page_num is not None:
                # Buscar patrones específicos de corrupción de "Antología Rubén Darío"
                patterns_to_check = [
                    r'\*Antolo\*.*\*[gí]\*.*\*[íi]a\*.*Rub[eé]n.*Dar[íi]o',  # *Antolo* *g* *ía* *Rubén Darío*
                    r'Antolo.*Rub[eé]n.*Dar[íi]o',  # Variaciones simples de "Antología Rubén Darío"
                    r'\*.*Antolo.*\*.*Rub[eé]n.*Dar[íi]o',  # Cualquier cosa con asteriscos, Antolo, Rubén, Darío
                ]
                
                for pattern in patterns_to_check:
                    if re.search(pattern, original_text, re.IGNORECASE):
                        pattern_key = "antologia_ruben_dario_pattern"
                        if pattern_key not in pattern_pages:
                            pattern_pages[pattern_key] = set()
                        pattern_pages[pattern_key].add(page_num)
                        logger.debug(f"🎯 Patrón detectado en página {page_num}: '{original_text[:50]}...'")
                        break
        
        # Verificar si los patrones aparecen en suficientes páginas
        for pattern_key, pages in pattern_pages.items():
            frequency = len(pages) / total_pages
            if frequency >= threshold:
                logger.warning(f"🚫 Patrón estructural detectado ({frequency*100:.1f}%): {pattern_key}")
                
                # Agregar todos los bloques que coincidan con este patrón
                for block in blocks:
                    original_text = block.get('text', '').strip()
                    if original_text and len(original_text) >= 5:
                        # Aplicar los mismos patrones de búsqueda
                        patterns_to_check = [
                            r'\*Antolo\*.*\*[gí]\*.*\*[íi]a\*.*Rub[eé]n.*Dar[íi]o',
                            r'Antolo.*Rub[eé]n.*Dar[íi]o',
                            r'\*.*Antolo.*\*.*Rub[eé]n.*Dar[íi]o',
                        ]
                        
                        for pattern in patterns_to_check:
                            if re.search(pattern, original_text, re.IGNORECASE):
                                structural_elements.append(original_text)
                                logger.debug(f"🎯 Agregado por patrón: '{original_text[:30]}...'")
                                break
        
        logger.info(f"🔍 Detección completada: {len(structural_elements)} elementos estructurales encontrados")
        return structural_elements

    def _filter_structural_elements(self, blocks: List[Dict], structural_elements: List[str]) -> List[Dict]:
        """
        🔧 MEJORADO: Filtra elementos estructurales de los bloques Y limpia texto que los contenga.
        
        Args:
            blocks: Lista de bloques originales
            structural_elements: Lista de textos estructurales a filtrar
            
        Returns:
            Lista de bloques filtrados sin elementos estructurales
        """
        if not structural_elements:
            return blocks
            
        filtered_blocks = []
        filtered_count = 0
        cleaned_count = 0
        
        for block in blocks:
            text = block.get('text', '').strip()
            
            # Verificar si el texto ES EXACTAMENTE un elemento estructural
            is_structural = text in structural_elements
            
            if is_structural:
                filtered_count += 1
                logger.debug(f"🚫 Filtrando bloque estructural completo: '{text[:30]}{'...' if len(text) > 30 else ''}'")
                continue
            
            # NUEVA FUNCIONALIDAD: Limpiar elementos estructurales DENTRO del texto
            cleaned_text = text
            text_was_cleaned = False
            
            for structural_element in structural_elements:
                if structural_element in cleaned_text:
                    # Remover el elemento estructural del texto
                    cleaned_text = cleaned_text.replace(structural_element, '').strip()
                    text_was_cleaned = True
                    logger.debug(f"🧹 Limpiando elemento estructural '{structural_element[:20]}...' del bloque")
            
            # Limpiar saltos de línea y espacios excesivos después de la limpieza
            if text_was_cleaned:
                cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Max 2 saltos consecutivos
                cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)  # Limpiar espacios al inicio/fin de líneas
                cleaned_text = cleaned_text.strip()
                cleaned_count += 1
            
            # Solo agregar si queda contenido después de la limpieza
            if cleaned_text:
                # Crear bloque con texto limpio
                cleaned_block = block.copy()
                cleaned_block['text'] = cleaned_text
                filtered_blocks.append(cleaned_block)
            else:
                # El bloque quedó vacío después de limpiar elementos estructurales
                filtered_count += 1
                logger.debug(f"🗑️ Bloque vacío después de limpieza: eliminado")
        
        logger.info(f"🔄 Filtrado estructural: {len(blocks)} → {len(filtered_blocks)} bloques")
        logger.info(f"   📊 {filtered_count} bloques eliminados, {cleaned_count} bloques limpiados")
        return filtered_blocks

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