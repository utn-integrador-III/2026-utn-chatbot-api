"""
app/repositories/keyword_repository.py
Acceso a la tabla `chunk_keyword`. Reemplaza el string concatenado
que ChromaDB guardaba en metadatos por filas normalizadas.
"""

from psycopg.rows import dict_row

from app.config.database import get_connection
from app.models.keyword_model import Keyword


def save_keywords(chunk_id: str, keywords: list[str]) -> list[Keyword]:
    clean = [k.strip() for k in keywords if k and k.strip()]
    if not clean:
        return []

    saved: list[Keyword] = []

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for keyword in clean:
                cur.execute(
                    """
                    INSERT INTO chunk_keyword (chunk_id, keyword)
                    VALUES (%s, %s)
                    RETURNING *;
                    """,
                    (chunk_id, keyword),
                )
                saved.append(Keyword.from_row(cur.fetchone()))
        conn.commit()

    return saved


def find_keywords_by_chunk(chunk_id: str) -> list[str]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT keyword FROM chunk_keyword WHERE chunk_id = %s;",
                (chunk_id,),
            )
            rows = cur.fetchall()
    return [row["keyword"] for row in rows]


def find_keywords_by_pdf(pdf_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT ck.chunk_id, ck.keyword
                FROM chunk_keyword ck
                INNER JOIN document_chunks dc ON dc.id = ck.chunk_id
                WHERE dc.pdf_id = %s
                ORDER BY ck.chunk_id;
                """,
                (pdf_id,),
            )
            return cur.fetchall()