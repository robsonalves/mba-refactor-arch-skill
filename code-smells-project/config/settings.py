"""Application configuration loaded from environment variables.

Nothing sensitive is hardcoded: secrets and toggles come from the environment,
with safe defaults for local development (DEBUG off, secret generated per boot).
"""
import os
import secrets


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# Secret used for signing. In production it MUST be provided via env.
# Falls back to an ephemeral random value so nothing secret is ever hardcoded.
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Debug is OFF unless explicitly enabled via env (never in production).
DEBUG = _as_bool(os.environ.get("DEBUG"), default=False)

# Database file path.
DB_PATH = os.environ.get("DB_PATH", "loja.db")

# HTTP server binding.
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

# CORS allowlist (comma separated). Defaults to none-open in dev.
_cors_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()]

# Token required to call destructive admin endpoints. If unset, they are denied.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

# Domain constants (no magic numbers scattered in the code).
API_VERSION = "1.0.0"

# Discount tiers for the sales report: (revenue threshold, discount rate).
DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

VALID_CATEGORIES = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
VALID_ORDER_STATUSES = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

NAME_MIN_LEN = 2
NAME_MAX_LEN = 200

# Pagination defaults for unbounded collections.
DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 500
