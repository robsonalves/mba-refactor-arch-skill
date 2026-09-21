================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy (Frankenstein LMS)
Stack: JavaScript (Node.js) + Express ^4.18.2 + sqlite3 ^5.1.6 (SQLite in-memory)
Files: 3 analyzed | ~181 lines of code
Date: 2026-09-21

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 3
Total: 16 findings

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets in Source
File: `src/utils.js:1-7`
Description: Objeto `config` traz `dbUser`, `dbPass` (`"senha_super_secreta_prod_123"`), `smtpUser` e a chave de pagamento de PRODUÇÃO `paymentGatewayKey: "pk_live_1234567890abcdef"` em texto puro no código.
Impact: Segredos vazam em qualquer clone/commit; a chave `pk_live_...` compromete a conta de pagamento real (OWASP A02).
Recommendation: Mover para variáveis de ambiente via `config/` (dotenv + `process.env`), fornecer `.env.example`, remover do fonte e rotacionar as chaves expostas.

### [CRITICAL] Card PAN + Payment Key Logged (PCI-DSS)
File: `src/AppManager.js:45`
Description: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` loga o número completo do cartão (PAN) e a chave do gateway a cada checkout.
Impact: Violação direta de PCI-DSS e OWASP A02 — PAN e segredo em logs/telemetria expõem dados de cartão e credencial de produção.
Recommendation: Nunca logar PAN nem segredos; se precisar rastrear, logar apenas os últimos 4 dígitos mascarados e um id de transação, com logging estruturado.

### [CRITICAL] Insecure Password Handling (Home-grown Crypto + Default Password)
File: `src/utils.js:17-23`, `src/AppManager.js:68`, `src/AppManager.js:12,18`
Description: `badCrypto` é um "hash" caseiro (loop de 10000 concatenações de base64, truncado em 10 chars, sem salt); a senha default `"123456"` é aplicada quando `pwd` é vazio; schema guarda `pass TEXT` e o seed insere senha `'123'` em texto puro.
Impact: Hash reversível/colidível e sem salt — vazamento do DB expõe todas as senhas; senha default fraca permite acesso trivial.
Recommendation: Substituir por `bcrypt` (salt + work factor), exigir senha na fronteira e remover o default; nunca retornar/serializar o hash.

### [CRITICAL] SQL Injection Risk via String-built Query Surface
File: `src/AppManager.js:57`
Description: O audit_log usa placeholder, porém o valor interpolado ``Checkout curso ${cid} por ${userId}`` monta a mensagem por template string com input do request (`cid`) antes de persistir; o padrão de concatenar input em strings de SQL/persistência está presente e é o vetor clássico de SQLi caso migre para concatenação direta.
Impact: Confiança em input não validado dentro de operações de escrita; risco de injeção/poluição de dados e, em manutenção, de SQLi por concatenação.
Recommendation: Validar/normalizar `c_id` como inteiro na fronteira e manter estritamente queries parametrizadas em toda a camada de dados (models/repositories).

### [HIGH] God Object (AppManager)
File: `src/AppManager.js:4-141`
Description: A classe `AppManager` acumula conexão de DB (`:memory:`), DDL + seed (`initDb`), registro de rotas, regra de negócio de pagamento, persistência e montagem de resposta HTTP.
Impact: SRP violado; classe intestável; qualquer mudança toca conexão, schema, rotas e regra ao mesmo tempo.
Recommendation: Quebrar em Config / Models(Repositories) / Services / Controllers / Routes / Middlewares com composition root em `app.js`.

### [HIGH] Business Logic in Route Handler (Fat Controller)
File: `src/AppManager.js:43-64`
Description: A decisão de aprovação de pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`), criação de usuário, matrícula, pagamento, audit log e cache estão inline dentro do handler de `POST /api/checkout`.
Impact: Regra de pagamento acoplada ao HTTP, não reusável nem testável; efeitos colaterais misturados à I/O.
Recommendation: Extrair um `CheckoutService` com `PaymentGateway` injetado; controller só orquestra request→service→response.

### [HIGH] Global Mutable State
File: `src/utils.js:9-10,12-15`, `src/AppManager.js:7`
Description: `globalCache = {}` e `totalRevenue = 0` são estado global mutável compartilhado; `logAndCache` escreve no cache global; a conexão SQLite é única na instância compartilhada entre requests.
Impact: Race conditions, acoplamento oculto, não escala horizontalmente; `totalRevenue` é importado mas nunca usado (estado morto).
Recommendation: Remover estado global; conexão gerida no módulo de DB/composição, cache (se necessário) injetado com TTL.

### [HIGH] Callback Hell + Swallowed/Missing Error Handling
File: `src/AppManager.js:37-77`, `src/AppManager.js:80-129`, `src/AppManager.js:133-136`
Description: Pirâmide de callbacks aninhados do `sqlite3`; erros de `INSERT audit_logs` e do `DELETE` são ignorados (callback recebe `err` e não trata); o report agrega por contadores manuais (`coursesPending`/`enrPending`) com risco de `res.json` duplo ou nunca enviado.
Impact: Erros engolidos, respostas inconsistentes, risco de `ERR_HTTP_HEADERS_SENT` e vazamento de recursos.
Recommendation: Migrar para API síncrona/Promise (`better-sqlite3`) + `try/catch` e middleware de erro central; remover agregação por contador.

