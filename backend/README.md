# Backend auxiliar

Área exclusiva do Colaborador 1, reservada para integrações corporativas que Matrix, Synapse, OIDC e suas APIs administrativas não atendam.

## Situação

Nenhum backend personalizado está autorizado ou é necessário para a prova de conceito. A decisão anterior de usar FastAPI como servidor principal de mensagens foi substituída por `DEC-010`.

## Limites

- Todo serviço de backend pertence ao Colaborador 1.
- O Colaborador 2 não deve modificar esta pasta.
- Não implementar salas, mensagens, sincronização, presença ou mídia que já existam no Matrix.
- Não criar serviço auxiliar sem caso de uso e decisão registrados.
- Não acessar diretamente o banco do Synapse para implementar regras de negócio.
- Não expor tokens administrativos ao frontend.

## Possíveis usos futuros

- Integração com RH ou ERP.
- Automação de provisionamento não atendida pelo OIDC.
- Relatórios ou exportações aprovados.
- Fluxos administrativos específicos.

FastAPI continua como candidato para essas integrações, mas ORM, migrações e ambiente Python só serão escolhidos quando uma necessidade concreta for aprovada.
