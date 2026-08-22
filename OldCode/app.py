#Importsciones de las librerias 
from flask import Flask, make_response, request, jsonify, abort
from flask_cors import CORS
import requests

OLLAMA_URL = "http://10.90.28.157:11434/api/chat"
OLLAMA_URL_CHAT = "http://10.90.28.157:11434/api/generate"
OLLAMA_MODEL = "custom-modelfile-mistral"
OLLAMA_MODEL2 = "mistral:latest"
OLLAMA_MODEL3 = "llama3.2:3b"
OLLAMA_MODEL4 = "custom-modelfile-llama3b"


# Create flask application
app = Flask(__name__)
CORS(app)

# Control de errores para las reglas de httpRequest.
@app.errorhandler(400)
def BAD_REQUEST(error):
    return make_response(jsonify({'error': 'Solicitud incorrecta (Bad Request)'}), 400)

@app.errorhandler(404)
def NOT_FOUND(error):
    return make_response(jsonify({'error': 'Recurso no encontrado (Not Found)'}), 404)

@app.errorhandler(405)
def METHOD_NOT_ALLOWED(error):
    return make_response(jsonify({'error': 'Método HTTP no permitido (Method Not Allowed)'}), 405)

@app.errorhandler(429)
def TOO_MANY_REQUESTS(error):
    return make_response(jsonify({'error': 'Demasiadas solicitudes (Too Many Requests)'}), 429)

@app.errorhandler(500)
def INTERNAL_SERVER_ERROR(error):
    return make_response(jsonify({'error': 'Error interno del servidor (Internal Server Error)'}), 500)

@app.errorhandler(502)
def BAD_GATEWAY(error):
    return make_response(jsonify({'error': 'Respuesta inválida desde Ollama (Bad Gateway)'}), 502)

@app.errorhandler(503)
def SERVICE_UNAVAILABLE(error):
    return make_response(jsonify({'error': 'Servicio no disponible (Service Unavailable)'}), 503)

@app.errorhandler(504)
def GATEWAY_TIMEOUT(error):
    return make_response(jsonify({"error": "Tiempo de espera agotado con Ollama (Gateway Timeout)"}), 504)

# Rutas de la API
@app.route("/", methods=["GET"])
def INDEX():
    try:
        data = {
            "status_code": 200,
            "status_message": "Conexion exitosa a la API",
            "body_message": {
                "description": "ApiChat, es una API-Rest para la conexion a Ollama",
                "author": "Grupo de Proyector Integrador Pukeyackos"
            }
        }
    except Exception as expc:
        abort(404)
    return jsonify(data)


@app.route("/chat", methods=["POST"])
def CHAT():
    data = request.get_json()
    if not data or "prompt" not in data:
        abort(400)  # Dispara BAD_REQUEST
    
    prompt = data["prompt"]

    # Arma el JSON para enviar a Ollama
    payload = {
        "model": OLLAMA_MODEL3,  # Cambia al modelo que quieras usar
        "prompt": prompt,
        "stream": False  # si se coloca True, tienes que procesar la respuesta por partes (o eso entiendo)
    }

    try:
        # Solicitud POST a Ollama
        print(f"Enviando solicitud a Ollama con el prompt: {prompt}")
        response = requests.post(OLLAMA_URL_CHAT, json=payload, timeout=600)
    except requests.exceptions.ConnectionError:
        abort(503)  # Dispara SERVICE_UNAVAILABLE 
    except requests.exceptions.Timeout:
        abort(504)  # Dispara GATEWAY_TIMEOUT
    except requests.exceptions.RequestException:
        abort(502)  # Dispara BAD_GATEWAY
        
    if response.status_code == 429:
        abort(429)  # Dispara TOO_MANY_REQUESTS
    elif response.status_code != 200:
        abort(500)  # Dispara INTERNAL_SERVER_ERROR
        
    try:
        result = response.json()
    except ValueError:
        abort(502)  # Dispara BAD_GATEWAY si la respuesta no es JSON
    return jsonify(result)
    #return jsonify({"respuesta": result.get("response", "Sin respuesta")})


@app.route("/savechat", methods=["POST"])
def SAVE_CHAT():
    data = request.get_json()
    
    if not data or "prompt" not in data:
        abort(400)  # Dispara BAD_REQUEST
    
    prompt = data["prompt"]

    # Arma el JSON para enviar a Ollama
    payload = {
        "model": OLLAMA_MODEL3,
        "messages": [
            { "role": "system", "content": "Eres un asistente de Universidad, donde solo vas a responder con respecto a solo temas de la Universidad" },
            { "role": "user", "content": prompt }
        ],
        "stream": False
    }

    try:
        # Solicitud POST a Ollama
        response = requests.post(OLLAMA_URL, json=payload, timeout=600)
    except requests.exceptions.ConnectionError:
        abort(503)  # Dispara SERVICE_UNAVAILABLE 
    except requests.exceptions.Timeout:
        abort(504)  # Dispara GATEWAY_TIMEOUT
    except requests.exceptions.RequestException:
        abort(502)  # Dispara BAD_GATEWAY
        
    if response.status_code == 429:
        abort(429)  # Dispara TOO_MANY_REQUESTS
    elif response.status_code != 200:
        abort(500)  # Dispara INTERNAL_SERVER_ERROR
        
    try:
        result = response.json()
    except ValueError:
        abort(502)  # Dispara BAD_GATEWAY si la respuesta no es JSON
    return jsonify(result)
    #return jsonify({"respuesta": result.get("response", "Sin respuesta")})
    

if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    app.run(HOST, PORT)