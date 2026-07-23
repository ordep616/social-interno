# Tarefas independentes e marcos de integração

## Princípio

O Matrix define o protocolo compartilhado. Depois que configuração, autenticação e convenções forem aprovadas, os colaboradores trabalham em paralelo: um mantém o fork corporativo do Cinny; o outro implanta, protege e opera o Synapse.

## Etapa conjunta curta — prova de conceito e congelamento

- [~] Confirmar Synapse após a prova de conceito; configuração inicial criada, revisão final pendente.
- [~] Avaliar Synapse `1.156.0`, Cinny `v4.12.3` e `matrix-js-sdk` `41.7.0`; validação conjunta pendente.
- [x] Definir federação privada por lista de permissão, iniciando sem organizações parceiras e sem listener de federação exposto.
- [x] Definir política híbrida de criptografia ponta a ponta para o MVP.
- [x] Aprovar a ativação de identidade previamente definida em `DEC-022`.
- [ ] Definir domínio de produção e formato definitivo dos identificadores.
- [ ] Definir convenções para conversas diretas, grupos e departamentos.
- [x] Executar prova de conceito: dois usuários, uma sala, mensagem, leitura e arquivo.

Aceitação: a equipe comprova o fluxo mínimo e registra as decisões antes da personalização ampla.

## Colaborador 1 — Backend, plataforma, infraestrutura e segurança

Todo trabalho de backend pertence ao Colaborador 1. Esta trilha pode ser validada com um cliente Matrix genérico, sem depender da interface própria.

### P1 — Fundação do homeserver

- [x] Criar a área exclusiva `platform/` e documentar seus limites.
- [x] Preparar e executar Synapse e PostgreSQL em Compose no ambiente local.
- [x] Fixar versões iniciais das imagens e registrar suas licenças.
- [x] Configurar domínio local, logs e verificação de saúde.
- [x] Criar dois usuários de teste sem credenciais reais.
- [x] Validar mensagens, histórico, leitura e mídia com o cliente web local.

Aceitação: o homeserver inicia e o fluxo básico funciona sem o frontend próprio.

### P2 — Isolamento e identidade

- [x] Desabilitar cadastro público na configuração local.
- [x] Retirar o listener de federação, configurar lista vazia e validar o bloqueio localmente e pela borda pública temporária.
- [x] Aprovar contrato REST e fundação técnica reproduzível para o serviço FastAPI de convites.
- [x] Implementar a fundação executável do FastAPI com saúde, configuração, PostgreSQL/Alembic e verificações de qualidade.
- [x] Criar o modelo e a migração reversível de convites e validar suas restrições em PostgreSQL isolado.
- [~] Implementar o serviço FastAPI de convites administrativos de uso único, com validade de 24 horas; geração segura, repositório, ciclo de vida interno, endpoints administrativos e controle de acesso concluídos; endpoints públicos, limites e auditoria pendentes.
- [x] Criar armazenamento próprio de papéis e procedimento local, idempotente e serializado para o primeiro `platform_admin`.
- [x] Implementar cliente Matrix `whoami` e autorização interna de `platform_admin`, sem persistir ou registrar o token.
- [~] Implementar provisionamento, bloqueio, redefinição de senha e desligamento
  de usuários; o cliente `PUT /users/{user_id}` permanece fundação para ciclo
  de vida, mas está excluído da ativação por também modificar contas
  existentes; mecanismo create-only, orquestração, auditoria e demais
  operações ainda pendentes.
- [x] Planejar e aprovar a orquestração interna do cadastro como saga durável em `DEC-021`, antes de modelo, migração ou implementação.
- [x] Implementar o modelo e a migração reversível de `registration_attempts`, com restrições e índices parciais validados em PostgreSQL isolado.
- [x] Implementar o repositório de `registration_attempts`, com consultas ativas e transições condicionais validadas sem assumir os limites da futura unidade de trabalho.
- [x] Revisar e aprovar conjuntamente a ativação de identidades em `DEC-022`.
- [ ] Migrar convites para `target_user_id`, unicidade
  parcial por identidade ativa e estado terminal `conflicted`.
