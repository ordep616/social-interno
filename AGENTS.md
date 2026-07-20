# Instruções para os agentes

## Contexto

Este repositório será usado para planejar e, somente após autorização explícita, desenvolver um sistema web privado de comunicação corporativa.

O produto terá backend, autenticação e armazenamento próprios. Ele não utilizará contas, servidores, datacenters, `api_id` ou `api_hash` do Telegram.

## Estado atual

O projeto está na fase de planejamento e divisão de responsabilidades.

- Não implemente funcionalidades sem solicitação explícita.
- Não transforme pedidos de planejamento em alterações de código.
- Antes de qualquer mudança, diferencie claramente: documentação, protótipo, implementação, infraestrutura ou publicação.
- Não apague nem reverta arquivos sem autorização explícita.

## Leitura obrigatória

Antes de começar uma tarefa, leia os documentos relevantes:

- `docs/PROJECT.md`: objetivo, MVP e limites.
- `docs/ARCHITECTURE.md`: arquitetura pretendida.
- `docs/TASKS.md`: responsáveis e andamento.
- `docs/DECISIONS.md`: decisões já tomadas.
- `docs/API.md`: contrato inicial entre frontend e backend.
- `docs/OPEN_SOURCE.md`: política de reutilização e licenças.

Não é necessário carregar documentos sem relação com a tarefa atual.

## Colaboradores

### Colaborador 1 — Frontend e código aberto

Responsável por:

- Analisar os clientes web abertos do Telegram.
- Criar o inventário de componentes potencialmente reutilizáveis.
- Desenvolver a interface web e a PWA.
- Implementar lista de conversas, chat, compositor e componentes de mídia.
- Integrar o frontend à API HTTP e aos eventos WebSocket corporativos.
- Garantir responsividade, acessibilidade e estados de erro.

### Colaborador 2 — Backend, infraestrutura e segurança

Responsável por:

- Modelar banco de dados e migrações.
- Implementar API HTTP e servidor WebSocket.
- Implementar autenticação, autorização e controle administrativo.
- Implementar mensagens, grupos, anexos, auditoria e retenção.
- Configurar armazenamento, Redis, observabilidade, backup e ambientes.
- Integrar o provedor corporativo de identidade.

### Responsabilidade compartilhada

Exigem acordo dos dois colaboradores:

- Contratos da API e eventos WebSocket.
- Alterações no escopo do MVP.
- Inclusão de dependências relevantes.
- Incorporação de código de terceiros.
- Política de segurança, auditoria e retenção.
- Escolhas que afetem frontend e backend simultaneamente.

## Reutilização de código do Telegram

Nenhum código deve ser incorporado antes de registrar:

- Repositório oficial de origem.
- Hash do commit.
- Arquivos ou componentes utilizados.
- Licença aplicável.
- Dependências, fontes, ícones, sons e demais ativos relacionados.
- Alterações realizadas.
- Aprovação dos dois colaboradores e, quando necessário, revisão jurídica.

Não utilizar no produto corporativo:

- MTProto ou GramJS.
- TDLib como camada de comunicação.
- `api_id` ou `api_hash`.
- Login do Telegram por telefone ou QR Code.
- Datacenters, bots, canais ou busca global do Telegram.
- Nome, logotipo ou identidade visual oficial do Telegram.

Componentes visuais só podem falar com interfaces próprias do projeto. Eles não devem importar tipos ou clientes da Telegram API.

## Processo de trabalho

1. Leia a tarefa e os documentos relacionados.
2. Confirme o responsável em `docs/TASKS.md`.
3. Identifique dependências com o trabalho do outro colaborador.
4. Apresente um plano antes de mudanças grandes ou irreversíveis.
5. Trabalhe em uma branch específica, nunca diretamente na `main`.
6. Mantenha a alteração pequena e limitada à tarefa.
7. Execute os testes aplicáveis quando houver implementação.
8. Atualize decisões, contratos e inventário quando necessário.
9. Entregue a alteração para revisão do outro colaborador.

## Restrições

- Não alterar contratos compartilhados unilateralmente.
- Não adicionar dependências sem justificativa e revisão de licença.
- Não copiar código externo sem atualizar `docs/OPEN_SOURCE.md`.
- Não inserir segredos ou credenciais no repositório.
- Não implementar funcionalidades fora do MVP sem aprovação.
- Não publicar nem realizar deploy sem autorização explícita.

## Critério de conclusão

Uma tarefa só está concluída quando:

- Os critérios de aceitação foram atendidos.
- Os testes relevantes passaram.
- A documentação necessária foi atualizada.
- Não existem credenciais ou dados pessoais indevidos no código.
- Código externo possui origem e licença registradas.
- A alteração está pronta para revisão do outro colaborador.

## Orientação inicial ao Codex

Ao iniciar uma nova conversa, o colaborador deve informar seu papel e pedir apenas uma análise do estado atual antes de autorizar implementação.
