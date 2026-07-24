# Registro de decisões

Não apague decisões antigas. Quando algo mudar, marque a decisão anterior como substituída e crie uma nova entrada.

## DEC-001 — Produto web

- Status: aceita.
- Decisão: o produto será um site responsivo, com possibilidade de instalação como PWA.
- Motivo: menor complexidade de distribuição e manutenção do que clientes nativos.

## DEC-002 — Infraestrutura própria

- Status: aceita.
- Decisão: contas, mensagens, arquivos e autenticação ficarão em infraestrutura controlada pela organização.
- Consequência: nenhuma comunicação operacional dependerá da rede Telegram.

## DEC-003 — Não implementar servidor MTProto

- Status: aceita.
- Decisão original: seria criada uma API corporativa via HTTPS e WebSockets.
- Motivo: reproduzir a API e o comportamento do backend do Telegram teria custo e risco elevados.
- Atualização: a rejeição ao MTProto continua aceita, mas a API própria foi substituída pelo uso do protocolo Matrix em `DEC-010`.

## DEC-004 — Reutilização seletiva

- Status: substituída inicialmente por `DEC-011` e posteriormente por `DEC-014`.
- Decisão original: componentes abertos do Telegram Web poderiam ser avaliados individualmente.
- Consequência atual: o Cinny é a base aprovada; Telegram Web e Element Web permanecem somente como referências.

## DEC-005 — Divisão inicial

- Status: atualizada por `DEC-010` e `DEC-011`.
- Decisão original: o responsável principal assumiria backend e infraestrutura; o outro colaborador assumiria frontend e análise de código aberto.
- Divisão atual: o Colaborador 1 assume todo o backend, plataforma Matrix/Synapse, PostgreSQL, infraestrutura, identidade, segurança e integrações; o Colaborador 2 assume frontend, interface web/PWA e integração com o SDK.

## DEC-006 — Desenvolvimento orientado a contratos

- Status: substituída por `DEC-012`.
- Decisão original: frontend e backend seriam desenvolvidos em paralelo usando uma API corporativa versionada.
- Consequência atual: o Matrix é o contrato principal; apenas extensões corporativas próprias terão contrato interno.

## DEC-007 — Propriedade por diretório

- Status: aceita.
- Decisão: cada colaborador possui sua área principal e não modifica a área do outro durante o desenvolvimento normal.
- Consequência: mudanças compartilhadas ficam limitadas às convenções Matrix, extensões em `contracts/` e documentos de integração.

## DEC-008 — Integração por marcos

- Status: aceita.
- Decisão: a integração não será contínua nem bloqueará o trabalho diário. Ela ocorrerá em marcos curtos após cada conjunto funcional.
- Marcos iniciais: autenticação, conversas, mensagens em tempo real e arquivos.

## DEC-009 — FastAPI para o backend

- Status: substituída por `DEC-010`.
- Decisão original: o backend seria desenvolvido em Python com FastAPI.
- Motivos: integração direta com OpenAPI e JSON Schema, validação com Pydantic, suporte oficial a WebSockets e menor carga inicial para uma equipe pequena.
- Consequência atual: FastAPI poderá ser usado posteriormente apenas em integrações corporativas que o Matrix não atender; ele não será o servidor de mensagens.

## DEC-010 — Adaptar uma plataforma Matrix

- Status: aceita em princípio; condicionada à prova de conceito e revisão de licença.
- Decisão: utilizar o protocolo Matrix e inicialmente o homeserver Synapse, auto-hospedado pela organização, em vez de desenvolver o backend de comunicação.
- Motivo: salas, mensagens, sincronização, histórico, mídia e estados em tempo real já existem na plataforma.
- Consequência: o trabalho principal de backend passa a ser implantação, configuração, identidade, isolamento, segurança, operação e integrações opcionais.

## DEC-011 — Interface própria sobre o SDK Matrix

