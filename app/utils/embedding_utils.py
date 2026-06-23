"""
app/utils/embedding_utils.py
Funciones para generar embeddings usando Ollama (mistral:latest).
"""

from app.config.ollama import get_embedding_client

# Cliente reutilizable: se instancia una vez y se comparte en todo el proceso
# para no crear conexiones multiples a Ollama innecesariamente.
_client = get_embedding_client()


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Genera los embeddings para una lista de textos en una sola llamada
    a Ollama (mas eficiente que llamar uno por uno).

    Retorna una lista de vectores de 1024 dimensiones, en el mismo orden
    que la lista de entrada.

    Usado por data_ingest_service.py para embeddings de chunks al subir PDFs.
    """
    return _client.embed_documents(texts)


def generate_query_embedding(query: str) -> list[float]:
    """
    Genera el embedding de una consulta de usuario (una sola cadena).

    Retorna un vector de 1024 dimensiones.
    Usado por main_service.py para buscar chunks similares en pgvector.
    """
    return _client.embed_query(query)