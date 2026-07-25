"""
app/config/database.py
-
"""

import os

from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool


# Configuración de conexión obtenida desde variables de entorno
# Si no existen, utiliza valores por defecto.
PG_HOST     = os.environ.get("PG_HOST", "3.131.90.150")
PG_PORT     = os.environ.get("PG_PORT", "5432")
PG_DATABASE = os.environ.get("PG_DATABASE", "nova")
PG_USER     = os.environ.get("PG_USER", "nova_user")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "nova123")


# Cadena de conexión hacia PostgreSQL
CONNINFO = (
    f"host={PG_HOST} port={PG_PORT} dbname={PG_DATABASE} "
    f"user={PG_USER} password={PG_PASSWORD}"
)


def _configure_connection(conn) -> None:
    """
    Configura cada conexión del pool para reconocer
    el tipo de dato vector utilizado por pgvector.
    """
    register_vector(conn)


# Pool de conexiones a PostgreSQL.
# Permite mantener conexiones disponibles y reutilizarlas
# evitando abrir una nueva conexión por cada petición.
pool = ConnectionPool(
    conninfo=CONNINFO,
    min_size=2,
    max_size=10,
    configure=_configure_connection,
    open=True,
)


def get_connection():
    """
    Obtiene una conexión disponible del pool.

    Debe utilizarse con 'with' para liberar la conexión
    automáticamente después de utilizarla.

    Ejemplo:

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    return pool.connection()