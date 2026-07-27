"""
app/middleware/jwt_middleware.py
Protege endpoints administrativos validando el JWT.
Incluye control de acceso basado en roles (RBAC) y blacklist de tokens revocados.
-
"""
import jwt
from functools import wraps
from flask import request, jsonify
from config.settings import JWT_SECRET, JWT_ALGORITHM
from services.token_blacklist_service import is_token_revoked


# ──────────────────────────────────────────────
# DECORADOR BASE: valida token y carga payload
# ──────────────────────────────────────────────

def jwt_required(f):
    """
    Valida que el request tenga un JWT válido, no expirado y no revocado.
    Inyecta en el request:
        - request.admin_id  → UUID del admin autenticado
        - request.admin_role → rol del admin (para RBAC)
        - request.token_jti  → JTI del token (para logout)
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token no proporcionado."}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido."}), 401

        # Verificar si el token fue revocado (logout previo)
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            return jsonify({"error": "Token revocado. Inicia sesión nuevamente."}), 401

        # Inyectar datos del admin autenticado en el contexto del request
        request.admin_id   = payload.get("admin_id")
        request.admin_role = payload.get("role", "admin")
        request.token_jti  = jti

        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────
# DECORADOR RBAC: restringe por rol
# ──────────────────────────────────────────────

def roles_required(*allowed_roles: str):
    """
    Restringe el acceso a endpoints según el rol del admin autenticado.
    Debe usarse DESPUÉS de @jwt_required.

    Uso:
        @jwt_required
        @roles_required("super_admin")
        def delete_user(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            admin_role = getattr(request, "admin_role", None)
            if admin_role not in allowed_roles:
                return jsonify({
                    "error": "Acceso denegado. No tienes permisos para esta acción.",
                    "required_roles": list(allowed_roles),
                    "your_role": admin_role,
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ──────────────────────────────────────────────
# HELPER: verifica si el usuario autenticado
# es el mismo que el recurso solicitado o es super_admin
# ──────────────────────────────────────────────

def is_self_or_super_admin(target_admin_id: str) -> bool:
    """
    Verifica permisos: permite la acción si el admin autenticado
    es el propio usuario o tiene rol super_admin.
    """
    return (
        getattr(request, "admin_id", None) == target_admin_id
        or getattr(request, "admin_role", None) == "super_admin"
    )