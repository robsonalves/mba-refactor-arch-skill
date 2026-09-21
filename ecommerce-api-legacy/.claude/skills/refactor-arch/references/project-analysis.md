# Análise de Projeto — Heurísticas de Detecção (Fase 1)

Objetivo: descobrir **linguagem, framework, banco de dados, domínio e arquitetura
atual** sem assumir nada. Use os sinais abaixo; combine vários antes de concluir.

## 1. Linguagem e gerenciador de pacotes

| Sinal (arquivo) | Linguagem | Ecossistema |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `*.py` | Python | pip/poetry |
| `package.json`, `*.js`, `*.ts` | JavaScript/TypeScript | npm/pnpm/yarn |
| `go.mod`, `*.go` | Go | go modules |
| `pom.xml`, `build.gradle`, `*.java` | Java | maven/gradle |
| `composer.json`, `*.php` | PHP | composer |
| `Gemfile`, `*.rb` | Ruby | bundler |

Leia o **manifesto de dependências** para extrair versões exatas.

## 2. Framework (a partir das dependências + imports)

- Python: `flask` → Flask; `fastapi` → FastAPI; `django` → Django.
- Node: `express` → Express; `@nestjs/*` → NestJS; `koa`/`fastify` → idem.
- Confirme lendo os imports do entrypoint (`app.py`, `src/app.js`, `main.*`).
- Anote a **versão** vinda do manifesto (ex.: `express ^4.18.2`, `flask==3.1.1`).

## 3. Banco de dados

- Procure drivers nas dependências: `sqlite3` (stdlib py ou pacote node), `psycopg`,
  `mysqlclient`, `pg`, `mongoose`, `sequelize`, `sqlalchemy`, `prisma`.
- Procure DDL/conexão no código: `CREATE TABLE`, `new sqlite3.Database(...)`,
  `sqlite3.connect(...)`, `.env`/config com host/porta.
- Liste as **tabelas** a partir dos `CREATE TABLE` encontrados.
- In-memory (`:memory:`) vs arquivo vs servidor — anote.

## 4. Domínio

Infira das **tabelas**, **rotas** e **nomes de entidade**. Ex.: rotas
`/produtos`, `/pedidos`, tabela `itens_pedido` → *E-commerce*; `courses`,
`enrollments`, `payments` → *LMS/checkout*; `tasks`, `projects` → *Task Manager*.

## 5. Arquitetura atual (classifique)

- **Monolito procedural / God file**: tudo (rotas + regra + acesso a dados) em 1-2
  arquivos ou numa única classe/objeto "manager".
- **Pseudo-camadas por arquivo**: existem `models`/`controllers`/`routes` mas as
  responsabilidades vazam (regra de negócio no model, SQL no controller).
- **Parcialmente em camadas**: já há `models/`, `routes/`, `services/`, `utils/`
  como pastas, porém com problemas de segurança/acoplamento/qualidade.
- **MVC adequado**: separação real de Model, View/Route, Controller, Config.

## 6. Contagem de arquivos

Conte apenas **arquivos de código-fonte** relevantes (exclua lockfiles, `.md`,
`node_modules`, venvs). Reporte esse número no resumo da Fase 1.

## Saída da fase (formato)

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language: <...>
Framework: <... versão>
Dependencies: <principais>
Domain: <...>
Architecture: <uma das categorias acima + descrição curta>
Source files: <N> files analyzed
DB tables: <tabela1, tabela2, ...>
================================
```
