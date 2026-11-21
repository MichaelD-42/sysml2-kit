"""Diagram views over the loaded graph: one Cypher query per kind, plus the containment tree."""

import json
from pathlib import Path

from sysml2kit.compliance import compliance

KINDS = (
    "context",
    "boundary",
    "interfaces",
    "activity",
    "composition",
    "variants",
    "usecases",
    "trace",
    "compliance",
)
NEED_LINKS = "SATISFIES|ALLOCATED_TO|VERIFIES|REALIZES|MATCHES|PARTIAL_MATCHES|ANSWERS|TESTS|REQUIRES"
ROW = ("crs", "title", "features", "reuse", "partial", "statements", "domains")
TREE_KINDS = [
    "Package",
    "PartDefinition",
    "PartUsage",
    "ActionUsage",
    "PortUsage",
    "UseCaseUsage",
    "RequirementUsage",
]

# a view query binds `nodes` ([{key, parent, ...extras}]) and `edges`; these close it
LABEL = (
    "coalesce(r.item, head(COLLECT { MATCH (end)-[:TYPED_BY]->(:PortDefinition)"
    "-[:OWNS]->(:ItemUsage)-[:TYPED_BY]->(item) WHERE end IN [startNode(r), endNode(r)] RETURN item.name }))"
)


def _close(types, extra="[]"):
    return f"""
WITH nodes, [n IN nodes | n.key] AS keys
RETURN nodes, COLLECT {{
  MATCH (a:Node)-[r:{types}]->(b:Node) WHERE a.key IN keys AND b.key IN keys
  RETURN {{src: a.key, dst: b.key, type: type(r), label: {LABEL}}}
}} + {extra} AS edges"""


# parts below f, walking definitions and specialized parts; a child of a definition shows under
# the part that uses it, a part another child redefines is left out, and variants stay in their view
PARTS = """
WITH f, COLLECT {
  MATCH p = (f) ((:Node)-[:OWNS|SPECIALIZES|TYPED_BY]->(:PartUsage|PartDefinition))* (x)-[:OWNS]->(c:PartUsage)
  WHERE none(n IN nodes(p)[..-1] WHERE n.isVariation)
  WITH c, nodes(p) AS ns, [i IN range(0, length(p) - 2) WHERE type(relationships(p)[i]) = 'OWNS'] AS owns
  WITH c, collect(CASE owns WHEN [] THEN f ELSE ns[last(owns) + 1] END)[0] AS parent
  RETURN {n: c, parent: parent}
} AS found
WITH f, [p IN found WHERE NOT EXISTS {
  MATCH (o)-[:SPECIALIZES]->(c) WHERE c = p.n AND o IN [q IN found | q.n]
}] AS parts"""

# ports a part shows: its own and those of what it specializes or is typed by
PORTS = """COLLECT {{
  UNWIND {holders} AS h
  MATCH (h)-[:SPECIALIZES|TYPED_BY*0..]->()-[:OWNS]->(q:PortUsage)
  RETURN {{n: q, parent: h}}
}}"""

CONTEXT = (
    """
MATCH (f:Node {key: $focus})
WITH f, COLLECT { MATCH (p:PartUsage)-[:SPECIALIZES]->(f) RETURN p } AS uses
WITH f, uses, COLLECT {
  UNWIND uses AS p
  MATCH (o)-[:OWNS]->(p), (o)-[:OWNS]->(x:PartUsage)-[:OWNS*0..1]->()-[:CONNECTS|FLOW]-()<-[:OWNS*0..1]-(p)
  WHERE x <> p
  RETURN DISTINCT x
} AS others,
// shortcut: subjects are untyped references, matched to the focus by name; type them to drop this
COLLECT {
  MATCH (uc:UseCaseUsage)-[:SUBJECT]->({name: f.name}), (uc)-[:OWNS]->(a:PartUsage)
  RETURN {a: a, uc: uc.name}
} AS actors
// one node per actor name, the context's own part when it has one
WITH f, uses, others, actors, COLLECT {
  UNWIND actors AS x WITH x WHERE NOT x.a.name IN [o IN others | o.name]
  WITH x.a.name AS name, collect(x.a)[0] AS a RETURN a
} AS cast
WITH f, uses, others + cast AS shown, actors
// the usages that specialize the focus are drawn as the focus itself
WITH f, [n IN [f] + shown | {key: n.key, parent: null}] AS nodes,
  [n IN [f] + uses + shown | n.key] AS keys, [p IN uses | p.key] AS folded,
  [x IN actors | {src: [n IN shown WHERE n.name = x.a.name][0].key, dst: f.key, type: 'ACTOR', label: x.uc}] AS extra
RETURN nodes, COLLECT {
  MATCH (a:Node)-[:OWNS*0..1]->()-[r:CONNECTS|FLOW]->()<-[:OWNS*0..1]-(b:Node)
  WHERE a.key IN keys AND b.key IN keys AND a <> b
  RETURN DISTINCT {
    src: CASE WHEN a.key IN folded THEN f.key ELSE a.key END,
    dst: CASE WHEN b.key IN folded THEN f.key ELSE b.key END,
    type: type(r), label: """
    + LABEL
    + """
  }
} + extra AS edges"""
)

