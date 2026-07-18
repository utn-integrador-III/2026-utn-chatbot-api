"""
app/config/settings.py
-
"""

import os
from dotenv import load_dotenv


# =========================
# Configuración de seguridad
# =========================

# Clave utilizada para crear y validar tokens JWT.
# En producción debe configurarse mediante variable de entorno.
load_dotenv()
 
JWT_SECRET             = os.environ["JWT_SECRET"] # Falla si no está definida
JWT_ALGORITHM          = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", 60))
 
DATABASE_URL = os.environ["DATABASE_URL"]

# =========================
# Archivos PDF
# =========================

# Carpeta donde se almacenan temporalmente los PDFs cargados.
UPLOAD_FOLDER = os.environ.get(
    "UPLOAD_FOLDER",
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "uploads"
    )
)


# ===========================
# Procesamiento de documentos
# ===========================

# Tamaño de los fragmentos de texto generados
# antes de crear los embeddings.
CHUNK_SIZE = int(
    os.environ.get("CHUNK_SIZE", "1000")
)


# Cantidad de caracteres compartidos entre fragmentos.
# Ayuda a mantener contexto entre partes del documento.
CHUNK_OVERLAP = int(
    os.environ.get("CHUNK_OVERLAP", "200")
)


# =========================
# Búsqueda vectorial
# =========================

# Cantidad de resultados obtenidos desde pgvector.
VECTOR_SEARCH_K = int(
    os.environ.get("VECTOR_SEARCH_K", "8")
)


# Cantidad de resultados utilizados por búsqueda tradicional BM25.
# Se mantiene por compatibilidad con la lógica anterior.
BM25_K = int(
    os.environ.get("BM25_K", "12")
)


# Cantidad final de documentos seleccionados después del re-ranking.
RERANK_TOP_K = int(
    os.environ.get("RERANK_TOP_K", "5")
)


# Máximo de caracteres enviados como contexto al modelo Ollama.
MAX_CONTEXT_CHARS = int(
    os.environ.get(
        "MAX_CONTEXT_CHARS",
        "3000"
    )
)


# =========================
# Servidor Flask
# =========================

# Puerto donde se ejecuta la API.
FLASK_PORT = int(
    os.environ.get("FLASK_PORT", "5005")
)
