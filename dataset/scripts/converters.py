"""
dataset/scripts/converters.py
Convierte archivos de distintos formatos (DOCX, PDF, HTML, TXT, MD) a Markdown.

• DOCX   → pandoc
• PDF    → pdfminer.six  → texto plano  → Markdown simple
• HTML   → BeautifulSoup4 + markdownify
• TXT/MD → lectura directa

La función principal devuelve:
    (markdown_text: str, metadata: Dict[str, Any])

`metadata` incluye, cuando es posible:
    - 'source_title'      (título del documento)
    - 'num_pages'         (PDF)
    - 'num_chars'         (conteo caracteres del Markdown)
    - 'converter_notes'   (warnings, etc.)
"""

from __future__ import annotations

import subprocess
import tempfile
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple

import re

# PDF
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.psparser import PSLiteral
    from pdfminer.utils import PDFDate
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage
except ImportError:
    pdf_extract_text = None  # type: ignore
    PDFParser = None # type: ignore
    PDFDocument = None # type: ignore
    PSLiteral = None # type: ignore
    PDFDate = None # type: ignore
    PDFPage = None # type: ignore
    LAParams = None # type: ignore

# HTML
try:
    from bs4 import BeautifulSoup
    from markdownify import markdownify as mdify
except ImportError:
    BeautifulSoup = None  # type: ignore
    mdify = None  # type: ignore

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#                               CORE FUNCTION                                 #
# --------------------------------------------------------------------------- #

