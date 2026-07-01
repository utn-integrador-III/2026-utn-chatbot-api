"""
Servicio principal del chatbot.
RAG usando PostgreSQL + pgvector.
"""


from config.ollama import chat
from utils import embedding_utils
from repositories import chunk_repository



SYSTEM_PROMPT = """
Eres un chatbot de asistencia universitaria de la Universidad Técnica Nacional.

Solo puedes responder sobre:

- matrícula
- becas
- carreras
- requisitos
- trámites universitarios
- fechas académicas
- información oficial

Reglas:

- Responde en español.
- No inventes información.
- Usa únicamente los documentos encontrados.
- Si no existe información suficiente indica que no tienes datos.
- No solicites información personal.
"""



def build_context(chunks):

    if not chunks:
        return "No se encontró información."


    context = []


    for chunk in chunks:

        source = chunk.get(
            "source",
            "documento"
        )


        context.append(
            f"""
Fuente: {source}

{chunk["chunk_text"]}
"""
        )


    return "\n\n".join(context)



def process_chat(user_prompt: str) -> dict:
    """
    Flujo:

    pregunta
    ↓
    embedding
    ↓
    pgvector
    ↓
    contexto
    ↓
    Ollama
    """


    # 1. Convertir pregunta a vector

    question_embedding = (
        embedding_utils.generate_query_embedding(
            user_prompt
        )
    )


    # 2. Buscar en PostgreSQL

    chunks = chunk_repository.search_similar_chunks(
        question_embedding,
        limit=5
    )


    # 3. Crear contexto

    context = build_context(chunks)



    prompt = f"""

Información encontrada:

{context}


Pregunta:

{user_prompt}

"""


    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": prompt
        }
    ]


    # 4. Preguntar al modelo

    response = chat(messages)



    return {

        "question": user_prompt,

        "context_used": context,

        "sources": [
            c.get("source")
            for c in chunks
        ],

        "answer": response["message"]["content"]

    }