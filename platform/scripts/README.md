# Scripts operacionais

`render_config.py` gera a configuração local do Synapse e dos serviços
MatrixRTC a partir das variáveis aprovadas.

`test_edge_security.py` valida a borda Traefik já iniciada e um FastAPI
escutando atrás dela:

```bash
python3 platform/scripts/test_edge_security.py
```

O teste verifica cabeçalhos, recusa de corpo acima de 1 KiB, limitação de uma
rajada de 101 requisições e impossibilidade de contornar o limite com
`X-Forwarded-For` forjado. Reinicie o Traefik antes de repetir se quiser uma
janela de limite limpa.

Para gerar e testar o perfil HTTPS interno:

```bash
platform/scripts/generate_hml_tls.sh
CAROOT="$PWD/platform/runtime/tls/ca" mkcert -install
python3 platform/scripts/test_edge_security.py \
  --base-url https://matrix-hml.expbetweenus:8443 \
  --ca-file platform/runtime/tls/ca/rootCA.pem
```

O gerador exige `mkcert v1.4.4`, usa uma CA exclusiva em `runtime/` e não
versiona certificados ou chaves. A instalação da CA é separada porque pode
exigir a senha de administrador do dispositivo.
