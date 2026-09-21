# Catálogo de Anti-Patterns (Fase 2)

Cruze o código contra este catálogo. Cada item tem **sinais de detecção
acionáveis** e a **severidade** padrão. Ajuste a severidade ao contexto real.
Catálogo agnóstico de stack — os sinais valem para Python/Flask, Node/Express e
outras linguagens (traduza a sintaxe).

> Severidade: **CRITICAL** (segurança/arquitetura que quebra ou expõe) ·
> **HIGH** (violação forte de MVC/SOLID) · **MEDIUM** (padronização/perf/validação) ·
> **LOW** (legibilidade/nomes/magic values).

---

## CRITICAL

### 1. SQL Injection
- **Sinais**: query montada por **concatenação/interpolação de string** com input
  (`"... WHERE x = '" + valor + "'"`, f-strings/template strings em SQL). Login por
  igualdade de string.
- **Por quê**: bypass de auth (`' OR '1'='1`), exfiltração/DROP do banco.
- **Correção**: queries parametrizadas (placeholders `?`/`$1`/`:nome`) ou ORM.

### 2. Remote Arbitrary SQL / Command Execution (Backdoor)
- **Sinais**: endpoint que recebe SQL/comando do body e executa (`execute(req.sql)`);
  rotas `/admin/query`, `/admin/reset-db` sem auth.
- **Por quê**: equivale a RCE sobre o banco/host.
- **Correção**: remover; se necessário, ferramenta interna autenticada fora do web.

### 3. Hardcoded Credentials / Secrets in Source
- **Sinais**: `SECRET_KEY="..."`, `pk_live_...`, `dbPass`, `email_password` no código;
  segredos versionados.
- **Por quê**: vazam em qualquer clone/commit; comprometem produção.
- **Correção**: mover para variáveis de ambiente / secrets manager; rotacionar.

### 4. Secret / Sensitive Data Exposure
- **Sinais**: `/health` ou respostas devolvendo `secret_key`/`debug`; `to_dict()`
  incluindo `password`/hash; **PAN de cartão ou chave logados** (`console.log(cc)`).
- **Por quê**: vazamento de credenciais/PII/PAN (PCI-DSS/OWASP A02).
- **Correção**: nunca serializar/logar segredos; serializer explícito sem senha.

### 5. Insecure Password Handling (Plaintext / Weak / Home-grown Crypto)
- **Sinais**: senha em texto puro; `md5(pwd)` sem salt; "hash" caseiro (loop de
  base64); senha default (`"123456"`).
- **Por quê**: rainbow tables; vazamento do DB expõe todas as senhas.
- **Correção**: `bcrypt`/`argon2` (ou `werkzeug.security`) com salt e work factor.

---

## HIGH

### 6. God Class / God Object / God File
- **Sinais**: uma classe/arquivo acumula conexão de DB + DDL/seed + rotas +
  validação + regra de negócio + persistência.
- **Por quê**: SRP violado; intestável; qualquer mudança toca tudo.
- **Correção**: separar em Model / Controller / Service / Route (ver guidelines).

### 7. Business Logic in Controller/Route (Fat Controller / Anemic Layering)
- **Sinais**: regra de negócio, cálculo, notificações/efeitos colaterais e
  decisões (ex.: aprovação de pagamento) dentro do handler de rota.
- **Por quê**: regra não reusável nem testável; acoplada ao HTTP.
- **Correção**: extrair service layer; controller só orquestra I/O.

### 8. Global Mutable State / Non-Thread-Safe Singleton
- **Sinais**: `globalCache={}`, `totalRevenue=0`, conexão única em variável global
  compartilhada entre requests (`check_same_thread=False`).
- **Por quê**: race conditions, não escala horizontal, acoplamento oculto.
- **Correção**: conexão por request (`flask.g`/pool); store injetado com TTL.

### 9. No Dependency Injection / Tight Coupling
- **Sinais**: funções chamando `get_db()` direto; controller importando model
  concreto; nada mockável sem monkeypatch global.
- **Por quê**: viola DIP; rigidez; baixa testabilidade.
- **Correção**: injetar conexão/serviço por parâmetro/construtor no composition root.

### 10. Debug Mode Enabled in Production
- **Sinais**: `debug=True`, `app.run(debug=True, host="0.0.0.0")`, `DEBUG=True`.
- **Por quê**: console interativo do Werkzeug = RCE; stack traces vazados.
- **Correção**: `debug` por env (default False); servir via WSGI (gunicorn).

