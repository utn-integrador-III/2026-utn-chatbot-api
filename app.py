"""
app.py
Punto de entrada principal de la API.
-
"""

import sys
import os

# Agrega la carpeta app/ al sys.path para que los imports "cortos"
# (controllers.xxx, services.xxx, middleware.xxx, etc.) funcionen
# tal como están escritos en los archivos internos del proyecto.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_cors import CORS

from app.config.settings import FLASK_PORT
from app.route.login_routes import login_bp
from app.route.main_routes import main_bp
from app.route.data_ingest_routes import data_ingest_bp


def create_app() -> Flask:
    app = Flask(__name__)

    CORS(app)
    
    # Registrar blueprints
    app.register_blueprint(login_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(data_ingest_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)