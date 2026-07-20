# Adaptador Matrix

Esta camada pertence ao Colaborador 2 e impede que os componentes visuais dependam diretamente de `matrix-js-sdk`.

## Responsabilidades atuais

- criar um `MatrixClient` a partir de uma sessão já autenticada;
- iniciar e encerrar a sincronização;
- listar salas como conversas;
- mapear eventos de mensagem para tipos próprios;
- carregar histórico anterior;
- enviar texto, leitura e indicador de digitação.

## Ainda não implementado

- fluxo OIDC e persistência segura da sessão;
- assinatura reativa dos eventos da linha do tempo;
- criação de conversas e grupos;
- participantes e permissões;
- upload e download de mídia;
- criptografia ponta a ponta;
- ligação do adaptador ao protótipo visual.

As telas em `frontend/app/` ainda usam dados simulados. A integração visual pertence à próxima tarefa do Colaborador 2.
