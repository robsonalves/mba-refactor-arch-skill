"""Erros de aplicação e handler central.

Os services lançam ApiError (e subclasses) na fronteira de negócio; o handler
central converte em JSON `{'error': ...}` com o status correto, sem vazar stack
trace ao cliente.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    status_code = 500
    message = 'Erro interno'

    def __init__(self, message=None, status_code=None):
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code


class BadRequest(ApiError):
    status_code = 400
    message = 'Dados inválidos'


class Unauthorized(ApiError):
    status_code = 401
    message = 'Não autorizado'


class Forbidden(ApiError):
    status_code = 403
    message = 'Acesso negado'


class NotFound(ApiError):
    status_code = 404
    message = 'Recurso não encontrado'


class Conflict(ApiError):
    status_code = 409
    message = 'Conflito'


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        logger.exception('Erro não tratado: %s', error)
        return jsonify({'error': 'Erro interno'}), 500
