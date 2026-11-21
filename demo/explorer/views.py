"""Diagram views over the loaded graph: one Cypher query per kind, plus the containment tree."""

import json
from pathlib import Path

from explorer.graph import LAYERS
from sysml2kit.compliance import compliance, ctr_rows

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
    "vmodel",
)
NEED_LINKS = "SATISFIES|ALLOCATED_TO|VERIFIES|REALIZES|MATCHES|PARTIAL_MATCHES|ANSWERS|TESTS|REQUIRES|APPLIES_TO|IMPLEMENTS"
ROW = (
    "crs",
    "title",
    "class",
    "features",
    "reuse",
    "partial",
    "statements",
    "domains",
    "constraints",
)
CTR_ROW = ("ctr", "title", "purpose", "method", "implemented_by", "statements")
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
  MATCH p = (f)-[:OWNS|SPECIALIZES|TYPED_BY*0..]->(x)-[:OWNS]->(c:PartUsage)
  WHERE all(n IN nodes(p)[1..-1] WHERE n:PartUsage OR n:PartDefinition)
    AND none(n IN nodes(p)[..-1] WHERE n.isVariation)
  WITH c, nodes(p) AS ns, [i IN range(0, length(p) - 2) WHERE type(relationships(p)[i]) = 'OWNS'] AS owns
  WITH c, collect(CASE owns WHEN [] THEN f ELSE ns[last(owns) + 1] END)[0] AS parent
  RETURN {n: c, parent: parent}
} AS found
WITH f, found, COLLECT {
  UNWIND found AS q WITH q.n AS o MATCH (o)-[:SPECIALIZES]->(c) RETURN c
} AS redefined
WITH f, [p IN found WHERE NOT p.n IN redefined] AS parts"""

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
// another customer requirement ends the chain, and a shared use case is not walked through:
// the view is this requirement's RFLP chain
WITH [f] + COLLECT {{
  MATCH p = (f)-[:{NEED_LINKS}*1..6]-(n) WHERE none(x IN nodes(p)[1..] WHERE x:crs)
    AND none(x IN nodes(p)[1..-1] WHERE x:usecase)
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
# the first project part a package owns
TOP_PART = """
MATCH (:Package)-[:OWNS]->(n:PartUsage)
RETURN n.key ORDER BY coalesce(n.platform, false), n.key
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
    # a requirement with links, so the default is not a single box
    "trace": "MATCH (n:crs) RETURN n.key ORDER BY coalesce(n.platform, false), "
    "NOT EXISTS { (n)--(:Need) }, n.key LIMIT 1",
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


def _read(graph, query, **params):
    return graph.query(query, **params)


def _nodes(graph, rows):
    """Each view row's node once, with its properties and compartments."""
    first = {}
    for r in rows:
        first.setdefault(r["key"], r)
    rows = list(first.values())
    props = {r["key"]: r for r in _read(graph, NODES, keys=[r["key"] for r in rows])}
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
    """The kit's compliance rows and customer test requirement rows as dicts, and its findings."""
    data = json.loads(needs_path.read_text())
    needs = data["versions"][data.get("current_version", "")]["needs"]
    rows, findings = compliance(needs)
    return {
        "rows": [dict(zip(ROW, r)) for r in rows],
        "ctrs": [dict(zip(CTR_ROW, r)) for r in ctr_rows(needs)],
        "findings": findings,
    }


def view(graph, kind: str, focus: str | None, needs_path: Path | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"unknown view kind {kind!r}")
    if kind == "vmodel":
        return vmodel(graph, focus)
    if kind == "compliance":
        if needs_path is None:
            raise ValueError("the compliance view needs needs_path")
        table = compliance_rows(needs_path)
        rows, ctrs = table["rows"], table["ctrs"]
        keys = [r["crs"] for r in rows] + [r["ctr"] for r in ctrs]
        nodes = _nodes(graph, [{"key": k, "parent": None} for k in keys])
        return {
            "kind": kind,
            "focus": None,
            "nodes": nodes,
            "edges": [],
            "rows": rows,
            "ctrs": ctrs,
            "findings": table["findings"],
            "reason": None if nodes else "no customer requirements",
        }
    found = _read(graph, FOCUS if focus else DEFAULTS[kind], focus=focus)
    if not found:
        raise KeyError(focus or f"no default focus for {kind}")
    key = next(iter(found[0].values()))
    records = _read(graph, QUERIES[kind], focus=key)
    nodes = _nodes(graph, records[0]["nodes"]) if records else []
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


