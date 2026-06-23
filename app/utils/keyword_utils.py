"""
app/utils/keyword_utils.py
Extraccion de palabras clave de un texto.

La logica es identica al original (chromadbapi.py):
    - Regex: [a-záéíóúüñ]{3,}  (solo letras en espanol, minimo 3 chars)
    - Stopwords en espanol
    - Top 10 por frecuencia
"""

import re


# Stopwords tomadas exactamente del original (chromadbapi.py)
STOPWORDS_ES = {
    'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te',
    'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del',
    'los', 'las', 'una', 'como', 'más', 'pero', 'sus', 'me', 'hasta'
}


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    """
    Extrae las palabras clave mas frecuentes de un texto.

    Identica a extract_keywords_from_text() del original (chromadbapi.py):
        1. Tokeniza con regex [a-záéíóúüñ]{3,} (solo palabras en espanol)
        2. Filtra stopwords
        3. Calcula frecuencia
        4. Retorna el top max_keywords por frecuencia

    Retorna lista de strings en minusculas, sin duplicados.
    """
    words = re.findall(r'\b[a-záéíóúüñ]{3,}\b', text.lower())
    keywords = [w for w in words if w not in STOPWORDS_ES]

    freq: dict[str, int] = {}
    for word in keywords:
        freq[word] = freq.get(word, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]