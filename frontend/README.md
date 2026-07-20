# Frontend

Área exclusiva do Colaborador 2, responsável pela interface web/PWA própria, acessibilidade e integração com Matrix.

## Situação

O protótipo visual permanece com dados simulados. O `matrix-js-sdk` `41.9.0` e o primeiro adaptador foram adicionados, mas ainda não estão ligados às telas nem ao login.

## Responsabilidades

- Interface de conversas e mensagens.
- Componentes de mídia.
- Responsividade e acessibilidade.
- Adaptador isolado para `matrix-js-sdk`.
- Sessão, sincronização e estados de erro do cliente Matrix.
- Avaliação e inventário do SDK e de qualquer código aberto incorporado.

## Regra de independência

O frontend deve usar um homeserver Matrix de desenvolvimento e simular estados que não sejam fáceis de produzir. Ele não depende de um backend FastAPI nem da configuração de produção. O Colaborador 1 não deve modificar esta pasta durante o trabalho normal.

## Desenvolvimento local

```bash
cp .env.example .env.local
pnpm install
pnpm dev
```

O homeserver padrão é `http://localhost:8008`. A tela atual continua simulada até o Colaborador 2 integrar o adaptador em `lib/matrix/`.

## Primeira tarefa

Concluir F1 e F2 de `docs/TASKS.md`: revisar o adaptador, implementar a sessão de desenvolvimento e ligar a sincronização ao estado da aplicação, sem modificar `platform/` ou `backend/`.
