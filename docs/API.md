# Integrações e convenções técnicas

## Estado

A proposta anterior de uma API HTTP/WebSocket própria foi substituída pela adoção do Matrix. Seus contratos não aprovados foram removidos e não devem orientar implementação nova.

## Contrato principal

O frontend utilizará a Matrix Client-Server API por meio da integração existente no fork do Cinny. Não serão recriados endpoints próprios para salas, mensagens, sincronização, leitura, digitação, presença ou mídia.

## Configuração compartilhada inicial

Os dois colaboradores precisam aprovar e documentar:

- URL pública do homeserver por ambiente;
- fluxo de login e redirecionamento OIDC;
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

## Extensões corporativas

Uma API auxiliar só será criada quando houver uma necessidade que Matrix, Synapse, OIDC e suas APIs administrativas não atendam, por exemplo:

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
