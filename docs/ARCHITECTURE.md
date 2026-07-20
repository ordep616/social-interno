# Arquitetura pretendida

## Visão geral

```text
Navegador / PWA
  ├── Interface de conversas
  ├── Cache e sincronização local
  └── Cliente HTTP e WebSocket
              │
              ▼
API corporativa
  ├── Identidade e autorização
  ├── Usuários e grupos
  ├── Conversas e mensagens
  ├── Presença e confirmações
  ├── Arquivos
  ├── Administração
  └── Auditoria e retenção
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
  PostgreSQL Redis  MinIO/S3
```

## Tecnologias candidatas

As escolhas finais devem ser registradas em `DECISIONS.md`.

- Frontend: React e Next.js.
- Backend: FastAPI ou NestJS.
- Banco relacional: PostgreSQL.
- Eventos e presença: Redis.
- Tempo real: WebSockets.
- Arquivos: MinIO on-premises ou armazenamento S3 privado.
- Identidade: OIDC ou SAML por meio do provedor corporativo.
- Ambiente: contêineres e Docker Compose durante desenvolvimento e homologação.

## Limites

### Frontend

- Não conhece credenciais do provedor de identidade.
- Não acessa banco ou armazenamento diretamente.
- Não importa clientes ou tipos MTProto.
- Consome apenas contratos corporativos definidos em `API.md`.

### Backend

- É a fonte de verdade para autorização e estado das mensagens.
- Valida participação em toda operação de conversa.
- Autoriza inscrições WebSocket individualmente.
- Emite URLs temporárias para arquivos.
- Registra operações administrativas relevantes.

### Armazenamento

- Banco relacional guarda usuários, conversas, participantes e metadados.
- Redis guarda presença e estado efêmero, não o histórico definitivo.
- Armazenamento de objetos guarda os bytes dos anexos.

## Arquitetura para trabalho paralelo

```text
                  docs/contracts/
             OpenAPI + eventos + exemplos
                    /            \
                   ▼              ▼
       Frontend independente   Backend independente
       ├─ servidor mock        ├─ API real
       ├─ dados de exemplo     ├─ WebSocket real
       ├─ testes de UI         ├─ banco e armazenamento
       └─ adaptador da API     └─ testes de contrato
                   \              /
                    ▼            ▼
                 Marco de integração
```

### Regras de independência

- O contrato é o único acoplamento obrigatório durante cada ciclo.
- O frontend alterna entre `mock` e `real` por configuração, sem alterar componentes.
- O backend valida respostas e eventos contra os esquemas publicados.
- IDs, datas, paginação, erros e estados são definidos antes da implementação.
- Funcionalidades experimentais ficam atrás de capacidades anunciadas por `/me` ou configuração.
- Nenhum colaborador altera arquivos da área do outro durante seu trabalho normal.

### Estrutura futura recomendada

```text
frontend/               propriedade do colaborador de frontend
backend/                propriedade do responsável pelo backend
contracts/              contratos versionados e aprovados em conjunto
contracts/openapi.yaml  endpoints HTTP
contracts/events/       esquemas dos eventos WebSocket
contracts/examples/     respostas usadas pelo servidor mock
docs/                   decisões e planejamento
```

## Entidades iniciais

- `User`
- `Conversation`
- `ConversationMember`
- `Message`
- `Attachment`
- `Session`
- `AuditLog`
- `RetentionPolicy`

## Segurança

- Login pelo provedor corporativo.
- Autorização no servidor em todas as operações.
- HTTPS obrigatório em ambientes compartilhados.
- Sessões com expiração e revogação.
- Proteção contra abuso e limites de requisição.
- Validação de tipo, tamanho e conteúdo dos arquivos.
- Verificação antimalware quando exigida.
- Segredos fora do frontend e do repositório.
- Backups testados e criptografados.

## Estratégia de código aberto

O Telegram Web será analisado por componente. Material aprovado deve ficar isolado, rastreável e desacoplado do backend. Consulte `OPEN_SOURCE.md`.
