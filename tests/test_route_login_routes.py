from flask import Flask

import sys
import importlib
config_pkg = importlib.import_module("app.config")
sys.modules["config"] = config_pkg
sys.modules["controllers"] = importlib.import_module("app.controllers")
sys.modules["middleware"] = importlib.import_module("app.middleware")

from app.route.login_routes import login_bp


# ──────────────────────────────────────────────
# LOGIN ROUTES
# ──────────────────────────────────────────────


def test_login_blueprint_registers_expected_routes():

    app = Flask(__name__)

    app.register_blueprint(login_bp)
    rules = {r.rule for r in app.url_map.iter_rules()}

    assert "/signup" in rules
    assert "/login" in rules
    assert "/logout" in rules
    assert "/delete_user" in rules
