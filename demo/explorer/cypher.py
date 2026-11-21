"""Read-only Cypher for the explorer's query panel."""


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


def run_read(graph, query, params=None, limit=500, timeout_s=10) -> dict:
    try:
        return graph.read_only(query, params, limit, timeout_s)
    except Exception as e:
        raise CypherError(str(e)) from e
