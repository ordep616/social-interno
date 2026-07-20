# Tarefas independentes e marcos de integração

## Princípio

O Matrix define o protocolo compartilhado. Depois que configuração, autenticação e convenções forem aprovadas, os colaboradores trabalham em paralelo: um desenvolve a interface sobre `matrix-js-sdk`; o outro implanta, protege e opera o Synapse.

## Etapa conjunta curta — prova de conceito e congelamento

- [~] Confirmar Synapse após a prova de conceito; configuração inicial criada, revisão final pendente.
- [~] Avaliar Synapse `1.156.0` e `matrix-js-sdk` `41.9.0`; aprovação conjunta pendente.
- [ ] Decidir se a federação ficará completamente desabilitada.
- [ ] Decidir se criptografia ponta a ponta pertence ao MVP.
- [ ] Escolher o provedor OIDC e o formato dos identificadores dos usuários.
- [ ] Definir convenções para conversas diretas, grupos e departamentos.
- [ ] Executar prova de conceito: dois usuários, uma sala, mensagem, leitura e arquivo.

Aceitação: a equipe comprova o fluxo mínimo e registra as decisões antes da personalização ampla.

## Colaborador 1 — Backend, plataforma, infraestrutura e segurança

Todo trabalho de backend pertence ao Colaborador 1. Esta trilha pode ser validada com um cliente Matrix genérico, sem depender da interface própria.

### P1 — Fundação do homeserver

- [x] Criar a área exclusiva `platform/` e documentar seus limites.
- [~] Preparar Synapse e PostgreSQL em Compose; execução pendente em máquina com Docker.
- [x] Fixar versões iniciais das imagens e registrar suas licenças.
- [x] Configurar domínio local, logs e verificação de saúde.
- [ ] Criar dois usuários de teste sem credenciais reais.
- [ ] Validar mensagens, histórico, leitura e mídia com um cliente de teste.

Aceitação: o homeserver inicia e o fluxo básico funciona sem o frontend próprio.

### P2 — Isolamento e identidade

- [x] Desabilitar cadastro público na configuração local.
- [~] Retirar o listener de federação e configurar lista vazia; teste em execução pendente.
- [ ] Integrar o provedor OIDC escolhido.
- [ ] Definir provisionamento, bloqueio e desligamento de usuários.
- [ ] Separar papéis de usuário, operador e administrador.
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

- [ ] Levantar lacunas que Synapse, Matrix e OIDC não atendem.
- [ ] Priorizar integrações com RH, ERP, relatórios ou auditoria personalizada.
- [ ] Criar FastAPI somente após aprovar uma necessidade concreta.
- [ ] Manter qualquer serviço auxiliar fora do caminho principal das mensagens.

Aceitação: nenhum backend personalizado duplica funcionalidades nativas da plataforma.

## Colaborador 2 — Frontend, interface web e experiência

Esta trilha utiliza um homeserver Matrix local ou compartilhado e não depende da configuração de produção.

### F1 — Fundação e SDK

- [x] Criar estrutura exclusiva de `frontend/`.
- [x] Registrar origem, versão e licença do `matrix-js-sdk`.
- [~] Criar adaptador próprio para encapsular o SDK; autenticação e eventos reativos ainda pendentes.
- [ ] Definir design, identidade provisória e componentes base.
- [x] Configurar a URL do homeserver por ambiente.

Aceitação: a interface inicia sem código do Telegram ou Element e o SDK fica isolado dos componentes visuais.

### F2 — Sessão e sincronização

- [ ] Implementar entrada pelo fluxo definido com o Synapse/OIDC.
- [ ] Restaurar e encerrar sessão com segurança.
- [ ] Inicializar sincronização e tratar reconexão.
- [ ] Criar estados de carregamento, vazio, indisponibilidade e acesso negado.
- [ ] Simular erros para não depender de falhas reais do servidor.

Aceitação: sessão e sincronização funcionam no homeserver de desenvolvimento.

### F3 — Conversas

- [ ] Implementar lista e seleção de salas.
- [ ] Mapear salas para conversas individuais e grupos conforme convenção aprovada.
- [ ] Implementar histórico e compositor.
- [ ] Implementar estados de envio, falha e repetição.
- [ ] Implementar leitura, digitação e presença conforme política.

Aceitação: dois usuários trocam mensagens pela interface própria.

### F4 — Mídia e experiência

- [ ] Implementar upload e download pelo repositório de mídia Matrix.
- [ ] Exibir progresso, limites e falhas.
- [ ] Criar visualização segura de imagens e documentos.
- [ ] Concluir responsividade, acessibilidade e comportamento PWA.

Aceitação: o fluxo de mídia funciona em computador e celular dentro dos limites do servidor.

### F5 — Administração necessária

- [ ] Definir com o Colaborador 1 quais operações precisam de interface própria.
- [ ] Criar somente telas administrativas aprovadas.
- [ ] Nunca expor token ou API administrativa no navegador.
- [ ] Implementar estados de conta bloqueada e permissão negada.

## Marcos de integração

### I1 — Conectividade e sessão

- O Colaborador 2 conecta o frontend ao Synapse de homologação e conclui login/logout.
- O Colaborador 1 valida isolamento, logs e encerramento de acesso.

### I2 — Salas e mensagens

- Validar conversas diretas, grupos, histórico e sincronização.
- Registrar divergências como convenções, sem modificar o protocolo Matrix.

### I3 — Mídia e estados em tempo real

- Validar leitura, digitação, presença, upload, download e limites.

### I4 — Segurança e piloto

- Validar OIDC, permissões, retenção, auditoria, backup e experiência PWA.

## Regras para bloqueios

- Dúvida visual não bloqueia a configuração do Synapse.
- Dúvida operacional não bloqueia componentes visuais que possam usar o ambiente local.
- Extensão personalizada do Matrix exige proposta e aprovação conjunta.
- O frontend não solicita acesso direto ao banco ou token administrativo.
- A plataforma não modifica componentes da interface para contornar configuração incorreta.

## Bloqueios reais atuais

- Aceitação final da licença e do modelo de manutenção do Synapse.
- Provedor de identidade corporativa ainda não informado.
- Federação e criptografia ponta a ponta ainda não decididas.
- Política de retenção ainda não aprovada.
- Licença do código próprio ainda não definida.
- Nome e identidade visual ainda não definidos; isso não bloqueia a prova de conceito.
