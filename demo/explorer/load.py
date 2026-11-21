"""Write a Graph into the Relate graph, replacing its :Node graph.

`python -m explorer.load <project-dir>` loads into a throwaway in-memory graph: a load check.
"""

import json
import re
import sys
from itertools import groupby
from pathlib import Path

from explorer import db
from explorer.graph import Graph, build
from explorer.search import Embedder

BATCH = 500
CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")


def batches(rows):
    for i in range(0, len(rows), BATCH):
        yield rows[i : i + BATCH]


def embed(graph: Graph, embedder) -> None:
    nodes = list(graph.nodes.values())
    # words split out of the camelCase name and the constraint expression help the embedding
    texts = [
        "\n".join(
            filter(
                None,
                (
                    CAMEL.sub(" ", n.props.get("name") or ""),
                    n.props.get("searchText") or n.key,
                    n.props.get("expression"),
                ),
            )
        )
        for n in nodes
    ]
    for batch_nodes, vectors in zip(
        batches(nodes), (embedder.embed(b) for b in batches(texts))
    ):
        for n, v in zip(batch_nodes, vectors):
            n.props["embedding"] = v


def indexes(graph: db.Graph, dims: int) -> None:
    graph.query(
        "CREATE VECTOR INDEX element_embedding IF NOT EXISTS FOR (n:Node) ON (n.embedding) "
        "OPTIONS {indexConfig: {`vector.dimensions`: $dims, "
        "`vector.similarity_function`: 'cosine'}}",
        dims=dims,
    )
    graph.query(
        "CREATE FULLTEXT INDEX element_text IF NOT EXISTS FOR (n:Node) "
        "ON EACH [n.name, n.shortName, n.title, n.searchText]"
    )
    graph.query("CALL db.awaitIndexes(300)")


def write(graph: Graph, target: db.Graph) -> None:
    def statements(run):
        run("MATCH (n:Node) DETACH DELETE n")
        nodes = sorted(graph.nodes.values(), key=lambda n: n.labels)
        for labels, group in groupby(nodes, key=lambda n: n.labels):
            label = ":".join(f"`{x}`" for x in labels)
            rows = [
                {"props": {k: v for k, v in n.props.items() if v is not None}}
                for n in group
            ]
            for batch in batches(rows):
                run(
                    f"UNWIND $rows AS r CREATE (n:{label}) SET n = r.props",
                    {"rows": batch},
                )
        edges = sorted(graph.edges, key=lambda e: e.type)
        for type, group in groupby(edges, key=lambda e: e.type):
            rows = [{"src": e.src, "dst": e.dst, "props": e.props} for e in group]
            for batch in batches(rows):
                run(
                    "UNWIND $rows AS r MATCH (a:Node {key: r.src}), (b:Node {key: r.dst}) "
                    f"CREATE (a)-[x:`{type}`]->(b) SET x = r.props",
                    {"rows": batch},
                )

    target.query(
        "CREATE CONSTRAINT node_key IF NOT EXISTS FOR (n:Node) REQUIRE n.key IS UNIQUE"
    )
    target.write(statements)


def read_project(project: Path) -> Graph:
    export = json.loads((project / "build" / "model.json").read_text())
    needs = json.loads((project / "build" / "needs" / "needs.json").read_text())
    return build(export, needs["versions"][needs["current_version"]]["needs"])


def load(project: Path, target: db.Graph, embedder) -> tuple[int, int]:
    """Replace the graph with the project's model; returns (nodes, edges)."""
    graph = read_project(project)
    embed(graph, embedder)
    write(graph, target)
    indexes(target, embedder.dims)
    return len(graph.nodes), len(graph.edges)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        sys.exit("usage: python -m explorer.load <project-dir>")
    embedder = Embedder()
    target = db.Graph()
    try:
        nodes, edges = load(Path(argv[0]), target, embedder)
    finally:
        target.close()
    print(f"loaded {nodes} nodes, {edges} edges")


if __name__ == "__main__":
    main()
