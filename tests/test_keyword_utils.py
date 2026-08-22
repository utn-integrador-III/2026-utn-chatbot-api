from app.utils.keyword_utils import extract_keywords


def test_extract_keywords_returns_words():
    text = "Python Flask PostgreSQL"

    result = extract_keywords(text)

    assert "python" in result
    assert "flask" in result
    assert "postgresql" in result


def test_extract_keywords_converts_text_to_lowercase():
    text = "PYTHON FLASK PostgreSQL"

    result = extract_keywords(text)

    assert "python" in result
    assert "flask" in result
    assert "postgresql" in result


def test_extract_keywords_removes_stopwords():
    text = "el sistema de chatbot y la base de datos"

    result = extract_keywords(text)

    assert "el" not in result
    assert "de" not in result
    assert "y" not in result
    assert "la" not in result


def test_extract_keywords_ignores_words_shorter_than_three_characters():
    text = "a al de la en es yo si api web"

    result = extract_keywords(text)

    assert "a" not in result
    assert "al" not in result
    assert "de" not in result
    assert "la" not in result
    assert "en" not in result
    assert "es" not in result


def test_extract_keywords_orders_by_frequency():
    text = (
        "python python python "
        "flask flask "
        "postgresql"
    )

    result = extract_keywords(text)

    assert result[0] == "python"
    assert result[1] == "flask"
    assert result[2] == "postgresql"


def test_extract_keywords_respects_max_keywords():
    text = (
        "python flask postgres ollama "
        "langchain chatbot database"
    )

    result = extract_keywords(text, max_keywords=3)

    assert len(result) == 3


def test_extract_keywords_empty_text_returns_empty_list():
    result = extract_keywords("")

    assert result == []