- Status: substituída por `DEC-014`.
- Decisão: criar interface web/PWA própria usando `matrix-js-sdk`, sem criar um fork integral do Telegram Web ou Element Web.
- Motivo: manter identidade e experiência próprias com menor risco de acoplamento e licenciamento.
- Consequência: referências visuais podem ser estudadas, mas qualquer código incorporado continua sujeito ao inventário e à aprovação.

## DEC-012 — Trabalho paralelo orientado pelo Matrix

- Status: aceita.
- Decisão: o protocolo Matrix, a configuração do homeserver e convenções aprovadas formam o limite entre as duas trilhas.
- Consequência: o frontend testa com um homeserver Matrix de desenvolvimento; a plataforma é validada com clientes genéricos e não depende da interface própria.

## DEC-013 — Versões da prova de conceito Matrix

- Status: atualizada por `DEC-014`; versões ainda exigem validação antes de produção.
- Decisão original: iniciar a prova de conceito com Synapse `1.156.0`, PostgreSQL `17.6-alpine` e `matrix-js-sdk` `41.9.0`.
- Atualização: o fork do Cinny `v4.12.3` fixa `matrix-js-sdk` `41.7.0`; essa passa a ser a versão do cliente durante a prova de conceito.
- Motivo: utilizar versões estáveis e explícitas, evitando tags mutáveis como `latest`.
- Consequência: atualizações serão deliberadas e acompanhadas de testes e revisão de mudanças incompatíveis.
- Limite: essas versões ainda não estão aprovadas para produção.

## DEC-014 — Fork corporativo do Cinny

- Status: aceita pelos dois colaboradores.
- Decisão: utilizar o Cinny `v4.12.3`, commit `69515e8e81d082a7b0609247e296391d3d6f1e38`, como base integral do frontend e preservar o máximo possível de sua interface.
- Motivo: reduzir o desenvolvimento de recursos Matrix já disponíveis e concentrar a equipe em isolamento, identidade corporativa, autenticação e operação.
- Licença: AGPL-3.0-only; o código-fonte correspondente e os avisos obrigatórios serão preservados e disponibilizados conforme a licença.
- Consequência: a interface Next.js própria e seu adaptador inicial foram substituídos. Alterações no fork devem ser pequenas, rastreáveis e reaplicáveis sobre novas versões do Cinny.
- Limite: servidores externos, cadastro público, descoberta de comunidades públicas e recursos fora do MVP devem permanecer indisponíveis na implantação corporativa.

## DEC-015 — Federação privada inicialmente fechada

- Status: aceita pelos dois colaboradores e validada na prova de conceito.
- Decisão: a arquitetura admite somente federação privada por lista explícita de organizações parceiras; inicialmente a lista ficará vazia e nenhum listener de federação será exposto.
- Validação: a API cliente respondeu com `200`, enquanto a API de federação respondeu com `404`, tanto localmente quanto pela borda pública temporária. O cadastro público respondeu com `403` e o diretório público sem autenticação respondeu com `401`.
- Consequência: no estado inicial não existe comunicação externa. A inclusão futura de uma organização exige aprovação conjunta, lista de permissão recíproca, proteção na borda e novo teste entre dois homeservers.
- Limite: a lista de permissão do Synapse não substitui firewall, proxy reverso ou controle de ingresso.

## DEC-016 — Política híbrida de criptografia ponta a ponta

- Status: aceita pelos dois colaboradores.
- Decisão: conversas diretas internas terão criptografia ponta a ponta obrigatória; grupos confidenciais também usarão criptografia; grupos institucionais ou sujeitos a auditoria operarão sem criptografia ponta a ponta.
- Administração: o administrador define a política no momento da criação do grupo e a interface deve indicar claramente o estado de criptografia.
- Recuperação: recuperação e proteção das chaves devem estar definidas e testadas antes do piloto.
- Federação: salas federadas, quando existirem, terão política de criptografia avaliada separadamente.

## DEC-017 — Cadastro controlado por convite

