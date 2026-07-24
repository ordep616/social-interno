# Plataforma Matrix

Área exclusiva do Colaborador 1 para Synapse, PostgreSQL, identidade, infraestrutura, segurança e operação.

## Fundação implementada

- Synapse `1.156.0` em imagem oficial.
- PostgreSQL `17.6-alpine`.
- PostgreSQL isolado na rede Docker interna, sem porta publicada.
- Synapse conectado à rede interna e a uma rede de borda, com a API Matrix
  publicada somente em `127.0.0.1`.
- POC local de chamadas MatrixRTC com LiveKit, `lk-jwt-service` e coturn,
  publicada somente em `127.0.0.1`.
- Cadastro público desabilitado.
- Listener configurado para API de cliente e OpenID necessário ao
  `lk-jwt-service`, sem recurso de federação.
- Federação limitada por lista vazia.
- Diretório público e pré-visualização de URLs desabilitados.
- Configuração gerada localmente a partir de variáveis, sem versionar segredos.

Este ambiente é uma prova de conceito local. Não possui TLS, OIDC, backup,
monitoramento ou endurecimento de produção. A POC de chamadas não altera o MVP
e não deve ser exposta na internet sem domínio, HTTPS, TURN público,
observabilidade, limites e revisão de licenças.

## Pré-requisitos

- Docker com Compose.
- Python 3 para renderizar a configuração local.

## Início local

```bash
cd platform
cp .env.example .env
```

Troque todos os valores iniciados por `change-me`. Depois:

```bash
make config
make up
make ps
```

O endpoint ficará disponível em:

```text
http://localhost:8008/_matrix/client/versions
```

Com a POC de chamadas, também ficam disponíveis localmente:

```text
http://localhost:8008/.well-known/matrix/client
http://localhost:8085/healthz
ws://host.docker.internal:7880
turn:localhost:3478
```

No navegador local, o fork do Cinny lê o `.well-known` do Synapse e só mostra
os controles de chamada quando `org.matrix.msc4143.rtc_foci` está anunciado.

## Comandos

```bash
make init     # gera as configurações em runtime/ e copia o log.config
make keys     # gera a chave de assinatura do homeserver com a imagem oficial
make config   # valida o Compose
make up       # gera a configuração e inicia os serviços
make logs     # acompanha os serviços principais
make ps       # mostra a saúde dos serviços
make down     # encerra os serviços sem apagar os volumes
```

## Chamadas MatrixRTC — POC local

A POC usa:

- Synapse como fonte de salas, membros, sinalização MatrixRTC e OpenID.
- Element Call incorporado ao fork do Cinny.
- LiveKit como SFU local.
- `lk-jwt-service` para trocar identidade Matrix por JWT LiveKit.
- coturn para anunciar TURN local aos clientes Matrix.

Valores de desenvolvimento ficam em `.env.example`. Os padrões gerados pelo
script são apenas placeholders locais; troque qualquer valor `change-me` antes
de compartilhar o ambiente.

Limites conhecidos:

- a publicação está presa a `127.0.0.1`;
- `host.docker.internal` é voltado ao Docker Desktop local;
- teste em celular ou redes diferentes exige IP/domínio alcançável, HTTPS e
  regras de firewall;
- chamadas em grupo continuam fora do escopo até validação de capacidade e
  segurança.

## Dados locais

- PostgreSQL: volume Docker `postgres-data`.
- Configuração gerada, chaves e mídia: `platform/runtime/`, ignorado pelo Git.

Não apague o volume e `runtime/` de um ambiente importante sem backup conjunto. O `server_name` define os identificadores Matrix e não deve ser alterado depois da implantação definitiva.

## Usuários de teste

O cadastro público permanece desabilitado. A criação administrativa de usuários deverá usar a ferramenta oficial `register_new_matrix_user` dentro do contêiner, com o segredo local de registro. O procedimento será validado na próxima etapa da prova de conceito.

## Pendências antes de produção

- domínio definitivo;
- proxy reverso e TLS;
- provedor OIDC;
- política final de federação;
- política de criptografia ponta a ponta;
- retenção e antimalware;
- backup e restauração testados;
- métricas e alertas;
- revisão jurídica da licença do Synapse.

## Regra de independência

A plataforma deve ser testável com um cliente Matrix genérico, sem depender do frontend próprio. O Colaborador 2 não deve modificar esta pasta, e o Colaborador 1 não deve alterar `frontend/` para resolver problemas de configuração do Synapse.
