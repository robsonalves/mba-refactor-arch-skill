"""Configuração da aplicação carregada de variáveis de ambiente.

Nada de segredo hardcoded: tudo vem de os.environ (com defaults seguros para
desenvolvimento). Em produção, SECRET_KEY e credenciais SMTP devem ser
fornecidas via ambiente / secrets manager.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_list(name, default):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(',') if item.strip()]


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Segredo de assinatura de sessão/token. Trocar em produção via env.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-secret-change-me')

    DEBUG = _env_bool('FLASK_DEBUG', False)
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = _env_int('PORT', 5000)

    # CORS restrito a uma allowlist (nunca '*').
    CORS_ORIGINS = _env_list('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')

    # SMTP para o NotificationService.
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = _env_int('SMTP_PORT', 587)
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

    # Paginação de listagens.
    DEFAULT_PAGE_SIZE = _env_int('DEFAULT_PAGE_SIZE', 50)
    MAX_PAGE_SIZE = _env_int('MAX_PAGE_SIZE', 100)

    # Validade do token de autenticação (segundos).
    TOKEN_MAX_AGE = _env_int('TOKEN_MAX_AGE', 86400)
