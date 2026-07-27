# Proxy e TLS

Traefik `v3.7.1` é a borda local aprovada em `DEC-025`. A configuração usa
somente o file provider: o socket Docker não é montado e o único upstream é o
FastAPI local em `host.docker.internal:8081`.

## Controles locais

- porta publicada somente em `127.0.0.1:8082`;
- 100 requisições por origem a cada período de 15 minutos nas duas rotas
  públicas de ativação, com burst inicial máximo de 100;
- corpo máximo de 1 KiB antes do FastAPI;
- `Cache-Control: no-store`, CSP restritiva, `Referrer-Policy: no-referrer`,
  bloqueio de frames, `nosniff`, política de permissões e `X-Robots-Tag`;
- cabeçalhos encaminhados aceitos somente dos CIDRs explicitamente confiáveis;
- dashboard, telemetria, verificação automática de versão e access log
  desabilitados.

Essa configuração é de desenvolvimento. TLS, domínio, proxy anterior,
endereços confiáveis e parâmetros finais precisam de nova validação antes de
homologação ou publicação.

## Homologação interna descartável

O perfil `homologation` atende somente a `matrix-hml.expbetweenus`. Ele não
altera `MATRIX_SERVER_NAME`, o `server_name` do Synapse nem convenções
compartilhadas. Não use esse nome como domínio Matrix definitivo.

### Gerar a CA e o certificado

O projeto exige `mkcert v1.4.4`. No macOS:

```bash
brew install mkcert
brew install nss  # somente se os testes usarem Firefox
platform/scripts/generate_hml_tls.sh
CAROOT="$PWD/platform/runtime/tls/ca" mkcert -install
```

O último comando pode solicitar a senha de administrador do macOS. O script
cria uma CA exclusiva em `platform/runtime/tls/`; a instalação no repositório
de confiança é uma ação explícita e separada. Certificados e chaves permanecem
fora do Git.
Nunca copie ou compartilhe `rootCA-key.pem`. Para dispositivos de teste,
distribua somente `rootCA.pem` por um canal interno controlado.

### Resolver o nome e escolher o bind

Na máquina do Traefik, acrescente a `/etc/hosts`:

```text
127.0.0.1 matrix-hml.expbetweenus
```

Em outro dispositivo da rede interna/VPN, substitua pelo IP privado real do
servidor. O bind padrão em `platform/.env` continua restrito à máquina local:

```dotenv
TRAEFIK_HML_BIND_ADDRESS=127.0.0.1
TRAEFIK_HML_HTTPS_PORT=8443
```

Para acesso remoto, use um IP privado específico da interface interna ou VPN.
Não use `0.0.0.0` sem revisar antes as regras de firewall.

### Iniciar e validar

Inicie primeiro o FastAPI em `127.0.0.1:8081`. Depois:

```bash
docker compose --env-file platform/.env \
  -f platform/compose.yaml --profile homologation up -d traefik-hml

python3 platform/scripts/test_edge_security.py \
  --base-url https://matrix-hml.expbetweenus:8443 \
  --ca-file platform/runtime/tls/ca/rootCA.pem
```

Somente o Traefik recebe HTTPS. Synapse continua sem publicação direta na
internet, e o upstream permanece o FastAPI local.

### Instalar e remover a CA nos dispositivos

Copie somente `platform/runtime/tls/ca/rootCA.pem`:

- macOS: importe no Acesso às Chaves do usuário de teste e habilite confiança
  para SSL;
- Windows: importe em **Autoridades de Certificação Raiz Confiáveis** do
  usuário de teste;
- iOS/iPadOS: instale o perfil e habilite a confiança total da CA;
- Android: instale como certificado CA do usuário; aplicativos podem exigir
  configuração própria para aceitar CAs de usuário;
- Firefox: importe em autoridades ou instale `nss` antes de
  `mkcert -install`.

Use apenas dispositivos controlados de teste. Para encerrar:

```bash
docker compose --env-file platform/.env \
  -f platform/compose.yaml --profile homologation stop traefik-hml

CAROOT="$PWD/platform/runtime/tls/ca" mkcert -uninstall
```

Remova também a CA dos repositórios de confiança de cada dispositivo. Depois
de confirmar que nenhum teste depende dela, descarte
`platform/runtime/tls/`. Isso não altera o repositório.

## Execução

O FastAPI deve escutar em `127.0.0.1:8081`. Depois:

```bash
docker compose --env-file platform/.env -f platform/compose.yaml up -d traefik
curl -i http://127.0.0.1:8082/health
```

Valide os controles da borda com o FastAPI ativo:

```bash
python3 platform/scripts/test_edge_security.py
```

O teste envia 101 requisições para comprovar o limite. Reinicie o Traefik antes
de repeti-lo para limpar o estado local do limitador em memória.

O `503` indica que a borda está ativa, mas o FastAPI não está acessível. Pare
somente o proxy com:

```bash
docker compose --env-file platform/.env -f platform/compose.yaml stop traefik
```
