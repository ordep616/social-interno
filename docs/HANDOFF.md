# Repasse para os colaboradores e seus Codex

## Preparação

1. Trabalhar a partir do mesmo repositório Git, cada tarefa em uma branch própria.
2. Atualizar a cópia local antes de iniciar.
3. Abrir o Codex na raiz do repositório.
4. Pedir primeiro uma análise; autorizar implementação separadamente.
5. Não alterar a área pertencente ao outro colaborador.

## Prompt do Colaborador 2 — Frontend

```text
Leia o AGENTS.md e os documentos indicados por ele.

Eu sou o Colaborador 2, responsável pelo frontend, interface web/PWA e integração
do cliente com Matrix usando matrix-js-sdk. Não sou responsável por implantar
ou administrar o Synapse, nem por qualquer serviço de backend.

Analise o estado atual e o docs/TASKS.md. Não implemente nada ainda.
Explique:
1. o contexto da adaptação da plataforma Matrix;
2. as tarefas F1 a F5 atribuídas a mim;
3. como isolar o matrix-js-sdk atrás de um adaptador;
4. como trabalhar com um homeserver de desenvolvimento e estados simulados;
5. quais configurações e convenções compartilhadas precisam ser respeitadas;
6. os riscos e decisões pendentes da minha área;
7. a primeira tarefa de frontend recomendada.

Não altere platform/, backend/, infraestrutura ou segurança. Não copie código
do Telegram Web ou Element Web sem registro de origem, licença e aprovação.
```

## Prompt do Colaborador 1 — Backend e plataforma

```text
Leia o AGENTS.md e os documentos indicados por ele.

Eu sou o Colaborador 1, responsável por todo o backend, pela plataforma
Matrix/Synapse, PostgreSQL, infraestrutura, identidade, segurança e operação.
FastAPI é apenas uma opção para integrações futuras e não será o servidor de mensagens.

Analise o estado atual e o docs/TASKS.md. Não implemente nada ainda.
Explique:
1. o contexto da adaptação do Matrix/Synapse;
2. as tarefas P1 a P5 atribuídas ao Colaborador 1;
3. as dependências mínimas com a interface;
4. os riscos de licença, federação, OIDC, criptografia, retenção e operação;
5. as decisões pendentes;
6. a primeira tarefa de plataforma recomendada.

Não altere frontend/, que pertence ao Colaborador 2. Valide a plataforma com um cliente Matrix genérico e
não crie backend próprio para recursos que o Matrix já oferece.
```

## Prompt para iniciar uma tarefa

```text
Leia o AGENTS.md e os documentos relacionados a esta tarefa.

Minha tarefa é: [descrever a tarefa].

Antes de alterar arquivos:
1. confirme se ela está atribuída ao meu papel;
2. identifique critérios de aceitação e dependências;
3. informe quais arquivos pretende alterar;
4. apresente um plano curto;
5. aguarde minha autorização para implementar.
```

## Regra para trabalho independente

```text
Trabalhe somente na minha área e respeite o Matrix e as convenções aprovadas.
- como Colaborador 2, trabalhe somente em `frontend/`, use um homeserver de desenvolvimento e simule estados de erro;
- como Colaborador 1, trabalhe somente em `platform/` e `backend/` e use clientes Matrix genéricos para validar o Synapse.

Registre dúvidas não bloqueantes para o próximo marco de integração. Não
altere arquivos pertencentes à área do outro colaborador.
```

## Revisão cruzada

```text
Revise as alterações desta branch com base no AGENTS.md, nos critérios de
aceitação e nas decisões compartilhadas.

Procure por alterações fora do escopo, exposição de segredos, quebra do
isolamento, uso indevido de APIs administrativas, código externo sem licença,
duplicação de recursos Matrix e falta de testes ou documentação.

Não implemente correções. Primeiro apresente os achados por prioridade.
```

## Reuniões de integração

Ao final de cada marco, atualizar em conjunto `TASKS.md`, `DECISIONS.md`, `API.md` e `OPEN_SOURCE.md`.
