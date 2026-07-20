# Sistema interno de comunicação privada

Projeto de uma plataforma web/PWA para comunicação exclusiva entre funcionários de uma organização.

O repositório está na fase de fundação da prova de conceito. A estrutura local de Synapse/PostgreSQL e o adaptador inicial de `matrix-js-sdk` foram adicionados; login, integração visual e fluxo completo ainda não foram implementados.

## Documentação

- [Visão do projeto](docs/PROJECT.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Tarefas e responsáveis](docs/TASKS.md)
- [Decisões](docs/DECISIONS.md)
- [Contrato inicial da API](docs/API.md)
- [Código aberto e licenças](docs/OPEN_SOURCE.md)
- [Repasse para os colaboradores](docs/HANDOFF.md)

## Participantes

- Colaborador 1 (usuário deste workspace): todo o backend, plataforma Matrix/Synapse, PostgreSQL, infraestrutura, identidade, segurança e integrações opcionais.
- Colaborador 2: frontend, interface web/PWA, experiência e integração com `matrix-js-sdk`.

## Estrutura de trabalho

- `platform/`: área do Colaborador 1 para configuração e operação do Synapse.
- `backend/`: área do Colaborador 1 para integrações corporativas opcionais.
- `frontend/`: área do Colaborador 2 para interface própria e adaptador do SDK Matrix.
- `docs/`: planejamento, tarefas, decisões e política de código aberto.

O diretório `contracts/` somente será criado novamente se uma extensão corporativa própria for aprovada.

## Regra principal

O produto adaptará uma plataforma Matrix auto-hospedada e terá interface própria. Telegram Web e Element Web poderão servir como referência, mas seus códigos não serão incorporados sem análise e aprovação.
