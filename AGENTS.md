# Instruções para os agentes

## Contexto

Este repositório será usado para planejar e, somente após autorização explícita, desenvolver um sistema web privado de comunicação corporativa.

O produto adaptará uma plataforma Matrix auto-hospedada, inicialmente Synapse, e terá interface web própria. A organização controlará autenticação, dados e infraestrutura. O produto não utilizará contas, servidores, datacenters, `api_id` ou `api_hash` do Telegram.

## Estado atual

O projeto está na fase de fundação da prova de conceito Matrix. A configuração local de Synapse/PostgreSQL e o adaptador inicial do SDK já existem, mas o fluxo completo ainda não foi validado.

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
- `docs/API.md`: convenções Matrix e regras para integrações opcionais.
- `docs/OPEN_SOURCE.md`: política de reutilização e licenças.

Não é necessário carregar documentos sem relação com a tarefa atual.


## Colaboradores

### Colaborador 2 — Frontend e SDK Matrix

Responsável por:

- Desenvolver a interface web e a PWA.
- Implementar lista de conversas, chat, compositor e componentes de mídia.
- Criar um adaptador isolado para `matrix-js-sdk`.
- Implementar sessão, sincronização e tratamento de eventos Matrix no cliente.
- Registrar origem e licença do SDK e de qualquer código externo incorporado.
- Garantir responsividade, acessibilidade e estados de erro.

### Colaborador 1 (usuário deste workspace) — Backend, plataforma, infraestrutura e segurança

Responsável por:

- Assumir todo trabalho relacionado a backend e serviços de servidor.
- Implantar e configurar Synapse e PostgreSQL.
- Restringir cadastro e federação externa.
- Integrar o provedor corporativo de identidade por OIDC.
- Configurar políticas, mídia, retenção e administração da plataforma.
- Configurar observabilidade, backup, restauração e ambientes.
- Criar e manter integrações FastAPI somente para lacunas aprovadas, sem duplicar o Matrix.

### Responsabilidade compartilhada

Exigem acordo dos dois colaboradores:

- Aprovação das versões do Synapse, Matrix e `matrix-js-sdk`.
- Configuração compartilhada e convenções de salas e usuários.
- Alterações no escopo do MVP.
- Inclusão de dependências relevantes.
- Incorporação de código de terceiros.
- Política de segurança, auditoria e retenção.
- Escolhas que afetem frontend e backend simultaneamente.

Depois da prova de conceito e da aprovação das convenções, cada colaborador deve trabalhar de forma independente. O frontend usa um homeserver de desenvolvimento e estados simulados; a plataforma é validada com clientes Matrix genéricos. Dúvidas não bloqueantes devem ser registradas para o próximo marco de integração.

## Código aberto e plataforma

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

O `matrix-js-sdk` deve ficar atrás de um adaptador do frontend. Element Web e Telegram Web são apenas referências por padrão; não copiar seus componentes sem registro e aprovação.

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

- O Colaborador 1 possui `platform/` e `backend/`; o Colaborador 2 possui `frontend/`.
- O frontend usa um homeserver Matrix de desenvolvimento e não depende da infraestrutura de produção.
- A plataforma usa clientes Matrix genéricos e não depende da interface própria.
- O protocolo Matrix não deve ser redefinido em contratos internos.
- Extensões corporativas e eventos personalizados exigem contratos versionados.
- A integração acontece apenas nos marcos definidos em `docs/TASKS.md`.

## Restrições

- Não alterar configuração e convenções compartilhadas unilateralmente.
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
