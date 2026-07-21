# Instruções locais — backend auxiliar

## Finalidade

Esta pasta pertence ao Colaborador 1. O serviço FastAPI de convites aprovado
em `DEC-017` é sua primeira integração autorizada; novas integrações continuam
dependendo de uma lacuna concreta e decisão registrada.

## Regras

- Limite a implementação autorizada ao fluxo de convites, provisionamento e
  ciclo de vida de contas definido em `DEC-017` e `../docs/API.md`.
- Não duplique salas, mensagens, sincronização, presença ou mídia do Matrix.
- FastAPI é a tecnologia aprovada para o serviço de convites, não para o chat.
- Não exponha tokens administrativos ao navegador.
- Não use acesso direto ao PostgreSQL do Synapse como API de negócio.
- Qualquer extensão deve possuir autenticação, autorização, contrato e testes.
- Use banco e credenciais próprios; não compartilhe o banco lógico do Synapse.
- Nunca registre token de convite, senha ou credencial administrativa em logs.
