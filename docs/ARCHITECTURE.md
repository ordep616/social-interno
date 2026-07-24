# Arquitetura pretendida

## Visão geral

O produto será uma adaptação de uma plataforma Matrix auto-hospedada. A equipe não implementará um protocolo de mensagens nem um servidor de chat próprio.

```text
Navegador / PWA
  ├── Fork corporativo do Cinny
  ├── Identidade visual e restrições corporativas
  ├── Ativação anterior ao login e painel por capacidade
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
  ├── identidades pré-autorizadas, papéis e auditoria
  ├── ativação create-only no Synapse
  └── PostgreSQL próprio
```

A camada de ativação acima foi aprovada pelos dois colaboradores em `DEC-022`.
Ela ainda depende das implementações autorizadas separadamente e não altera o
cadastro público desabilitado do Synapse.

## Tecnologias adotadas ou candidatas

- Protocolo: Matrix Client-Server API.
- Homeserver inicial: Synapse, sujeito à prova de conceito e revisão de licença.
- Frontend: fork do Cinny `v4.12.3`, baseado em React, Vite e `matrix-js-sdk`.
- SDK do frontend: versão utilizada e fixada pelo Cinny; atualizações exigem teste conjunto.
- Banco do Synapse: PostgreSQL.
- Identidade inicial: `DEC-022` exige que `platform_admin` defina
  previamente a conta local e que o funcionário escolha somente sua senha por
  link de uso único; OIDC poderá ser avaliado posteriormente. O mecanismo
  inicial por segredo compartilhado não é compatível com uma integração ao
  Matrix Authentication Service (MAS), que exigirá nova decisão conjunta de
  provisionamento.
- Ambiente: contêineres durante desenvolvimento e homologação.
- Serviço complementar: API REST FastAPI aprovada para convites, provisionamento e ciclo de vida de contas; novos usos exigem outra decisão.
- Fundação do serviço: CPython `>=3.14,<3.15`, FastAPI síncrono, Uvicorn, SQLAlchemy `2.0.x`, Psycopg 3, Alembic, `pydantic-settings` e HTTPX.
- Dependências e qualidade: `uv` com `uv.lock`, Ruff, mypy, pytest e pytest-cov.

## Limites

### Frontend — Colaborador 2

- Mantém o fork do Cinny, sua interface, experiência e integração Matrix no navegador.
- Não acessa PostgreSQL, armazenamento ou APIs administrativas diretamente.
- Não importa código, tipos ou clientes do Telegram.
- Evita alterações profundas na camada Matrix original do Cinny e mantém personalizações corporativas isoladas sempre que possível.
- Recebe URL do homeserver e opções públicas por configuração, nunca segredos administrativos.
- Mantém o painel administrativo fechado por padrão e consulta capacidades no
  backend antes de mostrá-lo.
- Implementa ativação como página corporativa anterior ao login, sem reutilizar
  o cadastro nativo Matrix ou seu `PasswordRegisterForm`.

### Backend, plataforma e infraestrutura — Colaborador 1

- O Synapse é a fonte de verdade para contas Matrix, salas, participantes, mensagens, mídia e sincronização.
- O acesso público, o registro livre e a federação externa permanecem desabilitados, salvo decisão conjunta posterior.
- Conforme `DEC-022`, o serviço de convites controlará uma identidade
  previamente definida e o Synapse autenticará a conta depois da ativação.
- A administração deve usar APIs e módulos suportados, evitando alterações diretas no banco do Synapse.
- FastAPI não duplicará mensagens, salas, presença ou sincronização.
- O serviço FastAPI usa PostgreSQL próprio e mantém credenciais administrativas fora do navegador.
- A API própria segue REST versionado; operações de chat continuam usando diretamente o contrato Matrix.
- O ambiente e o banco do serviço são independentes dos processos e do banco lógico do Synapse.
- Somente `platform_admin` poderá criar ativações; `group_admin` continuará sem
  administração de usuários.
- Nenhuma conta existente será atualizada, reativada ou terá senha redefinida
  pelo fluxo de ativação.
- Qualquer sessão criada incidentalmente pelo mecanismo de provisionamento será
  revogada antes de concluir a ativação; falha ou ambiguidade bloqueará o
  convite para reconciliação.
- Antes da revogação, o backend comparará exatamente o `user_id` retornado com
  o `target_user_id`, validará o domínio configurado e confirmará por `whoami`
  que o token pertence ao `device_id` esperado. Depois da exclusão, confirmará
  a ausência do dispositivo e a recusa do token.
- Conforme o refinamento aceito em `DEC-023`, a confirmação será persistida
  em `provisioning_session_revoked_at`; a unidade de trabalho não finalizará a
  ativação confiando somente na ordem das chamadas externas.
- Uma reconciliação bem-sucedida retornará atomicamente a tentativa para
  `synapse_created`, limpará a falha e registrará a revogação antes de liberar
  a finalização.

### Dados

- PostgreSQL guarda o estado persistente do homeserver.
- O armazenamento de mídia segue a configuração suportada pelo Synapse.
- Identificador e instante de revogação da sessão de provisionamento são dados
  operacionais internos e não pertencem às respostas públicas.
- Loggers do Synapse capazes de expor dados de registro ou autenticação não
  operarão em `DEBUG` durante a prova de conceito; senha, segredo, MAC, nonce,
  tokens e corpos sensíveis não pertencerão a logs ou relatórios.
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
| Criação de conta | Identidade pré-autorizada pelo FastAPI e mecanismo create-only do Synapse, conforme `DEC-022` |
| Login | Autenticação local do Synapse; OIDC é evolução possível |
| Administração | FastAPI, APIs administrativas e políticas do Synapse |

## Segurança

- HTTPS obrigatório fora do computador local.
- Cadastro público desabilitado.
- Identidade e papel definidos previamente por `platform_admin`; o funcionário
  informa somente a própria senha.
- Federação desabilitada por padrão e validada em teste.
- Ativação administrativa de identidade previamente definida e encerramento de
  acesso após desligamento.
- Segredos fora do frontend e do repositório.
- Token de ativação no fragmento, removido da URL e mantido somente em memória.
- Autorização administrativa sempre revalidada no backend, independentemente
  da visibilidade do botão.
- Limites de requisição e upload configurados.
- Política explícita para criptografia ponta a ponta, recuperação e auditoria.
- Backups testados e criptografados.
- Atualizações de segurança do homeserver acompanhadas continuamente.

## Estratégia de código aberto

O projeto adotará Matrix/Synapse como plataforma e o Cinny como base do cliente web. Element Web e Telegram Web não fazem parte da implementação aprovada. Consulte `OPEN_SOURCE.md`.