### 11. Callback Hell / Swallowed & Missing Error Handling
- **Sinais**: pirâmide de callbacks; `catch`/`except` que ignora o erro; agregação
  manual com contadores (race), risco de `res.json` duplo ou nunca.
- **Por quê**: erros engolidos, respostas inconsistentes, `HEADERS_SENT`.
- **Correção**: `async/await` + `try/catch`; error-handling middleware central.

---

## MEDIUM

### 12. N+1 Query Problem
- **Sinais**: query dentro de loop; buscar nome/relacionado por item; múltiplos
  `count()` que caberiam num `group by`.
- **Por quê**: latência linear/quadrática; pressão no DB.
- **Correção**: `JOIN`/eager loading (`joinedload`); agregação num único SELECT.

### 13. Missing / Inconsistent Input Validation
- **Sinais**: acesso a `body["x"]` sem checar; `int(param)` sem try/except; regex de
  e-mail fraca/duplicada; schema ausente (mesmo com marshmallow/zod instalado).
- **Por quê**: 500 genéricos, dados inconsistentes, confiança no cliente.
- **Correção**: validação por schema na fronteira (`marshmallow`/`pydantic`/`zod`).

### 14. Missing Pagination (Unbounded Result Sets)
- **Sinais**: `GET /coisas` retornando `.all()` sem `limit`/`offset`.
- **Por quê**: estoura memória em escala.
- **Correção**: paginação (`limit`/`offset` ou keyset).

### 15. Duplicated Code (DRY) / Dead Code / Cosmetic Layers
- **Sinais**: mesma regra (ex.: "overdue") repetida em N lugares; serialização
  manual em vez de `to_dict()`; camada `services/` que nunca é importada.
- **Por quê**: divergência na manutenção; falsa sensação de arquitetura.
- **Correção**: centralizar num único lugar; ligar ou remover camadas mortas.

### 16. Broken Referential Integrity / No Transaction Boundary
- **Sinais**: `DELETE` de entidade-pai deixando filhos órfãos; múltiplos inserts
  sem transação (falha no meio deixa dados inconsistentes).
- **Por quê**: dados órfãos, relatórios corrompidos.
- **Correção**: FK `ON DELETE`/soft-delete; envolver operações em transação.

### 17. Overly Permissive CORS
- **Sinais**: `CORS(app)` / `cors()` sem allowlist, liberando `*`.
- **Correção**: restringir `origins`, métodos e headers.

---

## LOW

### 18. Magic Numbers & Magic Strings
- **Sinais**: `10000`/`0.1` (faixas/percentuais), `"4"`, `"PAID"`, porta `5000`
  soltos no código.
- **Correção**: extrair para constantes/enums nomeados ou config.

### 19. Poor Naming / Builtin Shadowing / Cryptic Abbreviations
- **Sinais**: `u`, `e`, `cc`; parâmetro `id` sombreando builtin; campos `usr`/`pwd`.
- **Correção**: nomes de domínio (`user_id`, `email`, `card`).

### 20. print()-based Logging & Leaking Internal Errors
- **Sinais**: `print(...)`/`console.log` como telemetria; `return str(e)` ao cliente.
- **Correção**: `logging` estruturado (JSON, nível, requestId); erro genérico ao cliente.

---

## Detecção de APIs deprecated (obrigatório verificar)

Procure e recomende o equivalente moderno:

| API deprecated | Onde aparece | Equivalente moderno |
|---|---|---|
| `datetime.utcnow()` | Python ≥3.12 | `datetime.now(timezone.utc)` (aware) |
| `Model.query.get(id)` | SQLAlchemy 2.0 (LegacyAPIWarning) | `db.session.get(Model, id)` |
| `sqlite3` callback API (`db.run(cb)`) | Node, callback hell | `better-sqlite3` (sync) ou `sqlite` (Promise) |
| `sqlite3.verbose()` em prod | Node | só em debug |
| registro manual `app.add_url_rule` | Flask | `@app.route` / **Blueprints** |
| `express.json()` sem `limit` | Express | `express.json({ limit: '100kb' })` |
| `crypto` "roll-your-own" | qualquer | lib de hashing consagrada (bcrypt/argon2) |

Se a stack tiver outra API obsoleta, **consulte a doc oficial da versão** e
registre o equivalente atual no relatório (seção "Deprecated APIs").
