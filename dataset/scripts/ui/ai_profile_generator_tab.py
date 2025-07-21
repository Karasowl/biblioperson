#!/usr/bin/env python3
"""
Pestaña de generación de perfiles asistida por IA para Biblioperson.

Este módulo contiene la interfaz para generar perfiles de procesamiento
utilizando modelos de lenguaje (LLM) basándose en documentos de ejemplo
y descripciones del usuario.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import uuid
import uuid

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QFileDialog,
    QCheckBox, QGroupBox, QFrame, QSizePolicy, QMessageBox, QProgressBar,
    QPlainTextEdit, QSlider, QSpinBox
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QObject, QTimer
from PySide6.QtGui import QFont, QIcon

# Importar el backend de procesamiento
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dataset.processing.profile_manager import ProfileManager

# Importar el sistema de configuración
from .config_manager import ConfigManager, ErrorLearningSystem
from .api_config_dialog import APIConfigDialog
from .intelligent_profile_generator import IntelligentProfileGenerator


class ProfileGenerationWorker(QObject):
    """Worker para generar perfiles usando análisis semántico avanzado del documento."""
    
    progress_update = Signal(str)  # mensaje de progreso
    generation_finished = Signal(str, str)  # yaml_content, profile_name
    generation_error = Signal(str)  # error_message
    
    def __init__(self, document_path: str, description: str, provider: str, 
                 model: str, api_key: str, segmenter_base: str, error_learning=None):
        super().__init__()
        self.document_path = document_path
        self.description = description
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.segmenter_base = segmenter_base
        self.error_learning = error_learning
    
    def generate_profile(self):
        """Genera el perfil usando análisis semántico avanzado."""
        try:
            # Paso 1: Cargar y analizar el documento
            self.progress_update.emit("Cargando documento...")
            document_content = self._load_document()
            
            # Paso 2: Crear embeddings del documento para análisis semántico
            self.progress_update.emit("Creando análisis semántico...")
            document_analysis = self._analyze_document_structure(document_content)
            
            # Paso 3: Generar perfil con IA usando el análisis
            self.progress_update.emit("Generando perfil con IA...")
            profile_yaml = self._generate_with_ai(document_analysis)
            
            # Paso 4: Validar y refinar el perfil
            self.progress_update.emit("Validando perfil generado...")
            validated_profile = self._validate_and_refine_profile(profile_yaml, document_analysis)
            
            # Generar nombre sugerido
            profile_name = self._generate_profile_name()
            
            # Registrar éxito en el sistema de aprendizaje
            if self.error_learning:
                try:
                    import yaml
                    profile_data = yaml.safe_load(validated_profile)
                    self.error_learning.log_success(
                        provider=self.provider,
                        model=self.model,
                        document_type=document_analysis.get('document_type', 'general'),
                        user_description=self.description,
                        generated_profile=profile_data
                    )
                except:
                    pass  # No fallar si hay error en el logging
            
            self.generation_finished.emit(validated_profile, profile_name)
            
        except Exception as e:
            error_message = f"Error en generación: {str(e)}"
            
            # Registrar error en el sistema de aprendizaje
            if self.error_learning:
                try:
                    self.error_learning.log_error(
                        provider=self.provider,
                        model=self.model,
                        document_type='general',
                        error_type='generation_error',
                        error_details=str(e),
                        user_description=self.description,
                        attempted_fix="Revisar conexión y clave API"
                    )
                except:
                    pass  # No fallar si hay error en el logging
            
            self.generation_error.emit(error_message)
    
    def _load_document(self) -> str:
        """Carga el contenido del documento."""
        from pathlib import Path
        
        file_path = Path(self.document_path)
        
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.suffix.lower() == '.pdf':
            # Usar el loader de PDF del proyecto
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
            from dataset.processing.loaders.pdf_loader import PDFLoader
            
            loader = PDFLoader(str(file_path))
            result = loader.load()
            
            # Extraer texto de los blocks
            blocks = result.get('blocks', [])
            content = '\n\n'.join(block.get('text', '') for block in blocks if block.get('text'))
            return content
        else:
            # Para otros formatos, intentar leer como texto
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analiza la estructura del documento para entender patrones."""
        import re
        
        analysis = {
            'total_length': len(content),
            'line_count': len(content.split('\n')),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'heading_patterns': [],
            'structural_patterns': [],
            'content_samples': [],
            'language_style': 'formal',
            'document_type': 'general',
            'numeric_patterns': [],
            'formatting_patterns': []
        }
        
        lines = content.split('\n')
        
        # Detectar patrones numéricos universales
        numeric_patterns = [
            r'\b\d+:\d+\b',          # Formato capítulo:verso (1:1, 12:15)
            r'\b\d+\.\d+\b',         # Formato decimal (1.1, 2.5)
            r'^\d+\s+[A-Z]',         # Número seguido de texto (versículo/item)
            r'^\d+\.\s+',            # Numeración con punto (1. Item)
            r'^\d+\)\s+',            # Numeración con paréntesis (1) Item)
            r'^[IVX]+\.\s+',         # Numeración romana (I. II. III.)
            r'^[a-z]\)\s+',          # Letras minúsculas (a) b) c))
            r'^[A-Z]\)\s+',          # Letras mayúsculas (A) B) C))
        ]
        
        for pattern in numeric_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                analysis['numeric_patterns'].append({
                    'pattern': pattern,
                    'examples': matches[:10],
                    'count': len(matches)
                })
        
        # Detectar patrones de formato universales
        formatting_patterns = [
            r'^#{1,6}\s+',           # Encabezados Markdown
            r'^\*{1,3}\s+',          # Asteriscos para listas/énfasis
            r'^-\s+',                # Guiones para listas
            r'^\+\s+',               # Signos más para listas
            r'^[A-Z][A-Z\s]{3,}$',   # TEXTO EN MAYÚSCULAS (títulos)
            r'^\s*\*\*.*\*\*\s*$',   # Texto en negrita markdown
            r'^\s*_.*_\s*$',         # Texto en cursiva markdown
            r'^\s*```',              # Bloques de código
            r'^\s*>',                # Citas/blockquotes
        ]
        
        for pattern in formatting_patterns:
            matches = [line for line in lines if re.match(pattern, line, re.MULTILINE)]
            if matches:
                analysis['formatting_patterns'].append({
                    'pattern': pattern,
                    'examples': matches[:5],
                    'count': len(matches)
                })
        
        # Detectar patrones de encabezados universales
        heading_patterns = [
            r'^#{1,6}\s+(.+)$',      # Encabezados Markdown
            r'^[A-Z][A-Z\s]{3,}$',   # TÍTULOS EN MAYÚSCULAS
            r'^\d+\.\s+(.+)$',       # Secciones numeradas (1. Título)
            r'^\d+\.\d+\s+(.+)$',    # Subsecciones (1.1 Título)
            r'^[IVX]+\.\s+(.+)$',    # Numeración romana (I. Título)
            r'^Capítulo\s+\d+',      # Patrones de capítulo
            r'^CAPÍTULO\s+[IVX]+',   # Capítulos en romano
            r'^[A-Z][a-záéíóúñ\s]+\d+$',  # Texto seguido de número
            r'^\d+\s+[A-Z][a-záéíóúñ]',   # Número seguido de texto
        ]
        
        for pattern in heading_patterns:
            matches = [line for line in lines if re.match(pattern, line.strip(), re.MULTILINE | re.IGNORECASE)]
            if matches:
                analysis['heading_patterns'].append({
                    'pattern': pattern,
                    'examples': matches[:5],  # Primeros 5 ejemplos
                    'count': len(matches)
                })
        
        # Detectar patrones estructurales generales
        if re.search(r'\b(diálogo|dijo|preguntó|respondió)\b', content, re.IGNORECASE):
            analysis['structural_patterns'].append('dialogue')
        
        if re.search(r'\b(verso|estrofa|rima)\b', content, re.IGNORECASE):
            analysis['structural_patterns'].append('poetry')
        
        if re.search(r'\b(figura|tabla|gráfico|imagen)\b', content, re.IGNORECASE):
            analysis['structural_patterns'].append('academic')
        
        # Obtener muestras de contenido representativas
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            # Tomar muestras del inicio, medio y final
            sample_indices = [0, len(paragraphs)//2, -1] if len(paragraphs) > 2 else [0]
            analysis['content_samples'] = [paragraphs[i][:300] + "..." if len(paragraphs[i]) > 300 else paragraphs[i] 
                                         for i in sample_indices if i < len(paragraphs)]
        
        return analysis
    
    def _generate_with_ai(self, analysis: Dict[str, Any]) -> str:
        """Genera el perfil YAML usando IA con el análisis del documento."""
        
        # Crear prompt especializado con el análisis
        prompt = self._create_specialized_prompt(analysis)
        
        # Llamar a la API según el proveedor
        if self.provider == "OpenAI":
            return self._call_openai_api(prompt)
        elif self.provider == "Anthropic":
            return self._call_anthropic_api(prompt)
        elif self.provider == "Google Gemini":
            return self._call_gemini_api(prompt)

        else:
            raise ValueError(f"Proveedor no soportado: {self.provider}")
    
    def _create_specialized_prompt(self, analysis: Dict[str, Any]) -> str:
        """Crea un prompt especializado basado en el análisis del documento."""
        
        prompt = f"""Eres un experto en procesamiento de documentos y segmentación de texto para el sistema Biblioperson.

CONTEXTO DEL SISTEMA BIBLIOPERSON:
- Sistema de procesamiento de datasets literarios
- Usa ProfileManager para gestionar perfiles de segmentación
- Soporta segmentadores: heading, paragraph, sentence, verse, custom
- Los perfiles se almacenan en dataset/config/profiles/
- Cada perfil define patrones regex, umbrales y filtros específicos
- Los segmentadores procesan documentos en bloques estructurados

ANÁLISIS DEL DOCUMENTO:
- Longitud total: {analysis['total_length']} caracteres
- Líneas: {analysis['line_count']}
- Párrafos: {analysis['paragraph_count']}
- Patrones estructurales detectados: {', '.join(analysis['structural_patterns']) if analysis['structural_patterns'] else 'Ninguno específico'}

PATRONES NUMÉRICOS Y DE FORMATO ENCONTRADOS:
"""
        
        # Agregar contexto de aprendizaje si está disponible
        if self.error_learning:
            learning_context = self.error_learning.get_learning_context(
                self.provider, 
                analysis.get('document_type', 'general')
            )
            if learning_context:
                prompt += f"\n\nCONOCIMIENTO PREVIO (ERRORES Y ÉXITOS):\n{learning_context}\n"
        
        # Mostrar patrones numéricos encontrados
        for numeric_pattern in analysis['numeric_patterns']:
            prompt += f"- Patrón numérico: {numeric_pattern['pattern']} (encontrado {numeric_pattern['count']} veces)\n"
            prompt += f"  Ejemplos: {', '.join(str(ex) for ex in numeric_pattern['examples'][:5])}\n"
        
        # Mostrar patrones de formato encontrados
        for format_pattern in analysis['formatting_patterns']:
            prompt += f"- Patrón de formato: {format_pattern['pattern']} (encontrado {format_pattern['count']} veces)\n"
            prompt += f"  Ejemplos: {', '.join(format_pattern['examples'][:3])}\n"
        
        prompt += "\nPATRONES DE ENCABEZADOS ENCONTRADOS:\n"
        for pattern_info in analysis['heading_patterns']:
            prompt += f"- Patrón: {pattern_info['pattern']} (encontrado {pattern_info['count']} veces)\n"
            prompt += f"  Ejemplos: {', '.join(pattern_info['examples'][:3])}\n"
        
        prompt += f"""
MUESTRAS DE CONTENIDO REAL:
"""
        for i, sample in enumerate(analysis['content_samples'], 1):
            prompt += f"Muestra {i}: {sample}\n\n"
        
        prompt += f"""
DESCRIPCIÓN DEL USUARIO:
{self.description}

SEGMENTADOR BASE SUGERIDO: {self.segmenter_base}

EJEMPLOS DE PERFILES FUNCIONALES:

EJEMPLO 1 - Estructura de Libros:
```yaml
name: book_structure
description: "Detecta estructura jerárquica en libros y documentos SOLO con señales estructurales"
segmenter: heading
file_types: [".txt", ".md", ".docx", ".pdf"]
thresholds:
  max_heading_length: 200
  max_section_depth: 3
  min_heading_content: 1
heading_patterns:
  - "^#{1,6} "                 # Encabezados Markdown
  - "^\\\\d+\\\\.\\\\d*\\\\s+"         # Numeración tipo "1.2 Título"
  - "^[A-Z][A-ZÁ-Ú ]{{3,}}$"     # TÍTULO EN MAYÚSCULAS
post_processor: text_normalizer
metadata_map:
  titulo: title
  nivel: level
  contenido: content
exporter: ndjson
```

EJEMPLO 2 - Poemas y Versos:
```yaml
name: poem_or_lyrics
description: "Detecta poemas y canciones en archivos de texto"
segmenter: verse
file_types: [".txt", ".md", ".docx", ".pdf"]
thresholds:
  max_verse_length: 120
  max_title_length: 80
  min_consecutive_verses: 3
  min_stanza_verses: 2
title_patterns:
  - "^# "                  # Markdown H1
  - "^\\\\* "                # Asterisco inicial
  - "^[A-Z ]{{4,}}:$"        # TÍTULO: (mayúsculas + dos puntos)
post_processor: text_normalizer
metadata_map:
  titulo: title
  versos: verses_count
  estrofas: stanzas_count
exporter: ndjson
```



TAREA ESPECÍFICA:
Analiza el contenido real proporcionado y genera un perfil YAML completo y funcional que:

1. **DETECTE PATRONES REALES**: Basado en las muestras de contenido y patrones encontrados, no en suposiciones
2. **USE SEGMENTADOR APROPIADO**: 
   - "verse" para contenido con líneas cortas, versos, elementos numerados
   - "heading" para documentos con estructura jerárquica clara
   - "paragraph" para texto corrido sin estructura específica
   - "sentence" para análisis granular de oraciones
3. **PATRONES ESPECÍFICOS**: Regex que coincidan exactamente con los patrones detectados en el documento
4. **UMBRALES REALISTAS**: Basados en el tamaño real de los segmentos observados en las muestras
5. **CONFIGURACIÓN COMPLETA**: Incluye file_types, post_processor, metadata_map, exporter
6. **ADAPTABILIDAD**: El perfil debe funcionar para documentos similares del mismo tipo

ESTRUCTURA YAML REQUERIDA (usa esta estructura exacta):
```yaml
name: "nombre_descriptivo_sin_espacios"
description: "Descripción específica de qué detecta este perfil"
segmenter: "tipo_segmentador"  # verse, heading, paragraph, sentence
file_types: [".txt", ".md", ".docx", ".pdf"]
thresholds:
  # Umbrales específicos según el segmentador elegido
  # Para heading: max_heading_length, max_section_depth, etc.
  # Para verse: max_verse_length, min_consecutive_verses, etc.
  # Para paragraph: min_length, max_length, etc.
patterns_o_heading_patterns_o_title_patterns:  # Según el segmentador
  - "regex_patron_1"
  - "regex_patron_2"
  # Patrones específicos basados en el contenido real
post_processor: text_normalizer
post_processor_config:
  min_length: numero_minimo
metadata_map:
  campo_interno: campo_final
  # Mapeo específico según el tipo de contenido
exporter: ndjson
```

IMPORTANTE: 
- Analiza las muestras de contenido para detectar patrones reales del documento
- Usa los patrones numéricos y de formato detectados para crear regex específicos
- Si hay numeración frecuente (1:1, 1., a), etc.) incorpora esos patrones
- Si hay encabezados markdown (#, ##) o títulos en mayúsculas, úsalos
- Si hay líneas cortas y numeradas, considera segmentador "verse"
- Si hay estructura jerárquica clara, usa segmentador "heading"
- Si es texto corrido sin estructura, usa segmentador "paragraph"
- Los umbrales deben reflejar el tamaño real de los segmentos en las muestras
- El perfil debe ser genérico para procesar documentos similares del mismo tipo

Responde SOLO con el YAML válido y completo, sin explicaciones adicionales."""
        
        return prompt
    
    def _call_openai_api(self, prompt: str) -> str:
        """Llama a la API de OpenAI."""
        import openai
        
        client = openai.OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Eres un experto en análisis de documentos y generación de perfiles de segmentación."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    
    def _call_anthropic_api(self, prompt: str) -> str:
        """Llama a la API de Anthropic."""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        response = client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Llama a la API de Google Gemini."""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000
            )
        )
        
        return response.text.strip()
    

    
    def _validate_and_refine_profile(self, yaml_content: str, analysis: Dict[str, Any] = None) -> str:
        """Valida y refina el perfil YAML generado."""
        import yaml
        
        try:
            # Intentar parsear el YAML
            profile_data = yaml.safe_load(yaml_content)
            
            # Verificar que el resultado sea un diccionario válido
            if not isinstance(profile_data, dict):
                raise yaml.YAMLError("El contenido no es un diccionario YAML válido")
            
            # Validaciones básicas
            required_fields = ['name', 'description', 'segmenter']
            for field in required_fields:
                if field not in profile_data:
                    if field == 'segmenter':
                        profile_data[field] = 'paragraph'  # Segmentador por defecto válido
                    else:
                        profile_data[field] = f"default_{field}"
            
            # Validar que el segmentador sea válido
            valid_segmenters = ['heading', 'paragraph', 'sentence', 'verse', 'custom']
            if profile_data.get('segmenter') not in valid_segmenters:
                profile_data['segmenter'] = 'paragraph'  # Fallback a segmentador válido
            
            # Asegurar que los patrones sean válidos
            if 'patterns' in profile_data and isinstance(profile_data['patterns'], list):
                # Validar que los regex sean válidos
                import re
                valid_patterns = []
                for pattern in profile_data['patterns']:
                    try:
                        re.compile(pattern)
                        valid_patterns.append(pattern)
                    except re.error:
                        # Patrón inválido, omitir
                        pass
                profile_data['patterns'] = valid_patterns
            
            # Regenerar YAML limpio
            return yaml.dump(profile_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
        except yaml.YAMLError:
            # Si el YAML es inválido, crear uno funcional basado en el segmentador
            segmenter = getattr(self, 'segmenter_base', 'paragraph')
            if segmenter == 'Automático' or not segmenter:
                segmenter = 'paragraph'
            else:
                segmenter = segmenter.lower()
            
            # Crear fallback basado en el análisis del documento (si está disponible)
            detected_patterns = []
            if analysis:
                detected_patterns = analysis.get('numeric_patterns', []) + analysis.get('formatting_patterns', [])
            
            if segmenter == 'heading':
                # Usar patrones detectados para encabezados
                heading_patterns = ['^#{1,6} ', '^\\d+\\.\\s+', '^[A-Z][A-ZÁ-Ú ]{3,}$']
                
                # Agregar patrones específicos encontrados en el documento
                if analysis:
                    for pattern_info in analysis.get('heading_patterns', []):
                        if pattern_info['count'] > 2:  # Solo patrones frecuentes
                            heading_patterns.append(pattern_info['pattern'])
                
                fallback_profile = {
                    'name': 'perfil_generado_heading',
                    'description': 'Perfil para detectar encabezados y estructura de documentos',
                    'segmenter': 'heading',
                    'file_types': ['.txt', '.md', '.docx', '.pdf'],
                    'thresholds': {
                        'max_heading_length': 200,
                        'max_section_depth': 3,
                        'min_heading_content': 1
                    },
                    'heading_patterns': list(set(heading_patterns)),  # Remover duplicados
                    'post_processor': 'text_normalizer',
                    'metadata_map': {
                        'titulo': 'title',
                        'nivel': 'level',
                        'contenido': 'content'
                    },
                    'exporter': 'ndjson'
                }
            elif segmenter == 'verse':
                # Detectar si hay patrones de versos cortos o numeración
                verse_length = 120  # Default
                title_patterns = ['^# ', '^\\* ', '^[A-Z ]{4,}:$']
                
                # Ajustar según patrones encontrados
                for pattern_info in detected_patterns:
                    if 'numeric' in str(pattern_info.get('pattern', '')):
                        title_patterns.append(pattern_info['pattern'])
                
                fallback_profile = {
                    'name': 'perfil_generado_verse',
                    'description': 'Perfil para detectar versos, estrofas y contenido estructurado en líneas cortas',
                    'segmenter': 'verse',
                    'file_types': ['.txt', '.md', '.docx', '.pdf'],
                    'thresholds': {
                        'max_verse_length': verse_length,
                        'max_title_length': 80,
                        'min_consecutive_verses': 2,
                        'min_stanza_verses': 1
                    },
                    'title_patterns': list(set(title_patterns)),
                    'post_processor': 'text_normalizer',
                    'metadata_map': {
                        'titulo': 'title',
                        'versos': 'verses_count',
                        'estrofas': 'stanzas_count',
                        'contenido': 'content'
                    },
                    'exporter': 'ndjson'
                }
            else:  # paragraph o sentence
                fallback_profile = {
                    'name': 'perfil_generado_paragraph',
                    'description': 'Perfil para segmentación por párrafos',
                    'segmenter': segmenter,
                    'file_types': ['.txt', '.md', '.docx', '.pdf'],
                    'thresholds': {
                        'min_length': 50,
                        'max_length': 2000
                    },
                    'post_processor': 'text_normalizer',
                    'post_processor_config': {
                        'min_length': 30
                    },
                    'metadata_map': {
                        'contenido': 'content',
                        'longitud': 'length'
                    },
                    'exporter': 'ndjson'
                }
            
            return yaml.dump(fallback_profile, default_flow_style=False, allow_unicode=True)
    
    def _generate_profile_name(self) -> str:
        """Genera un nombre sugerido para el perfil."""
        from datetime import datetime
        
        # Extraer palabras clave de la descripción
        description_words = self.description.lower().split()
        keywords = [word for word in description_words if len(word) > 3 and word.isalpha()]
        
        if keywords:
            base_name = "_".join(keywords[:3])  # Primeras 3 palabras clave
        else:
            base_name = "perfil_ia"
        
        # Agregar timestamp para unicidad
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        return f"{base_name}_{timestamp}"


class ModelLoaderWorker(QObject):
    """Worker para cargar modelos de APIs de forma asíncrona."""
    
    models_loaded = Signal(str, list)  # provider, models
    loading_error = Signal(str, str)   # provider, error_message
    
    def __init__(self):
        super().__init__()
        
    def load_openai_models(self, api_key: str = None):
        """Carga modelos de OpenAI desde la API real."""
        try:
            if not api_key:
                raise ValueError("Se requiere clave API para OpenAI")
            
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # Obtener modelos reales de la API
            response = client.models.list()
            all_models = [model.id for model in response.data]
            
            # Filtrar solo modelos de chat/completions relevantes (sin visión, audio, etc.)
            chat_models = [
                model for model in all_models 
                if any(prefix in model for prefix in ['gpt-4', 'gpt-3.5', 'o1'])
                and not any(suffix in model for suffix in [
                    'instruct', 'edit', 'search', 'similarity', 'vision', 'audio', 
                    'whisper', 'tts', 'dall-e', 'embedding', 'moderation'
                ])
            ]
            
            # Ordenar por relevancia (más nuevos primero)
            priority_order = ['o1', 'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5']
            def sort_key(model):
                for i, prefix in enumerate(priority_order):
                    if model.startswith(prefix):
                        return (i, model)
                return (len(priority_order), model)
            
            chat_models.sort(key=sort_key)
            
            if not chat_models:
                # Fallback si no se encuentran modelos
                chat_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            
            self.models_loaded.emit("OpenAI", chat_models)
            
        except Exception as e:
            self.loading_error.emit("OpenAI", f"Error conectando con OpenAI: {str(e)}")
    
    def load_anthropic_models(self, api_key: str = None):
        """Carga modelos de Anthropic con estrategia mejorada de descubrimiento."""
        try:
            if not api_key:
                raise ValueError("Se requiere clave API para Anthropic")
            
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            # Estrategia de descubrimiento mejorada
            available_models = []
            
            # Paso 1: Modelos conocidos estables (siempre verificar primero)
            known_stable_models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022", 
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ]
            
            for model in known_stable_models:
                try:
                    response = client.messages.create(
                        model=model,
                        max_tokens=1,
                        messages=[{"role": "user", "content": "test"}]
                    )
                    available_models.append(model)
                except anthropic.NotFoundError:
                    continue
                except anthropic.AuthenticationError:
                    raise ValueError("Clave API inválida")
                except anthropic.RateLimitError:
                    available_models.append(model)  # Asumir que existe si hay rate limit
                except Exception:
                    continue
            
            # Paso 2: Buscar modelos más recientes con patrones específicos
            import datetime
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            
            # Patrones de modelos más probables (fechas recientes)
            recent_model_patterns = []
            
            # Generar fechas de los últimos 6 meses hacia adelante
            for month_offset in range(-3, 6):  # 3 meses atrás, 6 meses adelante
                target_month = current_month + month_offset
                target_year = current_year
                
                # Ajustar año si el mes se sale del rango
                while target_month > 12:
                    target_month -= 12
                    target_year += 1
                while target_month < 1:
                    target_month += 12
                    target_year -= 1
                
                # Solo buscar en 2024-2025
                if target_year < 2024 or target_year > 2025:
                    continue
                
                # Días típicos de lanzamiento de Anthropic
                for day in [1, 15, 22, 29]:
                    if day > 28 and target_month == 2:  # Febrero
                        continue
                    if day > 30 and target_month in [4, 6, 9, 11]:  # Meses de 30 días
                        continue
                        
                    date_str = f"{target_year}{target_month:02d}{day:02d}"
                    
                    # Modelos más probables primero
                    recent_model_patterns.extend([
                        f"claude-3-5-sonnet-{date_str}",
                        f"claude-3-5-haiku-{date_str}",
                        f"claude-3-opus-{date_str}",
                        f"claude-3-haiku-{date_str}"
                    ])
            
            # Ordenar por fecha (más recientes primero)
            recent_model_patterns.sort(reverse=True)
            
            # Verificar modelos recientes (limitado para evitar rate limits)
            max_recent_checks = 15
            checked = 0
            
            for model_pattern in recent_model_patterns:
                if checked >= max_recent_checks:
                    break
                    
                if model_pattern not in available_models:
                    try:
                        response = client.messages.create(
                            model=model_pattern,
                            max_tokens=1,
                            messages=[{"role": "user", "content": "test"}]
                        )
                        available_models.append(model_pattern)
                        checked += 1
                    except anthropic.NotFoundError:
                        checked += 1
                        continue
                    except anthropic.AuthenticationError:
                        raise ValueError("Clave API inválida")
                    except anthropic.RateLimitError:
                        available_models.append(model_pattern)
                        checked += 1
                    except Exception:
                        checked += 1
                        continue
            
            # Paso 3: Verificar aliases y modelos experimentales
            experimental_models = [
                "claude-3-5-sonnet-latest",
                "claude-3-5-haiku-latest", 
                "claude-3-opus-latest",
                "claude-3-haiku-latest",
                "claude-3-5-sonnet-20250115",  # Fechas específicas recientes
                "claude-3-5-sonnet-20250101",
                "claude-3-5-haiku-20250115",
                "claude-3-5-haiku-20250101"
            ]
            
            for model in experimental_models:
                if model not in available_models:
                    try:
                        response = client.messages.create(
                            model=model,
                            max_tokens=1,
                            messages=[{"role": "user", "content": "test"}]
                        )
                        available_models.append(model)
                    except:
                        continue
            
            # Paso 4: Asegurar que tenemos al menos los modelos básicos
            if not available_models:
                # Fallback final - agregar modelo conocido
                available_models = ["claude-3-5-sonnet-20241022"]
            
            # Paso 5: Ordenar modelos por relevancia y fecha
            def model_sort_key(model):
                # Extraer fecha del modelo para ordenar por recencia
                import re
                date_match = re.search(r'(\d{8})', model)
                date_score = 0
                if date_match:
                    try:
                        date_score = int(date_match.group(1))
                    except:
                        date_score = 0
                
                # Prioridad por tipo de modelo
                if "claude-3-5-sonnet" in model:
                    return (0, -date_score, model)  # Sonnet 3.5 primero, más reciente primero
                elif "claude-3-5-haiku" in model:
                    return (1, -date_score, model)  # Haiku 3.5 segundo
                elif "claude-3-opus" in model:
                    return (2, -date_score, model)  # Opus 3 tercero
                elif "claude-3-haiku" in model:
                    return (3, -date_score, model)  # Haiku 3 cuarto
                else:
                    return (10, -date_score, model)  # Otros al final
            
            available_models.sort(key=model_sort_key)
            
            # Remover duplicados manteniendo orden
            seen = set()
            unique_models = []
            for model in available_models:
                if model not in seen:
                    seen.add(model)
                    unique_models.append(model)
            
            # Limitar a máximo 10 modelos para no saturar la interfaz
            if len(unique_models) > 10:
                unique_models = unique_models[:10]
            
            self.models_loaded.emit("Anthropic", unique_models)
            
        except Exception as e:
            self.loading_error.emit("Anthropic", f"Error conectando con Anthropic: {str(e)}")
    
    def load_gemini_models(self, api_key: str = None):
        """Carga modelos de Google Gemini desde la API real."""
        try:
            if not api_key:
                raise ValueError("Se requiere clave API para Google Gemini")
            
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Obtener modelos reales de la API
            models_response = genai.list_models()
            all_models = []
            
            for model in models_response:
                model_name = model.name.replace('models/', '')
                # Filtrar solo modelos generativos (no embedding, etc.)
                # También excluir modelos de visión si solo queremos texto
                if ('generateContent' in model.supported_generation_methods and 
                    not any(exclude in model_name.lower() for exclude in ['vision', 'embedding', 'aqa'])):
                    all_models.append(model_name)
            
            # Ordenar por relevancia (más nuevos primero)
            priority_order = [
                'gemini-2.0-flash-exp',
                'gemini-2.0', 
                'gemini-1.5-pro', 
                'gemini-1.5-flash', 
                'gemini-1.0-pro'
            ]
            
            def sort_key(model):
                for i, prefix in enumerate(priority_order):
                    if model.startswith(prefix):
                        return (i, model)
                return (len(priority_order), model)
            
            all_models.sort(key=sort_key)
            
            # Filtrar modelos duplicados manteniendo el orden
            seen = set()
            unique_models = []
            for model in all_models:
                if model not in seen:
                    seen.add(model)
                    unique_models.append(model)
            
            if not unique_models:
                # Fallback si no se encuentran modelos
                unique_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
            
            self.models_loaded.emit("Google Gemini", unique_models)
            
        except Exception as e:
            self.loading_error.emit("Google Gemini", f"Error conectando con Google Gemini: {str(e)}")
    



class AIProfileGeneratorTab(QWidget):
    """
    Pestaña para generación de perfiles asistida por IA.
    
    Esta clase implementa la interfaz que permite a los usuarios:
    - Cargar documentos de ejemplo
    - Describir el tipo de segmentación deseada
    - Configurar parámetros de IA
    - Generar perfiles YAML automáticamente
    - Editar y guardar perfiles generados
    """
    
    # Señales para comunicación con la ventana principal
    profile_generated = Signal(dict)  # Perfil generado por IA
    profile_saved = Signal(str)       # Nombre del perfil guardado
    
    def __init__(self, profile_manager: ProfileManager):
        super().__init__()
        self.profile_manager = profile_manager
        
        # Variables de estado
        self.sample_document_path: Optional[str] = None
        self.generated_profile: Optional[Dict[str, Any]] = None
        
        # Sistema de configuración y aprendizaje
        self.config_manager = ConfigManager()
        self.error_learning = ErrorLearningSystem(self.config_manager)
        
        # Cache de modelos por proveedor
        self.provider_models: Dict[str, List[str]] = {}
        
        # Worker para cargar modelos
        self.model_loader = ModelLoaderWorker()
        self.model_loader_thread = QThread()
        self.model_loader.moveToThread(self.model_loader_thread)
        self.model_loader_thread.start()
        
        # Configurar la interfaz
        self._setup_ui()
        self._setup_connections()
        self._load_initial_data()
    
    def _setup_ui(self):
        """Configura todos los elementos de la interfaz de usuario."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Título de la pestaña
        title_label = QLabel("Generador de Perfiles Asistido por IA")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; margin: 10px 0; background-color: rgba(52, 73, 94, 0.8); padding: 8px; border-radius: 5px;")
        main_layout.addWidget(title_label)
        
        # Splitter principal (horizontal)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel de configuración (izquierda)
        config_panel = self._create_config_panel()
        main_splitter.addWidget(config_panel)
        
        # Panel de resultado y edición (derecha)
        result_panel = self._create_result_panel()
        main_splitter.addWidget(result_panel)
        
        # Configurar proporciones del splitter
        main_splitter.setSizes([400, 600])  # 40% config, 60% resultado
        main_splitter.setStretchFactor(0, 0)  # Panel config no se estira
        main_splitter.setStretchFactor(1, 1)  # Panel resultado se estira
    
    def _create_config_panel(self) -> QWidget:
        """Crea el panel de configuración para la generación de perfiles."""
        panel = QWidget()
        panel.setMaximumWidth(480)
        panel.setMinimumWidth(380)
        
        # Crear un scroll area para evitar superposición
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(600)  # Altura mínima para el scroll area
        
        # Widget contenedor dentro del scroll
        content_widget = QWidget()
        content_widget.setMinimumHeight(800)  # Altura mínima del contenido para activar scroll
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)  # Espaciado reducido
        layout.setContentsMargins(8, 8, 8, 8)
        
        # === Sección 1: Documento de Ejemplo ===
        doc_group = QGroupBox("Documento de Ejemplo")
        doc_group.setMaximumHeight(110)  # Altura máxima más compacta
        doc_layout = QVBoxLayout(doc_group)
        doc_layout.setSpacing(6)
        doc_layout.setContentsMargins(8, 12, 8, 8)
        
        # Botón para cargar documento
        self.load_doc_btn = QPushButton("📁 Cargar Documento de Ejemplo")
        self.load_doc_btn.setFixedHeight(32)  # Altura más compacta
        self.load_doc_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        
        # Campo para mostrar archivo seleccionado
        self.doc_path_edit = QLineEdit()
        self.doc_path_edit.setPlaceholderText("Ningún documento seleccionado...")
        self.doc_path_edit.setReadOnly(True)
        self.doc_path_edit.setFixedHeight(22)
        
        doc_layout.addWidget(self.load_doc_btn)
        doc_layout.addSpacing(3)
        doc_layout.addWidget(QLabel("Archivo seleccionado:"))
        doc_layout.addWidget(self.doc_path_edit)
        layout.addWidget(doc_group)
        
        # === Sección 2: Descripción del Usuario ===
        desc_group = QGroupBox("Descripción del Perfil Deseado")
        desc_group.setMaximumHeight(160)  # Altura máxima más compacta
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.setSpacing(6)
        desc_layout.setContentsMargins(8, 12, 8, 8)
        
        # Área de texto para descripción
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Describe cómo quieres que se segmente este documento...\n\n"
            "Ejemplos:\n"
            "• 'Extraer párrafos que contengan diálogos'\n"
            "• 'Separar por capítulos y secciones'\n"
            "• 'Identificar versos de poemas'\n"
            "• 'Segmentar por temas o conceptos'"
        )
        self.description_edit.setMaximumHeight(120)  # Altura máxima más compacta
        
        desc_layout.addWidget(self.description_edit)
        layout.addWidget(desc_group)
        
        # === Sección 3: Configuración de IA ===
        ai_group = QGroupBox("Configuración de IA")
        ai_group.setMaximumHeight(140)  # Altura máxima más compacta
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setSpacing(6)
        ai_layout.setContentsMargins(8, 12, 8, 8)
        
        # Selector de proveedor de API
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Proveedor:"))
        self.provider_combo = QComboBox()
        self.provider_combo.setFixedHeight(22)
        provider_layout.addWidget(self.provider_combo)
        ai_layout.addLayout(provider_layout)
        
        # Selector de modelo (se actualiza según proveedor)
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modelo:"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("Selecciona un proveedor primero...")
        self.model_combo.setFixedHeight(22)
        model_layout.addWidget(self.model_combo)
        ai_layout.addLayout(model_layout)
        
        # Estado de configuración de API Keys (más compacto)
        config_layout = QHBoxLayout()
        self.config_status_label = QLabel("Config: No configurada")
        self.config_status_label.setStyleSheet("color: #e74c3c; font-size: 10px; background-color: transparent;")
        self.config_api_btn = QPushButton("⚙️ Config")
        self.config_api_btn.setFixedHeight(24)
        self.config_api_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        config_layout.addWidget(self.config_status_label)
        config_layout.addStretch()
        config_layout.addWidget(self.config_api_btn)
        ai_layout.addLayout(config_layout)
        layout.addWidget(ai_group)
        
        # === Sección 4: Segmentador Base ===
        seg_group = QGroupBox("Segmentador Base (Opcional)")
        seg_group.setMaximumHeight(60)  # Altura máxima más compacta
        seg_layout = QVBoxLayout(seg_group)
        seg_layout.setContentsMargins(8, 12, 8, 8)
        
        seg_combo_layout = QHBoxLayout()
        seg_combo_layout.addWidget(QLabel("Base:"))
        self.segmenter_combo = QComboBox()
        self.segmenter_combo.addItems([
            "Automático",
            "heading",
            "verse", 
            "paragraph",
            "sentence"
        ])
        self.segmenter_combo.setFixedHeight(22)
        seg_combo_layout.addWidget(self.segmenter_combo)
        seg_layout.addLayout(seg_combo_layout)
        layout.addWidget(seg_group)
        
        # === Sección 5: Generación ===
        gen_group = QGroupBox("Generación")
        gen_group.setMaximumHeight(140)  # Altura máxima más compacta
        gen_layout = QVBoxLayout(gen_group)
        gen_layout.setContentsMargins(8, 12, 8, 8)
        gen_layout.setSpacing(6)  # Espaciado reducido
        
        # Botón de generación
        self.generate_btn = QPushButton("🤖 Generar Perfil con IA")
        self.generate_btn.setFixedHeight(32)  # Altura más compacta
        self.generate_btn.setEnabled(False)  # Deshabilitado inicialmente
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        gen_layout.addWidget(self.generate_btn)
        
        # Botones de control del proceso (más compactos)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(3)
        
        self.pause_btn = QPushButton("⏸️")
        self.pause_btn.setFixedSize(24, 24)
        self.pause_btn.setToolTip("Pausar proceso")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.pause_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("▶️")
        self.resume_btn.setFixedSize(24, 24)
        self.resume_btn.setToolTip("Reanudar proceso")
        self.resume_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.resume_btn.setEnabled(False)
        control_layout.addWidget(self.resume_btn)
        
        self.stop_btn = QPushButton("🛑")
        self.stop_btn.setFixedSize(24, 24)
        self.stop_btn.setToolTip("Detener proceso")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()  # Empujar botones hacia la izquierda
        
        gen_layout.addLayout(control_layout)
        
        # Barra de progreso y estado (más compactos)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                font-weight: bold;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 2px;
            }
        """)
        
        self.status_label = QLabel("Estado: Listo")
        self.status_label.setFixedHeight(16)
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px; background-color: transparent;")
        
        gen_layout.addWidget(self.progress_bar)
        gen_layout.addWidget(self.status_label)
        layout.addWidget(gen_group)
        
        # Espaciador para empujar todo hacia arriba
        layout.addStretch()
        
        # Configurar el scroll area
        scroll_area.setWidget(content_widget)
        
        # Layout principal del panel
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll_area)
        
        return panel
    
    def _create_result_panel(self) -> QWidget:
        """Crea el panel de resultado y edición."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título del panel
        result_title = QLabel("Resultado y Edición")
        result_title.setFont(QFont("Arial", 12, QFont.Bold))
        result_title.setStyleSheet("color: #ffffff; margin-bottom: 10px; background-color: rgba(52, 73, 94, 0.8); padding: 6px; border-radius: 4px;")
        layout.addWidget(result_title)
        
        # === Sección 1: Algoritmo Generado ===
        algorithm_group = QGroupBox("Algoritmo Generado")
        algorithm_layout = QVBoxLayout(algorithm_group)
        
        # Editor de algoritmo
        self.algorithm_editor = QPlainTextEdit()
        self.algorithm_editor.setFont(QFont("Arial", 10))
        self.algorithm_editor.setPlaceholderText(
            "El algoritmo específico generado por IA aparecerá aquí...\n\n"
            "Incluirá reglas detalladas, umbrales y casos especiales."
        )
        self.algorithm_editor.setReadOnly(True)
        self.algorithm_editor.setMaximumHeight(200)
        self.algorithm_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f0f8ff;
                color: #2c3e50;
                border: 1px solid #3498db;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        algorithm_layout.addWidget(self.algorithm_editor)
        layout.addWidget(algorithm_group)
        
        # === Sección 2: Código Generado ===
        code_group = QGroupBox("Código Python Generado")
        code_layout = QVBoxLayout(code_group)
        
        # Tabs para diferentes tipos de código
        from PySide6.QtWidgets import QTabWidget
        self.code_tabs = QTabWidget()
        
        # Tab para segmentador
        self.segmenter_code_editor = QPlainTextEdit()
        self.segmenter_code_editor.setFont(QFont("Consolas", 9))
        self.segmenter_code_editor.setPlaceholderText("El código del segmentador personalizado aparecerá aquí...")
        self.segmenter_code_editor.setReadOnly(True)
        self.segmenter_code_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.code_tabs.addTab(self.segmenter_code_editor, "Segmentador")
        
        # Tab para loader (si se genera)
        self.loader_code_editor = QPlainTextEdit()
        self.loader_code_editor.setFont(QFont("Consolas", 9))
        self.loader_code_editor.setPlaceholderText("Código de loader personalizado (si es necesario)...")
        self.loader_code_editor.setReadOnly(True)
        self.loader_code_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.code_tabs.addTab(self.loader_code_editor, "Loader")
        
        code_layout.addWidget(self.code_tabs)
        layout.addWidget(code_group)
        
        # === Sección 3: Configuración YAML ===
        yaml_group = QGroupBox("Configuración YAML")
        yaml_layout = QVBoxLayout(yaml_group)
        
        # Editor YAML
        self.yaml_editor = QPlainTextEdit()
        self.yaml_editor.setFont(QFont("Consolas", 10))
        self.yaml_editor.setPlaceholderText(
            "El perfil YAML generado aparecerá aquí...\n\n"
            "Podrás editarlo antes de guardarlo."
        )
        self.yaml_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        
        # Indicador de validez YAML
        self.yaml_status_label = QLabel("⚪ Sin contenido")
        self.yaml_status_label.setStyleSheet("color: #6c757d; font-weight: bold; background-color: transparent;")
        
        yaml_layout.addWidget(self.yaml_editor)
        yaml_layout.addWidget(self.yaml_status_label)
        layout.addWidget(yaml_group)
        

        
        # === Sección 4: Estado y Resultados ===
        results_group = QGroupBox("Estado y Resultados")
        results_layout = QVBoxLayout(results_group)
        
        # Información del perfil generado
        self.profile_info_label = QLabel("Perfil: No generado")
        self.profile_info_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin: 5px 0;")
        results_layout.addWidget(self.profile_info_label)
        
        # Archivos generados
        self.files_info_label = QLabel("Archivos: Ninguno")
        self.files_info_label.setStyleSheet("color: #7f8c8d; margin: 5px 0;")
        results_layout.addWidget(self.files_info_label)
        
        # Resultados de pruebas
        self.test_results_label = QLabel("Pruebas: No ejecutadas")
        self.test_results_label.setStyleSheet("color: #7f8c8d; margin: 5px 0;")
        results_layout.addWidget(self.test_results_label)
        
        # Botón para probar perfil generado
        self.test_generated_btn = QPushButton("🧪 Probar Perfil Generado")
        self.test_generated_btn.setEnabled(False)
        self.test_generated_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        results_layout.addWidget(self.test_generated_btn)
        
        layout.addWidget(results_group)
        
        # === Sección 5: Logs Detallados ===
        logs_group = QGroupBox("Logs del Proceso de Generación")
        logs_layout = QVBoxLayout(logs_group)
        
        # Área de logs con scroll
        self.logs_display = QPlainTextEdit()
        self.logs_display.setFont(QFont("Consolas", 9))
        self.logs_display.setPlaceholderText(
            "Los logs detallados del proceso de generación aparecerán aquí...\n\n"
            "Incluirá información sobre cada paso, llamadas a la API, errores y correcciones."
        )
        self.logs_display.setReadOnly(True)
        self.logs_display.setMaximumHeight(250)
        self.logs_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        
        # Botones para manejo de logs
        logs_buttons_layout = QHBoxLayout()
        
        self.copy_logs_btn = QPushButton("📋 Copiar Logs")
        self.copy_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        self.clear_logs_btn = QPushButton("🗑️ Limpiar Logs")
        self.clear_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        self.save_logs_btn = QPushButton("💾 Guardar Logs")
        self.save_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        logs_buttons_layout.addWidget(self.copy_logs_btn)
        logs_buttons_layout.addWidget(self.clear_logs_btn)
        logs_buttons_layout.addWidget(self.save_logs_btn)
        logs_buttons_layout.addStretch()
        
        logs_layout.addWidget(self.logs_display)
        logs_layout.addLayout(logs_buttons_layout)
        
        layout.addWidget(logs_group)
        
        # Espaciador
        layout.addStretch()
        
        return panel
    
    def _setup_connections(self):
        """Configura las conexiones de señales y slots."""
        # Botones principales
        self.load_doc_btn.clicked.connect(self._load_document)
        self.generate_btn.clicked.connect(self._generate_intelligent_profile)
        self.test_generated_btn.clicked.connect(self._test_generated_profile)
        
        # Botones de control del proceso
        self.pause_btn.clicked.connect(self._pause_generation)
        self.resume_btn.clicked.connect(self._resume_generation)
        self.stop_btn.clicked.connect(self._stop_generation)
        
        # Botones de logs
        self.copy_logs_btn.clicked.connect(self._copy_logs)
        self.clear_logs_btn.clicked.connect(self._clear_logs)
        self.save_logs_btn.clicked.connect(self._save_logs)
        
        # (Configuración avanzada removida para simplificar la interfaz)
        
        # Configuración de IA
        self.provider_combo.currentTextChanged.connect(self._update_models_for_provider)
        self.provider_combo.currentTextChanged.connect(self._validate_inputs)
        self.model_combo.currentTextChanged.connect(self._validate_inputs)
        self.config_api_btn.clicked.connect(self._open_api_config_dialog)
        
        # Conectar señales del worker de modelos
        self.model_loader.models_loaded.connect(self._on_models_loaded)
        self.model_loader.loading_error.connect(self._on_models_error)
        
        # Validación en tiempo real
        self.description_edit.textChanged.connect(self._validate_inputs)
    
    def _load_initial_data(self):
        """Carga datos iniciales."""
        # Cargar proveedores configurados
        self._update_provider_list()
        
        # Usar un timer para cargar modelos después de que la UI esté lista
        QTimer.singleShot(100, self._load_default_provider_models)
    
    def closeEvent(self, event):
        """Maneja el cierre de la pestaña limpiando threads."""
        # Limpiar thread de carga de modelos
        if hasattr(self, 'model_loader_thread') and self.model_loader_thread.isRunning():
            self.model_loader_thread.quit()
            self.model_loader_thread.wait(3000)  # Esperar máximo 3 segundos
        
        # Limpiar thread de generación
        if hasattr(self, 'generation_thread') and self.generation_thread.isRunning():
            self.generation_thread.quit()
            self.generation_thread.wait(3000)  # Esperar máximo 3 segundos
        
        # Limpiar thread de generación inteligente
        if hasattr(self, 'intelligent_thread') and self.intelligent_thread.isRunning():
            self.intelligent_thread.quit()
            self.intelligent_thread.wait(3000)  # Esperar máximo 3 segundos
        
        super().closeEvent(event)
    
    def _update_provider_list(self):
        """Actualiza la lista de proveedores basada en las claves configuradas."""
        # Obtener estado de configuración
        api_status = self.config_manager.get_api_key_status()
        
        # Limpiar combo
        self.provider_combo.clear()
        
        # Agregar proveedores configurados con Anthropic como prioridad
        configured_providers = []
        
        # Priorizar Anthropic como proveedor por defecto
        if api_status['anthropic']:
            configured_providers.append("Anthropic")
        if api_status['openai']:
            configured_providers.append("OpenAI")
        if api_status['google']:
            configured_providers.append("Google Gemini")
        
        if configured_providers:
            self.provider_combo.addItems(configured_providers)
            # Establecer Anthropic como selección por defecto si está disponible
            if "Anthropic" in configured_providers:
                self.provider_combo.setCurrentText("Anthropic")
            self.config_status_label.setText(f"✅ {len(configured_providers)} configurado(s)")
            self.config_status_label.setStyleSheet("color: #27ae60; font-size: 10px; background-color: transparent; font-weight: bold;")
        else:
            self.provider_combo.addItem("No hay proveedores configurados")
            self.config_status_label.setText("❌ Sin configurar")
            self.config_status_label.setStyleSheet("color: #e74c3c; font-size: 10px; background-color: transparent; font-weight: bold;")
    
    def _load_default_provider_models(self):
        """Configura el estado inicial de modelos."""
        if self.provider_combo.count() > 0 and self.provider_combo.currentText() != "No hay proveedores configurados":
            self.model_combo.clear()
            self.model_combo.addItem("Cargando modelos...")
            self._update_models_for_provider(self.provider_combo.currentText())
        else:
            self.model_combo.clear()
            self.model_combo.addItem("Configura un proveedor primero...")
    
    def _load_document(self):
        """Abre diálogo para cargar documento de ejemplo."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Seleccionar Documento de Ejemplo",
            "",
            "Documentos (*.txt *.pdf *.md *.docx);;Todos los archivos (*)"
        )
        
        if file_path:
            self.sample_document_path = file_path
            self.doc_path_edit.setText(Path(file_path).name)
            self._validate_inputs()
    
    def _load_document_content(self) -> str:
        """Carga el contenido del documento seleccionado."""
        if not self.sample_document_path:
            return ""
        
        from pathlib import Path
        
        file_path = Path(self.sample_document_path)
        
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.suffix.lower() == '.pdf':
            # Usar el loader de PDF del proyecto
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
            from dataset.processing.loaders.pdf_loader import PDFLoader
            
            loader = PDFLoader(str(file_path))
            result = loader.load()
            
            # Extraer texto de los blocks
            blocks = result.get('blocks', [])
            content = '\n\n'.join(block.get('text', '') for block in blocks if block.get('text'))
            return content
        else:
            # Para otros formatos, intentar leer como texto
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def _generate_intelligent_profile(self):
        """Inicia el proceso de generación inteligente de perfil completo."""
        self.status_label.setText("Estado: Iniciando generación inteligente...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 11px;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.generate_btn.setEnabled(False)
        
        # Habilitar botones de control
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        
        # Limpiar editores
        self.algorithm_editor.clear()
        self.segmenter_code_editor.clear()
        self.loader_code_editor.clear()
        self.yaml_editor.clear()
        
        # Obtener clave API del proveedor seleccionado
        provider = self.provider_combo.currentText()
        api_keys = self.config_manager.load_api_keys()
        
        if provider == "OpenAI":
            api_key = api_keys.get('openai', '')
        elif provider == "Google Gemini":
            api_key = api_keys.get('google', '')
        elif provider == "Anthropic":
            api_key = api_keys.get('anthropic', '')
        else:
            api_key = ''
        
        # Crear generador inteligente
        self.intelligent_generator = IntelligentProfileGenerator(
            document_path=self.sample_document_path,
            description=self.description_edit.toPlainText().strip(),
            provider=provider,
            model=self.model_combo.currentText(),
            api_key=api_key,
            project_root=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        )
        
        # Conectar señales
        self.intelligent_generator.progress_update.connect(self._on_intelligent_progress)
        self.intelligent_generator.algorithm_generated.connect(self._on_algorithm_generated)
        self.intelligent_generator.code_generated.connect(self._on_code_generated)
        self.intelligent_generator.profile_completed.connect(self._on_profile_completed)
        self.intelligent_generator.generation_error.connect(self._on_intelligent_error)
        self.intelligent_generator.log_update.connect(self._on_log_update)
        
        # Crear thread y mover generador
        self.intelligent_thread = QThread()
        self.intelligent_generator.moveToThread(self.intelligent_thread)
        self.intelligent_thread.started.connect(self.intelligent_generator.generate_complete_profile)
        
        # Conectar señal finished para auto-limpieza del thread
        self.intelligent_thread.finished.connect(self.intelligent_thread.deleteLater)
        
        # Iniciar procesamiento
        self.intelligent_thread.start()
    
    def _on_intelligent_progress(self, message: str):
        """Maneja actualizaciones de progreso durante la generación inteligente."""
        self.status_label.setText(f"Estado: {message}")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 11px;")
    
    def _on_algorithm_generated(self, algorithm: str):
        """Maneja cuando se genera el algoritmo."""
        self.algorithm_editor.setPlainText(algorithm)
    
    def _on_code_generated(self, file_type: str, code: str):
        """Maneja cuando se genera código."""
        if file_type == 'segmenter':
            self.segmenter_code_editor.setPlainText(code)
        elif file_type == 'loader':
            self.loader_code_editor.setPlainText(code)
    
    def _on_profile_completed(self, profile_name: str, metadata: dict):
        """Maneja cuando se completa la generación del perfil."""
        # Actualizar información del perfil
        self.profile_info_label.setText(f"Perfil: {profile_name}")
        self.profile_info_label.setStyleSheet("font-weight: bold; color: #27ae60; margin: 5px 0;")
        
        # Mostrar archivos generados
        files_generated = metadata.get('files_generated', [])
        files_text = f"Archivos: {len(files_generated)} generados"
        if files_generated:
            files_text += f"\n• " + "\n• ".join([os.path.basename(f) for f in files_generated])
        self.files_info_label.setText(files_text)
        self.files_info_label.setStyleSheet("color: #27ae60; margin: 5px 0;")
        
        # Mostrar resultados de pruebas
        test_result = metadata.get('test_result', {})
        if test_result.get('success'):
            segments_count = test_result.get('segments_count', 0)
            self.test_results_label.setText(f"Pruebas: ✅ Exitosas ({segments_count} segmentos)")
            self.test_results_label.setStyleSheet("color: #27ae60; margin: 5px 0;")
        else:
            self.test_results_label.setText(f"Pruebas: ❌ Error")
            self.test_results_label.setStyleSheet("color: #e74c3c; margin: 5px 0;")
        
        # Cargar configuración YAML generada
        try:
            profile_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", 
                "dataset", "config", "profiles", f"{profile_name}.yaml"
            )
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    self.yaml_editor.setPlainText(f.read())
        except:
            pass
        
        # Restaurar estado
        self._reset_generation_ui()
        self.status_label.setText("Estado: Perfil generado y guardado exitosamente")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
        self.test_generated_btn.setEnabled(True)
        
        # Emitir señal de perfil generado
        self.profile_generated.emit(metadata)
        self.profile_saved.emit(profile_name)
    
    def _on_intelligent_error(self, error_message: str):
        """Maneja errores durante la generación inteligente."""
        # Restaurar estado
        self._reset_generation_ui()
        self.status_label.setText("Estado: Error en generación inteligente")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
        
        # Mostrar error al usuario
        self._show_error_dialog(error_message)
    
    def _test_generated_profile(self):
        """Prueba el perfil generado con el documento original."""
        if not hasattr(self, 'intelligent_generator') or not self.intelligent_generator.profile_name:
            QMessageBox.warning(self, "Sin Perfil", "No hay un perfil generado para probar.")
            return
        
        try:
            # Usar el ProfileManager para probar el perfil
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
            from dataset.processing.profile_manager import ProfileManager
            
            manager = ProfileManager()
            manager.load_profiles()
            
            profile_name = self.intelligent_generator.profile_name
            
            if profile_name not in manager.profiles:
                QMessageBox.warning(self, "Perfil No Encontrado", f"El perfil '{profile_name}' no se encontró en el sistema.")
                return
            
            # Procesar el documento con el perfil
            result = manager.process_file(self.sample_document_path, profile_name)
            
            if result and len(result) >= 3:
                segments, stats, metadata = result
                
                if metadata.get('error'):
                    QMessageBox.critical(self, "Error en Procesamiento", f"Error al procesar: {metadata['error']}")
                    return
                
                # Mostrar resultados
                segments_count = len(segments) if segments else 0
                self.test_results_label.setText(f"Pruebas: ✅ {segments_count} segmentos generados")
                self.test_results_label.setStyleSheet("color: #27ae60; margin: 5px 0;")
                
                # Mostrar estadísticas en un diálogo
                stats_text = f"""Resultados del procesamiento:

