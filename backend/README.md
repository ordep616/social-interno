# Backend

Área do responsável por backend, banco de dados, infraestrutura, segurança e integrações.

## Situação

Somente estrutura de planejamento. Nenhuma tecnologia ou implementação foi iniciada.

## Responsabilidades

- API HTTP compatível com `contracts/openapi.yaml`.
- Eventos WebSocket compatíveis com `contracts/events/`.
- Banco de dados e migrações.
- Autenticação e autorização.
- Conversas, mensagens e arquivos.
- Auditoria, retenção e administração.
- Redis, armazenamento de objetos, observabilidade e backup.

## Regra de independência

O backend deve ser executável e testável sem o frontend. Use testes de contrato e clientes automatizados como consumidores.

## Primeira tarefa

Executar B1 de `docs/TASKS.md` somente depois de escolher a tecnologia e registrar a decisão em `docs/DECISIONS.md`.
