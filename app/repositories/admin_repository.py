"""
app/repositories/admin_repository.py
Acceso a la tabla `admins`. Todo el SQL de administradores vive aqui.
"""

from psycopg.rows import dict_row

from app.config.database import get_connection
from app.models.admin_model import Admin


def create_admin(full_name: str, user_name: str, email: str, hashed_password: str) -> Admin:
    """
    Inserta un nuevo administrador y retorna el objeto Admin creado.
    La contrasena debe llegar ya hasheada desde login_service.py;
    este repository nunca recibe ni almacena contrasenas en texto plano.
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO admins (full_name, user_name, email, password)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
                """,
                (full_name, user_name, email, hashed_password),
            )
            row = cur.fetchone()
        conn.commit()
    return Admin.from_row(row)


def find_admin_by_email(email: str) -> Admin | None:
    """
    Busca un administrador por email.
    Retorna None si no existe. Lo usa login_service.py para validar
    credenciales en el endpoint POST /login.
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE email = %s;",
                (email,),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def find_admin_by_username(user_name: str) -> Admin | None:
    """
    Busca un administrador por nombre de usuario.
    Retorna None si no existe. Lo usa login_service.py para validar
    que el user_name no este duplicado en POST /signup.
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE user_name = %s;",
                (user_name,),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def find_admin_by_id(admin_id: str) -> Admin | None:
    """
    Busca un administrador por su UUID.
    Lo usa login_service.py para resolver el perfil en GET /profile.
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE id = %s;",
                (admin_id,),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def delete_admin(admin_id: str) -> bool:
    """
    Elimina un administrador por su UUID.
    Retorna True si se elimino, False si no existia.
    Los PDFs subidos por este admin no se borran (ON DELETE SET NULL).
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