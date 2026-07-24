# POC create-only do registro administrativo

Esta ferramenta executa a prova aprovada em `DEC-022` e `DEC-023` sem tocar no
homeserver persistente em `platform/compose.yaml`.

## Isolamento

- usa Synapse `1.156.0` e PostgreSQL `17.6-alpine`;
- cria nome de projeto Docker, rede, volume e diretório temporário exclusivos;
- publica o Synapse somente em uma porta aleatória de `127.0.0.1`;
- mantém o PostgreSQL sem porta publicada;
- usa segredo de registro temporário por arquivo montado como Docker secret;
- remove contêineres, redes, volume e diretório temporário mesmo quando falha;
- não lê `platform/.env`, `platform/runtime/` ou credenciais do backend.

As imagens permanecem no cache local do Docker, mas não contêm contas ou dados
da execução.

## Cenários validados

1. Registro administrativo retorna `200 OK`.
2. A conta-alvo é criada com `admin: false`.
3. `user_id`, domínio e `device_id` coincidem exatamente com o autorizado.
4. `whoami` confirma a sessão antes da revogação.
5. A API administrativa remove o dispositivo.
6. O dispositivo passa a responder `404` e o token passa a responder `401`.
7. Nova tentativa para a mesma identidade retorna `M_USER_IN_USE`.
8. Propriedades, dispositivos e senha original da conta existente não mudam.
9. Senha alternativa é recusada e a original permanece válida.
10. Logs não contêm senha, segredos, MAC, nonce ou tokens conhecidos.

Uma conta administrativa temporária é criada somente para operar a API
administrativa dentro da stack descartável. Seu token é encerrado por
`/logout` e confirmado como inválido antes da destruição integral do ambiente.
A conta-alvo é sempre não administrativa.

## Execução

Pré-requisitos:

- Docker Desktop em execução;
- Docker Compose;
- Python 3.11 ou mais recente.

Testes locais, sem Docker:

```bash
cd platform/poc
python3 -m unittest -v test_create_only_registration.py
```

Prova integrada:

```bash
cd platform/poc
python3 create_only_registration.py
```

O resultado é um JSON sanitizado. A ferramenta não aceita endereço externo,
senha, segredo ou token por argumento.

## Resultado validado

Em 2026-07-24, a execução com Synapse `1.156.0` e PostgreSQL `17.6-alpine`
terminou com `status: passed`. Todos os dez cenários funcionais passaram, a
inspeção não encontrou os valores sensíveis conhecidos nos logs e a verificação
posterior encontrou somente o projeto persistente `social-interno`, sem
contêiner ou volume remanescente da POC.

## Reversão

A reversão normal é automática. Se o processo for encerrado abruptamente,
identifique somente projetos com o prefixo exclusivo da prova:

```bash
docker ps -a --filter label=com.docker.compose.project --format '{{.Label "com.docker.compose.project"}}'
docker volume ls --filter label=com.docker.compose.project
```

Remova apenas o projeto exato iniciado pela prova; nunca use o nome
`social-interno` do ambiente persistente.
