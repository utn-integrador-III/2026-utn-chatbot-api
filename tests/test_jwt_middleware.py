from unittest.mock import patch

import jwt
from flask import Flask, request

from app.middleware.jwt_middleware import (
    jwt_required,
    roles_required,
    is_self_or_super_admin,
)

app = Flask(__name__)


def test_jwt_required_without_header_returns_401():
    @jwt_required
    def view():
        return "ok"

    with app.test_request_context("/"):
        response, status = view()

    assert status == 401
    assert response.json["error"] == "Token no proporcionado."


def test_jwt_required_header_without_bearer_returns_401():
    @jwt_required
    def view():
        return "ok"

    with app.test_request_context("/", headers={"Authorization": "Token abc123"}):
        response, status = view()

    assert status == 401
    assert response.json["error"] == "Token no proporcionado."


@patch("app.middleware.jwt_middleware.is_token_revoked", return_value=False)
@patch("app.middleware.jwt_middleware.jwt.decode")
def test_jwt_required_valid_token_injects_admin_data(mock_decode, mock_revoked):
    mock_decode.return_value = {"admin_id": "admin-123", "role": "super_admin", "jti": "jti-abc"}

    @jwt_required
    def view():
        return request.admin_id, request.admin_role, request.token_jti

    with app.test_request_context("/", headers={"Authorization": "Bearer valid-token"}):
        admin_id, admin_role, token_jti = view()

    assert admin_id == "admin-123"
    assert admin_role == "super_admin"
    assert token_jti == "jti-abc"


@patch("app.middleware.jwt_middleware.jwt.decode", side_effect=jwt.ExpiredSignatureError)
def test_jwt_required_expired_token_returns_401(mock_decode):
    @jwt_required
    def view():
        return "ok"

    with app.test_request_context("/", headers={"Authorization": "Bearer expired-token"}):
        response, status = view()

    assert status == 401
    assert response.json["error"] == "Token expirado."


@patch("app.middleware.jwt_middleware.jwt.decode", side_effect=jwt.InvalidTokenError)
def test_jwt_required_invalid_token_returns_401(mock_decode):
    @jwt_required
    def view():
        return "ok"

    with app.test_request_context("/", headers={"Authorization": "Bearer invalid-token"}):
        response, status = view()

    assert status == 401
    assert response.json["error"] == "Token inválido."


@patch("app.middleware.jwt_middleware.is_token_revoked", return_value=True)
@patch("app.middleware.jwt_middleware.jwt.decode")
def test_jwt_required_revoked_token_returns_401(mock_decode, mock_revoked):
    mock_decode.return_value = {"admin_id": "admin-123", "role": "admin", "jti": "jti-revoked"}

    @jwt_required
    def view():
        return "ok"

    with app.test_request_context("/", headers={"Authorization": "Bearer revoked-token"}):
        response, status = view()

    assert status == 401
    assert response.json["error"] == "Token revocado. Inicia sesión nuevamente."


def test_roles_required_allows_authorized_role():
    @roles_required("super_admin", "admin")
    def view():
        return "ok"

    with app.test_request_context("/"):
        request.admin_role = "admin"

        result = view()

    assert result == "ok"


def test_roles_required_rejects_unauthorized_role():
    @roles_required("super_admin")
    def view():
        return "ok"

    with app.test_request_context("/"):
        request.admin_role = "admin"

        response, status = view()

    assert status == 403
    assert response.json["error"] == "Acceso denegado. No tienes permisos para esta acción."
    assert response.json["required_roles"] == ["super_admin"]
    assert response.json["your_role"] == "admin"


def test_roles_required_without_role_in_request_rejects():
    @roles_required("admin")
    def view():
        return "ok"

    with app.test_request_context("/"):
        response, status = view()

    assert status == 403
    assert response.json["your_role"] is None


def test_is_self_or_super_admin_same_user_returns_true():
    with app.test_request_context("/"):
        request.admin_id = "admin-123"
        request.admin_role = "admin"

        result = is_self_or_super_admin("admin-123")

    assert result is True


def test_is_self_or_super_admin_super_admin_returns_true():
    with app.test_request_context("/"):
        request.admin_id = "admin-999"
        request.admin_role = "super_admin"

        result = is_self_or_super_admin("admin-123")

    assert result is True


def test_is_self_or_super_admin_other_user_not_super_admin_returns_false():
    with app.test_request_context("/"):
        request.admin_id = "admin-999"
        request.admin_role = "admin"

        result = is_self_or_super_admin("admin-123")

    assert result is False