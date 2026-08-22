from flask import Flask

import sys
import importlib
config_pkg = importlib.import_module("app.config")
sys.modules["config"] = config_pkg
sys.modules["controllers"] = importlib.import_module("app.controllers")

from app.route.main_routes import main_bp


# ──────────────────────────────────────────────
# MAIN ROUTES
# ──────────────────────────────────────────────


def test_main_blueprint_registers_savechat_route():

    app = Flask(__name__)

    app.register_blueprint(main_bp)
    rules = {r.rule for r in app.url_map.iter_rules()}

    assert "/savechat" in rules
