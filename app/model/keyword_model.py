"""
app/models/keyword_model.py
Representacion de la tabla `chunk_keyword`.
"""

from dataclasses import dataclass


@dataclass
class Keyword:
    id:       str
    chunk_id: str
    keyword:  str

    @staticmethod
    def from_row(row: dict) -> "Keyword":
        return Keyword(
            id=str(row["id"]),
            chunk_id=str(row["chunk_id"]),
            keyword=row["keyword"],
        )