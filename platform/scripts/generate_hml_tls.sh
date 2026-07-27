#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
tls_root="$project_dir/platform/runtime/tls"
ca_dir="$tls_root/ca"
certificate_dir="$tls_root/matrix-hml.expbetweenus"

if ! command -v mkcert >/dev/null 2>&1; then
  echo "mkcert não encontrado. Instale mkcert v1.4.4 antes de continuar." >&2
  exit 1
fi

if [ "$(mkcert -version)" != "v1.4.4" ]; then
  echo "A homologação foi validada para mkcert v1.4.4." >&2
  echo "Versão encontrada: $(mkcert -version)" >&2
  exit 1
fi

mkdir -p "$ca_dir" "$certificate_dir"
chmod 700 "$tls_root" "$ca_dir" "$certificate_dir"

CAROOT="$ca_dir" mkcert \
  -cert-file "$certificate_dir/tls-cert.pem" \
  -key-file "$certificate_dir/tls-key.pem" \
  matrix-hml.expbetweenus

chmod 644 "$certificate_dir/tls-cert.pem" "$ca_dir/rootCA.pem"
chmod 600 "$certificate_dir/tls-key.pem" "$ca_dir/rootCA-key.pem"

echo "Certificado: $certificate_dir/tls-cert.pem"
echo "CA pública para dispositivos de teste: $ca_dir/rootCA.pem"
echo "Nunca copie nem compartilhe: $ca_dir/rootCA-key.pem"
echo "A CA ainda precisa ser instalada explicitamente no dispositivo de teste."
