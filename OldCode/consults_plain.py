from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime
import hashlib
import re
from typing import List, Dict

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ========== CONFIGURACIÓN OPTIMIZADA ==========
OLLAMA_MODEL = "mistral:latest"
OLLAMA_URL = "http://10.90.28.157:11434"
CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_storage")
COLLECTION_NAME = "universidad_docs"

# Configuración de chunking optimizada
CHUNK_SIZE = 1000           # Más contexto por chunk
CHUNK_OVERLAP = 200         # Mayor solapamiento para continuidad
MIN_CHUNK_SIZE = 100        # Evitar chunks muy pequeños

# ========== INICIALIZACIÓN ==========
app = Flask(__name__)
CORS(app)

embeddings = OllamaEmbeddings(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
db = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings
)

def preprocess_text(text: str) -> str:
    """
    Preprocesa el texto para mejorar la calidad
    """
    # Normalizar espacios en blanco
    text = re.sub(r'\s+', ' ', text)
    
    # Eliminar caracteres extraños pero mantener puntuación importante
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\n\r]', '', text)
    
    # Normalizar saltos de línea
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()

def extract_keywords_from_text(text: str) -> List[str]:
    """
    Extrae palabras clave importantes del texto
    """
    # Palabras comunes a filtrar
    stopwords = {
        'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 
        'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del',
        'los', 'las', 'una', 'como', 'más', 'pero', 'sus', 'me', 'hasta'
    }
    
    # Extraer palabras de 3+ caracteres
    words = re.findall(r'\b[a-záéíóúüñ]{3,}\b', text.lower())
    keywords = [word for word in words if word not in stopwords]
    
    # Retornar palabras más frecuentes (máximo 10)
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:10]]

def intelligent_chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """Divide el texto de manera inteligente con metadata enriquecida
    """
    # Preprocesar texto
    clean_text = preprocess_text(text)
    
    # Configurar splitter con separadores más inteligentes
    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n\n",  # Separaciones de sección
            "\n\n",    # Párrafos
            "\n",      # Líneas
            ". ",      # Oraciones
            "–",       # Guiones largos
            "•",       # Bullets
            " "        # Espacios (último recurso)
        ],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        keep_separator=True
    )
    
    chunks = splitter.split_text(clean_text)
    
    # Filtrar chunks demasiado pequeños
    chunks = [chunk for chunk in chunks if len(chunk.strip()) >= MIN_CHUNK_SIZE]
    
    # Crear metadata enriquecida para cada chunk
    enriched_chunks = []
    for i, chunk in enumerate(chunks):
        # Generar hash único para el contenido
        content_hash = hashlib.md5(chunk.encode()).hexdigest()[:12]
        
        # Extraer keywords del chunk
        keywords = extract_keywords_from_text(chunk)
        
        # Identificar si contiene información estructurada
        has_numbers = bool(re.search(r'\d+', chunk))
        has_dates = bool(re.search(r'\d{4}|\d{1,2}/\d{1,2}', chunk))
        has_emails = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', chunk))
        has_phones = bool(re.search(r'\d{4}[-\s]\d{4}|\(\d{3}\)', chunk))
        
        chunk_info = {
            'content': chunk.strip(),
            'metadata': {
                'chunk_id': f"chunk_{content_hash}",
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_size': len(chunk),
                'keywords': ', '.join(keywords[:5]),  # String en lugar de lista
                'has_numbers': has_numbers,
                'has_dates': has_dates,
                'has_contact_info': has_emails or has_phones,
                'created_at': datetime.now().isoformat(),
                'content_hash': content_hash
            }
        }
        
        enriched_chunks.append(chunk_info)
    
    return enriched_chunks

def check_duplicate_content(content_hash: str) -> bool:
    """Verifica si el contenido ya existe en la base de datos"""
    try:
        # Buscar por hash en metadata
        results = db.get(where={"content_hash": content_hash})
        return len(results['ids']) > 0
    except:
        return False

def agregar_conocimiento_inteligente(texto: str, origen: str = "manual_input") -> Dict:
    """Agrega conocimiento con procesamiento inteligente y deduplicación"""
    # Validación básica
    if not texto or len(texto.strip()) < 50:
        raise ValueError("El texto debe tener al menos 50 caracteres")
    
    # Generar hash del documento completo
    doc_hash = hashlib.md5(texto.encode()).hexdigest()[:16]
    
    # Chunking inteligente
    chunk_info_list = intelligent_chunk_text(texto)
    
    if not chunk_info_list:
        raise ValueError("No se pudieron generar chunks válidos del texto")
    
    # Preparar documentos para insertar
    documents_to_add = []
    ids_to_add = []
    duplicates_found = 0
    
    for chunk_info in chunk_info_list:
        content = chunk_info['content']
        metadata = chunk_info['metadata']
        
        # Agregar metadata del documento
        metadata.update({
            'source': origen,
            'document_hash': doc_hash,
            'document_length': len(texto)
        })
        
        # Verificar duplicados
        if check_duplicate_content(metadata['content_hash']):
            duplicates_found += 1
            continue
        
        # Crear documento
        doc = Document(page_content=content, metadata=metadata)
        chunk_id = str(uuid.uuid4())
        
        documents_to_add.append(doc) 
        ids_to_add.append(chunk_id)
    
    # Insertar documentos no duplicados
    inserted_count = 0
    if documents_to_add:
        db.add_documents(documents_to_add, ids=ids_to_add)
        inserted_count = len(documents_to_add)
    
    # Estadísticas
    stats = {
        'total_chunks_processed': len(chunk_info_list),
        'chunks_inserted': inserted_count,
        'duplicates_skipped': duplicates_found,
        'document_hash': doc_hash,
        'source': origen,
        'processing_timestamp': datetime.now().isoformat()
    }
    
    return stats

# ========== ENDPOINTS ==========
@app.route("/teach", methods=["POST"])
def teach():
    """
    Endpoint principal para agregar conocimiento
    """
    try:
        # Parsear request
        if request.is_json:
            data = request.get_json()
            texto = data.get("texto", "").strip()
            origen = data.get("origen", "manual_input")
        else:
            texto = request.data.decode("utf-8").strip()
            origen = "manual_input"

        if not texto:
            return jsonify({"error": "No se recibió texto válido para enseñar"}), 400

        # Procesar y agregar conocimiento
        stats = agregar_conocimiento_inteligente(texto, origen)
        
        # Respuesta exitosa
        response = {
            "mensaje": "✅ Conocimiento procesado exitosamente",
            "estadisticas": stats,
            "success": True
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": f"Error de validación: {str(e)}", "success": False}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}", "success": False}), 500

@app.route("/stats", methods=["GET"])
def get_stats():
    """
    Obtiene estadísticas de la base de datos
    """
    try:
        # Contar documentos totales
        collection_count = db._collection.count()
        
        # Obtener algunos metadatos de muestra
        sample_docs = db.get(limit=5)
        
        sources = set()
        if sample_docs and 'metadatas' in sample_docs:
            for metadata in sample_docs['metadatas']:
                if metadata and 'source' in metadata:
                    sources.add(metadata['source'])
        
        stats = {
            "total_documents": collection_count,
            "sources_found": list(sources),
            "database_path": CHROMA_DIR,
            "collection_name": COLLECTION_NAME,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clear", methods=["POST"])
def clear_database():
    """
    Limpia la base de datos (usar con cuidado)
    """
    try:
        # Obtener confirmación
        data = request.get_json() or {}
        confirm = data.get("confirm", False)
        
        if not confirm:
            return jsonify({
                "error": "Para limpiar la base de datos, envía: {'confirm': true}",
                "warning": "Esta acción eliminará todos los documentos permanentemente"
            }), 400
        
        # Limpiar colección
        db.delete_collection()
        
        # Recrear colección vacía
        db = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )
        
        return jsonify({
            "mensaje": "Base de datos limpiada exitosamente",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    print(f"🚀 Iniciando API de almacenamiento optimizada en puerto 6000")
    print(f"📁 Directorio ChromaDB: {CHROMA_DIR}")
    print(f"📊 Configuración: chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    
    app.run(host="0.0.0.0", port=8000, debug=False)