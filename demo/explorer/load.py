"""Write a Graph into Neo4j, replacing what is there: `python -m explorer.load <project-dir>`."""

import json
import os
import sys
from itertools import groupby
from pathlib import Path

from neo4j import GraphDatabase

from explorer.graph import Graph, build

BATCH = 500


def batches(rows):
    for i in range(0, len(rows), BATCH):
        yield rows[i : i + BATCH]


def write(graph: Graph, driver) -> None:
    def tx_work(tx):
        tx.run("MATCH (n) DETACH DELETE n")
        nodes = sorted(graph.nodes.values(), key=lambda n: n.labels)
        for labels, group in groupby(nodes, key=lambda n: n.labels):
            label = ":".join(f"`{x}`" for x in labels)
            rows = [
                {"props": {k: v for k, v in n.props.items() if v is not None}}
                for n in group
            ]
            for batch in batches(rows):
                tx.run(
                    f"UNWIND $rows AS r CREATE (n:{label}) SET n = r.props", rows=batch
                )
        edges = sorted(graph.edges, key=lambda e: e.type)
        for type, group in groupby(edges, key=lambda e: e.type):
            rows = [{"src": e.src, "dst": e.dst, "props": e.props} for e in group]
            for batch in batches(rows):
                tx.run(
                    "UNWIND $rows AS r MATCH (a:Node {key: r.src}), (b:Node {key: r.dst}) "
                    f"CREATE (a)-[x:`{type}`]->(b) SET x = r.props",
                    rows=batch,
                )

    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT node_key IF NOT EXISTS FOR (n:Node) REQUIRE n.key IS UNIQUE"
        ).consume()
        session.execute_write(tx_work)


def read_project(project: Path) -> Graph:
    export = json.loads((project / "build" / "model.json").read_text())
    needs = json.loads((project / "build" / "needs" / "needs.json").read_text())
    return build(export, needs["versions"][needs["current_version"]]["needs"])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        sys.exit("usage: python -m explorer.load <project-dir>")
    graph = read_project(Path(argv[0]))
    with GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    ) as driver:
        write(graph, driver)
    print(f"loaded {len(graph.nodes)} nodes, {len(graph.edges)} edges")


if __name__ == "__main__":
    main()
