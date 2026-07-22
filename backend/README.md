# Backend auxiliar

Área exclusiva do Colaborador 1 para serviços corporativos auxiliares que não duplicam o protocolo Matrix nem o servidor de mensagens.

## Situação

O serviço FastAPI de convites e provisionamento foi autorizado em `DEC-017`. Nenhum código foi implementado ainda. A decisão anterior de usar FastAPI como servidor principal de mensagens continua substituída por `DEC-010`.

## Serviço autorizado

O primeiro escopo do backend auxiliar é:

- criar, listar e revogar convites administrativos;
- validar convite secreto de uso único com validade de 24 horas;
- criar contas pela API administrativa suportada pelo Synapse;
- armazenar papéis próprios sem conceder administração global do Synapse;
- registrar auditoria sem guardar tokens, senhas ou credenciais administrativas;
- apoiar posteriormente bloqueio, redefinição de senha e desligamento.

O contrato está definido em `../docs/API.md`.

## Limites

- Todo serviço de backend pertence ao Colaborador 1.
- O Colaborador 2 não deve modificar esta pasta.
- Não implementar salas, mensagens, sincronização, presença ou mídia que já existam no Matrix.
- Não criar serviço auxiliar sem caso de uso e decisão registrados.
- Não acessar diretamente o banco do Synapse para implementar regras de negócio.
- Não expor tokens administrativos ao frontend.
- Usar PostgreSQL e credenciais próprios, separados do banco lógico do Synapse.
- Manter a credencial administrativa do Synapse somente no servidor.

## Possíveis usos futuros

- Integração com RH ou ERP.
- Integração futura com OIDC, se posteriormente aprovada.
- Relatórios ou exportações aprovados.
- Fluxos administrativos específicos.

FastAPI e PostgreSQL foram aprovados para o serviço de convites. ORM, ferramenta de migração, empacotamento Python e execução por ambiente ainda precisam ser escolhidos antes da implementação.
