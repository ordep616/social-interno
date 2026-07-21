# Arquitetura pretendida

## Visão geral

O produto será uma adaptação de uma plataforma Matrix auto-hospedada. A equipe não implementará um protocolo de mensagens nem um servidor de chat próprio.

```text
Navegador / PWA
  ├── Fork corporativo do Cinny
  ├── Identidade visual e restrições corporativas
  ├── Estado e cache da aplicação
  └── Integração Matrix mantida pelo cliente
                    │
                    ▼
          Homeserver Matrix (Synapse)
          ├── contas, salas e mensagens
          ├── sincronização e tempo real
          ├── anexos e confirmações
          ├── autorização e administração
          └── autenticação e administração Matrix
                    │
             ┌──────┴──────┐
             ▼             ▼
        PostgreSQL   mídia/armazenamento

Serviço de convites (FastAPI)
  ├── convites, papéis e auditoria
  ├── API administrativa do Synapse
  └── PostgreSQL próprio
```

## Tecnologias adotadas ou candidatas

- Protocolo: Matrix Client-Server API.
- Homeserver inicial: Synapse, sujeito à prova de conceito e revisão de licença.
- Frontend: fork do Cinny `v4.12.3`, baseado em React, Vite e `matrix-js-sdk`.
- SDK do frontend: versão utilizada e fixada pelo Cinny; atualizações exigem teste conjunto.
- Banco do Synapse: PostgreSQL.
- Identidade inicial: conta local criada por convite administrativo de uso único; OIDC poderá ser avaliado posteriormente.
- Ambiente: contêineres durante desenvolvimento e homologação.
- Serviço complementar: FastAPI aprovado para convites, provisionamento e ciclo de vida de contas; novos usos exigem outra decisão.

## Limites

### Frontend — Colaborador 2

- Mantém o fork do Cinny, sua interface, experiência e integração Matrix no navegador.
- Não acessa PostgreSQL, armazenamento ou APIs administrativas diretamente.
- Não importa código, tipos ou clientes do Telegram.
- Evita alterações profundas na camada Matrix original do Cinny e mantém personalizações corporativas isoladas sempre que possível.
- Recebe URL do homeserver e opções públicas por configuração, nunca segredos administrativos.

### Backend, plataforma e infraestrutura — Colaborador 1

- O Synapse é a fonte de verdade para contas Matrix, salas, participantes, mensagens, mídia e sincronização.
- O acesso público, o registro livre e a federação externa permanecem desabilitados, salvo decisão conjunta posterior.
- O serviço de convites controla a criação inicial; o Synapse autentica as contas e controla o acesso à plataforma.
- A administração deve usar APIs e módulos suportados, evitando alterações diretas no banco do Synapse.
- FastAPI não duplicará mensagens, salas, presença ou sincronização.
- O serviço FastAPI usa PostgreSQL próprio e mantém credenciais administrativas fora do navegador.

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
       ├─ fork do Cinny         ├─ Synapse de homologação
       ├─ cliente de teste      ├─ PostgreSQL e mídia
       ├─ estados simulados     ├─ convites e políticas
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
frontend/       Colaborador 2: fork do Cinny, personalização e testes visuais
platform/       Colaborador 1: configuração do Synapse, contêineres e operação
backend/        Colaborador 1: convites e integrações FastAPI aprovadas; não é o servidor de chat
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
| Criação de conta | Convite FastAPI e API administrativa do Synapse |
| Login | Autenticação local do Synapse; OIDC é evolução possível |
| Administração | FastAPI, APIs administrativas e políticas do Synapse |

## Segurança

- HTTPS obrigatório fora do computador local.
- Cadastro público desabilitado.
- Federação desabilitada por padrão e validada em teste.
- Cadastro por convite administrativo e encerramento de acesso após desligamento.
- Segredos fora do frontend e do repositório.
- Limites de requisição e upload configurados.
- Política explícita para criptografia ponta a ponta, recuperação e auditoria.
- Backups testados e criptografados.
- Atualizações de segurança do homeserver acompanhadas continuamente.

## Estratégia de código aberto

O projeto adotará Matrix/Synapse como plataforma e o Cinny como base do cliente web. Element Web e Telegram Web não fazem parte da implementação aprovada. Consulte `OPEN_SOURCE.md`.
