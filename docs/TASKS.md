# Tarefas independentes e marcos de integração

## Princípio

Depois da aprovação do contrato inicial, os dois colaboradores trabalham em paralelo. O frontend usa mocks; o backend usa testes de contrato. A dependência direta entre pessoas deve ocorrer somente nos marcos de integração.

## Etapa conjunta curta — congelar contratos

Prazo sugerido: 1–2 dias.

- [ ] Aprovar entidades públicas: usuário, conversa, participante, mensagem, anexo e erro.
- [ ] Aprovar endpoints HTTP do MVP.
- [ ] Aprovar eventos WebSocket do MVP.
- [ ] Criar exemplos JSON válidos.
- [ ] Marcar o contrato como `v1-draft` e depois `v1-approved`.

Após isso, nenhuma dúvida pequena deve bloquear o desenvolvimento. Questões são anotadas e resolvidas no próximo marco.

## Sua trilha — Backend, infraestrutura e segurança

Você pode executar esta sequência sem depender das telas.

### B1 — Fundação

- [ ] Escolher FastAPI ou NestJS e registrar a decisão.
- [ ] Criar estrutura exclusiva de `backend/`.
- [ ] Preparar configuração, logs, tratamento de erros e teste de saúde.
- [ ] Preparar ambiente local do banco, Redis e armazenamento.
- [ ] Criar pipeline de testes do backend.

Aceitação: backend inicia sozinho, possui teste de saúde e não exige frontend.

### B2 — Identidade e autorização

- [ ] Criar abstração do provedor de identidade.
- [ ] Implementar sessão de desenvolvimento controlada.
- [ ] Implementar usuários, perfis e bloqueios.
- [ ] Implementar autorização centralizada.
- [ ] Criar testes negativos de acesso.

Aceitação: testes demonstram que um usuário não acessa conversas das quais não participa.

### B3 — Conversas e mensagens HTTP

- [ ] Modelar banco e migrações.
- [ ] Implementar conversas individuais e grupos.
- [ ] Implementar histórico por cursor.
- [ ] Implementar envio, edição e exclusão conforme contrato.
- [ ] Validar respostas com os esquemas compartilhados.

Aceitação: testes de integração cobrem o fluxo completo pela API, sem navegador.

### B4 — Tempo real

- [ ] Implementar autenticação WebSocket.
- [ ] Implementar assinatura autorizada de conversas.
- [ ] Publicar eventos versionados.
- [ ] Implementar leitura, digitação e presença.
- [ ] Testar reconexão e eventos duplicados.

Aceitação: um cliente de teste recebe os eventos definidos no contrato.

### B5 — Arquivos

- [ ] Configurar armazenamento de objetos.
- [ ] Implementar upload autorizado e metadados.
- [ ] Implementar URLs temporárias.
- [ ] Validar tamanho e tipo.
- [ ] Preparar verificação antimalware, se exigida.

Aceitação: testes enviam, consultam e bloqueiam arquivos sem utilizar o frontend.

### B6 — Administração e produção

- [ ] Implementar papéis administrativos.
- [ ] Implementar auditoria.
- [ ] Integrar OIDC/SAML real.
- [ ] Definir backup, retenção, métricas e alertas.
- [ ] Documentar implantação e recuperação.

## Trilha do outro colaborador — Frontend e código aberto

O outro colaborador pode executar esta sequência usando apenas contratos e mocks.

### F1 — Fundação visual

- [ ] Analisar componentes abertos e registrar licenças.
- [ ] Criar estrutura exclusiva de `frontend/`.
- [ ] Definir design próprio e componentes base.
- [ ] Criar navegação responsiva e acessível.

Aceitação: frontend inicia sozinho e não exige backend.

### F2 — Cliente simulado

- [ ] Criar adaptador único da API.
- [ ] Criar servidor mock com os exemplos do contrato.
- [ ] Criar cliente WebSocket simulado.
- [ ] Simular sucesso, vazio, carregamento e erro.

Aceitação: todas as telas podem ser demonstradas offline com dados simulados.

### F3 — Conversas

- [ ] Lista, busca e seleção de conversas.
- [ ] Histórico paginado.
- [ ] Compositor e estados de envio.
- [ ] Edição, exclusão, resposta e confirmação visual conforme escopo.

Aceitação: fluxo completo funciona contra o mock.

### F4 — Tempo real e arquivos simulados

- [ ] Aplicar eventos simulados ao estado da interface.
- [ ] Exibir leitura, digitação e presença.
- [ ] Implementar upload simulado com progresso e erro.
- [ ] Implementar visualização segura de mídia.

Aceitação: cenários de tempo real e arquivos são reproduzíveis sem backend.

### F5 — Administração

- [ ] Criar telas administrativas com dados simulados.
- [ ] Criar estados de permissão negada e conta bloqueada.
- [ ] Concluir acessibilidade e responsividade.

## Marcos de integração

### I1 — Sessão e usuário

- Trocar o mock de `/me` pelo backend real.
- Corrigir apenas divergências do contrato.

### I2 — Conversas HTTP

- Integrar lista, histórico e envio.
- Não incluir WebSocket nem arquivos neste marco.

### I3 — Tempo real

- Integrar eventos e reconexão.
- Registrar qualquer alteração como nova revisão do contrato.

### I4 — Arquivos e administração

- Integrar uploads, acesso temporário e permissões administrativas.

## Regras para bloqueios

- Dúvida visual não bloqueia backend.
- Dúvida interna de banco não bloqueia frontend.
- Campo ausente no contrato é registrado em uma proposta de mudança.
- Correção compatível pode entrar na versão atual.
- Mudança incompatível espera o próximo marco ou cria nova versão.

## Bloqueios reais atuais

- Provedor de identidade corporativa ainda não informado.
- Política de retenção ainda não aprovada.
- Licença desejada para o código próprio ainda não definida.
- Nome e identidade visual ainda não definidos, mas isso não bloqueia o backend.
