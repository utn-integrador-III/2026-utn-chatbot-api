from io import BytesIO
from unittest.mock import patch, MagicMock

import sys
import importlib
sys.modules["config"] = importlib.import_module("app.config")
sys.modules["repositories"] = importlib.import_module("app.repositories")
sys.modules["utils"] = importlib.import_module("app.utils")
sys.modules["model"] = importlib.import_module("app.model")

from app.services import data_ingest_service


# ──────────────────────────────────────────────
# DATA INGEST SERVICE
# ──────────────────────────────────────────────


@patch("app.services.data_ingest_service.pdf_utils")
@patch("app.services.data_ingest_service.pdf_repository")
def test_process_pdf_when_no_text_saves_pdf_with_warning(mock_pdf_repo, mock_pdf_utils, tmp_path):

    
    fileobj = MagicMock()
    filename = "doc.pdf"
    mock_pdf_utils.extract_text_from_pdf.return_value = ("", 3)
    fake_pdf = MagicMock()
    fake_pdf.id = "pdf-1"
    mock_pdf_repo.save_pdf.return_value = fake_pdf

    result = data_ingest_service.process_pdf(fileobj, filename, admin_id="admin-1")

    assert result["pdf_id"] == "pdf-1"
    assert result["total_chunks"] == 0
    assert "warning" in result



@patch("app.services.data_ingest_service.embedding_utils")
@patch("app.services.data_ingest_service.keyword_repository")
@patch("app.services.data_ingest_service.keyword_utils")
@patch("app.services.data_ingest_service.chunk_repository")
@patch("app.services.data_ingest_service.text_utils")
@patch("app.services.data_ingest_service.pdf_utils")
@patch("app.services.data_ingest_service.pdf_repository")
def test_process_pdf_happy_path_saves_chunks(
    mock_pdf_repo, mock_pdf_utils, mock_text_utils, mock_chunk_repo, mock_keyword_utils, mock_keyword_repo, mock_embedding
):

    
    fileobj = MagicMock()
    filename = "doc.pdf"
    mock_pdf_utils.extract_text_from_pdf.return_value = ("some text", 2)
    mock_text_utils.preprocess_text.return_value = "clean"
    mock_text_utils.split_into_chunks.return_value = [
        {"chunk_text": "a", "chunk_index": 0},
        {"chunk_text": "b", "chunk_index": 1},
    ]
    mock_embedding.generate_embeddings.return_value = [[0.1], [0.2]]
    fake_pdf = MagicMock()
    fake_pdf.id = "pdf-2"
    mock_pdf_repo.save_pdf.return_value = fake_pdf
    saved_chunk = MagicMock()
    saved_chunk.id = "chunk-1"
    mock_chunk_repo.save_chunk.side_effect = [saved_chunk, saved_chunk]
    mock_keyword_utils.extract_keywords.return_value = ["kw1"]

    result = data_ingest_service.process_pdf(fileobj, filename, admin_id=None)

    assert result["pdf_id"] == "pdf-2"
    assert result["total_chunks"] == 2



@patch("app.services.data_ingest_service.embedding_utils")
@patch("app.services.data_ingest_service.pdf_repository")
@patch("app.services.data_ingest_service.pdf_utils")
def test_process_pdf_embedding_raises_propagates(mock_pdf_utils, mock_pdf_repo, mock_embedding):

    
    fileobj = MagicMock()
    filename = "doc.pdf"
    mock_pdf_utils.extract_text_from_pdf.return_value = ("some text", 1)
    fake_pdf = MagicMock()
    fake_pdf.id = "pdf-x"
    mock_pdf_repo.save_pdf.return_value = fake_pdf
    mock_embedding.generate_embeddings.side_effect = Exception("Embedding failure")

    try:
        data_ingest_service.process_pdf(fileobj, filename)
    except Exception as e:
        assert "Embedding failure" in str(e)



@patch("app.services.data_ingest_service.pdf_repository")
def test_get_all_pdfs_formats_dates_and_fields(mock_pdf_repo):

    
    fake1 = MagicMock()
    fake1.id = "p1"
    fake1.filename = "f1"
    fake1.total_pages = 1
    fake1.total_chunks = 0
    fake1.uploaded_at = None

    fake2 = MagicMock()
    fake2.id = "p2"
    fake2.filename = "f2"
    fake2.total_pages = 2
    fake2.total_chunks = 3
    from datetime import datetime, timezone
    fake2.uploaded_at = datetime.now(timezone.utc)

    mock_pdf_repo.get_all_pdfs.return_value = [fake1, fake2]

    res = data_ingest_service.get_all_pdfs()

    assert res[0]["uploaded_at"] is None
    assert "filename" in res[1]
