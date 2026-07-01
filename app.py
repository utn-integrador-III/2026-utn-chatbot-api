"""
app.py
Punto de entrada principal de la API.
"""

from flask import Flask
from flask_cors import CORS

from app.config.settings import FLASK_PORT
from app.routes.login_routes import login_bp
from app.routes.main_routes import main_bp
from app.routes.data_ingest_routes import data_ingest_bp


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