- [ ] Implementar `GET /v1/me/capabilities` sem conceder criação de usuários a
  `user` ou `group_admin`.
- [ ] Executar prova de conceito create-only do registro administrativo por
  segredo compartilhado, revogar o dispositivo e o token de sessão retornados
  antes da conclusão e comprovar que conta existente nunca é modificada.
- [ ] Adaptar `registration_attempts` para guardar somente o identificador do
  dispositivo de provisionamento necessário à revogação e à reconciliação,
  nunca o `access_token`.
- [ ] Registrar o shared-secret registration como incompatível com MAS e exigir
  nova decisão conjunta de provisionamento antes de qualquer adoção futura do
  Matrix Authentication Service.
- [ ] Adaptar emissão, pré-validação, unidade de trabalho e orquestração ao
  contrato aprovado, sem aceitar `username` do funcionário.
- [ ] Implementar limites, auditoria e cabeçalhos de segurança antes de
  publicar a ativação.
- [x] Definir os papéis `user`, `group_admin` e `platform_admin`; a promoção a `platform_admin` será separada do convite.
- [ ] Avaliar OIDC como evolução posterior, sem bloquear o MVP baseado em convite.
- [ ] Testar acessos negados e revogação de sessão.

Aceitação: somente identidades corporativas autorizadas entram e não há comunicação externa.

### P3 — Dados e mídia

- [ ] Configurar PostgreSQL para homologação.
- [ ] Definir armazenamento e limites de mídia.
- [ ] Configurar retenção de mensagens e arquivos após aprovação da política.
- [ ] Planejar e testar backup e restauração conjunta de banco, mídia e configuração.
- [ ] Definir verificação antimalware, se exigida.

Aceitação: dados e anexos podem ser restaurados e respeitam limites documentados.

### P4 — Operação e segurança

- [ ] Configurar TLS, proxy reverso e cabeçalhos de segurança.
- [ ] Configurar métricas, logs, alertas e trilha administrativa.
- [ ] Definir processo de atualização e correção de vulnerabilidades.
- [ ] Executar testes de carga e limites do piloto.
- [ ] Escrever procedimentos de implantação, recuperação e incidente.

Aceitação: o ambiente de homologação é observável, recuperável e pronto para avaliação de segurança.

### P5 — Integrações opcionais

- [ ] Levantar lacunas que Synapse, Matrix e suas APIs administrativas não atendem.
- [ ] Priorizar integrações com RH, ERP, relatórios ou auditoria personalizada.
- [ ] Criar novas integrações FastAPI somente após aprovar outra necessidade concreta.
- [ ] Manter qualquer serviço auxiliar fora do caminho principal das mensagens.

Aceitação: nenhum backend personalizado duplica funcionalidades nativas da plataforma.

## Colaborador 2 — Frontend, interface web e experiência

Esta trilha utiliza um homeserver Matrix local ou compartilhado e não depende da configuração de produção.

### F1 — Fundação do fork

- [x] Criar estrutura exclusiva de `frontend/`.
- [x] Aprovar o Cinny como base do frontend.
- [x] Registrar origem, commit e licença AGPL do Cinny.
- [x] Incorporar o Cinny `v4.12.3` sem o histórico Git externo.
- [~] Restringir o cliente ao homeserver corporativo; configuração local criada, validação pendente.
- [ ] Definir nome, identidade e ativos próprios.
- [ ] Documentar o procedimento de atualização do fork.

Aceitação: o fork inicia, conecta somente ao homeserver configurado e preserva licença, origem e rastreabilidade das alterações.

### F2 — Ativação, sessão e sincronização

