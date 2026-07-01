"""
app/models/pdf_model.py
Representacion de la tabla `pdfs`.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Pdf:
    id:            str
    filename:      str
    filepath:      str
    uploaded_user: str | None = None
    total_pages:   int | None = None
    total_chunks:  int | None = None
    uploaded_at:   datetime | None = None

    @staticmethod
    def from_row(row: dict) -> "Pdf":
        return Pdf(
            id=str(row["id"]),
            filename=row["filename"],
            filepath=row["filepath"],
            uploaded_user=str(row["uploaded_user"]) if row.get("uploaded_user") else None,
            total_pages=row.get("total_pages"),
            total_chunks=row.get("total_chunks"),
            uploaded_at=row.get("uploaded_at"),
        )