# label order is not kept by the graph, so a need's type is picked from this list
NEED_TYPES = list(LAYERS)

# need link -> label read from the requirement's side, outgoing and incoming
OUT_REL = {
    "SATISFIES": "satisfies",
    "VERIFIES": "verifies",
    "ANSWERS": "answers",
    "REQUIRES": "requires",
    "REALIZES": "realizes",
    "MATCHES": "matches",
    "TESTS": "tests",
    "IMPLEMENTS": "implements",
    "APPLIES_TO": "applies to",
}
IN_REL = {
    "SATISFIES": "satisfied by",
    "PARTIAL_SATISFIES": "satisfied by (partial)",
    "REALIZES": "realized by",
    "MATCHES": "matched by",
    "PARTIAL_MATCHES": "matched by (partial)",
    "ANSWERS": "answered by",
    "VERIFIES": "verified by",
    "TESTS": "result",
    "REQUIRES": "required by",
    "IMPLEMENTS": "implemented by",
    "APPLIES_TO": "test requirement",
}
REQUIREMENTS = """
MATCH (n:Need) WHERE (NOT n:Element AND NOT n:testresult) OR n:sysreq
RETURN n.key AS key, coalesce(n.title, n.name, n.key) AS name, head([l IN labels(n) WHERE l IN $types]) AS kind,
  CASE WHEN n:sysreq THEN 'System requirements' ELSE coalesce(n.section, 'Other needs') END AS grp,
  n.docname AS doc, coalesce(n.platform, false) AS platform, n.class AS class,
  COLLECT { MATCH (n)-[r]->(m:Node) WHERE type(r) IN $out
            RETURN {dir: 'out', type: type(r), key: m.key, name: coalesce(m.name, m.title, m.expression, m.key), kind: m.kind} } +
  COLLECT { MATCH (m:Node)-[r]->(n) WHERE type(r) IN $in
            RETURN {dir: 'in', type: type(r), key: m.key, name: coalesce(m.name, m.title, m.expression, m.key), kind: m.kind} } AS links
ORDER BY platform, CASE kind WHEN 'crs' THEN 0 WHEN 'ctr' THEN 1 WHEN 'sysreq' THEN 2 WHEN 'cst' THEN 3 ELSE 4 END, doc, key"""


def requirements_tree(graph) -> list[dict]:
    """Requirements grouped by document section, each with the elements linked to it."""
    groups = {}
    for r in _read(
        graph,
        REQUIREMENTS,
        types=NEED_TYPES,
        out=list(OUT_REL),
        **{"in": list(IN_REL)},
    ):
        # a partial match or satisfaction is also exported as the full link: show it once
        partial = {
            (x["type"].removeprefix("PARTIAL_"), x["key"])
            for x in r["links"]
            if x["type"].startswith("PARTIAL_")
        }
        kids = [
            {
                "key": x["key"],
                "name": x["name"],
                "kind": x["kind"],
                "children": [],
                "rel": (OUT_REL if x["dir"] == "out" else IN_REL)[x["type"]],
            }
            for x in r["links"]
            if not (x["dir"] == "in" and (x["type"], x["key"]) in partial)
        ]
        kids.sort(key=lambda k: (k["rel"], k["key"]))
        groups.setdefault(r["grp"], []).append(
            {
                "key": r["key"],
                "name": r["name"],
                "kind": r["kind"],
                "children": kids,
                "platform": r["platform"],
                "class": r["class"],
            }
        )
    return [
        {"key": None, "name": g, "kind": "group", "children": items}
        for g, items in groups.items()
    ]


RFLP = """
MATCH (a:Node)-[r:PERFORMS|OWNS|ALLOCATED_TO]->(b:Node)
WHERE (type(r) = 'PERFORMS' AND a:usecase AND b:feature)
   OR (type(r) = 'OWNS' AND (a:feature OR a:function) AND b:function)
   OR (type(r) = 'ALLOCATED_TO' AND a:function AND b:component)
   OR (type(r) = 'ALLOCATED_TO' AND a:component AND b:physical)
RETURN a.key AS src, b.key AS dst"""
RFLP_NODES = """
MATCH (n:usecase|feature|function|component|physical)
RETURN n.key AS key, coalesce(n.name, n.title, n.key) AS name, head([l IN labels(n) WHERE l IN $types]) AS kind,
  n.domain AS domain, coalesce(n.platform, false) AS platform"""


