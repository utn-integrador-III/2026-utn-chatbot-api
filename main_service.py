# =========================
# Importación de librerías
# =========================
from click import prompt
from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
import requests
import os
import re
from datetime import datetime

# LangChain y Chroma para embeddings y recuperación
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document


# =========================
# Configuración inicial
# =========================
OLLAMA_MODEL = "mistralModelfile:latest"   # Modelo de embeddings y chat en Ollama
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_storage")
COLLECTION_NAME = "universidad_docs"

# Cliente de embeddings con Ollama
embedding = OllamaEmbeddings(model="mistral:latest", base_url="http://localhost:11434")

# Base de datos vectorial Chroma
db = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embedding
)

# Expresión regular para detectar fechas en español
MONTHS_ES = r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
DATE_REGEX = re.compile(
    rf"\b(\d{{1,2}}\s+de\s+{MONTHS_ES}\s+(de\s+\d{{4}})?)\b|\b\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}\b",
    re.IGNORECASE
)


# =========================
# Inicializar la API Flask
# =========================
app = Flask(__name__)
CORS(app)


# =========================
# Funciones auxiliares
# =========================
def _load_all_docs_from_chroma(max_batch=1000):
    """
    Carga todos los documentos almacenados en ChromaDB en lotes.
    Devuelve una lista de objetos Document con contenido y metadatos.
    """
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
    """
    Construye un recuperador BM25 (basado en frecuencia de palabras).
    Útil para complementar la búsqueda semántica de embeddings.
    """
    docs = _load_all_docs_from_chroma()
    if docs:
        retriever = BM25Retriever.from_documents(docs)
        retriever.k = 12
        return retriever
    return None


# Inicializar BM25 y VectorRetriever
bm25 = _build_bm25()
vector_retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 8, "fetch_k": 30, "lambda_mult": 0.7}
)


def _build_ensemble():
    """
    Combina BM25 y Chroma en un EnsembleRetriever.
    Si no hay BM25 disponible, usa solo Chroma.
    """
    if bm25:
        return EnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=[0.55, 0.45]
        )
    else:
        return vector_retriever


ensemble = _build_ensemble()


def _rerank_light(docs, question, top_k=5):
    """
    Re-ranking ligero para priorizar documentos relevantes.
    - Detecta fechas si la pregunta las solicita.
    - Da más peso a documentos que mencionen "I cuatrimestre".
    - Penaliza textos muy cortos o demasiado largos.
    Retorna los `top_k` documentos mejor puntuados.
    """
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
    """
    Construye el contexto final que se envía a Ollama.
    Incluye fragmentos de documentos con metadatos de fuente.
    Limita la longitud total para no sobrecargar el modelo.
    """
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
# Manejo de errores HTTP
# =========================
@app.errorhandler(400)
def BAD_REQUEST(error):
    return make_response(jsonify({'error': 'Solicitud incorrecta (Bad Request)'}), 400)

@app.errorhandler(404)
def NOT_FOUND(error):
    return make_response(jsonify({'error': 'Recurso no encontrado (Not Found)'}), 404)

@app.errorhandler(405)
def METHOD_NOT_ALLOWED(error):
    return make_response(jsonify({'error': 'Método HTTP no permitido (Method Not Allowed)'}), 405)

@app.errorhandler(429)
def TOO_MANY_REQUESTS(error):
    return make_response(jsonify({'error': 'Demasiadas solicitudes (Too Many Requests)'}), 429)

@app.errorhandler(500)
def INTERNAL_SERVER_ERROR(error):
    return make_response(jsonify({'error': 'Error interno del servidor (Internal Server Error)'}), 500)

@app.errorhandler(502)
def BAD_GATEWAY(error):
    return make_response(jsonify({'error': 'Respuesta inválida desde Ollama (Bad Gateway)'}), 502)

@app.errorhandler(503)
def SERVICE_UNAVAILABLE(error):
    return make_response(jsonify({'error': 'Servicio no disponible (Service Unavailable)'}), 503)

