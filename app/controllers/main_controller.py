from flask import request, jsonify, abort
from services.main_service import process_chat, refresh_bm25


def save_chat():
    """
    POST /savechat
    Recibe { "prompt": "..." } y retorna la respuesta del modelo con contexto RAG.
    """
    data = request.get_json()

    if not data or "prompt" not in data:
        abort(400)

    user_prompt = data["prompt"]

    try:
        result = process_chat(user_prompt)
    except Exception as e:
        print(f"[main_controller] Error en process_chat: {e}")
        abort(500)

    return jsonify(result)


def refresh_bm25_index():
    """
    POST /refresh_bm25
    Reconstruye el índice BM25 y el EnsembleRetriever con los documentos actuales de Chroma.
    """
    try:
        result = refresh_bm25()
    except Exception as e:
        print(f"[main_controller] Error en refresh_bm25: {e}")
        abort(500)

    return jsonify(result)