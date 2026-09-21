"""Data access for the `usuarios` entity.

Passwords are stored hashed (senha_hash) and are NEVER serialized back to the
API. The public serializer intentionally omits any credential field.
"""


def _to_public_dict(row):
    """Serialize a user WITHOUT the password hash."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def find_all(db, limit, offset=0):
    rows = db.execute(
        "SELECT * FROM usuarios ORDER BY id LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return [_to_public_dict(r) for r in rows]


def find_by_id(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_public_dict(row) if row else None


def find_by_email(db, email):
    """Return the raw row (incl. senha_hash) for authentication purposes only."""
    return db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def create(db, nome, email, senha_hash, tipo="cliente"):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid
