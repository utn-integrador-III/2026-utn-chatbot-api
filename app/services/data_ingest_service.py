"""
app/services/data_ingest_service.py
Logica de negocio para la ingestion de documentos PDF.

Basado en el flujo original de chromadbapi.py, adaptado a la nueva
arquitectura por capas (repositories, models, pgvector).

Flujo identico al original, solo cambia el destino de almacenamiento:
    Original : ChromaDB  (archivos locales SQLite + binarios)
    Nuevo    : PostgreSQL + pgvector (tabla document_chunks)

Pasos:
    1. Guardar el archivo fisico en uploads/
    2. Extraer texto con PyMuPDF (fitz), igual que el original
    3. Limpiar texto con preprocess_text(), igual que el original
    4. Dividir en chunks con los mismos parametros del original
       (chunk_size=2500, chunk_overlap=400, mismos separadores)
    5. Generar embeddings con Ollama (mistral:latest)
    6. Guardar chunks en `document_chunks` via chunk_repository
    7. Extraer keywords con la misma logica del original
    8. Guardar keywords en `chunk_keyword` via keyword_repository
    9. Actualizar total_chunks en `pdfs`
"""

import os

from app.config.settings import UPLOAD_FOLDER
from app.repositories import chunk_repository, keyword_repository, pdf_repository
from app.utils import embedding_utils, keyword_utils, pdf_utils, text_utils


def process_pdf(file, filename: str, admin_id: str | None = None) -> dict:
    """
    Ejecuta el pipeline completo de ingestion de un PDF.

    Parametros:
        file      : objeto de archivo de Flask (request.files['file'])
        filename  : nombre original del archivo (ej: "calendario_2025.pdf")
        admin_id  : UUID del administrador que sube el PDF (puede ser None)

    Retorna:
        dict con pdf_id, filename, total_pages, total_chunks.
        Si el PDF no tiene texto extraible, retorna total_chunks=0 y un warning.
    """

    # ── 1. Guardar archivo fisico en uploads/ ────────────────────────────────
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"[data_ingest_service] Archivo guardado: {filepath}")

    # ── 2. Extraer texto con PyMuPDF ─────────────────────────────────────────
    # Identico al original: usa fitz y mantiene marcadores "--- Pagina N ---"
    print("[data_ingest_service] Inicia extraccion de texto")
    raw_text, total_pages = pdf_utils.extract_text_from_pdf(filepath)

    if not raw_text:
        pdf_record = pdf_repository.save_pdf(
            filename=filename,
            filepath=filepath,
            uploaded_user=admin_id,
            total_pages=total_pages,
            total_chunks=0,
        )
        return {
            "pdf_id":       pdf_record.id,
            "filename":     filename,
            "total_pages":  total_pages,
            "total_chunks": 0,
            "warning":      "No se pudo extraer texto del PDF.",
        }

    # ── 3. Limpiar texto ─────────────────────────────────────────────────────
    # preprocess_text() es identica a la del original (chromadbapi.py)
    clean_text = text_utils.preprocess_text(raw_text)

    # ── 4. Dividir en chunks ─────────────────────────────────────────────────
    # Mismos parametros que el original: chunk_size=2500, chunk_overlap=400
    chunks = text_utils.split_into_chunks(clean_text)
    print(f"[data_ingest_service] Generados {len(chunks)} fragmentos.")

    # ── 5. Crear registro en `pdfs` ──────────────────────────────────────────
    # Se crea despues de extraer el texto para tener total_pages real.
    pdf_record = pdf_repository.save_pdf(
        filename=filename,
        filepath=filepath,
        uploaded_user=admin_id,
        total_pages=total_pages,
    )
    pdf_id = pdf_record.id

    # ── 6. Generar embeddings en lote ────────────────────────────────────────
    # Una sola llamada a Ollama con todos los textos, igual que el original
    # usaba OllamaEmbeddings para insertar en ChromaDB de una vez.
    print("[data_ingest_service] Generando embeddings con Ollama")
    texts = [chunk["chunk_text"] for chunk in chunks]
    embeddings = embedding_utils.generate_embeddings(texts)

    # ── 7 y 8. Guardar chunks y keywords ─────────────────────────────────────
    # En el original: db.add_texts(texts=[chunk], metadatas=[{"source": ..., "keywords": ...}])
    # Ahora: chunk_repository.save_chunk() + keyword_repository.save_keywords()
    # La diferencia es que las keywords ya no son un string concatenado
    # ("matricula,fechas,carrera") sino filas individuales en chunk_keyword.
    print("[data_ingest_service] Guardando chunks en PostgreSQL")

    for i, chunk in enumerate(chunks):
        # Guardar chunk con embedding en document_chunks
        saved_chunk = chunk_repository.save_chunk(
            pdf_id=pdf_id,
            chunk_text=chunk["chunk_text"],
            embedding=embeddings[i],
            chunk_index=chunk["chunk_index"],
            page_ref=chunk.get("page_ref"),
        )

        # Extraer keywords con la misma logica del original y guardar en chunk_keyword
        keywords = keyword_utils.extract_keywords(chunk["chunk_text"])
        if keywords:
            keyword_repository.save_keywords(saved_chunk.id, keywords)

    print("[data_ingest_service] Chunks guardados exitosamente")

    # ── 9. Actualizar total_chunks en el registro del PDF ────────────────────
    total_chunks = len(chunks)
    pdf_repository.update_pdf_chunks(pdf_id, total_chunks)

    return {
        "pdf_id":       pdf_id,
        "filename":     filename,
        "total_pages":  total_pages,
        "total_chunks": total_chunks,
    }


def get_all_pdfs() -> list[dict]:
    """
    Retorna la lista de todos los PDFs indexados.
    Llamado desde data_ingest_controller.py en GET /add_pdf.
    """
    pdfs = pdf_repository.get_all_pdfs()
    return [
        {
            "id":           pdf.id,
            "filename":     pdf.filename,
            "total_pages":  pdf.total_pages,
            "total_chunks": pdf.total_chunks,
            "uploaded_at":  pdf.uploaded_at.isoformat() if pdf.uploaded_at else None,
        }
        for pdf in pdfs
    ]