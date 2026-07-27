from __future__ import annotations

import argparse
import http.client
import json
import ssl
from urllib.parse import urlsplit

REQUIRED_HEADERS = {
    "cache-control",
    "content-security-policy",
    "permissions-policy",
    "referrer-policy",
    "x-content-type-options",
    "x-frame-options",
    "x-robots-tag",
}


def request(
    connection: http.client.HTTPConnection,
    method: str,
    path: str,
    body: str | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str]]:
    connection.request(method, path, body=body, headers=headers or {})
    response = connection.getresponse()
    response.read()
    return response.status, {
        name.lower(): value for name, value in response.getheaders()
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida os controles locais da borda Traefik.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8082",
        help="Origem local da borda, sem caminho.",
    )
    parser.add_argument(
        "--ca-file",
        help="CA PEM usada para validar uma origem HTTPS interna.",
    )
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.path not in {"", "/"}
    ):
        raise SystemExit("--base-url deve ser uma origem HTTP(S) sem caminho")
    if parsed.scheme == "https":
        if not args.ca_file:
            raise SystemExit("--ca-file é obrigatório para HTTPS")
        context = ssl.create_default_context(cafile=args.ca_file)
        connection: http.client.HTTPConnection = http.client.HTTPSConnection(
            parsed.hostname,
            parsed.port or 443,
            timeout=5,
            context=context,
        )
    else:
        if args.ca_file:
            raise SystemExit("--ca-file só pode ser usado com HTTPS")
        connection = http.client.HTTPConnection(
            parsed.hostname,
            parsed.port or 80,
            timeout=5,
        )
    status, headers = request(connection, "GET", "/health")
    if status != 200:
        raise SystemExit(f"/health retornou {status}, esperado 200")
    missing_headers = REQUIRED_HEADERS - headers.keys()
    if missing_headers:
        raise SystemExit(
            "Cabeçalhos ausentes: " + ", ".join(sorted(missing_headers))
        )

    oversized = json.dumps({"invitation_token": "x" * 1100})
    status, _ = request(
        connection,
        "POST",
        "/v1/activation-validations",
        oversized,
        {"Content-Type": "application/json"},
    )
    if status != 413:
        raise SystemExit(f"corpo acima de 1 KiB retornou {status}, esperado 413")

    payload = json.dumps({})
    statuses = [
        request(
            connection,
            "POST",
            "/v1/activation-validations",
            payload,
            {"Content-Type": "application/json"},
        )[0]
        for _ in range(101)
    ]
    if 429 not in statuses:
        raise SystemExit("a borda não limitou a rajada de 101 requisições")

    status, _ = request(
        connection,
        "POST",
        "/v1/activation-validations",
        payload,
        {
            "Content-Type": "application/json",
            "X-Forwarded-For": "198.51.100.77",
        },
    )
    if status != 429:
        raise SystemExit("X-Forwarded-For forjado contornou o limite por origem")

    print("Borda local validada: headers, 1 KiB, rate limit e origem confiável.")


if __name__ == "__main__":
    main()
