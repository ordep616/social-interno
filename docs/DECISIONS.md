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

- Status: aceita pelos dois colaboradores.
- Decisão: o cadastro público continuará desabilitado. Um `platform_admin` poderá gerar um link secreto, de uso único e com validade de 24 horas, para que o convidado escolha usuário e senha sem informar e-mail.
- Papéis: o convite poderá conceder `user` ou `group_admin`. A promoção a `platform_admin` será uma operação administrativa separada.
- Implementação: um serviço FastAPI validará o hash do token, validade, uso, cancelamento e limites de tentativa; depois criará a conta pela API administrativa do Synapse, aplicará o papel e invalidará o convite.
- Segurança: token administrativo nunca será entregue ao navegador. Logs de auditoria não registrarão token de convite, senha ou credenciais administrativas.
- Ciclo de vida: redefinição de senha, bloqueio e desligamento serão operações administrativas; seus procedimentos e a revogação de sessões ainda precisam ser implementados e testados.
- Evolução: OIDC poderá ser avaliado posteriormente e não bloqueia o MVP baseado em convite.

## DEC-018 — API própria orientada a REST

- Status: aceita pelos dois colaboradores.
- Decisão: APIs próprias do serviço FastAPI seguirão REST sobre HTTP, serão versionadas em `/v1`, usarão recursos nomeados por substantivos, JSON e códigos HTTP consistentes.
- Contrato inicial: convites administrativos usam `POST`, `GET` e `DELETE` em `/v1/admin/invitations`; a revogação é uma remoção lógica e idempotente. O convidado valida o token em `GET /v1/invitations/{token}` e cria seu cadastro em `POST /v1/registrations`.
- Motivo: manter o contrato simples, previsível, independente de linguagem e compatível com o frontend e ferramentas HTTP comuns.
- Limite: Matrix continua sendo o contrato de salas, mensagens, mídia e sincronização. O FastAPI não encapsula nem redefine a Matrix Client-Server API.
- Segurança: token administrativo do Synapse permanece no servidor; tokens de convite e senhas não são registrados; respostas relacionadas ao convite usam `Cache-Control: no-store`.
- Consequência: mudanças incompatíveis exigem nova versão do contrato e aprovação conjunta antes da implementação no frontend ou backend.

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
