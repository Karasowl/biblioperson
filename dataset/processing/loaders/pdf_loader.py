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
            
            # Extraer texto usando el método de markdown con páginas
            text_blocks_with_pages = self._extract_as_markdown(pdf_document)
            # Calcular total de caracteres
            self.total_chars_extracted = sum(len(text) for text, _ in text_blocks_with_pages)
            
            self.logger.warning(f"📝 EXTRACCIÓN TRADICIONAL: {self.total_chars_extracted} caracteres")
            
            # Crear bloques estructurados con información de página
            self.logger.warning("🔄 EXTRAYENDO BLOQUES DE MARKDOWN CON PÁGINAS")
            blocks = self._create_blocks_from_markdown(text_blocks_with_pages)
            self.logger.warning(f"📦 BLOQUES EXTRAÍDOS: {len(blocks)}")
            
            # Crear metadatos
            # Reconstruir texto completo para metadatos
            full_text = "\n\n".join(text for text, _ in text_blocks_with_pages)
            metadata = self._create_metadata(pdf_document, full_text)
            
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
        
        MODIFICADO: Criterios aún más restrictivos para evitar colgarse en OCR.
        Solo activa OCR en casos de fallo total de extracción.
        
        Args:
            blocks: Bloques extraídos tradicionalmente
            metadata: Metadatos del documento
            
        Returns:
            Tuple[bool, List[str]]: (necesita_ocr, razones)
        """
        reasons = []
        page_count = metadata.get('page_count', 1)
        
        # NUEVO: Deshabilitar OCR post-segmentación para documentos grandes (>10 páginas)
        # para evitar timeouts en el MVP
        if page_count > 10:
            self.logger.warning(f"🚫 OCR POST-SEGMENTACIÓN DESHABILITADO: Documento muy grande ({page_count} páginas)")
            return False, ["OCR deshabilitado para documentos >10 páginas (MVP)"]
        
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
            
            # Criterios EXTREMADAMENTE RESTRICTIVOS para activar OCR (solo fallas totales)
            
            # Criterio 1: SOLO documentos con 0 segmentos (falla total)
            if segment_count == 0:
                reasons.append(f"Extracción completamente fallida: 0 segmentos")
            
            # Criterio 2: SOLO documentos con ≤1 segmento muy pequeño (probable corrupción)
            elif segment_count <= 1:
                total_chars = sum(len(block.get('text', '')) for block in blocks)
                if total_chars < 100:  # Menos de 100 caracteres total
                    reasons.append(f"Extracción casi fallida: {segment_count} segmento, {total_chars} caracteres")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en evaluación post-segmentación: {e}")
            # NO activar OCR por errores de segmentación para evitar colgarse
            pass
        
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
        Determina si se necesita usar OCR basándose únicamente en fallas 
        objetivas de extracción, siguiendo la política ULTRA RESTRICTIVA
        documentada (memoria ID 280523630388657116):
            • Activar solo cuando la extracción normal produce 0-3 bloques
              útiles en total.
            • O cuando el análisis de corrupción detecta ≥70 % de caracteres
              ilegibles.
        Cualquier criterio secundario (permisos de PDF, tamaño del texto,
        etc.) ya no debe forzar OCR por sí mismo.
        """
        reasons: List[str] = []
        
        # Estadísticas de corrupción
        total_chars = 0
        corrupted_chars = 0
        for block in blocks:
            text = block.get("text", "")
            total_chars += len(text)
            corrupted_chars += sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\r\t")

        corruption_percentage = (corrupted_chars / total_chars * 100) if total_chars else 0
        self.corruption_percentage = corruption_percentage
        self.logger.warning(f"📊 Corrupción detectada: {corruption_percentage:.1f}%")
        
        # 1️⃣ Corrupción extrema >=70 %
        if corruption_percentage >= 70:
            reasons.append(f"Corrupción extrema de texto: {corruption_percentage:.1f}% ≥ 70%")
        
        # 2️⃣ Falla total/parcial: ≤3 bloques legibles
        if len(blocks) <= 3:
            reasons.append(f"Extracción tradicional produjo solo {len(blocks)} bloques (≤3)")
        
        # OCR solo si hay razones válidas
        needs_ocr = bool(reasons)
        if needs_ocr:
            self.logger.warning("🚨 PRE-SEGMENTACIÓN: OCR NECESARIO (criterios ultra restrictivos)")
            for r in reasons:
                self.logger.warning(f"   • {r}")
        else:
            self.logger.warning("✅ PRE-SEGMENTACIÓN: Texto suficientemente legible; se omite OCR")

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
        Ahora incluye información de página para cada bloque.
        
        Args:
            doc: Documento PDF abierto con fitz
            
        Returns:
            List[Tuple[str, int]]: Lista de tuplas (texto, página)
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
                        # Agregar tupla (texto, número_página)
                        page_text_blocks.append((block_text.strip(), page_num + 1))
            
            # Agregar los bloques de la página con su número
            text_blocks.extend(page_text_blocks)
        
        return text_blocks
    
    def _create_blocks_from_markdown(self, text_blocks_with_pages: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        """
        Crea bloques estructurados a partir de los bloques de texto con páginas.
        
        Args:
            text_blocks_with_pages: Lista de tuplas (texto, página)
            
        Returns:
            List[Dict]: Lista de bloques estructurados con página original
        """
        blocks = []
        block_order = 0
        
        for text, page_num in text_blocks_with_pages:
            if not text.strip():
                continue
            
            # Dividir cada bloque en párrafos si es necesario
            paragraphs = re.split(r'\n\s*\n', text)
            
            for paragraph in paragraphs:
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
                        'order': block_order,
                        'page': page_num,  # Página real del documento
                        'bbox': [0, 0, 100, 100],  # Placeholder
                        'area': len(paragraph),
                        'char_count': len(paragraph),
                        'line_count': paragraph.count('\n') + 1,
                        'vertical_gap': 0,
                        'extraction_method': 'traditional'
                    }
                }
                blocks.append(block)
                block_order += 1
        
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