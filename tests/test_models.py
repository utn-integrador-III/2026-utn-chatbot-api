from app.model.admin_model import Admin, AdminRole
from app.model.chunk_model import Chunk
from app.model.keyword_model import Keyword
from app.model.pdf_model import Pdf


def test_admin_from_row_creates_admin():
    row = {
        "id": "123",
        "full_name": "Usuario Prueba",
        "user_name": "usuario",
        "email": "usuario@test.com",
        "password_hash": "hash-falso",
        "role": "admin",
        "created_at": None,
    }

    admin = Admin.from_row(row)

    assert admin.id == "123"
    assert admin.full_name == "Usuario Prueba"
    assert admin.user_name == "usuario"
    assert admin.email == "usuario@test.com"
    assert admin.password == "hash-falso"
    assert admin.role == "admin"
    assert admin.created_at is None
    
def test_admin_public_dict_does_not_expose_password():
    admin = Admin(
        id="123",
        full_name="Usuario Prueba",
        user_name="usuario",
        email="usuario@test.com",
        password="hash-secreto",
        role=AdminRole.ADMIN,
        created_at=None,
    )

    result = admin.to_public_dict()

    assert result["id"] == "123"
    assert result["full_name"] == "Usuario Prueba"
    assert result["user_name"] == "usuario"
    assert result["email"] == "usuario@test.com"
    assert result["role"] == AdminRole.ADMIN

    assert "password" not in result
    assert "password_hash" not in result

def test_chunk_from_row():
    row = {
        "id": "chunk-1",
        "pdf_id": "pdf-1",
        "chunk_text": "Texto de prueba",
        "chunk_index": 0,
        "embedding": [0.1, 0.2, 0.3],
        "page_ref": "1",
        "created_at": None,
    }

    chunk = Chunk.from_row(row)

    assert chunk.id == "chunk-1"
    assert chunk.pdf_id == "pdf-1"
    assert chunk.chunk_text == "Texto de prueba"
    assert chunk.chunk_index == 0
    assert chunk.embedding == [0.1, 0.2, 0.3]
    assert chunk.page_ref == "1"

def test_keyword_from_row():
    row = {
        "id": "keyword-1",
        "chunk_id": "chunk-1",
        "keyword": "python",
    }

    keyword = Keyword.from_row(row)

    assert keyword.id == "keyword-1"
    assert keyword.chunk_id == "chunk-1"
    assert keyword.keyword == "python"

def test_pdf_from_row():
    row = {
        "id": "pdf-1",
        "filename": "documento.pdf",
        "filepath": "/uploads/documento.pdf",
        "uploaded_by": "admin-1",
        "total_pages": 10,
        "total_chunks": 25,
        "uploaded_at": None,
    }

    pdf = Pdf.from_row(row)

    assert pdf.id == "pdf-1"
    assert pdf.filename == "documento.pdf"
    assert pdf.filepath == "/uploads/documento.pdf"
    assert pdf.uploaded_user == "admin-1"
    assert pdf.total_pages == 10
    assert pdf.total_chunks == 25