- Status: substituída parcialmente por `DEC-022`, aceita pelos dois
  colaboradores. A regra em que o convidado escolhe o usuário não deve
  orientar nova implementação.
- Decisão histórica: o cadastro público continuaria desabilitado e um
  `platform_admin` geraria um link para o convidado escolher usuário e senha.
  Essa escolha de identidade não deve orientar nova implementação durante a
  revisão de `DEC-022`.
- Papéis: o convite poderá conceder `user` ou `group_admin`. A promoção a `platform_admin` será uma operação administrativa separada.
- Implementação: um serviço FastAPI validará o hash do token, validade, uso, cancelamento e limites de tentativa; depois criará a conta pela API administrativa do Synapse, aplicará o papel e invalidará o convite.
- Segurança: token administrativo nunca será entregue ao navegador. Logs de auditoria não registrarão token de convite, senha ou credenciais administrativas.
- Ciclo de vida: redefinição de senha, bloqueio e desligamento serão operações administrativas; seus procedimentos e a revogação de sessões ainda precisam ser implementados e testados.
- Evolução: OIDC poderá ser avaliado posteriormente e não bloqueia o MVP baseado em convite.

## DEC-018 — API própria orientada a REST

- Status: aceita pelos dois colaboradores; o estilo REST permanece vigente e
  o contrato inicial de cadastro foi substituído parcialmente por `DEC-022`.
- Decisão: APIs próprias do serviço FastAPI seguirão REST sobre HTTP, serão versionadas em `/v1`, usarão recursos nomeados por substantivos, JSON e códigos HTTP consistentes.
- Contrato inicial histórico: convites administrativos usam `POST`, `GET` e
  `DELETE` em `/v1/admin/invitations`; a revogação é lógica e idempotente. A
  validação com token no caminho e o `username` escolhido pelo convidado não
  devem orientar nova implementação durante a revisão de `DEC-022`.
- Motivo: manter o contrato simples, previsível, independente de linguagem e compatível com o frontend e ferramentas HTTP comuns.
- Limite: Matrix continua sendo o contrato de salas, mensagens, mídia e sincronização. O FastAPI não encapsula nem redefine a Matrix Client-Server API.
- Segurança: token administrativo do Synapse permanece no servidor; tokens de convite e senhas não são registrados; respostas relacionadas ao convite usam `Cache-Control: no-store`.
- Consequência: mudanças incompatíveis exigem nova versão do contrato e aprovação conjunta antes da implementação no frontend ou backend.

## DEC-019 — Fundação técnica do serviço de convites

- Status: aceita pelos dois colaboradores.
- Execução: CPython `>=3.14,<3.15`, FastAPI sem o extra `standard`, Uvicorn explícito e implementação inicialmente síncrona.
- Persistência: PostgreSQL próprio, SQLAlchemy `2.0.x` estável, Psycopg 3 com extra `binary` e Alembic. SQLAlchemy `2.1` não será adotado enquanto estiver em pré-lançamento.
- Configuração e integração: `pydantic-settings` para variáveis de ambiente, HTTPX para a API do Synapse e `secrets`/`hashlib` da biblioteca padrão para tokens.
- Ambiente: `uv`, `pyproject.toml`, `.python-version`, ambiente virtual local ignorado e `uv.lock` versionado.
- Qualidade: Ruff para lint e formatação, mypy para tipos, pytest para testes e pytest-cov para cobertura.
- Motivo: usar uma base pequena, reproduzível, tipada e comum no ecossistema Python, reduzindo a complexidade inicial do serviço administrativo.
- Licenças: dependências diretas serão registradas antes da incorporação. As transitivas serão identificadas na primeira resolução e registradas antes do merge da implementação. Psycopg 3 e o extra `binary` exigem atenção específica à `LGPL-3.0-only` e às bibliotecas empacotadas antes de homologação ou produção.
- Limite: a fundação é exclusiva para convites, provisionamento e ciclo de vida de contas aprovados. Ela não implementa chat nem substitui Matrix ou Synapse.

