"""
app/repositories/pdf_repository.py
Acceso a la tabla `pdfs`. Todo el SQL de documentos PDF vive aqui.
"""

from psycopg.rows import dict_row

from config.database import get_connection
from app.models.pdf_model import Pdf


def save_pdf(
    filename: str,
    filepath: str,
    uploaded_user: str | None = None,
    total_pages: int | None = None,
    total_chunks: int | None = None,
) -> Pdf:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO pdfs (uploaded_user, filename, filepath, total_pages, total_chunks)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (uploaded_user, filename, filepath, total_pages, total_chunks),
            )
            row = cur.fetchone()
        conn.commit()
    return Pdf.from_row(row)


def update_pdf_chunks(pdf_id: str, total_chunks: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pdfs SET total_chunks = %s WHERE id = %s;",
                (total_chunks, pdf_id),
            )
        conn.commit()


def find_pdf_by_filepath(filepath: str) -> Pdf | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM pdfs WHERE filepath = %s;",
                (filepath,),
            )
            row = cur.fetchone()
    return Pdf.from_row(row) if row else None


def get_pdf(pdf_id: str) -> Pdf | None:
    """Busca un PDF por su UUID."""
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM pdfs WHERE id = %s;", (pdf_id,))
            row = cur.fetchone()
    return Pdf.from_row(row) if row else None


def get_all_pdfs() -> list[Pdf]:
    """Retorna todos los PDFs ordenados del mas reciente al mas antiguo."""
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM pdfs ORDER BY uploaded_at DESC;")
            rows = cur.fetchall()
    return [Pdf.from_row(r) for r in rows]