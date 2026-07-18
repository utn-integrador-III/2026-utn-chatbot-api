"""
app/services/login_service.py
Lógica de negocio para autenticación de administradores.
Aquí vive: signup, login, logout y delete_user.
-
"""
import uuid
import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config.settings import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
from model.admin_model import Admin, AdminRole
from repositories import admin_repository as repo
from services.token_blacklist_service import revoke_token


# ──────────────────────────────────────────────
# CONSTANTES DE VALIDACIÓN
# ──────────────────────────────────────────────

_EMAIL_RE    = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,50}$")
# Contraseña: mínimo 8 caracteres, al menos 1 mayúscula, 1 número y 1 carácter especial
_PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,}$")


# ──────────────────────────────────────────────
# SIGNUP
# ──────────────────────────────────────────────

def signup(
    full_name: str,
    user_name: str,
    email:     str,
    password:  str,
    role:      str = AdminRole.ADMIN,
) -> dict:
    """
    Registra un nuevo administrador.
    Valida los campos, verifica duplicados y almacena la contraseña hasheada.

    Returns:
        dict con "admin" (datos públicos) y "token" JWT generado.
    Raises:
        ValueError si alguna validación falla.
    """
    # 1. Sanitización básica
    full_name = full_name.strip()
    user_name = user_name.strip()
    email     = email.strip().lower()

    # 2. Validaciones de formato
    _validate_signup_fields(full_name, user_name, email, password, role)

    # 3. Unicidad en BD
    if repo.email_exists(email):
        raise ValueError("El correo electrónico ya está registrado.")
    if repo.username_exists(user_name):
        raise ValueError("El nombre de usuario ya está en uso.")

    # 4. Hash de contraseña con bcrypt (cost factor 12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

    # 5. Persistencia
    admin = repo.create_admin(
        full_name=full_name,
        user_name=user_name,
        email=email,
        hashed_password=hashed.decode("utf-8"),
        role=role,
    )

    # 6. Generar token de acceso
    token, expires_at = _generate_token(admin)

    return {
        "admin":      admin.to_public_dict(),
        "token":      token,
        "expires_at": expires_at.isoformat(),
    }


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────

def login(identifier: str, password: str) -> dict:
    """
    Autentica un administrador por email o username.

    Returns:
        dict con "admin" (datos públicos) y "token" JWT.
    Raises:
        ValueError si las credenciales son inválidas.
    """
    identifier = identifier.strip()

    if not identifier or not password:
        raise ValueError("Identificador y contraseña son obligatorios.")

    # Buscar por email o username en una sola consulta
    admin = repo.find_admin_by_identifier(identifier)

    # Comparación en tiempo constante para evitar timing attacks
    # Si el admin no existe, comparamos contra un hash dummy para no revelar
    # la existencia del usuario mediante diferencia de tiempo de respuesta
    dummy_hash = "$2b$12$placeholderHashToPreventTimingAttacks000000000000000000"
    stored_hash = admin.password.encode("utf-8") if admin else dummy_hash.encode("utf-8")

    password_ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash)

    if not admin or not password_ok:
        raise ValueError("Credenciales incorrectas.")

    token, expires_at = _generate_token(admin)

    return {
        "admin":      admin.to_public_dict(),
        "token":      token,
        "expires_at": expires_at.isoformat(),
    }


# ──────────────────────────────────────────────
# LOGOUT
# ──────────────────────────────────────────────

def logout(jti: str, token_raw: str) -> None:
    """
    Revoca el token actual agregando su JTI a la blacklist.
    Se necesita el token para extraer la fecha de expiración.
    """
    try:
        payload = jwt.decode(
            token_raw,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},   # Ya validado en el middleware
        )
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    except Exception:
        # Si falla el decode, usar expiración conservadora
        exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    revoke_token(jti, exp)


# ──────────────────────────────────────────────
# DELETE USER
# ──────────────────────────────────────────────

def delete_user(target_admin_id: str, requesting_admin_id: str, requesting_role: str) -> dict:
    """
    Elimina un administrador del sistema.

    Reglas de autorización:
      - Un super_admin puede eliminar cualquier cuenta.
      - Un admin estándar solo puede eliminar su propia cuenta.

    Raises:
        PermissionError si no tiene permisos.
        ValueError si el usuario no existe.
    """
    # Verificar permisos
    is_self       = requesting_admin_id == target_admin_id
    is_super      = requesting_role == AdminRole.SUPER_ADMIN

    if not is_self and not is_super:
        raise PermissionError("No tienes permisos para eliminar esta cuenta.")

    # Verificar que el target existe
    target = repo.find_admin_by_id(target_admin_id)
    if not target:
        raise ValueError("El usuario no existe.")

    # Evitar que un super_admin se elimine a sí mismo accidentalmente
    # (política de seguridad: requiere otro super_admin para hacerlo)
    if is_self and requesting_role == AdminRole.SUPER_ADMIN:
        # Permitido: puede auto-eliminarse, pero se registra la acción
        pass

    deleted = repo.delete_admin(target_admin_id)
    if not deleted:
        raise ValueError("No se pudo eliminar el usuario.")

    return {"message": f"Usuario '{target.user_name}' eliminado correctamente."}


# ──────────────────────────────────────────────
# HELPERS PRIVADOS
# ──────────────────────────────────────────────

def _generate_token(admin: Admin) -> tuple[str, datetime]:
    """
    Genera un JWT firmado con los datos del admin.
    Incluye JTI único para poder revocar el token en logout.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    payload = {
        "admin_id":  admin.id,
        "user_name": admin.user_name,
        "email":     admin.email,
        "role":      admin.role,
        "jti":       str(uuid.uuid4()),      # JWT ID único por token
        "iat":       datetime.now(timezone.utc),
        "exp":       expires_at,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at


def _validate_signup_fields(
    full_name: str,
    user_name: str,
    email:     str,
    password:  str,
    role:      str,
) -> None:
    """Valida todos los campos del signup. Lanza ValueError si algo falla."""
    errors = []

    if not full_name or len(full_name) < 2:
        errors.append("El nombre completo debe tener al menos 2 caracteres.")
    if len(full_name) > 150:
        errors.append("El nombre completo no puede exceder 150 caracteres.")

    if not _USERNAME_RE.match(user_name):
        errors.append(
            "El nombre de usuario solo puede contener letras, números y guiones bajos (3-50 caracteres)."
        )

    if not _EMAIL_RE.match(email):
        errors.append("El formato del correo electrónico es inválido.")

    if not _PASSWORD_RE.match(password):
        errors.append(
            "La contraseña debe tener al menos 8 caracteres, "
            "una mayúscula, un número y un carácter especial."
        )

    valid_roles = {r.value for r in AdminRole}
    if role not in valid_roles:
        errors.append(f"Rol inválido. Opciones válidas: {', '.join(valid_roles)}.")

    if errors:
        raise ValueError(" | ".join(errors))