BOUNDARY = (
    """
MATCH (f:Node {key: $focus})
WITH f, COLLECT {
  MATCH (f)-[:SPECIALIZES|TYPED_BY*0..]->()-[:OWNS]->(q:PortUsage) RETURN DISTINCT q
} AS fports, COLLECT {
  MATCH (f) ((:Node)-[:SPECIALIZES|TYPED_BY]->(:PartUsage|PartDefinition))* ()-[:OWNS]->(c:PartUsage)
  RETURN DISTINCT c
} AS found
WITH f, fports, [c IN found WHERE NOT EXISTS {
  MATCH (o)-[:SPECIALIZES]->(c) WHERE o IN found
}] AS parts
WITH f, fports, parts, """
    + PORTS.format(holders="parts")
    + """ AS pports
WITH f, fports, parts, pports, COLLECT {
  UNWIND fports AS q
  MATCH (q)-[:CONNECTS|FLOW]-(r:PortUsage)<-[:OWNS]-(o:Node)
  WHERE NOT r IN fports AND NOT r IN [x IN pports | x.n]
  RETURN DISTINCT {port: r, part: o}
} AS outside
WITH [{key: f.key, parent: null}]
  + [q IN fports | {key: q.key, parent: f.key}]
  + [c IN parts | {key: c.key, parent: f.key}]
  + [x IN pports | {key: x.n.key, parent: x.parent.key}]
  + [x IN outside | {key: x.part.key, parent: null}]
  + [x IN outside | {key: x.port.key, parent: x.part.key}] AS nodes"""
    + _close("CONNECTS|FLOW")
)

INTERFACES = (
    """
MATCH (f:Node {key: $focus})"""
    + PARTS
    + """
WITH f, parts, """
    + PORTS.format(holders="[f] + [p IN parts | p.n]")
    + """ AS ports
WITH f, parts, ports, COLLECT {
  UNWIND [x IN ports | x.n] AS q
  MATCH (q)-[:TYPED_BY]->()<-[:TYPED_BY]-(:PortUsage)<-[:OWNS]-(i:InterfaceDefinition)
  RETURN DISTINCT i
} AS interfaces
WITH [{key: f.key, parent: null}]
  + [p IN parts | {key: p.n.key, parent: p.parent.key}]
  + [x IN ports | {key: x.n.key, parent: x.parent.key}]
  + [i IN interfaces | {key: i.key, parent: null}] AS nodes"""
    + _close("CONNECTS|FLOW")
)

COMPOSITION = (
    """
MATCH (f:Node {key: $focus})"""
    + PARTS
    + """
WITH [{key: f.key, parent: null}] + [p IN parts | {key: p.n.key, parent: null}] AS nodes,
  [p IN parts | {src: p.parent.key, dst: p.n.key, type: 'OWNS', label: null}] AS edges
RETURN nodes, edges"""
)

ACTIVITY = """
MATCH (f:Node {key: $focus})
MATCH p = (f) ((:Node)-[:OWNS]->(:ActionUsage))+
WITH f, last(nodes(p)) AS a, nodes(p)[-2] AS owner
WITH collect({
  key: a.key,
  parent: CASE owner WHEN f THEN null ELSE owner.key END,
  lane: head(COLLECT { MATCH (a)-[:ALLOCATED_TO]->(c:PartUsage) RETURN {key: c.key, name: c.name} })
}) AS nodes""" + _close("SUCCESSION|FLOW")

