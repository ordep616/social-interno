# Sistema interno de comunicação privada

Projeto de uma plataforma web/PWA para comunicação exclusiva entre funcionários de uma organização.

O repositório está na fase de fundação da prova de conceito. A estrutura local de Synapse/PostgreSQL e o fork inicial do Cinny foram adicionados; login corporativo e fluxo completo ainda não foram validados.

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
- Colaborador 2: fork corporativo do Cinny, interface web/PWA, experiência e integração Matrix no cliente.

## Estrutura de trabalho

- `platform/`: área do Colaborador 1 para configuração e operação do Synapse.
- `backend/`: área do Colaborador 1 para integrações corporativas opcionais.
- `frontend/`: área do Colaborador 2 para o fork corporativo do Cinny e suas personalizações.
- `docs/`: planejamento, tarefas, decisões e política de código aberto.

Cada área de implementação possui um `AGENTS.md` local com seus limites. Uma IA
deve ler primeiro o `AGENTS.md` da raiz e depois o arquivo local da pasta em que
trabalhará.

O diretório `contracts/` somente será criado novamente se uma extensão corporativa própria for aprovada.

## Regra principal

O produto adaptará uma plataforma Matrix auto-hospedada e utilizará um fork corporativo do Cinny, registrado em `docs/OPEN_SOURCE.md`. Telegram Web e Element Web permanecem apenas como referências.
