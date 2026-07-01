"""
app/models/admin_model.py
Representacion de la tabla `admins`.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Admin:
    """
    Refleja exactamente las columnas de la tabla admins.
    Se usa para tipar los datos que devuelven los repositories
    en vez de trabajar con diccionarios crudos.
    """
    id:         str
    full_name:  str
    user_name:  str
    email:      str
    password:   str            # siempre almacenado como hash, nunca texto plano
    created_at: datetime | None = None

    @staticmethod
    def from_row(row: dict) -> "Admin":
        return Admin(
            id=str(row["id"]),
            full_name=row["full_name"],
            user_name=row["user_name"],
            email=row["email"],
            password=row["password"],
            created_at=row.get("created_at"),
        )