"""Tokens de autenticação assinados (substitui o 'fake-jwt-token').

Usa itsdangerous (dependência do Flask) para emitir um token assinado com o
SECRET_KEY. Não é adivinhável como o token fake anterior.
"""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_SALT = 'auth-token'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)


def generate_token(user):
    return _serializer().dumps({'user_id': user.id, 'role': user.role})


def verify_token(token, max_age=None):
    if max_age is None:
        max_age = current_app.config.get('TOKEN_MAX_AGE', 86400)
    try:
        return _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