def rflp_tree(graph) -> list[dict]:
    """Use case > feature > function (nested) > logical > physical; a shared element repeats."""
    info = {r["key"]: r for r in _read(graph, RFLP_NODES, types=NEED_TYPES)}
    kids = {}
    for r in _read(graph, RFLP):
        kids.setdefault(r["src"], []).append(r["dst"])

    def node(key, seen):
        n = dict(info[key])
        n["children"] = [
            node(k, seen | {key})
            for k in sorted(kids.get(key, []), key=lambda k: (info[k]["platform"], k))
            if k not in seen
        ]
        return n

    roots = sorted(
        (k for k, v in info.items() if v["kind"] == "usecase"),
        key=lambda k: (info[k]["platform"], k),
    )
    return [node(k, frozenset()) for k in roots]


# V-model: need type -> (level, side)
V_PLACE = {
    "crs": (1, "left"),
    "acctest": (1, "right"),
    "ctr": (1, "right"),
    "usecase": (2, "left"),
    "sysreq": (2, "left"),
    "systest": (2, "right"),
    "feature": (3, "left"),
    "function": (3, "left"),
    "component": (4, "left"),
    "physical": (5, "bottom"),
}
V_NODES = """
MATCH (n:Need) WHERE NOT coalesce(n.platform, false) AND ($keys IS NULL OR n.key IN $keys)
RETURN n.key AS key, head([l IN labels(n) WHERE l IN $types]) AS type,
  COLLECT { MATCH (t:Node)-[:TESTS]->(n) RETURN {key: t.key, result: t.result} } AS results"""
V_REACH = (
    """
MATCH (f:crs {key: $focus})
WITH f, [f] + COLLECT {
  MATCH p = (f)-[:"""
    + NEED_LINKS
    + """*1..6]-(n) WHERE none(x IN nodes(p)[1..] WHERE x:crs)
    AND none(x IN nodes(p)[1..-1] WHERE x:usecase) RETURN DISTINCT n
} AS ns
UNWIND ns AS n
OPTIONAL MATCH (n:feature)-[:OWNS*]->(fn:function)
OPTIONAL MATCH (fn)-[:ALLOCATED_TO]->(lc:component)
OPTIONAL MATCH (lc)-[:ALLOCATED_TO]->(pc:physical)
WITH collect(n.key) + collect(fn.key) + collect(lc.key) + collect(pc.key) AS keys
RETURN [k IN keys WHERE k IS NOT NULL] AS keys"""
)
V_EDGES = "SATISFIES|REALIZES|MATCHES|PARTIAL_MATCHES|PERFORMS|OWNS|ALLOCATED_TO|VERIFIES|TESTS|IMPLEMENTS"


def vmodel(graph, focus):
    """Left leg (requirements to parts) against right leg (tests and results), level by level."""
    keys = None
    if focus is not None:
        found = _read(graph, FOCUS, focus=focus)
        if not found:
            raise KeyError(focus)
        focus = next(iter(found[0].values()))
        # a customer requirement narrows the V to its chain; any other focus is shown in the whole V
        reach = _read(graph, V_REACH, focus=focus)
        if reach and reach[0]["keys"]:
            keys = reach[0]["keys"]
    rows, results = [], []
    for r in _read(graph, V_NODES, keys=keys, types=NEED_TYPES):
        if r["type"] not in V_PLACE:
            continue
        level, side = V_PLACE[r["type"]]
        rows.append({"key": r["key"], "parent": None, "level": level, "side": side})
        results += [
            {
                "key": t["key"],
                "parent": None,
                "level": level,
                "side": "right",
                "result": t["result"],
            }
            for t in r["results"]
        ]
    nodes = _nodes(graph, rows + results)
    present = {n["key"] for n in nodes}
    edges = [
        {"src": r["a"], "dst": r["b"], "type": r["t"], "label": None}
        for r in _read(
            graph,
            f"MATCH (a:Node)-[r:{V_EDGES}]->(b:Node) WHERE a.key IN $k AND b.key IN $k "
            "RETURN a.key AS a, b.key AS b, type(r) AS t",
            k=list(present),
        )
    ]
    right = {n["level"] for n in nodes if n["side"] == "right"}
    return {
        "kind": "vmodel",
        "focus": focus,
        "nodes": nodes,
        "edges": edges,
        "empty": [lv for lv in (1, 2, 3, 4) if lv not in right],
        "reason": None if nodes else "no requirements to place",
    }


def tree(graph) -> list[dict]:
    rows = _read(graph, TREE, kinds=TREE_KINDS)
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
