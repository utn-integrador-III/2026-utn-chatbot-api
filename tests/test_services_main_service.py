from unittest.mock import patch, MagicMock

import sys
import importlib
sys.modules["config"] = importlib.import_module("app.config")
sys.modules["repositories"] = importlib.import_module("app.repositories")
sys.modules["utils"] = importlib.import_module("app.utils")

from app.services import main_service


# ──────────────────────────────────────────────
# MAIN SERVICE
# ──────────────────────────────────────────────


def test_build_context_with_no_chunks_returns_message():

    result = main_service.build_context([])

    assert "No se encontró información" in result



def test_build_context_with_chunks_concatenates_sources():

    chunks = [{"chunk_text": "texto1", "source": "doc1"}, {"chunk_text": "texto2", "source": "doc2"}]

    ctx = main_service.build_context(chunks)

    assert "Fuente: doc1" in ctx
    assert "texto2" in ctx



@patch("app.services.main_service.chat")
@patch("app.services.main_service.chunk_repository")
@patch("app.services.main_service.embedding_utils")
def test_process_chat_happy_path(mock_embedding, mock_chunks, mock_chat):

    mock_embedding.generate_query_embedding.return_value = [0.1]
    mock_chunks.search_similar_chunks.return_value = [{"chunk_text": "c1", "source": "s1"}]
    mock_chat.return_value = {"message": {"content": "respuesta"}}

    res = main_service.process_chat("¿hola?")

    assert res["answer"] == "respuesta"
    assert "context_used" in res
