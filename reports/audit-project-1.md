================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project (API de E-commerce "Loja")
Stack: Python + Flask 3.1.1 (flask-cors 5.0.1)
Files: 4 analyzed | ~690 lines of code (app.py 89, models.py 315, controllers.py 293, database.py 87)
Date: 2026-09-21

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 4 | LOW: 3
Total: 18 findings

## Findings

### [CRITICAL] SQL Injection por concatenação de string em todas as queries dinâmicas
File: `models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 148-149, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 289-297`
Description: Toda query que recebe input é montada por concatenação de string (`"... WHERE id = " + str(id)`, `"... WHERE email = '" + email + "'"`, `LIKE '%" + termo + "%'`). Nenhuma usa placeholders.
Impact: Bypass de autenticação (`' OR '1'='1' --` no `/login`), exfiltração e destruição do banco (`DROP`/`DELETE` via qualquer campo). OWASP A03.
Recommendation: Substituir por queries parametrizadas (placeholders `?`) em todos os models; a busca com filtros opcionais monta a lista de params dinamicamente, nunca o valor no SQL.

### [CRITICAL] Backdoor de execução de SQL arbitrário — endpoint `/admin/query`
File: `app.py:59-78`
Description: Endpoint POST que recebe SQL cru do body (`dados.get("sql")`) e o executa direto, sem autenticação. Equivale a RCE sobre o banco.
Impact: Qualquer requisição anônima lê/altera/apaga qualquer tabela (`DROP TABLE usuarios`). Comprometimento total.
Recommendation: Remover o endpoint por completo. Operações administrativas só via ferramenta interna autenticada fora da superfície web.

### [CRITICAL] Endpoint destrutivo sem autenticação — `/admin/reset-db`
File: `app.py:47-57`
Description: POST público que apaga `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem qualquer verificação de credencial.
Impact: Negação de serviço / perda total de dados por qualquer anônimo.
Recommendation: Remover ou proteger atrás de token administrativo (env `ADMIN_TOKEN`) validado por middleware; nunca expor sem auth em produção.

### [CRITICAL] SECRET_KEY hardcoded no código-fonte
File: `app.py:7`
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` versionado no repositório.
Impact: Segredo vaza em qualquer clone/commit; permite forjar sessões/tokens assinados. OWASP A05/A07.
Recommendation: Ler de variável de ambiente (`config/settings.py` → `os.environ`), sem default de produção; rotacionar a chave comprometida.

### [CRITICAL] Exposição de segredo e config sensível no `/health`
File: `controllers.py:287-289`
Description: A resposta do `/health` devolve `"db_path"`, `"debug": True` e `"secret_key": "minha-chave-super-secreta-123"` em texto claro, sem auth.
Impact: Vazamento direto do SECRET_KEY e de detalhes internos por endpoint público. OWASP A02.
Recommendation: `/health` retorna apenas status/contadores; nunca serializar segredos nem flags internas.

### [CRITICAL] Senha em texto puro — armazenada, comparada e retornada na API
File: `database.py:31,76-78` (schema `senha TEXT` + seed plaintext), `models.py:110` (login por igualdade), `models.py:83-84,99` (`to_dict` inclui `senha`)
Description: Senhas gravadas em texto puro; login compara string diretamente; `get_todos_usuarios`/`get_usuario_por_id` incluem o campo `senha` na resposta JSON.
Impact: Vazamento do banco expõe todas as senhas; a API entrega as senhas a quem listar usuários. OWASP A02/A07.
Recommendation: Hash forte com `werkzeug.security.generate_password_hash`/`check_password_hash` (coluna `senha_hash`); serializer de usuário nunca inclui senha/hash.

### [HIGH] Estado global mutável de conexão (singleton não thread-safe)
File: `database.py:4-10`
Description: Conexão única em variável global `db_connection`, reaproveitada entre requests com `check_same_thread=False`.
Impact: Race conditions, cursores/transações compartilhados entre requests concorrentes, não escala horizontalmente. Viola thread-safety do sqlite3.
Recommendation: Conexão por request via `flask.g` + `teardown_appcontext` para fechar; DDL/seed apenas uma vez no startup.

### [HIGH] Regra de negócio e efeitos colaterais dentro do controller (fat controller)
File: `controllers.py:208-210, 247-250`
Description: Notificações (email/SMS/push) e decisões de negócio disparadas por `print` dentro do handler de rota de pedido e de atualização de status.
Impact: Regra não reusável nem testável, acoplada ao HTTP; efeito colateral misturado com serialização de resposta.
Recommendation: Extrair service layer (`services/pedido_service.py` + `notification_service`); controller só orquestra I/O.

### [HIGH] Debug mode habilitado (RCE via console Werkzeug)
File: `app.py:8, 88`
Description: `app.config["DEBUG"] = True` e `app.run(debug=True, host="0.0.0.0")` fixos.
Impact: O console interativo do Werkzeug em erro permite execução remota de código; stack traces vazam para o cliente.
Recommendation: `DEBUG` vindo de env com default `false`; servir via WSGI (gunicorn) em produção.

