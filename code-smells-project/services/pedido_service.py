"""Business logic for orders: stock validation, total computation, sales report.

The controller only orchestrates I/O; the domain rules live here.
"""
from config import settings
from models import pedido_model, produto_model
from services import notification_service


class OrderError(Exception):
    """Raised for domain validation failures (mapped to HTTP 400 upstream)."""


def create_order(db, usuario_id, itens):
    """Validate stock, compute total, persist atomically and notify."""
    validated_items = []
    total = 0
    for item in itens:
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if not isinstance(produto_id, int) or not isinstance(quantidade, int) or quantidade <= 0:
            raise OrderError("Item inválido: produto_id e quantidade positivos são obrigatórios")

        produto = produto_model.find_by_id(db, produto_id)
        if produto is None:
            raise OrderError(f"Produto {produto_id} não encontrado")
        if produto["estoque"] < quantidade:
            raise OrderError(f"Estoque insuficiente para {produto['nome']}")

        total += produto["preco"] * quantidade
        validated_items.append({
            "produto_id": produto_id,
            "quantidade": quantidade,
            "preco_unitario": produto["preco"],
        })

    pedido_id = pedido_model.persist_order(db, usuario_id, total, validated_items)
    notification_service.notify_order_created(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def change_status(db, pedido_id, novo_status):
    pedido_model.update_status(db, pedido_id, novo_status)
    notification_service.notify_status_change(pedido_id, novo_status)


def _discount_for(faturamento):
    for limite, taxa in settings.DISCOUNT_TIERS:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def sales_report(db):
    agg = pedido_model.sales_aggregates(db)
    faturamento = agg["faturamento"]
    total_pedidos = agg["total_pedidos"]
    desconto = _discount_for(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": agg["pendentes"],
        "pedidos_aprovados": agg["aprovados"],
        "pedidos_cancelados": agg["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
