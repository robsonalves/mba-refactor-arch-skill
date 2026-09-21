# Template do Relatório de Auditoria (Fase 2)

Gere o relatório **exatamente** neste formato. Salve em
`reports/audit-project-N.md` na raiz do repositório.

Regras:
- Findings **ordenados por severidade**: CRITICAL → HIGH → MEDIUM → LOW.
- Todo finding tem **arquivo e linhas exatas**.
- O `## Summary` traz a contagem por severidade.
- Mínimo de **5 findings**, com **pelo menos 1 CRITICAL ou HIGH**.

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack: <Linguagem> + <Framework versão>
Files: <N> analyzed | ~<linhas> lines of code
Date: <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>
Total: <n> findings

## Findings

### [CRITICAL] <Nome do anti-pattern>
File: `<arquivo>:<linha ou intervalo>`
Description: <o que está errado, objetivamente>
Impact: <consequência técnica/segurança>
Recommendation: <como corrigir rumo ao MVC>

### [HIGH] <Nome do anti-pattern>
File: `<arquivo>:<linhas>`
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] ...
### [LOW] ...

## Deprecated APIs
- `<api antiga>` (`arquivo:linha`) → usar `<equivalente moderno>`

================================
Total: <n> findings
================================
```

## Boas práticas do relatório
- Não use "código ruim" — descreva o sinal concreto ("query montada por
  concatenação de string em `models.py:110`").
- Uma linha de `Recommendation` por finding, acionável.
- Se não houver APIs deprecated, escreva "Nenhuma API deprecated detectada."
