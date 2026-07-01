"""
app/utils/keyword_utils.py
Extraccion de palabras clave de un texto.

"""

import re


# Stopwords tomadas exactamente del original (chromadbapi.py)
STOPWORDS_ES = {
    'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te',
    'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del',
    'los', 'las', 'una', 'como', 'más', 'pero', 'sus', 'me', 'hasta'
}


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:

    words = re.findall(r'\b[a-záéíóúüñ]{3,}\b', text.lower())
    keywords = [w for w in words if w not in STOPWORDS_ES]

    freq: dict[str, int] = {}
    for word in keywords:
        freq[word] = freq.get(word, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]