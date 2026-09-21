# Playbook de Refatoração — Padrões de Transformação (Fase 3)

Para cada anti-pattern, o padrão concreto **antes → depois**. Preserve o
comportamento (mesmas rotas/respostas). Exemplos em Python/Flask e Node/Express;
traduza para a stack real.

---

## 1. SQL Injection → Query parametrizada
**Antes (Python)**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?", (email, senha_hash))
```
**Node**: `db.get("SELECT * FROM users WHERE email = ?", [email])` (nunca template string).

## 2. Segredo hardcoded → Config por ambiente
**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**Depois** (`config/settings.py`)
```python
import os
SECRET_KEY = os.environ["SECRET_KEY"]              # obrigatório, sem default
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```
**Node** (`config/index.js`): `module.exports = { dbPass: process.env.DB_PASS, paymentKey: process.env.PAYMENT_KEY }` + `.env.example`.

## 3. Senha em texto/MD5 → Hash forte
**Antes**
```python
senha TEXT                                  # schema
if row["senha"] == senha: ...               # login
hashlib.md5(pwd.encode()).hexdigest()       # "hash"
```
**Depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash
senha_hash = generate_password_hash(senha)          # bcrypt/scrypt+salt
if check_password_hash(user.senha_hash, senha): ...
```
E **remover `password` do `to_dict()`/resposta**.

## 4. God File/Object → Camadas MVC
**Antes**: `models.py` (350 linhas: SQL + regra + mapping de 4 domínios) ou
`AppManager` (conexão + DDL + rotas + pagamento).
**Depois**
```
models/produto_model.py     # só acesso a dados de produto (parametrizado)
models/usuario_model.py
controllers/produto_controller.py   # orquestra request→model→response
services/pedido_service.py          # regra de negócio de pedido
routes/produto_routes.py            # Blueprint/Router
config/settings.py ; middlewares/error_handler.py ; app.py (composition root)
```
Mova cada responsabilidade para sua camada; um domínio por arquivo.

## 5. Regra de negócio no Controller → Service layer
**Antes**
```python
def criar_pedido():
    # valida, calcula total, baixa estoque, envia email/sms/push tudo aqui
    print("Enviando email...")
```
**Depois**
```python
# controller
def criar_pedido():
    dados = valida_entrada(request.get_json())
    pedido = pedido_service.criar(dados)      # regra fica no service
    return jsonify(pedido), 201
# services/pedido_service.py concentra cálculo, estoque (em transação) e notificação
```

## 6. N+1 → JOIN / eager loading
**Antes**
```python
for pedido in pedidos:
    itens = query("... itens_pedido WHERE pedido_id = " + id)
    for item in itens:
        nome = query("SELECT nome FROM produtos WHERE id = " + item_id)
```
**Depois**
```python
rows = cursor.execute("""
  SELECT p.id, p.status, ip.quantidade, pr.nome
  FROM pedidos p
  JOIN itens_pedido ip ON ip.pedido_id = p.id
  JOIN produtos pr ON pr.id = ip.produto_id
  WHERE p.usuario_id = ?""", (usuario_id,)).fetchall()
# agrupa em memória
```
**SQLAlchemy**: `Task.query.options(joinedload(Task.user), joinedload(Task.category))`.

## 7. Conexão global mutável → Por request / DI
**Antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```
**Depois**
```python
from flask import g
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(settings.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db
@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db: db.close()
```
Models recebem a conexão por parâmetro/injeção (não chamam o global).

## 8. Validação ausente → Schema na fronteira
**Antes**: `dados["produto_id"]` (KeyError→500); `int(priority)` sem try.
**Depois**
```python
from marshmallow import Schema, fields
class ItemPedidoSchema(Schema):
    produto_id = fields.Int(required=True)
    quantidade = fields.Int(required=True, validate=lambda q: q > 0)
dados = PedidoSchema().load(request.get_json())   # 400 estruturado se inválido
```
**Node**: `zod`/`express-validator` no middleware, retornando 400 `{ error }`.

## 9. Error handling espalhado → Middleware central
**Antes**: cada handler com `except Exception as e: return str(e)`.
**Depois**
```python
@app.errorhandler(Exception)
def handle(e):
    app.logger.exception(e)                  # log interno, estruturado
    code = getattr(e, "code", 500)
    return jsonify({"error": "internal_error", "code": code}), code
```
**Node**: `app.use((err, req, res, next) => res.status(err.status||500).json({error:err.code||'internal'}))`.

## 10. Backdoor / endpoint perigoso → Remover
Remova `/admin/query` (SQL arbitrário) e proteja/retire `/admin/reset-db`.
Nada de execução de SQL vindo do request.

## 11. API deprecated → Equivalente moderno
```python
datetime.utcnow()          → datetime.now(timezone.utc)
Model.query.get(id)        → db.session.get(Model, id)
app.add_url_rule(...)      → Blueprint + @bp.route(...)
```
```js
new sqlite3.Database(...)+callbacks → better-sqlite3 (sync)  // ou sqlite (Promise)
express.json()             → express.json({ limit: '100kb' })
```

## 12. Magic numbers → Constantes nomeadas
**Antes**: `if faturamento > 10000: desconto = faturamento * 0.1`
**Depois**
```python
DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
desconto = next((f*p for limite, p in DISCOUNT_TIERS if f > limite), 0)
```

---

## Ordem de aplicação sugerida
1. Config/segredos (destrava o resto sem hardcode).
2. Camada de dados (models parametrizados) — mata SQLi.
3. Controllers/services (tira regra da rota).
4. Rotas/Blueprints + middleware de erro/validação.
5. Segurança de senha + remoção de backdoors + CORS.
6. Deprecated APIs, magic numbers, naming, logging.
7. Validar boot + smoke test dos endpoints.

## Adaptação ao contexto
- **Monolito** (code-smells, ecommerce-legacy): criar a estrutura MVC do zero.
- **Parcialmente em camadas** (task-manager): não recriar tudo — **ligar a service
  layer morta**, remover duplicação, corrigir segurança/deprecated, sem quebrar o
  que já funciona. Refatoração proporcional ao estado atual.
