# Integrações e convenções técnicas

## Estado

A proposta anterior de uma API HTTP/WebSocket própria foi substituída pela adoção do Matrix. Seus contratos não aprovados foram removidos e não devem orientar implementação nova.

## Contrato principal

O frontend utilizará a Matrix Client-Server API por meio da integração existente no fork do Cinny. Não serão recriados endpoints próprios para salas, mensagens, sincronização, leitura, digitação, presença ou mídia.

## Configuração compartilhada inicial

Os dois colaboradores precisam aprovar e documentar:

- URL pública do homeserver por ambiente;
- fluxo inicial de cadastro por convite e login Matrix;
- versões suportadas do homeserver e do SDK;
- convenção para conversas diretas e grupos;
- política de presença, leitura e digitação;
- limites de mídia;
- política de criptografia ponta a ponta;
- capacidades habilitadas ou desabilitadas no servidor.

## Integração do frontend

O fork deve preservar, sempre que possível, a separação interna do Cinny entre componentes visuais e operações Matrix. Personalizações corporativas não devem espalhar novas chamadas diretas ao SDK. A integração existente cobre operações como:

- iniciar e encerrar sessão;
- observar sincronização;
- listar e abrir conversas;
- criar salas conforme as convenções aprovadas;
- paginar histórico;
- enviar mensagens e anexos;
- atualizar leitura e digitação;
- observar participantes e presença.

Essa camada pertence ao frontend e não constitui uma API de servidor própria.

## Serviço de convites aprovado

`DEC-017` aprovou uma API FastAPI auxiliar exclusivamente para convites, provisionamento e ciclo de vida de contas. Ela não participa do envio, recebimento ou armazenamento de mensagens.

### Estilo da API

`DEC-018` define que as APIs próprias do serviço seguem REST sobre HTTP, com contrato versionado em `/v1`, recursos nomeados por substantivos, JSON e códigos HTTP consistentes. Operações nativas de chat continuam usando diretamente o contrato Matrix e não são encapsuladas pelo FastAPI.

- `GET` consulta recursos sem alterar seu estado.
- `POST` cria recursos.
- `PATCH` será usado quando uma alteração parcial de recurso for aprovada.
- `DELETE` torna um recurso indisponível; quando a auditoria exigir preservação, a remoção é lógica.
- Endpoints administrativos e públicos permanecem separados e aplicam autenticação, autorização e limites próprios.

### Autenticação e autorização administrativa

- Endpoints administrativos recebem o token Matrix do usuário autenticado em `Authorization: Bearer`.
- O serviço valida a identidade pelo endpoint suportado `whoami` do Synapse e consulta seu próprio papel.
- Somente `platform_admin` cria, lista ou revoga convites.
- A credencial usada pelo serviço para chamar a API administrativa do Synapse permanece no servidor e nunca é enviada ao navegador.
- `group_admin` não recebe administração global do Synapse.
- O primeiro `platform_admin` é criado por procedimento local de inicialização; promoções posteriores usam processo administrativo separado e auditado.

### Convite

O token deve possuir alta entropia e ser armazenado somente como hash SHA-256. O link completo é retornado uma única vez, expira em 24 horas e aceita um único uso. Token, senha e credenciais administrativas não podem aparecer em logs ou eventos de auditoria.

O token aparece na rota de validação e no corpo da criação do cadastro. Proxy, servidor HTTP, rastreamento e monitoramento devem omitir ou mascarar o caminho da validação e nunca registrar corpos dessas requisições. As respostas usam `Cache-Control: no-store`.

Campos persistidos:

```text
id
token_hash
role
status
created_by
created_at
expires_at
used_at
revoked_at
accepted_user_id
```

Estados permitidos:

```text
pending
processing
used
revoked
expired
```

Os dados pertencem a um PostgreSQL próprio do serviço. O serviço não acessa diretamente o banco do Synapse.

