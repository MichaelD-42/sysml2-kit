.PHONY: up down test

up:
	podman compose up -d

down:
	podman compose down

test:
	uv run python -m unittest discover -s tests
