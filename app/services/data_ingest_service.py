"""
app/services/data_ingest_service.py
Logica de negocio para la ingestion de documentos PDF.
"""

import os

from config.settings import UPLOAD_FOLDER
from repositories import chunk_repository, keyword_repository, pdf_repository
from utils import embedding_utils, keyword_utils, pdf_utils, text_utils


def process_pdf(file, filename: str, admin_id: str | None = None) -> dict:

    # ── 1. Guardar archivo fisico en uploads/ ────────────────────────────────
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"[data_ingest_service] Archivo guardado: {filepath}")

    # ── 2. Extraer texto con PyMuPDF ─────────────────────────────────────────
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
    clean_text = text_utils.preprocess_text(raw_text)

    # ── 4. Dividir en chunks ─────────────────────────────────────────────────
    chunks = text_utils.split_into_chunks(clean_text)
    print(f"[data_ingest_service] Generados {len(chunks)} fragmentos.")

    # ── 5. Crear registro en `pdfs` ──────────────────────────────────────────
    pdf_record = pdf_repository.save_pdf(
        filename=filename,
        filepath=filepath,
        uploaded_user=admin_id,
        total_pages=total_pages,
    )
    pdf_id = pdf_record.id

    # ── 6. Generar embeddings en lote ────────────────────────────────────────
    print("[data_ingest_service] Generando embeddings con Ollama")
    texts = [chunk["chunk_text"] for chunk in chunks]
    embeddings = embedding_utils.generate_embeddings(texts)

    # ── 7 y 8. Guardar chunks y keywords ─────────────────────────────────────
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