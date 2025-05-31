from datetime import datetime, timezone, timedelta
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
# import PyPDF2 # Eliminado PyPDF2
import fitz  # Importación de PyMuPDF
import logging

from .base_loader import BaseLoader

def _calculate_sha256(file_path: Path) -> str:
    """Calcula el hash SHA256 de un archivo."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

logger = logging.getLogger(__name__)

class PDFLoader(BaseLoader):
    """Loader para archivos PDF (.pdf) usando PyMuPDF (fitz) para mayor rendimiento."""
    
    def __init__(self, file_path: str | Path, tipo: str = 'escritos', encoding: str = 'utf-8'):
        """
        Inicializa el loader para archivos PDF.
        
        Args:
            file_path: Ruta al archivo PDF
            tipo: Tipo de contenido (no se usa directamente aquí pero podría ser útil para perfiles)
            encoding: Codificación (no se usa directamente en PDFs pero se mantiene por consistencia)
        """
        super().__init__(file_path)
        self.tipo = tipo.lower()
        # self.encoding = encoding # Encoding no es tan relevante para fitz de esta manera
        logger.debug(f"PDFLoader (fitz) inicializado para: {self.file_path} con tipo: {self.tipo}")

    def _reconstruct_paragraphs(self, lines: List[str]) -> str:
        """
        🚨 VERSIÓN 6.0 - RECONSTRUCCIÓN ANTI-SALTO DE PÁGINA 🚨
        
        Reconstruye párrafos inteligentemente a partir de líneas individuales.
        
        Heurísticas aplicadas:
        1. Las líneas que terminan sin puntuación se unen con la siguiente
        2. Las líneas muy cortas se unen con la anterior/siguiente
        3. Se detectan saltos de párrafo reales vs saltos de línea por formato
        
        Args:
            lines: Lista de líneas de texto del bloque
            
        Returns:
            str: Texto reconstruido con párrafos separados por doble salto de línea
        """
        print("🚨🚨🚨 PDLOADER V6.0 - RECONSTRUCCIÓN ANTI-SALTO 🚨🚨🚨")
        logger.warning("🚨🚨🚨 PDLOADER V6.0 - RECONSTRUCCIÓN ANTI-SALTO 🚨🚨🚨")
        if not lines:
            return ""
        
        if len(lines) == 1:
            single_line_result = lines[0]
            print(f"🔍 PDLOADER: Línea única detectada: '{single_line_result[:100]}...'")
            return single_line_result
            
        paragraphs = []
        current_paragraph = []
        
        print(f"🔍 PDLOADER: Procesando {len(lines)} líneas para reconstrucción")
        logger.warning(f"🔍 PDLOADER: Procesando {len(lines)} líneas para reconstrucción")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Heurística 1: Si la línea anterior no termina con puntuación fuerte
            # y la línea actual no empieza con mayúscula o numeración, unir
            if current_paragraph:
                previous_line = current_paragraph[-1]
                is_break = self._is_paragraph_break(previous_line, line)
                
                # DIAGNÓSTICO ESPECÍFICO para caso "atractivo"
                if "atractivo" in previous_line.lower() or "atractivo" in line.lower():
                    print(f"🚨 DIAGNÓSTICO CRÍTICO ATRACTIVO:")
                    print(f"   Línea anterior: '{previous_line}'")
                    print(f"   Línea actual: '{line}'")
                    print(f"   ¿Es salto de párrafo?: {is_break}")
                    logger.warning(f"🚨 ATRACTIVO - Anterior: '{previous_line}' | Actual: '{line}' | Break: {is_break}")
                
                if not is_break:
                    current_paragraph.append(line)
                else:
                    # Nuevo párrafo
                    if current_paragraph:
                        paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = [line]
            else:
                current_paragraph = [line]
        
        # Agregar el último párrafo
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Unir párrafos con doble salto de línea
        return '\n\n'.join(paragraphs)
    
    def _is_paragraph_break(self, previous_line: str, current_line: str) -> bool:
        """
        Determina si debe haber un salto de párrafo entre dos líneas.
        
        HEURÍSTICAS ANTI-SALTO DE PÁGINA:
        1. Si la línea anterior termina sin puntuación fuerte → UNIR
        2. Si la línea actual empieza con minúscula → UNIR (continuación)
        3. Si la línea actual continúa una frase obvio → UNIR
        4. ESPECÍFICO: Detectar casos como "atractivo" + "de esta idea"
        
        Args:
            previous_line: Línea anterior
            current_line: Línea actual
            
        Returns:
            bool: True si debe haber salto de párrafo, False si unir
        """
        import re
        
        prev_stripped = previous_line.strip()
        curr_stripped = current_line.strip()
        
        # ===== DETECCIÓN ESPECÍFICA DE ORACIONES DIVIDIDAS =====
        prev_words = prev_stripped.split()
        curr_words = curr_stripped.split()
        
        if prev_words and curr_words:
            last_word = prev_words[-1].lower().rstrip('.,!?:;')
            first_word = curr_words[0].lower()
            
            # Casos específicos de división artificial
            artificial_splits = [
                # "atractivo" + "de esta idea"
                (last_word == "atractivo" and first_word in ["de", "del"]),
                # Otros patrones comunes
                (last_word in ["muy", "más", "tan", "poco", "tanto"] and 
                 first_word not in ["pero", "sin", "embargo", "aunque"]),
                # Preposiciones que requieren continuación
                (last_word in ["para", "por", "en", "con", "sin", "de", "del", "al", "hacia"] and
                 not curr_stripped[0].isupper()),
                # Adjetivos que claramente continúan
                (last_word in ["hermoso", "interesante", "importante", "necesario", "posible"] and
                 first_word in ["de", "para", "que", "en"]),
            ]
            
            if any(artificial_splits):
                print(f"🔗 DETECTADA DIVISIÓN ARTIFICIAL: '{prev_stripped}' + '{curr_stripped}'")
                logger.warning(f"🔗 DIVISIÓN ARTIFICIAL: '{prev_stripped}' + '{curr_stripped}'")
                return False
        
        # REGLA 1: Si la línea anterior NO termina con puntuación fuerte → UNIR
        if not re.search(r'[.!?][\s"]*$', prev_stripped):
            return False
        
        # REGLA 2: Si la línea actual empieza con minúscula → UNIR (continuación)
        if re.match(r'^[a-záéíóúñü]', curr_stripped):
            return False
            
        # REGLA 3: Patrones de continuación obvia → UNIR
        # Ej: "atractivo" + "de esta idea"
        continuation_patterns = [
            r'^(de|del|la|el|en|con|por|para|que|y|o|pero|sin|sobre|bajo)\s+',
            r'^(esta|este|esa|ese|aquella|aquel)\s+',
            r'^(muy|más|menos|tan|tanto)\s+',
            r'^(todos|todas|algunos|muchos|pocos)\s+'
        ]
        
        for pattern in continuation_patterns:
            if re.match(pattern, curr_stripped, re.IGNORECASE):
                return False
        
        # REGLA 4: Si la línea anterior termina con puntuación Y la actual empieza con mayúscula
        if re.search(r'[.!?][\s"]*$', prev_stripped):
            if re.match(r'^[A-ZÁÉÍÓÚÑÜ\d]', curr_stripped):
                return True
        
        # REGLA 5: Si la línea actual empieza con guión o numeración → nuevo párrafo
        if re.match(r'^[-•]\s+|^\d+[\.\)]\s+', curr_stripped):
            return True
            
        # REGLA 6: Si ambas líneas son muy cortas → probablemente mismo párrafo
        if len(prev_stripped) < 40 and len(curr_stripped) < 40:
            return False
            
        # POR DEFECTO: Si llegamos aquí, es muy probable que sea continuación
        # (la mayoría de saltos de página NO son cambios de párrafo)
        return False

    @staticmethod
    def _parse_pdf_datetime_str(date_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Parsea una cadena de fecha/hora de metadatos PDF (ej. 'D:YYYYMMDDHHMMSS[Z|+-HH\'MM\']').

        Returns:
            Tuple[Optional[str], Optional[str]]: (fecha YYYY-MM-DD, fecha ISO completa) o (None, None).
        """
        if not date_str or not isinstance(date_str, str) or not date_str.startswith('D:'):
            return None, None
        
        raw_dt_part = date_str[2:] # Remover 'D:'
        
        # Extraer la parte principal de la fecha/hora (YYYYMMDDHHMMSS)
        dt_core = raw_dt_part[:14]
        
        try:
            parsed_dt = datetime.strptime(dt_core, '%Y%m%d%H%M%S')
            
            # Manejar la información de la zona horaria si existe
            tz_part = raw_dt_part[14:]
            if tz_part:
                if tz_part == 'Z':
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                elif tz_part.startswith(('+', '-')) and len(tz_part) >= 3:
                    try:
                        offset_hours = int(tz_part[1:3])
                        offset_minutes = int(tz_part[4:6]) if len(tz_part) >= 6 and tz_part[3] == "'" else 0
                        delta = timezone(timedelta(hours=offset_hours, minutes=offset_minutes) * (1 if tz_part[0] == '+' else -1))
                        parsed_dt = parsed_dt.replace(tzinfo=delta)
                    except ValueError:
                        # Si la zona horaria es inválida, mantener como naive pero loguear
                        logger.debug(f"No se pudo parsear la zona horaria de PDF: {tz_part} para fecha {date_str}")
                        # Devolver la fecha parseada sin tzinfo explícito, pero sí como ISO
                        return parsed_dt.strftime('%Y-%m-%d'), parsed_dt.isoformat() 
            
            return parsed_dt.strftime('%Y-%m-%d'), parsed_dt.isoformat()
        
        except ValueError as e:
            logger.warning(f"No se pudo parsear la parte central de la fecha PDF '{dt_core}' de '{date_str}': {e}")
            return None, date_str # Devolver la cadena original como fecha ISO si falla el parseo

    def _extract_pdf_metadata(self, doc) -> Dict[str, Any]:
        """
        Extrae metadatos del documento PDF.
        
        Args:
            doc: Documento PyMuPDF abierto
            
        Returns:
            Dict[str, Any]: Metadatos estructurados del PDF
        """
        try:
            pdf_meta = doc.metadata
            
            # Parsear fechas
            creation_date_str = pdf_meta.get('creationDate') if pdf_meta else None
            mod_date_str = pdf_meta.get('modDate') if pdf_meta else None
            
            parsed_creation_date_simple, parsed_creation_date_iso = self._parse_pdf_datetime_str(creation_date_str)
            parsed_mod_date_simple, parsed_mod_date_iso = self._parse_pdf_datetime_str(mod_date_str)
            
            return {
                'titulo_documento': pdf_meta.get('title') if pdf_meta and pdf_meta.get('title') else self.file_path.stem,
                'autor_documento': pdf_meta.get('author') if pdf_meta and pdf_meta.get('author') else None,
                'fecha_publicacion_documento': parsed_creation_date_simple or parsed_mod_date_simple,
                'ruta_archivo_original': str(self.file_path.resolve()),
                'file_format': 'pdf',
                'hash_documento_original': _calculate_sha256(self.file_path),
                'idioma_documento': 'und',
                'metadatos_adicionales_fuente': {
                    'loader_used': 'PDFLoader',
                    'loader_config': {'tipo': self.tipo},
                    'original_fuente': 'pdf_file',
                    'original_contexto': 'document_processing',
                    'blocks_are_fitz_native': True,
                    'pdf_subject': pdf_meta.get('subject') if pdf_meta else None,
                    'pdf_keywords': pdf_meta.get('keywords') if pdf_meta else None,
                    'pdf_creator': pdf_meta.get('creator') if pdf_meta else None,
                    'pdf_producer': pdf_meta.get('producer') if pdf_meta else None,
                    'pdf_creation_date_iso': parsed_creation_date_iso,
                    'pdf_modified_date_iso': parsed_mod_date_iso,
                    'pdf_page_count': doc.page_count
                }
            }
        except Exception as e:
            logger.warning(f"Error extrayendo metadatos PDF: {e}")
            return {
                'titulo_documento': self.file_path.stem,
                'autor_documento': None,
                'fecha_publicacion_documento': None,
                'ruta_archivo_original': str(self.file_path.resolve()),
                'file_format': 'pdf',
                'hash_documento_original': _calculate_sha256(self.file_path),
                'idioma_documento': 'und',
                'metadatos_adicionales_fuente': {
                    'loader_used': 'PDFLoader',
                    'loader_config': {'tipo': self.tipo},
                    'original_fuente': 'pdf_file',
                    'original_contexto': 'document_processing',
                    'blocks_are_fitz_native': True,
                    'pdf_page_count': doc.page_count if doc else 0
                }
            }

    def load(self) -> Dict[str, Any]:
        """
        Carga y procesa el PDF completo, aplicando fusión inteligente entre páginas.
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"El archivo PDF no existe: {self.file_path}")
        
        logger.info(f"Cargando PDF: {self.file_path}")
        
        doc = fitz.open(str(self.file_path))
        
        # Extraer metadatos del PDF
        metadata = self._extract_pdf_metadata(doc)
        
        # 🚨 NUEVA LÓGICA: Procesar todas las páginas y detectar divisiones entre páginas
        all_pages_blocks = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extraer bloques de esta página usando el método dict para máximo detalle
            try:
                text_dict = page.get_text("dict")
                page_blocks = []
                
                for block in text_dict.get("blocks", []):
                    if "lines" in block:  # Solo bloques de texto
                        # Reconstruir texto del bloque Y extraer información visual
                        lines = []
                        font_sizes = []
                        font_weights = []
                        font_names = []
                        
                        for line in block["lines"]:
                            line_text = ""
                            line_fonts = []
                            
                            for span in line["spans"]:
                                line_text += span["text"]
                                # Extraer información de formato de cada span
                                line_fonts.append({
                                    'size': span.get('size', 0),
                                    'flags': span.get('flags', 0),  # bit flags para bold, italic, etc.
                                    'font': span.get('font', ''),
                                    'color': span.get('color', 0)
                                })
                            
                            if line_text.strip():
                                lines.append(line_text.strip())
                                font_sizes.extend([f['size'] for f in line_fonts])
                                font_weights.extend([f['flags'] for f in line_fonts])
                                font_names.extend([f['font'] for f in line_fonts])
                        
                        if lines:
                            # Aplicar reconstrucción de párrafos
                            reconstructed_text = self._reconstruct_paragraphs(lines)
                            if reconstructed_text.strip():
                                # Calcular características visuales promedio
                                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
                                is_bold = any(flags & 2**4 for flags in font_weights)  # Bold flag
                                is_italic = any(flags & 2**1 for flags in font_weights)  # Italic flag
                                dominant_font = max(set(font_names), key=font_names.count) if font_names else ''
                                
                                # Calcular alineación basándose en posición del bloque
                                bbox = block.get('bbox', [0, 0, 0, 0])
                                page_width = page.rect.width
                                left_margin = bbox[0]
                                right_margin = page_width - bbox[2]
                                width = bbox[2] - bbox[0]
                                
                                # Heurística simple para alineación
                                if abs(left_margin - right_margin) < 20:  # Centrado
                                    alignment = 'center'
                                elif left_margin < 50:  # Izquierda
                                    alignment = 'left'
                                else:  # Indentado
                                    alignment = 'indented'
                                
                                page_blocks.append({
                                    'text': reconstructed_text,
                                    'bbox': bbox,
                                    'page': page_num + 1,
                                    'block_type': 'text',
                                    # 🆕 METADATOS VISUALES PARA DETECCIÓN DE TÍTULOS
                                    'visual_metadata': {
                                        'avg_font_size': avg_font_size,
                                        'is_bold': is_bold,
                                        'is_italic': is_italic,
                                        'dominant_font': dominant_font,
                                        'alignment': alignment,
                                        'text_length': len(reconstructed_text),
                                        'line_count': len(lines),
                                        'bbox_width': width,
                                        'page_position': left_margin / page_width if page_width > 0 else 0
                                    }
                                })
                
                all_pages_blocks.extend(page_blocks)
                logger.debug(f"Página {page_num + 1}: {len(page_blocks)} bloques extraídos")
                
            except Exception as e:
                logger.warning(f"Error procesando página {page_num + 1}: {e}")
                # Fallback al método blocks si falla dict
                blocks_raw = page.get_text("blocks")
                for block in blocks_raw:
                    if len(block) >= 5 and block[4].strip():
                        all_pages_blocks.append({
                            'text': block[4].strip(),
                            'bbox': [block[0], block[1], block[2], block[3]],
                            'page': page_num + 1,
                            'block_type': 'text'
                        })
        
        doc.close()
        
        # 🚨 APLICAR FUSIÓN ENTRE PÁGINAS 🚨
        final_blocks = self._merge_cross_page_sentences(all_pages_blocks)
        
        # Convertir al formato esperado por el pipeline
        formatted_blocks = []
        for i, block in enumerate(final_blocks):
            formatted_blocks.append({
                'type': 'text_block',
                'text': block['text'],
                'order_in_document': i,
                'source_page_number': block['page'],
                'source_block_number': i,
                'coordinates': {
                    'x0': block['bbox'][0], 'y0': block['bbox'][1], 
                    'x1': block['bbox'][2], 'y1': block['bbox'][3]
                },
                'merged_from_pages': block.get('merged_from_pages', [block['page']])
            })
        
        logger.info(f"PDF procesado: {len(all_pages_blocks)} bloques iniciales → {len(formatted_blocks)} bloques finales")
        
        return {
            'blocks': formatted_blocks,
            'document_metadata': metadata
        }
    
    def _merge_cross_page_sentences(self, blocks: List[Dict]) -> List[Dict]:
        """
        🚨 FUSIÓN ANTI-SALTO DE PÁGINA 🚨
        
        Detecta y fusiona oraciones divididas artificialmente entre páginas.
        
        Args:
            blocks: Lista de bloques con página, texto y bbox
            
        Returns:
            List[Dict]: Bloques con fusiones aplicadas
        """
        print("🚨🚨🚨 APLICANDO FUSIÓN ENTRE PÁGINAS 🚨🚨🚨")
        logger.warning("🚨🚨🚨 APLICANDO FUSIÓN ENTRE PÁGINAS 🚨🚨🚨")
        
        if len(blocks) < 2:
            return blocks
            
        merged_blocks = []
        i = 0
        
        while i < len(blocks):
            current_block = blocks[i].copy()
            
            # Verificar si hay un siguiente bloque
            if i + 1 < len(blocks):
                next_block = blocks[i + 1]
                
                # ¿Están en páginas consecutivas?
                if (next_block['page'] == current_block['page'] + 1):
                    
                    current_text = current_block['text'].strip()
                    next_text = next_block['text'].strip()
                    
                    # DIAGNÓSTICO ESPECÍFICO
                    if ("atractivo" in current_text.lower() and 
                        "de esta idea" in next_text.lower()):
                        print(f"🎯 DIVISIÓN ENTRE PÁGINAS DETECTADA:")
                        print(f"   Página {current_block['page']}: '{current_text[-50:]}'")
                        print(f"   Página {next_block['page']}: '{next_text[:50]}'")
                        logger.warning(f"🎯 DIVISIÓN CRÍTICA: '{current_text[-50:]}' | '{next_text[:50]}'")
                    
                    # Aplicar heurísticas de fusión
                    if self._should_merge_cross_page(current_text, next_text):
                        print(f"🔗 FUSIONANDO PÁGINAS {current_block['page']} y {next_block['page']}")
                        logger.warning(f"🔗 FUSIÓN APLICADA: páginas {current_block['page']}-{next_block['page']}")
                        
                        # Fusionar textos
                        merged_text = current_text + " " + next_text
                        current_block['text'] = merged_text
                        current_block['merged_from_pages'] = [current_block['page'], next_block['page']]
                        
                        # Saltar el siguiente bloque (ya fue fusionado)
                        i += 2
                        merged_blocks.append(current_block)
                        continue
            
            # No se fusionó, agregar bloque normal
            merged_blocks.append(current_block)
            i += 1
        
        print(f"📊 FUSIÓN COMPLETADA: {len(blocks)} → {len(merged_blocks)} bloques")
        logger.warning(f"📊 FUSIÓN COMPLETADA: {len(blocks)} → {len(merged_blocks)} bloques")
        
        return merged_blocks
    
    def _should_merge_cross_page(self, page1_text: str, page2_text: str) -> bool:
        """
        Determina si dos textos de páginas consecutivas deben fusionarse.
        
        PATRONES DE FUSIÓN ESPECÍFICOS:
        1. Página anterior termina sin puntuación + página siguiente empieza con minúscula
        2. Patrones específicos como "atractivo" + "de esta idea"
        3. Preposiciones y artículos al inicio de página siguiente
        
        Args:
            page1_text: Texto del final de la página anterior
            page2_text: Texto del inicio de la página siguiente
            
        Returns:
            bool: True si deben fusionarse
        """
        import re
        
        # Obtener las últimas palabras de la página anterior
        page1_words = page1_text.strip().split()
        page2_words = page2_text.strip().split()
        
        if not page1_words or not page2_words:
            return False
            
        last_word = page1_words[-1].lower().rstrip('.,!?:;')
        first_word = page2_words[0].lower()
        
        # 🎯 PATRONES ESPECÍFICOS DE DIVISIÓN ARTIFICIAL
        specific_patterns = [
            # El caso exacto que estamos resolviendo
            (last_word == "atractivo" and first_word == "de"),
            # Otros patrones comunes de división por página
            (last_word in ["muy", "más", "tan", "poco", "tanto"] and first_word not in ["pero", "sin"]),
            (last_word in ["para", "por", "en", "con", "sin", "del", "al"] and not page2_text[0].isupper()),
            (last_word in ["que", "como", "cuando", "donde", "quien"] and not page2_text[0].isupper()),
            # Artículos y preposiciones al inicio de página siguiente
            (first_word in ["de", "del", "la", "el", "los", "las", "en", "con", "por", "para", "que"]),
        ]
        
        if any(specific_patterns):
            return True
        
        # REGLA GENERAL: Si página anterior no termina con puntuación Y página siguiente empieza con minúscula
        if (not re.search(r'[.!?][\s"]*$', page1_text.strip()) and 
            page2_text[0].islower()):
            return True
            
        return False