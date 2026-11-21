"""Hybrid search over the graph: vector similarity and full-text, fused by rank."""

import re
from pathlib import Path

CACHE = Path(__file__).resolve().parents[1] / ".cache" / "fastembed"
MODEL = "BAAI/bge-small-en-v1.5"
RRF_K = 60
LUCENE = re.compile(r'([+\-&|!(){}\[\]^"~*?:\\/])')
OPERATORS = {"AND", "OR", "NOT"}


class Embedder:
    dims = 384

    def __init__(self):
        from fastembed import TextEmbedding

        self.model = TextEmbedding(MODEL, cache_dir=str(CACHE))

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self.model.embed(texts)]


def lucene(q: str) -> str:
    words = [w.lower() if w in OPERATORS else w for w in q.split()]
    return LUCENE.sub(r"\\\1", " ".join(words))


def search(graph, embedder, q: str, k: int = 10) -> list[dict]:
    q = q.strip()
    if not q:
        return []
    vector = embedder.embed([q])[0]
    ranked = {}  # key -> fused score
    lists = [
        graph.query(
            "CALL db.index.vector.queryNodes('element_embedding', $k, $v) "
            "YIELD node RETURN node.key AS key",
            k=k,
            v=vector,
        )
    ]
    if text := lucene(q):
        lists.append(
            graph.query(
                "CALL db.index.fulltext.queryNodes('element_text', $q) "
                "YIELD node RETURN node.key AS key LIMIT $k",
                q=text,
                k=k,
            )
        )
    for rows in lists:
        for rank, row in enumerate(rows):
            ranked[row["key"]] = ranked.get(row["key"], 0) + 1 / (RRF_K + rank + 1)
    exact = graph.query("MATCH (n:Node {key: $q}) RETURN n.key AS key", q=q)
    if exact:
        ranked[exact[0]["key"]] = float("inf")
    keys = sorted(ranked, key=ranked.get, reverse=True)[:k]
    rows = graph.query(
        "UNWIND $keys AS key MATCH (n:Node {key: key}) "
        "OPTIONAL MATCH (o:Node)-[:OWNS]->(n) "
        "RETURN n.key AS key, n.name AS name, n.kind AS kind, n.shortName AS shortName, "
        "o.key AS owner, substring(coalesce(n.searchText, ''), 0, 200) AS snippet",
        keys=keys,
    )
    by_key = {r["key"]: r for r in rows}
    return [
        {**by_key[key], "score": ranked[key] if ranked[key] != float("inf") else 1.0}
        for key in keys
    ]


def neighbourhood(graph, key: str) -> dict:
    """The node and its 1-hop edges."""
    records = graph.query(
        "MATCH (n:Node {key: $key}) "
        "OPTIONAL MATCH (n)-[r]-(m:Node) "
        "RETURN n, collect(CASE WHEN r IS NULL THEN NULL ELSE {type: type(r), "
        "direction: CASE WHEN startNode(r) = n THEN 'out' ELSE 'in' END, "
        "other: m.key, name: m.name} END) AS edges",
        key=key,
    )
    if not records:
        return {}
    node = {k: v for k, v in records[0]["n"].items() if k != "embedding"}
    return {"node": node, "edges": records[0]["edges"]}
