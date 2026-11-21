.PHONY: setup up down test

setup:
	uv sync
	uv run python -c "from explorer.search import Embedder; Embedder()"

up:
	podman compose up -d

down:
	podman compose down

test:
	uv run python -m unittest discover -s tests
