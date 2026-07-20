# Arquitetura pretendida

## Visão geral

O produto será uma adaptação de uma plataforma Matrix auto-hospedada. A equipe não implementará um protocolo de mensagens nem um servidor de chat próprio.

```text
Navegador / PWA
  ├── Interface e identidade visual próprias
  ├── Estado e cache da aplicação
  └── Adaptador isolado para matrix-js-sdk
                    │
                    ▼
          Homeserver Matrix (Synapse)
          ├── contas, salas e mensagens
          ├── sincronização e tempo real
          ├── anexos e confirmações
          ├── autorização e administração
          └── integração OIDC/SSO
                    │
             ┌──────┴──────┐
             ▼             ▼
        PostgreSQL   mídia/armazenamento

Serviço corporativo opcional (FastAPI)
  └── somente integrações que o Matrix não atender
```

## Tecnologias adotadas ou candidatas

- Protocolo: Matrix Client-Server API.
- Homeserver inicial: Synapse, sujeito à prova de conceito e revisão de licença.
- SDK do frontend: `matrix-js-sdk`.
- Frontend: aplicação web/PWA própria; framework ainda deve ser confirmado.
- Banco do Synapse: PostgreSQL.
- Identidade: OIDC por meio do provedor corporativo.
- Ambiente: contêineres durante desenvolvimento e homologação.
- Serviço complementar: FastAPI somente se surgir uma necessidade corporativa não coberta pelo Matrix ou pelas APIs administrativas do Synapse.

## Limites

### Frontend — Colaborador 2

- Implementa somente interface, experiência, estado visual e adaptação do SDK.
- Não acessa PostgreSQL, armazenamento ou APIs administrativas diretamente.
- Não importa código, tipos ou clientes do Telegram.
- Centraliza o acesso ao Matrix em um adaptador próprio para evitar acoplamento dos componentes visuais ao SDK.
- Recebe URL do homeserver e opções públicas por configuração, nunca segredos administrativos.

### Backend, plataforma e infraestrutura — Colaborador 1

- O Synapse é a fonte de verdade para contas Matrix, salas, participantes, mensagens, mídia e sincronização.
- O acesso público, o registro livre e a federação externa permanecem desabilitados, salvo decisão conjunta posterior.
- O provedor OIDC autentica os funcionários; as políticas do Synapse controlam o acesso à plataforma.
- A administração deve usar APIs e módulos suportados, evitando alterações diretas no banco do Synapse.
- FastAPI não duplicará mensagens, salas, presença ou sincronização.

### Dados

- PostgreSQL guarda o estado persistente do homeserver.
- O armazenamento de mídia segue a configuração suportada pelo Synapse.
- Cache e filas adicionais só serão incluídos quando houver necessidade comprovada.
- Backup, retenção, auditoria e restauração precisam considerar banco, mídia e configuração como um conjunto.

## Arquitetura para trabalho paralelo

```text
            configuração e convenções aprovadas
       homeserver + autenticação + tipos de sala
                    /                 \
                   ▼                   ▼
       Colaborador 2           Colaborador 1
       Frontend independente   Backend/plataforma independente
       ├─ adaptador Matrix      ├─ Synapse de homologação
       ├─ cliente de teste      ├─ PostgreSQL e mídia
       ├─ estados simulados     ├─ OIDC e políticas
       └─ testes de UI          └─ testes operacionais
                   \                   /
                    ▼                 ▼
                 marcos de integração
```

### Regras de independência

- O colaborador de frontend desenvolve contra um homeserver Matrix local ou de teste e simula estados de erro quando necessário.
- O responsável pela plataforma valida o Synapse com clientes e ferramentas genéricas, sem depender da interface própria.
- Eventos e formatos padrão do Matrix não serão redefinidos em contratos internos.
- Eventos personalizados, APIs auxiliares e convenções de salas exigem aprovação conjunta e documentação.
- Nenhum colaborador altera a área do outro durante o trabalho normal.

### Estrutura recomendada

```text
frontend/       Colaborador 2: interface, adaptador matrix-js-sdk e testes visuais
platform/       Colaborador 1: configuração do Synapse, contêineres e operação
backend/        Colaborador 1: integrações FastAPI opcionais; não é o servidor de chat
docs/           decisões, planejamento e inventário de código aberto
```

O diretório `contracts/` será criado somente quando uma extensão corporativa própria exigir contrato versionado.

## Mapeamento funcional inicial

| Necessidade do produto | Recurso da plataforma |
|---|---|
| Conversa individual ou grupo | Sala Matrix |
| Mensagem e histórico | Eventos e sincronização Matrix |
| Leitura e digitação | Receipts e typing notifications |
| Presença | Presence, se habilitada pela política |
| Imagens e documentos | Repositório de mídia Matrix |
| Login corporativo | OIDC no Synapse |
| Administração | APIs administrativas e políticas do Synapse |

## Segurança

- HTTPS obrigatório fora do computador local.
- Cadastro público desabilitado.
- Federação desabilitada por padrão e validada em teste.
- Login pelo provedor corporativo e encerramento de acesso após desligamento.
- Segredos fora do frontend e do repositório.
- Limites de requisição e upload configurados.
- Política explícita para criptografia ponta a ponta, recuperação e auditoria.
- Backups testados e criptografados.
- Atualizações de segurança do homeserver acompanhadas continuamente.

## Estratégia de código aberto

O projeto adotará Matrix/Synapse como plataforma e `matrix-js-sdk` como SDK. A interface será própria; copiar Element Web ou Telegram Web não faz parte da arquitetura aprovada. Consulte `OPEN_SOURCE.md`.
