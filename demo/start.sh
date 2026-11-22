#!/usr/bin/env bash
# Start the model explorer: build a kit project's docs, load it, serve http://127.0.0.1:8000.
# Usage: demo/start.sh [project]   (default: the window-switch RFQ example)
set -euo pipefail
# a project given relative to where the script is called from, resolved before moving to demo/
project="$(cd "${1:-$(dirname "$0")/../examples/window-switch-rfq}" && pwd)"
cd "$(dirname "$0")"

for tool in uv make sysml sysml2kit sphinx-build; do
	if ! command -v "$tool" >/dev/null; then
		echo "start.sh: $tool is not on PATH (uv: https://docs.astral.sh/uv/; the kit's tools: make tools in the project)" >&2
		exit 1
	fi
done

uv sync --quiet
# rule violations are reported, not fatal, as with `make -C demo demo`
make -C "$project" docs STRICT=
exec uv run python -m explorer.server "$project"
