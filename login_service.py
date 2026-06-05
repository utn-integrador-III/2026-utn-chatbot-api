"""
API de Autenticación de Usuarios con Flask + MongoDB + JWT
==========================================================
Dependencias principales:
-------------------------
- Flask
- Flask-Cors
- PyMongo
- Pydantic
- Werkzeug (para hash de contraseñas)
- PyJWT

Base de datos:
--------------
- MongoDB
- Colección: `ChatBotDB.users`
- Esquema del documento:
    {
        "username": str,
        "email": str,
        "password": str (hashed)
    }

"""

from flask import Flask, request, jsonify, abort, make_response
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime
from functools import wraps
from pydantic import BaseModel, EmailStr, ValidationError
from datetime import datetime, timedelta


# ==========================
# Configuración inicial
# ==========================
app = Flask(__name__)
CORS(app)

# Clave secreta para firmar JWT (ideal usar variable de entorno en prod)
app.config['SECRET_KEY'] = "super-secret-key"  


# ==========================
# Conexión a MongoDB
# ==========================
def contextDB():
    """
    Establece conexión con MongoDB y devuelve el cliente.
    Retorna:
        MongoClient: instancia de conexión a la base de datos.
    """
    return MongoClient("mongodb://admin:esteban2511@127.0.0.1:27017/")


# ==========================
# Modelos de validación con Pydantic
# ==========================
class UserSignupModel(BaseModel):
    """Modelo de datos para registro de usuario."""
    username: str
    email: EmailStr
    password: str


class UserLoginModel(BaseModel):
    """
    Modelo de datos para login de usuario.
    Se puede usar `username` o `email` junto con la contraseña.
    """
    username: str | None = None
    email: str | None = None   # ahora es str para evitar error de validación
    password: str



# ==========================
# Decorador para verificación de JWT
# ==========================
def token_required(f):
    """
    Decorador que protege rutas para que solo sean accesibles
    con un token JWT válido.
    
    Args:
        f (function): función de vista protegida.
    
    Returns:
        function: la función envuelta con validación de token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # El token debe venir en el header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'mensaje': 'Token faltante'}), 401

        try:
            # Decodificar token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except:
            return jsonify({'mensaje': 'Token inválido o expirado'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# =========================
# Rutas principales
# =========================
@app.route("/", methods=["GET"])
def INDEX():
    """
    Ruta raíz para verificar el estado de la API.
    Devuelve JSON con descripción, autor y estado actual.
    """
    try:
        data = {
            "status_code": 200,
            "status_message": "Conexion exitosa a la API",
            "status_time": datetime.now().isoformat(),
            "body_message": {
                "description": "ApiConex, es una API-Rest para la validación de usuarios en mongo",
                "author": "Grupo de Proyecto Integrador Pukeyackos"
            }
        }
    except Exception:
        abort(404)
    return jsonify(data)


# ==========================
# Endpoint: Registro de usuario
# ==========================
@app.route('/signup', methods=['POST'])
def signup():
    """
    Registro de usuario.
    --------------------
    Espera JSON en el body:
    {
        "username": "nombre_usuario",
        "email": "correo@ejemplo.com",
        "password": "contraseña"
    }

    Validaciones:
    - Email debe tener formato correcto.
    - No se permiten usernames o emails duplicados.

    Respuestas:
    - 201: Usuario registrado con éxito.
    - 400: Datos inválidos o usuario ya existente.
    """
    try:
        data = UserSignupModel(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    db = contextDB().ChatBotDB

    # Verificar duplicados
    if db.users.find_one({'email': data.email}):
        return jsonify({'mensaje': 'El correo ya está registrado'}), 400
    if db.users.find_one({'username': data.username}):
        return jsonify({'mensaje': 'El nombre de usuario ya está registrado'}), 400

    # Hashear contraseña
    hashed_password = generate_password_hash(data.password, method='pbkdf2:sha256')


    # Guardar en BD
    user_doc = {
        'username': data.username,
        'email': data.email,
        'password': hashed_password
    }
    db.users.insert_one(user_doc)

    return jsonify({'mensaje': 'Usuario registrado correctamente'}), 201


# ==========================
# Endpoint: Login
# ==========================
@app.route('/login', methods=['POST'])
def login():
    """
    Login de usuario.
    -----------------
    Se puede usar username o email junto con la contraseña.
    """
    try:
        data = UserLoginModel(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    # Validar que haya username o email
    if not (data.username or (data.email and data.email.strip() != "")):
        return jsonify({'mensaje': 'Debes proporcionar username o email'}), 400

    db = contextDB().ChatBotDB

    # Construir query según lo que envíe el usuario
    query = {}
    if data.username and data.username.strip() != "":
        query = {'username': data.username}
    elif data.email and data.email.strip() != "":
        query = {'email': data.email}

    user = db.users.find_one(query)
    if not user:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404

    # Validar contraseña
    if not check_password_hash(user['password'], data.password):
        return jsonify({'mensaje': 'Contraseña incorrecta'}), 401

    # Generar JWT válido por 1 hora
    token = jwt.encode({
        'username': user['username'],
        'exp': datetime.utcnow() + timedelta(minutes=20)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'mensaje': 'Inicio de sesión exitoso',
        'token': token,
        'Tiempo Para cerrar sesión': (datetime.utcnow() + timedelta(minutes=20)).strftime("%H:%M")  # Solo hora y minutos
    }), 200

# ==========================
# Endpoint: Perfil protegido
# ==========================
@app.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    """
    Perfil de usuario autenticado.
    ------------------------------
    Requiere header:
        Authorization: Bearer <token>
    Devuelve:
    - Datos del usuario (sin contraseña).
    """
    db = contextDB().ChatBotDB
    user = db.users.find_one({'username': current_user}, {"_id": 0, "password": 0})
    return jsonify({'user': user}), 200

# ==========================
# Inicio de la API
# ==========================
if __name__ == '__main__':
    app.run("0.0.0.0", 7005)
