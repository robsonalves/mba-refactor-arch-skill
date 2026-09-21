"""HTTP orchestration for pedidos. Business rules delegated to pedido_service."""
from flask import request, jsonify

from config import settings
from database import get_db
from models import pedido_model
from services import pedido_service
from services.pedido_service import OrderError


def criar_pedido():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens or len(itens) == 0:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    try:
        resultado = pedido_service.create_order(get_db(), usuario_id, itens)
    except OrderError as exc:
        return jsonify({"erro": str(exc), "sucesso": False}), 400

    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.list_by_usuario(get_db(), usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedido_model.list_all(get_db())
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")
    if novo_status not in settings.VALID_ORDER_STATUSES:
        return jsonify({"erro": "Status inválido"}), 400

    pedido_service.change_status(get_db(), pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    relatorio = pedido_service.sales_report(get_db())
    return jsonify({"dados": relatorio, "sucesso": True}), 200
