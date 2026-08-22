from io import BytesIO
from unittest.mock import patch
from flask import Flask
import sys
import importlib
config_pkg = importlib.import_module("app.config")
sys.modules["config"] = config_pkg
for sub in ("settings", "ollama", "database"):
    try:
        sys.modules[f"config.{sub}"] = importlib.import_module(f"app.config.{sub}")
    except Exception:
        pass

services_pkg = importlib.import_module("app.services")
sys.modules["services"] = services_pkg
try:
    sys.modules["services.data_ingest_service"] = importlib.import_module(
        "app.services.data_ingest_service"
    )
except Exception:
    pass

try:
    repos_pkg = importlib.import_module("app.repositories")
    sys.modules["repositories"] = repos_pkg
    for sub in ("chunk_repository", "keyword_repository", "pdf_repository"):
        try:
            sys.modules[f"repositories.{sub}"] = importlib.import_module(f"app.repositories.{sub}")
        except Exception:
            pass
except Exception:
    pass

try:
    model_pkg = importlib.import_module("app.model")
    sys.modules["model"] = model_pkg
    try:
        sys.modules["model.admin_model"] = importlib.import_module("app.model.admin_model")
    except Exception:
        pass
except Exception:
    pass

try:
    utils_pkg = importlib.import_module("app.utils")
    sys.modules["utils"] = utils_pkg
    try:
        sys.modules["utils.embedding_utils"] = importlib.import_module("app.utils.embedding_utils")
    except Exception:
        pass
except Exception:
    pass

from app.controllers.data_ingest_controller import add_pdf, list_pdfs

app = Flask(__name__)


# ──────────────────────────────────────────────
# add_pdf
# ──────────────────────────────────────────────

def test_add_pdf_without_file_returns_400():
    with app.test_request_context("/add_pdf", method="POST"):
        response, status = add_pdf()

    assert status == 400
    assert response.json["error"] == "No se encontró ningún archivo en la petición."


def test_add_pdf_with_empty_filename_returns_400():
    data = {"file": (BytesIO(b"contenido"), "")}

    with app.test_request_context(
        "/add_pdf", method="POST", data=data, content_type="multipart/form-data"
    ):
        response, status = add_pdf()

    assert status == 400
    assert response.json["error"] == "El nombre del archivo está vacío."


def test_add_pdf_with_non_pdf_extension_returns_400():
    data = {"file": (BytesIO(b"contenido"), "documento.txt")}

    with app.test_request_context(
        "/add_pdf", method="POST", data=data, content_type="multipart/form-data"
    ):
        response, status = add_pdf()

    assert status == 400
    assert response.json["error"] == "Solo se permiten archivos con extensión .pdf"


@patch("app.controllers.data_ingest_controller.data_ingest_service.process_pdf")
def test_add_pdf_success_returns_201(mock_process_pdf):
    mock_process_pdf.return_value = {
        "pdf_id": "pdf-1",
        "filename": "documento.pdf",
        "total_pages": 10,
        "total_chunks": 25,
    }
    data = {"file": (BytesIO(b"contenido"), "documento.pdf")}

    with app.test_request_context(
        "/add_pdf", method="POST", data=data, content_type="multipart/form-data"
    ):
        from flask import request
        request.admin_id = "admin-1"

        response, status = add_pdf()

    assert status == 201
    assert response.json["message"] == "PDF procesado e indexado correctamente."
    assert response.json["pdf_id"] == "pdf-1"
    assert response.json["total_pages"] == 10
    assert response.json["total_chunks"] == 25


@patch("app.controllers.data_ingest_controller.data_ingest_service.process_pdf")
def test_add_pdf_service_exception_returns_500(mock_process_pdf):
    mock_process_pdf.side_effect = Exception("Fallo al generar embeddings.")
    data = {"file": (BytesIO(b"contenido"), "documento.pdf")}

    with app.test_request_context(
        "/add_pdf", method="POST", data=data, content_type="multipart/form-data"
    ):
        response, status = add_pdf()

    assert status == 500
    assert "Fallo al generar embeddings." in response.json["error"]


# ──────────────────────────────────────────────
# list_pdfs
# ──────────────────────────────────────────────

@patch("app.controllers.data_ingest_controller.data_ingest_service.get_all_pdfs")
def test_list_pdfs_returns_200_with_pdfs(mock_get_all_pdfs):
    mock_get_all_pdfs.return_value = [
        {"id": "pdf-1", "filename": "documento.pdf"},
        {"id": "pdf-2", "filename": "manual.pdf"},
    ]

    with app.test_request_context("/list_pdfs", method="GET"):
        response, status = list_pdfs()

    assert status == 200
    assert response.json["total"] == 2
    assert len(response.json["pdfs"]) == 2


@patch("app.controllers.data_ingest_controller.data_ingest_service.get_all_pdfs")
def test_list_pdfs_service_exception_returns_500(mock_get_all_pdfs):
    mock_get_all_pdfs.side_effect = Exception("Error de conexión a la base de datos.")

    with app.test_request_context("/list_pdfs", method="GET"):
        response, status = list_pdfs()

    assert status == 500
    assert "Error de conexión a la base de datos." in response.json["error"]