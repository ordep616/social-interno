# Plataforma Matrix

Área exclusiva do Colaborador 1 para Synapse, PostgreSQL, identidade, infraestrutura, segurança e operação.

## Fundação implementada

- Synapse `1.156.0` em imagem oficial.
- PostgreSQL `17.6-alpine`.
- PostgreSQL isolado na rede Docker interna, sem porta publicada.
- Synapse conectado à rede interna e a uma rede de borda, com a API Matrix
  publicada somente em `127.0.0.1`.
- Cadastro público desabilitado.
- Listener configurado apenas para a API de cliente, sem recurso de federação.
- Federação limitada por lista vazia.
- Diretório público e pré-visualização de URLs desabilitados.
- Configuração gerada localmente a partir de variáveis, sem versionar segredos.

Este ambiente é uma prova de conceito local. Não possui TLS, OIDC, backup, monitoramento ou endurecimento de produção.

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

## Comandos

```bash
make init     # gera runtime/homeserver.yaml e copia o log.config
make keys     # gera a chave de assinatura do homeserver com a imagem oficial
make config   # valida o Compose
make up       # gera a configuração e inicia os serviços
make logs     # acompanha Synapse e PostgreSQL
make ps       # mostra a saúde dos serviços
make down     # encerra os serviços sem apagar os volumes
```

## Dados locais

- PostgreSQL: volume Docker `postgres-data`.
- Configuração gerada, chaves e mídia: `platform/runtime/`, ignorado pelo Git.

Não apague o volume e `runtime/` de um ambiente importante sem backup conjunto. O `server_name` define os identificadores Matrix e não deve ser alterado depois da implantação definitiva.

## Usuários de teste

O cadastro público permanece desabilitado. Usuários do ambiente persistente
continuam sendo administrados separadamente e não são usados na prova
create-only.

## Prova create-only descartável

A prova do registro por segredo compartilhado foi executada com sucesso em
2026-07-24 contra Synapse `1.156.0` e PostgreSQL `17.6-alpine`. Ela confirmou:

- resposta `200 OK` e identidade exata;
- conta-alvo não administrativa;
- sessão confirmada por `whoami`;
- dispositivo ausente por `404` e token recusado por `401` após a revogação;
- conflito `M_USER_IN_USE` sem mudar propriedades, dispositivos ou senha da
  conta existente;
- ausência dos valores sensíveis conhecidos nos logs;
- remoção de contêineres, redes, volume e diretório temporário.

O procedimento e o executor estão em `poc/`. Ele não lê `.env`, `runtime/` ou
credenciais do ambiente persistente:

```bash
cd platform/poc
python3 -m unittest -v test_create_only_registration.py
python3 create_only_registration.py
```

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
