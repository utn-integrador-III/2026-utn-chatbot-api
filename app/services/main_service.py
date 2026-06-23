"""
app/services/main_service.py

Servicio principal del chatbot RAG.

Gestiona el proceso de:
- búsqueda de información con BM25 y pgvector
- selección de documentos relevantes
- construcción del contexto
- envío de consultas a Ollama

Migración:
ChromaDB fue reemplazado por PostgreSQL + pgvector.
Los embeddings son generados con OllamaEmbeddings.
"""

import re

from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.config.ollama import chat, get_embedding_client
from app.config.settings import (
    BM25_K,
    VECTOR_SEARCH_K,
    MAX_CONTEXT_CHARS,
    RERANK_TOP_K
)

from app.repositories import chunk_repository



# Expresión usada para detectar fechas dentro de consultas
MONTHS_ES = r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"

DATE_REGEX = re.compile(
    rf"\b(\d{{1,2}}\s+de\s+{MONTHS_ES}\s+(de\s+\d{{4}})?)\b|\b\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}\b",
    re.IGNORECASE,
)


# Cliente encargado de generar embeddings usando Ollama
_embedding_client = get_embedding_client()



def _load_all_docs_from_pg() -> list[Document]:
    """
    Obtiene los fragmentos almacenados en PostgreSQL
    y los convierte al formato Document de LangChain.
    """



def _build_bm25() -> BM25Retriever | None:
    """
    Crea el buscador BM25 utilizando los documentos cargados.
    """



class _PGVectorRetriever:
    """
    Retriever personalizado para consultar pgvector.

    Convierte la pregunta en un embedding y busca
    fragmentos similares en PostgreSQL.
    """


    def invoke(self, query: str) -> list[Document]:
        """
        Realiza la búsqueda semántica en pgvector.
        """



    def get_relevant_documents(self, query: str):
        return self.invoke(query)



def _build_ensemble(bm25, vector_retriever):
    """
    Combina búsqueda por texto (BM25)
    y búsqueda vectorial (pgvector).
    """



def _rerank_light(
    docs: list[Document],
    question: str,
    top_k: int = RERANK_TOP_K
):
    """
    Reordena documentos según relevancia
    antes de enviarlos al modelo.
    """



def _build_context(
    docs: list[Document],
    max_chars: int = MAX_CONTEXT_CHARS
):
    """
    Construye el contexto que recibe Ollama.
    """



def process_chat(user_prompt: str) -> dict:
    """
    Ejecuta el flujo completo del chatbot:

    Pregunta → búsqueda → re-ranking → contexto → Ollama.
    """



def refresh_bm25() -> dict:
    """
    Actualiza BM25 después de agregar nuevos documentos.
    """