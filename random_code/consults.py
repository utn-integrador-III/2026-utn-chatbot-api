from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import requests
import os
import re

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# +++ NUEVO: híbrido y re-ranker +++
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document

# ========== CONFIGURACIÓN ==========
OLLAMA_URL = "http://10.90.28.157:11434/api/chat"  # (no lo uso abajo; dejo tu conexión intacta)
OLLAMA_MODEL = "mistral:latest"
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_storage")
COLLECTION_NAME = "universidad_docs"

# ========== FLASK APP ==========
app = Flask(__name__)
CORS(app)

# ========== CHROMADB & EMBEDDINGS ==========
embedding = OllamaEmbeddings(model=OLLAMA_MODEL, base_url="http://10.90.28.157:11434")
db = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embedding
)

# ---------- Utilidades de recuperación ----------
MONTHS_ES = r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
DATE_REGEX = re.compile(rf"\b(\d{{1,2}}\s+de\s+{MONTHS_ES}\s+(de\s+\d{{4}})?)\b|\b\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}\b", re.IGNORECASE)

def _load_all_docs_from_chroma(max_batch=1000):
    """Carga todos los documentos de la colección para BM25 (solo texto + metadatos)."""
    total = db._collection.count()
    docs: list[Document] = []
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

# Construir BM25 al iniciar (rápido si el corpus no es gigante)
_all_docs_bm25 = _load_all_docs_from_chroma()
bm25 = BM25Retriever.from_documents(_all_docs_bm25)
bm25.k = 12  # candidatos BM25

# Retriever denso con MMR para diversidad
vector_retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 8,        # top finales por denso
        "fetch_k": 30, # candidatos previos a MMR
        "lambda_mult": 0.7
    }
)

# Ensemble: combinamos BM25 (léxico) + denso (semántico)
ensemble = EnsembleRetriever(
    retrievers=[bm25, vector_retriever],
    weights=[0.55, 0.45]  # BM25 prioriza exactitud de términos
)

def _rerank_light(docs: list[Document], question: str, top_k: int = 5):
    """Re-ranking ligero: overlap de keywords, bonus por fechas y por ‘primer/I cuatrimestre’."""
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
        # penaliza ruido muy corto/largo
        length = len(text)
        len_penalty = -0.05 if (length < 80 or length > 1800) else 0.0

        score = overlap + date_bonus + q1_bonus + len_penalty
        scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_k]]

def _build_context(docs: list[Document], max_chars: int = 2500):
    """Concatena contenido con límite de caracteres y etiqueta la fuente."""
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

# ========== RUTA PRINCIPAL ==========
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data or "prompt" not in data:
        abort(400, description="Falta el campo 'prompt'")

    user_question = data["prompt"]

    # 1) Recuperación híbrida (BM25 + denso MMR)
    try:
        candidates = ensemble.get_relevant_documents(user_question)  # mezcla de ambos mundos
    except Exception as e:
        abort(500, description=f"Error buscando contexto (ensemble): {e}")

    # 2) Re-ranking ligero especializado
    selected = _rerank_light(candidates, user_question, top_k=5)

    if not selected:
        context = "No se encontró información relevante."
        selected_meta = []
    else:
        context = _build_context(selected, max_chars=2500)
        selected_meta = [d.metadata for d in selected]

    # 3) Prompt a Ollama (sin inventar)
    full_prompt = (
        "Eres un asistente de la Universidad Técnica Nacional (UTN). "
        "Responde únicamente con base en los documentos proporcionados. "
        "No inventes datos; si no hay información suficiente, responde que no lo sabes.\n\n"
        f"Documentos:\n{context}\n\n"
        f"Pregunta: {user_question}"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        # Mantengo la URL que ya usabas en producción:
        response = requests.post("http://10.90.28.157:11434/api/generate", json=payload, timeout=600)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        abort(500, description=f"Error consultando a Ollama: {e}")

    return jsonify({
        "question": user_question,
        "context_used": context,
        "selected_docs": selected_meta,
        "response": result.get("response", "").strip()
    })

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)
