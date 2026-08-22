from unittest.mock import MagicMock, patch

import sys
import importlib
sys.modules["config"] = importlib.import_module("app.config")
sys.modules["model"] = importlib.import_module("app.model")

from app.repositories import chunk_repository


# ──────────────────────────────────────────────
# CHUNK REPOSITORY
# ──────────────────────────────────────────────


@patch("app.repositories.chunk_repository.get_connection")
def test_save_chunk_calls_from_row_and_returns_chunk(mock_get_conn):

    row = {"id": "c1", "embedding": MagicMock()}
    row["embedding"].to_list.return_value = [0.1, 0.2]
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = row
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    with patch("app.repositories.chunk_repository.Chunk") as mock_chunk:
        fake_chunk = MagicMock()
        mock_chunk.from_row.return_value = fake_chunk

        res = chunk_repository.save_chunk("pdf1", "text", [0.1], 0)

        mock_chunk.from_row.assert_called_once()
        assert res is fake_chunk
 


@patch("app.repositories.chunk_repository.get_connection")
def test_save_chunks_batch_saves_multiple_chunks(mock_get_conn):

    rows = [
        {"id": "c1", "embedding": MagicMock()},
        {"id": "c2", "embedding": MagicMock()},
    ]
    for r in rows:
        r["embedding"].to_list.return_value = [0.1]

    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.side_effect = rows
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    with patch("app.repositories.chunk_repository.Chunk") as mock_chunk:
        mock_chunk.from_row.side_effect = [MagicMock(), MagicMock()]

        saved = chunk_repository.save_chunks_batch("pdf1", [{"chunk_text": "a", "embedding": [0.1], "chunk_index": 0}, {"chunk_text": "b", "embedding": [0.2], "chunk_index": 1}])

        assert len(saved) == 2



@patch("app.repositories.chunk_repository.get_connection")
def test_search_similar_chunks_returns_rows(mock_get_conn):

    rows = [{"id": "c1", "chunk_text": "t1"}]
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = rows
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    res = chunk_repository.search_similar_chunks([0.1, 0.2], limit=1)

    assert res == rows



@patch("app.repositories.chunk_repository.get_connection")
def test_get_chunks_by_pdf_converts_rows_to_chunk_objects(mock_get_conn):

    rows = [{"id": "c1"}, {"id": "c2"}]
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = rows
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    with patch("app.repositories.chunk_repository.Chunk") as mock_chunk:
        fake1 = MagicMock()
        fake2 = MagicMock()
        mock_chunk.from_row.side_effect = [fake1, fake2]

        res = chunk_repository.get_chunks_by_pdf("pdf-1")

        assert res == [fake1, fake2]
