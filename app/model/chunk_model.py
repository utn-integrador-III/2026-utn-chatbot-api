"""
app/models/chunk_model.py
Representacion de la tabla `document_chunks`.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Chunk:
    """
    Refleja exactamente las columnas de la tabla document_chunks.
    embedding es la lista de floats de 1024 dimensiones generada
    por Ollama (mistral:latest).
    """
    id:          str
    pdf_id:      str
    chunk_text:  str
    chunk_index: int
    embedding:   list[float] = field(default_factory=list)
    page_ref:    str | None = None
    created_at:  datetime | None = None

    @staticmethod
    def from_row(row: dict) -> "Chunk":
        """Construye un Chunk a partir de una fila de psycopg (dict_row)."""
        return Chunk(
            id=str(row["id"]),
            pdf_id=str(row["pdf_id"]),
            chunk_text=row["chunk_text"],
            chunk_index=row["chunk_index"],
            embedding=list(row["embedding"]) if row.get("embedding") else [],
            page_ref=row.get("page_ref"),
            created_at=row.get("created_at"),
        )