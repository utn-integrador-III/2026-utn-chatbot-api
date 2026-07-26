"""
app/utils/text_utils.py
Limpieza y division de texto en chunks.

"""

import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


def preprocess_text(text: str) -> str:

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\n\r]', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def split_into_chunks(full_text: str) -> list[dict]:
    
    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n\n",   # Seccion larga
            "\n\n",     # Parrafos
            ". ",       # Oraciones completas
            "\n",       # Lineas
            "; ",       # Listas
            " "         # Espacios (ultimo recurso)
        ],
        chunk_size=2500,
        chunk_overlap=400,
        length_function=len,
        keep_separator=True,
    )

    raw_chunks = splitter.split_text(full_text)

    result: list[dict] = []
    for index, chunk_text in enumerate(raw_chunks):
        # Intentar detectar numero de pagina en el marcador "--- Pagina N ---"
        match = re.search(r'---\s*P[aá]gina\s+(\d+)\s*---', chunk_text)
        page_ref = match.group(1) if match else None

        result.append({
            "chunk_text":  chunk_text,
            "chunk_index": index,
            "page_ref":    page_ref,
        })

    return result