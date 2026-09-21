"""System route registration: index, health and guarded admin reset."""
from flask import Blueprint

from controllers import system_controller

bp = Blueprint("system", __name__)

bp.add_url_rule("/", "index", system_controller.index, methods=["GET"])
bp.add_url_rule("/health", "health_check", system_controller.health_check, methods=["GET"])
bp.add_url_rule("/admin/reset-db", "reset_database", system_controller.reset_database, methods=["POST"])
