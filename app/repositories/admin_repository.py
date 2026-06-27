"""
app/repositories/admin_repository.py
Acceso a la tabla `admins`. Todo el SQL de administradores vive aqui.
"""

from psycopg.rows import dict_row

from config.database import get_connection
from app.models.admin_model import Admin


def create_admin(full_name: str, user_name: str, email: str, hashed_password: str) -> Admin:
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


def find_admin_by_id(admin_id: str) -> Admin | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM admins WHERE id = %s;",
                (admin_id,),
            )
            row = cur.fetchone()
    return Admin.from_row(row) if row else None


def delete_admin(admin_id: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM admins WHERE id = %s;",
                (admin_id,),
            )
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted