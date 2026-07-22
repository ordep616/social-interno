# Backend auxiliar

Área exclusiva do Colaborador 1 para serviços corporativos auxiliares que não duplicam o protocolo Matrix nem o servidor de mensagens.

## Situação

O serviço FastAPI de convites e provisionamento foi autorizado em `DEC-017`. A fundação, o modelo persistente e a camada interna de emissão e ciclo de vida dos convites já estão implementados. A decisão anterior de usar FastAPI como servidor principal de mensagens continua substituída por `DEC-010`.

## Serviço autorizado

O primeiro escopo do backend auxiliar é:

- criar, listar e revogar convites administrativos;
- validar convite secreto de uso único com validade de 24 horas;
- criar contas pela API administrativa suportada pelo Synapse;
- armazenar papéis próprios sem conceder administração global do Synapse;
- registrar auditoria sem guardar tokens, senhas ou credenciais administrativas;
- apoiar posteriormente bloqueio, redefinição de senha e desligamento.

O contrato está definido em `../docs/API.md` e segue o estilo REST aprovado em `DEC-018`. A revogação usa `DELETE` com remoção lógica para preservar auditoria, e o aceite do convite cria um cadastro por `POST /v1/registrations`.

## Limites

- Todo serviço de backend pertence ao Colaborador 1.
- O Colaborador 2 não deve modificar esta pasta.
- Não implementar salas, mensagens, sincronização, presença ou mídia que já existam no Matrix.
- Não criar serviço auxiliar sem caso de uso e decisão registrados.
- Não acessar diretamente o banco do Synapse para implementar regras de negócio.
- Não expor tokens administrativos ao frontend.
- Usar PostgreSQL e credenciais próprios, separados do banco lógico do Synapse.
- Manter a credencial administrativa do Synapse somente no servidor.

## Possíveis usos futuros

- Integração com RH ou ERP.
- Integração futura com OIDC, se posteriormente aprovada.
- Relatórios ou exportações aprovados.
- Fluxos administrativos específicos.

A fundação aprovada em `DEC-019` usa CPython `>=3.14,<3.15`, FastAPI síncrono, Uvicorn, SQLAlchemy `2.0.x`, Psycopg 3 com extra `binary`, Alembic, `pydantic-settings` e HTTPX. O ambiente será gerenciado por `uv` com `uv.lock`; Ruff, mypy, pytest e pytest-cov formam a verificação inicial de qualidade.

As versões exatas e dependências transitivas estão fixadas no `uv.lock` e inventariadas em `../docs/OPEN_SOURCE.md`. As obrigações da `LGPL-3.0-only` do Psycopg e as bibliotecas incluídas pelo extra `binary` ainda exigem conferência antes de homologação ou produção.

## Fundação executável

A fundação inicial contém apenas:

- aplicação FastAPI com `GET /health`;
- configuração validada por variáveis `BACKEND_*`;
- criação preguiçosa do engine e das sessões SQLAlchemy;
- modelo `Invitation` que armazena apenas o hash SHA-256 do token;
- modelo `UserRoleAssignment` que associa uma identidade Matrix a um papel próprio;
- Alembic com revisão-base e migrações reversíveis de `invitations` e `user_role_assignments`;
- gerador de token URL-safe com 256 bits de entropia e hash SHA-256;
- repositório SQLAlchemy com paginação e transições atômicas;
- serviço interno para emissão, validação, revogação, reserva, conclusão e liberação;
- testes de saúde, configuração, banco, convite e ponto de entrada ASGI.

O token aberto existe apenas no retorno da emissão e não aparece no `repr` do resultado. A emissão fixa validade de 24 horas. A reserva usa uma atualização condicional de `pending` para `processing`, impedindo que duas tentativas processem o mesmo convite; a conclusão e a liberação também usam transições condicionais.

Endpoints REST, validação da sessão Matrix, aplicação da autorização nos endpoints, limites de tentativa, auditoria e chamadas administrativas ao Synapse ainda não foram implementados.

## Bootstrap do primeiro administrador

O primeiro `platform_admin` é atribuído por um comando local, depois que a conta Matrix correspondente já existir no Synapse. O comando não cria a conta, não recebe senha ou token e não concede administração global do Synapse.

Com o banco próprio migrado e as variáveis `BACKEND_*` disponíveis, execute na pasta `backend/`:

```bash
PYTHONPATH=src uv run python -m \
  social_internal_backend.commands.bootstrap_platform_admin @admin:localhost
```

Repetir o comando para a mesma identidade é idempotente. Depois do primeiro bootstrap, outra identidade é recusada; promoções posteriores deverão usar o processo administrativo separado e auditado previsto em `DEC-017`. Um bloqueio transacional no PostgreSQL impede que duas execuções concorrentes criem dois primeiros administradores.

## Desenvolvimento local

Na pasta `backend/`:

```bash
uv sync
cp .env.example .env
uv run uvicorn social_internal_backend.main:app --app-dir src --host 127.0.0.1 --port 8081
```

Verificações:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

Com um PostgreSQL próprio disponível pela `BACKEND_DATABASE_URL`:

```bash
uv run alembic upgrade head
uv run alembic check
```

A migração de convites foi validada com upgrade, downgrade e reaplicação em PostgreSQL `17.6-alpine`. O banco rejeitou papéis fora do contrato, hashes inválidos e estados `used` ou `revoked` sem seus campos obrigatórios.

O serviço interno também foi validado em PostgreSQL `17.6-alpine`: emissão, validade de 24 horas, validação sem mutação, revogação idempotente, expiração, liberação após falha e conclusão funcionaram. Em duas reservas simultâneas do mesmo token, apenas uma avançou para `processing`.

A migração de papéis e o bootstrap foram validados no mesmo PostgreSQL com upgrade, downgrade e reaplicação. O comando foi testado de forma idempotente e duas execuções simultâneas com identidades diferentes resultaram em somente um `platform_admin` inicial.

O arquivo `.env` é local e não deve ser versionado. `.env.example` contém apenas valores fictícios.
