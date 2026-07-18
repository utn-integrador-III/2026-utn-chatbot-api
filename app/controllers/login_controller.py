"""
app/controllers/login_controller.py
Capa HTTP para autenticación. Solo gestiona request/response.
Toda la lógica de negocio vive en login_service.py.
-
"""
from flask import request, jsonify
from services import login_service
from middleware.jwt_middleware import is_self_or_super_admin


# ──────────────────────────────────────────────
# POST /signup
# ──────────────────────────────────────────────

def signup():
    """
    Registra un nuevo administrador.

    Body JSON esperado:
    {
        "full_name": "John Doe",
        "user_name": "johndoe",
        "email":     "john@example.com",
        "password":  "SecurePass1!",
        "role":      "admin"            ← opcional, default: "admin"
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Se esperaba un body JSON."}), 400

    required_fields = ["full_name", "user_name", "email", "password"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({
            "error":   "Campos obligatorios faltantes.",
            "missing": missing,
        }), 400

    try:
        result = login_service.signup(
            full_name=data["full_name"],
            user_name=data["user_name"],
            email=data["email"],
            password=data["password"],
            role=data.get("role", "admin"),
        )
        return jsonify({
            "message":    "Administrador registrado exitosamente.",
            "admin":      result["admin"],
            "token":      result["token"],
            "expires_at": result["expires_at"],
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 409   # Conflict (duplicado o validación)


# ──────────────────────────────────────────────
# POST /login
# ──────────────────────────────────────────────

def login():
    """
    Autentica un administrador y devuelve un JWT.

    Body JSON esperado:
    {
        "identifier": "johndoe" OR "john@example.com",
        "password":   "SecurePass1!"
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Se esperaba un body JSON."}), 400

    identifier = data.get("identifier", "").strip()
    password   = data.get("password",   "").strip()

    if not identifier or not password:
        return jsonify({"error": "Los campos 'identifier' y 'password' son obligatorios."}), 400

    try:
        result = login_service.login(identifier=identifier, password=password)
        return jsonify({
            "message":    "Inicio de sesión exitoso.",
            "admin":      result["admin"],
            "token":      result["token"],
            "expires_at": result["expires_at"],
        }), 200

    except ValueError as e:
        # Mismo mensaje para credenciales inválidas (no revelar si existe o no el usuario)
        return jsonify({"error": "Credenciales incorrectas."}), 401


# ──────────────────────────────────────────────
# POST /logout
# ──────────────────────────────────────────────

def logout():
    """
    Revoca el token actual del administrador autenticado.
    Requiere JWT válido en el header Authorization.
    No necesita body.
    """
    jti       = getattr(request, "token_jti", None)
    token_raw = request.headers.get("Authorization", "").split(" ", 1)[-1]

    if not jti:
        return jsonify({"error": "No se pudo identificar el token."}), 400

    login_service.logout(jti=jti, token_raw=token_raw)

    return jsonify({"message": "Sesión cerrada correctamente."}), 200


# ──────────────────────────────────────────────
# DELETE /delete_user
# ──────────────────────────────────────────────

def delete_user():
    """
    Elimina un administrador del sistema.

    Body JSON esperado:
    {
        "admin_id": "uuid-del-admin-a-eliminar"
    }

    Reglas:
      - super_admin puede eliminar cualquier cuenta.
      - admin estándar solo puede eliminar su propia cuenta.
    """
    data = request.get_json(silent=True)

    if not data or not data.get("admin_id"):
        return jsonify({"error": "El campo 'admin_id' es obligatorio."}), 400

    target_admin_id    = data["admin_id"].strip()
    requesting_admin_id = getattr(request, "admin_id",   None)
    requesting_role     = getattr(request, "admin_role", "admin")

    try:
        result = login_service.delete_user(
            target_admin_id=target_admin_id,
            requesting_admin_id=requesting_admin_id,
            requesting_role=requesting_role,
        )
        return jsonify(result), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except ValueError as e:
        return jsonify({"error": str(e)}), 404