from unittest.mock import MagicMock, patch

import sys
import importlib
sys.modules["config"] = importlib.import_module("app.config")
sys.modules["model"] = importlib.import_module("app.model")

from app.repositories import keyword_repository


# ──────────────────────────────────────────────
# KEYWORD REPOSITORY
# ──────────────────────────────────────────────


@patch("app.repositories.keyword_repository.get_connection")
def test_save_keywords_returns_empty_on_blank(mock_get_conn):


    res = keyword_repository.save_keywords("chunk-1", ["", "   "])

    assert res == []



@patch("app.repositories.keyword_repository.get_connection")
def test_find_keywords_by_chunk_returns_list(mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = [{"keyword": "k1"}, {"keyword": "k2"}]
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    res = keyword_repository.find_keywords_by_chunk("chunk-1")

    assert res == ["k1", "k2"]



@patch("app.repositories.keyword_repository.get_connection")
@patch("app.repositories.keyword_repository.Keyword")
def test_save_keywords_inserts_and_returns_keywords(mock_keyword_class, mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.side_effect = [{"keyword": "k1"}, {"keyword": "k2"}]
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    k1 = MagicMock()
    k2 = MagicMock()
    mock_keyword_class.from_row.side_effect = [k1, k2]

    res = keyword_repository.save_keywords("chunk-1", ["k1", "k2"])

    assert res == [k1, k2]



@patch("app.repositories.keyword_repository.get_connection")
def test_find_keywords_by_pdf_returns_rows(mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    rows = [{"chunk_id": "c1", "keyword": "k1"}]
    cur.fetchall.return_value = rows
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    res = keyword_repository.find_keywords_by_pdf("pdf-1")

    assert res == rows
