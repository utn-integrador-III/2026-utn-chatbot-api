"""
app/routes/data_ingest_routes.py
Definicion de rutas para la ingestión de documentos PDF.

Endpoints:
    POST /add_pdf → sube, procesa e indexa un PDF en pgvector
    GET  /add_pdf → lista todos los PDFs indexados

Las rutas protegidas requieren JWT valido (jwt_middleware).
"""

from flask import Blueprint

from controllers.data_ingest_controller import add_pdf, list_pdfs
from middleware.jwt_middleware import jwt_required

data_ingest_bp = Blueprint("data_ingest", __name__)

# POST /add_pdf: solo administradores autenticados pueden subir PDFs
data_ingest_bp.add_url_rule(
    "/add_pdf",
    view_func=jwt_required(add_pdf),
    methods=["POST"],
)

# GET /list_pdfs: lista los PDFs indexados (protegido tambien por JWT)
data_ingest_bp.add_url_rule(
    "/list_pdfs",
    view_func=jwt_required(list_pdfs),
    methods=["GET"],
)