## DEC-020 — Mensagens de voz no MVP e chamadas em fase posterior

- Status: aceita pelos dois colaboradores; o Colaborador 2 delegou a escolha final de escopo ao Colaborador 1.
- Escopo: mensagens de voz gravadas entram no MVP. Chamadas de voz e vídeo continuam fora do MVP, mas poderão receber uma prova de conceito paralela que não bloqueia o piloto inicial.
- Mensagens de voz: utilizarão o evento Matrix `m.audio` e o fluxo de mídia já existente no Cinny, sem passar pelo FastAPI. A gravação terá limite inicial de 5 minutos e 10 MB.
- Compatibilidade: WebM/Opus será o formato preferencial e MP4/AAC será aceito como alternativa para navegadores que não produzam WebM. Os formatos definitivos serão confirmados em testes de navegador e celular.
- Segurança: mensagens de voz herdam a criptografia e a retenção da sala. O acesso ao microfone será solicitado somente durante a gravação e exigirá contexto seguro fora de `localhost`.
- Chamadas: a prova de conceito reutilizará MatrixRTC e o Element Call incorporado ao Cinny, com LiveKit, MatrixRTC Authorization Service (`lk-jwt-service`) e coturn. A equipe não desenvolverá uma pilha WebRTC própria.
- Implantação: chamadas externas exigirão domínio, HTTPS, descoberta por `.well-known/matrix/client`, TURN com IP público, proteção de rede, limites e observabilidade. A federação pública continuará desabilitada.
- Validação: a prova de conceito começará com duas pessoas em redes diferentes. Chamadas em grupo só avançarão depois da validação funcional, de segurança e de capacidade.
- Código aberto: versões, commits, imagens, arquivos incorporados e licenças dos componentes de chamada deverão ser aprovados e registrados antes da incorporação à plataforma.

## DEC-021 — Orquestração durável do cadastro

- Status: aceita pelos dois colaboradores; a origem da identidade e o
  mecanismo de criação usados especificamente na ativação foram atualizados
  por `DEC-022`.
- Problema: PostgreSQL e Synapse não compartilham uma transação. Uma interrupção entre criar a conta, atribuir o papel e concluir o convite pode deixar estado parcial.
- Decisão proposta: coordenar o cadastro como uma saga durável, com uma tentativa operacional persistida e fases transacionais locais separadas da chamada HTTP.
- Identidade proposta: `username` terá 3 a 32 caracteres ASCII minúsculos, começará e terminará com letra ou número e aceitará apenas `.`, `_` e `-` no interior. Maiúsculas serão rejeitadas, não normalizadas. O backend acrescentará o `server_name` configurado. Conforme `DEC-022`, esse valor virá exclusivamente da identidade definida pelo `platform_admin`.
- Senha proposta: 15 a 128 caracteres, sem regras de composição, transformação, persistência ou registro. A fonte e a licença de uma lista local de senhas comuns ou comprometidas serão aprovadas antes do endpoint público.
- Referência de senha: a proposta segue a orientação para senha de fator único do [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html), preservando frases-senha, espaços, Unicode e gerenciadores de senha.
- Concorrência: a reserva do convite e a criação da tentativa ocorrerão na mesma transação. Restrições únicas parciais impedirão tentativas ativas simultâneas para o mesmo convite ou identidade.
- Provisionamento: nenhuma transação de banco ficará aberta durante a chamada ao Synapse. Para o mecanismo aprovado em `DEC-022`, a resposta `200 OK` do registro administrativo permitirá persistir o resultado externo, mas a finalização local continuará condicionada à revogação comprovada em `DEC-023`. Resultados que possam ter criado uma conta serão tratados como ambíguos. A ativação não deverá modificar contas existentes.
- Finalização: atribuição do papel próprio, conclusão do convite e conclusão da tentativa ocorrerão atomicamente no PostgreSQL. O convite nunca concederá `platform_admin` ou administração global do Synapse.
- Reconciliação: falha seguramente anterior à requisição de criação poderá liberar o convite. Falha posterior ou ambígua manterá o convite indisponível e exigirá reconciliação, sem repetição automática da criação.
- Persistência: `registration_attempts` guardará somente identificadores, papel, estado, instantes e código sanitizado de falha. Não guardará token, hash de token, senha, credencial administrativa ou corpo retornado pelo Synapse.
- Limite: esta decisão não cria endpoints públicos, contas reais, auditoria, limites de tentativa, bloqueio, redefinição de senha ou desligamento.

