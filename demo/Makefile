.PHONY: setup test demo

PROJECT ?= ../examples/vehicle

setup:
	uv sync
	uv run python -c "from explorer.search import Embedder; Embedder()"

test:
	uv run python -m unittest discover -s tests

# build the project, load it into an in-memory graph, serve on http://127.0.0.1:8000
demo:
	$(MAKE) -C $(PROJECT) docs STRICT=
	uv run python -m explorer.server $(PROJECT)