VARIANTS = """
MATCH (f:Node {key: $focus}) WHERE f.isVariation
WITH f, COLLECT { MATCH (f)-[:OWNS]->(v:Node) WHERE v.kind = f.kind RETURN v } AS variants
WITH f, variants, COLLECT {
  UNWIND variants AS v
  MATCH (s:Node)-[:SPECIALIZES]->(v) WHERE s.kind = v.kind AND NOT s IN variants
  RETURN {s: s, v: v}
} AS picks
UNWIND variants AS v
WITH f, picks, v, COLLECT {
  MATCH (v)-[:OWNS]->(a:AttributeUsage)
  WHERE EXISTS {
    MATCH (w)-[:OWNS]->(b:AttributeUsage)
    WHERE w <> v AND w IN [(f)-[:OWNS]->(x) WHERE x.kind = f.kind | x] AND b.name = a.name AND b.value <> a.value
  }
  RETURN {name: a.name, value: a.value, unit: a.unit}
} AS differs
WITH f, picks, collect({key: v.key, parent: f.key, selected: v IN [p IN picks | p.v], attributes: differs}) AS vs
WITH [{key: f.key, parent: null, selected: size(picks) > 0}] + vs
  + [p IN picks | {key: p.s.key, parent: null, selected: true}] AS nodes,
  [p IN picks | {src: p.s.key, dst: p.v.key, type: 'SPECIALIZES', label: null}] AS edges
RETURN nodes, edges"""

USECASES = """
MATCH (f:UseCaseUsage {key: $focus})-[:SUBJECT]->(s), (pkg)-[:OWNS]->(f)
WITH s, COLLECT { MATCH (pkg)-[:OWNS]->(uc:UseCaseUsage) RETURN uc } AS ucs
WITH s, ucs, COLLECT {
  UNWIND ucs AS uc MATCH (uc)-[:OWNS]->(a:PartUsage) RETURN {a: a, uc: uc}
} AS actors
// one node per actor name across the use cases
WITH s, ucs, actors, COLLECT {
  UNWIND actors AS x WITH x.a.name AS name, collect(x.a)[0] AS a RETURN a
} AS cast
RETURN [{key: s.key, parent: null}] + [uc IN ucs | {key: uc.key, parent: s.key}]
  + [a IN cast | {key: a.key, parent: null}] AS nodes,
  [x IN actors | {
    src: [a IN cast WHERE a.name = x.a.name][0].key, dst: x.uc.key, type: 'ACTOR', label: null
  }] AS edges"""

TRACE = f"""
MATCH (f:Node {{key: $focus}})
// another customer requirement ends the chain: the view is this requirement's RFLP chain
WITH [f] + COLLECT {{
  MATCH p = (f)-[:{NEED_LINKS}*1..6]-(n) WHERE none(x IN nodes(p)[1..] WHERE x:crs)
  RETURN DISTINCT n
}} AS ns
WITH [n IN ns | {{key: n.key, parent: null}}] AS nodes""" + _close(NEED_LINKS)

QUERIES = {
    "context": CONTEXT,
    "boundary": BOUNDARY,
    "interfaces": INTERFACES,
    "activity": ACTIVITY,
    "composition": COMPOSITION,
    "variants": VARIANTS,
    "usecases": USECASES,
    "trace": TRACE,
}
# the vehicle's logical part when there is one, else the first project part a package owns
TOP_PART = """
MATCH (:Package)-[:OWNS]->(n:PartUsage)
RETURN n.key ORDER BY n.qualifiedName = 'VehicleLogical::vehicle' DESC, coalesce(n.platform, false), n.key
LIMIT 1"""
DEFAULTS = {
    "context": TOP_PART,
    "boundary": TOP_PART,
    "interfaces": TOP_PART,
    "composition": TOP_PART,
    "activity": "MATCH (n:feature) RETURN n.key ORDER BY coalesce(n.platform, false), "
    "COUNT { (n)-[:OWNS*]->(:ActionUsage) } DESC, n.key LIMIT 1",
    "variants": "MATCH (n:Node) WHERE n.isVariation RETURN n.key ORDER BY coalesce(n.platform, false), n.key LIMIT 1",
    "usecases": "MATCH (n:UseCaseUsage) RETURN n.key ORDER BY coalesce(n.platform, false), n.key LIMIT 1",
    "trace": "MATCH (n:crs) RETURN n.key ORDER BY coalesce(n.platform, false), n.key LIMIT 1",
}
REASONS = {
    "activity": "has no actions",
    "variants": "is not a variation",
    "usecases": "is not a use case with a subject",
}
FOCUS = "MATCH (n:Node) WHERE n.key = $focus OR n.qualifiedName = $focus RETURN n.key LIMIT 1"
NODES = """
UNWIND $keys AS k MATCH (n:Node {key: k})
RETURN n.key AS key, coalesce(n.name, n.title, n.key) AS name,
  coalesce(n.kind, [l IN labels(n) WHERE NOT l IN ['Node', 'Element', 'Need']][0]) AS kind,
  n.shortName AS shortName, n.domain AS domain, n.layer AS layer, n.platform AS platform,
  n.variant AS variant, n.reuse AS reuse,
  COLLECT {
    MATCH p = (n)-[:SPECIALIZES*0..]->()-[:OWNS]->(a:AttributeUsage)
    WITH a.name AS name, a ORDER BY length(p)
    WITH name, collect(a)[0] AS a
    RETURN {name: name, value: a.value, unit: a.unit}
  } AS attributes,
  COLLECT {
    MATCH (n)-[:SPECIALIZES|TYPED_BY*0..]->()-[:OWNS]->(q:PortUsage)
    RETURN DISTINCT {key: q.key, name: q.name}
  } AS ports"""
