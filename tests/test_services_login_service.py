import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

import sys
import importlib
sys.modules["config"] = importlib.import_module("app.config")
sys.modules["repositories"] = importlib.import_module("app.repositories")
sys.modules["model"] = importlib.import_module("app.model")

from app.services import login_service


# ──────────────────────────────────────────────
# LOGIN SERVICE
# ──────────────────────────────────────────────


@patch("app.services.login_service.repo")
@patch("app.services.login_service._generate_token")
def test_signup_success_calls_repo_and_returns_token(mock_generate, mock_repo):

    mock_repo.email_exists.return_value = False
    mock_repo.username_exists.return_value = False
    fake_admin = MagicMock()
    fake_admin.to_public_dict.return_value = {"id": "admin-1", "user_name": "jdoe"}
    mock_repo.create_admin.return_value = fake_admin
    mock_generate.return_value = ("jwt-token", datetime.now(timezone.utc) + timedelta(minutes=30))

    result = login_service.signup(
        full_name="John Doe",
        user_name="jdoe",
        email="john@example.com",
        password="Valid1!pass",
        role="admin",
    )

    mock_repo.create_admin.assert_called_once()
    assert result["token"] == "jwt-token"


def test_signup_invalid_fields_raises_value_error():

    try:
        login_service.signup(full_name="J", user_name="x", email="bad", password="weak", role="invalid")
    except ValueError as e:
        assert "El nombre completo" in str(e) or "Rol inválido" in str(e)


@patch("app.services.login_service.repo")
def test_login_with_missing_credentials_raises_value_error(mock_repo):

    try:
        login_service.login(identifier="", password="")
    except ValueError as e:
        assert "Identificador y contraseña" in str(e)


@patch("app.services.login_service.repo")
@patch("app.services.login_service.bcrypt")
def test_login_success_returns_token(mock_bcrypt, mock_repo):

    fake_admin = MagicMock()
    fake_admin.password = "$2b$12$hashhash"
    fake_admin.to_public_dict.return_value = {"id": "admin-1", "user_name": "jdoe"}
    mock_repo.find_admin_by_identifier.return_value = fake_admin
    mock_bcrypt.checkpw.return_value = True
    with patch("app.services.login_service._generate_token", return_value=("t", datetime.now(timezone.utc))):
        result = login_service.login(identifier="jdoe", password="Valid1!pass")

    assert result["token"] == "t"


@patch("app.services.login_service.revoke_token")
def test_logout_decodes_and_calls_revoke(mock_revoke):

    fake_token = "raw.token"
    jti = "jti-123"
    future = datetime.now(timezone.utc) + timedelta(minutes=10)

    with patch.object(login_service, "jwt") as mock_jwt:
        mock_jwt.decode.return_value = {"exp": int(future.timestamp())}

        login_service.logout(jti=jti, token_raw=fake_token)

    mock_revoke.assert_called_once()


@patch("app.services.login_service.repo")
def test_delete_user_permission_denied(mock_repo):

    mock_repo.find_admin_by_id.return_value = MagicMock()

    try:
        login_service.delete_user(target_admin_id="a", requesting_admin_id="b", requesting_role="admin")
    except PermissionError as e:
        assert "No tienes permisos" in str(e)


@patch("app.services.login_service.repo")
def test_signup_duplicate_email_raises_value_error(mock_repo):

    mock_repo.email_exists.return_value = True

    try:
        login_service.signup(full_name="John Doe", user_name="johndoe", email="e@e.com", password="Valid1!pass")
    except ValueError as e:
        assert "correo electrónico" in str(e) or "registrado" in str(e)


@patch("app.services.login_service.repo")
def test_signup_duplicate_username_raises_value_error(mock_repo):

    mock_repo.email_exists.return_value = False
    mock_repo.username_exists.return_value = True

    try:
        login_service.signup(full_name="John Doe", user_name="u1", email="e@e.com", password="Valid1!pass")
    except ValueError as e:
        assert "nombre de usuario" in str(e) or "en uso" in str(e)


@patch("app.services.login_service.repo")
def test_login_raises_value_error_when_admin_not_found(mock_repo):

    mock_repo.find_admin_by_identifier.return_value = None

    try:
        login_service.login(identifier="nouser", password="pw")
    except ValueError as e:
        assert "Credenciales" in str(e) or "incorrectas" in str(e)


@patch("app.services.login_service.repo")
def test_delete_user_not_found_raises_value_error(mock_repo):

    mock_repo.find_admin_by_id.return_value = None

    try:
        login_service.delete_user(target_admin_id="x", requesting_admin_id="x", requesting_role="super_admin")
    except ValueError as e:
        assert "no existe" in str(e).lower() or "No se pudo" in str(e)


@patch("app.services.login_service.repo")
def test_delete_user_super_admin_can_delete_other(mock_repo):

    fake_target = MagicMock()
    fake_target.user_name = "target"
    mock_repo.find_admin_by_id.return_value = fake_target
    mock_repo.delete_admin.return_value = True

    res = login_service.delete_user(target_admin_id="t1", requesting_admin_id="s1", requesting_role="super_admin")

    assert "eliminado" in res["message"]

