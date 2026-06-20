# Arquitectura Final - 2026-UTN-Chatbot-API

## Objetivos de la Arquitectura

- Un único puerto para toda la API.
- Mantener los endpoints actuales:
  - `/signup`
  - `/login`
  - `/profile`
  - `/savechat`
  - `/refresh_bm25`
  - `/add_pdf`
- Migrar de MongoDB + ChromaDB a PostgreSQL + pgvector.
- Utilizar Ollama como LLM.
- Utilizar LangChain como orquestador del flujo RAG.
- Los administradores se autentican.
- Los usuarios finales NO requieren autenticación.
- Aplicar MVC con arquitectura por capas.

---

# Estructura Final

```text
2026-utn-chatbot-api/
│
├── app.py
│
├── app/
│   │
│   ├── controllers/
│   │   ├── login_controller.py
│   │   ├── main_controller.py
│   │   └── data_ingest_controller.py
│   │
│   ├── services/
│   │   ├── login_service.py
│   │   ├── main_service.py
│   │   └── data_ingest_service.py
│   │
│   ├── repositories/
│   │   ├── admin_repository.py
│   │   ├── pdf_repository.py
│   │   ├── chunk_repository.py
│   │   └── keyword_repository.py
│   │
│   ├── models/
│   │   ├── admin_model.py
│   │   ├── pdf_model.py
│   │   ├── chunk_model.py
│   │   └── keyword_model.py
│   │
│   ├── routes/
│   │   ├── login_routes.py
│   │   ├── main_routes.py
│   │   └── data_ingest_routes.py
│   │
│   ├── middleware/
│   │   └── jwt_middleware.py
│   │
│   ├── config/
│   │   ├── database.py
│   │   ├── ollama.py
│   │   └── settings.py
│   │
│   └── utils/
│       ├── pdf_utils.py
│       ├── text_utils.py
│       ├── embedding_utils.py
│       └── keyword_utils.py
│
├── uploads/
│
├── ollamaModefiles/
│   ├── custom-modelfile-llama3.2
│   └── custom-modelfile-mistral
│
├── random_code/
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Flujo General del Sistema

```text
Cliente
   │
   ▼
Routes
   │
   ▼
Controllers
   │
   ▼
Services
   │
   ▼
Repositories
   │
   ▼
PostgreSQL + pgvector
```

Cuando sea necesario:

```text
Services
   │
   ├── LangChain
   ├── Ollama Embeddings
   └── Ollama LLM