### Endpoints administrativos

```text
POST /v1/admin/invitations
GET  /v1/admin/invitations
GET  /v1/admin/invitations/{id}
DELETE /v1/admin/invitations/{id}
```

Criação de convite:

```json
{
  "role": "user"
}
```

`role` aceita somente `user` ou `group_admin`. A resposta inclui metadados, o cabeçalho `Location` com o recurso administrativo criado e `invite_url`; essa é a única resposta que apresenta o token em texto aberto. Promoção a `platform_admin` usa procedimento administrativo separado.

Respostas esperadas: criação `201`, listagem e consulta `200` e revogação idempotente `204`.

A listagem, consulta e revogação usam o identificador público do convite e nunca retornam `token_hash` ou o token original. `DELETE` realiza revogação lógica: preenche `revoked_at`, muda o estado para `revoked` e preserva o registro para auditoria. Revogar um convite já revogado é uma operação idempotente. Identificador administrativo inexistente retorna `404`; convite em processamento ou já usado não pode ser revogado e retorna `409`.

### Endpoints do convidado

```text
GET  /v1/invitations/{token}
POST /v1/registrations
```

Criação de cadastro usando convite:

```json
{
  "invitation_token": "token-secreto",
  "username": "pedro",
  "password": "senha-escolhida"
}
```

Resposta após criação:

```json
{
  "user_id": "@pedro:localhost"
}
```

O recurso criado representa o cadastro inicial da conta. O serviço não retorna token de sessão. O usuário realiza login normal no cliente depois da criação. Token de convite e senha são encaminhados somente ao processamento necessário, nunca são persistidos em texto aberto e não aparecem em logs.

Respostas esperadas: validação `200` e criação do cadastro `201`. Token inexistente retorna `404`; token expirado, usado ou revogado retorna a mesma resposta genérica `410`; nome indisponível retorna `409`; limite excedido retorna `429`. Endpoints administrativos retornam `401` sem autenticação válida e `403` sem o papel exigido.

### Concorrência e falhas

- A aceitação move o convite atomicamente de `pending` para `processing` antes de criar a conta.
- Apenas uma tentativa pode processar o mesmo convite por vez.
- Sucesso no Synapse conclui o estado `used` e registra `accepted_user_id`.
- Falhas antes da criação podem devolver o convite a `pending` conforme política de repetição.
- Falha após a criação da conta exige reconciliação administrativa e não pode criar uma segunda conta silenciosamente.
- Convites inválidos, expirados, usados ou revogados retornam resposta genérica que não revela dados internos.
- Validação e aceitação possuem limite de tentativas por origem e por hash do token.

### Auditoria

Uma tabela separada registra criação, revogação, aceitação, falha de provisionamento, bloqueio e redefinição administrativa. Cada evento contém autor, ação, alvo, instante UTC e resultado, sem token, senha ou credencial.

## Outras extensões corporativas

Fora do serviço de convites aprovado, uma nova API auxiliar só será criada quando houver uma necessidade que Matrix, Synapse e suas APIs administrativas não atendam, por exemplo:

- integração específica com RH ou ERP;
- relatório corporativo personalizado;
- fluxo administrativo próprio;
- exportação de auditoria aprovada.

Cada extensão deverá ter justificativa, responsável, autenticação, autorização, contrato versionado e testes. Tokens administrativos nunca serão entregues ao navegador.

## Eventos personalizados

Usar eventos Matrix padrão sempre que possível. Um evento personalizado exige:

1. caso de uso que não possa ser representado de forma padrão;
2. namespace próprio da organização;
3. esquema e exemplos versionados;
4. comportamento definido para clientes que não o reconheçam;
5. aprovação dos dois colaboradores.

## Próximo artefato compartilhado

Após a prova de conceito, criar um documento pequeno de configuração e convenções Matrix. O diretório `contracts/` só será recriado se uma extensão corporativa própria for aprovada.
