from __future__ import annotations

import os
from pathlib import Path


PLATFORM_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = PLATFORM_DIR / "synapse" / "homeserver.yaml.template"
LOG_CONFIG_PATH = PLATFORM_DIR / "synapse" / "log.config"
RUNTIME_DIR = PLATFORM_DIR / "runtime"

REQUIRED_ENV = (
    "MATRIX_SERVER_NAME",
    "MATRIX_PUBLIC_BASEURL",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "REGISTRATION_SHARED_SECRET",
    "MACAROON_SECRET_KEY",
    "FORM_SECRET",
)


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            "Variáveis obrigatórias ausentes: " + ", ".join(sorted(missing))
        )

    rendered = TEMPLATE_PATH.read_text(encoding="utf-8")
    for name in REQUIRED_ENV:
        value = os.environ[name]
        if "\n" in value or "\r" in value:
            raise SystemExit(f"{name} não pode conter quebra de linha")
        rendered = rendered.replace(f"__{name}__", value.replace('"', '\\"'))

    RUNTIME_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    (RUNTIME_DIR / "homeserver.yaml").write_text(rendered, encoding="utf-8")
    (RUNTIME_DIR / "log.config").write_text(
        LOG_CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    print(f"Configuração gerada em {RUNTIME_DIR}")


if __name__ == "__main__":
    main()
