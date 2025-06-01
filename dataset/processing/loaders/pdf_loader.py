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
    """
    Cargador para archivos PDF con capacidades de OCR inteligente.
    
    Incluye:
    - Detección automática de necesidad de OCR
    - OCR como fallback para PDFs problemáticos
    - Evaluación POST-segmentación para detectar granularidad insuficiente
    """
    
    def __init__(self, file_path: str, tipo: str = None, encoding: str = 'utf-8', **kwargs):
        """
        Inicializa el cargador PDF.
        
        Args:
            file_path (str): Ruta al archivo PDF
            tipo (str): Tipo de contenido (opcional, por compatibilidad)
            encoding (str): Codificación (opcional, por compatibilidad)
            **kwargs: Argumentos adicionales para compatibilidad
        """
        super().__init__(file_path)
        self.logger = logging.getLogger(__name__)
        
        # PREPROCESSOR VERSION LOCK LOG
        self.logger.warning("🚀 PDLOADER V7.5 - OCR ULTRA RESTRICTIVO (SOLO CASOS EXTREMOS) 🚀")
        
        # Mantener atributos por compatibilidad, manejando tanto argumentos posicionales como keyword
        # Si tipo viene como None, usar valor por defecto
        self.tipo = (tipo or 'escritos').lower() if tipo else 'escritos'
        
        # El encoding puede venir como argumento keyword desde ProfileManager
        self.encoding = kwargs.get('encoding', encoding)
        
        self.total_chars_extracted = 0
        self.corruption_percentage = 0.0
        self.uses_ocr = False
        
    def load(self) -> Dict[str, Any]:
        """
        Carga el archivo PDF con detección inteligente de OCR.
        
        Incluye evaluación POST-segmentación para activar OCR automáticamente
        cuando la granularidad de segmentos es insuficiente.
        
        Returns:
            Dict[str, Any]: Diccionario con la información extraída
        """
        self.logger.warning("🚀 PDLOADER V7.5 LOAD - OCR ULTRA RESTRICTIVO 🚀")
        
        try:
            self.logger.warning("📋 PASO 1: EXTRACCIÓN TRADICIONAL...")
            
            # Paso 1: Intentar extracción tradicional
            pdf_document = fitz.open(self.file_path)
            
            # Extraer texto usando el método de markdown
            markdown_text = self._extract_as_markdown(pdf_document)
            self.total_chars_extracted = len(markdown_text)
            
            self.logger.warning(f"📝 EXTRACCIÓN TRADICIONAL: {self.total_chars_extracted} caracteres")
            
            # Crear bloques estructurados
            self.logger.warning("🔄 EXTRAYENDO BLOQUES DE MARKDOWN")
            blocks = self._create_blocks_from_markdown(markdown_text)
            self.logger.warning(f"📦 BLOQUES EXTRAÍDOS: {len(blocks)}")
            
            # Crear metadatos
            metadata = self._create_metadata(pdf_document, markdown_text)
            
            # Paso 2: Evaluación PRE-segmentación (corrupción, etc.)
            self.logger.warning("🧠 EVALUANDO NECESIDAD DE OCR PRE-SEGMENTACIÓN...")
            needs_ocr_pre, reasons_pre = self._should_use_ocr(pdf_document, blocks, metadata)
            
            if needs_ocr_pre:
                self.logger.warning(f"🎯 DECISIÓN PRE-SEGMENTACIÓN: ACTIVAR OCR - {', '.join(reasons_pre)}")
                return self._extract_with_ocr(pdf_document, blocks, metadata)
            else:
                self.logger.warning("🎯 DECISIÓN PRE-SEGMENTACIÓN: CONTINUAR SIN OCR")
            
            # Paso 3: Evaluación POST-segmentación (granularidad de segmentos)
            self.logger.warning("🧠 EVALUANDO NECESIDAD DE OCR POST-SEGMENTACIÓN...")
            needs_ocr_post, reasons_post = self._should_use_ocr_post_segmentation(blocks, metadata)
            
            if needs_ocr_post:
                self.logger.warning(f"🎯 DECISIÓN POST-SEGMENTACIÓN: ACTIVAR OCR - {', '.join(reasons_post)}")
                return self._extract_with_ocr(pdf_document, blocks, metadata)
            else:
                self.logger.warning("🎯 DECISIÓN POST-SEGMENTACIÓN: NO REQUIERE OCR")
            
            # Si no necesita OCR, proceder normalmente
            pdf_document.close()
            
            self.logger.warning(f"✅ LOAD COMPLETADO: {len(blocks)} bloques extraídos")
            
            return {
                'blocks': blocks,
                'metadata': metadata,
                'source_info': {
                    'file_path': self.file_path,
                    'total_chars': self.total_chars_extracted,
                    'corruption_percentage': self.corruption_percentage,
                    'uses_ocr': self.uses_ocr,
                    'extraction_method': 'traditional'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando PDF: {e}")
            raise
    
    def _should_use_ocr_post_segmentation(self, blocks: List[Dict], metadata: Dict) -> Tuple[bool, List[str]]:
        """
        Evalúa si se necesita OCR después de la segmentación inicial.
        
        Detecta casos donde la extracción tradicional genera muy pocos segmentos
        en relación al número de páginas, indicando granularidad insuficiente.
        
        Args:
            blocks: Bloques extraídos tradicionalmente
            metadata: Metadatos del documento
            
        Returns:
            Tuple[bool, List[str]]: (necesita_ocr, razones)
        """
        reasons = []
        page_count = metadata.get('page_count', 1)
        
        # Simular segmentación para evaluar granularidad
        try:
            # Import aquí para evitar dependencias circulares
            from ..segmenters.verse_segmenter import VerseSegmenter
            
            segmenter = VerseSegmenter()
            segments = segmenter.segment(blocks)
            segment_count = len(segments)
            
            # Calcular ratio segmentos/páginas
            ratio = segment_count / page_count if page_count > 0 else 0
            
            self.logger.warning(f"📊 EVALUACIÓN POST-SEGMENTACIÓN:")
            self.logger.warning(f"   📄 Páginas: {page_count}")
            self.logger.warning(f"   🎭 Segmentos detectados: {segment_count}")
            self.logger.warning(f"   📊 Ratio segmentos/páginas: {ratio:.2f}")
            
            # Criterios ULTRA RESTRICTIVOS para activar OCR (solo casos extremos)
            
            # Criterio 1: SOLO documentos con ≤3 segmentos totales (falla completa)
            if segment_count <= 3:
                reasons.append(f"Falla completa de extracción: solo {segment_count} segmentos detectados")
            
            # Criterio 2: SOLO documentos largos (≥20 páginas) con ratio extremadamente bajo (< 0.1)
            elif page_count >= 20 and ratio < 0.1:
                reasons.append(f"Documento muy largo con ratio extremo: {ratio:.3f} < 0.1 en {page_count} páginas")
            
            # Criterio 3: SOLO cuando no hay segmentos útiles (0 segmentos)
            elif segment_count == 0:
                reasons.append(f"Extracción completamente fallida: 0 segmentos")
            
            # CRITERIO 4 ELIMINADO: No usar ratio general como criterio
            # CRITERIO 5 ELIMINADO: No usar "documentos de poesía" como criterio automático
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en evaluación post-segmentación: {e}")
            # Si hay error en segmentación, es otra razón para usar OCR
            reasons.append("Error en segmentación tradicional")
        
        needs_ocr = len(reasons) > 0
        
        if needs_ocr:
            self.logger.warning(f"🚨 POST-SEGMENTACIÓN: OCR NECESARIO")
            for reason in reasons:
                self.logger.warning(f"   • {reason}")
        else:
            self.logger.warning(f"✅ POST-SEGMENTACIÓN: GRANULARIDAD SUFICIENTE")
        
        return needs_ocr, reasons
    
    def _should_use_ocr(self, pdf_document, blocks: List[Dict], metadata: Dict) -> Tuple[bool, List[str]]:
        """
        Determina inteligentemente si se necesita usar OCR basado en múltiples factores.
        
        Args:
            pdf_document: Documento PDF abierto
            blocks: Bloques extraídos tradicionalmente
            metadata: Metadatos del documento
            
        Returns:
            Tuple[bool, List[str]]: (necesita_ocr, razones)
        """
        reasons = []
        
        # Calcular estadísticas de corrupción
        total_text = ""
        total_chars = 0
        corrupted_chars = 0
        very_corrupted_blocks = 0
        
        for block in blocks:
            text = block.get('text', '')
            total_text += text
            total_chars += len(text)
            
            if text:
                # Contar caracteres problemáticos
                corrupted_in_block = sum(1 for char in text if ord(char) < 32 and char not in '\n\r\t')
                corrupted_chars += corrupted_in_block
                
                # Contar bloques altamente corruptos
                block_corruption_rate = corrupted_in_block / len(text) if len(text) > 0 else 0
                if block_corruption_rate > 0.8:  # Más del 80% corrupto
                    very_corrupted_blocks += 1
        
        # Calcular porcentaje de corrupción
        corruption_percentage = (corrupted_chars / total_chars * 100) if total_chars > 0 else 0
        self.corruption_percentage = corruption_percentage
        
        # Calcular bloques legibles
        legible_blocks = len(blocks) - very_corrupted_blocks
        legible_percentage = (legible_blocks / len(blocks) * 100) if len(blocks) > 0 else 0
        
        self.logger.warning(f"📊 Corrupción detectada: {corruption_percentage:.1f}%")
        self.logger.warning(f"📦 Bloques legibles: {legible_blocks}/{len(blocks)} ({legible_percentage:.1f}%)")
        
        # Criterios ULTRA RESTRICTIVOS para activar OCR (solo casos extremos)
        
        # Criterio 1: SOLO corrupción extrema (≥70%)
        if corruption_percentage >= 70:
            reasons.append(f"Corrupción extrema de texto: {corruption_percentage:.1f}%")
        
        # Criterio 2: SOLO cuando >80% de bloques están corruptos
        if very_corrupted_blocks > len(blocks) * 0.8:
            reasons.append(f"Mayoría de bloques corruptos: {very_corrupted_blocks}/{len(blocks)}")
        
        # Criterio 3: SOLO fallas extremas de extracción (≤10 bloques en documentos grandes)
        page_count = metadata.get('page_count', 1)
        if page_count > 20 and len(blocks) <= 10:
            reasons.append(f"Falla extrema de extracción: {len(blocks)} bloques para {page_count} páginas")
        
        # Criterio 4: PDF con protección o encoding especial
        try:
            if pdf_document.needs_pass:
                reasons.append("PDF requiere contraseña")
            elif pdf_document.permissions < 0:  # Permisos negativos indican protección
                reasons.append(f"PDF con protección especial (permisos: {pdf_document.permissions})")
        except:
            pass
        
        # Criterio 5: Texto extraído sospechosamente corto
        if total_chars < 100 and page_count > 2:
            reasons.append(f"Texto extraído muy corto: {total_chars} caracteres en {page_count} páginas")
        
        needs_ocr = len(reasons) > 0
        return needs_ocr, reasons
    
    def _extract_with_ocr(self, pdf_document, fallback_blocks: List[Dict], metadata: Dict) -> Dict[str, Any]:
        """
        Extrae texto usando el sistema OCR flexible con múltiples proveedores.
        
        Args:
            pdf_document: Documento PDF abierto
            fallback_blocks: Bloques de fallback si OCR falla
            metadata: Metadatos del documento
            
        Returns:
            Dict[str, Any]: Resultado con bloques OCR o fallback
        """
        self.logger.warning("🔍 INICIANDO EXTRACCIÓN CON SISTEMA OCR FLEXIBLE...")
        
        try:
            # Importar el nuevo sistema OCR
            from .ocr_providers import OCRManager
            
            # Inicializar gestor OCR
            ocr_manager = OCRManager()
            
            if not ocr_manager.has_available_providers():
                self.logger.warning("❌ No hay proveedores OCR disponibles")
                self.logger.warning("🔄 Usando bloques tradicionales como fallback")
                return self._create_fallback_response(fallback_blocks, metadata, "No OCR providers available")
            
            available_providers = ocr_manager.get_available_providers()
            self.logger.warning(f"✅ Proveedores OCR disponibles: {', '.join(available_providers)}")
            
            # Procesar páginas con OCR
            ocr_blocks = []
            total_ocr_text = ""
            successful_pages = 0
            
            for page_num in range(len(pdf_document)):
                self.logger.warning(f"🔍 OCR en página {page_num + 1}/{len(pdf_document)}")
                
                page = pdf_document[page_num]
                
                # Renderizar página a imagen con alta resolución
                mat = fitz.Matrix(3, 3)  # 3x zoom para mejor calidad OCR
                pix = page.get_pixmap(matrix=mat)
                
                # Convertir a PIL Image
                from PIL import Image
                import io
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Usar OCR Manager para extraer texto
                page_text, provider_used = ocr_manager.extract_text_from_image(image, language='spa')
                
                if page_text.strip():
                    total_ocr_text += page_text + "\n\n"
                    successful_pages += 1
                    
                    # Crear bloques granulares a partir del texto OCR
                    page_blocks = self._create_granular_blocks_from_ocr(page_text, page_num + 1)
                    ocr_blocks.extend(page_blocks)
                    
                    self.logger.warning(f"✅ Página {page_num + 1} procesada con {provider_used}: {len(page_text)} chars")
                else:
                    self.logger.warning(f"⚠️ Página {page_num + 1}: No se extrajo texto")
            
            pdf_document.close()
            
            # Verificar si OCR fue exitoso
            if successful_pages == 0:
                self.logger.warning("❌ OCR no extrajo texto de ninguna página")
                self.logger.warning("🔄 Usando bloques tradicionales como fallback")
                return self._create_fallback_response(fallback_blocks, metadata, "OCR extraction failed")
            
            self.uses_ocr = True
            self.total_chars_extracted = len(total_ocr_text)
            
            # Actualizar metadatos con información OCR
            metadata.update({
                'extraction_method': 'ocr_flexible',
                'ocr_total_chars': len(total_ocr_text),
                'ocr_blocks_generated': len(ocr_blocks),
                'ocr_successful_pages': successful_pages,
                'ocr_providers_used': available_providers
            })
            
            self.logger.warning(f"✅ OCR COMPLETADO: {len(ocr_blocks)} bloques, {len(total_ocr_text)} caracteres")
            self.logger.warning(f"📊 Páginas exitosas: {successful_pages}/{len(pdf_document)}")
            
            return {
                'blocks': ocr_blocks,
                'metadata': metadata,
                'source_info': {
                    'file_path': self.file_path,
                    'total_chars': self.total_chars_extracted,
                    'corruption_percentage': 0.0,  # OCR produce texto limpio
                    'uses_ocr': True,
                    'extraction_method': 'ocr_flexible',
                    'ocr_providers_available': available_providers,
                    'successful_pages': successful_pages
                }
            }
            
        except ImportError as e:
            self.logger.warning(f"❌ Sistema OCR no disponible: {e}")
            self.logger.warning("💡 Para usar OCR, instalar: pip install pytesseract pillow")
            return self._create_fallback_response(fallback_blocks, metadata, f"OCR system unavailable: {e}")
        
        except Exception as e:
            self.logger.error(f"❌ Error en extracción OCR: {e}")
            return self._create_fallback_response(fallback_blocks, metadata, f"OCR error: {e}")
    
    def _create_fallback_response(self, fallback_blocks: List[Dict], metadata: Dict, error_reason: str) -> Dict[str, Any]:
        """Crea respuesta de fallback cuando OCR falla"""
        return {
            'blocks': fallback_blocks,
            'metadata': metadata,
            'source_info': {
                'file_path': self.file_path,
                'total_chars': self.total_chars_extracted,
                'corruption_percentage': self.corruption_percentage,
                'uses_ocr': False,
                'extraction_method': 'traditional_fallback',
                'ocr_error': error_reason
            }
        }
    
    def _create_granular_blocks_from_ocr(self, page_text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Crea bloques granulares a partir del texto OCR de una página.
        
        Cada línea significativa se convierte en un bloque separado
        para mejor segmentación posterior.
        
        Args:
            page_text: Texto extraído por OCR
            page_num: Número de página
            
        Returns:
            List[Dict]: Lista de bloques granulares
        """
        blocks = []
        lines = page_text.split('\n')
        
        current_paragraph = []
        block_order = 0
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Línea vacía - finalizar párrafo actual si existe
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    
                    block = {
                        'text': paragraph_text,
                        'metadata': {
                            'type': 'paragraph',
                            'order': block_order,
                            'page': page_num,
                            'bbox': [0, 0, 100, 100],  # OCR no tiene coordenadas precisas
                            'area': len(paragraph_text),
                            'char_count': len(paragraph_text),
                            'line_count': len(current_paragraph),
                            'vertical_gap': 0,
                            'extraction_method': 'ocr'
                        }
                    }
                    blocks.append(block)
                    block_order += 1
                    current_paragraph = []
                continue
            
            # Detectar si es título (línea corta, centrada, mayúsculas, etc.)
            is_title = self._looks_like_title_ocr(line)
            
            if is_title:
                # Finalizar párrafo anterior si existe
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    
                    block = {
                        'text': paragraph_text,
                        'metadata': {
                            'type': 'heading',
                            'order': block_order,
                            'page': page_num,
                            'bbox': [0, 0, 100, 100],
                            'area': len(paragraph_text),
                            'char_count': len(paragraph_text),
                            'line_count': len(current_paragraph),
                            'vertical_gap': 0,
                            'extraction_method': 'ocr'
                        }
                    }
                    blocks.append(block)
                    block_order += 1
                    current_paragraph = []
                
                # Crear bloque para el título
                title_block = {
                    'text': line,
                    'metadata': {
                        'type': 'heading',
                        'order': block_order,
                        'page': page_num,
                        'bbox': [0, 0, 100, 100],
                        'area': len(line),
                        'char_count': len(line),
                        'line_count': 1,
                        'vertical_gap': 0,
                        'extraction_method': 'ocr'
                    }
                }
                blocks.append(title_block)
                block_order += 1
            else:
                # Agregar línea al párrafo actual
                current_paragraph.append(line)
        
        # Finalizar último párrafo si existe
        if current_paragraph:
            paragraph_text = '\n'.join(current_paragraph)
            
            block = {
                'text': paragraph_text,
                'metadata': {
                    'type': 'paragraph',
                    'order': block_order,
                    'page': page_num,
                    'bbox': [0, 0, 100, 100],
                    'area': len(paragraph_text),
                    'char_count': len(paragraph_text),
                    'line_count': len(current_paragraph),
                    'vertical_gap': 0,
                    'extraction_method': 'ocr'
                }
            }
            blocks.append(block)
        
        return blocks
    
    def _looks_like_title_ocr(self, line: str) -> bool:
        """
        Determina si una línea parece ser un título basado en características OCR.
        
        Args:
            line: Línea de texto
            
        Returns:
            bool: True si parece título
        """
        # Limpiar línea
        line = line.strip()
        
        if len(line) < 3:
            return False
        
        # Patrones comunes de títulos de poemas
        title_patterns = [
            r'^(Poema|POEMA)\s+\d+',  # "Poema 1", "POEMA IV"
            r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)\.?\s*$',  # Números romanos
            r'^\d+\.?\s*$',  # Números arábigos simples
            r'^[A-Z][A-Z\s]{2,30}$',  # Títulos en mayúsculas
            r'.*[Cc]anción.*',  # Títulos con "canción"
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, line):
                return True
        
        # Líneas cortas que podrían ser títulos
        if len(line) <= 50 and (
            line.isupper() or  # Todo en mayúsculas
            line.istitle() or  # Primera letra mayúscula
            line.count(' ') <= 5  # Pocas palabras
        ):
            return True
        
        return False

    def _extract_as_markdown(self, doc):
        """
        Extrae el texto del PDF utilizando un enfoque de markdown estructurado.
        
        Args:
            doc: Documento PDF abierto con fitz
            
        Returns:
            str: Texto en formato markdown
        """
        text_blocks = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Obtener bloques de texto con información de formato
            blocks = page.get_text("dict")
            
            page_text_blocks = []
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    block_text = ""
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                        
                        if line_text.strip():
                            block_text += line_text + "\n"
                    
                    if block_text.strip():
                        page_text_blocks.append(block_text.strip())
            
            # Agregar los bloques de la página
            if page_text_blocks:
                text_blocks.extend(page_text_blocks)
        
        # Unir todos los bloques
        full_text = "\n\n".join(text_blocks)
        
        return full_text
    
    def _create_blocks_from_markdown(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Crea bloques estructurados a partir del texto markdown.
        
        Args:
            markdown_text: Texto en formato markdown
            
        Returns:
            List[Dict]: Lista de bloques estructurados
        """
        blocks = []
        
        if not markdown_text.strip():
            return blocks
        
        # Dividir por párrafos (doble salto de línea)
        paragraphs = re.split(r'\n\s*\n', markdown_text)
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Detectar tipo de bloque
            block_type = 'paragraph'
            if paragraph.startswith('#'):
                block_type = 'heading'
            elif len(paragraph.split('\n')) == 1 and len(paragraph) < 100:
                # Líneas cortas podrían ser títulos
                if any(keyword in paragraph.lower() for keyword in ['poema', 'capítulo', 'parte']):
                    block_type = 'heading'
                
            block = {
                'text': paragraph,
                'metadata': {
                    'type': block_type,
                    'order': i,
                    'page': 1,  # Se actualizará si es necesario
                    'bbox': [0, 0, 100, 100],  # Placeholder
                    'area': len(paragraph),
                    'char_count': len(paragraph),
                    'line_count': paragraph.count('\n') + 1,
                    'vertical_gap': 0
                }
            }
            blocks.append(block)
        
        return blocks

    def _create_metadata(self, doc, text: str) -> Dict[str, Any]:
        """
        Crea metadatos del documento PDF.
        
        Args:
            doc: Documento PDF abierto
            text: Texto extraído
            
        Returns:
            Dict: Metadatos del documento
        """
        # Obtener metadatos básicos
        metadata = doc.metadata if doc.metadata else {}
        
        # Calcular hash del archivo
        file_hash = _calculate_sha256(Path(self.file_path))
        
        # Crear metadatos completos
        result = {
            'file_path': self.file_path,
            'file_hash': file_hash,
            'page_count': len(doc),
            'char_count': len(text),
            'word_count': len(text.split()) if text else 0,
            'author': metadata.get('author', ''),
            'title': metadata.get('title', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', ''),
            'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
            'loader_version': 'PDFLoader_v7.4_OCR_Inteligente_Post_Segmentacion'
        }
        
        return result