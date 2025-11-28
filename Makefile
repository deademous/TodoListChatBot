VENV_DIR = .venv
ACTIVATE_VENV := . $(VENV_DIR)/bin/activate

$(VENV_DIR):
	python3 -m venv $(VENV_DIR)
	$(ACTIVATE_VENV) && pip install --upgrade pip
	$(ACTIVATE_VENV) && pip install --requirements.txt

install: $(VENV_DIR)

black: $(VENV_DIR)
	$(ACTIVATE_VENV) && black .

ruff: $(VENV_DIR)
	$(ACTIVATE_VENV) && ruff check .

pytest: $(VENV_DIR)
	$(ACTIVATE_VENV) && PYTHONPATH=. pytest

test: black ruff pytest


DOCKER_NETWORK=todolist_bot_network

POSTGRES_VOLUME=postgres_data
POSTGRES_CONTAINER=postgres_17

BOT_CONTAINER=todolist_bot
BOT_IMAGE=nilopod/tg_todolist_bot

include .env
export $(shell sed 's/=.*//' .env)

docker_volume:
	docker volume create $(POSTGRES_VOLUME) || true

docker_net:
	docker network create $(DOCKER_NETWORK) || true

postgres_run: docker_volume docker_net
	docker run -d \
	  --name $(POSTGRES_CONTAINER) \
	  -e POSTGRES_USER="$(POSTGRES_USER)" \
	  -e POSTGRES_PASSWORD="$(POSTGRES_PASSWORD)" \
	  -e POSTGRES_DB="$(POSTGRES_DATABASE)" \
	  -p "$(POSTGRES_HOST_PORT):$(POSTGRES_CONTAINER_PORT)" \
	  -v $(POSTGRES_VOLUME):/var/lib/postgresql/data \
	  --health-cmd="pg_isready -U $(POSTGRES_USER)" \
	  --health-interval=10s \
	  --health-timeout=5s \
	  --health-retries=5 \
	  --network $(DOCKER_NETWORK) \
	  postgres:17


postgres_stop:
	docker stop $(POSTGRES_CONTAINER)
	docker rm $(POSTGRES_CONTAINER)

build:
	docker build \
	-t $(BOT_IMAGE) \
	--platform linux/amd64 \
	-f Dockerfile \
	.

push:
	docker push $(BOT_IMAGE)


run: docker_volume
	docker run -d \
	  --name $(BOT_CONTAINER) \
	  --restart unless-stopped \
	  -e POSTGRES_HOST="$(POSTGRES_CONTAINER)" \
	  -e POSTGRES_HOST_PORT="5432" \
	  -e POSTGRES_USER="$(POSTGRES_USER)" \
	  -e POSTGRES_PASSWORD="$(POSTGRES_PASSWORD)" \
	  -e POSTGRES_DATABASE="$(POSTGRES_DATABASE)" \
	  -e TELEGRAM_TOKEN="$(TELEGRAM_TOKEN)" \
	  -e TELEGRAM_BASE_URI="$(TELEGRAM_BASE_URI)" \
	  --network $(DOCKER_NETWORK) \
	  $(BOT_IMAGE)

stop:
	docker stop $(BOT_CONTAINER)
	docker rm $(BOT_CONTAINER)