import os
import re
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document

# Importar desde config: cliente de embeddings y función de chat
from config.ollama import get_embedding_client, chat

# =========================
# Configuración
# =========================
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chroma_storage")
COLLECTION_NAME = "universidad_docs"

SYSTEM_PROMPT = """Eres un chatbot de asistencia universitaria de la Universidad Técnica Nacional (UTN).
Responde únicamente sobre temas universitarios: matrícula y fechas importantes, carreras, requisitos y grados,
servicios estudiantiles, calendarios académicos e información oficial universitaria.
Responde siempre en español. No inventes datos; si no hay información suficiente, responde que no lo sabes.
Cabe aclararte que la pagina oficial de la UTN es https://www.utn.ac.cr.
Quiero que seas consciente con las respuestas que vayas a generar.
Si la pregunta no trata sobre los temas permitidos, responde:
'Lo siento, esa pregunta no está relacionada con temas universitarios y no puedo responderla.'
No almacenes ni reveles información personal proporcionada por los usuarios.
Siempre que uses información documental, indica el nombre del documento o enlace."""

MONTHS_ES = r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
DATE_REGEX = re.compile(
    rf"\b(\d{{1,2}}\s+de\s+{MONTHS_ES}\s+(de\s+\d{{4}})?)\b|\b\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}\b",
    re.IGNORECASE
)

# =========================
# Inicialización de recursos
# =========================

# Se obtiene el cliente de embeddings desde config/ollama.py
embedding = get_embedding_client()

db = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embedding
)

vector_retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 8, "fetch_k": 30, "lambda_mult": 0.7}
)


# =========================
# Funciones internas
# =========================
def _load_all_docs_from_chroma(max_batch=1000):
    """Carga todos los documentos almacenados en ChromaDB en lotes."""
    total = db._collection.count()
    docs = []
    offset = 0
    while offset < total:
        batch = db._collection.get(
            include=["documents", "metadatas"],
            limit=min(max_batch, total - offset),
            offset=offset
        )
        for i, text in enumerate(batch["documents"]):
            meta = batch["metadatas"][i] if batch["metadatas"] else {}
            docs.append(Document(page_content=text, metadata=meta))
        offset += len(batch["ids"])
    return docs


def _build_bm25():
    """Construye un recuperador BM25 a partir de los documentos en Chroma."""
    docs = _load_all_docs_from_chroma()
    if docs:
        retriever = BM25Retriever.from_documents(docs)
        retriever.k = 12
        return retriever
    return None


def _build_ensemble(bm25):
    """Combina BM25 y Chroma en un EnsembleRetriever."""
    if bm25:
        return EnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=[0.55, 0.45]
        )
    return vector_retriever


def _rerank_light(docs, question, top_k=5):
    """Re-ranking ligero para priorizar documentos relevantes."""
    q_tokens = set(re.findall(r"\w+", question.lower()))
    want_fecha = bool(DATE_REGEX.search(question) or any(w in question.lower() for w in ["cuándo", "cuando", "fecha"]))
    want_q1 = any(w in question.lower() for w in ["primer", "i cuatrimestre", "1er", "i-2025", "i 2025", "i-2026"])

    scored = []
    for d in docs:
        text = d.page_content.lower()
        words = set(re.findall(r"\w+", text))
        overlap = len(q_tokens & words) / max(1, len(q_tokens))
        date_bonus = 0.15 if (want_fecha and DATE_REGEX.search(text)) else 0.0
        q1_bonus = 0.15 if (want_q1 and re.search(r"\b(i|1er|primer)\s*cuatrimestre|\bi-20\d{2}\b", text, re.IGNORECASE)) else 0.0
        len_penalty = -0.05 if (len(text) < 80 or len(text) > 1800) else 0.0
        scored.append((overlap + date_bonus + q1_bonus + len_penalty, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_k]]


def _build_context(docs, max_chars=2500):
    """Construye el contexto final que se envía a Ollama."""
    parts = []
    total = 0
    for d in docs:
        snippet = d.page_content.strip()
        src = d.metadata.get("source", "desconocido")
        block = f"[Fuente: {src}]\n{snippet}"
        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > 50:
                parts.append(block[:remaining] + " …")
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)


# =========================
# Estado del retriever
# =========================
_bm25 = _build_bm25()
_ensemble = _build_ensemble(_bm25)


# =========================
# Servicios públicos
# =========================
def process_chat(user_prompt: str) -> dict:
    """
    Ejecuta el pipeline RAG completo:
    recuperación → re-ranking → contexto → Ollama → respuesta.
    Lanza excepciones en caso de error para que el controlador las maneje.
    """
    candidates = _ensemble.invoke(user_prompt)

    selected = _rerank_light(candidates, user_prompt, top_k=5)
    if not selected:
        context = "No se encontró información relevante."
        selected_meta = []
    else:
        context = _build_context(selected, max_chars=2500)
        selected_meta = [d.metadata for d in selected]

    full_prompt = f"Documentos:\n{context}\n\nPregunta: {user_prompt}"

    # Se usa config/ollama.py → chat() en lugar de requests.post directo
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": full_prompt}
    ]
    result = chat(messages)

    return {
        "user_prompt": user_prompt,
        "context_used": context,
        "selected_docs": selected_meta,
        **result
    }


def refresh_bm25() -> dict:
    """
    Reconstruye el índice BM25 y el EnsembleRetriever.
    Devuelve un dict con el conteo de documentos actualizados.
    """
    global _bm25, _ensemble
    _bm25 = _build_bm25()
    _ensemble = _build_ensemble(_bm25)
    docs_count = len(_load_all_docs_from_chroma())
    return {"message": "BM25 refrescado", "docs_count": docs_count}