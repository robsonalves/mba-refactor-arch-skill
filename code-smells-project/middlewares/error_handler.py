"""Centralized error handling: never leaks stack traces or internal messages."""
import logging

from werkzeug.exceptions import HTTPException
from flask import jsonify

logger = logging.getLogger("app")


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return jsonify({"erro": exc.description, "code": exc.code}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        logger.exception("unhandled_error")
        # Generic message to the client; details stay in the server logs.
        return jsonify({"erro": "internal_error", "code": 500}), 500
