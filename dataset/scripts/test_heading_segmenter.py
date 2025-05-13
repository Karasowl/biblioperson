#!/usr/bin/env python3
"""
Script para probar el HeadingSegmenter con un ejemplo.

Uso:
    python test_heading_segmenter.py
"""

import os
import sys
import json
from pathlib import Path

# Asegurar que el paquete 'dataset' está en el PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dataset.processing.segmenters.heading_segmenter import HeadingSegmenter

def create_test_document():
    """Crea un documento de prueba con estructura jerárquica."""
    return [
        # Documento de prueba con estructura de libro
        {"text": "# Título del Libro", "is_heading": True, "heading_level": 1},
        {"text": ""},
        {"text": "Descripción inicial del libro que sirve como introducción."},
        {"text": ""},
        {"text": "## Capítulo 1: Introducción", "is_heading": True, "heading_level": 2},
        {"text": ""},
        {"text": "Este es el primer párrafo del capítulo 1."},
        {"text": "Este es el segundo párrafo con más contenido para el ejemplo."},
        {"text": ""},
        {"text": "### 1.1 Primera Sección", "is_heading": True, "heading_level": 3},
        {"text": ""},
        {"text": "Contenido de la subsección 1.1 que explica conceptos básicos."},
        {"text": "Más texto para esta subsección."},
        {"text": ""},
        {"text": "### 1.2 Segunda Sección", "is_heading": True, "heading_level": 3},
        {"text": ""},
        {"text": "Contenido de la subsección 1.2 con información importante."},
        {"text": ""},
        {"text": "## Capítulo 2: Desarrollo", "is_heading": True, "heading_level": 2},
        {"text": ""},
        {"text": "Este capítulo contiene el desarrollo principal del tema."},
        {"text": ""},
        {"text": "### 2.1 Primera parte", "is_heading": True, "heading_level": 3},
        {"text": ""},
        {"text": "Detalle de la primera parte del desarrollo."},
        {"text": ""},
        {"text": "#### 2.1.1 Subsección detallada", "is_heading": True, "heading_level": 4},
        {"text": ""},
        {"text": "Información muy específica sobre este subtema."},
        {"text": ""},
        {"text": "### 2.2 Segunda parte", "is_heading": True, "heading_level": 3},
        {"text": ""},
        {"text": "Explicación de la segunda parte con más detalles."},
        {"text": ""},
        {"text": "## Capítulo 3: Conclusiones", "is_heading": True, "heading_level": 2},
        {"text": ""},
        {"text": "Este es el capítulo final que resume las ideas principales."},
        {"text": "Contiene las conclusiones y recomendaciones finales."}
    ]

def print_section_tree(section, level=0):
    """Imprime la estructura jerárquica de manera visual."""
    indent = "  " * level
    title = section.get("title", "Sin título")
    
    print(f"{indent}{'▶' if level > 0 else '📚'} {title} (Nivel: {section.get('level', '?')})")
    
    # Imprimir contenido resumido
    content = section.get("content", [])
    if content:
        content_count = len(content)
        print(f"{indent}  📝 {content_count} párrafo(s)")
        if content_count <= 2:  # Mostrar solo si hay pocos párrafos
            for item in content:
                text = item.get("text", "")
                if len(text) > 50:
                    text = text[:47] + "..."
                print(f"{indent}     └─ \"{text}\"")
    
    # Procesar subsecciones recursivamente
    subsections = section.get("subsections", [])
    for subsection in subsections:
        print_section_tree(subsection, level + 1)

def main():
    # Crear segmentador con configuración predeterminada
    segmenter = HeadingSegmenter()
    
    # Crear documento de prueba
    blocks = create_test_document()
    print(f"Documento de prueba creado con {len(blocks)} bloques\n")
    
    # Segmentar documento
    print("Procesando documento...")
    segments = segmenter.segment(blocks)
    
    # Analizar resultados
    sections = [s for s in segments if s.get("type") == "section"]
    paragraphs = [s for s in segments if s.get("type") == "paragraph"]
    headings = [s for s in segments if s.get("type") == "heading"]
    
    print(f"\nResultados de la segmentación:")
    print(f"- Secciones: {len(sections)}")
    print(f"- Párrafos sueltos: {len(paragraphs)}")
    print(f"- Encabezados sueltos: {len(headings)}")
    
    # Imprimir estructura jerárquica
    print("\nEstructura del documento:")
    for section in sections:
        print_section_tree(section)
    
    # Guardar resultados en JSON para análisis
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "heading_segmenter_test.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    
    print(f"\nResultados guardados en: {output_file}")
    
    # Probar la versión plana
    flat_sections = segmenter._flatten_sections(sections)
    flat_output = output_dir / "heading_segmenter_flat.json"
    
    with open(flat_output, 'w', encoding='utf-8') as f:
        json.dump(flat_sections, f, ensure_ascii=False, indent=2)
    
    print(f"Versión plana guardada en: {flat_output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