- [ ] Criar `/activate` conforme `DEC-022`, ler `#token`, limpar
  a URL, pré-validar no FastAPI e pedir somente senha.
- [ ] Redirecionar a ativação concluída para o login Matrix normal com apenas o
  `username` preenchido.
- [ ] Restaurar e encerrar sessão com segurança.
- [ ] Inicializar sincronização e tratar reconexão.
- [ ] Criar estados de carregamento, vazio, indisponibilidade e acesso negado.
- [ ] Simular erros para não depender de falhas reais do servidor.
- [ ] Remover ou ocultar cadastro, seleção de homeserver e descoberta pública.

Aceitação: sessão e sincronização funcionam no homeserver de desenvolvimento.

### F3 — Conversas

- [ ] Implementar lista e seleção de salas.
- [ ] Mapear salas para conversas individuais e grupos conforme convenção aprovada.
- [ ] Implementar histórico e compositor.
- [ ] Implementar estados de envio, falha e repetição.
- [ ] Implementar leitura, digitação e presença conforme política.

Aceitação: dois usuários trocam mensagens pelo fork corporativo.

### F4 — Mídia e experiência

- [ ] Implementar upload e download pelo repositório de mídia Matrix.
- [ ] Exibir progresso, limites e falhas.
- [ ] Criar visualização segura de imagens e documentos.
- [ ] Concluir responsividade, acessibilidade e comportamento PWA.

Aceitação: o fluxo de mídia funciona em computador e celular dentro dos limites do servidor.

### F5 — Administração necessária

- [ ] Definir com o Colaborador 1 quais operações precisam de interface própria.
- [ ] Consultar `GET /v1/me/capabilities` e manter “Gerenciamento” fechado e
  oculto sem `can_manage_user_activations`.
- [ ] Criar painel aprovado para listar, emitir e revogar ativações, definindo
  `username` e papel `user` ou `group_admin`.
- [ ] Garantir que `group_admin` não veja criação de usuários e que nenhuma
  tela ofereça `platform_admin` como papel de convite.
- [ ] Nunca expor token ou API administrativa no navegador.
- [ ] Implementar estados de conta bloqueada e permissão negada.

## Mensagens de voz aprovadas e chamadas futuras

`DEC-020` inclui mensagens de voz no MVP e mantém chamadas fora do MVP. A prova
de conceito de chamadas pode avançar em paralelo, mas não bloqueia os marcos
atuais. Matrix, Synapse e o repositório de mídia continuam sendo o caminho dos
áudios; o FastAPI não processará mensagens ou mídia.

### Decisões e preparação compartilhadas

- [x] Incluir mensagens de voz gravadas no MVP e manter chamadas em fase posterior.
- [x] Escolher MatrixRTC, Element Call, LiveKit, `lk-jwt-service` e coturn para a futura prova de conceito, sem desenvolver WebRTC próprio.
- [x] Definir limite inicial de 5 minutos e 10 MB por mensagem de voz, com WebM/Opus preferencial e MP4/AAC alternativo.
- [x] Fazer mensagens de voz e chamadas herdarem a política de criptografia e retenção da sala.
- [ ] Aprovar e registrar versões, commits, imagens, arquivos incorporados e licenças antes de adicionar componentes de chamada à plataforma.
- [ ] Aprovar os nomes públicos, domínio e endereços de Matrix, MatrixRTC e TURN antes de qualquer implantação externa.

### Colaborador 1 — Plataforma, mídia e infraestrutura

