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

- Status: substituída por `DEC-011`.
- Decisão original: componentes abertos do Telegram Web poderiam ser avaliados individualmente.
- Consequência atual: Telegram Web e Element Web podem ser estudados como referência, mas a interface será própria.

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

- Status: aceita.
- Decisão: criar interface web/PWA própria usando `matrix-js-sdk`, sem criar um fork integral do Telegram Web ou Element Web.
- Motivo: manter identidade e experiência próprias com menor risco de acoplamento e licenciamento.
- Consequência: referências visuais podem ser estudadas, mas qualquer código incorporado continua sujeito ao inventário e à aprovação.

## DEC-012 — Trabalho paralelo orientado pelo Matrix

- Status: aceita.
- Decisão: o protocolo Matrix, a configuração do homeserver e convenções aprovadas formam o limite entre as duas trilhas.
- Consequência: o frontend testa com um homeserver Matrix de desenvolvimento; a plataforma é validada com clientes genéricos e não depende da interface própria.

## DEC-013 — Versões da prova de conceito Matrix

- Status: em avaliação; requer revisão do Colaborador 2 antes do merge.
- Decisão: iniciar a prova de conceito com Synapse `1.156.0`, PostgreSQL `17.6-alpine` e `matrix-js-sdk` `41.9.0`.
- Motivo: utilizar versões estáveis e explícitas, evitando tags mutáveis como `latest`.
- Consequência: atualizações serão deliberadas e acompanhadas de testes e revisão de mudanças incompatíveis.
- Limite: essas versões ainda não estão aprovadas para produção.

## Decisões pendentes
- Confirmação do Synapse após prova de conceito e revisão da licença AGPL/comercial aplicável.
- Aprovação das versões da prova de conceito para homologação e produção.
- Federação completamente desabilitada ou restrita.
- Criptografia ponta a ponta no MVP e política de recuperação.
- Provedor OIDC.
- Armazenamento de mídia e estratégia de backup.
- Licença do código próprio.
- Política de retenção.
- Nome e identidade visual.