## DEC-022 — Ativação de identidade previamente definida

- Status: aceita pelos dois colaboradores em 2026-07-23. A decisão define o
  contrato e o desenho aprovados, mas cada implementação, migração ou
  publicação ainda exige autorização própria.
- Problema: `DEC-017` permite que o portador do convite escolha o `username`.
  Isso concede liberdade indevida para criar identidades e não atende ao fluxo
  administrativo em que a organização autoriza previamente cada conta.
- Administração: somente uma sessão Matrix válida associada ao papel
  próprio `platform_admin` poderá criar, listar ou revogar links de ativação.
  `user` e `group_admin` não recebem essa capacidade. Ocultar a interface é
  apenas experiência; o backend continuará sendo a autoridade.
- Identidade: o `platform_admin` escolherá `username` e papel
  `user` ou `group_admin` antes da emissão. O backend validará o nome,
  acrescentará seu `server_name` configurado e persistirá o
  `target_user_id` completo. O funcionário não poderá mudar identidade ou
  papel.
- Senha: somente o funcionário informará a senha na ativação. O
  administrador não a define nem a conhece; backend e frontend não a
  persistem, registram ou colocam em URL. As regras de senha de `DEC-021`
  permanecem aplicáveis a esse campo.
- Papéis: um link poderá conceder somente `user` ou
  `group_admin`. A ativação jamais concederá `platform_admin` ou
  administração global do Synapse.
- Link: a URL pública usará `/activate#<token>`. O fragmento não será
  enviado em requisições HTTP; o frontend o lerá uma vez, chamará
  `history.replaceState` e conservará o token apenas em memória.
- Pré-validação: `POST /v1/activation-validations` receberá o token
  no corpo e retornará identidade, papel e expiração quando utilizável. Não
  existirá preflight público com token no caminho.
- Ativação: `POST /v1/registrations` receberá somente token e senha,
  criará a conta autorizada e retornará apenas `user_id`. O frontend seguirá
  para o login Matrix normal com o `username` preenchido, sem receber sessão
  ou token Matrix do backend.
- Capacidades: `GET /v1/me/capabilities` validará a credencial
  Matrix por `whoami` e retornará o papel próprio e a capacidade
  `can_manage_user_activations`. A rota administrativa verificará
  `platform_admin` novamente em cada operação. `user` e `group_admin`
  receberão a capacidade falsa; convidado Matrix ou identidade sem papel
  próprio receberá `403`. O frontend permanecerá fechado diante de qualquer
  erro e não confundirá esse contrato com as capacidades nativas Matrix.
- Persistência: `invitations` receberá `target_user_id`; um índice
  único parcial impedirá dois convites ativos para a mesma identidade. O
  estado terminal `conflicted` representará identidade confirmadamente
  indisponível antes da criação.
- Migração: convites legados pendentes sem identidade serão
  revogados; registros usados poderão derivar `target_user_id` de
  `accepted_user_id`; qualquer registro legado em processamento bloqueará a
  implantação até revisão manual. Estados históricos terminais poderão
  conservar `target_user_id` nulo.
- Conflitos: a emissão consultará a disponibilidade suportada pelo
  Synapse, mas essa consulta não reserva a identidade. A criação deverá usar
  mecanismo create-only e tratar identidade já utilizada como conflito. Uma
  conta existente nunca será atualizada, reativada ou terá senha redefinida
  por um link.
