"""Helpers compartilhados: constantes de domínio, validação e datas aware.

Antes este módulo era dead code (nunca importado). Agora concentra as regras
duplicadas (regex de e-mail, "overdue", constantes) num único lugar.
"""
from datetime import datetime, timezone
import re

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
FINISHED_STATUSES = ('done', 'cancelled')

MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
DUE_DATE_FORMAT = '%Y-%m-%d'

# Exige domínio com ponto (rejeita "a@b"); usada em toda a validação de e-mail.
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$')


def now_utc():
    return datetime.now(timezone.utc)


def ensure_aware(dt):
    """SQLite devolve datetimes naive; tratamos naive como UTC para comparar."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_valid_email(email):
    return bool(email and EMAIL_REGEX.match(email))


def calculate_percentage(part, total):
    if not total:
        return 0
    return round((part / total) * 100, 2)


def parse_due_date(date_string):
    """Levanta ValueError se o formato não for YYYY-MM-DD."""
    return datetime.strptime(date_string, DUE_DATE_FORMAT)


def paginate_params():
    """Lê limit/offset da querystring com defaults e teto vindos da config."""
    from flask import request, current_app

    default = current_app.config['DEFAULT_PAGE_SIZE']
    maximum = current_app.config['MAX_PAGE_SIZE']

    try:
        limit = int(request.args.get('limit', default))
    except (TypeError, ValueError):
        limit = default
    limit = max(1, min(limit, maximum))

    try:
        offset = int(request.args.get('offset', 0))
    except (TypeError, ValueError):
        offset = 0
    offset = max(0, offset)

    return limit, offset
