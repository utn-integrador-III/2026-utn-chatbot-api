"""
app/repositories/chunk_repository.py
Acceso a la tabla `document_chunks`. Todo el SQL de chunks y
busquedas semanticas con pgvector vive aqui.
"""

from psycopg.rows import dict_row

from config.database import get_connection
from model.chunk_model import Chunk


def save_chunk(
    pdf_id: str,
    chunk_text: str,
    embedding: list[float],
    chunk_index: int,
    page_ref: str | None = None,
) -> Chunk:
    """
    Guarda un chunk de texto con su embedding y retorna el objeto Chunk.
    Llamado por data_ingest_service.py una vez por cada fragmento del PDF.
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO document_chunks (pdf_id, chunk_text, embedding, chunk_index, page_ref)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (pdf_id, chunk_text, embedding, chunk_index, page_ref),
            )
            row = cur.fetchone()
        conn.commit()
    return Chunk.from_row(row)


def save_chunks_batch(pdf_id: str, chunks: list[dict]) -> list[Chunk]:
    saved: list[Chunk] = []

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for chunk in chunks:
                cur.execute(
                    """
                    INSERT INTO document_chunks (pdf_id, chunk_text, embedding, chunk_index, page_ref)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *;
                    """,
                    (
                        pdf_id,
                        chunk["chunk_text"],
                        chunk["embedding"],
                        chunk["chunk_index"],
                        chunk.get("page_ref"),
                    ),
                )
                saved.append(Chunk.from_row(cur.fetchone()))
        conn.commit()

    return saved


def search_similar_chunks(query_embedding: list[float], limit: int = 5) -> list[dict]:

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    dc.id,
                    dc.pdf_id,
                    dc.chunk_text,
                    dc.chunk_index,
                    dc.page_ref,
                    p.filename AS source,
                    dc.embedding <=> %s AS distance
                FROM document_chunks dc
                LEFT JOIN pdfs p ON p.id = dc.pdf_id
                ORDER BY dc.embedding <=> %s
                LIMIT %s;
                """,
                (query_embedding, query_embedding, limit),
            )
            return cur.fetchall()


def get_chunks_by_pdf(pdf_id: str) -> list[Chunk]:
    """
    Retorna todos los chunks de un PDF ordenados por su indice.
    Util para depuracion y para reconstruir el texto original.
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM document_chunks
                WHERE pdf_id = %s
                ORDER BY chunk_index;
                """,
                (pdf_id,),
            )
            rows = cur.fetchall()
    return [Chunk.from_row(r) for r in rows]