def convert_file_to_markdown(
    file_path: str | Path,
    converter_config: Dict[str, Any] | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Convierte `file_path` a Markdown y extrae metadatos del documento fuente.

    Args:
        file_path: ruta al archivo de entrada.
        converter_config: diccionario opcional para override de opciones
                          (por ahora solo se pasa a pandoc).

    Returns:
        Tuple[str, Dict[str, Any]]: 
            - markdown_text (str): Contenido convertido a Markdown.
            - source_doc_metadata (Dict[str, Any]): Diccionario con metadatos
              alineados con ProcessedContentItem (ej. 'titulo_documento',
              'hash_documento_original', 'metadatos_adicionales_fuente').
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("Archivo no encontrado: %s", path)
        # Devolver estructura de metadatos vacía pero con nota de error
        return "", {
            "ruta_archivo_original": str(path.resolve()),
            "hash_documento_original": None,
            "titulo_documento": None,
            "autor_documento": None,
            "fecha_publicacion_documento": None,
            "editorial_documento": None,
            "isbn_documento": None,
            "idioma_documento": "und", # Indeterminado
            "metadatos_adicionales_fuente": {
                "converter_notes": "file_not_found",
                "num_chars_markdown": 0
            }
        }

    ext = path.suffix.lower()
    # Inicializar metadatos del documento fuente
    source_doc_metadata: Dict[str, Any] = {
        "ruta_archivo_original": str(path.resolve()),
        "hash_documento_original": _calculate_sha256(path),
        "titulo_documento": path.stem, # Fallback inicial
        "autor_documento": None,
        "fecha_publicacion_documento": None,
        "editorial_documento": None,
        "isbn_documento": None,
        "idioma_documento": "und", # Default, loaders/processors deben verificar/establecer.
        "metadatos_adicionales_fuente": {
            "converter_notes": "",
            "num_chars_markdown": 0,
            "file_extension": ext
        }
    }

    md = ""
    # -- DOCX ----------------------------------------------------------------
    if ext == ".docx":
        md, docx_meta = _docx_to_markdown(path, converter_config or {})
        source_doc_metadata.update(docx_meta) # Actualiza con lo que pandoc pudo extraer
        if not source_doc_metadata.get("titulo_documento"):
             source_doc_metadata["titulo_documento"] = path.stem
    # -- PDF -----------------------------------------------------------------
    elif ext == ".pdf":
        md, pdf_meta = _pdf_to_markdown(path)
        source_doc_metadata.update(pdf_meta)
        if not source_doc_metadata.get("titulo_documento"):
             source_doc_metadata["titulo_documento"] = path.stem
    # -- HTML / HTM ----------------------------------------------------------
    elif ext in (".html", ".htm"):
        md = _html_to_markdown_text(path)
        source_doc_metadata["titulo_documento"] = _guess_html_title(path) or path.stem
    # -- MARKDOWN ------------------------------------------------------------
    elif ext in (".md", ".markdown"):
        md = path.read_text(encoding="utf-8", errors="ignore")
        source_doc_metadata["titulo_documento"] = path.stem
    # -- PLAIN TEXT ----------------------------------------------------------
    elif ext in (".txt", ".text", ".log"):
        md = path.read_text(encoding="utf-8", errors="ignore")
        source_doc_metadata["titulo_documento"] = path.stem
    else:
        logger.warning("Extensión %s no soportada aún → se devuelve vacío.", ext)
        source_doc_metadata["metadatos_adicionales_fuente"]["converter_notes"] = "unsupported_extension"
        return "", source_doc_metadata

    source_doc_metadata["metadatos_adicionales_fuente"]["num_chars_markdown"] = len(md)
    if source_doc_metadata["idioma_documento"] == "und":
        current_notes = source_doc_metadata["metadatos_adicionales_fuente"].get("converter_notes", "")
        if current_notes:
            current_notes += "; idioma_documento set to 'und', requires verification"
        else:
            current_notes = "idioma_documento set to 'und', requires verification"
        source_doc_metadata["metadatos_adicionales_fuente"]["converter_notes"] = current_notes

    return md, source_doc_metadata


# --------------------------------------------------------------------------- #
#                           FORMAT‑SPECIFIC HELPERS                           #
# --------------------------------------------------------------------------- #

def _calculate_sha256(file_path: Path) -> str:
    """Calcula el hash SHA256 de un archivo."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error("No se pudo leer el archivo para hashing %s: %s", file_path, e)
        return ""

def _docx_to_markdown(path: Path, config: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Usa pandoc para convertir DOCX a Markdown y extraer metadatos básicos."""
    meta: Dict[str, Any] = {}
    # TODO: Investigar cómo extraer metadatos de DOCX (autor, fecha_publicacion) con pandoc.
    # Pandoc puede extraerlos a un AST JSON, pero no directamente con la conversión a markdown simple.
    # Por ahora, se usará el nombre de archivo como título y otros campos quedarán vacíos o None.
    # Considerar parsear docProps/core.xml si es necesario y no hay opción pandoc directa.

    pandoc_cmd = ["pandoc", "-f", "docx", "-t", "markdown", str(path)]
    extra = config.get("pandoc_extra_args", [])
    if extra:
        pandoc_cmd[1:1] = extra

    try:
        completed = subprocess.run(
            pandoc_cmd,
            text=True,
            check=False,
            capture_output=True,
            encoding='utf-8' # Asegurar UTF-8
        )
        if completed.returncode != 0:
            logger.error("pandoc error (%s): %s", completed.returncode, completed.stderr[:200])
            meta.setdefault("metadatos_adicionales_fuente", {}).setdefault("converter_notes", "")
            meta["metadatos_adicionales_fuente"]["converter_notes"] += f"pandoc_error: {completed.stderr[:100]}; "
            return "", meta
        return completed.stdout, meta
    except FileNotFoundError:
        logger.error("pandoc no está instalado o no está en PATH.")
        meta.setdefault("metadatos_adicionales_fuente", {}).setdefault("converter_notes", "")
        meta["metadatos_adicionales_fuente"]["converter_notes"] += "pandoc_not_found; "
        return "", meta
    except Exception as e:
        logger.error(f"Error inesperado al ejecutar pandoc: {e}")
        meta.setdefault("metadatos_adicionales_fuente", {}).setdefault("converter_notes", "")
        meta["metadatos_adicionales_fuente"]["converter_notes"] += f"pandoc_unexpected_error: {str(e)[:100]}; "
        return "", meta

def _decode_pdf_string(s, default_encoding='utf-8') -> str:
    """Decodifica una cadena de PDF (puede ser bytes o PSLiteral)."""
    if isinstance(s, bytes):
        try:
            return s.decode(default_encoding, 'surrogateescape')
        except UnicodeDecodeError:
            return s.decode('latin-1', 'replace') # Fallback a latin-1
    if PSLiteral is not None and isinstance(s, PSLiteral):
        # Los PSLiteral a menudo ya están en una forma cercana a una cadena Python
        # pero su .name podría ser la representación str que queremos.
        # Esto es heurístico y puede necesitar ajustes según el contenido.
        s_name = getattr(s, 'name', str(s))
        if isinstance(s_name, bytes):
             try:
                return s_name.decode(default_encoding, 'surrogateescape')
             except UnicodeDecodeError:
                return s_name.decode('latin-1', 'replace')
        return str(s_name) # Convertir a str como último recurso
    return str(s) # Si no es bytes ni PSLiteral conocido, intentar convertir a str

def _pdf_to_markdown(path: Path) -> Tuple[str, Dict[str, Any]]:
    """Extrae texto de PDF y lo convierte a Markdown simple. Intenta extraer metadatos."""
    extracted_metadata: Dict[str, Any] = {
        "metadatos_adicionales_fuente": {}
    }
    num_pages = 0

    if pdf_extract_text is None or PDFParser is None or PDFDocument is None:
        logger.error("pdfminer.six no instalado o componentes faltantes; no se puede procesar PDF.")
        extracted_metadata["metadatos_adicionales_fuente"]["converter_notes"] = "pdfminer_not_installed_or_incomplete; "
        return "", extracted_metadata

    text_content = ""
    try:
        with open(path, 'rb') as fp:
            # Extraer texto
            # Usar LAParams para mejorar el layout si es necesario, por defecto es simple
            text_content = pdf_extract_text(fp)

            # Extraer metadatos
            fp.seek(0) # Volver al inicio para el parser de metadatos
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            
            if doc.info: # doc.info es una lista de diccionarios de metadatos
                doc_info = doc.info[0] # Usualmente solo hay un diccionario
                title = doc_info.get('Title')
                if title:
                    extracted_metadata['titulo_documento'] = _decode_pdf_string(title)
                
                author = doc_info.get('Author')
                if author:
                    extracted_metadata['autor_documento'] = _decode_pdf_string(author)
                
                # Fechas pueden ser CreationDate o ModDate. Usaremos CreationDate si está.
                # El formato es D:YYYYMMDDHHMMSSOHH'mm'
                creation_date_str = doc_info.get('CreationDate')
                if PDFDate is not None and creation_date_str:
                    try:
                        # PDFDate.decode maneja la conversión de formato PDF Date string
                        dt_obj = PDFDate.decode(creation_date_str)
                        # Formatear a YYYY-MM-DD o YYYY
                        # strftime puede fallar si el año es muy antiguo/grande, así que proteger
                        try:
                            if dt_obj.year > 1: # Año válido
                                extracted_metadata['fecha_publicacion_documento'] = dt_obj.strftime('%Y-%m-%d')
                        except ValueError:
                             if hasattr(dt_obj, 'year') and dt_obj.year > 1:
                                extracted_metadata['fecha_publicacion_documento'] = str(dt_obj.year) # Solo año como fallback
                    except Exception as e_date:
                        logger.warning(f"Error decodificando fecha PDF '{creation_date_str}': {e_date}")
                        extracted_metadata['metadatos_adicionales_fuente']["converter_notes"] = extracted_metadata['metadatos_adicionales_fuente'].get("converter_notes","") + f"pdf_date_parse_error: {e_date}; "
            
            # Contar páginas
            fp.seek(0)
            if PDFPage is not None:
                try:
                    num_pages = sum(1 for _ in PDFPage.get_pages(fp, check_extractable=True))
                except Exception as e_page_count:
                    logger.warning(f"Error contando páginas PDF: {e_page_count}")
                    num_pages = 0 # O manejar el error como se prefiera
            extracted_metadata["metadatos_adicionales_fuente"]["num_pages"] = num_pages

    except Exception as e:
        logger.error("Error al procesar PDF %s: %s", path, e)
        extracted_metadata["metadatos_adicionales_fuente"]["converter_notes"] = extracted_metadata['metadatos_adicionales_fuente'].get("converter_notes","") + f"pdf_processing_error: {e}; "
        return "", extracted_metadata

    # Separar párrafos dobles
    text_content = re.sub(r"\n\s*\n", "\n\n", text_content.strip())
    return text_content, extracted_metadata


def _html_to_markdown_text(path: Path) -> str:
    """Convierte HTML → Markdown usando BeautifulSoup + markdownify."""
    if BeautifulSoup is None or mdify is None:
        logger.error("bs4/markdownify no instalados; no se puede procesar HTML.")
        return ""

    html_content = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html_content, "html.parser")

    # Eliminar scripts y estilos
    for tag in soup(["script", "style"]):
        tag.decompose()

    markdown_text = mdify(str(soup), heading_style="ATX")
    return markdown_text


