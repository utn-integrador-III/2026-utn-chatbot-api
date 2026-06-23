"""
app/models/keyword_model.py
Representacion de la tabla `chunk_keyword`.
"""

from dataclasses import dataclass


@dataclass
class Keyword:
    """
    Refleja exactamente las columnas de la tabla chunk_keyword.
    Reemplaza el string concatenado ('matricula,fechas,carrera')
    que ChromaDB guardaba en los metadatos, por filas individuales.
    """
    id:       str
    chunk_id: str
    keyword:  str

    @staticmethod
    def from_row(row: dict) -> "Keyword":
        """Construye un Keyword a partir de una fila de psycopg (dict_row)."""
        return Keyword(
            id=str(row["id"]),
            chunk_id=str(row["chunk_id"]),
            keyword=row["keyword"],
        )