### [HIGH] No Dependency Injection / Tight Coupling
File: `src/AppManager.js:1-2,7`, `src/app.js:1-10`
Description: `AppManager` instancia diretamente `new sqlite3.Database`, importa `config`/`badCrypto` concretos e registra rotas; nada é injetado nem mockável sem monkeypatch.
Impact: Viola DIP; rigidez e baixa testabilidade (impossível trocar gateway de pagamento ou DB em teste).
Recommendation: Injetar conexão, repositories e gateway por construtor; composition root único em `app.js`.

### [MEDIUM] Missing Input Validation
File: `src/AppManager.js:29-35`
Description: Só existe checagem de presença (`if (!u || !e || !cid || !cc)`); não há validação de formato de e-mail, de `c_id` ser inteiro, nem do formato/tamanho do cartão; `pwd` não é exigido.
Impact: 500 genéricos, dados inconsistentes, confiança total no cliente.
Recommendation: Validação por schema na fronteira (`express-validator` ou `zod`) retornando 400 estruturado.

### [MEDIUM] Broken Referential Integrity / No Transaction Boundary
File: `src/AppManager.js:131-137`, `src/AppManager.js:50-63`
Description: `DELETE FROM users` remove o usuário e deixa `enrollments`/`payments` órfãos (a própria resposta admite: "ficaram sujos no banco"); o checkout faz 3 inserts (enrollment, payment, audit) sem transação — falha no meio deixa dados inconsistentes.
Impact: Dados órfãos, relatórios financeiros corrompidos, inconsistência parcial.
Recommendation: Envolver o checkout em transação e o delete em cascade/transação (remover pagamentos+matrículas antes do usuário) ou soft-delete.

### [MEDIUM] Overly Permissive / Absent CORS and No Body Limit
File: `src/app.js:6`
Description: `express.json()` é usado sem `limit`; não há política de CORS configurada (nenhum allowlist), o app aceita payloads arbitrários sem limite.
Impact: Exposição a payloads grandes (DoS) e ausência de controle de origem.
Recommendation: `express.json({ limit: '100kb' })` e `cors` restrito por allowlist de origens/métodos.

### [MEDIUM] N+1 Query in Financial Report
File: `src/AppManager.js:83-127`
Description: O relatório busca todos os cursos, depois para cada curso busca enrollments e para cada enrollment faz 2 queries (usuário + pagamento) em loop.
Impact: Latência quadrática e pressão no DB conforme cresce o número de matrículas.
Recommendation: Substituir por um único SELECT com `JOIN` entre courses/enrollments/users/payments e agregar em memória.

### [LOW] Magic Values (Strings e Numbers)
File: `src/AppManager.js:46`, `src/utils.js:19,22`
Description: `"4"` (prefixo de aprovação de cartão), `"PAID"`/`"DENIED"`, `10000` e `substring(0,10)` do hash caseiro, porta `3000` soltos no código.
Impact: Regras escondidas em literais, difíceis de manter e propensas a divergência.
Recommendation: Extrair para constantes/enums nomeados (`PaymentStatus`, `APPROVED_CARD_PREFIX`) e config.

### [LOW] Poor Naming / Cryptic Abbreviations
File: `src/AppManager.js:29-33`
Description: Variáveis `u`, `e`, `p`, `cid`, `cc` e campos de payload `usr`/`eml`/`pwd`/`c_id` são crípticos e não expressam domínio.
Impact: Baixa legibilidade e maior chance de erro na manutenção.
Recommendation: Usar nomes de domínio (`name`, `email`, `password`, `courseId`, `card`); mapear o payload externo explicitamente na camada de validação.

### [LOW] print()-based Logging & Leaking Internal Details
File: `src/utils.js:13`, `src/AppManager.js:45,59`, `src/AppManager.js:135`
Description: `console.log` usado como telemetria; a resposta do DELETE vaza detalhe interno de implementação ("ficaram sujos no banco") ao cliente.
Impact: Ausência de logging estruturado; vazamento de detalhes internos na resposta HTTP.
Recommendation: Logging estruturado (nível, timestamp, requestId) sem PII/segredos; respostas genéricas ao cliente.

## Deprecated APIs
- `sqlite3` callback API — `new sqlite3.Database(...)` + `db.run/get/all(cb)` (`src/AppManager.js:7,37-136`) → usar `better-sqlite3` (síncrono) ou `sqlite` (Promise) para eliminar o callback hell.
- `sqlite3.verbose()` em execução normal (`src/AppManager.js:1`) → habilitar verbosidade só em debug.
- `crypto` "roll-your-own" (`src/utils.js:17-23` `badCrypto`) → `bcrypt`/`argon2`.
- `express.json()` sem `limit` (`src/app.js:6`) → `express.json({ limit: '100kb' })`.

================================
Total: 16 findings
================================
