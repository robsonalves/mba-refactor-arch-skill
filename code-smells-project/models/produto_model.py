"""Data access for the `produtos` entity. All queries are parameterized."""
from config import settings

_COLUMNS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    return {col: row[col] for col in _COLUMNS}


def find_all(db, limit=settings.DEFAULT_PAGE_LIMIT, offset=0):
    rows = db.execute(
        "SELECT * FROM produtos ORDER BY id LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return [_to_dict(r) for r in rows]


def find_by_id(db, produto_id):
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _to_dict(row) if row else None


def create(db, nome, descricao, preco, estoque, categoria):
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
        " VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def update(db, produto_id, nome, descricao, preco, estoque, categoria):
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?,"
        " categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()
    return True


def delete(db, produto_id):
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    return True


def search(db, termo=None, categoria=None, preco_min=None, preco_max=None):
    """Filtered search. Filters are appended as bound parameters, never inlined."""
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        like = f"%{termo}%"
        params.extend((like, like))
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    rows = db.execute(query, tuple(params)).fetchall()
    return [_to_dict(r) for r in rows]