def _guess_html_title(path: Path) -> str | None:
    if BeautifulSoup is None:
        return None
    html_content = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html_content, "html.parser")
    title_tag = soup.find("title")
    return title_tag.text.strip() if title_tag else None


if __name__ == '__main__':
    # Crear directorio de prueba si no existe
    test_dir = "test_conversion_files_output"
    os.makedirs(test_dir, exist_ok=True)
    
    # Para probar, necesitas colocar archivos de ejemplo en un directorio, por ejemplo "sample_files"
    sample_files_dir = "sample_files_for_conversion"
    os.makedirs(sample_files_dir, exist_ok=True)
    print(f"Place your sample DOCX, PDF, HTML, TXT, MD files in '{sample_files_dir}' to test conversion.")

    # Archivo de prueba TXT (creado automáticamente)
    sample_txt_path = os.path.join(sample_files_dir, "sample.txt")
    with open(sample_txt_path, "w", encoding="utf-8") as f:
        f.write("This is the first line of the text file.\n\nThis is a second paragraph after a blank line.\nThis line directly follows.")
    
    # Archivo de prueba HTML (creado automáticamente)
    sample_html_path = os.path.join(sample_files_dir, "sample.html")
    with open(sample_html_path, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Sample HTML Title</title></head><body><h1>Main Heading</h1><p>This is a paragraph with <b>bold</b> and <i>italic</i> text.</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>")

    # Lista de archivos a probar (añade tus archivos DOCX y PDF aquí manualmente)
    # Ejemplo:
    # test_file_paths = [
    #     os.path.join(sample_files_dir, "my_document.docx"),
    #     os.path.join(sample_files_dir, "my_presentation.pdf"),
    #     sample_txt_path,
    #     sample_html_path,
    #     os.path.join(sample_files_dir, "my_notes.md") # Asumiendo que tienes un my_notes.md
    # ]
    
    # Para una prueba rápida solo con los creados automáticamente:
    test_file_paths = [sample_txt_path, sample_html_path]
    if DOCX_PYTHON_AVAILABLE: # Solo añadir si python-docx está para metadatos, pandoc es externo
         # Necesitarás un DOCX de prueba real llamado "sample.docx" en sample_files_dir
        sample_docx_path = os.path.join(sample_files_dir, "sample.docx")
        if os.path.exists(sample_docx_path):
            test_file_paths.append(sample_docx_path)
        else:
            print(f"WARNING: DOCX test file '{sample_docx_path}' not found. Skipping DOCX test.")
            
    if pdfminer_extract_text:
        # Necesitarás un PDF de prueba real llamado "sample.pdf" en sample_files_dir
        sample_pdf_path = os.path.join(sample_files_dir, "sample.pdf")
        if os.path.exists(sample_pdf_path):
            test_file_paths.append(sample_pdf_path)
        else:
            print(f"WARNING: PDF test file '{sample_pdf_path}' not found. Skipping PDF test.")


    for f_path in test_file_paths:
        if not os.path.exists(f_path):
            logging.warning(f"Test file {f_path} not found. Skipping.")
            continue
        
        print(f"\n--- Converting: {os.path.basename(f_path)} ---")
        markdown_content, metadata = convert_file_to_markdown(f_path)
        
        if markdown_content:
            print(f"Successfully converted {os.path.basename(f_path)}.")
            print("Extracted Metadata:", metadata)
            # Guardar el markdown resultante para inspección
            output_md_filename = os.path.join(test_dir, os.path.basename(f_path) + ".md")
            with open(output_md_filename, "w", encoding="utf-8") as out_f:
                out_f.write(f"# METADATA: {metadata}\n\n---\n\n{markdown_content}")
            print(f"Output saved to: {output_md_filename}")
        else:
            print(f"Failed to convert {os.path.basename(f_path)}.")

    print(f"\nCheck all converted Markdown files in the '{test_dir}' directory.")
    print("Ensure Pandoc is installed if you are testing DOCX files: https://pandoc.org/installing.html")