```

---

# Función de cada directorio

## app/

Contiene toda la lógica de la aplicación.

---

## routes/

Recibe las peticiones HTTP.

Ejemplos:

- POST /login
- POST /signup
- POST /savechat
- POST /add_pdf

No contiene lógica de negocio.

Solo define rutas y métodos HTTP.

---

## controllers/

Recibe la petición desde las rutas.

Responsabilidades:

- Leer `request.json`
- Leer `request.files`
- Leer `request.headers`
- Validar datos básicos
- Llamar al servicio correspondiente

---

## services/

Contiene la lógica de negocio.

Ejemplos:

- Validar contraseñas
- Generar JWT
- Procesar PDFs
- Crear embeddings
- Buscar contexto
- Construir prompts
- Consultar Ollama

Es el corazón de la aplicación.

---

## repositories/

Acceso a PostgreSQL.

Aquí vive todo el SQL.

Ejemplos:

- SELECT
- INSERT
- UPDATE
- DELETE

Los Services no deberían ejecutar SQL directamente.

---

## models/

Representación de las entidades del sistema.

Basadas en las tablas:

- admins
- pdfs
- document_chunks
- chunk_keyword

---

## middleware/

Funciones ejecutadas antes de llegar al endpoint.

---

## config/

Configuraciones globales.

Ejemplos:

- PostgreSQL
- Ollama
- Variables de entorno

---

## utils/

Funciones reutilizables.

Ejemplos:

- Extraer texto de PDF
- Limpiar texto
- Generar embeddings
- Extraer keywords

---


## uploads/

Almacena los PDFs cargados por los administradores.

---

## ollamaModefiles/

Contiene los Modelfiles personalizados utilizados por Ollama.

---

# Función de cada archivo

## app.py

Punto de entrada principal.

Responsabilidades:

- Crear instancia Flask
- Registrar Blueprints
- Configurar CORS
- Levantar la aplicación

---

# Routes

## login_routes.py

Endpoints:

- POST /signup
- POST /login
- GET /profile

---

## main_routes.py

Endpoints:

- POST /savechat
- POST /refresh_bm25

---

## data_ingest_routes.py

Endpoints:

- POST /add_pdf

---

# Controllers

## login_controller.py

Controla:

- signup
- login
- profile

Recibe request y delega al LoginService.

---

## main_controller.py

Controla:

- savechat
- refresh_bm25

Recibe request y delega al MainService.

---

## data_ingest_controller.py

Controla:

- add_pdf

Recibe request y delega al DataIngestService.

---

# Services

## login_service.py

Responsable de:

- Hash de contraseña
- Validación de contraseña
- Generación de JWT
- Lectura de administradores
- Registro de administradores

---

## data_ingest_service.py

Responsable de:

- Leer PDF
- Extraer texto
- Dividir en chunks
- Generar embeddings
- Guardar información en PostgreSQL

---

## main_service.py

Responsable de:

- Procesar preguntas
- Generar embedding de la consulta
- Buscar contexto usando pgvector
- Construir prompt
- Consultar Ollama
- Retornar respuesta

---

# Repositories

## admin_repository.py

Tabla:

- admins

Métodos sugeridos:

- create_admin()
- find_admin_by_email()
- find_admin_by_username()

---

## pdf_repository.py

Tabla:

- pdfs

Métodos sugeridos:

- save_pdf()
- get_pdf()
- get_all_pdfs()

---

## chunk_repository.py

Tabla:

- document_chunks

Métodos sugeridos:

- save_chunk()
- save_embedding()
- search_similar_chunks()

Aquí vive la lógica de búsqueda semántica con pgvector.

Ejemplo conceptual:

```sql
SELECT *
FROM document_chunks
ORDER BY embedding <=> :query_embedding
LIMIT 5;
```

---

## keyword_repository.py

Tabla:

- chunk_keyword

Métodos sugeridos:

- save_keywords()
- find_keywords()

---

# Models

## admin_model.py

Representa la tabla:

- admins

---

## pdf_model.py

Representa la tabla:

- pdfs

---

## chunk_model.py

Representa la tabla:

- document_chunks

---

## keyword_model.py

Representa la tabla:

- chunk_keyword

---

# Middleware

## jwt_middleware.py

Protege endpoints administrativos.

Ejemplos:

- /profile
- /add_pdf

Valida el JWT antes de permitir el acceso.

---

# Config

## database.py

Configura la conexión con PostgreSQL.

Puede utilizar:

- SQLAlchemy
- psycopg

---

## ollama.py

Configuración relacionada con Ollama.

Ejemplos:

- URL de Ollama
- Modelo de embeddings
- Modelo de chat

---

## settings.py

Variables globales.

Ejemplos:

- JWT_SECRET
- UPLOAD_FOLDER
- CHUNK_SIZE
- CHUNK_OVERLAP

---

# Utils

## pdf_utils.py

Funciones:

- extract_text_from_pdf()
- count_pages()

---

## text_utils.py

Funciones:

- clean_text()
- normalize_text()

---

## embedding_utils.py

Funciones:

- generate_embedding()
- generate_query_embedding()

---

## keyword_utils.py

Funciones:

- extract_keywords()

---

# Papel de LangChain

LangChain sigue siendo el orquestador del flujo RAG.

Responsabilidades:

- Text Splitter
- Prompt Templates
- Chains
- Integración con Ollama
- Flujo de recuperación de contexto

Ya NO utilizará ChromaDB.

Los vectores vivirán dentro de PostgreSQL mediante pgvector.

---

# Flujo de Ingesta

```text
/add_pdf
    │
    ▼
DataIngestController
    │
    ▼
DataIngestService
    │
    ├── Extraer PDF
    ├── Dividir en chunks
    ├── Generar embeddings
    │
    ▼
Repositories
    │
    ▼
PostgreSQL + pgvector
```

---

# Flujo de Consulta

```text
/savechat
    │
    ▼
MainController
    │
    ▼
MainService
    │
    ├── Embedding de la pregunta
    ├── Búsqueda semántica en pgvector
    ├── Construcción del contexto
    ├── Prompt final
    │
    ▼
Ollama
    │
    ▼
Respuesta
```
