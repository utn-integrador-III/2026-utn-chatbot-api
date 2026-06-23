"""
app/utils/text_utils.py
Limpieza y division de texto en chunks.

Los parametros del splitter y la logica de preprocess_text se mantienen
identicos al original (chromadbapi.py) para no alterar la calidad de los
chunks que ya estaba validada en produccion:
    chunk_size=2500, chunk_overlap=400
    Separadores: secciones largas → parrafos → oraciones → lineas → listas → espacios
"""

import re

from langchain.text_splitter import RecursiveCharacterTextSplitter


def preprocess_text(text: str) -> str:
    """
    Limpia y normaliza el texto extraido del PDF.
    Identica a la funcion del original (chromadbapi.py):
        - Normaliza espacios multiples
        - Elimina caracteres extraños manteniendo puntuacion basica
        - Reduce saltos de linea innecesarios
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\n\r]', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def split_into_chunks(full_text: str) -> list[dict]:
    """
    Divide el texto completo del PDF en chunks usando los mismos
    parametros y separadores del original (chromadbapi.py).

    Recibe el texto ya preprocesado (salida de preprocess_text).

    Retorna una lista de dicts con:
        chunk_text  : str → texto del fragmento
        chunk_index : int → posicion del chunk (0-based)
        page_ref    : str | None → numero de pagina detectado en el marcador
                      "--- Pagina N ---" mas cercano antes del chunk

    Por que chunk_size=2500 y overlap=400:
    El original usaba estos valores para mantener fragmentos grandes con
    suficiente contexto, y el overlap alto (400) para no perder informacion
    en los bordes de los chunks.
    """
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