TREE = """
MATCH (n:Node) WHERE n.kind IN $kinds
OPTIONAL MATCH (p:Node)-[:OWNS]->(n) WHERE p.kind IN $kinds
RETURN n.key AS key, coalesce(n.name, n.key) AS name, n.kind AS kind, p.key AS parent
ORDER BY name"""


def _read(driver, query, **params):
    return driver.execute_query(query, params, routing_="r").records


def _nodes(driver, rows):
    """Each view row's node once, with its properties and compartments."""
    first = {}
    for r in rows:
        first.setdefault(r["key"], r)
    rows = list(first.values())
    props = {
        r["key"]: r.data() for r in _read(driver, NODES, keys=[r["key"] for r in rows])
    }
    out = []
    for row in rows:
        node = dict(props[row["key"]])
        attributes, ports = node.pop("attributes"), node.pop("ports")
        extras = {k: v for k, v in row.items() if k != "attributes"}
        node |= extras
        node["compartments"] = {
            "attributes": row.get("attributes", attributes),
            "ports": ports,
        }
        out.append(node)
    return out


def compliance_rows(needs_path: Path) -> dict:
    """The kit's compliance rows as dicts and its findings."""
    data = json.loads(needs_path.read_text())
    rows, findings = compliance(
        data["versions"][data.get("current_version", "")]["needs"]
    )
    return {"rows": [dict(zip(ROW, r)) for r in rows], "findings": findings}


def view(driver, kind: str, focus: str | None, needs_path: Path | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"unknown view kind {kind!r}")
    if kind == "compliance":
        if needs_path is None:
            raise ValueError("the compliance view needs needs_path")
        table = compliance_rows(needs_path)
        rows, findings = table["rows"], table["findings"]
        nodes = _nodes(driver, [{"key": r["crs"], "parent": None} for r in rows])
        return {
            "kind": kind,
            "focus": None,
            "nodes": nodes,
            "edges": [],
            "rows": rows,
            "findings": findings,
            "reason": None if nodes else "no customer requirements",
        }
    found = _read(driver, FOCUS if focus else DEFAULTS[kind], focus=focus)
    if not found:
        raise KeyError(focus or f"no default focus for {kind}")
    key = found[0][0]
    records = _read(driver, QUERIES[kind], focus=key)
    nodes = _nodes(driver, records[0]["nodes"]) if records else []
    reason = None
    if not nodes:
        reason = f"{focus or key} {REASONS.get(kind, f'has no {kind} view')}"
    return {
        "kind": kind,
        "focus": key,
        "nodes": nodes,
        "edges": records[0]["edges"] if nodes else [],
        "reason": reason,
    }


def tree(driver) -> list[dict]:
    rows = _read(driver, TREE, kinds=TREE_KINDS)
    items = {
        r["key"]: {
            "key": r["key"],
            "name": r["name"],
            "kind": r["kind"],
            "children": [],
        }
        for r in rows
    }
    roots = []
    for r in rows:
        if r["parent"]:
            items[r["parent"]]["children"].append(items[r["key"]])
        elif r["kind"] == "Package":
            roots.append(items[r["key"]])
    return roots
