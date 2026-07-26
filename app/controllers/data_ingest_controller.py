"""
app/controllers/data_ingest_controller.py
Controlador del endpoint POST /add_pdf.
"""

from flask import jsonify, request
from services import data_ingest_service


def add_pdf():
    """
    Maneja POST /add_pdf.

    Espera:
        - Archivo en request.files["file"]
        - JWT valido en el header Authorization (validado por jwt_middleware)
        - admin_id inyectado en request.admin_id por jwt_middleware

    Retorna 201 con el resumen del proceso si todo va bien.
    Retorna 400 si no viene archivo o no es PDF.
    Retorna 500 si ocurre un error interno durante la ingestión.
    """

    # Validar que venga un archivo en la peticion
    if "file" not in request.files:
        return jsonify({"error": "No se encontró ningún archivo en la petición."}), 400

    file = request.files["file"]

    # Validar que el campo no este vacio
    if file.filename == "" or file.filename is None:
        return jsonify({"error": "El nombre del archivo está vacío."}), 400

    # Validar que sea un PDF por extension
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Solo se permiten archivos con extensión .pdf"}), 400

    # Leer el admin_id que jwt_middleware inyecto en el request
    admin_id = getattr(request, "admin_id", None)

    try:
        result = data_ingest_service.process_pdf(
            file=file,
            filename=file.filename,
            admin_id=admin_id,
        )
    except Exception as e:
        return jsonify({"error": f"Error procesando el PDF: {str(e)}"}), 500

    return jsonify({
        "message":      "PDF procesado e indexado correctamente.",
        "pdf_id":       result["pdf_id"],
        "filename":     result["filename"],
        "total_pages":  result["total_pages"],
        "total_chunks": result["total_chunks"],
    }), 201


def list_pdfs():
    """
    Maneja GET /list_pdfs.
    Retorna la lista de todos los PDFs indexados en el sistema.
    """
    try:
        pdfs = data_ingest_service.get_all_pdfs()
    except Exception as e:
        return jsonify({"error": f"Error obteniendo los PDFs: {str(e)}"}), 500

    return jsonify({"pdfs": pdfs, "total": len(pdfs)}), 200