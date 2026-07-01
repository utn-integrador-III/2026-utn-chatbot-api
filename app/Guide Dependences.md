# ============================================================
# Instalation of dependences
# ============================================================

# Enter to project

   - cd 2026-utn-chatbot-api


# ============================================================
# app/config/
# PostgreSQL + pgvector + pool de conexiones
# ============================================================

   - pip install psycopg[binary] psycopg-pool pgvector


# ============================================================
# app/utils/
# ============================================================

   - pip install pymupdf langchain-text-splitters langchain-ollama


# ============================================================
# app/services/
# ============================================================

   - pip install langchain langchain-community


# ============================================================
# app/routes/
# ============================================================

   - pip install flask flask-cors


# ============================================================
# Ollama + variables entorno
# ============================================================

   - pip install requests python-dotenv