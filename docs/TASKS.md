# Tarefas e responsabilidades

Atualize este arquivo em toda reunião de alinhamento. Cada tarefa deve possuir responsável, critério de aceitação e dependências.

## Estado

- `[ ]` não iniciada
- `[~]` em andamento
- `[R]` em revisão
- `[x]` concluída
- `[B]` bloqueada

## Fase 1 — Viabilidade

### Colaborador 1 — Frontend

- [ ] Mapear os repositórios web oficiais relevantes.
  - Aceitação: lista de repositórios, versões e licenças.
- [ ] Identificar componentes visuais potencialmente reutilizáveis.
  - Aceitação: cada componente possui dependências e nível de acoplamento registrados.
- [ ] Criar uma proposta visual própria para o produto.
  - Dependência: nome, marca e paleta da organização.
- [ ] Classificar componentes em reutilizar, adaptar, usar como referência ou descartar.
  - Dependência: revisão conjunta e jurídica.

### Colaborador 2 — Backend

- [ ] Escolher a tecnologia do backend.
  - Aceitação: decisão registrada com justificativa.
- [ ] Definir o modelo inicial de dados.
  - Aceitação: entidades, relações e regras de retenção descritas.
- [ ] Definir contratos HTTP e WebSocket.
  - Dependência: casos de uso do frontend.
- [ ] Identificar o provedor de identidade corporativa.
  - Dependência: informação da organização.
- [ ] Propor ambientes local, homologação e produção.

### Compartilhadas

- [ ] Confirmar funcionalidades do MVP.
- [ ] Definir política inicial de retenção e auditoria.
- [ ] Aprovar a estratégia de reutilização de código.
- [ ] Fechar o contrato inicial da API.
- [ ] Criar o primeiro backlog de implementação.

## Fase 2 — Fundação

### Colaborador 1

- [ ] Preparar frontend e identidade visual.
- [ ] Criar interfaces corporativas independentes do Telegram.
- [ ] Implementar protótipo com dados simulados.

### Colaborador 2

- [ ] Preparar backend e banco de dados.
- [ ] Criar migrações iniciais.
- [ ] Implementar autenticação provisória controlada.
- [ ] Preparar ambiente local reproduzível.

## Fase 3 — Mensagens

### Colaborador 1

- [ ] Lista e busca de conversas.
- [ ] Histórico paginado.
- [ ] Compositor e estados de envio.
- [ ] Integração HTTP e WebSocket.

### Colaborador 2

- [ ] Conversas individuais e grupos.
- [ ] Persistência e paginação de mensagens.
- [ ] Gateway WebSocket.
- [ ] Entrega, leitura, presença e digitação.

## Fase 4 — Arquivos

### Colaborador 1

- [ ] Upload com progresso.
- [ ] Visualização segura de imagens e documentos.
- [ ] Lista de arquivos compartilhados.

### Colaborador 2

- [ ] Armazenamento de objetos.
- [ ] URLs temporárias e autorização.
- [ ] Limites e validação de arquivos.
- [ ] Integração antimalware, se exigida.

## Fase 5 — Administração e SSO

### Colaborador 1

- [ ] Painel de usuários e grupos.
- [ ] Visualização de auditoria conforme permissão.

### Colaborador 2

- [ ] Integração OIDC/SAML.
- [ ] Perfis e permissões.
- [ ] Ativação e bloqueio de contas.
- [ ] Auditoria administrativa.

## Fase 6 — Homologação

### Compartilhadas

- [ ] Testes funcionais e de integração.
- [ ] Testes de segurança e autorização.
- [ ] Testes de carga e recuperação.
- [ ] Validação em computador e celular.
- [ ] Piloto com grupo restrito.
- [ ] Documentação de operação e implantação.

## Bloqueios atuais

- Nome e identidade visual ainda não definidos.
- Provedor corporativo de identidade ainda não informado.
- Política de retenção ainda não aprovada.
- Licença desejada para o produto ainda não definida.
