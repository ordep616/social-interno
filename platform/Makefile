PYTHON ?= python3
COMPOSE ?= docker compose

.PHONY: init keys up down logs ps config

init:
	@set -a; . ./.env; set +a; $(PYTHON) scripts/render_config.py

config:
	$(COMPOSE) --env-file .env -f compose.yaml config

keys:
	$(COMPOSE) --env-file .env -f compose.yaml run --rm --no-deps synapse run --generate-keys

up: init keys
	$(COMPOSE) --env-file .env -f compose.yaml up -d

down:
	$(COMPOSE) --env-file .env -f compose.yaml down

logs:
	$(COMPOSE) --env-file .env -f compose.yaml logs -f synapse postgres livekit lk-jwt-service coturn

ps:
	$(COMPOSE) --env-file .env -f compose.yaml ps
