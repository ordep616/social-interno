from __future__ import annotations

import os
from pathlib import Path


PLATFORM_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = PLATFORM_DIR / "synapse" / "homeserver.yaml.template"
LOG_CONFIG_PATH = PLATFORM_DIR / "synapse" / "log.config"
LIVEKIT_TEMPLATE_PATH = PLATFORM_DIR / "livekit" / "livekit.yaml.template"
COTURN_TEMPLATE_PATH = PLATFORM_DIR / "coturn" / "turnserver.conf.template"
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

MATRIX_RTC_DEFAULTS = {
    "MATRIX_RTC_LIVEKIT_SERVICE_URL": "http://localhost:8085",
    "LIVEKIT_KEY": "devkey",
    "LIVEKIT_SECRET": "change-me-local-livekit-secret",
    "LIVEKIT_NODE_IP": "127.0.0.1",
    "LIVEKIT_RTC_TCP_PORT": "7881",
    "LIVEKIT_RTC_UDP_PORT": "7882",
    "LIVEKIT_JWT_INTERNAL_WEBHOOK_URL": "http://lk-jwt-service:8080/sfu_webhook",
    "TURN_PUBLIC_HOST": "localhost",
    "TURN_PORT": "3478",
    "TURN_SHARED_SECRET": "change-me-local-turn-secret",
    "TURN_REALM": "localhost",
}

TEMPLATE_ENV = REQUIRED_ENV + tuple(MATRIX_RTC_DEFAULTS)


def env_value(name: str) -> str:
    return os.environ.get(name) or MATRIX_RTC_DEFAULTS[name]


def render_template(path: Path, names: tuple[str, ...]) -> str:
    rendered = path.read_text(encoding="utf-8")
    for name in names:
        value = env_value(name)
        if "\n" in value or "\r" in value:
            raise SystemExit(f"{name} não pode conter quebra de linha")
        rendered = rendered.replace(f"__{name}__", value.replace('"', '\\"'))
    return rendered


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            "Variáveis obrigatórias ausentes: " + ", ".join(sorted(missing))
        )

    RUNTIME_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    (RUNTIME_DIR / "homeserver.yaml").write_text(
        render_template(TEMPLATE_PATH, TEMPLATE_ENV), encoding="utf-8"
    )
    (RUNTIME_DIR / "livekit.yaml").write_text(
        render_template(LIVEKIT_TEMPLATE_PATH, TEMPLATE_ENV), encoding="utf-8"
    )
    (RUNTIME_DIR / "turnserver.conf").write_text(
        render_template(COTURN_TEMPLATE_PATH, TEMPLATE_ENV), encoding="utf-8"
    )
    (RUNTIME_DIR / "log.config").write_text(
        LOG_CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    print(f"Configuração gerada em {RUNTIME_DIR}")


if __name__ == "__main__":
    main()
