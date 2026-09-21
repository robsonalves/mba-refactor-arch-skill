"""Data access for `pedidos` / `itens_pedido`. All queries are parameterized."""


def persist_order(db, usuario_id, total, validated_items):
    """Insert order, its items and decrement stock inside a single transaction.

    validated_items: list of dicts with produto_id, quantidade, preco_unitario.
    """
    try:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid
        for item in validated_items:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)"
                " VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        db.commit()
        return pedido_id
    except Exception:
        db.rollback()
        raise


def _group_orders(rows):
    """Group flat JOIN rows into orders with nested items (fixes N+1)."""
    orders = {}
    order_sequence = []
    for row in rows:
        pedido_id = row["pedido_id"]
        if pedido_id not in orders:
            orders[pedido_id] = {
                "id": pedido_id,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            order_sequence.append(pedido_id)
        # A LEFT JOIN yields a NULL item row for orders without items.
        if row["produto_id"] is not None:
            orders[pedido_id]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_nome"] else "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return [orders[pid] for pid in order_sequence]


_ORDER_JOIN = """
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, ip.quantidade, ip.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
"""


def list_by_usuario(db, usuario_id):
    rows = db.execute(
        _ORDER_JOIN + " WHERE p.usuario_id = ? ORDER BY p.id", (usuario_id,)
    ).fetchall()
    return _group_orders(rows)


def list_all(db):
    rows = db.execute(_ORDER_JOIN + " ORDER BY p.id").fetchall()
    return _group_orders(rows)


def update_status(db, pedido_id, novo_status):
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def sales_aggregates(db):
    """Return raw sales aggregates in a single grouped query plus totals."""
    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0

    status_rows = db.execute(
        "SELECT status, COUNT(*) AS n FROM pedidos GROUP BY status"
    ).fetchall()
    by_status = {row["status"]: row["n"] for row in status_rows}

    return {
        "total_pedidos": total_pedidos,
        "faturamento": faturamento,
        "pendentes": by_status.get("pendente", 0),
        "aprovados": by_status.get("aprovado", 0),
        "cancelados": by_status.get("cancelado", 0),
    }
