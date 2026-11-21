"""Read-only Cypher for the explorer's query panel."""

import neo4j
from neo4j.graph import Node, Path, Relationship


class CypherError(Exception):
    pass


EXAMPLES = [
    {
        "title": "Composition of a part",
        "query": (
            "MATCH (p:Node {qualifiedName: 'VehiclePhysical::vehicleAssembly'})"
            "-[:OWNS*1..3]->(c:PartUsage) RETURN p, c"
        ),
    },
    {
        "title": "Constraints on a part and its ancestors",
        # via the logical component it is allocated to, the platform part it specialises and the
        # definition it is typed by
        "query": (
            "MATCH (anc:Node)-[:OWNS*0..]->(:Node {key: 'PC-001'}) "
            "MATCH (anc)-[:ALLOCATED_TO|SPECIALIZES|TYPED_BY*0..3]-(s:Node) "
            "MATCH (s)-[:OWNS]->(c:ConstraintUsage) "
            "RETURN DISTINCT s.name AS source, 'owns' AS via, c.name AS constraint, c.expression AS expression "
            "UNION "
            "MATCH (anc:Node)-[:OWNS*0..]->(:Node {key: 'PC-001'}) "
            "MATCH (anc)-[:ALLOCATED_TO|SPECIALIZES|TYPED_BY*0..3]-(s:Node) "
            "MATCH (s)-[:SATISFIES]->(r:Node)-[:REQUIRES]->(c:ConstraintUsage) "
            "RETURN DISTINCT s.name AS source, r.key AS via, c.name AS constraint, c.expression AS expression"
        ),
    },
    {
        "title": "CRS whose features are not all platform",
        "query": (
            "MATCH (f:Node)-[:MATCHES|PARTIAL_MATCHES]->(c:crs) "
            "WITH c, collect(f.platform) AS flags WHERE NOT all(x IN flags WHERE x) "
            "RETURN c.key AS crs, c.title AS title, flags"
        ),
    },
    {
        "title": "Interfaces by domain",
        "query": (
            "MATCH (p:PartUsage)-[:OWNS]->(port:PortUsage)-[:TYPED_BY]->(d:PortDefinition) "
            "RETURN coalesce(p.domain, '(none)') AS domain, d.name AS interface, count(*) AS ports "
            "ORDER BY domain, interface"
        ),
    },
]


def plain(v):
    if isinstance(v, Node):
        return {"key": v.get("key"), "name": v.get("name"), "kind": v.get("kind")}
    if isinstance(v, Relationship):
        return {
            "type": v.type,
            "src": v.start_node.get("key"),
            "dst": v.end_node.get("key"),
        }
    if isinstance(v, Path):
        return [plain(x) for x in (*v.nodes, *v.relationships)]
    if isinstance(v, list):
        return [plain(x) for x in v]
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    return v if v is None or isinstance(v, (str, int, float, bool)) else str(v)


def run_read(driver, query, params=None, limit=500, timeout_s=10) -> dict:
    # a transaction function's timeout is set by unit_of_work, not by a Query passed to tx.run
    @neo4j.unit_of_work(timeout=timeout_s)
    def work(tx):
        result = tx.run(query, params or {})
        return result.keys(), [r.values() for _, r in zip(range(limit + 1), result)]

    try:
        with driver.session() as session:
            columns, rows = session.execute_read(work)
    except Exception as e:
        raise CypherError(getattr(e, "message", None) or str(e)) from e
    return {
        "columns": list(columns),
        "rows": [[plain(v) for v in r] for r in rows[:limit]],
        "truncated": len(rows) > limit,
    }
