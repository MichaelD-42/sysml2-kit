"""Shared test helpers: a fresh in-memory graph, and loading a kit project into it."""

from pathlib import Path

from explorer import db, load
from explorer.search import Embedder

RFQ = Path(__file__).resolve().parents[2] / "examples" / "window-switch-rfq"

_embedder = None


def load_project(graph, project: Path):
    global _embedder
    _embedder = _embedder or Embedder()  # loading the model is slow: once per run
    return load.load(project, graph, _embedder)


def rfq() -> db.Graph:
    """A new graph with the window-switch RFQ (and its platform) loaded; the caller closes it."""
    graph = db.Graph()
    load_project(graph, RFQ)
    return graph
