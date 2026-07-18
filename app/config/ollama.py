"""
app/config/ollama.py
-
"""

import os

import requests
from langchain_ollama import OllamaEmbeddings


# Dirección del servidor Ollama
OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_BASE_URL",
    "http://3.236.216.9:11434"
)


# Modelo utilizado para respuestas del chatbot
OLLAMA_CHAT_MODEL = os.environ.get(
    "OLLAMA_CHAT_MODEL",
    "mistralModelfile:latest"
)


# Modelo utilizado para crear embeddings
OLLAMA_EMBEDDING_MODEL = os.environ.get(
    "OLLAMA_EMBEDDING_MODEL",
    "nomic-embed-text"
)


# Endpoint para enviar mensajes a Ollama
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"


def get_embedding_client() -> OllamaEmbeddings:
    """
    Crea el cliente de embeddings de LangChain.

    Convierte textos en vectores que serán almacenados
    y consultados mediante pgvector.
    """

    return OllamaEmbeddings(
        model=OLLAMA_EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL
    )


def chat(messages: list[dict], timeout: int = 600) -> dict:
    """
    Envía una conversación al modelo de Ollama.

    Recibe los mensajes del usuario y retorna
    la respuesta generada por el modelo.
    """

    payload = {
        "model": OLLAMA_CHAT_MODEL,
        "messages": messages,
        "stream": False
    }

    response = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=timeout
    )

    response.raise_for_status()

    return response.json()