@app.errorhandler(504)
def GATEWAY_TIMEOUT(error):
    return make_response(jsonify({"error": "Tiempo de espera agotado con Ollama (Gateway Timeout)"}), 504)


# =========================
# Rutas principales
# =========================
@app.route("/", methods=["GET"])
def INDEX():
    """
    Ruta raíz para verificar el estado de la API.
    Devuelve JSON con descripción, autor y estado actual.
    """
    try:
        data = {
            "status_code": 200,
            "status_message": "Conexion exitosa a la API",
            "status_time": datetime.now().isoformat(),
            "body_message": {
                "description": "ApiChat, es una API-Rest para la conexion a Ollama",
                "author": "Grupo de Proyecto Integrador Pukeyackos"
            }
        }
    except Exception:
        abort(404)
    return jsonify(data)


@app.route("/savechat", methods=["POST"])
def SAVE_CHAT():
    """
    Procesa un chat del usuario con RAG:
    1. Recibe prompt del usuario.
    2. Busca documentos relevantes en Chroma + BM25.
    3. Re-rankea los resultados.
    4. Construye contexto con fragmentos.
    5. Envía prompt a Ollama y retorna la respuesta.
    """
    data = request.get_json()
    if not data or "prompt" not in data:
        print("Falta el campo 'prompt'")
        abort(400)

    user_prompt = data["prompt"]

    # Recuperar documentos relevantes
    try:
        candidates = ensemble.invoke(user_prompt)
    except Exception as e:
        print(f"Error buscando documentos relevantes: {e}")
        abort(500, description=f"Error buscando contexto: {e}")

    # Re-ranking y construcción de contextoca
    selected = _rerank_light(candidates, user_prompt, top_k=5)
    if not selected:
        context = "No se encontró información relevante."
        selected_meta = []
    else:
        context = _build_context(selected, max_chars=2500)
        selected_meta = [d.metadata for d in selected]

    # Prompt final para Ollama
    full_prompt = (
        f"Documentos:\n{context}\n\n"
        f"Pregunta: {user_prompt}"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [   
            { "role": "system", "content": """Eres un chatbot de asistencia universitaria de la Universidad Técnica Nacional (UTN).
                                              Responde únicamente sobre temas universitarios: matrícula y fechas importantes, carreras, requisitos y grados,
                                              servicios estudiantiles, calendarios académicos e información oficial universitaria.
                                              Responde siempre en español. No inventes datos; si no hay información suficiente, responde que no lo sabes.
                                              Cabe aclararte que la pagina oficial de la UTN es https://www.utn.ac.cr.
                                              Quiero que seas consciente con las respuestas que vayas a generar.
                                              Si la pregunta no trata sobre los temas permitidos, responde:
                                              'Lo siento, esa pregunta no está relacionada con temas universitarios y no puedo responderla.'
                                              No almacenes ni reveles información personal proporcionada por los usuarios.
                                              Siempre que uses información documental, indica el nombre del documento o enlace.\n\n
                                           """ },
            { "role": "user", "content": full_prompt }
        ],
        "stream": False
    }

    # Enviar a Ollama
    try:
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=600)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        abort(500, description=f"Error consultando a Ollama: {e}")
        
    # Respuesta final
    return jsonify({
        "user_prompt": user_prompt,
        "context_used": context,
        "selected_docs": selected_meta,
        **result
    })


@app.route("/refresh_bm25", methods=["POST"])
def REFRESH_BM25():
    """
    Reconstruye el índice BM25 y el EnsembleRetriever.
    Útil cuando se agregan nuevos documentos a Chroma.
    """
    global bm25, ensemble
    bm25 = _build_bm25()
    ensemble = _build_ensemble()
    return jsonify({"message": "BM25 refrescado", "docs_count": len(_load_all_docs_from_chroma())})


# =========================
# Ejecutar servidor
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
