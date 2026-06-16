# =======================================
# API para procesar PDFs y guardarlos en
# una base de datos vectorial con ChromaDB
# =======================================

import os
import re
import uuid
import fitz  # PyMuPDF para extracción de texto de PDFs
from datetime import datetime
from typing import List
from textwrap import wrap

from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# ========== CONFIGURACIÓN ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # Ruta absoluta al backend
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")          # Carpeta de PDFs subidos
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_storage") # Carpeta para almacenamiento de ChromaDB
COLLECTION_NAME = "universidad_docs"                    # Nombre de la colección en ChromaDB
OLLAMA_BASE_URL = "http://localhost:11434"              # URL de Ollama
OLLAMA_MODEL = "mistral:latest"                         # Modelo a usar en Ollama

# Crear carpetas si no existen
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)


# ========== INICIAR APP ==========
app = Flask(__name__)
CORS(app)


# ========== FUNCIONES AUXILIARES ==========
def preprocess_text(text: str) -> str:
    """
    Limpia y normaliza el texto extraído:
    - Normaliza espacios múltiples.
    - Elimina caracteres extraños manteniendo puntuación básica.
    - Reduce saltos de línea innecesarios.
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\n\r]', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def extract_keywords_from_text(text: str) -> List[str]:
    """
    Extrae palabras clave más frecuentes de un texto, 
    excluyendo stopwords comunes en español.
    """
    stopwords = {
        'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te',
        'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del',
        'los', 'las', 'una', 'como', 'más', 'pero', 'sus', 'me', 'hasta'
    }

    words = re.findall(r'\b[a-záéíóúüñ]{3,}\b', text.lower())
    keywords = [word for word in words if word not in stopwords]

    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:10]]


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrae texto de un archivo PDF con PyMuPDF,
    manteniendo separación por página.
    """
    try:
        doc = fitz.open(file_path)
        full_text = ""
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                text = " ".join(text.split())
                full_text += f"\n--- Página {page_num} ---\n{text}"
        doc.close()
        return full_text.strip()
    except Exception as e:
        print(f"Error extrayendo texto del PDF: {e}")
        return ""


def save_chunks_to_pdf(chunks, original_filename):
    """
    Guarda los chunks generados en un PDF para depuración.
    Cada chunk se escribe en una página distinta.
    """
    debug_pdf_path = os.path.join(UPLOAD_DIR, f"debug_chunks_{original_filename}.pdf")
    c = canvas.Canvas(debug_pdf_path, pagesize=A4)
    width, height = A4

    for i, chunk in enumerate(chunks):
        text_y = height - 50

        # Título del chunk
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, text_y, f"Chunk {i+1}")
        text_y -= 20
        c.setFont("Helvetica", 10)

        # Ajustar líneas para que quepan en la página
        wrapped_lines = wrap(chunk, 100)
        for line in wrapped_lines:
            if text_y < 50:  # Si llegamos al final de la página
                c.showPage()
                text_y = height - 50
                c.setFont("Helvetica", 10)
            c.drawString(50, text_y, line)
            text_y -= 15

        c.showPage()  # Forzar nueva página para el siguiente chunk

    c.save()
    print(f"PDF de depuración guardado en: {debug_pdf_path}")
    return debug_pdf_path


# ========== CONTROL DE ERRORES ==========
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


# ========== RUTAS ==========
@app.route("/", methods=["GET"])
def INDEX():
    """
    Endpoint raíz para comprobar conexión con la API.
    Devuelve estado, fecha y descripción de la API.
    """
    try:
        data = {
            "status_code": 200,
            "status_message": "Conexion exitosa a la API",
            "status_time": datetime.now().isoformat(),
            "body_message": {
                "description": "ApiChromaDB, es una API-Rest para la insercion de documentos PDF en una base de datos vectorial ChromaDB",
                "author": "Grupo de Proyecto Integrador Pukeyackos"
            }
        }
    except Exception as expc:
        abort(404)
    return jsonify(data)


@app.route("/add_pdf", methods=["POST"])
def ADD_PDF():
    """
    Sube un PDF, procesa su texto y lo guarda en ChromaDB.
    Flujo:
    1. Recibe el archivo PDF.
    2. Extrae y limpia el texto.
    3. Divide en chunks (fragmentos de texto) de forma semántica.
    4. Genera embeddings con Ollama.
    5. Inserta embeddings en ChromaDB.
    6. Guarda PDF de depuración con los chunks.
    7. Retorna información del proceso en JSON.
    """
    if "file" not in request.files:
        abort(400)

    pdf_file = request.files["file"]

    # Guardar archivo original
    file_path = os.path.join(UPLOAD_DIR, pdf_file.filename)
    pdf_file.save(file_path)

    # Extraer y procesar texto
    print("Inicia extracción de texto")
    extracted_text = extract_text_from_pdf(file_path)
    if not extracted_text:
        abort(500, description="No se pudo extraer texto del PDF")

    clean_text = preprocess_text(extracted_text)

    # División en chunks mejorada
    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n\n",  # Sección larga
            "\n\n",    # Párrafos
            ". ",      # Oraciones completas
            "\n",      # Líneas
            "; ",      # Listas
            " "        # Espacios (último recurso)
        ],
        chunk_size=2500,   # Tamaño más controlado de chunk
        chunk_overlap=400, # Mayor solapamiento para no perder contexto
        length_function=len,
        keep_separator=True
    )
    
    chunks = splitter.split_text(clean_text)
    print(f"Generados {len(chunks)} fragmentos.")

    # Inicializar embeddings
    print("Inicializando Embeddings")
    embedding = OllamaEmbeddings(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL
    )

    # Cargar/crear base vectorial
    print("Cargar base de datos Vectorial")
    db = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding
    )

    # Agregar chunks a la colección
    print("Agregando chunks a la coleccion")
    ids = []
    for chunk in chunks:
        doc_id = str(uuid.uuid4())
        keywords = extract_keywords_from_text(chunk)

        db.add_texts(
            texts=[chunk],
            metadatas=[{
                "source": pdf_file.filename,
                "keywords": "," .join(keywords)
            }],
            ids=[doc_id]
        )
        ids.append(doc_id)
    print("Chunks agregados exitosamente")
    
    save_chunks_to_pdf(chunks, pdf_file.filename)

    return jsonify({
        "message": "PDF procesado y agregado correctamente",
        "chunks": len(chunks),
        "ids": ids,
        "archivo": pdf_file.filename
    })


# ========== MAIN ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6005)
