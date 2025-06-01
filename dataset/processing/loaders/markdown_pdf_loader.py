#!/usr/bin/env python3
"""
Markdown PDF Loader - Conversión PDF → Markdown Estructurado

Utiliza pymupdf4llm para preservar la estructura jerárquica del PDF
manteniendo títulos, párrafos y formato original.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import fitz

logger = logging.getLogger(__name__)

class MarkdownPDFLoader:
    """Loader que convierte PDF a markdown estructurado preservando jerarquía"""
    
    def __init__(self, file_path: str, **kwargs):
        """
        Inicializar el loader con pymupdf4llm
        
        Args:
            file_path: Ruta al archivo PDF
            **kwargs: Argumentos adicionales (ignorados para compatibilidad)
        """
        self.file_path = file_path
        self.kwargs = kwargs
        self.logger = logging.getLogger(f"{__name__}.MarkdownPDFLoader")
        
    def load(self) -> Dict[str, Any]:
        """
        Cargar y procesar el PDF usando pymupdf4llm
        
        Returns:
            Dict con blocks, metadata y source_info
        """
        try:
            # Importar pymupdf4llm
            try:
                import pymupdf4llm
            except ImportError:
                self.logger.error("pymupdf4llm no disponible - instalar con: pip install pymupdf4llm")
                return self._fallback_extraction()
            
            # Verificar que el archivo existe
            if not Path(self.file_path).exists():
                raise FileNotFoundError(f"PDF no encontrado: {self.file_path}")
            
            self.logger.info(f"Iniciando conversión PDF → Markdown: {self.file_path}")
            
            # 1. CONVERSIÓN A MARKDOWN
            markdown_text = pymupdf4llm.to_markdown(self.file_path)
            
            if not markdown_text or not markdown_text.strip():
                self.logger.warning("Markdown vacío - usando fallback")
                return self._fallback_extraction()
            
            # 2. LIMPIAR TEXTO DUPLICADO
            cleaned_markdown = self._clean_duplicated_text(markdown_text)
            
            # 3. CONVERTIR MARKDOWN A BLOQUES ESTRUCTURADOS
            blocks = self._markdown_to_blocks(cleaned_markdown)
            
            # 4. METADATA
            metadata = self._extract_metadata(cleaned_markdown)
            
            # 5. SOURCE INFO
            source_info = {
                'extraction_method': 'pymupdf4llm_markdown',
                'converter_version': getattr(pymupdf4llm, '__version__', 'unknown'),
                'original_char_count': len(markdown_text),
                'cleaned_char_count': len(cleaned_markdown),
                'blocks_generated': len(blocks)
            }
            
            self.logger.info(f"✅ Conversión exitosa: {len(blocks)} bloques generados")
            
            return {
                'blocks': blocks,
                'metadata': metadata,
                'source_info': source_info,
                'raw_markdown': cleaned_markdown  # Para debug
            }
            
        except Exception as e:
            self.logger.error(f"Error en conversión markdown: {e}")
            return self._fallback_extraction()
    
    def _clean_duplicated_text(self, markdown_text: str) -> str:
        """
        Limpiar texto duplicado como 'VVeeiinnttee ppooeem'
        
        Args:
            markdown_text: Texto markdown original
            
        Returns:
            Texto markdown limpio
        """
        lines = markdown_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Detectar líneas con caracteres duplicados
            if self._has_duplicated_chars(line):
                # Intentar des-duplicar
                cleaned_line = self._deduplicate_line(line)
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
                else:
                    # Si no se puede limpiar, omitir la línea
                    self.logger.debug(f"Línea corrupta omitida: {line[:50]}")
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _has_duplicated_chars(self, line: str) -> bool:
        """
        Detectar si una línea tiene caracteres duplicados sospechosos
        
        Args:
            line: Línea de texto
            
        Returns:
            True si parece tener duplicación
        """
        if len(line) < 6:  # Líneas muy cortas no se evalúan
            return False
        
        # Contar secuencias de caracteres repetidos
        duplicate_count = 0
        for i in range(len(line) - 1):
            if line[i] == line[i + 1] and line[i].isalpha():
                duplicate_count += 1
        
        # Si más del 30% son duplicados consecutivos, es sospechoso
        return duplicate_count > len(line) * 0.3
    
    def _deduplicate_line(self, line: str) -> str:
        """
        Intentar des-duplicar una línea corrupta
        
        Args:
            line: Línea con duplicación
            
        Returns:
            Línea limpia o vacía si no se puede limpiar
        """
        try:
            # Método 1: Tomar cada segundo carácter si hay patrón AABBCC
            if len(line) % 2 == 0:
                deduplicated = ""
                for i in range(0, len(line), 2):
                    if i + 1 < len(line) and line[i] == line[i + 1]:
                        deduplicated += line[i]
                    else:
                        # No hay patrón claro, usar original
                        return line
                
                # Verificar que el resultado tiene sentido
                if len(deduplicated) > 3 and deduplicated.replace(' ', '').isalpha():
                    return deduplicated
            
            # Método 2: Remover duplicados consecutivos simples
            deduplicated = re.sub(r'(.)\1+', r'\1', line)
            if len(deduplicated) > len(line) * 0.4:  # Al menos 40% del original
                return deduplicated
            
            return ""  # No se pudo limpiar
            
        except Exception:
            return ""
    
    def _markdown_to_blocks(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Convertir markdown a bloques estructurados
        
        Args:
            markdown_text: Texto markdown limpio
            
        Returns:
            Lista de bloques estructurados
        """
        blocks = []
        lines = markdown_text.split('\n')
        
        current_section = None
        current_content = []
        block_id = 0
        
        for line_num, line in enumerate(lines):
            line = line.rstrip()
            
            # DETECTAR TÍTULOS PRINCIPALES
            if line.startswith('# '):
                # Guardar sección anterior
                if current_section and current_content:
                    blocks.append(self._create_block(
                        block_id, current_section, current_content, 'section'
                    ))
                    block_id += 1
                
                # Nueva sección principal
                current_section = line[2:].strip()
                current_content = []
                
                # Agregar título como bloque separado
                blocks.append(self._create_block(
                    block_id, line[2:].strip(), [], 'title', level=1
                ))
                block_id += 1
            
            # DETECTAR SUBTÍTULOS (POEMAS)
            elif line.startswith('## '):
                # Guardar contenido anterior
                if current_content:
                    blocks.append(self._create_block(
                        block_id, current_section or 'unknown', current_content, 'content'
                    ))
                    block_id += 1
                    current_content = []
                
                # Agregar subtítulo como bloque de poema
                poem_title = line[3:].strip()
                blocks.append(self._create_block(
                    block_id, poem_title, [], 'poem_title', level=2
                ))
                block_id += 1
            
            # DETECTAR OTROS PATRONES DE TÍTULOS
            elif self._is_poem_title(line):
                # Guardar contenido anterior
                if current_content:
                    blocks.append(self._create_block(
                        block_id, current_section or 'unknown', current_content, 'content'
                    ))
                    block_id += 1
                    current_content = []
                
                # Agregar como título de poema
                blocks.append(self._create_block(
                    block_id, line.strip(), [], 'poem_title'
                ))
                block_id += 1
            
            # CONTENIDO REGULAR
            elif line.strip():
                # MEJORA: Para poesía, crear bloques por verso individual
                if self._looks_like_verse_line(line):
                    # Guardar contenido anterior si existe
                    if current_content:
                        blocks.append(self._create_block(
                            block_id, current_section or 'unknown', current_content, 'content'
                        ))
                        block_id += 1
                        current_content = []
                    
                    # Crear bloque individual para el verso
                    blocks.append(self._create_block(
                        block_id, current_section or 'unknown', [line], 'verse'
                    ))
                    block_id += 1
                else:
                    current_content.append(line)
            
            # LÍNEA VACÍA
            else:
                # Si hay contenido acumulado y la siguiente línea parece título, guardar
                if current_content and line_num + 1 < len(lines):
                    next_line = lines[line_num + 1].strip()
                    if (next_line.startswith('#') or 
                        self._is_poem_title(next_line) or 
                        len(current_content) > 5):  # Bloque suficientemente largo
                        
                        blocks.append(self._create_block(
                            block_id, current_section or 'unknown', current_content, 'content'
                        ))
                        block_id += 1
                        current_content = []
        
        # Guardar último bloque
        if current_content:
            blocks.append(self._create_block(
                block_id, current_section or 'unknown', current_content, 'content'
            ))
        
        self.logger.info(f"Markdown convertido a {len(blocks)} bloques estructurados")
        return blocks
    
    def _is_poem_title(self, line: str) -> bool:
        """
        Detectar si una línea es un título de poema
        
        Args:
            line: Línea a evaluar
            
        Returns:
            True si parece título de poema
        """
        line = line.strip()
        
        if not line or len(line) > 100:  # Muy largo para ser título
            return False
        
        # Patrones específicos
        patterns = [
            r'^Poema\s+\d+',  # "Poema 1", "Poema 20"
            r'^[IVX]+\.?\s*$',  # Números romanos
            r'^\d+\.?\s*$',  # Números arábigos solos
            r'.*[Cc]anción.*',  # Contiene "canción"
            r'^[A-Z][A-Z\s]{10,50}$',  # Mayúsculas largas
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        
        # Heurística: línea corta, sin puntuación final, mayúsculas
        if (len(line) < 60 and 
            not line.endswith('.') and 
            not line.endswith(',') and
            (line.isupper() or line.istitle())):
            return True
        
        return False
    
    def _looks_like_verse_line(self, line: str) -> bool:
        """
        Detectar si una línea individual parece ser un verso
        MEJORADO: Mucho más permisivo para capturar todos los versos
        
        Args:
            line: Línea a evaluar
            
        Returns:
            True si parece un verso individual
        """
        line = line.strip()
        
        # Filtros básicos más permisivos
        if not line or len(line) < 5 or len(line) > 150:
            return False
        
        # Excluir patrones que NO son versos
        non_verse_patterns = [
            r'^Página\s+\d+',  # "Página N de M"
            r'^#',             # Títulos markdown
            r'^\d+\s*$',       # Solo números
            r'^[IVX]+\s*$',    # Solo números romanos
        ]
        
        for pattern in non_verse_patterns:
            if re.match(pattern, line):
                return False
        
        # CRITERIO PRINCIPAL: Si no es título y tiene longitud razonable, ES VERSO
        # En poesía, prácticamente cualquier línea no-título es un verso
        
        # Detectar títulos (que NO son versos)
        title_patterns = [
            r'^Poema\s+\d+',           # "Poema 13"
            r'^[A-Z][A-Z\s]{5,}$',     # Títulos en mayúsculas
            r'^".*"$',                 # Entre comillas
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, line):
                return False  # Es título, no verso
        
        # Si llegamos aquí y tiene contenido, muy probablemente es un verso
        # En poesía, cualquier línea con 5-150 caracteres que no sea título es verso
        return True
    
    def _create_block(self, block_id: int, section: str, content: List[str], 
                     block_type: str, level: int = 0) -> Dict[str, Any]:
        """
        Crear un bloque estructurado
        MEJORADO: Preserva saltos de línea poéticos
        
        Args:
            block_id: ID único del bloque
            section: Sección o título
            content: Lista de líneas de contenido
            block_type: Tipo del bloque
            level: Nivel jerárquico
            
        Returns:
            Diccionario del bloque
        """
        if content:
            # Si hay múltiples líneas, unirlas preservando estructura
            text_content = '\n'.join(content).strip()
            
            # MEJORA: Detectar y preservar estructura poética
            if block_type == 'content' and self._looks_like_poetry(text_content):
                text_content = self._preserve_verse_structure(text_content)
                
        else:
            text_content = section
        
        return {
            'id': block_id,
            'text': text_content,
            'metadata': {
                'type': block_type,
                'section': section,
                'level': level,
                'line_count': len(content),
                'char_count': len(text_content),
                'is_poem_content': block_type in ['poem_title', 'content'] and level > 0
            }
        }
    
    def _looks_like_poetry(self, text: str) -> bool:
        """
        Detectar si un bloque de texto parece ser poesía
        
        Args:
            text: Texto a analizar
            
        Returns:
            True si parece poesía
        """
        if not text or len(text) < 50:
            return False
        
        # Indicadores de poesía
        poetry_indicators = 0
        
        # 1. Líneas cortas (típico de versos)
        lines = text.split('\n')
        if lines:
            avg_line_length = sum(len(line.strip()) for line in lines) / len(lines)
            if avg_line_length < 60:  # Versos tienden a ser más cortos
                poetry_indicators += 1
        
        # 2. Patrones poéticos en el texto
        poetry_patterns = [
            r'\b(amor|corazón|alma|dolor|sueño|noche|día|luna|sol|mar|cielo)\b',
            r'\b(te amo|mi vida|querida|amada|amado)\b',
            r'\b(verso|poema|estrofa|rima)\b',
            r'[.!?]\s*[A-Z]',  # Múltiples oraciones (típico de poesía narrativa)
        ]
        
        for pattern in poetry_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                poetry_indicators += 1
        
        # 3. Estructura de oraciones poéticas (frases fragmentadas)
        sentences = re.split(r'[.!?]', text)
        short_sentences = sum(1 for s in sentences if len(s.strip()) < 40)
        if len(sentences) > 0 and short_sentences / len(sentences) > 0.3:
            poetry_indicators += 1
        
        return poetry_indicators >= 2
    
    def _preserve_verse_structure(self, text: str) -> str:
        """
        Detectar y preservar estructura de versos en texto corrido
        
        Args:
            text: Texto que puede tener versos unidos
            
        Returns:
            Texto con saltos de línea de versos preservados
        """
        # Si ya tiene saltos de línea frecuentes, probablemente está bien
        if text.count('\n') > len(text) / 100:  # ~1 salto cada 100 caracteres
            return text
        
        # PATRONES PARA DETECTAR FINALES DE VERSO
        verse_end_patterns = [
            r'([.!?])\s+([A-Z])',  # Fin de oración + Mayúscula
            r'([,;:])\s+([A-Z][a-z]+)',  # Puntuación + Palabra capitalizada
            r'(\w{1,3})\.\s+([A-Z])',  # Palabra corta + punto + Mayúscula
            r'([a-z]+[aeiou])\s+([A-Z][a-z]+)',  # Palabra terminada en vocal + Mayúscula
            r'(\w+[ado|ada|ido|ida])\s+([A-Z])',  # Participios + Mayúscula
            r'(\w+[mente])\s+([A-Z])',  # Adverbios + Mayúscula
        ]
        
        # Aplicar patrones para insertar saltos de línea
        result = text
        for pattern in verse_end_patterns:
            # Insertar salto de línea preservando la puntuación
            result = re.sub(pattern, r'\1\n\2', result)
        
        # LIMPIEZA: Evitar demasiados saltos seguidos
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # VERIFICACIÓN: Si se generaron muchos saltos, puede ser un poema
        original_lines = text.count('\n')
        new_lines = result.count('\n')
        
        if new_lines > original_lines + 3:  # Se añadieron varios saltos
            self.logger.debug(f"Estructura poética detectada: {original_lines} → {new_lines} líneas")
            return result
        else:
            # No se detectó estructura clara, mantener original
            return text
    
    def _extract_metadata(self, markdown_text: str) -> Dict[str, Any]:
        """
        Extraer metadata del markdown
        
        Args:
            markdown_text: Texto markdown
            
        Returns:
            Diccionario de metadata
        """
        lines = markdown_text.split('\n')
        
        # Contar elementos
        title_count = sum(1 for line in lines if line.startswith('# '))
        subtitle_count = sum(1 for line in lines if line.startswith('## '))
        poem_titles = sum(1 for line in lines if self._is_poem_title(line.strip()))
        
        # Detectar autor
        author = None
        for line in lines[:10]:  # Buscar en primeras líneas
            if any(name in line.lower() for name in ['neruda', 'autor', 'author']):
                author = line.strip()
                break
        
        return {
            'loader_type': 'markdown_pdf',
            'char_count': len(markdown_text),
            'line_count': len(lines),
            'title_count': title_count,
            'subtitle_count': subtitle_count,
            'detected_poems': max(subtitle_count, poem_titles),
            'author': author,
            'language': 'es'  # Español por defecto para poesía
        }
    
    def _fallback_extraction(self) -> Dict[str, Any]:
        """
        Método de respaldo usando PyMuPDF tradicional
        
        Returns:
            Resultado de extracción de respaldo
        """
        try:
            from .pdf_loader import PDFLoader
            
            self.logger.info("Usando PDFLoader tradicional como fallback")
            fallback_loader = PDFLoader(self.file_path)
            result = fallback_loader.load()
            
            # Marcar como fallback
            if 'source_info' in result:
                result['source_info']['extraction_method'] = 'fallback_pymupdf'
                result['source_info']['fallback_reason'] = 'pymupdf4llm_failed'
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fallback también falló: {e}")
            return {
                'blocks': [],
                'metadata': {'loader_type': 'failed', 'error': str(e)},
                'source_info': {'extraction_method': 'failed'}
            } 