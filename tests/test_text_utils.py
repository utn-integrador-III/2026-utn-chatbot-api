from app.utils.text_utils import (
    preprocess_text,
    split_into_chunks,
)


def test_preprocess_text_removes_extra_spaces():
    text = "Hola     mundo"

    result = preprocess_text(text)

    assert result == "Hola mundo"


def test_preprocess_text_removes_unsupported_characters():
    text = "Hola @#$% mundo"

    result = preprocess_text(text)

    assert "@" not in result
    assert "#" not in result
    assert "$" not in result
    assert "%" not in result


def test_preprocess_text_preserves_supported_punctuation():
    text = "Hola, mundo. ¿Cómo estás? (Bien)"

    result = preprocess_text(text)

    assert "," in result
    assert "." in result
    assert "?" in result
    assert "(" in result
    assert ")" in result


def test_preprocess_text_strips_text():
    text = "   Hola mundo   "

    result = preprocess_text(text)

    assert result == "Hola mundo"


def test_preprocess_empty_text():
    result = preprocess_text("")

    assert result == ""


def test_split_into_chunks_returns_list():
    text = "Este es un texto de prueba."

    result = split_into_chunks(text)

    assert isinstance(result, list)


def test_split_into_chunks_contains_expected_fields():
    text = "Este es un texto de prueba."

    result = split_into_chunks(text)

    assert len(result) == 1

    chunk = result[0]

    assert "chunk_text" in chunk
    assert "chunk_index" in chunk
    assert "page_ref" in chunk


def test_split_into_chunks_assigns_chunk_index():
    text = "Este es un texto de prueba."

    result = split_into_chunks(text)

    assert result[0]["chunk_index"] == 0


def test_split_into_chunks_detects_page_reference():
    text = "--- Página 5 ---\nEste contenido pertenece a la página cinco."

    result = split_into_chunks(text)

    assert len(result) >= 1
    assert result[0]["page_ref"] == "5"


def test_split_into_chunks_without_page_has_none():
    text = "Este texto no tiene marcador de página."

    result = split_into_chunks(text)

    assert result[0]["page_ref"] is None