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
- Decisão: será criada uma API corporativa via HTTPS e WebSockets.
- Motivo: reproduzir a API e o comportamento do backend do Telegram teria custo e risco elevados.

## DEC-004 — Reutilização seletiva

- Status: aceita.
- Decisão: componentes abertos do Telegram Web poderão ser avaliados individualmente.
- Consequência: não será feito um fork integral antes da análise técnica e jurídica.

## DEC-005 — Divisão inicial

- Status: aceita.
- Decisão: o responsável principal deste workspace assume backend, banco de dados, infraestrutura, segurança e integrações; o outro colaborador assume frontend e análise de código aberto.

## DEC-006 — Desenvolvimento orientado a contratos

- Status: aceita.
- Decisão: frontend e backend serão desenvolvidos em paralelo usando contratos versionados.
- Consequência: o frontend terá servidor mock e exemplos próprios; o backend terá testes de contrato e não dependerá das telas.

## DEC-007 — Propriedade por diretório

- Status: aceita.
- Decisão: cada colaborador possui sua área principal e não modifica a área do outro durante o desenvolvimento normal.
- Consequência: mudanças compartilhadas ficam limitadas a `contracts/` e documentos de integração.

## DEC-008 — Integração por marcos

- Status: aceita.
- Decisão: a integração não será contínua nem bloqueará o trabalho diário. Ela ocorrerá em marcos curtos após cada conjunto funcional.
- Marcos iniciais: autenticação, conversas, mensagens em tempo real e arquivos.

## Decisões pendentes

- Tecnologia final do backend.
- PostgreSQL/Redis/MinIO local ou serviços equivalentes em nuvem privada.
- Provedor OIDC/SAML.
- Licença do código próprio.
- Política de retenção.
- Nome e identidade visual.
