"""Usuario + auth route registration (Blueprint)."""
from flask import Blueprint

from controllers import usuario_controller

bp = Blueprint("usuarios", __name__)

bp.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar_usuarios, methods=["GET"])
bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_controller.buscar_usuario, methods=["GET"])
bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"])
bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])