- [ ] Confirmar no Synapse os MIME types, o limite de 10 MB e a retenção aplicáveis às mensagens de voz sem reduzir indevidamente o limite dos demais arquivos.
- [ ] Validar upload, download, autenticação de mídia, E2EE, backup e restauração de eventos `m.audio`.
- [ ] Preparar uma prova de conceito isolada de MatrixRTC com LiveKit e `lk-jwt-service`, sem reabrir federação pública.
- [ ] Configurar os recursos exigidos pelo MatrixRTC no Synapse e anunciar o backend por `.well-known/matrix/client`.
- [ ] Implantar coturn com IP público, credenciais temporárias, cotas e bloqueio de acesso a redes internas.
- [ ] Definir TLS, proxy reverso, WebSocket, portas UDP/TCP e regras de firewall para MatrixRTC e TURN.
- [ ] Adicionar métricas, logs sem credenciais, alertas e limites contra abuso dos serviços de chamada.
- [ ] Testar uma chamada entre duas contas em redes diferentes, incluindo computador e celular, reconexão e falha do TURN.

### Colaborador 2 — Gravação, reprodução e experiência

- [ ] Validar e testar o envio e a reprodução de arquivos `m.audio` já existentes no fork.
- [ ] Adicionar ao compositor um botão de microfone com iniciar, pausar, continuar, cancelar e enviar.
- [ ] Gravar com `MediaRecorder`, selecionando WebM/Opus quando disponível e MP4/AAC como alternativa compatível.
- [ ] Integrar a gravação ao upload Matrix e à criptografia de mídia já existentes, sem criar outra API de upload.
- [ ] Incluir duração, tamanho, progresso, limite, falha, repetição e estado de permissão negada.
- [ ] Garantir acessibilidade, descarte do áudio cancelado e liberação imediata do microfone ao terminar.
- [ ] Testar gravação e reprodução em Chrome, Safari, Android e iPhone.
- [ ] Validar o Element Call incorporado ao Cinny e manter os controles de chamada ocultos quando MatrixRTC não estiver anunciado.
- [ ] Preparar estados de chamada recebida, saída, conectando, mute, reconexão, encerramento e indisponibilidade, sem liberar chamadas no MVP.

Aceitação das mensagens de voz: duas contas gravam, enviam, recebem, descriptografam
e reproduzem áudio no computador e no celular dentro dos limites aprovados.

Aceitação futura das chamadas: duas contas em redes diferentes concluem uma
chamada de voz com TURN validado, sem federação pública e sem credenciais no
navegador ou no repositório.

## Marcos de integração

### I1 — Conectividade e sessão

- O Colaborador 2 conecta o frontend ao Synapse de homologação e conclui login/logout.
- O Colaborador 1 valida isolamento, logs e encerramento de acesso.

### I2 — Salas e mensagens

- Validar conversas diretas, grupos, histórico e sincronização.
- Registrar divergências como convenções, sem modificar o protocolo Matrix.

### I3 — Mídia e estados em tempo real

- Validar leitura, digitação, presença, upload, download, mensagens de voz e limites.

### I4 — Segurança e piloto

- Validar convites, permissões, retenção, auditoria, backup e experiência PWA.

### I5 — Chamadas após o MVP

- Validar MatrixRTC, LiveKit, serviço de autorização e TURN em ambiente isolado.
- Testar chamada entre computador e celular em redes diferentes antes de avaliar grupos.
- Liberar chamadas no produto somente após revisão conjunta de segurança, capacidade, operação e licenças.

## Regras para bloqueios

- Dúvida visual não bloqueia a configuração do Synapse.
- Dúvida operacional não bloqueia componentes visuais que possam usar o ambiente local.
- Extensão personalizada do Matrix exige proposta e aprovação conjunta.
- O frontend não solicita acesso direto ao banco ou token administrativo.
- A plataforma não modifica componentes da interface para contornar configuração incorreta.

## Bloqueios reais atuais

- Aceitação final da licença e do modelo de manutenção do Synapse.
- Domínio de produção e formato definitivo dos identificadores Matrix ainda não definidos.
- Serviço de convites e ciclo de vida das contas ainda não implementados.
- Política de retenção ainda não aprovada.
- Licença do código próprio ainda não definida.
- Nome e identidade visual ainda não definidos; isso não bloqueia a prova de conceito.
