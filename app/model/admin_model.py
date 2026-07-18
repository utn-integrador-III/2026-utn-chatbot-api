"""
app/models/admin_model.py
Representación de la tabla `admins`.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AdminRole(str, Enum):
    """
    Roles disponibles para administradores.
    Permite control de acceso basado en roles (RBAC).
    """
    SUPER_ADMIN = "super_admin"  # Acceso total: puede crear/eliminar admins
    ADMIN       = "admin"        # Acceso estándar: gestión de datos del sistema


@dataclass
class Admin:
    """
    Refleja exactamente las columnas de la tabla admins.
    Se usa para tipar los datos devueltos por los repositories
    en vez de trabajar con diccionarios crudos.
    """
    id:         str
    full_name:  str
    user_name:  str
    email:      str
    password:   str                         # Siempre almacenado como hash bcrypt
    role:       str = AdminRole.ADMIN       # Rol por defecto: admin estándar
    created_at: datetime | None = None

    @staticmethod
    def from_row(row: dict) -> "Admin":
        return Admin(
            id=str(row["id"]),
            full_name=row["full_name"],
            user_name=row["user_name"],
            email=row["email"],
            password=row["password_hash"],
            role=row.get("role", AdminRole.ADMIN),
            created_at=row.get("created_at"),
        )

    def to_public_dict(self) -> dict:
        """
        Devuelve solo los campos seguros para exponer en respuestas HTTP.
        Nunca incluye el hash de contraseña.
        """
        return {
            "id":         self.id,
            "full_name":  self.full_name,
            "user_name":  self.user_name,
            "email":      self.email,
            "role":       self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }