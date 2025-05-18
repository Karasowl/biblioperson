#!/usr/bin/env python3
"""
Script para probar los loaders de diferentes formatos de archivo.
Este script muestra cómo cargar cada tipo de archivo soportado.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Asegurar que los módulos se encuentren en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.loaders import (
    txtLoader, MarkdownLoader, NDJSONLoader, DocxLoader, 
    PDFLoader, ExcelLoader, CSVLoader
)

def mostrar_documento(doc):
    """Muestra un documento procesado de forma legible."""
    # Filtrar campos internos
    campos_a_mostrar = {k: v for k, v in doc.items() if not k.startswith('_')}
    return json.dumps(campos_a_mostrar, ensure_ascii=False, indent=2)

def probar_loader(loader_class, archivo, tipo='escritos'):
    """Prueba un loader específico y muestra los resultados."""
    print(f"\n{'='*80}")
    print(f"Probando {loader_class.__name__} con {archivo}")
    print(f"{'='*80}")
    
    try:
        loader = loader_class(archivo, tipo=tipo)
        for i, doc in enumerate(loader.load(), 1):
            if i <= 3:  # Mostrar solo los primeros 3 documentos para no saturar la salida
                print(f"\nDocumento {i}:")
                print(mostrar_documento(doc))
            else:
                print(f"\n... y {i-3} documentos más")
                break
                
        print(f"\nProcesamiento completado. Total documentos: {i}")
    except Exception as e:
        print(f"Error al procesar: {e}")

def probar_gestor_perfiles(archivo, perfil='book_structure'):
    """Prueba el gestor de perfiles con un archivo dado."""
    print(f"\n{'='*80}")
    print(f"Probando ProfileManager con {archivo} usando perfil '{perfil}'")
    print(f"{'='*80}")
    
    try:
        manager = ProfileManager()
        resultados = manager.process_file(archivo, perfil)
        
        if resultados:
            for i, doc in enumerate(resultados[:3], 1):  # Mostrar solo los 3 primeros
                print(f"\nResultado {i}:")
                print(mostrar_documento(doc))
            
            if len(resultados) > 3:
                print(f"\n... y {len(resultados)-3} resultados más")
                
            print(f"\nProcesamiento completado. Total resultados: {len(resultados)}")
        else:
            print("No se obtuvieron resultados.")
    except Exception as e:
        print(f"Error en el gestor de perfiles: {e}")

def main():
    """Función principal de prueba."""
    # Configurar logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Directorio de pruebas (ajustar según estructura del proyecto)
    test_dir = Path(__file__).parent / "prueba_loaders"
    test_dir.mkdir(exist_ok=True)
    
    # Crear archivos de ejemplo para pruebas si no existen
    crear_archivos_ejemplo(test_dir)
    
    # Probar cada loader
    print("\nPRUEBAS DE LOADERS INDIVIDUALES")
    print("-"*50)
    
    # Archivos de ejemplo para cada loader
    archivos_ejemplo = {
        txtLoader: test_dir / "ejemplo.txt",
        MarkdownLoader: test_dir / "ejemplo.md",
        NDJSONLoader: test_dir / "ejemplo.ndjson",
        DocxLoader: test_dir / "ejemplo.docx",
        PDFLoader: test_dir / "ejemplo.pdf",
        ExcelLoader: test_dir / "ejemplo.xlsx",
        CSVLoader: test_dir / "ejemplo.csv"
    }
    
    # Probar cada loader que tenga su archivo de ejemplo
    for loader_class, archivo in archivos_ejemplo.items():
        if archivo.exists():
            probar_loader(loader_class, archivo)
    
    # Probar el gestor de perfiles
    print("\nPRUEBAS DEL GESTOR DE PERFILES")
    print("-"*50)
    
    for archivo in archivos_ejemplo.values():
        if archivo.exists():
            probar_gestor_perfiles(archivo)
    
def crear_archivos_ejemplo(directorio):
    """Crea archivos de ejemplo para pruebas si no existen."""
    # Ejemplo de texto
    archivo_txt = directorio / "ejemplo.txt"
    if not archivo_txt.exists():
        with open(archivo_txt, 'w', encoding='utf-8') as f:
            f.write("Título del documento\n\n")
            f.write("Este es un ejemplo de archivo de texto.\n")
            f.write("Contiene múltiples líneas para probar el txtLoader.\n\n")
            f.write("Y también tiene múltiples párrafos separados por líneas en blanco.")
    
    # Ejemplo de Markdown
    archivo_md = directorio / "ejemplo.md"
    if not archivo_md.exists():
        with open(archivo_md, 'w', encoding='utf-8') as f:
            f.write("# Título del documento Markdown\n\n")
            f.write("Este es un **ejemplo** de archivo *Markdown*.\n\n")
            f.write("## Una sección\n\n")
            f.write("- Elemento 1\n")
            f.write("- Elemento 2\n\n")
            f.write("### Subsección\n\n")
            f.write("Texto de la subsección.")
    
    # Ejemplo de NDJSON
    archivo_ndjson = directorio / "ejemplo.ndjson"
    if not archivo_ndjson.exists():
        with open(archivo_ndjson, 'w', encoding='utf-8') as f:
            f.write('{"id": 1, "texto": "Primer registro en NDJSON"}\n')
            f.write('{"id": 2, "texto": "Segundo registro"}\n')
            f.write('{"id": 3, "texto": "Tercer registro", "metadatos": {"fecha": "2023-05-15"}}\n')
    
    # Ejemplo de CSV
    archivo_csv = directorio / "ejemplo.csv"
    if not archivo_csv.exists():
        with open(archivo_csv, 'w', encoding='utf-8') as f:
            f.write('Nombre,Edad,Ciudad\n')
            f.write('Juan Pérez,32,Madrid\n')
            f.write('María López,28,Barcelona\n')
            f.write('Carlos Ruiz,45,Valencia\n')
    
    # Informar sobre los archivos que requieren creación manual
    print(f"Los siguientes archivos deben crearse manualmente en {directorio}:")
    for ext in ['.docx', '.pdf', '.xlsx']:
        print(f"  - ejemplo{ext}")

if __name__ == "__main__":
    main() 