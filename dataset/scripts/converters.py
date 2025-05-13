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
from pathlib import Path
from typing import Any, Dict, Tuple

import re

# PDF
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
except ImportError:
    pdf_extract_text = None  # type: ignore

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
    Convierte `file_path` a Markdown.

    Args:
        file_path: ruta al archivo de entrada.
        converter_config: diccionario opcional para override de opciones
                          (por ahora solo se pasa a pandoc).

    Returns:
        markdown_text, metadata_dict
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("Archivo no encontrado: %s", path)
        return "", {"converter_notes": "file_not_found"}

    ext = path.suffix.lower()
    meta: Dict[str, Any] = {"converter_notes": "", "num_chars": 0}

    # -- DOCX ----------------------------------------------------------------
    if ext == ".docx":
        md = _docx_to_markdown(path, converter_config or {})
        meta["source_title"] = path.stem
    # -- PDF -----------------------------------------------------------------
    elif ext == ".pdf":
        md = _pdf_to_markdown(path)
        meta["source_title"] = path.stem
    # -- HTML / HTM ----------------------------------------------------------
    elif ext in (".html", ".htm"):
        md = _html_to_markdown(path)
        meta["source_title"] = _guess_html_title(path)
    # -- MARKDOWN ------------------------------------------------------------
    elif ext in (".md", ".markdown"):
        md = path.read_text(encoding="utf-8", errors="ignore")
        meta["source_title"] = path.stem
    # -- PLAIN TEXT ----------------------------------------------------------
    elif ext in (".txt", ".text", ".log"):
        md = path.read_text(encoding="utf-8", errors="ignore")
        meta["source_title"] = path.stem
    else:
        logger.warning("Extensión %s no soportada aún → se devuelve vacío.", ext)
        meta["converter_notes"] = "unsupported_extension"
        return "", meta

    meta["num_chars"] = len(md)
    return md, meta


# --------------------------------------------------------------------------- #
#                           FORMAT‑SPECIFIC HELPERS                           #
# --------------------------------------------------------------------------- #

def _docx_to_markdown(path: Path, config: Dict[str, Any]) -> str:
    """Usa pandoc para convertir DOCX a Markdown."""
    pandoc_cmd = ["pandoc", "-f", "docx", "-t", "markdown", str(path)]
    # pasar flags extra si existen
    extra = config.get("pandoc_extra_args", [])
    if extra:
        pandoc_cmd[1:1] = extra

    try:
        completed = subprocess.run(
            pandoc_cmd,
            text=True,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            logger.error("pandoc error (%s): %s", completed.returncode, completed.stderr[:200])
            return ""
        return completed.stdout
    except FileNotFoundError:
        logger.error("pandoc no está instalado o no está en PATH.")
        return ""


def _pdf_to_markdown(path: Path) -> str:
    """Extrae texto de PDF y lo convierte a Markdown simple."""
    if pdf_extract_text is None:
        logger.error("pdfminer.six no instalado; no se puede procesar PDF.")
        return ""

    try:
        text = pdf_extract_text(str(path))
    except Exception as e:
        logger.error("Error al extraer texto PDF: %s", e)
        return ""

    # Separar párrafos dobles
    text = re.sub(r"\n\s*\n", "\n\n", text.strip())
    return text


def _html_to_markdown(path: Path) -> str:
    """Convierte HTML → Markdown usando BeautifulSoup + markdownify."""
    if BeautifulSoup is None or mdify is None:
        logger.error("bs4/markdownify no instalados; no se puede procesar HTML.")
        return ""

    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # Eliminar scripts y estilos
    for tag in soup(["script", "style"]):
        tag.decompose()

    markdown_text = mdify(str(soup), heading_style="ATX")
    return markdown_text


def _guess_html_title(path: Path) -> str | None:
    if BeautifulSoup is None:
        return None
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
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