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

### Outro colaborador — Frontend e código aberto

Responsável por:

- Analisar os clientes web abertos do Telegram.
- Criar o inventário de componentes potencialmente reutilizáveis.
- Desenvolver a interface web e a PWA.
- Implementar lista de conversas, chat, compositor e componentes de mídia.
- Integrar o frontend à API HTTP e aos eventos WebSocket corporativos.
- Garantir responsividade, acessibilidade e estados de erro.

### Responsável principal (usuário deste workspace) — Backend, infraestrutura e segurança

Responsável por:

- Modelar banco de dados e migrações.
- Implementar API HTTP e servidor WebSocket.
- Implementar autenticação, autorização e controle administrativo.
- Implementar mensagens, grupos, anexos, auditoria e retenção.
- Configurar armazenamento, Redis, observabilidade, backup e ambientes.
- Integrar o provedor corporativo de identidade.

### Responsabilidade compartilhada

Exigem acordo dos dois colaboradores:

- Aprovação da versão inicial dos contratos da API e eventos WebSocket.
- Alterações no escopo do MVP.
- Inclusão de dependências relevantes.
- Incorporação de código de terceiros.
- Política de segurança, auditoria e retenção.
- Escolhas que afetem frontend e backend simultaneamente.

Depois que um contrato for marcado como aprovado, cada colaborador deve trabalhar de forma independente. O frontend usa mocks baseados no contrato; o backend implementa o contrato com testes próprios. Dúvidas não bloqueantes devem ser registradas para o próximo marco de integração, sem interromper o trabalho do outro colaborador.

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

## Trabalho independente

- Frontend e backend vivem em diretórios e branches separados.
- O frontend não deve depender de um backend local para desenvolver ou testar telas.
- O backend não deve depender de componentes visuais para executar testes.
- Exemplos JSON e um servidor mock representam o backend para o frontend.
- Testes de contrato representam o frontend para o backend.
- Mudanças incompatíveis criam uma nova versão do contrato; não altere silenciosamente a versão vigente.
- A integração acontece apenas nos marcos definidos em `docs/TASKS.md`.

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
