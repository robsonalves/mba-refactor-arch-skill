# Guidelines de Arquitetura — MVC alvo (Fase 3)

O destino da refatoração é **MVC** com fronteiras claras. Adapte os nomes de
pasta à convenção da linguagem, mas mantenha as responsabilidades.

## Camadas e responsabilidades

### Config (`config/` ou `settings`)
- Carrega configuração e **segredos de variáveis de ambiente** (`.env` +
  `process.env` / `os.environ`). **Nada hardcoded.**
- `DEBUG`/porta/CORS/keys vêm daqui. Fornece defaults seguros (debug=false).

### Model (`models/`)
- **Única camada que fala com o banco.** Uma entidade/domínio por arquivo.
- Toda query é **parametrizada** (placeholders), nunca concatenação de string.
- Sem regra de negócio de aplicação (isso é do controller/service); o model
  encapsula persistência e mapeamento linha→objeto/dict.
- Expõe métodos por operação (`find_all`, `find_by_id`, `create`, `update`,
  `delete`), recebendo a conexão/sessão por injeção quando possível.

### View / Routes (`views/` ou `routes/`)
- **Só o registro de rotas** e binding para os controllers. Sem SQL, sem regra.
- Em Flask: Blueprints por domínio. Em Express: `Router` por domínio.

### Controller (`controllers/`)
- Orquestra o fluxo: **request → valida entrada → chama model/service →
  monta resposta**. Fino. Sem SQL direto, sem detalhes de persistência.
- Regra de negócio pesada e efeitos colaterais (notificações, pagamento) vão
  para uma **service layer** (`services/`) quando existirem/forem necessários.

### Middlewares (`middlewares/`)
- **Tratamento de erros centralizado** (um handler que captura exceções e
  devolve JSON `{ error, code }` sem vazar stack/detalhes internos).
- Validação de payload na fronteira (schema), CORS restrito, limites de body.

### Entry point / Composition root (`app.*`)
- Monta o app: cria config, instancia models/controllers, registra rotas e
  middlewares. É o único lugar que "conhece" todas as peças (injeção de
  dependência acontece aqui).

## Estrutura de referência (adapte à stack)

```
src/
├── config/            # settings a partir de env
├── models/            # acesso a dados, queries parametrizadas
├── controllers/       # orquestração por domínio
├── services/          # regra de negócio / efeitos colaterais (quando houver)
├── views/ | routes/   # registro de rotas (blueprints/routers)
├── middlewares/       # error handler, validação, cors
└── app.*              # composition root / entry point
```

## Regras invioláveis
1. **Segurança**: zero credenciais hardcoded; zero SQL por concatenação; zero
   execução de SQL arbitrário vindo de request; senha sempre com hash forte
   (bcrypt/argon2), nunca em texto nem na resposta da API.
2. **Preservar contrato**: mesmas rotas, métodos e formato de resposta.
3. **Boot + endpoints**: a aplicação deve subir sem erro e responder nos
   endpoints originais após a refatoração.
4. **DI sobre singleton global**: dependências entram por parâmetro/construtor,
   não por estado global mutável.
5. **Sem regra de negócio na View/Route**; sem SQL no Controller.

## Princípios SOLID aplicados
- **SRP**: um arquivo/classe, uma razão para mudar (quebra God Class/Object).
- **DIP**: controllers dependem de abstrações (model/service injetado), não do DB.
- **DRY**: extrair validação/serialização/regra duplicada para um único lugar.