### [HIGH] God file — `models.py` acumula 4 domínios + regra de negócio
File: `models.py:1-315`
Description: Um único arquivo concentra acesso a dados de produtos, usuários, pedidos e itens, além de cálculo de faturamento/desconto (`relatorio_vendas`) e mapeamento manual repetido.
Impact: SRP violado; qualquer mudança toca tudo; difícil de testar isoladamente.
Recommendation: Separar em `models/produto_model.py`, `usuario_model.py`, `pedido_model.py`; cálculo de relatório vira service.

### [HIGH] Acoplamento forte / sem injeção de dependência
File: `models.py:5,25,44` (etc. — todas as funções chamam `get_db()`), `controllers.py:3,266`
Description: Models e controllers chamam `get_db()` global direto; nada é injetável/mockável sem monkeypatch.
Impact: Viola DIP; baixa testabilidade; rigidez.
Recommendation: Injetar a conexão por parâmetro (controller obtém `get_db()` e passa ao model); composition root monta as dependências.

### [MEDIUM] Problema N+1 na listagem de pedidos
File: `models.py:187-199` (`get_pedidos_usuario`) e `models.py:219-231` (`get_todos_pedidos`)
Description: Para cada pedido roda uma query de itens, e para cada item uma query de nome de produto (loops aninhados de queries).
Impact: Latência linear/quadrática e pressão no banco conforme cresce o volume.
Recommendation: Um único `SELECT` com `LEFT JOIN` entre pedidos, itens_pedido e produtos; agrupar em memória.

### [MEDIUM] Validação de entrada ausente/inconsistente
File: `controllers.py:170-171` (`/login` sem checar `dados is None`), `controllers.py:195,240` (acesso a chaves sem schema), `models.py:140,144` (`item["produto_id"]`/`item["quantidade"]` sem validação)
Description: Payloads acessados sem schema; `request.get_json()` pode ser `None` (500 em vez de 400); itens de pedido sem validação de tipo/positividade.
Impact: 500 genéricos, dados inconsistentes, confiança no cliente.
Recommendation: Validação por schema na fronteira (helper de validação/`marshmallow`) devolvendo 400 estruturado.

### [MEDIUM] Ausência de paginação em coleções
File: `models.py:7` (`SELECT * FROM produtos`), `models.py:75` (usuarios), `models.py:206` (pedidos)
Description: `GET /produtos`, `/usuarios`, `/pedidos` retornam o conjunto inteiro sem `limit`/`offset`.
Impact: Estouro de memória e latência em escala.
Recommendation: Paginação por `limit`/`offset` (ou keyset) com defaults seguros.

### [MEDIUM] CORS totalmente aberto
File: `app.py:9`
Description: `CORS(app)` sem allowlist libera qualquer origem (`*`).
Impact: Qualquer site pode chamar a API no navegador do usuário.
Recommendation: Restringir `origins`/métodos/headers via config (env `CORS_ORIGINS`).

### [LOW] Magic numbers e magic strings de desconto/status/porta
File: `models.py:257-262` (faixas `10000/5000/1000` e `0.1/0.05/0.02`), `app.py:85,88` (porta `5000` fixa), status literais espalhados
Description: Faixas e percentuais de desconto, porta e strings de status embutidos no código.
Impact: Divergência de manutenção; difícil ajustar regra/config.
Recommendation: Extrair para constantes nomeadas / enum de status / config (porta via env `PORT`).

### [LOW] Logging via `print()` e vazamento de erro interno ao cliente
File: `controllers.py:8,11,57,61,106,161,179,182,208-210,219,248-250` (`print`), e `return str(e)` em todos os `except` (ex. `controllers.py:12,22,62,96,...`)
Description: `print` usado como telemetria; exceções devolvidas cruas ao cliente (`{"erro": str(e)}`).
Impact: Sem níveis/estrutura; vaza detalhes internos e mensagens de SQL ao cliente.
Recommendation: `logging` estruturado (nível, mensagem); error handler central devolve erro genérico ao cliente.

### [LOW] Sem boundary transacional / integridade referencial na criação de pedido
File: `models.py:148-168`
Description: Insert do pedido, dos itens e baixa de estoque em múltiplos `execute` com um único `commit` no fim, sem `BEGIN`/rollback explícito; falha no meio deixa dados parciais. Tabelas sem FK/`ON DELETE`.
Impact: Pedidos/itens órfãos ou estoque inconsistente em falha parcial.
Recommendation: Envolver a operação em transação com rollback em erro; declarar FKs.

## Deprecated APIs
- `app.add_url_rule(...)` (`app.py:11-30`) → usar **Blueprints** (`Blueprint` + `@bp.route`).
- `flask_cors.CORS(app)` sem allowlist (`app.py:9`) → `CORS(app, origins=[...])` restrito.
- Comparação de senha em texto puro (`models.py:110`) → `werkzeug.security.check_password_hash`.

================================
Total: 18 findings
================================
