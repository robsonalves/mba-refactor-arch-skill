"""System endpoints: index, health and the guarded admin reset."""
from flask import request, jsonify, abort

from config import settings
from database import get_db


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": settings.API_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    db = get_db()
    db.execute("SELECT 1")
    counts = {
        "produtos": db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
        "usuarios": db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
        "pedidos": db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
    }
    # No secrets, debug flags or internal paths are ever exposed here.
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": settings.API_VERSION,
    }), 200


def reset_database():
    """Guarded destructive reset: requires a matching X-Admin-Token header.

    Denied entirely when no ADMIN_TOKEN is configured.
    """
    token = request.headers.get("X-Admin-Token")
    if not settings.ADMIN_TOKEN or token != settings.ADMIN_TOKEN:
        abort(403)

    db = get_db()
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    db.execute("DELETE FROM produtos")
    db.execute("DELETE FROM usuarios")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
