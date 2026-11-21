"""Shared test helpers: a fresh in-memory graph, and loading a kit project into it."""

from pathlib import Path

from explorer import db, load
from explorer.search import Embedder

VEHICLE = Path(__file__).resolve().parents[2] / "examples" / "vehicle"

_embedder = None


def load_project(graph, project: Path):
    global _embedder
    _embedder = _embedder or Embedder()  # loading the model is slow: once per run
    return load.load(project, graph, _embedder)


def vehicle() -> db.Graph:
    """A new graph with the vehicle example loaded; the caller closes it."""
    graph = db.Graph()
    load_project(graph, VEHICLE)
    return graph
