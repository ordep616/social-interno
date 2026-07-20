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
- Decisão: Colaborador 1 assume frontend e análise de código aberto; Colaborador 2 assume backend, infraestrutura e segurança.

## Decisões pendentes

- Tecnologia final do backend.
- PostgreSQL/Redis/MinIO local ou serviços equivalentes em nuvem privada.
- Provedor OIDC/SAML.
- Licença do código próprio.
- Política de retenção.
- Nome e identidade visual.
