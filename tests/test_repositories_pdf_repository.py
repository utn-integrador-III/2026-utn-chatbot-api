from unittest.mock import MagicMock, patch

import sys
import importlib
sys.modules["config"] = importlib.import_module("app.config")
sys.modules["model"] = importlib.import_module("app.model")

from app.repositories import pdf_repository


# ──────────────────────────────────────────────
# PDF REPOSITORY
# ──────────────────────────────────────────────


def make_conn_mock(fetchone_return=None, fetchall_return=None, rowcount=1):
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = fetchone_return
    cur.fetchall.return_value = fetchall_return
    cur.rowcount = rowcount
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = None
    m = MagicMock()
    m.__enter__.return_value = conn
    return m, conn, cur


@patch("app.repositories.pdf_repository.get_connection")
@patch("app.repositories.pdf_repository.Pdf")
def test_save_pdf_returns_pdf_object(mock_pdf_class, mock_get_conn):

    row = {"id": "p1", "filename": "f"}
    cm, conn, cur = make_conn_mock(fetchone_return=row)
    mock_get_conn.return_value = cm
    fake_pdf = MagicMock()
    mock_pdf_class.from_row.return_value = fake_pdf

    res = pdf_repository.save_pdf("f", "/tmp/f", uploaded_user=None)

    mock_pdf_class.from_row.assert_called_once_with(row)
    assert res is fake_pdf



@patch("app.repositories.pdf_repository.get_connection")
def test_update_pdf_chunks_executes_update(mock_get_conn):

    cm, conn, cur = make_conn_mock()
    mock_get_conn.return_value = cm

    pdf_repository.update_pdf_chunks("pdf-1", 5)

    cur.execute.assert_called_once()



@patch("app.repositories.pdf_repository.get_connection")
@patch("app.repositories.pdf_repository.Pdf")
def test_find_pdf_by_filepath_and_get_pdf_return_none_and_object(mock_pdf_class, mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.side_effect = [None, {"id": "p2"}]
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm
    fake_pdf = MagicMock()
    mock_pdf_class.from_row.return_value = fake_pdf

    res_none = pdf_repository.find_pdf_by_filepath("/nope")
    res_obj = pdf_repository.get_pdf("p2")

    assert res_none is None
    assert res_obj is fake_pdf



@patch("app.repositories.pdf_repository.get_connection")
@patch("app.repositories.pdf_repository.Pdf")
def test_get_all_pdfs_maps_rows_to_pdf_objects(mock_pdf_class, mock_get_conn):

    rows = [{"id": "p1"}, {"id": "p2"}]
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = rows
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm
    fake1 = MagicMock()
    fake2 = MagicMock()
    mock_pdf_class.from_row.side_effect = [fake1, fake2]

    res = pdf_repository.get_all_pdfs()

    assert res == [fake1, fake2]
