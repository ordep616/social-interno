# Integrações e convenções técnicas

## Estado

A proposta anterior de uma API HTTP/WebSocket própria foi substituída pela adoção do Matrix. Seus contratos não aprovados foram removidos e não devem orientar implementação nova.

## Contrato principal

O frontend utilizará a Matrix Client-Server API por meio da integração existente no fork do Cinny. Não serão recriados endpoints próprios para salas, mensagens, sincronização, leitura, digitação, presença ou mídia.

## Configuração compartilhada inicial

Os dois colaboradores precisam aprovar e documentar:

- URL pública do homeserver por ambiente;
- fluxo inicial de ativação administrativa e login Matrix;
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

## Serviço aprovado de ativação por convite

`DEC-017` aprovou uma API FastAPI auxiliar exclusivamente para convites,
provisionamento e ciclo de vida de contas. `DEC-022`, aceita pelos dois
colaboradores, substitui a escolha de identidade pelo convidado por ativação de
uma identidade definida previamente por `platform_admin`. Esta seção registra
o contrato aprovado, mas não autoriza por si só cada implementação, migração ou
publicação. O serviço continua fora do envio, recebimento e armazenamento de
mensagens.

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
- Somente `platform_admin` cria, lista ou revoga ativações de usuários.
- A credencial usada pelo serviço para chamar a API administrativa do Synapse permanece no servidor e nunca é enviada ao navegador.
- `user` e `group_admin` não recebem a capacidade de criar usuários.
- O primeiro `platform_admin` é criado por procedimento local de inicialização; promoções posteriores usam processo administrativo separado e auditado.
- A visibilidade da interface não concede autorização; cada rota administrativa
  verifica novamente o papel no backend.

Consulta das capacidades da identidade atual:

```text
GET /v1/me/capabilities
```

Exemplo de resposta:

```json
{
  "user_id": "@admin:localhost",
  "role": "platform_admin",
  "capabilities": {
    "can_manage_user_activations": true
  }
}
```

A rota exige uma credencial Matrix válida. `user` e `group_admin` recebem a
capacidade falsa. O frontend nasce com o painel fechado e só mostra
“Gerenciamento” depois dessa confirmação.

### Convite

O token deve possuir alta entropia e ser armazenado somente como hash SHA-256.
O link completo é retornado uma única vez, expira em 24 horas e aceita um único
uso. O administrador define `username` e papel, mas não informa nem conhece a
senha. Token, senha e credenciais administrativas não podem aparecer em logs
ou eventos de auditoria.

O endereço público terá o formato `/activate#<token>`. O fragmento não é
enviado ao servidor HTTP. O frontend deverá lê-lo uma vez, limpar a URL com
`history.replaceState` e mantê-lo somente em memória. Pré-validação e ativação
enviam o token no corpo de `POST`; proxy, servidor HTTP, rastreamento e
monitoramento nunca registram esses corpos. As respostas usam
`Cache-Control: no-store`.

`BACKEND_INVITATION_PUBLIC_BASE_URL` continuará configurável por ambiente, mas
deverá apontar para a rota `/activate` do frontend, sem token, consulta ou
fragmento. Ao emitir o convite, o backend anexará somente `#<token>` a essa
base; nenhum host ou caminho público ficará fixo no código.

Campos persistidos:

```text
id
token_hash
target_user_id
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
conflicted
```

Os dados pertencem a um PostgreSQL próprio do serviço. O serviço não acessa diretamente o banco do Synapse.

Um índice único parcial em `target_user_id` impedirá dois convites com estado
`pending` ou `processing` para a mesma identidade. Novos registros não poderão
omitir a identidade; registros históricos terminais poderão conservá-la nula
durante a migração proposta.

### Migração proposta

- convite legado `pending` sem identidade: revogar e preencher `revoked_at`;
- convite legado `used`: derivar `target_user_id` de `accepted_user_id`;
- convite legado `processing`: interromper a implantação e exigir revisão
  manual;
