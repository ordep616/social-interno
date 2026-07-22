# Backend auxiliar

Área exclusiva do Colaborador 1 para serviços corporativos auxiliares que não duplicam o protocolo Matrix nem o servidor de mensagens.

## Situação

O serviço FastAPI de convites e provisionamento foi autorizado em `DEC-017`. Nenhum código foi implementado ainda. A decisão anterior de usar FastAPI como servidor principal de mensagens continua substituída por `DEC-010`.

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
- Alembic com revisão-base e migração reversível da tabela `invitations`;
- testes de saúde, configuração, banco, convite e ponto de entrada ASGI.

Endpoints de convite, geração de tokens, regras de transição e chamadas administrativas ao Synapse ainda não foram implementados.

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

O arquivo `.env` é local e não deve ser versionado. `.env.example` contém apenas valores fictícios.
