
# Descripción del proyecto

## NOVA - ChatBot Universitario

NOVA es un chatbot orientado a brindar respuestas y asistencia a consultas universitaras de la UTN.  
El proyecto en la parte del backend está desarrollado completamente en **Python** y utiliza tecnologías de inteligencia artificial local para el procesamiento y generación de respuestas.

La arquitectura del sistema se basa en:

- **Ollama** como servidor de modelos LLM locales.
- **LangChain** para la gestión del flujo conversacional y la integración con los modelos de inteligencia artificial.
- **Flask** como backend principal de la API.

---

## Funcionamiento general

El funcionamiento del proyecto se basa en una arquitectura cliente-servidor donde la API desarrollada en Python se comunica con un servidor Ollama encargado de ejecutar los modelos de lenguaje de manera local.

### Flujo general del sistema

1. El usuario realiza una consulta al chatbot NOVA.
2. La API Flask recibe la solicitud.
3. LangChain procesa el contexto y administra la interacción con el modelo.
4. La consulta es enviada al servidor Ollama.
5. Ollama ejecuta el modelo LLM configurado.
6. La respuesta generada retorna a la API.
7. Finalmente, NOVA devuelve la respuesta al usuario.

---

## Tecnologías utilizadas

| Tecnología | Función |
|------------|----------|
| Python | Backend principal del proyecto |
| Flask | Desarrollo de la API REST |
| Ollama | Ejecución local de modelos LLM |
| LangChain | Gestión del flujo conversacional e integración con IA |
| ChromaDB | Almacenamiento y consultas vectoriales |
---

# Implementación de PY

# Creación del entorno virtual

Antes de iniciar, asegúrate de tener instalado y seleccionado Python correctamente en tu máquina.

## Pasos para crear y activar el entorno virtual

1. Abrir una nueva terminal desde tu IDE.
2. Ejecutar los siguientes comandos:

```bash
python -m venv env_chatbot
````

```bash
.\env_chatbot\Scripts\activate
```

```bash
pip install -r "ruta donde se encuentra el requirements.txt"
```

## Desactivar el entorno virtual

```bash
deactivate
```

---

# Configuración local de la API

Sigue los siguientes pasos para ejecutar la API de forma local correctamente.

---

## 1. Configuración del servidor Ollama

La API utiliza un servidor Ollama para la ejecución de modelos de inteligencia artificial de forma local.

Es importante verificar y actualizar la dirección IP del servidor Ollama dentro de la configuración del proyecto para asegurar una comunicación correcta entre la API y el servidor de modelos.

> **Importante:**  
> Asegúrate de utilizar la IP correcta del servidor donde se encuentra ejecutándose Ollama.

---

## 2. Configuración de modelos LLM

El proyecto permite trabajar con distintos modelos de lenguaje configurables desde el backend.

Puedes utilizar los modelos predeterminados del proyecto o modificarlos según las necesidades de implementación y disponibilidad en el servidor Ollama.

---

## 3. Crear el entorno virtual

Para ejecutar la API de forma local, es necesario crear un entorno virtual.

Sigue las instrucciones indicadas en la sección:

- **Creación del entorno virtual**

---

## 4. Documentación de la API Flask del ChatBot

* https://documenter.getpostman.com/view/45666071/2sB3B8sDiw

---

# API Ollama

## Referencia oficial

* https://github.com/ollama/ollama/blob/main/docs/api.md

---

# Información extra de la API de Ollama

## Response

---

# `/api/generate` - Generación simple

## Descripción

Este endpoint es para enviar un prompt directo a un modelo (como `mistral`) y recibir una respuesta textual.

No guarda contexto, ni estructura tipo chat.

---

## ¿Cuándo usar `/api/generate`?

* Cuando quieres una sola respuesta directa, sin seguimiento.
* Cuando no necesitas un historial de conversación.
* Ideal para preguntas sueltas o generación puntual de texto.

---

## Ejemplo de solicitud

**POST →** `http://localhost:11434/api/generate`

```json
{
  "model": "mistral",
  "prompt": "Explica qué es un sistema operativo",
  "stream": false
}
```

---

## Ejemplo de respuesta (`stream: false`)

```json
{
  "response": "Un sistema operativo es un software que gestiona los recursos de hardware y software...",
  "done": true
}
```

---

## Campos importantes

| Campo   | Descripción                                                                         |
| ------- | ----------------------------------------------------------------------------------- |
| model   | Nombre del modelo a usar (ej: `"mistral"`)                                          |
| prompt  | Texto que el usuario quiere que el modelo procese                                   |
| stream  | `true` para recibir respuesta por partes (útil para mostrar letra por letra)        |
| options | (Opcional) Parámetros avanzados como: `temperature`, `top_k`, `top_p`, `stop`, etc. |

---

# `/api/chat` – Conversación estructurada con contexto

## Descripción

Este endpoint es para simular un chat tipo conversación.

El modelo puede recordar lo que se dijo anteriormente en el mismo intercambio.

---

## ¿Cuándo usar `/api/chat`?

* Cuando construyes una interfaz de conversación más allá de un contexto.
* Cuando necesitas respuestas más coherentes a lo largo del tiempo.
* Cuando deseas mantener el contexto entre turnos del usuario y del modelo.

---

## Ejemplo de solicitud

```json
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
```

---

## Ejemplo de respuesta

```json
{
  "message": {
    "role": "assistant",
    "content": "Existen dos tipos principales de IP: IPv4 e IPv6..."
  },
  "done": true
}
```

---

## Campos importantes

| Rol       | Función                                                                            |
| --------- | ---------------------------------------------------------------------------------- |
| system    | Define el comportamiento general del modelo (como el `"System"` en un Modelfile)   |
| user      | Representa las preguntas del usuario                                               |
| assistant | Representa respuestas anteriores del modelo (importante para mantener el contexto) |

---