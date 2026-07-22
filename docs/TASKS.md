# Tarefas independentes e marcos de integração

## Princípio

O Matrix define o protocolo compartilhado. Depois que configuração, autenticação e convenções forem aprovadas, os colaboradores trabalham em paralelo: um mantém o fork corporativo do Cinny; o outro implanta, protege e opera o Synapse.

## Etapa conjunta curta — prova de conceito e congelamento

- [~] Confirmar Synapse após a prova de conceito; configuração inicial criada, revisão final pendente.
- [~] Avaliar Synapse `1.156.0`, Cinny `v4.12.3` e `matrix-js-sdk` `41.7.0`; validação conjunta pendente.
- [x] Definir federação privada por lista de permissão, iniciando sem organizações parceiras e sem listener de federação exposto.
- [x] Definir política híbrida de criptografia ponta a ponta para o MVP.
- [~] Definir autenticação inicial por convite; domínio de produção e formato definitivo dos identificadores ainda pendentes.
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
- [ ] Implementar o serviço FastAPI de convites administrativos de uso único, com validade de 24 horas.
- [ ] Implementar provisionamento, bloqueio, redefinição de senha e desligamento de usuários pela API administrativa do Synapse.
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

### F2 — Sessão e sincronização

- [ ] Implementar entrada pelo fluxo de convite e autenticação local do Synapse.
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

- Validar convites, permissões, retenção, auditoria, backup e experiência PWA.

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
