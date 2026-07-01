from flask import Blueprint
from controllers.main_controller import save_chat, refresh_bm25_index

main_bp = Blueprint("main", __name__)

main_bp.route("/savechat",     methods=["POST"])(save_chat)
main_bp.route("/refresh_bm25", methods=["POST"])(refresh_bm25_index)