📊 Segmentos generados: {segments_count}
⏱️ Tiempo de procesamiento: {stats.get('processing_time', 'N/A')}
📄 Archivo procesado: {os.path.basename(self.sample_document_path)}
🔧 Perfil usado: {profile_name}

Metadatos:
{json.dumps(metadata, indent=2, ensure_ascii=False)}"""
                
                QMessageBox.information(self, "Resultados de Prueba", stats_text)
            else:
                QMessageBox.warning(self, "Sin Resultados", "El procesamiento no devolvió resultados válidos.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al probar el perfil: {str(e)}")
    
    def _on_generation_progress(self, message: str):
        """Maneja actualizaciones de progreso durante la generación."""
        self.status_label.setText(f"Estado: {message}")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 11px;")
    
    def _on_generation_finished(self, yaml_content: str, profile_name: str):
        """Maneja la finalización exitosa de la generación."""
        # Actualizar la interfaz con el resultado
        self.yaml_editor.setPlainText(yaml_content)
        self.profile_name_edit.setText(profile_name)
        
        # Restaurar estado
        self.progress_bar.setVisible(False)
        self.status_label.setText("Estado: Perfil generado exitosamente")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
        self.generate_btn.setEnabled(True)
        self.validate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        # Limpiar thread
        if hasattr(self, 'generation_thread'):
            self.generation_thread.quit()
            self.generation_thread.wait()
            
        # Limpiar worker
        if hasattr(self, 'generation_worker'):
            self.generation_worker.deleteLater()
        
        # Validar automáticamente el YAML generado
        self._validate_yaml()
        
        # Emitir señal de perfil generado
        try:
            import yaml
            profile_data = yaml.safe_load(yaml_content)
            self.profile_generated.emit(profile_data)
        except:
            pass  # Si hay error en el parsing, no emitir señal
    
    def _on_generation_error(self, error_message: str):
        """Maneja errores durante la generación."""
        # Restaurar estado
        self.progress_bar.setVisible(False)
        self.status_label.setText("Estado: Error en generación")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
        self.generate_btn.setEnabled(True)
        
        # Limpiar thread
        if hasattr(self, 'generation_thread'):
            self.generation_thread.quit()
            self.generation_thread.wait()
            
        # Limpiar worker
        if hasattr(self, 'generation_worker'):
            self.generation_worker.deleteLater()
        
        # Mostrar error al usuario con diálogo personalizado
        self._show_error_dialog(error_message)
    
    def _show_error_dialog(self, error_message: str):
        """Muestra un diálogo de error mejorado con botón de copia."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtGui import QClipboard, QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Error en Generación")
        dialog.setFixedSize(500, 350)  # Tamaño más manejable
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Analizar el tipo de error para mostrar mensaje específico
        error_type, help_message = self._analyze_error_type(error_message)
        
        # Título del error
        title_label = QLabel(f"❌ {error_type}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #e74c3c; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Mensaje de ayuda específico
        help_label = QLabel(help_message)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(help_label)
        
        # Área de texto para el error (solo lectura)
        error_text = QTextEdit()
        error_text.setPlainText(error_message)
        error_text.setReadOnly(True)
        error_text.setFont(QFont("Consolas", 9))
        error_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(error_text)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        # Botón para copiar error
        copy_btn = QPushButton("📋 Copiar Error")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        def copy_error():
            clipboard = QClipboard()
            clipboard.setText(error_message)
            copy_btn.setText("✅ Copiado")
            QTimer.singleShot(2000, lambda: copy_btn.setText("📋 Copiar Error"))
        
        copy_btn.clicked.connect(copy_error)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        buttons_layout.addWidget(copy_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        
        dialog.exec()
    
    def _analyze_error_type(self, error_message: str) -> tuple[str, str]:
        """Analiza el tipo de error y retorna título y mensaje de ayuda específicos."""
        error_lower = error_message.lower()
        
        # Error de cuota/saldo agotado
        if "429" in error_message and ("quota" in error_lower or "free tier" in error_lower):
            if "doesn't have a free quota tier" in error_message:
                return (
                    "Modelo de Pago Seleccionado",
                    "El modelo seleccionado requiere saldo en tu cuenta de API. "
                    "Opciones:\n"
                    "• Selecciona un modelo gratuito (ej: gemini-1.5-flash)\n"
                    "• Agrega saldo a tu cuenta de Google AI Studio\n"
                    "• Usa un proveedor diferente (OpenAI, Anthropic)"
                )
            else:
                return (
                    "Cuota API Agotada",
                    "Has excedido los límites de uso gratuito de la API. "
                    "Opciones:\n"
                    "• Espera a que se renueve la cuota (generalmente diaria)\n"
                    "• Agrega saldo a tu cuenta para aumentar los límites\n"
                    "• Usa un proveedor diferente con cuota disponible"
                )
        
        # Error de autenticación
        elif "401" in error_message or "authentication" in error_lower or "api key" in error_lower:
            return (
                "Error de Autenticación",
                "Problema con la clave API. Verifica que:\n"
                "• La clave API esté correctamente configurada\n"
                "• La clave no haya expirado\n"
                "• Tengas permisos para usar la API"
            )
        
        # Error de conexión
        elif "connection" in error_lower or "network" in error_lower or "timeout" in error_lower:
            return (
                "Error de Conexión",
                "Problema de conectividad. Verifica:\n"
                "• Tu conexión a internet\n"
                "• Que no haya firewall bloqueando la conexión\n"
                "• El estado del servicio de la API"
            )
        
        # Error de modelo no encontrado
        elif "404" in error_message or "not found" in error_lower or "model" in error_lower:
            return (
                "Modelo No Disponible",
                "El modelo seleccionado no está disponible. Intenta:\n"
                "• Seleccionar un modelo diferente\n"
                "• Verificar que el modelo esté activo en tu región\n"
                "• Recargar la lista de modelos"
            )
        
        # Error genérico
        else:
            return (
                "Error en Generación",
                "Ocurrió un error durante la generación del perfil. "
                "Verifica tu conexión a internet, la clave API y que el modelo seleccionado esté disponible."
            )
    
    def _validate_yaml(self):
        """Valida el YAML del perfil de forma completa."""
        yaml_content = self.yaml_editor.toPlainText().strip()
        
        if not yaml_content:
            self.yaml_status_label.setText("⚪ Sin contenido")
            self.yaml_status_label.setStyleSheet("color: #6c757d; font-weight: bold;")
            return False
        
        try:
            import yaml
            import re
            
            # Parsear YAML
            profile_data = yaml.safe_load(yaml_content)
            
            # Validaciones estructurales
            errors = []
            warnings = []
            
            # Campos requeridos
            required_fields = ['name', 'description', 'segmenter']
            for field in required_fields:
                if field not in profile_data:
                    errors.append(f"Campo requerido faltante: '{field}'")
            
            # Validar patrones regex si existen
            if 'patterns' in profile_data and isinstance(profile_data['patterns'], list):
                for i, pattern in enumerate(profile_data['patterns']):
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        errors.append(f"Patrón regex inválido #{i+1}: {e}")
            
            # Validar segmentador
            valid_segmenters = ['heading', 'paragraph', 'sentence', 'verse', 'custom']
            if 'segmenter' in profile_data:
                if profile_data['segmenter'] not in valid_segmenters:
                    warnings.append(f"Segmentador '{profile_data['segmenter']}' no es estándar")
            
            # Validar umbrales
            if 'thresholds' in profile_data:
                thresholds = profile_data['thresholds']
                if isinstance(thresholds, dict):
                    if 'min_length' in thresholds and 'max_length' in thresholds:
                        if thresholds['min_length'] >= thresholds['max_length']:
                            errors.append("min_length debe ser menor que max_length")
            
            # Mostrar resultado
            if errors:
                error_text = "; ".join(errors[:3])  # Mostrar máximo 3 errores
                self.yaml_status_label.setText(f"❌ Errores: {error_text}")
                self.yaml_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
                return False
            elif warnings:
                warning_text = "; ".join(warnings[:2])  # Mostrar máximo 2 warnings
                self.yaml_status_label.setText(f"⚠️ Advertencias: {warning_text}")
                self.yaml_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                return True
            else:
                self.yaml_status_label.setText("✅ YAML válido y completo")
                self.yaml_status_label.setStyleSheet("color: #28a745; font-weight: bold;")
                return True
                
        except yaml.YAMLError as e:
            self.yaml_status_label.setText(f"❌ Error de sintaxis YAML: {str(e)[:50]}...")
            self.yaml_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            return False
        except Exception as e:
            self.yaml_status_label.setText(f"❌ Error de validación: {str(e)[:50]}...")
            self.yaml_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            return False
    
    def _validate_yaml_realtime(self):
        """Validación de YAML en tiempo real."""
        self._validate_yaml()
        self._validate_save_inputs()
    
    def _save_profile(self):
        """Guarda el perfil generado."""
        profile_name = self.profile_name_edit.text().strip()
        yaml_content = self.yaml_editor.toPlainText().strip()
        
        if not profile_name or not yaml_content:
            QMessageBox.warning(
                self,
                "Datos Incompletos",
                "Por favor, proporciona un nombre para el perfil y asegúrate de que el YAML no esté vacío."
            )
            return
        
        # TODO: Implementar guardado real
        QMessageBox.information(
            self,
            "Perfil Guardado",
            f"El perfil '{profile_name}' ha sido guardado exitosamente.\n\n"
            "Nota: La funcionalidad de guardado será implementada completamente en las próximas subtareas."
        )
        
        # Emitir señal
        self.profile_saved.emit(profile_name)
    
    def _test_profile(self):
        """Prueba el perfil generado con una muestra del documento."""
        if not self.sample_document_path:
            QMessageBox.warning(self, "Sin Documento", "No hay documento cargado para probar.")
            return
        
        yaml_content = self.yaml_editor.toPlainText().strip()
        if not yaml_content:
            QMessageBox.warning(self, "Sin Perfil", "No hay perfil YAML para probar.")
            return
        
        try:
            import yaml
            import tempfile
            import os
            from pathlib import Path
            
            # Parsear el perfil YAML
            profile_data = yaml.safe_load(yaml_content)
            
            # Validar que el perfil tenga un segmentador válido
            if not isinstance(profile_data, dict):
                QMessageBox.warning(self, "YAML Inválido", "El contenido YAML no es válido.")
                return
            
            # Verificar que tenga segmentador válido
            valid_segmenters = ['heading', 'paragraph', 'sentence', 'verse', 'custom']
            segmenter = profile_data.get('segmenter', '')
            if segmenter not in valid_segmenters:
                QMessageBox.warning(
                    self, 
                    "Segmentador Inválido", 
                    f"El segmentador '{segmenter}' no es válido.\n"
                    f"Segmentadores válidos: {', '.join(valid_segmenters)}"
                )
                return
            
            # Crear archivo temporal del perfil
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as temp_file:
                yaml.dump(profile_data, temp_file, default_flow_style=False, allow_unicode=True)
                temp_profile_path = temp_file.name
            
            try:
                # Cargar una muestra del documento (primeros 5000 caracteres)
                document_content = self._load_document_content()
                sample_content = document_content[:5000] if len(document_content) > 5000 else document_content
                
                # Crear archivo temporal con la muestra
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_doc:
                    temp_doc.write(sample_content)
                    temp_doc_path = temp_doc.name
                
                try:
                    # Usar ProfileManager para probar el perfil
                    from dataset.processing.profile_manager import ProfileManager
                    import tempfile
                    
                    # Crear ProfileManager temporal
                    temp_manager = ProfileManager()
                    
                    # Crear un perfil temporal en el directorio de perfiles
                    temp_profile_name = f"temp_test_profile_{uuid.uuid4().hex[:8]}"
                    profiles_dir = temp_manager.profiles_dir
                    
                    # Asegurar que el directorio existe
                    os.makedirs(profiles_dir, exist_ok=True)
                    
                    temp_profile_file = os.path.join(profiles_dir, f"{temp_profile_name}.yaml")
                    
                    try:
                        # Guardar perfil temporal
                        with open(temp_profile_file, 'w', encoding='utf-8') as f:
                            yaml.dump(profile_data, f, default_flow_style=False, allow_unicode=True)
                        
                        # Recargar perfiles para incluir el temporal
                        temp_manager.load_profiles()
                        
                        # Procesar la muestra con el perfil temporal
                        result = temp_manager.process_file(
                            file_path=temp_doc_path,
                            profile_name=temp_profile_name
                        )
                        
                    finally:
                        # Limpiar perfil temporal
                        try:
                            if os.path.exists(temp_profile_file):
                                os.unlink(temp_profile_file)
                        except:
                            pass
                    
                    # Analizar resultados - process_file devuelve una tupla (segments, stats, metadata)
                    if result and isinstance(result, (list, tuple)) and len(result) >= 3:
                        segments, stats, metadata = result
                        
                        # Verificar si hay error en metadata
                        if metadata.get('error'):
                            QMessageBox.warning(
                                self,
                                "Error en Procesamiento",
                                f"Error al procesar con el perfil:\n\n{metadata['error']}"
                            )
                            return
                        
                        # Verificar si hay segmentos
                        if segments and len(segments) > 0:
                            segments_count = len(segments)
                            sample_segments = segments[:3]  # Primeros 3 segmentos
                            
                            # Mostrar resultados en diálogo
                            self._show_test_results(segments_count, sample_segments, profile_data)
                        else:
                            QMessageBox.warning(
                                self, 
                                "Prueba Fallida", 
                                "El perfil no generó ningún segmento. Revisa los patrones y umbrales."
                            )
                    else:
                        QMessageBox.warning(
                            self, 
                            "Prueba Fallida", 
                            "Error inesperado en el procesamiento. Verifica el perfil y el documento."
                        )
                
                finally:
                    # Limpiar archivo temporal del documento
                    try:
                        os.unlink(temp_doc_path)
                    except:
                        pass
            
            finally:
                # Limpiar archivo temporal del perfil
                try:
                    os.unlink(temp_profile_path)
                except:
                    pass
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error en Prueba",
                f"Error al probar el perfil:\n\n{str(e)}\n\n"
                "Verifica que el YAML sea válido y que el perfil esté bien configurado."
            )
    
    def _show_test_results(self, segments_count: int, sample_segments: list, profile_data: dict):
        """Muestra los resultados de la prueba del perfil."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Resultados de Prueba del Perfil")
        dialog.setFixedSize(600, 500)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel(f"✅ Perfil probado exitosamente")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #28a745; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Estadísticas
        stats_label = QLabel(f"📊 Segmentos generados: {segments_count}")
        stats_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(stats_label)
        
        # Información del perfil
        profile_info = f"Perfil: {profile_data.get('name', 'Sin nombre')} | Segmentador: {profile_data.get('segmenter', 'No especificado')}"
        info_label = QLabel(profile_info)
        info_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Muestra de segmentos
        sample_label = QLabel("📝 Muestra de segmentos generados:")
        sample_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-bottom: 5px;")
        layout.addWidget(sample_label)
        
        # Área de texto para mostrar segmentos
        segments_text = QTextEdit()
        segments_text.setReadOnly(True)
        segments_text.setFont(QFont("Consolas", 9))
        
        # Formatear segmentos para mostrar
        segments_display = ""
        for i, segment in enumerate(sample_segments, 1):
            if hasattr(segment, 'content'):
                content = segment.content[:200] + "..." if len(segment.content) > 200 else segment.content
            elif isinstance(segment, dict):
                content = segment.get('content', str(segment))[:200] + "..."
            else:
                content = str(segment)[:200] + "..."
            
            segments_display += f"--- Segmento {i} ---\n{content}\n\n"
        
        if segments_count > 3:
            segments_display += f"... y {segments_count - 3} segmentos más."
        
        segments_text.setPlainText(segments_display)
        segments_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(segments_text)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    # Métodos de configuración avanzada removidos para simplificar
    
    def _validate_inputs(self):
        """Valida las entradas para habilitar el botón de generación."""
        has_document = self.sample_document_path is not None
        has_description = len(self.description_edit.toPlainText().strip()) >= 10
        
        # Verificar que hay un proveedor válido seleccionado
        provider = self.provider_combo.currentText()
        has_provider = provider != "No hay proveedores configurados"
        
        # Verificar que hay un modelo válido seleccionado
        current_model = self.model_combo.currentText()
        invalid_model_texts = [
            "Configura un proveedor primero...",
            "Cargando modelos...",
            "❌ Clave API inválida",
            "❌ Servicio no disponible", 
            "❌ Timeout",
            "❌ Error:",
            "❌ Clave API no configurada"
        ]
        has_model = (self.model_combo.currentIndex() >= 0 and 
                    not any(text in current_model for text in invalid_model_texts))
        
        self.generate_btn.setEnabled(has_document and has_description and has_provider and has_model)
    
    def _validate_save_inputs(self):
        """Valida las entradas para habilitar los botones de prueba y guardado."""
        has_name = len(self.profile_name_edit.text().strip()) > 0
        has_valid_yaml = self._validate_yaml()
        has_document = self.sample_document_path is not None
        
        # Habilitar botón de prueba si hay YAML válido y documento
        self.test_btn.setEnabled(has_valid_yaml and has_document)
        
        # Habilitar botón de guardado si hay nombre y YAML válido
        self.save_btn.setEnabled(has_name and has_valid_yaml)
    
    def _update_models_for_provider(self, provider: str):
        """Actualiza la lista de modelos según el proveedor seleccionado."""
        if provider == "No hay proveedores configurados":
            self.model_combo.clear()
            self.model_combo.addItem("Configura un proveedor primero...")
            self._validate_inputs()
            return
        
        self.model_combo.clear()
        
        if provider in self.provider_models:
            # Ya tenemos los modelos en cache
            models = self.provider_models[provider]
            self.model_combo.addItems(models)
            if models:
                # Para Anthropic, seleccionar el segundo modelo si está disponible
                if provider == "Anthropic" and len(models) > 1:
                    self.model_combo.setCurrentIndex(1)
                else:
                    self.model_combo.setCurrentIndex(0)
        else:
            # Cargar modelos usando las claves guardadas
            self.model_combo.addItem("Cargando modelos...")
            self._load_models_for_provider(provider)
        
        # Validar inputs después de actualizar modelos
        self._validate_inputs()
    
    def _load_models_for_provider(self, provider: str):
        """Carga modelos para el proveedor especificado usando las claves guardadas."""
        # Obtener claves guardadas
        api_keys = self.config_manager.load_api_keys()
        
        if provider == "OpenAI":
            api_key = api_keys.get('openai', '')
            if api_key:
                self.model_loader.load_openai_models(api_key)
            else:
                self._on_models_error(provider, "Clave API no configurada")
        elif provider == "Anthropic":
            api_key = api_keys.get('anthropic', '')
            if api_key:
                self.model_loader.load_anthropic_models(api_key)
            else:
                self._on_models_error(provider, "Clave API no configurada")
        elif provider == "Google Gemini":
            api_key = api_keys.get('google', '')
            if api_key:
                self.model_loader.load_gemini_models(api_key)
            else:
                self._on_models_error(provider, "Clave API no configurada")
    
    def _on_models_loaded(self, provider: str, models: List[str]):
        """Maneja cuando se cargan los modelos exitosamente."""
        self.provider_models[provider] = models
        
        # Si es el proveedor actualmente seleccionado, actualizar el combo
        if self.provider_combo.currentText() == provider:
            self.model_combo.clear()
            self.model_combo.addItems(models)
            if models:
                # Para Anthropic, seleccionar el segundo modelo si está disponible
                if provider == "Anthropic" and len(models) > 1:
                    self.model_combo.setCurrentIndex(1)
                else:
                    self.model_combo.setCurrentIndex(0)
    
    def _on_models_error(self, provider: str, error: str):
        """Maneja errores al cargar modelos."""
        if self.provider_combo.currentText() == provider:
            self.model_combo.clear()
            
            # Mensajes más amigables según el tipo de error
            if "Se requiere clave API" in error:
                self.model_combo.addItem("Ingresa clave API para ver modelos...")
            elif "clave API inválida" in error or "Clave API inválida" in error:
                self.model_combo.addItem("❌ Clave API inválida")
            elif "No se puede conectar" in error:
                self.model_combo.addItem("❌ Servicio no disponible")
            elif "Timeout" in error:
                self.model_combo.addItem("❌ Timeout - Intenta de nuevo")
            else:
                self.model_combo.addItem(f"❌ Error: {error[:30]}...")
        
        # Solo imprimir errores reales, no falta de API key
        if "Se requiere clave API" not in error:
            print(f"Error cargando modelos de {provider}: {error}")
        
        # Validar inputs después del error
        self._validate_inputs()
    

    
    def _open_api_config_dialog(self):
        """Abre el diálogo de configuración de API keys."""
        dialog = APIConfigDialog(self.config_manager, self)
        dialog.config_saved.connect(self._on_config_saved)
        dialog.exec()
    
    def _on_config_saved(self, status: Dict[str, bool]):
        """Maneja cuando se guarda la configuración de API keys."""
        # Actualizar lista de proveedores
        self._update_provider_list()
        
        # Limpiar cache de modelos para recargar
        self.provider_models.clear()
        
        # Recargar modelos para el proveedor actual
        if self.provider_combo.currentText() != "No hay proveedores configurados":
            self._update_models_for_provider(self.provider_combo.currentText())
    
    def _pause_generation(self):
        """Pausa el proceso de generación."""
        if hasattr(self, 'intelligent_generator') and self.intelligent_generator:
            self.intelligent_generator.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.status_label.setText("Estado: ⏸️ Proceso pausado")
            self.status_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 11px;")
    
    def _resume_generation(self):
        """Reanuda el proceso de generación."""
        if hasattr(self, 'intelligent_generator') and self.intelligent_generator:
            self.intelligent_generator.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.status_label.setText("Estado: ▶️ Proceso reanudado")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
    
    def _stop_generation(self):
        """Detiene el proceso de generación."""
        if hasattr(self, 'intelligent_generator') and self.intelligent_generator:
            self.intelligent_generator.stop()
            
        # Restaurar estado de la interfaz
        self._reset_generation_ui()
        
        # Mostrar mensaje de detención
        self.status_label.setText("Estado: 🛑 Proceso detenido por el usuario")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
    
    def _reset_generation_ui(self):
        """Restaura el estado de la interfaz después de completar/detener la generación."""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # Limpiar thread si existe
        if hasattr(self, 'intelligent_thread'):
            self.intelligent_thread.quit()
            self.intelligent_thread.wait()
        
        # Limpiar generador si existe
        if hasattr(self, 'intelligent_generator'):
            self.intelligent_generator.deleteLater()
    
    def _on_log_update(self, level: str, message: str):
        """Maneja actualizaciones de logs del generador inteligente."""
        # Aplicar colores según el nivel
        color_map = {
            'INFO': '#ffffff',      # Blanco
            'SUCCESS': '#28a745',   # Verde
            'WARNING': '#ffc107',   # Amarillo
            'ERROR': '#dc3545',     # Rojo
            'DEBUG': '#6c757d',     # Gris
            'STEP': '#17a2b8'       # Azul
        }
        
        color = color_map.get(level, '#ffffff')
        
        # Formatear mensaje con color
        formatted_message = f'<span style="color: {color};">{message}</span>'
        
        # Agregar al display de logs
        self.logs_display.appendHtml(formatted_message)
        
        # Auto-scroll al final
        cursor = self.logs_display.textCursor()
        cursor.movePosition(cursor.End)
        self.logs_display.setTextCursor(cursor)
    
    def _copy_logs(self):
        """Copia todos los logs al portapapeles."""
        from PySide6.QtWidgets import QApplication
        
        # Obtener texto plano (sin HTML)
        logs_text = self.logs_display.toPlainText()
        
        if logs_text.strip():
            clipboard = QApplication.clipboard()
            clipboard.setText(logs_text)
            
            # Mostrar confirmación temporal
            original_text = self.copy_logs_btn.text()
            self.copy_logs_btn.setText("✅ Copiado")
            QTimer.singleShot(2000, lambda: self.copy_logs_btn.setText(original_text))
        else:
            QMessageBox.information(self, "Sin Logs", "No hay logs para copiar.")
    
    def _clear_logs(self):
        """Limpia todos los logs del display."""
        reply = QMessageBox.question(
            self, 
            "Limpiar Logs", 
            "¿Estás seguro de que quieres limpiar todos los logs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logs_display.clear()
    
    def _save_logs(self):
        """Guarda los logs en un archivo."""
        logs_text = self.logs_display.toPlainText()
        
        if not logs_text.strip():
            QMessageBox.information(self, "Sin Logs", "No hay logs para guardar.")
            return
        
        # Diálogo para seleccionar archivo
        file_dialog = QFileDialog()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"biblioperson_profile_generation_logs_{timestamp}.txt"
        
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "Guardar Logs",
            default_name,
            "Archivos de texto (*.txt);;Todos los archivos (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Logs de Generación de Perfil - Biblioperson\n")
                    f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(logs_text)
                
                # Mostrar confirmación
                QMessageBox.information(
                    self, 
                    "Logs Guardados", 
                    f"Los logs se han guardado exitosamente en:\n{file_path}"
                )
                
                # Confirmación temporal en el botón
                original_text = self.save_logs_btn.text()
                self.save_logs_btn.setText("✅ Guardado")
                QTimer.singleShot(2000, lambda: self.save_logs_btn.setText(original_text))
                
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Error al Guardar", 
                    f"No se pudieron guardar los logs:\n{str(e)}"
                ) 