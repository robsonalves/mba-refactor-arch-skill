"""HTTP orchestration for produtos. No SQL, no business rules here."""
from flask import request, jsonify

from config import settings
from database import get_db
from models import produto_model


def _validate_produto_payload(dados):
    if not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"
    if dados["preco"] < 0:
        return "Preço não pode ser negativo"
    if dados["estoque"] < 0:
        return "Estoque não pode ser negativo"
    return None


def listar_produtos():
    produtos = produto_model.find_all(get_db())
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.find_by_id(get_db(), id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto():
    dados = request.get_json(silent=True)
    erro = _validate_produto_payload(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    nome = dados["nome"]
    if len(nome) < settings.NAME_MIN_LEN:
        return jsonify({"erro": "Nome muito curto"}), 400
    if len(nome) > settings.NAME_MAX_LEN:
        return jsonify({"erro": "Nome muito longo"}), 400

    categoria = dados.get("categoria", "geral")
    if categoria not in settings.VALID_CATEGORIES:
        return jsonify({"erro": "Categoria inválida. Válidas: " + str(list(settings.VALID_CATEGORIES))}), 400

    produto_id = produto_model.create(
        get_db(), nome, dados.get("descricao", ""), dados["preco"], dados["estoque"], categoria
    )
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    db = get_db()
    if not produto_model.find_by_id(db, id):
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json(silent=True)
    erro = _validate_produto_payload(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_model.update(
        db, id, dados["nome"], dados.get("descricao", ""),
        dados["preco"], dados["estoque"], dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    db = get_db()
    if not produto_model.find_by_id(db, id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    produto_model.delete(db, id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)
    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    resultados = produto_model.search(get_db(), termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