- convite histórico `revoked` ou `expired`: permitir identidade nula;
- registrar a ação na auditoria antes da publicação.

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
  "username": "pedro",
  "role": "user"
}
```

`username` aceita de 3 a 32 caracteres ASCII minúsculos, começa e termina com
letra ou número e aceita `.`, `_` e `-` apenas no interior. O backend rejeita
maiúsculas, acrescenta seu `server_name` configurado e persiste o identificador
completo em `target_user_id`.

`role` aceita somente `user` ou `group_admin`. A resposta inclui metadados,
`target_user_id`, o cabeçalho `Location` com o recurso administrativo criado e
`invite_url`; essa é a única resposta que apresenta o token aberto, dentro do
fragmento da URL. Promoção a `platform_admin` usa procedimento administrativo
separado.

Respostas esperadas: criação `201`, listagem e consulta `200` e revogação idempotente `204`.

A listagem, consulta e revogação usam o identificador público do convite e nunca retornam `token_hash` ou o token original. `DELETE` realiza revogação lógica: preenche `revoked_at`, muda o estado para `revoked` e preserva o registro para auditoria. Revogar um convite já revogado é uma operação idempotente. Identificador administrativo inexistente retorna `404`; convite em processamento ou já usado não pode ser revogado e retorna `409`.

### Endpoints de ativação

```text
POST /v1/activation-validations
POST /v1/registrations
```

Pré-validação:

```json
{
  "invitation_token": "token-secreto"
}
```

Resposta válida:

```json
{
  "target_user_id": "@pedro:localhost",
  "username": "pedro",
  "role": "user",
  "expires_at": "2026-07-24T12:00:00Z"
}
```

A pré-validação não reserva nem consome o convite. O funcionário vê identidade
e papel como somente leitura. Não existe endpoint público com token no caminho.

Criação do cadastro autorizado:

```json
{
  "invitation_token": "token-secreto",
  "password": "senha-escolhida"
}
```

Resposta após criação:

```json
{
  "user_id": "@pedro:localhost"
}
```

O recurso criado representa o cadastro inicial da conta definida pelo
administrador. O serviço não retorna token de sessão Matrix. Depois de remover
token e senha da memória, o frontend segue para o login normal com apenas o
`username` preenchido. Token de convite e senha são encaminhados somente ao
processamento necessário, nunca são persistidos em texto aberto e não aparecem
em logs.

Respostas esperadas: pré-validação `200` e criação do cadastro `201`. Token
inexistente retorna `404`; token expirado, usado ou revogado retorna a mesma
resposta genérica `410`; identidade indisponível retorna `409`; limite excedido
retorna `429`. Endpoints administrativos retornam `401` sem autenticação válida
e `403` sem `platform_admin`. Todas as respostas relacionadas à ativação,
inclusive erros automáticos, usam `Cache-Control: no-store`.

### Concorrência e falhas

- A emissão valida e fixa `target_user_id` antes de retornar o link.
- A consulta de disponibilidade no Synapse não reserva a identidade; o banco
  próprio também impede dois convites ativos para o mesmo alvo.
- A aceitação move o convite atomicamente de `pending` para `processing` e cria
  uma tentativa para o `target_user_id` persistido.
- Apenas uma tentativa pode processar o mesmo convite por vez.
- Sucesso no Synapse conclui o estado `used` e registra `accepted_user_id`.
- Falhas antes da criação podem devolver o convite a `pending` conforme política de repetição.
- Falha após a criação da conta exige reconciliação administrativa e não pode criar uma segunda conta silenciosamente.
- Conta encontrada antes da criação torna o convite `conflicted`; ela nunca é
  modificada, reativada ou recebe nova senha pelo fluxo.
- Convites inválidos, expirados, usados ou revogados retornam resposta genérica que não revela dados internos.
- Validação e aceitação possuem limite de tentativas por origem e por hash do token.

### Orquestração interna proposta

`DEC-021` propõe uma saga durável para coordenar o PostgreSQL próprio e o
Synapse, pois os dois sistemas não compartilham uma transação. A decisão foi
aceita pelos dois colaboradores e esta seção não cria uma nova rota.

Antes de emitir o convite, o serviço administrativo deverá:

- aceitar `username` com 3 a 32 caracteres ASCII minúsculos, usando a expressão
  `^[a-z0-9][a-z0-9._-]{1,30}[a-z0-9]$`;
- rejeitar letras maiúsculas em vez de normalizá-las silenciosamente;
- formar o identificador `@{username}:{server_name}` somente com o domínio
  configurado no backend;
- rejeitar outro convite ativo para a mesma identidade;
- consultar a
  [disponibilidade pelo mecanismo suportado do Synapse](https://element-hq.github.io/synapse/latest/admin_api/user_admin_api.html#check-username-availability),
  reconhecendo que essa consulta não constitui reserva.

Antes de reservar o convite na ativação, o serviço deverá:

- aceitar senha entre 15 e 128 caracteres sem remover espaços, impor regras de
  composição ou modificar seu conteúdo;
- definir e revisar a licença de uma lista local de senhas comuns ou
  comprometidas antes de expor o endpoint público;
- validar token e senha antes de iniciar qualquer transação ou chamada ao
  Synapse;
- obter identidade e papel exclusivamente do convite persistido.

Uma tabela operacional `registration_attempts`, separada da futura auditoria,
deverá persistir somente:

```text
id
invitation_id
matrix_user_id
role
status
provisioning_device_id
created_at
updated_at
completed_at
failure_code
```

Os estados propostos são `processing`, `synapse_created`, `completed`,
`released` e `reconciliation_required`. Token de convite, hash do token, senha,
credencial administrativa, `access_token` e corpo de resposta do Synapse não
pertencem a essa tabela. Se o mecanismo aprovado criar uma sessão,
`provisioning_device_id` guardará somente o identificador necessário para sua
revogação durável. Restrições únicas parciais impedem mais de uma tentativa
ativa para o mesmo convite ou `matrix_user_id`, sem impedir uma repetição
controlada para a mesma identidade depois de uma liberação comprovadamente
segura.

O fluxo terá cinco fases:

1. Em uma transação local curta, mover o convite de `pending` para
   `processing` e criar a tentativa com seu `target_user_id`. Qualquer conflito
   desfaz as duas mudanças.
2. Depois do commit, sem manter transação ou bloqueio de banco durante a
   requisição, criar a conta por um mecanismo create-only aprovado.
3. Após confirmação `201`, persistir `synapse_created` em uma transação local
   curta, incluindo o `provisioning_device_id` quando houver sessão criada. O
   `access_token` nunca será persistido. Se nem o resultado mínimo puder ser
   registrado, a tentativa permanece ambígua e exige reconciliação.
4. Revogar o dispositivo de provisionamento pela
   [API administrativa suportada](https://element-hq.github.io/synapse/latest/admin_api/user_admin_api.html#delete-a-device).
   Somente a invalidação confirmada, inclusive ausência verificada do
   dispositivo em uma retomada, permite continuar. Falha, timeout ou resultado
   ambíguo mantém o convite indisponível e move a tentativa para
   `reconciliation_required`.
5. Em outra transação local, criar
   `UserRoleAssignment`, marcar o convite como `used` e concluir a tentativa.
   O campo `granted_by` recebe o `created_by` do convite.

O papel do convite será convertido diretamente: `user` para `user` e
`group_admin` para `group_admin`. O cadastro nunca cria `platform_admin` nem
administrador global do Synapse.

As falhas serão classificadas pela última operação que pode ter produzido
efeito:

- validação local, conflito transacional ou conta encontrada antes da
  requisição de criação:
  falha segura; liberar o convite e marcar a tentativa como `released`;
- resposta `201`: registrar `synapse_created` e o identificador do dispositivo
  de provisionamento antes de tentar encerrar a sessão;
- revogação confirmada do dispositivo: permitir a finalização local;
- falha ou resultado ambíguo na revogação: manter
  `reconciliation_required`, sem concluir o convite;
- timeout, queda de conexão ou resposta inesperada depois de iniciar a criação:
  não liberar o convite; marcar `reconciliation_required`;
- falha local depois do `201`: conservar o estado suficiente para retomar a
  revogação e, somente depois dela, concluir a atribuição do papel sem tentar
  criar outra conta;
- estado ambíguo: nunca repetir automaticamente a criação e nunca retornar
  senha, token ou detalhes internos ao cliente.

O [`PUT` administrativo de usuários](https://element-hq.github.io/synapse/latest/admin_api/user_admin_api.html#create-or-modify-account)
não fará parte da ativação porque também modifica contas existentes e pode
redefinir senhas. Antes da implementação será executada uma prova de conceito
do [registro por segredo compartilhado](https://element-hq.github.io/synapse/latest/admin_api/register_api.html),
sempre com `admin: false`. O segredo permanecerá no servidor. O
`access_token` e o `device_id` retornados constituem uma sessão ativa; não
basta descartar o token. O serviço deverá revogar o dispositivo antes de
finalizar o convite, persistindo somente o identificador necessário para
retomada segura. Nenhum desses valores chegará ao navegador.

Essa API de registro fica desabilitada quando o Matrix Authentication Service
(MAS) está integrado. A adoção futura do MAS dependerá de outro mecanismo de
provisionamento aprovado pelos dois colaboradores. A prova de conceito deverá
confirmar comportamento create-only, conflito de identidade, revogação da
sessão criada e compatibilidade com a configuração escolhida do Synapse.

A orquestração não chamará métodos atuais que realizam `commit` internamente;
as transições combinadas serão executadas por uma unidade de trabalho que
possua os limites transacionais acima. Nenhuma transação PostgreSQL permanecerá
aberta durante a requisição ao Synapse.

Os testes da implementação deverão cobrir a matriz completa de falhas com
clientes simulados, concorrência real no PostgreSQL, retomada após interrupção,
idempotência da finalização e ausência de segredos em modelos, erros e
representações. Nenhuma chamada real ao Synapse fará parte desses testes.

### Segurança da página de ativação

- rota pública `/activate` com token somente no fragmento;
- remoção imediata do fragmento por `history.replaceState`;
- nenhum token em `localStorage`, `sessionStorage`, IndexedDB ou estado
  persistido;
- `Referrer-Policy: no-referrer` e `Cache-Control: no-store`;
- CSP com scripts e conexões limitados às origens corporativas aprovadas,
  `object-src 'none'`, `base-uri 'none'` e `frame-ancestors 'none'`;
- nenhuma ferramenta de analytics, tag manager ou script de terceiro;
- corpos de pré-validação e ativação omitidos de logs;
- cadastro público e formulário nativo de registro Matrix indisponíveis;
- página própria que não reutiliza o `PasswordRegisterForm` do Cinny.

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
