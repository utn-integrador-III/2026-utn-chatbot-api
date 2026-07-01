"""
app/repositories/admin_repository.py
Acceso a la tabla `admins`. Todo el SQL de administradores vive aquí.
"""
from psycopg.rows import dict_row
from config.database import get_connection
from app.models.admin_model import Admin, AdminRole

# ──────────────────────────────────────────────
# ESCRITURA
# ──────────────────────────────────────────────

def create_admin(
    full_name:       str,
    user_name:       str,
    email:           str,
    hashed_password: str,
    role:            str = AdminRole.ADMIN,
) -> Admin:
    """
    Inserta un nuevo administrador y devuelve el registro completo.
    La contraseña debe llegar ya hasheada (bcrypt).
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO admins (full_name, user_name, email, password, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (full_name, user_name, email, hashed_password, role),
            )
            row = cur.fetchone()
        conn.commit()
    return Admin.from_row(row)


def delete_admin(admin_id: str) -> bool:
    """
    Elimina un administrador por su UUID.
    Devuelve True si se borró al menos una fila.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM admins WHERE id = %s;",
                (admin_id,),
            )
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted


# ──────────────────────────────────────────────
# LECTURA
# ──────────────────────────────────────────────

def find_admin_by_email(email: str) -> Admin | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE email = %s;",
                (email,),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def find_admin_by_username(user_name: str) -> Admin | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE user_name = %s;",
                (user_name,),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def find_admin_by_identifier(identifier: str) -> Admin | None:
    """
    Busca un admin por email o por username en una sola consulta.
    Útil para el flujo de login donde el usuario puede ingresar cualquiera de los dos.
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE email = %s OR user_name = %s;",
                (identifier, identifier),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def find_admin_by_id(admin_id: str) -> Admin | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE id = %s;",
                (admin_id,),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def email_exists(email: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM admins WHERE email = %s LIMIT 1;",
                (email,),
            )
            return cur.fetchone() is not None


def username_exists(user_name: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM admins WHERE user_name = %s LIMIT 1;",
                (user_name,),
            )
            return cur.fetchone() is not None