import fitz

from app.utils.pdf_utils import (
    extract_text_from_pdf,
    count_pages,
)


def create_test_pdf(filepath):
    doc = fitz.open()

    page = doc.new_page()

    page.insert_text(
        (72, 72),
        "Este es un documento de prueba."
    )

    doc.save(filepath)
    doc.close()


def create_multi_page_pdf(filepath):
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text(
        (72, 72),
        "Contenido de la pagina uno."
    )

    page2 = doc.new_page()
    page2.insert_text(
        (72, 72),
        "Contenido de la pagina dos."
    )

    doc.save(filepath)
    doc.close()


def test_extract_text_from_pdf_returns_text_and_page_count(tmp_path):
    filepath = tmp_path / "test.pdf"

    create_test_pdf(str(filepath))

    text, total_pages = extract_text_from_pdf(
        str(filepath)
    )

    assert "documento de prueba" in text
    assert total_pages == 1


def test_extract_text_from_pdf_includes_page_marker(tmp_path):
    filepath = tmp_path / "test.pdf"

    create_test_pdf(str(filepath))

    text, total_pages = extract_text_from_pdf(
        str(filepath)
    )

    assert total_pages == 1
    assert "--- Página 1 ---" in text


def test_extract_text_from_pdf_handles_multiple_pages(tmp_path):
    filepath = tmp_path / "multiple.pdf"

    create_multi_page_pdf(str(filepath))

    text, total_pages = extract_text_from_pdf(
        str(filepath)
    )

    assert total_pages == 2
    assert "pagina uno" in text
    assert "pagina dos" in text


def test_extract_text_from_pdf_invalid_file_returns_empty_result(tmp_path):
    filepath = tmp_path / "does_not_exist.pdf"

    text, total_pages = extract_text_from_pdf(
        str(filepath)
    )

    assert text == ""
    assert total_pages == 0


def test_count_pages_returns_correct_number(tmp_path):
    filepath = tmp_path / "multiple.pdf"

    create_multi_page_pdf(str(filepath))

    result = count_pages(str(filepath))

    assert result == 2


def test_count_pages_invalid_file_returns_zero(tmp_path):
    filepath = tmp_path / "does_not_exist.pdf"

    result = count_pages(str(filepath))

    assert result == 0