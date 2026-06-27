"""
app/utils/embedding_utils.py
Funciones para generar embeddings usando Ollama (mistral:latest).
"""

from config.ollama import get_embedding_client

_client = get_embedding_client()


def generate_embeddings(texts: list[str]) -> list[list[float]]:

    return _client.embed_documents(texts)


def generate_query_embedding(query: str) -> list[float]:
    
    return _client.embed_query(query)