from flask import Flask

import sys
import importlib
config_pkg = importlib.import_module("app.config")
sys.modules["config"] = config_pkg
sys.modules["repositories"] = importlib.import_module("app.repositories")
sys.modules["controllers"] = importlib.import_module("app.controllers")

from app.route.data_ingest_routes import data_ingest_bp


# ──────────────────────────────────────────────
# DATA INGEST ROUTES
# ──────────────────────────────────────────────


def test_blueprint_registers_add_pdf_and_list_pdfs_routes():

    app = Flask(__name__)

    app.register_blueprint(data_ingest_bp)
    rules = {r.rule for r in app.url_map.iter_rules()}

    assert "/add_pdf" in rules
    assert "/list_pdfs" in rules