- Provisionamento: o
  [`PUT` administrativo de usuários](https://element-hq.github.io/synapse/latest/admin_api/user_admin_api.html#create-or-modify-account)
  não será usado para ativação porque também modifica contas existentes. Será
  feita uma prova de conceito do
  [registro por segredo compartilhado](https://element-hq.github.io/synapse/latest/admin_api/register_api.html),
  com conta sempre não administrativa. A prova comparará exatamente o
  `user_id` retornado com o `target_user_id` autorizado e verificará também o
  domínio Matrix configurado. O `access_token` e o `device_id` retornados
  representam uma sessão ativa: antes da revogação, `whoami` deverá responder
  `200`, com o mesmo `user_id` e `device_id`. O token nunca será persistido ou
  enviado ao navegador, e o dispositivo deverá ser revogado pela API
  administrativa antes de concluir a ativação. A confirmação exigirá
  dispositivo ausente (`404`) e o token de provisionamento recusado por
  `whoami` (`401`). Divergência de identidade, falha ou resultado ambíguo na
  validação ou revogação levará a tentativa para
  `reconciliation_required`, sem marcar o convite como usado.
- Compatibilidade com MAS: o registro por segredo compartilhado fica
  desabilitado quando o Matrix Authentication Service (MAS) está integrado.
  Uma futura adoção do MAS exigirá outro mecanismo de provisionamento,
  registrado em nova decisão conjunta antes de substituir esse fluxo. A adoção
  do mecanismo inicial depende da prova de conceito, da proteção do segredo e
  da confirmação de compatibilidade com a configuração escolhida do Synapse.
- Consistência: Synapse e PostgreSQL não serão descritos como uma
  transação ACID. A saga de `DEC-021` reservará convite e tentativa, fechará a
  transação local, fará a criação externa, revogará a sessão de provisionamento
  e somente então finalizará papel, convite e tentativa. Resultado ambíguo na
  criação ou na revogação permanecerá bloqueado para reconciliação, sem
  repetição automática.
- Respostas: token inexistente retorna `404`; expirado, usado ou
  revogado compartilham `410` genérico; identidade indisponível retorna `409`;
  limitação retorna `429`. Todas as respostas de ativação usam
  `Cache-Control: no-store`.
- Segurança: a página de ativação terá `Referrer-Policy:
  no-referrer`, CSP restritiva, `frame-ancestors 'none'`, nenhum analytics ou
  script de terceiro e nenhum token em storage. Corpos sensíveis serão
  omitidos de logs; auditoria e limites são obrigatórios antes da publicação.
  Na prova de conceito, os loggers de registro e autenticação do Synapse não
  operarão em `DEBUG`, recursos de log sensível permanecerão desabilitados e
  senha, segredo compartilhado, MAC, nonce, tokens e corpos sensíveis não
  poderão aparecer em logs ou relatórios.
- Compatibilidade com o frontend: o cadastro público e o cadastro nativo do Cinny
  permanecerão indisponíveis. A ativação será uma camada corporativa anterior
  ao login e não modificará profundamente o fluxo Matrix normal do fork.
- Contrato: como os endpoints públicos ainda não foram publicados,
  a revisão ocorrerá em `/v1`; qualquer implantação anterior exigiria `/v2`.
- Limite: esta decisão não autoriza código, conta real, segredo de produção,
  endpoint público, migração, alteração no Synapse ou interface.

## DEC-023 — Evidência durável da revogação da sessão de provisionamento

- Status: aceita pelos dois colaboradores em 2026-07-23. A decisão define o
  contrato e as invariantes aprovadas, mas código e migração ainda exigem
  autorização própria.
- Problema: o registro por segredo compartilhado cria uma sessão Matrix. A
  remoção do dispositivo ocorre no Synapse e a conclusão do convite ocorre no
  PostgreSQL próprio; não existe transação ACID entre essas operações. O estado
  `synapse_created`, isoladamente, não comprova que a sessão foi revogada.
- Persistência: `registration_attempts` receberá
  `provisioning_device_id` e `provisioning_session_revoked_at`, ambos
  inicialmente nulos. O `access_token` retornado pelo Synapse nunca será
  persistido.
- Criação: após resposta `200 OK` do registro administrativo, o serviço
  comparará exatamente o `user_id` retornado com o `target_user_id`
  autorizado, validará o domínio Matrix configurado e usará `whoami` para
  comprovar que o token representa esse usuário e o `device_id` retornado.
  Somente então a tentativa passará para `synapse_created` e persistirá o
  `provisioning_device_id` antes de iniciar a revogação. Divergência, falha ou
  resultado ambíguo nessa validação, assim como falha ao registrar o resultado,
  exigirá reconciliação.
- Revogação: no fluxo inicial, a exclusão somente será considerada confirmada
  depois de o dispositivo responder como ausente (`404`) e o token de
  provisionamento ser recusado por `whoami` (`401`). Depois dessa confirmação,
  ou da ausência verificada do dispositivo em uma retomada, o serviço preencherá
  `provisioning_session_revoked_at` em uma transação local curta. Se a
  tentativa estiver em `reconciliation_required`, a mesma transação deverá
  movê-la condicionalmente para `synapse_created`, limpar `failure_code` e
  atualizar `updated_at`. Timeout, indisponibilidade ou resultado inconclusivo
  manterão o campo nulo e a tentativa em `reconciliation_required`.
- Finalização: a unidade de trabalho somente poderá atribuir papel,
  concluir o convite e marcar a tentativa como `completed` quando o estado for
  `synapse_created`, `provisioning_device_id` estiver preenchido e
  `provisioning_session_revoked_at` não for nulo. O chamador não poderá
  contornar essa pré-condição.
- Restrições: estados `synapse_created` e `completed` exigirão
  `provisioning_device_id`; uma tentativa `completed` exigirá
  `provisioning_session_revoked_at`; todo instante de revogação exigirá
  `provisioning_device_id`, não poderá ser anterior a `created_at` e só poderá
  existir em `synapse_created` ou `completed`. Estados `processing` e
  `released` exigirão ambos os campos de provisionamento nulos.
- Retomada: se o processo cair depois da revogação externa e antes do
  registro local, a reconciliação verificará a ausência do dispositivo pelo
  identificador persistido e só então executará atomicamente a transição para
  `synapse_created`, gravará a evidência, limpará a falha e permitirá a
  finalização. Uma atualização concorrente ou uma pré-condição divergente
  manterá a tentativa bloqueada.
- Compatibilidade futura: um mecanismo create-only que comprovadamente não
  crie sessão exigirá ajuste explícito desse contrato antes de substituir o
  registro por segredo compartilhado.
- Segurança: `provisioning_device_id` é dado operacional interno, não aparece
  em resposta pública ou log e segue a retenção das tentativas. Senha, token
  de convite, hash do token e credenciais administrativas permanecem fora da
  tabela.
- Limite: esta decisão detalha somente a evidência de revogação. Ela não
  cria endpoint, executa chamada ao Synapse, restaura o stash ou autoriza
  implementação.

## Decisões pendentes
- Confirmação do Synapse após prova de conceito e revisão da licença AGPL/comercial aplicável.
- Aprovação das versões da prova de conceito para homologação e produção.
- Domínio de produção e formato definitivo dos identificadores Matrix.
- Implementação e teste da recuperação de chaves para a política híbrida de criptografia.
- Implementação do serviço de convites e do ciclo de vida das contas.
- Armazenamento de mídia e estratégia de backup.
- Licença do código próprio.
- Política de retenção.
- Nome e identidade visual definitivos; os textos genéricos atuais são provisórios.
