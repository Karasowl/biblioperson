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
        # Nueva configuración para longitud mínima de párrafo y división inteligente por mayúscula
        'min_paragraph_length': 10,  # Longitud mínima para aceptar un párrafo
        'split_on_newline_capital': True,  # Dividir cuando \n y la siguiente línea inicia con mayúscula
        # NUEVA: Configuración específica para documentos largos
        'preserve_long_documents': False,  # Preservar contenido completo en documentos largos
        'max_consecutive_empty_blocks': 5,  # Máximo de bloques vacíos consecutivos antes de parar
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
        
        # 2. LIMPIEZA AGRESIVA: Remover TODOS los caracteres de control problemáticos
        # Caracteres de control ASCII (0x00-0x1F) excepto \n=0x0A, \r=0x0D, \t=0x09
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', ' ', text)
        
        # Caracteres de control extendidos (0x7F-0x9F) - TODOS
        text = re.sub(r'[\x7F-\x9F]', ' ', text)
        
        # 3. NUEVA: Limpieza específica de caracteres problemáticos para JSON
        # Remover caracteres que pueden causar "Invalid control character" en JSON
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\uFEFF\u200B-\u200F\u2028\u2029]', ' ', text)
        
        # 4. Remover secuencias de escape Unicode mal formadas
        text = re.sub(r'\\[uU][0-9a-fA-F]{0,3}(?![0-9a-fA-F])', ' ', text)
        
        # 5. NUEVA FUNCIONALIDAD: Detectar texto predominantemente corrupto
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        if total_chars > 0:
            # Contar caracteres reconocibles vs corruptos
            letras_validas = len(re.findall(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', text))
            palabras_validas = len(re.findall(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]{3,}\b', text))
            
            # Si menos del 30% son letras válidas y hay menos de 2 palabras, es corrupto
            ratio_letras = letras_validas / total_chars
            if ratio_letras < 0.3 and palabras_validas < 2 and total_chars > 50:
                # Marcar como corrupto para filtrado posterior
                return "texto corrupto en archivo de origen"  # Placeholder descriptivo
        
        # 6. Limpiar patrones específicos de corrupción en texto parcialmente corrupto
        # Remover secuencias de símbolos matemáticos sueltos
        text = re.sub(r'\s[+\-*/&%#$@!]{1,2}\s', ' ', text)
        
        # Remover letras sueltas entre espacios (probable corrupción)
        text = re.sub(r'\s[a-zA-Z]\s', ' ', text)
        
        # Remover números sueltos de 1-2 dígitos entre espacios
        text = re.sub(r'\s\d{1,2}\s', ' ', text)
        
        # 7. Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # 8. Limpiar líneas vacías excesivas (mantener máximo 2 saltos consecutivos)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 9. VALIDACIÓN FINAL: Asegurar que no queden caracteres problemáticos
        # Filtrar cualquier carácter que no sea imprimible o válido para JSON
        cleaned_chars = []
        for char in text:
            # Permitir solo caracteres seguros para JSON
            if (ord(char) >= 32 and ord(char) != 127) or char in '\n\r\t':
                cleaned_chars.append(char)
            else:
                cleaned_chars.append(' ')  # Reemplazar con espacio
        
        text = ''.join(cleaned_chars)
        
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
        print("🚨🚨🚨 COMMONBLOCK V7.1 - FUSIÓN INTELIGENTE OCR 🚨🚨🚨")
        logger.warning("🚨🚨🚨 COMMONBLOCK V7.1 - FUSIÓN INTELIGENTE OCR 🚨🚨🚨")
        
        # DEBUG: Ver qué texto estamos recibiendo
        print(f"📊 DEBUG _split_text_into_paragraphs:")
        print(f"   - Longitud del texto: {len(text)}")
        has_newlines = '\\n' in text
        print(f"   - Contiene saltos de línea: {has_newlines}")
        newline_count = text.count('\\n')
        print(f"   - Número de saltos de línea: {newline_count}")
        print(f"   - Primeros 200 chars: {repr(text[:200])}")
        logger.warning(f"📊 DEBUG _split_text_into_paragraphs:")
        logger.warning(f"   - Longitud: {len(text)}, Saltos: {newline_count}")
        logger.warning(f"   - Inicio: {repr(text[:200])}")
        
        if not text or len(text.strip()) < 10:
            return []
        
        # ======= ALGORITMO PRINCIPAL: DOBLE SALTO DE LÍNEA =======
        # Este es el que funcionaba antes para extraer los 60 poemas
        
        paragraphs = []
        
        # Dividir por doble salto de línea (como antes)
        raw_paragraphs = re.split(r'\n\s*\n', text)
        
        # ✨ MEJORADO: Aplicar división por punto + salto + mayúscula en TODOS los párrafos
        # Esto detecta los finales de párrafo típicos en PDFs
        enhanced_paragraphs = []
        for paragraph in raw_paragraphs:
            if paragraph.strip():
                # Dividir por patrón: punto final + salto de línea + mayúscula inicial
                sentence_splits = re.split(r'(?<=[.!?])\s*\n\s*(?=[A-ZÁÉÍÓÚÜÑ])', paragraph)
                enhanced_paragraphs.extend(sentence_splits)
        
        if len(enhanced_paragraphs) > len(raw_paragraphs):
            print(f"📄 DIVISIÓN MEJORADA: {len(raw_paragraphs)} → {len(enhanced_paragraphs)} párrafos")
            logger.warning(f"📄 DIVISIÓN MEJORADA: {len(raw_paragraphs)} → {len(enhanced_paragraphs)} párrafos")
            raw_paragraphs = enhanced_paragraphs
        
        # ✨ ADICIONAL: dividir cuando hay salto de línea seguido de mayúscula (si está configurado)
        if self.config.get('split_on_newline_capital', False) and len(raw_paragraphs) < 10:
            # Solo aplicar si tenemos pocos párrafos (evitar sobre-división)
            refined_paragraphs = []
            for par in raw_paragraphs:
                # Dividir parágrafo por "\nLetraMayúscula" que indica nuevo párrafo indentado en PDF
                sub_parts = re.split(r'\n(?=[A-ZÁÉÍÓÚÜÑ])', par)
                refined_paragraphs.extend(sub_parts)
            
            if len(refined_paragraphs) > len(raw_paragraphs):
                print(f"📄 DIVISIÓN ADICIONAL: {len(raw_paragraphs)} → {len(refined_paragraphs)} párrafos")
                raw_paragraphs = refined_paragraphs
        
        for i, paragraph in enumerate(raw_paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Limpiar el párrafo
            paragraph = re.sub(r'\s+', ' ', paragraph)  # Normalizar espacios
            
            min_len = self.config.get('min_paragraph_length', 20)
            if len(paragraph) >= min_len:
                # Fusión de líneas internas para PROSA/OCR – evita textos truncados
                paragraph_merged = self._merge_lines_in_paragraph(paragraph)

                order = base_order + (i * 0.001)
                paragraphs.append((paragraph_merged, order, original_coordinates))
        
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
                min_len = self.config.get('min_paragraph_length', 20)
                if segment and len(segment) >= min_len:
                    order = base_order + (i * 0.001)
                    fallback_paragraphs.append((segment, order, original_coordinates))
            
            if len(fallback_paragraphs) > len(paragraphs):
                print(f"✅ FALLBACK ESPACIOS: {len(fallback_paragraphs)} párrafos (mejor que {len(paragraphs)})")
                logger.warning(f"✅ FALLBACK ESPACIOS: {len(fallback_paragraphs)} párrafos")
                return fallback_paragraphs
            
            # Fallback 2: Detectar patrones sin saltos de línea (punto + espacio + mayúscula)
            if len(paragraphs) <= 1 and '\n' not in text:
                print("🔧 APLICANDO DIVISIÓN SIN SALTOS DE LÍNEA")
                logger.warning("🔧 APLICANDO DIVISIÓN SIN SALTOS DE LÍNEA")
                
                # Primero, separar números romanos o títulos muy cortos al inicio
                title_pattern = r'^(\*\*)?([IVXLCDM]+|\d+|Capítulo\s+[IVXLCDM]+|Capítulo\s+\d+|Cap\.\s*\d+)(\*\*)?\s+'
                title_match = re.match(title_pattern, text, re.IGNORECASE)
                
                smart_paragraphs = []
                remaining_text = text
                
                if title_match:
                    # Extraer el título como párrafo separado
                    title_text = title_match.group(0).strip()
                    smart_paragraphs.append((title_text, base_order, original_coordinates))
                    remaining_text = text[len(title_match.group(0)):]
                    print(f"📖 TÍTULO DETECTADO: '{title_text}'")
                    logger.warning(f"📖 TÍTULO DETECTADO: '{title_text}'")
                
                # Dividir el resto por punto + espacio + mayúscula
                sentence_pattern = r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÜÑ])'
                sentences = re.split(sentence_pattern, remaining_text)
                
                # Agrupar oraciones en párrafos lógicos
                current_paragraph = ""
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    # Criterios para iniciar nuevo párrafo
                    should_start_new = (
                        not current_paragraph or  # Primer párrafo
                        len(current_paragraph) > 300 or  # Párrafo ya largo
                        sentence.startswith('—') or  # Diálogo
                        re.match(r'^(Cuando|Después|Entonces|Así|De esta manera|Por eso|En ese momento)', sentence)
                    )
                    
                    if should_start_new and current_paragraph:
                        order = base_order + (len(smart_paragraphs) * 0.001)
                        smart_paragraphs.append((current_paragraph.strip(), order, original_coordinates))
                        current_paragraph = sentence
                    else:
                        current_paragraph += (' ' if current_paragraph else '') + sentence
                
                # Agregar último párrafo
                if current_paragraph:
                    order = base_order + (len(smart_paragraphs) * 0.001)
                    smart_paragraphs.append((current_paragraph.strip(), order, original_coordinates))
                
                if len(smart_paragraphs) > len(paragraphs):
                    print(f"✅ DIVISIÓN SIN SALTOS: {len(smart_paragraphs)} párrafos")
                    logger.warning(f"✅ DIVISIÓN SIN SALTOS: {len(smart_paragraphs)} párrafos")
                    return smart_paragraphs
            
            # Fallback 3: Fusión inteligente de líneas (para OCR)
            elif len(paragraphs) <= 1:
                print("🔧 APLICANDO FUSIÓN INTELIGENTE DE LÍNEAS (OCR)")
                logger.warning("🔧 APLICANDO FUSIÓN INTELIGENTE DE LÍNEAS (OCR)")
                
                lines = text.split('\n')
                smart_paragraphs = self._smart_merge_lines(lines, base_order, original_coordinates)
                
                if len(smart_paragraphs) > len(paragraphs):
                    print(f"✅ FUSIÓN INTELIGENTE: {len(smart_paragraphs)} párrafos")
                    logger.warning(f"✅ FUSIÓN INTELIGENTE: {len(smart_paragraphs)} párrafos")
                    return smart_paragraphs
        
        # Heurística adicional eliminada — se reemplaza por detección de fragmentación OCR integrada a nivel de bloque.

        print(f"🎯 RESULTADO FINAL: {len(paragraphs)} párrafos tras heurísticas")
        logger.warning(f"🎯 RESULTADO FINAL: {len(paragraphs)} párrafos tras heurísticas")
        
        return paragraphs

    def _merge_lines_in_paragraph(self, par_text: str) -> str:
        """Fusiona líneas internas de un mismo párrafo cuando parecen fragmentadas.

        Heurística: si el párrafo contiene numerosos saltos de línea internos (\n) y
        la longitud media por línea es baja (<90-100 caracteres), intentamos fusionar
        usando la lógica de _should_merge_lines para reconstruir oraciones completas.
        """

        if '\n' not in par_text:
            return par_text.strip()

        lines_local = [l.rstrip() for l in par_text.split('\n') if l.strip()]

        # Calcular longitud media para decidir si vale la pena fusionar
        avg_line_len = sum(len(l) for l in lines_local) / max(len(lines_local), 1)

        # Umbral conservador – solo fusionar si son líneas cortas en promedio
        if avg_line_len > 100:
            return par_text.strip()

        merged = lines_local[0]
        for ln in lines_local[1:]:
            if self._should_merge_lines(merged, ln):
                sep = self._get_merge_separator(merged, ln)
                merged = f"{merged}{sep}{ln.lstrip()}"
            else:
                merged = f"{merged}\n{ln}"  # Mantener salto si claramente inicia nuevo párrafo

        return merged.strip()

    def _smart_merge_lines(self, lines: List[str], base_order: float, original_coordinates: Optional[Dict] = None) -> List[Tuple[str, float, Optional[Dict]]]:
        """
        Fusiona líneas inteligentemente para formar párrafos coherentes.
        Especialmente útil para texto extraído por OCR.
        """
        if not lines:
            return []
        
        merged_paragraphs = []
        current_paragraph = ""
        paragraph_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                # Línea vacía - finalizar párrafo actual si existe
                min_len_cfg = self.config.get('min_paragraph_length', 30)
                if current_paragraph and len(current_paragraph) >= min_len_cfg:
                    order = base_order + (paragraph_count * 0.001)
                    merged_paragraphs.append((current_paragraph.strip(), order, original_coordinates))
                    paragraph_count += 1
                current_paragraph = ""
                continue
            
            if not current_paragraph:
                # Iniciar nuevo párrafo
                current_paragraph = line
            else:
                # Decidir si fusionar con el párrafo actual
                if self._should_merge_lines(current_paragraph, line):
                    # Fusionar con espacio
                    current_paragraph += " " + line
                else:
                    # Finalizar párrafo actual y empezar uno nuevo
                    min_len_cfg = self.config.get('min_paragraph_length', 30)
                    if current_paragraph and len(current_paragraph) >= min_len_cfg:
                        order = base_order + (paragraph_count * 0.001)
                        merged_paragraphs.append((current_paragraph.strip(), order, original_coordinates))
                        paragraph_count += 1
                    current_paragraph = line
        
        # Agregar el último párrafo si existe
        min_len_cfg = self.config.get('min_paragraph_length', 30)
        if current_paragraph and len(current_paragraph) >= min_len_cfg:
            order = base_order + (paragraph_count * 0.001)
            merged_paragraphs.append((current_paragraph.strip(), order, original_coordinates))
        
        return merged_paragraphs
    
    def _should_merge_lines(self, current_paragraph: str, new_line: str) -> bool:
        """
        Determina si una nueva línea debe fusionarse con el párrafo actual.
        """
        current_stripped = current_paragraph.strip()
        new_stripped = new_line.strip()
        
        if not current_stripped or not new_stripped:
            return False
        
        # No fusionar si el párrafo actual es muy largo (probablemente ya completo)
        if len(current_stripped) > 500:
            return False
        
        # No fusionar si la nueva línea parece ser un título o encabezado
        if self._looks_like_title(new_stripped):
            return False
        
        # Fusionar si el párrafo actual no termina con puntuación fuerte
        ends_without_punctuation = not current_stripped.endswith(('.', '!', '?', ':', ';'))
        
        # Fusionar si la nueva línea empieza con minúscula (continuación)
        starts_lowercase = new_stripped[0].islower()
        
        # Fusionar si el párrafo actual termina con palabra que requiere continuación
        current_words = current_stripped.split()
        if current_words:
            last_word = current_words[-1].lower()
            continuation_words = ['de', 'del', 'en', 'con', 'por', 'para', 'que', 'y', 'o', 'pero', 'sin', 'a', 'al']
            if last_word in continuation_words:
                return True
        
        return ends_without_punctuation and starts_lowercase
    
    def _looks_like_title(self, text: str) -> bool:
        """
        Detecta si un texto parece ser un título o encabezado.
        """
        text_stripped = text.strip()
        
        # Títulos suelen ser cortos
        if len(text_stripped) > 100:
            return False
        
        # Títulos suelen empezar con mayúscula
        if not text_stripped[0].isupper():
            return False
        
        # Títulos suelen tener todas las palabras importantes en mayúscula
        words = text_stripped.split()
        if len(words) <= 5:  # Solo para textos cortos
            capitalized_words = sum(1 for word in words if word[0].isupper())
            if capitalized_words / len(words) > 0.6:  # Más del 60% en mayúscula
                return True
        
        return False

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
                logger.info(f"🔗 FUSIONANDO ORACIÓN DIVIDIDA: '{current_block.get('text', '')[-30:]}' + '{block.get('text', '')[:30]}'")
                sep = self._get_merge_separator(current_block['text'], block['text'])
                current_block['text'] = current_block['text'].rstrip() + sep + block['text'].lstrip()
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
                sep = self._get_merge_separator(curr_text, next_text)
                current_block['text'] = curr_text.rstrip() + sep + next_text.lstrip()
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
        
        # NUEVA VALIDACIÓN: No fusionar si el segundo bloque es un título corto
        if self._looks_like_short_title(text2):
            logger.info(f"🚫 NO FUSIONAR ORACIONES: segundo bloque es título: '{text2[:50]}'")
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
            logger.info(f"🔍 DETECTADA DIVISIÓN ARTIFICIAL:")
            logger.info(f"   Bloque 1: '{text1[-50:]}'")
            logger.info(f"   Bloque 2: '{text2[:50]}'")
            logger.info(f"   Sin puntuación: {ends_without_punctuation}, Minúscula: {starts_lowercase}")
        
        return should_merge

    def _should_merge_blocks(self, curr_text: str, next_text: str, curr_page: int, 
                           next_page: int, vertical_gap: float, max_gap: float) -> bool:
        """
        Determina si dos bloques contiguos deben fusionarse.
        
        NUEVA LÓGICA: Más conservador con títulos y números romanos
        """
        curr_stripped = curr_text.strip()
        next_stripped = next_text.strip()
        
        # NO fusionar si el siguiente bloque parece ser un título corto
        if self._looks_like_short_title(next_stripped):
            logger.info(f"🚫 NO FUSIONAR: siguiente bloque parece título: '{next_stripped[:50]}'")
            return False
        
        # NO fusionar si son de páginas diferentes Y el siguiente es un título potencial
        if curr_page != next_page and len(next_stripped) < 100:
            if next_stripped[0].isupper() or re.match(r'^[IVXLCDM]+\s*$', next_stripped):
                logger.info(f"🚫 NO FUSIONAR: cambio de página con posible título: '{next_stripped[:50]}'")
                return False
        
        # Lógica existente de fusión
        # Fusión más agresiva para PDFs con OCR (problemas de líneas cortadas)
        if self.config.get('aggressive_merge_for_pdfs', True):
            # Criterios para NO fusionar
            if self._looks_like_title(next_text):
                return False
            
            # No fusionar si hay un cambio grande de página
            if abs(next_page - curr_page) > 1:
                return False
            
            # NUEVA LÓGICA: No fusionar si el gap vertical es grande Y el siguiente texto empieza con mayúscula
            # (indica nuevo párrafo/sección)
            if vertical_gap > 15 and next_stripped and next_stripped[0].isupper():
                return False
            
            # Fusionar si:
            # 1. Están en la misma página o páginas consecutivas
            # 2. El gap vertical es razonable
            # 3. El texto actual no termina con puntuación fuerte
            same_or_consecutive_page = abs(next_page - curr_page) <= 1
            reasonable_gap = vertical_gap <= self.config.get('max_vertical_gap_aggressive_pt', 20)
            needs_continuation = not curr_text.rstrip().endswith(('.', '!', '?', ':', ';'))
            
            return same_or_consecutive_page and reasonable_gap and needs_continuation
        
        # Lógica original más conservadora
        return (curr_page == next_page and 
                vertical_gap <= max_gap and 
                not self._looks_like_title(next_text))
    
    def _looks_like_short_title(self, text: str) -> bool:
        """
        Detecta títulos muy cortos como números romanos o capítulos
        """
        text_stripped = text.strip()
        
        # Números romanos solos
        if re.match(r'^[IVXLCDM]+\s*$', text_stripped):
            return True
        
        # Texto muy corto (menos de 20 chars) todo en mayúsculas
        if len(text_stripped) < 20 and text_stripped.isupper():
            return True
        
        # Patrones de capítulo/parte muy cortos
        short_title_patterns = [
            r'^(Capítulo|CAPÍTULO|Cap\.?|CAP\.?)\s*[IVXLCDM0-9]+\s*$',
            r'^(Parte|PARTE)\s*[IVXLCDM0-9]+\s*$',
            r'^\d+\s*$',  # Solo números
            r'^[A-Z]\s*$',  # Una sola letra mayúscula
        ]
        
        for pattern in short_title_patterns:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return True
        
        return False

    def _is_title_or_header_text(self, text: str) -> bool:
        """
        Detectar títulos o encabezados usando estructura markdown y patrones semánticos.
        Versión adaptada del MarkdownSegmenter para el CommonBlockPreprocessor.
        """
        text_stripped = text.strip()
        
        # 1. ENCABEZADOS MARKDOWN (###, ####, etc.)
        if re.match(r'^#{1,6}\s+', text_stripped):
            return True
        
        # 2. TEXTO EN NEGRITA QUE PARECE TÍTULO/SECCIÓN
        # Detectar **TEXTO** que parece encabezado de sección
        bold_pattern = r'^\*\*([^*]+)\*\*$'
        bold_match = re.match(bold_pattern, text_stripped)
        if bold_match:
            bold_content = bold_match.group(1).strip()
            # Si está en mayúsculas o parece título de sección
            if (bold_content.isupper() or 
                len(bold_content) < 100 or
                any(indicator in bold_content.lower() for indicator in 
                    ['radio', 'capítulo', 'parte', 'sección', 'prólogo', 'epílogo', 'miércoles', 'lunes', 'martes', 'jueves', 'viernes', 'sábado', 'domingo'])):
                return True
        
        # 3. TEXTO TODO EN MAYÚSCULAS (probable título)
        if text_stripped.isupper() and len(text_stripped) > 5:
            return True
        
        # 4. PATRONES DE TÍTULOS TRADICIONALES
        if len(text_stripped) < 100 and not text_stripped.endswith('.'):
            title_indicators = ['capítulo', 'parte', 'sección', 'prólogo', 'epílogo']
            if any(indicator in text_stripped.lower() for indicator in title_indicators):
                return True
        
        # 5. PATRONES DE FECHA/LUGAR QUE INDICAN NUEVA SECCIÓN
        # Ej: "RADIO EXTERIOR DE ESPAÑA. MIÉRCOLES 13 MARZO"
        date_place_patterns = [
            r'[A-Z\s]+\.\s+(LUNES|MARTES|MIÉRCOLES|JUEVES|VIERNES|SÁBADO|DOMINGO)',
            r'[A-Z\s]+\s+\d{1,2}\s+(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)',
            r'^[A-Z\s]{10,}\.$'  # Texto largo en mayúsculas terminado en punto
        ]
        
        for pattern in date_place_patterns:
            if re.search(pattern, text_stripped, re.IGNORECASE):
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
        🚨 VERSIÓN 7.1 - FUSIÓN INTELIGENTE OCR 🚨
        
        Procesa bloques con fusión inteligente para OCR que genera líneas fragmentadas.
        Detecta automáticamente si el texto viene de OCR y aplica fusión apropiada.
        
        Args:
            blocks: Lista de bloques de texto con metadatos.
            document_metadata: Metadatos del documento.
            
        Returns:
            Lista de bloques procesados.
        """
        print("🚨🚨🚨 COMMONBLOCK V7.1 - FUSIÓN INTELIGENTE OCR 🚨🚨🚨")
        logger.warning("🚨🚨🚨 COMMONBLOCK V7.1 - FUSIÓN INTELIGENTE OCR 🚨🚨🚨")
        
        # DEBUG: Ver qué bloques estamos recibiendo
        print(f"📊 DEBUG process - Bloques recibidos: {len(blocks)}")
        logger.warning(f"📊 DEBUG process - Bloques recibidos: {len(blocks)}")
        for i, block in enumerate(blocks[:3]):  # Primeros 3 bloques
            text = block.get('text', '')
            print(f"   Bloque {i}: {len(text)} chars, inicio: {repr(text[:100])}")
            logger.warning(f"   Bloque {i}: {len(text)} chars")
        
        if not blocks:
            logger.info("No hay bloques para procesar.")
            return []
        
        logger.info(f"Iniciando procesamiento de {len(blocks)} bloques.")
        
        # 🆕 PASO 1: Detectar y filtrar elementos estructurales
        structural_elements = self._detect_structural_elements(blocks)
        if structural_elements:
            blocks = self._filter_structural_elements(blocks, structural_elements)
            logger.info(f"✅ Filtrado estructural aplicado: {len(structural_elements)} elementos eliminados")
        
        # 🆕 PASO 2: Detectar si es texto OCR y aplicar fusión inteligente
        ocr_detected = self._detect_ocr_fragmentation(blocks, document_metadata.get('doc_profile_used', ''))
        if ocr_detected:
            logger.warning("🔍 TEXTO OCR DETECTADO - APLICANDO FUSIÓN INTELIGENTE")
            blocks = self._merge_contiguous_fitz_blocks(blocks)
            logger.warning(f"✅ FUSIÓN OCR APLICADA: {len(blocks)} bloques después de fusión")
        
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
                # Para texto OCR FUSIONADO, dividir en párrafos basándose en puntuación
                if ocr_detected and len(text) > 1000:  # Texto fusionado grande
                    logger.info(f"📄 Dividiendo texto fusionado OCR en párrafos: {len(text)} caracteres")
                    paragraph_blocks = self._split_fused_text_into_paragraphs(
                        text, 
                        i, 
                        block.get('metadata', {})
                    )
                    # Convertir la estructura devuelta por _split_fused_text_into_paragraphs
                    for para_block in paragraph_blocks:
                        new_block = {
                            'text': para_block['text'],
                            'metadata': {
                                'order': para_block['metadata']['order'],
                                'source_block': i,
                                'type': para_block['metadata'].get('type', 'paragraph'),
                                **block.get('metadata', {})
                            }
                        }
                        processed_blocks.append(new_block)
                elif ocr_detected:
                    # Para fragmentos OCR pequeños, usar fusión inteligente de líneas
                    paragraphs = self._smart_merge_lines(
                        text.split('\n'), 
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

    def _detect_ocr_fragmentation(self, blocks: List[Dict], doc_profile: str = "") -> bool:
        """
        Detecta si los bloques provienen de OCR y están excesivamente fragmentados.
        
        Criterios para detectar OCR fragmentado:
        - Muchos bloques muy cortos (< 100 caracteres)
        - Alta proporción de bloques de una sola línea
        - Patrones típicos de OCR línea por línea
        
        Returns:
            True si se detecta fragmentación OCR, False en caso contrario
        """
        # Evitar analizar documentos de verso: la poesía legítimamente produce líneas cortas
        if doc_profile and doc_profile.lower() == 'verso':
            return False

        if len(blocks) < 50:  # Muy pocos bloques para ser OCR fragmentado
            return False
        
        short_blocks = 0
        single_line_blocks = 0
        total_text_blocks = 0
        no_punct_blocks = 0
        
        for block in blocks:
            text = block.get('text', '').strip()
            if not text:
                continue
                
            total_text_blocks += 1
            
            # Contar bloques cortos
            if len(text) < 100:
                short_blocks += 1
            
            # Contar bloques de una sola línea
            if '\n' not in text:
                single_line_blocks += 1
            
            # Contar bloques que NO terminan en puntuación fuerte
            if not text.endswith(('.', '!', '?', ':', ';')):
                no_punct_blocks += 1
        
        if total_text_blocks == 0:
            return False
        
        # Calcular proporciones
        short_ratio = short_blocks / total_text_blocks
        single_line_ratio = single_line_blocks / total_text_blocks
        no_punct_ratio = no_punct_blocks / total_text_blocks
        
        # Métrica adicional: longitud media por bloque
        total_chars = sum(len(b.get('text','')) for b in blocks if b.get('text'))
        avg_len = (total_chars / total_text_blocks) if total_text_blocks else 0

        # Detectar OCR si se cumple UNO de los siguientes escenarios:
        # 1) Criterios estrictos (65/75/70) -> OCR fragmentado evidente
        # 2) Documento muy fragmentado (>500 bloques) Y la longitud media es baja (<120) Y al menos 50 % de bloques son cortos
        ocr_detected = (
            (short_ratio > 0.65 and single_line_ratio > 0.75 and no_punct_ratio > 0.7) or
            (total_text_blocks > 500 and avg_len < 120 and short_ratio > 0.5)
        )

        if ocr_detected:
            logger.warning("🔍 OCR FRAGMENTADO DETECTADO:")
            logger.warning(f"   📊 Bloques totales: {total_text_blocks}")
            logger.warning(f"   📏 Bloques cortos (<100 chars): {short_blocks} ({short_ratio:.1%})")
            logger.warning(f"   📝 Bloques una línea: {single_line_blocks} ({single_line_ratio:.1%})")
            logger.warning(f"   ❌ Bloques sin puntuación final: {no_punct_blocks} ({no_punct_ratio:.1%})")
            logger.warning(f"   ➡️  Longitud media por bloque: {avg_len:.1f} chars")
        
        return ocr_detected

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

    def _split_fused_text_into_paragraphs(self, text: str, base_order: float, original_metadata: Dict) -> List[Dict]:
        """
        Divide texto fusionado en párrafos usando ÚNICAMENTE la estructura semántica del documento.
        NO hace divisiones arbitrarias por longitud.
        """
        if not text.strip():
            return []
        
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 DIVIDIENDO TEXTO FUSIONADO: {len(text)} caracteres usando estructura semántica")
        
        # Método 1: División por dobles saltos de línea (estructura natural del documento)
        natural_paragraphs = re.split(r'\n\s*\n\s*', text)
        if len(natural_paragraphs) > 1:
            logger.info(f"📄 Encontrados {len(natural_paragraphs)} párrafos naturales (dobles saltos)")
            paragraphs = []
            for i, para_text in enumerate(natural_paragraphs):
                para_text = para_text.strip()
                if para_text:  # Cualquier párrafo con contenido es válido
                    paragraphs.append({
                        'text': para_text,
                        'metadata': {
                            'order': base_order + (i * 0.01),
                            'source_block': original_metadata.get('source_block', 0),
                            'type': 'paragraph',
                            'post_ocr_split': True,
                            'split_method': 'semantic_natural_paragraphs',
                            **original_metadata
                        }
                    })
            if paragraphs:
                logger.info(f"✅ División semántica por párrafos naturales: {len(paragraphs)} párrafos")
                return paragraphs
        
        # Método 2: División por headers markdown y patrones semánticos específicos
        semantic_patterns = [
            r'(?<=[.!?])\s*\n\s*(?=\*\*[A-ZÁÉÍÓÚÜÑ][^*]*\*\*)',  # **HEADERS EN MAYÚSCULAS**
            r'(?<=[.!?])\s*\n\s*(?=#{1,6}\s+)',  # Headers markdown (# ## ###)
            r'(?<=[.!?])\s*\n\s*(?=RADIO\s+EXTERIOR)',  # "RADIO EXTERIOR"
            r'(?<=[.!?])\s*\n\s*(?=RADIO\s+REBELDE)',  # "RADIO REBELDE"
            r'(?<=[.!?])\s*\n\s*(?=MIÉRCOLES|LUNES|MARTES|JUEVES|VIERNES|SÁBADO|DOMINGO)',  # Días de la semana
            r'(?<=[.!?])\s*\n\s*(?=[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]{15,})',  # TEXTO EN MAYÚSCULAS LARGO (títulos)
            r'(?<=[.!?])\s*\n\s*(?=\d+\.)',  # Punto + salto + número (listas)
            r'(?<=[.!?])\s*\n\s*(?=[-•*]\s)',  # Punto + salto + viñeta
        ]
        
        for pattern in semantic_patterns:
            splits = re.split(pattern, text)
            if len(splits) > 1:  # Al menos 2 segmentos
                logger.info(f"📄 Patrón semántico encontró {len(splits)} segmentos")
                paragraphs = []
                
                for i, segment in enumerate(splits):
                    segment = segment.strip()
                    if segment:  # Cualquier segmento con contenido es válido
                        paragraphs.append({
                            'text': segment,
                            'metadata': {
                                'order': base_order + (i * 0.01),
                                'source_block': original_metadata.get('source_block', 0),
                                'type': 'paragraph',
                                'post_ocr_split': True,
                                'split_method': 'semantic_pattern',
                                **original_metadata
                            }
                        })
                
                if len(paragraphs) > 1:
                    logger.info(f"✅ División semántica por patrón: {len(paragraphs)} párrafos")
                    return paragraphs
        
        # Método 3: División por estructura de párrafos (puntuación + salto + mayúscula)
        paragraph_pattern = r'(?<=[.!?])\s*\n\s*(?=[A-ZÁÉÍÓÚÜÑ])'
        sentences = re.split(paragraph_pattern, text)
        if len(sentences) > 1:
            logger.info(f"📄 División por estructura de párrafos: {len(sentences)} segmentos")
            paragraphs = []
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if sentence:  # Cualquier párrafo con contenido es válido
                    paragraphs.append({
                        'text': sentence,
                        'metadata': {
                            'order': base_order + (i * 0.01),
                            'source_block': original_metadata.get('source_block', 0),
                            'type': 'paragraph',
                            'post_ocr_split': True,
                            'split_method': 'semantic_paragraph_structure',
                            **original_metadata
                        }
                    })
            
            if len(paragraphs) > 1:
                logger.info(f"✅ División semántica por estructura: {len(paragraphs)} párrafos")
                return paragraphs
        
        # Si no se puede dividir semánticamente, mantener como párrafo único
        logger.info("📄 Manteniendo texto como párrafo único (no se encontró estructura semántica)")
        return [{
            'text': text.strip(),
            'metadata': {
                'order': base_order,
                'source_block': original_metadata.get('source_block', 0),
                'type': 'paragraph',
                'post_ocr_split': False,
                'split_method': 'semantic_single_paragraph',
                **original_metadata
            }
        }]

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