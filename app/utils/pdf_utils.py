"""
app/utils/pdf_utils.py
Extraccion de texto de PDFs usando PyMuPDF (fitz).
Requiere: pip install pymupdf

Se usa fitz en vez de pypdf porque el proyecto original (chromadbapi.py)
usaba PyMuPDF, que produce mejor calidad de extraccion de texto y mantiene
la separacion por pagina con marcadores "--- Pagina N ---".
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(filepath: str) -> tuple[str, int]:
    
    try:
        doc = fitz.open(filepath)
        full_text = ""

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                # Normalizar espacios dentro de la pagina (igual que el original)
                text = " ".join(text.split())
                full_text += f"\n--- Página {page_num} ---\n{text}"

        total_pages = len(doc)
        doc.close()
        return full_text.strip(), total_pages

    except Exception as e:
        print(f"[pdf_utils] Error extrayendo texto: {e}")
        return "", 0


def count_pages(filepath: str) -> int:
    try:
        doc = fitz.open(filepath)
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        print(f"[pdf_utils] Error contando paginas: {e}")
        return 0