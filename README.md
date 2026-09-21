# Desafio — Skill de Auditoria e Refatoração Arquitetural (`refactor-arch`)

Skill agnóstica de tecnologia que **audita** uma codebase de backend, gera um
**relatório de auditoria** com severidade e arquivo:linha, e **refatora** o
projeto para o padrão **MVC** — validando que a aplicação continua funcionando.

A skill vive em `.claude/skills/refactor-arch/` (copiada nos 3 projetos) e é
invocada com `/refactor-arch` no Claude Code.

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestra as 3 fases (prompt)
└── references/                           # conhecimento de domínio (progressive disclosure)
    ├── project-analysis.md               # heurísticas de detecção de stack/DB/arquitetura
    ├── anti-patterns.md                  # catálogo (20 anti-patterns) + APIs deprecated
    ├── report-template.md                # formato do relatório de auditoria
    ├── architecture-guidelines.md        # regras do MVC alvo (camadas e responsabilidades)
    └── refactoring-playbook.md           # 12 transformações antes/depois
```

---

## A) Análise Manual

Antes de escrever a skill, os três projetos foram lidos manualmente. Resumo dos
problemas de maior impacto por projeto (auditoria completa em `reports/`).

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)
Monolito com pseudo-camadas; responsabilidades vazam entre arquivos.

| Sev | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | **SQL Injection** em todas as queries | `models.py` (login `109-111`, busca `291`, etc.) | Bypass de login (`' OR '1'='1`), exfiltração/DROP do banco |
| CRITICAL | **Execução de SQL arbitrário** | `app.py:59-78` (`/admin/query`) | Qualquer cliente anônimo roda SQL — RCE sobre o DB |
| CRITICAL | **SECRET_KEY hardcoded e vazado** | `app.py:7`, `/health` em `controllers.py` | Forja de sessão; segredo exposto publicamente |
| CRITICAL | **Senha em texto puro + vazada** | `models.py:83,99` (`to_dict`), `database.py` | `GET /usuarios` devolve a senha de todos |
| HIGH | Lógica de negócio/notificação no controller | `controllers.py:208-250` | Regra não testável, acoplada ao HTTP |
| HIGH | Conexão global mutável (`check_same_thread=False`) | `database.py:4-11` | Race conditions sob concorrência |
| HIGH | `debug=True` em produção | `app.py:8,88` | Console do Werkzeug = RCE |
| MEDIUM | N+1 em pedidos | `models.py:171-233` | 1 + N + N·M queries |
| MEDIUM/LOW | CORS aberto · magic numbers de desconto · `print` como log | vários | Superfície de ataque, manutenção |

### Projeto 2 — `ecommerce-api-legacy` (Node/Express, LMS + checkout)
God Object `AppManager` acumula tudo; callbacks aninhados.

| Sev | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Segredos hardcoded** (incl. `pk_live_...`) | `src/utils.js:1-7` | Chave de gateway de produção versionada |
| CRITICAL | **Log de PAN do cartão + chave** | `AppManager.js:45` | Violação de PCI-DSS |
| CRITICAL | **God Object** (conexão+DDL+rotas+pagamento) | `AppManager.js` | SRP violado; intestável |
| CRITICAL | **Cripto caseira** (`badCrypto`) + senha default | `utils.js:17-23` | Senhas efetivamente sem proteção |
| HIGH | Regra de pagamento inline (aprovação por prefixo "4") | `AppManager.js:43-64` | Sem transação, mock inseguro |
| HIGH | Estado global mutável · callback hell + erros engolidos | `utils.js`, `AppManager.js` | Não escala; respostas inconsistentes |
| MEDIUM | Delete sem integridade referencial · sem validação | `AppManager.js:131-137` | Dados órfãos |

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy, Task Manager)
Camadas **parciais** (`models/`, `routes/`, `services/`, `utils/`) — mas
`services/` e `utils/helpers` estavam **mortos** (nunca importados).

| Sev | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | **MD5 sem salt** para senha | `models/user.py:27-32` | Quebrado; rainbow tables |
| CRITICAL | **Hash da senha exposto** na resposta | `models/user.py:16-25`, `user_routes.py` | `to_dict()` inclui `password` |
| CRITICAL | Token falso (não-JWT) + sem auth + SECRET_KEY/SMTP hardcoded | `user_routes.py:207`, `app.py:13` | Broken Access Control |
| HIGH | N+1 · `debug=True` + `create_all` no import | `task_routes.py`, `app.py` | Performance, RCE |
| MEDIUM | Bare `except` · sem paginação · DRY (`is_overdue` 4x) · camadas mortas | vários | Observabilidade, manutenção |
| LOW | **APIs deprecated**: `Query.get()`, `datetime.utcnow()` | vários | Quebra em upgrade |

---

## B) Construção da Skill

**Decisões de design.** O `SKILL.md` é o **prompt orquestrador**: define as 3 fases
(Análise → Auditoria → Refatoração) e a regra inviolável de **pausar e pedir
confirmação** antes de modificar arquivos. O conhecimento de domínio foi separado
em 5 arquivos de referência carregados **sob demanda** (progressive disclosure) —
cada fase lê só o que precisa, mantendo o contexto enxuto:
- `project-analysis.md` (Fase 1), `anti-patterns.md` + `report-template.md` (Fase 2),
  `architecture-guidelines.md` + `refactoring-playbook.md` (Fase 3).

**Catálogo de anti-patterns.** 20 padrões distribuídos por severidade, com
**sinais de detecção acionáveis** ("query montada por concatenação de string",
não "código ruim"). Inclui uma tabela dedicada de **APIs deprecated** →
equivalente moderno (`datetime.utcnow()`→aware, `Query.get()`→`db.session.get()`,
callback do `sqlite3`→`better-sqlite3`, `add_url_rule`→Blueprints).

**Como garanti que é agnóstica de tecnologia.** (1) A Fase 1 **detecta** a stack
por sinais (manifesto de dependências + imports) em vez de assumir; (2) os sinais
do catálogo são conceituais e os exemplos do playbook trazem **Python/Flask e
Node/Express** lado a lado; (3) as guidelines falam de *responsabilidades* de
camada, não de nomes de pasta específicos; (4) validei rodando a **mesma skill,
sem alteração**, nos 3 projetos (2 Flask + 1 Express) — cobrindo desde monolito
totalmente desestruturado até projeto já parcialmente em camadas.

**Desafios e como resolvi.** O maior risco é a Fase 3 **quebrar** o comportamento.
Mitigações: o playbook prega **preservar o contrato público** (mesmas rotas/
respostas) e a skill exige **validação** (boot + smoke test dos endpoints) ao
final. Para o projeto 3 (já em camadas), a refatoração é **proporcional**: em vez
de recriar tudo, a skill liga a service layer morta, remove duplicação e corrige
segurança/deprecated — sem reescrever o que já funcionava.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|:--:|:--:|:--:|:--:|:--:|
| 1 · code-smells-project | Python/Flask | 6 | 5 | 4 | 3 | **18** |
| 2 · ecommerce-api-legacy | Node/Express | 4 | 5 | 4 | 3 | **16** |
| 3 · task-manager-api | Python/Flask+SQLAlchemy | 4 | 4 | 5 | 3 | **16** |

Relatórios completos: `reports/audit-project-{1,2,3}.md`.

### Antes → Depois (estrutura)

| Projeto | Antes | Depois |
|---|---|---|
| 1 | `app.py` + `controllers.py` + `models.py`(SQL+regra) + `database.py`(conexão global) | `config/` · `models/`(parametrizado) · `controllers/` · `routes/`(Blueprints) · `services/` · `middlewares/` · `app.py`(factory) |
| 2 | `src/app.js` + `AppManager.js`(God Object) + `utils.js`(segredos+badCrypto) | `src/{config,db,repositories,services,controllers,routes,middlewares,errors}` + `app.js`(DI) |
| 3 | camadas parciais com `services/`/`utils` **mortos** | service layer **viva** (Task/User/Category/Report) + `utils` reaproveitado + `config/` + `middlewares/` + models seguros + rotas finas + `create_app()` |

### Checklist de validação (os 3 projetos)

| Critério | P1 | P2 | P3 |
|---|:--:|:--:|:--:|
| Fase 1 detecta stack | ✅ | ✅ | ✅ |
| Fase 2 ≥ 5 findings (≥1 CRITICAL/HIGH) | ✅ 18 | ✅ 16 | ✅ 16 |
| Estrutura MVC (config/models/controllers/routes/middlewares) | ✅ | ✅ | ✅ |
| Segredos fora do código (env) | ✅ | ✅ | ✅ |
| SQL parametrizado / injection eliminado | ✅ (`' OR '1'='1`→401) | ✅ | ✅ |
| Senha com hash forte, nunca na resposta | ✅ werkzeug | ✅ bcrypt | ✅ werkzeug |
| N+1 eliminado (JOIN/eager) | ✅ | ✅ | ✅ |
| Error handling central | ✅ | ✅ | ✅ |
| **App sobe sem erro** | ✅ :5001 | ✅ :3002 | ✅ :5003 |
| **Endpoints originais respondem** | ✅ | ✅ | ✅ |
| APIs deprecated corrigidas | ✅ Blueprints | ✅ better-sqlite3 | ✅ `db.session.get`/aware datetime |

**Comportamento em stacks diferentes.** A mesma skill produziu MVC idiomático em
cada ecossistema: Blueprints + `flask.g` no Flask, `Router` + DI + `better-sqlite3`
no Express, e refatoração *proporcional* (ligar service layer) no projeto já
parcialmente organizado — provando a agnosticidade.

> Nota de validação: o sandbox bloqueia acesso ao PyPI/npm; onde a instalação em
> venv limpo não era possível, a validação rodou contra as versões já instaladas
> (idênticas às fixadas nos manifestos). Todos os apps subiram e os endpoints
> responderam nas portas de teste.

---

## D) Como Executar

### Pré-requisitos
- **Claude Code** instalado e configurado (a skill usa `.claude/skills/`).
- Python 3.12 + pip (projetos 1 e 3) e Node 18+ + npm (projeto 2).

### Ordem sugerida e comandos

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"          # Fase 1→2 (gera reports/audit-project-1.md) → confirma → Fase 3
python app.py                    # valida: sobe e responde

# Projeto 2 — Node/Express
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"          # gera reports/audit-project-2.md
node src/app.js                  # valida

# Projeto 3 — Python/Flask+SQLAlchemy
cd ../task-manager-api
pip install -r requirements.txt
python seed.py                   # popula o banco
claude "/refactor-arch"          # gera reports/audit-project-3.md
python app.py                    # valida
```

### Como validar que funcionou
- A aplicação **inicia sem erro** (debug controlado por env, default off).
- Os **endpoints originais respondem** — smoke test com `curl` (ex.: `GET /produtos`,
  `POST /login`, `GET /reports/summary`). Deltas intencionais de segurança: senha
  nunca aparece na resposta; `/admin/query` removido; `/health` não vaza segredo.
- Confira o relatório em `reports/audit-project-N.md` e o checklist acima.

> A skill é **copiável**: a mesma pasta `.claude/skills/refactor-arch/` está nos 3
> projetos. Se a auditoria achar poucos problemas ou a refatoração falhar, ajuste
> os arquivos de referência e rode de novo (2-4 iterações é normal).
