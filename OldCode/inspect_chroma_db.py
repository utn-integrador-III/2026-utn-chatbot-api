from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
#from langchain_community.embeddings import OllamaEmbeddings
#from langchain_community.vectorstores import Chroma
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Ruta absoluta a /backend
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_storage")
COLLECTION_NAME = "universidad_docs"

# Instanciar embeddings (deben ser los mismos que usaste al indexar)
print("📦 Inicializando embeddings...")
embedding = OllamaEmbeddings(
    model="mistral:latest",
    base_url="http://localhost:11434"
)

print("📚 Cargando base vectorial...")
db = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embedding
)

# 👉 AQUÍ PEGÁS EL CÓDIGO:
print("📁 Ruta usada:", CHROMA_DB_DIR)
print("📂 Colecciones disponibles:")
print(db._client.list_collections())  # 👈 Esto te dice qué colecciones hay realmente
# Verificar número de documentos en la colección
print("🔍 Verificando número de documentos en la colección...")
print("Total de documentos:", db._collection.count())

# Obtener vectores y metadatos
collection = db._collection
data = collection.get(include=["documents", "metadatas", "embeddings"])
if not data["ids"]:
    print("⚠️ No hay datos en la colección.")
else:
    for i in range(len(data["ids"])):
        print(f"\n🆔 ID: {data['ids'][i]}")
        print(f"📄 Documento: {data['documents'][i][:300]}...")
        print(f"📌 Metadatos: {data['metadatas'][i]}")
        print(f"🔢 Vector (primeros 5 valores): {data['embeddings'][i][:5]}")
        
print("========================================")
query = "¿Cuándo es el inicio del periodo lectivo del I CUATRIMESTRE del 2025?"
print(f"🔍 Buscando: {query}")
results = db.similarity_search(query, k=3)  # top 1 resultado más similar
# Mostrar resultados
print("\n🔍 Resultados de la búsqueda con el valor en k3:")
for r in results:
    print("\n🔍 Resultado más relevante:")
    print(f"📄 Texto: {r.page_content}")
    print(f"📌 Metadatos: {r.metadata}")
    
#results2 = db.similarity_search(query, k=3)  # top 3 resultados más similares
# Mostrar resultados
#print("\n🔍 Resultados de la búsqueda con el valor en k2:")
#for r in results2:
    #print("\n🔍 Resultado más relevante:")
    #print(f"📄 Texto: {r.page_content}")
    #print(f"📌 Metadatos: {r.metadata}")