# Repasse para os colaboradores e seus Codex

## Preparação

1. Os dois colaboradores devem trabalhar a partir do mesmo repositório Git.
2. Antes de iniciar, cada um deve atualizar sua cópia local.
3. Cada colaborador deve abrir o Codex na raiz do repositório.
4. Após mudanças importantes no `AGENTS.md`, iniciar uma nova conversa do Codex para carregar as instruções atualizadas.
5. Cada tarefa de implementação deve usar sua própria branch.

## Prompt do outro colaborador — Frontend

```text
Leia o AGENTS.md e os documentos indicados por ele.

Eu sou o colaborador responsável pelo frontend, experiência web e análise
dos componentes de código aberto do Telegram Web.

Analise o estado atual e o docs/TASKS.md. Não implemente nada ainda.
Explique:
1. o contexto do projeto;
2. as tarefas atribuídas a mim;
3. as dependências com o backend;
4. os riscos e decisões pendentes;
5. a primeira tarefa que recomenda executar.
```

## Prompt para você — Backend

```text
Leia o AGENTS.md e os documentos indicados por ele.

Eu sou o responsável principal pelo backend, banco de dados, infraestrutura,
segurança e integrações.

Analise o estado atual e o docs/TASKS.md. Não implemente nada ainda.
Explique:
1. o contexto do projeto;
2. as tarefas atribuídas a mim;
3. as dependências com o frontend;
4. os riscos e decisões pendentes;
5. a primeira tarefa que recomenda executar.
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

Use este complemento nos dois Codex:

```text
Trabalhe somente na minha área e use o contrato compartilhado como limite.
Não dependa da implementação do outro colaborador:
- no frontend, use mocks e exemplos do contrato;
- no backend, use testes de contrato e clientes automatizados.

Se encontrar uma dúvida não bloqueante, registre uma proposta para o próximo
marco de integração e continue com uma suposição compatível com o contrato.
Não altere arquivos pertencentes à área do outro colaborador.
```

## Prompt para revisão cruzada

```text
Revise as alterações desta branch com base no AGENTS.md, nos critérios de
aceitação da tarefa e nos contratos compartilhados.

Procure especialmente por:
- alterações fora do escopo;
- quebra do contrato entre frontend e backend;
- falhas de autorização ou exposição de dados;
- dependências ou código externo sem licença registrada;
- falta de testes ou documentação.

Não implemente correções. Primeiro apresente os achados por prioridade.
```

## Reunião de integração

Ao final de cada ciclo, atualizar em conjunto:

- `TASKS.md`: andamento, bloqueios e próximas tarefas.
- `DECISIONS.md`: decisões novas ou substituídas.
- `API.md`: contratos aprovados.
- `OPEN_SOURCE.md`: código externo avaliado ou incorporado.
