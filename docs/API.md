# Contrato inicial da API

Este arquivo contém uma proposta para alinhamento, não um contrato aprovado. Alterações que afetem frontend e backend devem ser revisadas pelos dois colaboradores.

## Regras gerais

- Prefixo sugerido: `/api/v1`.
- Conteúdo JSON em UTF-8.
- Identificadores opacos.
- Datas em ISO 8601 UTC.
- Paginação por cursor.
- Erros com `code`, `message` e `requestId`.
- O servidor verifica autorização em todas as operações.

## Endpoints propostos

| Método | Rota | Finalidade |
|---|---|---|
| `GET` | `/me` | Obter usuário e permissões da sessão |
| `GET` | `/users` | Consultar diretório autorizado |
| `GET` | `/conversations` | Listar conversas paginadas |
| `POST` | `/conversations` | Criar conversa ou grupo |
| `GET` | `/conversations/:id` | Obter detalhes autorizados |
| `PATCH` | `/conversations/:id` | Alterar grupo conforme permissão |
| `GET` | `/conversations/:id/messages` | Obter histórico paginado |
| `POST` | `/conversations/:id/messages` | Enviar mensagem |
| `PATCH` | `/messages/:id` | Editar mensagem conforme política |
| `DELETE` | `/messages/:id` | Excluir mensagem conforme política |
| `POST` | `/conversations/:id/read` | Atualizar marcador de leitura |
| `POST` | `/uploads` | Iniciar upload autorizado |
| `GET` | `/attachments/:id/access` | Obter acesso temporário ao arquivo |
| `GET` | `/admin/audit` | Consultar auditoria autorizada |

## Eventos WebSocket propostos

- `message.created`
- `message.updated`
- `message.deleted`
- `message.read`
- `conversation.created`
- `conversation.updated`
- `member.joined`
- `member.removed`
- `presence.changed`
- `typing.started`
- `typing.stopped`

## Envelope de evento

```json
{
  "eventId": "evt_opaque",
  "type": "message.created",
  "version": 1,
  "occurredAt": "2026-07-20T13:00:00Z",
  "conversationId": "conv_opaque",
  "data": {}
}
```

## Pontos pendentes

- Estratégia de reconexão e recuperação de eventos.
- Limites de tamanho e tipos de arquivo.
- Regras de edição e exclusão.
- Política de presença.
- Formato de menções, respostas e formatação de texto.
