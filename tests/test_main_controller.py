 
import json
from unittest.mock import patch

import pytest
from flask import Flask
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
import sys
import importlib

config_pkg = importlib.import_module("app.config")
sys.modules["config"] = config_pkg
for sub in ("settings", "ollama", "database"):
    try:
        sys.modules[f"config.{sub}"] = importlib.import_module(f"app.config.{sub}")
    except Exception:
        pass

services_pkg = importlib.import_module("app.services")
sys.modules["services"] = services_pkg
try:
    sys.modules["services.main_service"] = importlib.import_module(
        "app.services.main_service"
    )
except Exception:
    pass

try:
    repos_pkg = importlib.import_module("app.repositories")
    sys.modules["repositories"] = repos_pkg
    for sub in ("chunk_repository", "keyword_repository", "pdf_repository"):
        try:
            sys.modules[f"repositories.{sub}"] = importlib.import_module(f"app.repositories.{sub}")
        except Exception:
            pass
except Exception:
    pass

try:
    model_pkg = importlib.import_module("app.model")
    sys.modules["model"] = model_pkg
    try:
        sys.modules["model.admin_model"] = importlib.import_module("app.model.admin_model")
    except Exception:
        pass
except Exception:
    pass

try:
    utils_pkg = importlib.import_module("app.utils")
    sys.modules["utils"] = utils_pkg
    try:
        sys.modules["utils.embedding_utils"] = importlib.import_module("app.utils.embedding_utils")
    except Exception:
        pass
except Exception:
    pass

from app.controllers.main_controller import save_chat

app = Flask(__name__)


def test_save_chat_without_json_body_raises_bad_request():
    with app.test_request_context("/savechat", method="POST"):
        with pytest.raises(UnsupportedMediaType):
            save_chat()


def test_save_chat_without_prompt_field_raises_bad_request():
    payload = {}

    with app.test_request_context(
        "/savechat", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        with pytest.raises(BadRequest):
            save_chat()


@patch("app.controllers.main_controller.process_chat")
def test_save_chat_success_returns_result(mock_process_chat):
    mock_process_chat.return_value = {"answer": "Respuesta del modelo con contexto RAG."}
    payload = {"prompt": "¿Qué becas hay disponibles?"}

    with app.test_request_context(
        "/savechat", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response = save_chat()

    assert response.get_json()["answer"] == "Respuesta del modelo con contexto RAG."
    mock_process_chat.assert_called_once_with("¿Qué becas hay disponibles?")


@patch("app.controllers.main_controller.process_chat")
def test_save_chat_service_exception_returns_500(mock_process_chat):
    mock_process_chat.side_effect = Exception("Fallo al consultar el modelo.")
    payload = {"prompt": "¿Qué becas hay disponibles?"}

    with app.test_request_context(
        "/savechat", method="POST", data=json.dumps(payload), content_type="application/json"
    ):
        response, status = save_chat()

    assert status == 500
    assert "Fallo al consultar el modelo." in response.json["error"]