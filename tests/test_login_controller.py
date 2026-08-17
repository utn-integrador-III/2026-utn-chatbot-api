 
import json
from unittest.mock import patch
from flask import Flask, request
import sys
import importlib

config_pkg = importlib.import_module("app.config")
sys.modules["config"] = config_pkg
for sub in ("settings", "ollama", "database"):
    try:
        sys.modules[f"config.{sub}"] = importlib.import_module(f"app.config.{sub}")
    except Exception:
        pass

services_pkg = importlib.import_module("app.services")
sys.modules["services"] = services_pkg
try:
    sys.modules["services.login_service"] = importlib.import_module(
        "app.services.login_service"
    )
except Exception:
    pass

try:
    repos_pkg = importlib.import_module("app.repositories")
    sys.modules["repositories"] = repos_pkg
    for sub in ("chunk_repository", "keyword_repository", "pdf_repository"):
        try:
            sys.modules[f"repositories.{sub}"] = importlib.import_module(f"app.repositories.{sub}")
        except Exception:
            pass
except Exception:
    pass

try:
    model_pkg = importlib.import_module("app.model")
    sys.modules["model"] = model_pkg
    try:
        sys.modules["model.admin_model"] = importlib.import_module("app.model.admin_model")
    except Exception:
        pass
except Exception:
    pass

try:
    utils_pkg = importlib.import_module("app.utils")
    sys.modules["utils"] = utils_pkg
    try:
        sys.modules["utils.embedding_utils"] = importlib.import_module("app.utils.embedding_utils")
    except Exception:
        pass
except Exception:
    pass

try:
    mw_pkg = importlib.import_module("app.middleware")
    sys.modules["middleware"] = mw_pkg
    try:
        sys.modules["middleware.jwt_middleware"] = importlib.import_module(
            "app.middleware.jwt_middleware"
        )
    except Exception:
        pass
except Exception:
    pass

from app.controllers.login_controller import signup, login, logout, delete_user

app = Flask(__name__)


# ──────────────────────────────────────────────
# signup
# ──────────────────────────────────────────────

def test_signup_without_json_body_returns_400():
    with app.test_request_context("/signup", method="POST"):
        response, status = signup()

    assert status == 400
    assert response.json["error"] == "Se esperaba un body JSON."


