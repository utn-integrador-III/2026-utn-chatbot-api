"""
app/services/data_ingest_service.py

Servicio encargado de procesar documentos PDF.

Flujo:

PDF
 |
Extracción de texto
 |
División en chunks
 |
Creación de embeddings con Ollama
 |
Almacenamiento en PostgreSQL + pgvector

Reemplaza el almacenamiento anterior de ChromaDB.
"""

import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader


from app.config.settings import (
    UPLOAD_FOLDER,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

from app.config.ollama import get_embedding_client

from app.repositories import chunk_repository



# Cliente para generar embeddings
_embedding_client = get_embedding_client()



def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrae todo el texto contenido dentro de un PDF.
    """

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text



def split_text(text: str) -> list[Document]:
    """
    Divide el texto en fragmentos pequeños.

    Los chunks permiten realizar búsquedas más precisas
    mediante embeddings.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    return splitter.create_documents(
        [text]
    )



def process_pdf(file_path: str, pdf_id: int) -> dict:
    """
    Procesa un PDF completo y almacena sus fragmentos.

    Pasos:
    1. Lee el PDF.
    2. Divide el contenido.
    3. Genera embeddings.
    4. Guarda los chunks en PostgreSQL.
    """

    text = extract_text_from_pdf(
        file_path
    )


    chunks = split_text(
        text
    )


    stored = 0


    for index, chunk in enumerate(chunks):

        embedding = _embedding_client.embed_query(
            chunk.page_content
        )


        chunk_repository.insert_chunk(
            pdf_id=pdf_id,
            chunk_index=index,
            chunk_text=chunk.page_content,
            embedding=embedding
        )


        stored += 1


    return {
        "message": "Documento procesado correctamente",
        "chunks": stored
    }



def save_uploaded_pdf(file) -> str:
    """
    Guarda físicamente un PDF recibido
    dentro de la carpeta uploads.
    """

    filename = file.filename

    path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(path)

    return path