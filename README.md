## Implementación de PY 🚀

# Creacion del entorno virtual 
1. Antes de iniciar, asegúrate de tener instalado y selecionado el entorno en tu maquina.
- Abrir una nueva terminal desde tu IDE
    * cd backend 
    * python -m venv env_chatbot
    * .\env_chatbot\Scripts\activate
    * pip install -r "ruta donde se encuentra el requirements.txt" 
        * Ejemplo: D:\Universidad_UTN\2025\Segundo_Cuatri\Proyecto_Integrador\chatbot-utn-pi\requirements.txt
    * deactivate

# Configuración local de la API ⚙️ 
Sigue los siguientes pasos para ejecutar la API de forma local correctamente:
1. Configurar las URLs del servidor Ollama
Debes actualizar las siguientes variables con la dirección IP correspondiente al servidor donde se ejecuta Ollama (en nuestro caso, test_chatbot_1.0.1):
- OLLAMA_URL = "http://<IP_DEL_SERVIDOR>:11434/api/chat"
- OLLAMA_URL_CHAT = "http://<IP_DEL_SERVIDOR>:11434/api/generate"
Importante: Asegúrate de reemplazar <IP_DEL_SERVIDOR> con la IP real donde está corriendo Ollama.

2. Configurar los modelos de lenguaje (LLM)
La API está preparada para usar hasta cuatro modelos. Estos están definidos en las siguientes variables:
- OLLAMA_MODEL = "custom-modelfile-mistral"
- OLLAMA_MODEL2 = "mistral"
- OLLAMA_MODEL3 = "llama3.2"
- OLLAMA_MODEL4 = "custom-modelfile-llama3b"
Puedes cambiar los modelos si lo consideras necesario, pero no es obligatorio para la ejecución básica.

3. Para ejecutar la API de forma local, es necesario crear un entorno virtual. Sigue las instrucciones indicadas en la sección "Creación del entorno virtual" de este repositorio.

4. Documentacion de la API Flask del ChatBot
- https://documenter.getpostman.com/view/45666071/2sB3B8sDiw 


# 📘 Api Ollama
- Referencia: https://github.com/ollama/ollama/blob/main/docs/api.md 

# Info Extra de la api de Ollama
**Response:**

## /api/generate - Generación simple
**Descripción**
Este endpoint es para enviar un prompt directo a un modelo (como mistral) y recibir una respuesta textual. No guarda contexto, ni estructura tipo chat.

**¿Cuándo usar /api/generate?**
Cuando quieres una sola respuesta directa, sin seguimiento.
Cuando no necesitas un historial de conversación.
Ideal para preguntas sueltas o generación puntual de texto.

**Ejemplo de solicitud (POST a http://localhost:11434/api/generate):**
{
  "model": "mistral",
  "prompt": "Explica qué es un sistema operativo",
  "stream": false
}

**Ejemplo de respuesta (si stream: false):**
{
  "response": "Un sistema operativo es un software que gestiona los recursos de hardware y software...",
  "done": true
}

**Campos importantes:**
Campo      | Descripción
-----------|---------------------------------------------------------------
model      | Nombre del modelo a usar (ej: "mistral")
prompt     | Texto que el usuario quiere que el modelo procese
stream     | true para recibir respuesta por partes (útil para mostrar letra por letra),
           | false para una sola respuesta completa
options    | (Opcional) Parámetros avanzados como: temperature, top_k, top_p, stop, etc.


## /api/chat – Conversación estructurada con contexto
**Descripción**
Este endpoint es para simular un chat tipo conversación: el modelo puede recordar lo que se dijo anteriormente en el mismo intercambio.

**¿Cuándo usar /api/chat?**
Cuando construyes una interfaz de conversación más allá de un contexto.
Cuando necesitas respuestas más coherentes a lo largo del tiempo.
Cuando deseas mantener el contexto entre turnos del usuario y del modelo.

**Ejemplo de solicitud:**
{
  "model": "mistral",
  "messages": [
    { "role": "system", "content": "Eres un asistente experto en informática." },
    { "role": "user", "content": "¿Qué es una IP?" },
    { "role": "assistant", "content": "Una IP es un identificador único de red..." },
    { "role": "user", "content": "¿Y qué tipos hay?" }
  ],
  "stream": false
}

**Ejemplo de respuesta:**
{
  "message": {
    "role": "assistant",
    "content": "Existen dos tipos principales de IP: IPv4 e IPv6..."
  },
  "done": true
}

**Campos importantes**
Rol         | Función
------------|--------------------------------------------------------------
system      | Define el comportamiento general del modelo (como el "System" en un Modelfile)
user        | Representa las preguntas del usuario
assistant   | Representa respuestas anteriores del modelo (importante para mantener el contexto)