def test_signup_with_missing_fields_returns_400_with_missing_list():
    payload = {"full_name": "John Doe", "user_name": "johndoe"}

    with app.test_request_context(
        "/signup", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response, status = signup()

    assert status == 400
    assert response.json["error"] == "Campos obligatorios faltantes."
    assert "email" in response.json["missing"]
    assert "password" in response.json["missing"]


@patch("app.controllers.login_controller.login_service.signup")
def test_signup_success_returns_201_with_token(mock_signup):
    mock_signup.return_value = {
        "admin": {"id": "admin-1", "user_name": "johndoe"},
        "token": "jwt-token",
        "expires_at": "2026-01-01T00:00:00",
    }
    payload = {
        "full_name": "John Doe",
        "user_name": "johndoe",
        "email": "john@example.com",
        "password": "SecurePass1!",
    }

    with app.test_request_context(
        "/signup", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response, status = signup()

    assert status == 201
    assert response.json["message"] == "Administrador registrado exitosamente."
    assert response.json["token"] == "jwt-token"
    mock_signup.assert_called_once_with(
        full_name="John Doe",
        user_name="johndoe",
        email="john@example.com",
        password="SecurePass1!",
        role="admin",
    )


@patch("app.controllers.login_controller.login_service.signup")
def test_signup_duplicate_user_returns_409(mock_signup):
    mock_signup.side_effect = ValueError("El usuario ya existe.")
    payload = {
        "full_name": "John Doe",
        "user_name": "johndoe",
        "email": "john@example.com",
        "password": "SecurePass1!",
    }

    with app.test_request_context(
        "/signup", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response, status = signup()

    assert status == 409
    assert response.json["error"] == "El usuario ya existe."


# ──────────────────────────────────────────────
# login
# ──────────────────────────────────────────────

def test_login_without_json_body_returns_400():
    with app.test_request_context("/login", method="POST"):
        response, status = login()

    assert status == 400
    assert response.json["error"] == "Se esperaba un body JSON."


def test_login_with_missing_credentials_returns_400():
    payload = {"identifier": "johndoe"}

    with app.test_request_context(
        "/login", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response, status = login()

    assert status == 400
    assert response.json["error"] == "Los campos 'identifier' y 'password' son obligatorios."


@patch("app.controllers.login_controller.login_service.login")
def test_login_success_returns_200_with_token(mock_login):
    mock_login.return_value = {
        "admin": {"id": "admin-1", "user_name": "johndoe"},
        "token": "jwt-token",
        "expires_at": "2026-01-01T00:00:00",
    }
    payload = {"identifier": "johndoe", "password": "SecurePass1!"}

    with app.test_request_context(
        "/login", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response, status = login()

    assert status == 200
    assert response.json["message"] == "Inicio de sesión exitoso."
    assert response.json["token"] == "jwt-token"
    mock_login.assert_called_once_with(identifier="johndoe", password="SecurePass1!")


@patch("app.controllers.login_controller.login_service.login")
def test_login_invalid_credentials_returns_401_generic_message(mock_login):
    mock_login.side_effect = ValueError("Usuario no encontrado.")
    payload = {"identifier": "johndoe", "password": "wrong-password"}

    with app.test_request_context(
        "/login", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response, status = login()

    assert status == 401
    assert response.json["error"] == "Credenciales incorrectas."


# ──────────────────────────────────────────────
# logout
# ──────────────────────────────────────────────

def test_logout_without_token_jti_returns_400():
    with app.test_request_context("/logout", method="POST"):
        response, status = logout()

    assert status == 400
    assert response.json["error"] == "No se pudo identificar el token."


@patch("app.controllers.login_controller.login_service.logout")
def test_logout_success_returns_200(mock_logout):
    with app.test_request_context(
        "/logout", method="POST", headers={"Authorization": "Bearer valid-token"}
    ):
        request.token_jti = "jti-abc"

        response, status = logout()

    assert status == 200
    assert response.json["message"] == "Sesión cerrada correctamente."
    mock_logout.assert_called_once_with(jti="jti-abc", token_raw="valid-token")


# ──────────────────────────────────────────────
# delete_user
# ──────────────────────────────────────────────

def test_delete_user_without_admin_id_returns_400():
    with app.test_request_context("/delete_user", method="DELETE"):
        response, status = delete_user()

    assert status == 400
    assert response.json["error"] == "El campo 'admin_id' es obligatorio."


@patch("app.controllers.login_controller.login_service.delete_user")
def test_delete_user_success_returns_200(mock_delete_user):
    mock_delete_user.return_value = {"message": "Administrador eliminado correctamente."}
    payload = {"admin_id": "admin-2"}

    with app.test_request_context(
        "/delete_user", method="DELETE", data=json.dumps(payload), content_type="application/json"
    ):
        request.admin_id = "admin-1"
        request.admin_role = "super_admin"

        response, status = delete_user()

    assert status == 200
    assert response.json["message"] == "Administrador eliminado correctamente."
    mock_delete_user.assert_called_once_with(
        target_admin_id="admin-2", requesting_admin_id="admin-1", requesting_role="super_admin"
    )


@patch("app.controllers.login_controller.login_service.delete_user")
def test_delete_user_permission_error_returns_403(mock_delete_user):
    mock_delete_user.side_effect = PermissionError("No tienes permisos para esta acción.")
    payload = {"admin_id": "admin-2"}

    with app.test_request_context(
        "/delete_user", method="DELETE", data=json.dumps(payload), content_type="application/json"
    ):
        request.admin_id = "admin-1"
        request.admin_role = "admin"

        response, status = delete_user()

    assert status == 403
    assert response.json["error"] == "No tienes permisos para esta acción."


@patch("app.controllers.login_controller.login_service.delete_user")
def test_delete_user_not_found_returns_404(mock_delete_user):
    mock_delete_user.side_effect = ValueError("Administrador no encontrado.")
    payload = {"admin_id": "admin-inexistente"}

    with app.test_request_context(
        "/delete_user", method="DELETE", data=json.dumps(payload), content_type="application/json"
    ):
        request.admin_id = "admin-1"
        request.admin_role = "super_admin"

        response, status = delete_user()

    assert status == 404
    assert response.json["error"] == "Administrador no encontrado."