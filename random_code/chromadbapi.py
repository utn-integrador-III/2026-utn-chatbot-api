from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
import os
import uuid
import fitz  # PyMuPDF
import re
import hashlib
from datetime import datetime
from typing import List, Dict
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ================= CONFIGURACIÓN =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_storage")
COLLECTION_NAME = "universidad_docs"
OLLAMA_URL = "http://10.90.28.1:11434"
OLLAMA_MODEL = "mistral:latest"

# Chunking optimizado
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 100

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# ================= INICIALIZACIÓN =================
app = Flask(__name__)
CORS(app)

embeddings = OllamaEmbeddings(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
db = Chroma(collection_name=COLLECTION_NAME, persist_directory=CHROMA_DIR, embedding_function=embeddings)

# ================= FUNCIONES AUXILIARES =================
def extract_text_from_pdf(file_path):
    """Extrae texto de un PDF"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extrayendo texto del PDF: {e}")
        return ""

def preprocess_text(text: str) -> str:
    """Limpia y normaliza el texto"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\n\r]', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def extract_keywords_from_text(text: str) -> List[str]:
    stopwords = {'el','la','de','que','y','en','un','es','se','no','te','lo','le','da','su','por','son','con','para','al','del','los','las','una','como','más','pero','sus','me','hasta'}
    words = re.findall(r'\b[a-záéíóúüñ]{3,}\b', text.lower())
    keywords = [w for w in words if w not in stopwords]
    freq = {}
    for w in keywords:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:10]]

def intelligent_chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    clean_text = preprocess_text(text)
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n\n","\n\n","\n",". ","–","•"," "],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        keep_separator=True
    )
    chunks = [c for c in splitter.split_text(clean_text) if len(c.strip()) >= MIN_CHUNK_SIZE]
    enriched_chunks = []
    for i, chunk in enumerate(chunks):
        content_hash = hashlib.md5(chunk.encode()).hexdigest()[:12]
        keywords = extract_keywords_from_text(chunk)
        has_numbers = bool(re.search(r'\d+', chunk))
        has_dates = bool(re.search(r'\d{4}|\d{1,2}/\d{1,2}', chunk))
        has_emails = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', chunk))
        has_phones = bool(re.search(r'\d{4}[-\s]\d{4}|\(\d{3}\)', chunk))
        enriched_chunks.append({
            'content': chunk.strip(),
            'metadata': {
                'chunk_id': f"chunk_{content_hash}",
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_size': len(chunk),
                'keywords': ', '.join(keywords[:5]),
                'has_numbers': has_numbers,
                'has_dates': has_dates,
                'has_contact_info': has_emails or has_phones,
                'created_at': datetime.now().isoformat(),
                'content_hash': content_hash
            }
        })
    return enriched_chunks

def check_duplicate_content(content_hash: str) -> bool:
    try:
        results = db.get(where={"content_hash": content_hash})
        return len(results['ids']) > 0
    except:
        return False

def agregar_conocimiento_inteligente(texto: str, origen: str) -> Dict:
    if not texto or len(texto.strip()) < 50:
        raise ValueError("El texto debe tener al menos 50 caracteres")
    doc_hash = hashlib.md5(texto.encode()).hexdigest()[:16]
    chunk_info_list = intelligent_chunk_text(texto)
    if not chunk_info_list:
        raise ValueError("No se pudieron generar chunks válidos")
    documents_to_add = []
    ids_to_add = []
    duplicates_found = 0
    for chunk_info in chunk_info_list:
        content = chunk_info['content']
        metadata = chunk_info['metadata']
        metadata.update({
            'source': origen,
            'document_hash': doc_hash,
            'document_length': len(texto)
        })
        if check_duplicate_content(metadata['content_hash']):
            duplicates_found += 1
            continue
        doc = Document(page_content=content, metadata=metadata)
        documents_to_add.append(doc)
        ids_to_add.append(str(uuid.uuid4()))
    inserted_count = 0
    if documents_to_add:
        db.add_documents(documents_to_add, ids=ids_to_add)
        inserted_count = len(documents_to_add)
    return {
        'total_chunks_processed': len(chunk_info_list),
        'chunks_inserted': inserted_count,
        'duplicates_skipped': duplicates_found,
        'document_hash': doc_hash,
        'source': origen,
        'processing_timestamp': datetime.now().isoformat()
    }

# ================= RUTAS =================
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "OK", "message": "API ChromaDB funcionando"})

@app.route("/add_pdf", methods=["POST"])
def add_pdf():
    """
    Procesa PDF usando el mismo flujo que /teach
    """
    try:
        if "file" not in request.files:
            abort(400, description="No se adjuntó ningún archivo PDF")

        pdf_file = request.files["file"]

        # Guardar PDF en carpeta de uploads
        file_path = os.path.join(UPLOAD_DIR, pdf_file.filename)
        pdf_file.save(file_path)

        # Extraer texto del PDF
        extracted_text = extract_text_from_pdf(file_path)
        if not extracted_text:
            abort(500, description="No se pudo extraer texto del PDF")

        # Procesar con el pipeline inteligente
        stats = agregar_conocimiento_inteligente(extracted_text, origen=pdf_file.filename)

        return jsonify({
            "mensaje": "✅ PDF procesado con chunking inteligente",
            "archivo": pdf_file.filename,
            "estadisticas": stats
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route("/teach", methods=["POST"])
def teach():
    """
    Procesa texto plano con chunking inteligente
    """
    try:
        if request.is_json:
            data = request.get_json()
            texto = data.get("texto", "").strip()
            origen = data.get("origen", "manual_input")
        else:
            texto = request.data.decode("utf-8").strip()
            origen = "manual_input"

        if not texto:
            return jsonify({"error": "No se recibió texto válido"}), 400

        stats = agregar_conocimiento_inteligente(texto, origen)
        return jsonify({"mensaje": "✅ Texto procesado con chunking inteligente", "estadisticas": stats}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

# ================= MAIN =================
if __name__ == "__main__":
    print(f"🚀 API iniciada en puerto 6000")
    app.run(host="0.0.0.0", port=6000, debug=False)
