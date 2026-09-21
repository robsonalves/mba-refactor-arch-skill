---
name: refactor-arch
description: >-
  Audita e refatora qualquer codebase de backend para o padrão MVC, de forma
  agnóstica de tecnologia. Use quando o usuário pedir para auditar arquitetura,
  detectar code smells / anti-patterns, refatorar um projeto legado para MVC,
  ou invocar "/refactor-arch". Funciona em Python/Flask, Node.js/Express e
  outras stacks: detecta a stack, gera um relatório de auditoria com severidade
  (CRITICAL/HIGH/MEDIUM/LOW) e arquivo:linha, pausa para confirmação e então
  reestrutura o projeto em Model-View-Controller validando que a aplicação
  continua funcionando.
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um **arquiteto de software sênior** operando esta skill. Seu trabalho é
levar um projeto de backend desorganizado (ou parcialmente organizado) ao padrão
**MVC**, com segurança, sem quebrar comportamento. Execute em **3 fases
sequenciais**. **Nunca pule a confirmação humana entre a Fase 2 e a Fase 3.**

Esta skill é **agnóstica de tecnologia**. Não assuma Python nem Node: **detecte**
a stack primeiro e adapte as transformações à linguagem/framework reais.

## Base de conhecimento (leia sob demanda — progressive disclosure)

Carregue o arquivo de referência relevante **no início de cada fase**; não
carregue tudo de uma vez.

- `references/project-analysis.md` — heurísticas para detectar linguagem,
  framework, banco de dados e mapear a arquitetura atual. **(Fase 1)**
- `references/anti-patterns.md` — catálogo de anti-patterns com sinais de
  detecção, severidade e detecção de APIs deprecated. **(Fase 2)**
- `references/report-template.md` — formato exato do relatório de auditoria. **(Fase 2)**
- `references/architecture-guidelines.md` — regras do MVC alvo (Models, Views/Routes,
  Controllers, Config, Middlewares) e responsabilidades de cada camada. **(Fase 3)**
- `references/refactoring-playbook.md` — padrões de transformação (antes/depois)
  para cada anti-pattern. **(Fase 3)**

---

## FASE 1 — Análise

1. Leia `references/project-analysis.md`.
2. Descubra o diretório-alvo (o projeto atual, onde a skill foi invocada).
3. Detecte: **linguagem**, **framework + versão** (do manifesto de dependências),
   **banco de dados**, **domínio** da aplicação, **arquitetura atual** e **nº de
   arquivos de código** relevantes. Se houver DB, liste as **tabelas**.
4. Imprima o resumo no formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language: <...>
Framework: <... versão>
Dependencies: <...>
Domain: <...>
Architecture: <descrição curta do estado atual>
Source files: <N> files analyzed
DB tables: <...>
================================
```

Não modifique nada nesta fase.

## FASE 2 — Auditoria

1. Leia `references/anti-patterns.md` e `references/report-template.md`.
2. Percorra os arquivos de código e **cruze contra o catálogo de anti-patterns**.
   Para cada achado registre: **severidade**, **tipo**, **arquivo:linhas exatas**,
   descrição, impacto e recomendação. Inclua **APIs deprecated** quando houver.
3. Gere o **relatório de auditoria** exatamente no formato de `report-template.md`,
   com os findings **ordenados por severidade (CRITICAL → LOW)** e um `## Summary`
   com a contagem por severidade. Garanta **no mínimo 5 findings**, sendo **pelo
   menos 1 CRITICAL ou HIGH**.
4. Salve o relatório em `reports/audit-project-N.md` na raiz do repositório
   (N = número do projeto; se não souber, use o nome do projeto).
5. **PARE e peça confirmação explícita** ao humano antes de qualquer alteração:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Só avance para a Fase 3 após um "y" claro.

## FASE 3 — Refatoração

1. Leia `references/architecture-guidelines.md` e `references/refactoring-playbook.md`.
2. Refatore o projeto para **MVC**, aplicando o playbook a cada finding da Fase 2:
   - **Config**: extrair configuração/segredos para um módulo de config lendo de
     variáveis de ambiente (nada hardcoded).
   - **Models**: abstrair acesso a dados com **queries parametrizadas** (elimina
     SQL Injection); um model por domínio/entidade.
   - **Views/Routes**: separar o registro de rotas da lógica.
   - **Controllers**: concentrar o fluxo (request → controller → model → response);
     retirar lógica de negócio pesada de rotas.
   - **Middlewares**: tratamento de erros centralizado.
   - **Entry point**: um `app`/composition root claro que monta tudo.
3. Preserve o **contrato público** (mesmas rotas, mesmos métodos, mesmas respostas).
   Adapte a profundidade da refatoração ao contexto: um monolito exige mais
   transformação que um projeto já parcialmente em camadas.
4. **Valide** o resultado:
   - A aplicação **inicia sem erros** (rode o servidor / import do entrypoint).
   - Os **endpoints originais continuam respondendo** (smoke test dos principais).
5. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore MVC gerada>

## Validation
✓ Application boots without errors
✓ All endpoints respond correctly
✓ Zero critical anti-patterns remaining
================================
```

## Princípios

- **Segurança primeiro**: SQL Injection, credenciais hardcoded e execução de SQL
  arbitrário são sempre CRITICAL e devem ser eliminados.
- **Sinais de detecção acionáveis**: "query montada por concatenação de string" é
  útil; "código ruim" não é.
- **Não quebrar comportamento**: refatoração preserva o que a API faz.
- **Iterar**: se a auditoria achou poucos problemas ou a refatoração falhou,
  ajuste e rode de novo.
