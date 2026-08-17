from unittest.mock import MagicMock, patch

import sys
import importlib
sys.modules["config"] = importlib.import_module("app.config")
sys.modules["model"] = importlib.import_module("app.model")

from app.repositories import admin_repository


# ──────────────────────────────────────────────
# ADMIN REPOSITORY
# ──────────────────────────────────────────────


@patch("app.repositories.admin_repository.get_connection")
@patch("app.repositories.admin_repository.Admin")
def test_create_admin_returns_admin_object(mock_admin_class, mock_get_conn):
    row = {"id": "a1", "user_name": "u"}
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = row
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm
    fake_admin = MagicMock()
    mock_admin_class.from_row.return_value = fake_admin

    res = admin_repository.create_admin("Full", "u", "e@e.com", "hash")

    mock_admin_class.from_row.assert_called_once_with(row)
    assert res is fake_admin



@patch("app.repositories.admin_repository.get_connection")
def test_delete_admin_returns_boolean(mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    cur.rowcount = 1
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    res = admin_repository.delete_admin("a1")

    assert res is True



@patch("app.repositories.admin_repository.get_connection")
def test_delete_admin_returns_false_when_no_row_deleted(mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    cur.rowcount = 0
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    res = admin_repository.delete_admin("a-missing")

    assert res is False



@patch("app.repositories.admin_repository.get_connection")
@patch("app.repositories.admin_repository.Admin")
def test_find_admin_by_email_and_username_return_none_when_missing(mock_admin_class, mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = None
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    res_email = admin_repository.find_admin_by_email("no@x.com")
    res_user = admin_repository.find_admin_by_username("nouser")

    assert res_email is None
    assert res_user is None



@patch("app.repositories.admin_repository.get_connection")
@patch("app.repositories.admin_repository.Admin")
def test_find_admin_by_identifier_and_id_return_object_when_present(mock_admin_class, mock_get_conn):

    row = {"id": "a2", "user_name": "u2"}
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = row
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm
    fake_admin = MagicMock()
    mock_admin_class.from_row.return_value = fake_admin

    res_ident = admin_repository.find_admin_by_identifier("ident")
    res_id = admin_repository.find_admin_by_id("a2")

    assert res_ident is fake_admin
    assert res_id is fake_admin



@patch("app.repositories.admin_repository.get_connection")
def test_email_and_username_exists_return_boolean(mock_get_conn):

    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.side_effect = [{"1": 1}, None]
    conn.cursor.return_value.__enter__.return_value = cur
    cm = MagicMock()
    cm.__enter__.return_value = conn
    mock_get_conn.return_value = cm

    email_exists = admin_repository.email_exists("e@e.com")
    username_exists = admin_repository.username_exists("u1")

    assert email_exists is True
    assert username_exists is False
