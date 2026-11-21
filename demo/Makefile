.PHONY: setup up down test demo

PROJECT ?= ../examples/vehicle
COMPOSE ?= $(shell command -v podman >/dev/null && echo podman compose || echo docker compose)
export NEO4J_URI ?= bolt://localhost:7687
PROBE = import os; from neo4j import GraphDatabase; GraphDatabase.driver(os.environ['NEO4J_URI'], auth=None if os.environ.get('NEO4J_AUTH') == 'none' else (os.environ.get('NEO4J_USER', 'neo4j'), os.environ['NEO4J_PASSWORD'])).verify_connectivity()

setup:
	uv sync
	uv run python -c "from explorer.search import Embedder; Embedder()"

up:
	podman compose up -d

down:
	podman compose down

test:
	uv run python -m unittest discover -s tests

# start Neo4j, build the project, load it, serve on http://127.0.0.1:8000
demo:
	@test -n "$$NEO4J_PASSWORD" -o "$$NEO4J_AUTH" = none || { echo "set NEO4J_PASSWORD, the password Neo4j is created with"; exit 1; }
	$(COMPOSE) up -d
	@for i in $$(seq 30); do uv run python -c "$(PROBE)" 2>/dev/null && exit 0; sleep 2; done; echo "Neo4j did not answer on $$NEO4J_URI within 60 s"; exit 1
	$(MAKE) -C $(PROJECT) docs STRICT=
	uv run python -m explorer.load $(PROJECT)
	uv run python -m explorer.server $(PROJECT)
