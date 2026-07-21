# Instruções locais — backend auxiliar

## Finalidade

Esta pasta pertence ao Colaborador 1 e permanece reservada para integrações
corporativas que Matrix, Synapse, OIDC e APIs administrativas não atendam.

## Regras

- Não implemente nada aqui sem uma lacuna concreta e decisão registrada.
- Não duplique salas, mensagens, sincronização, presença ou mídia do Matrix.
- FastAPI é apenas uma tecnologia candidata para integrações aprovadas.
- Não exponha tokens administrativos ao navegador.
- Não use acesso direto ao PostgreSQL do Synapse como API de negócio.
- Qualquer extensão deve possuir autenticação, autorização, contrato e testes.
