#!/usr/bin/env python3
"""
Nuevo endpoint para integrar el pipeline refactorizado de Biblioperson
Usa: src/pipeline/ingest.py, src/search/semantic.py, etc.
"""

import sys
import os
from pathlib import Path
import logging

# Agregar rutas al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importar el nuevo pipeline refactorizado
try:
    from src.pipeline.ingest import DocumentIngestor
    from src.pipeline.chunking import create_chunker
    # Por ahora usar componentes simplificados
    HAS_NEW_PIPELINE = True
    print("✅ Nuevo pipeline cargado exitosamente")
except ImportError as e:
    HAS_NEW_PIPELINE = False
    print(f"❌ Error cargando nuevo pipeline: {e}")

class NewPipelineProcessor:
    """Procesador que usa el nuevo pipeline refactorizado"""
    
    def __init__(self):
        if not HAS_NEW_PIPELINE:
            raise RuntimeError("Nuevo pipeline no disponible")
        
        # Inicializar componentes del nuevo pipeline
        self.ingestor = DocumentIngestor()
        # Otros componentes se implementarán gradualmente
    
    def process_document(self, file_path: str, profile: str = "prosa") -> dict:
        """
        Procesa un documento usando el nuevo pipeline
        
        Args:
            file_path: Ruta al archivo a procesar
            profile: Perfil de procesamiento (prosa, verso, json)
            
        Returns:
            dict: Resultado del procesamiento
        """
        try:
            print(f"🚀 Procesando {file_path} con perfil {profile}")
            
            # 1. Ingesta: Convertir a Markdown estructurado
            print("📖 Paso 1: Extrayendo contenido...")
            result = self.ingestor.process_file(file_path)
            elements = result.get('elements', [])
            markdown_text = result.get('markdown_text', '')
            print(f"   ✓ {len(elements)} elementos extraídos")
            print(f"   📏 Markdown generado: {len(markdown_text)} caracteres")
            
            # 2. Determinar tipo de contenido basado en perfil
            if profile == "verso":
                content_type = "poetry" 
            elif profile == "json":
                content_type = "technical"
            else:
                content_type = "narrative"  # prosa por defecto
                
            print(f"   ✓ Tipo de contenido: {content_type}")
            
            # 3. Chunking: Crear chunks para búsqueda
            print("✂️ Paso 2: Creando chunks semánticos...")
            chunker = create_chunker(content_type, 
                                   chunk_size=750, 
                                   chunk_overlap=200)
            
            # Usar markdown como fuente principal de texto
            if markdown_text.strip():
                full_text = markdown_text.strip()
                print(f"   📏 Usando Markdown: {len(full_text)} caracteres")
                print(f"   📄 Muestra: {full_text[:200]}..." if len(full_text) > 200 else f"   📄 Contenido: {full_text}")
            else:
                # Fallback: concatenar texto de elementos
                texts = []
                for elem in elements:
                    # Manejar tanto diccionarios como objetos Element
                    if isinstance(elem, dict):
                        elem_text = elem.get('text', '').strip()
                    else:
                        # Si es un objeto Element de unstructured
                        elem_text = str(elem).strip() if elem else ''
                    
                    if elem_text:
                        texts.append(elem_text)
                
                full_text = "\n\n".join(texts)
                print(f"   📏 Fallback text extraído: {len(full_text)} caracteres")
            
            if full_text.strip():
                chunks = chunker.split_text(full_text)
                print(f"   ✓ {len(chunks)} chunks creados")
                if chunks:
                    print(f"   📄 Primer chunk: {chunks[0][:100]}...")
            else:
                print("   ❌ No hay texto para procesar")
                chunks = []
            
            # TODO: Implementar persistencia y embeddings
            print("🚧 Paso 3-6: Persistencia y embeddings pendientes de implementar")
            
            return {
                'success': True,
                'document_id': f"doc_{os.path.basename(file_path)}",
                'elements_count': len(elements),
                'chunks_count': len(chunks),
                'embeddings_count': len(chunks),  # Por ahora igual a chunks_count
                'content_type': content_type,
                'file_processed': os.path.basename(file_path),
                'status': 'partially_implemented'
            }
            
        except Exception as e:
            print(f"❌ Error procesando {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_processed': os.path.basename(file_path)
            }
    
    def _extract_metadata(self, file_path: str, elements) -> dict:
        """Extrae metadatos del documento"""
        from datetime import datetime
        
        # Intentar detectar título y autor de los elementos
        title = "Unknown Document"
        author = "Unknown Author"
        
        # Buscar título en los primeros elementos
        for elem in elements[:5]:
            if hasattr(elem, 'category') and elem.category == 'Title':
                title = elem.text.strip()
                break
        
        # Si no se encontró título, usar nombre de archivo
        if title == "Unknown Document":
            title = Path(file_path).stem
        
        # Detectar idioma (simplificado)
        language = "es"  # Por defecto español
        
        return {
            'title': title,
            'author': author,
            'language': language,
            'source_file': file_path,
            'processed_date': datetime.now().isoformat(),
            'processing_version': '2.0_refactored'
        }

# Función para integrar con el endpoint existente
def process_with_new_pipeline(file_path: str, config: dict) -> dict:
    """
    Función de entrada para usar desde api_conexion.py
    
    Args:
        file_path: Ruta al archivo a procesar
        config: Configuración del procesamiento
        
    Returns:
        dict: Resultado del procesamiento
    """
    if not HAS_NEW_PIPELINE:
        return {
            'success': False,
            'error': 'Nuevo pipeline no disponible',
            'fallback_required': True
        }
    
    try:
        processor = NewPipelineProcessor()
        profile = config.get('profile', 'prosa')
        
        # Mapear perfiles automáticos
        if profile in ['auto', 'automatico', 'automático']:
            # TODO: Implementar detección automática inteligente
            profile = 'prosa'  # Por ahora usar prosa por defecto
        
        return processor.process_document(file_path, profile)
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error en nuevo pipeline: {str(e)}',
            'fallback_required': True
        }

if __name__ == "__main__":
    # Test del nuevo pipeline
    print("🧪 Probando nuevo pipeline...")
    
    test_config = {
        'profile': 'prosa',
        'encoding': 'utf-8',
        'verbose': True
    }
    
    # Buscar un archivo de prueba
    test_files = [
        "test_files/poema_amor.txt",
        "dataset/test_files/poema_amor.txt", 
        "data/test.txt"
    ]
    
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            test_file = f
            break
    
    if test_file:
        print(f"📄 Probando con: {test_file}")
        result = process_with_new_pipeline(test_file, test_config)
        print(f"🎯 Resultado: {result}")
    else:
        print("❌ No se encontró archivo de prueba") 