"""
app/routes/login_routes.py
Define las rutas del módulo de autenticación (puerto 7005).
Aplica los middlewares correspondientes a cada endpoint.
"""
from flask import Blueprint
from controllers.login_controller import signup, login, logout, delete_user
from middleware.jwt_middleware import jwt_required, roles_required

login_bp = Blueprint("login", __name__)

# ──────────────────────────────────────────────
# RUTAS PÚBLICAS (sin autenticación)
# ──────────────────────────────────────────────

# POST /signup → registro de nuevo administrador
# Nota: en producción considera proteger este endpoint
# para que solo un super_admin pueda crear nuevos admins.
# Por ahora es público para permitir el primer registro del sistema.
login_bp.add_url_rule(
    "/signup",
    view_func=jwt_required(roles_required("super_admin")(signup)),
    methods=["POST"],
)

# POST /login → autenticación y emisión de token
login_bp.add_url_rule(
    "/login",
    view_func=login,
    methods=["POST"],
)

# ──────────────────────────────────────────────
# RUTAS PROTEGIDAS (requieren JWT válido)
# ──────────────────────────────────────────────

# POST /logout → revoca el token actual
login_bp.add_url_rule(
    "/logout",
    view_func=jwt_required(logout),
    methods=["POST"],
)

# DELETE /delete_user → elimina una cuenta de administrador
# Solo super_admin puede eliminar otras cuentas;
# un admin estándar solo puede eliminar la suya propia
# (la lógica de self-vs-other vive en el service)
login_bp.add_url_rule(
    "/delete_user",
    view_func=jwt_required(delete_user),
    methods=["DELETE"],
)
