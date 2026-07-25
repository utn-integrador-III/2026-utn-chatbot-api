from flask import Blueprint
from controllers.main_controller import save_chat

main_bp = Blueprint("main", __name__)

main_bp.route("/savechat", methods=["POST"])(save_chat)