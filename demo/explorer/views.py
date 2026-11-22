"""Diagram views over the loaded graph: one Cypher query per kind, plus the containment tree."""

import json
from pathlib import Path

import tomllib

from explorer.graph import LAYERS
from sysml2kit.compliance import CONSTRAINED, compliance, ctr_rows

KINDS = (
    "product",
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
    "metamodel",
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
# every part that uses it (`parents`; `parent` is the first, for nesting), a part another child
# redefines is left out, and variants stay in their view
PARTS = """
WITH f, COLLECT {
  MATCH p = (f)-[:OWNS|SPECIALIZES|TYPED_BY*0..]->(x)-[:OWNS]->(c:PartUsage)
  WHERE all(n IN nodes(p)[1..-1] WHERE n:PartUsage OR n:PartDefinition)
    AND none(n IN nodes(p)[..-1] WHERE n.isVariation)
  WITH c, nodes(p) AS ns, [i IN range(0, length(p) - 2) WHERE type(relationships(p)[i]) = 'OWNS'] AS owns
  WITH c, collect(DISTINCT CASE owns WHEN [] THEN f ELSE ns[last(owns) + 1] END) AS parents
  // a part the focus inherits and its children also use hangs under the children only
  WITH c, CASE WHEN size(parents) > 1 THEN [x IN parents WHERE x <> f] ELSE parents END AS parents
  RETURN {n: c, parent: parents[0], parents: parents}
} AS found
WITH f, found, COLLECT {
  UNWIND found AS q WITH q.n AS o MATCH (o)-[:SPECIALIZES]->(c) RETURN c
} AS redefined
WITH f, [p IN found WHERE NOT p.n IN redefined] AS parts"""

# ports a part shows: its own and those of what it specializes or is typed by
PORTS = """COLLECT {{
  UNWIND {holders} AS h
  MATCH (h)-[:SPECIALIZES|TYPED_BY|VARIANT_OF*0..]->()-[:OWNS]->(q:PortUsage)
  RETURN {{n: q, parent: h}}
}}"""

CONTEXT = (
    """
MATCH (f:Node {key: $focus})
WITH f, [f] + COLLECT { MATCH (p:PartUsage)-[:SPECIALIZES]->(f) RETURN p } AS uses
// a connection may end on a port the part inherits (the harness wires to SwitchAssembly's ports)
WITH f, uses, COLLECT {
  UNWIND uses AS p
  MATCH (o)-[:OWNS]->(p), (o)-[:OWNS]->(x:PartUsage)-[:OWNS*0..1]->()-[:CONNECTS|FLOW]-()<-[:OWNS*0..1]-()
    <-[:SPECIALIZES|TYPED_BY*0..]-(p)
  WHERE x <> p
  RETURN DISTINCT x
} AS others,
// shortcut: subjects are untyped references, matched to the focus by name; type them to drop this
COLLECT {
  MATCH (uc:UseCaseUsage)-[:SUBJECT]->({name: f.name}), (uc)-[:OWNS]->(a:PartUsage)
  RETURN {a: a, uc: uc.name}
} AS actors
// one node per actor name, the context's own part when it has one (so its connections show)
WITH f, uses, others, actors, COLLECT {
  UNWIND uses AS p MATCH (o)-[:OWNS]->(p), (o)-[:OWNS]->(x:PartUsage) WHERE x <> p RETURN DISTINCT x
} AS siblings
WITH f, uses, others, actors, COLLECT {
  UNWIND actors AS x WITH x WHERE NOT x.a.name IN [o IN others | o.name]
  WITH x.a.name AS name, collect(x.a)[0] AS a
  RETURN coalesce([s IN siblings WHERE s.name = name][0], a)
} AS cast
WITH f, uses, others + cast AS shown, actors
// the usages that specialize the focus are drawn as the focus itself
WITH f, [n IN [f] + shown | {key: n.key, parent: null}] AS nodes,
  [n IN [f] + uses + shown | n.key] AS keys, [p IN uses | p.key] AS folded,
  [x IN actors | {src: [n IN shown WHERE n.name = x.a.name][0].key, dst: f.key, type: 'ACTOR', label: x.uc}] AS extra
RETURN nodes, COLLECT {
  MATCH (a:Node)-[:SPECIALIZES|TYPED_BY*0..]->()-[:OWNS*0..1]->()-[r:CONNECTS|FLOW]->()
    <-[:OWNS*0..1]-()<-[:SPECIALIZES|TYPED_BY*0..]-(b:Node)
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
  MATCH (f)-[:SPECIALIZES|TYPED_BY|VARIANT_OF*0..]->()-[:OWNS]->(q:PortUsage) RETURN DISTINCT q
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
  MATCH (q)-[:CONNECTS|FLOW|BINDS]-(r:PortUsage)<-[:OWNS]-(o:Node)
  WHERE NOT r IN fports AND NOT r IN [x IN pports | x.n]
  RETURN DISTINCT {port: r, part: o}
} AS outside
WITH [{key: f.key, parent: null}]
  + [q IN fports | {key: q.key, parent: f.key}]
  + [c IN parts | {key: c.key, parent: f.key}]
  + [x IN pports | {key: x.n.key, parent: x.parent.key}]
  + [x IN outside | {key: x.part.key, parent: null}]
  + [x IN outside | {key: x.port.key, parent: x.part.key}] AS nodes"""
    + _close("CONNECTS|FLOW|BINDS")
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
    + _close("CONNECTS|FLOW|BINDS")
)

COMPOSITION = (
    """
MATCH (f:Node {key: $focus})"""
    + PARTS
    + """
WITH [{key: f.key, parent: null}] + [p IN parts | {key: p.n.key, parent: null}] AS nodes,
  COLLECT {
    UNWIND parts AS p UNWIND p.parents AS o
    RETURN {src: o.key, dst: p.n.key, type: 'OWNS', label: null}
  } AS edges
RETURN nodes, edges"""
)

# a feature's own actions and those of the feature it specializes (an RFQ feature inherits the
# platform feature's functions)
ACTIVITY = """
MATCH (f:Node {key: $focus})
MATCH (f)-[:SPECIALIZES*0..1]->(g:ActionUsage)
MATCH p = (g) ((:Node)-[:OWNS]->(:ActionUsage))+
WITH g, last(nodes(p)) AS a, nodes(p)[-2] AS owner
WITH collect({
  key: a.key,
  parent: CASE owner WHEN g THEN null ELSE owner.key END,
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
    "context": "is connected to nothing in its owner",
    "composition": "has no parts",
}
# what a view is drawn for when the focus has none of its own: a port's owner, a function's
# feature, the variation a variant (or a part that selects it) belongs to; the focus stays highlighted
PORT_OWNER = "MATCH (o:Node)-[:OWNS]->(:PortUsage {key: $focus}) RETURN o.key LIMIT 1"
SUBJECTS = {
    "boundary": PORT_OWNER,
    "interfaces": PORT_OWNER,
    "activity": "MATCH (o:Node)-[:OWNS]->(n:ActionUsage {key: $focus}) "
    "WHERE NOT EXISTS { (n)-[:SPECIALIZES*0..1]->(:ActionUsage)-[:OWNS]->(:ActionUsage) } RETURN o.key LIMIT 1",
    "variants": "MATCH (:Node {key: $focus})-[:SPECIALIZES*0..1]->()-[:VARIANT_OF]->(v) RETURN v.key LIMIT 1",
}
FOCUS = "MATCH (n:Node) WHERE n.key = $focus OR n.qualifiedName = $focus RETURN n.key LIMIT 1"
NODES = """
UNWIND $keys AS k MATCH (n:Node {key: k})
RETURN n.key AS key, coalesce(CASE WHEN n:usecase THEN n.title END, n.name, n.title, n.key) AS name,
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
    MATCH (n)-[:SPECIALIZES|TYPED_BY|VARIANT_OF*0..]->()-[:OWNS]->(q:PortUsage)
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
    srs = {}  # crs -> system requirements satisfying it
    for k, n in needs.items():
        if n["type"] == "sysreq":
            for c in n.get("satisfies", []):
                srs.setdefault(c, []).append(k)
    out = [dict(zip(ROW, r)) for r in rows]
    for r in out:
        # a non-functional or constraint CRS is answered by constraints or textual SRs
        texts = sorted(srs.get(r["crs"], [])) if r["class"] in CONSTRAINED else []
        r["satisfied_by"] = list(r["constraints"]) + texts
    return {
        "rows": out,
        "ctrs": [dict(zip(CTR_ROW, r)) for r in ctr_rows(needs)],
        "findings": findings,
    }


def view(
    graph,
    kind: str,
    focus: str | None,
    needs_path: Path | None = None,
    project: Path | None = None,
) -> dict:
    if kind not in KINDS:
        raise ValueError(f"unknown view kind {kind!r}")
    if kind == "product":
        return product(graph)
    if kind == "metamodel":
        if project is None:
            raise ValueError("the meta-model view needs the project")
        return metamodel(graph, project)
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
    subject = _read(graph, SUBJECTS[kind], focus=key) if kind in SUBJECTS else []
    drawn = next(iter(subject[0].values())) if subject else key
    records = _read(graph, QUERIES[kind], focus=drawn)
    nodes = _nodes(graph, records[0]["nodes"]) if records else []
    # a part alone is no context or composition
    if kind in ("context", "composition") and len(nodes) == 1:
        nodes = []
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


PRODUCT_UCS = """
MATCH (f:Node {key: $product}), (uc:UseCaseUsage)-[:SUBJECT]->({name: f.name})
RETURN uc.key AS key,
  COLLECT { MATCH (uc)-[:OWNS]->(a:PartUsage) RETURN a.name } AS actors,
  COLLECT { MATCH (uc)-[:PERFORMS]->(x:feature) RETURN x.key } AS features
ORDER BY key"""
# a feature's functions, its own and those of the feature it specializes, and where they are allocated
PRODUCT_FEATURES = """
UNWIND $keys AS k MATCH (x:Node {key: k})
RETURN k AS key,
  COUNT { MATCH (x)-[:SPECIALIZES*0..1]->(:feature)-[:OWNS*]->(fn:function) RETURN DISTINCT fn } AS functions,
  COLLECT { MATCH (x)-[:SPECIALIZES*0..1]->(:feature)-[:OWNS*]->(:function)-[:ALLOCATED_TO]->(c:component)
            RETURN DISTINCT c.key } AS lcs"""
# the product's positions (its own parts) and the logical blocks of what it specializes
PRODUCT_LOGICAL = """
MATCH (f:Node {key: $product})
RETURN COLLECT { MATCH (f)-[:OWNS]->(c:component) RETURN {key: c.key, picks: COLLECT {
    MATCH (c)-[:ALLOCATED_TO]->(:physical)-[:SPECIALIZES]->(v)<-[:OWNS]-(x) WHERE x.isVariation
    RETURN x.name + ': ' + v.name
  }} } AS positions,
  COLLECT { MATCH (f)-[:SPECIALIZES]->()-[:OWNS]->(c:component) RETURN DISTINCT c.key } AS blocks"""
# top-level physical parts (a project part that selects a variant is no part of its own)
PRODUCT_PHYSICAL = """
MATCH (:Package)-[:OWNS]->(t:physical) WHERE NOT EXISTS { (t)-[:SPECIALIZES]->(:physical) }
RETURN t.key AS key, t.domain AS domain, coalesce(t.isVariation, false) AS variation,
  COLLECT { MATCH (t)-[:OWNS]->(c:physical) RETURN {key: c.key, parts: COUNT { (c)-[:OWNS]->(:physical) }} } AS parts
ORDER BY key"""
OVERVIEW_COLUMNS = ("Context", "Use cases", "Features", "Logical", "Physical")
DOMAINS = {"ME": "ME · mechanics", "EE": "EE · electronics", "SW": "SW · software"}


def _count(n, what):
    return [{"name": f"{n} {what}{'' if n == 1 else 's'}"}] if n else []


def product(graph) -> dict:
    """The whole product on one page: its context, use cases, features, logical blocks and positions
    (with the variants each selects), and its physical parts by domain. Top level only; what is
    below a box is a count on it. Edges: actor to use case, use case to feature, feature to the
    blocks its functions are allocated to."""
    found = _read(graph, PRODUCT, platform=False)
    if not found:
        return {
            "kind": "product",
            "focus": None,
            "nodes": [],
            "edges": [],
            "reason": "no product",
        }
    focus = found[0]["key"]
    group = {t: f"group:{t.split()[0].lower()}" for t in OVERVIEW_COLUMNS}
    rows, edges = [], []  # edges carry an empty label: the column says what they mean

    def add(key, parent, attributes=()):
        rows.append({"key": key, "parent": parent, "attributes": list(attributes)})

    # context: the parts around the product, each actor once; how they connect is the context view
    ctx = _read(graph, CONTEXT, focus=focus)[0]
    around = [n["key"] for n in ctx["nodes"] if n["key"] != focus]
    for k in around:
        add(k, group["Context"])
    by_name = {r["name"]: r["key"] for r in _read(graph, NODES, keys=around)}
    ucs = _read(graph, PRODUCT_UCS, product=focus)
    features = list(dict.fromkeys(k for uc in ucs for k in uc["features"]))
    feats = {r["key"]: r for r in _read(graph, PRODUCT_FEATURES, keys=features)}
    for uc in ucs:
        add(uc["key"], group["Use cases"])
        edges += [
            {"src": by_name[a], "dst": uc["key"], "type": "ACTOR", "label": ""}
            for a in uc["actors"]
            if a in by_name
        ]
        edges += [
            {"src": uc["key"], "dst": f, "type": "PERFORMS", "label": ""}
            for f in uc["features"]
        ]
    for f in features:
        add(f, group["Features"], _count(feats[f]["functions"], "function"))

    logical = _read(graph, PRODUCT_LOGICAL, product=focus)[0]
    add(focus, group["Logical"])
    for p in logical["positions"]:
        add(p["key"], focus, ({"name": x} for x in sorted(p["picks"])))
    for b in logical["blocks"]:
        add(b, group["Logical"])
    lcs = {p["key"] for p in logical["positions"]} | set(logical["blocks"])
    edges += [
        {"src": f, "dst": c, "type": "ALLOCATED_TO", "label": ""}
        for f in features
        for c in feats[f]["lcs"]
        if c in lcs
    ]

    # physical parts by domain; which block they realize is in the trace view and the tree
    for d, title in DOMAINS.items():
        rows.append(
            {
                "key": f"group:{d}",
                "parent": group["Physical"],
                "name": title,
                "domain": d,
            }
        )
    for t in _read(graph, PRODUCT_PHYSICAL):
        if not t["domain"]:
            continue
        what = "variant" if t["variation"] else "part"
        # a software part shows its components, each with its unit count
        if t["domain"] == "SW" and t["parts"]:
            add(t["key"], f"group:{t['domain']}")
            for c in t["parts"]:
                add(c["key"], t["key"], _count(c["parts"], "unit"))
        else:
            add(t["key"], f"group:{t['domain']}", _count(len(t["parts"]), what))

    nodes = _nodes(graph, [r for r in rows if not r["key"].startswith("group:")])
    columns = [
        {"key": group[t], "name": t, "parent": None, "partition": i}
        for i, t in enumerate(OVERVIEW_COLUMNS)
    ]
    groups = [
        {
            "kind": "group",
            "domain": None,
            "compartments": {"attributes": [], "ports": []},
        }
        | g
        for g in columns + [r for r in rows if r["key"].startswith("group:")]
    ]
    return {
        "kind": "product",
        "focus": focus,
        "nodes": groups + nodes,
        "edges": edges,
        "reason": None,
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
            RETURN {dir: 'out', type: type(r), key: m.key, name: coalesce(CASE WHEN m:usecase THEN m.title END, m.name, m.title, m.expression, m.key), kind: m.kind} } +
  COLLECT { MATCH (m:Node)-[r]->(n) WHERE type(r) IN $in
            RETURN {dir: 'in', type: type(r), key: m.key, name: coalesce(CASE WHEN m:usecase THEN m.title END, m.name, m.title, m.expression, m.key), kind: m.kind} } AS links
ORDER BY platform, CASE kind WHEN 'crs' THEN 0 WHEN 'ctr' THEN 1 WHEN 'sysreq' THEN 2 WHEN 'cst' THEN 3 ELSE 4 END, doc, key"""


def requirements_tree(graph) -> list[dict]:
    """Requirements grouped by document section, each with the elements linked to it as `links`."""
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
        links = [
            {
                "key": x["key"],
                "name": x["name"],
                "kind": x["kind"],
                "rel": (OUT_REL if x["dir"] == "out" else IN_REL)[x["type"]],
            }
            for x in r["links"]
            if not (x["dir"] == "in" and (x["type"], x["key"]) in partial)
        ]
        links.sort(key=lambda k: (k["rel"], k["key"]))
        groups.setdefault(r["grp"], []).append(
            {
                "key": r["key"],
                "name": r["name"],
                "kind": r["kind"],
                "children": [],
                "links": links,
                "platform": r["platform"],
                "class": r["class"],
            }
        )
    return [
        {"key": None, "name": g, "kind": "group", "children": items}
        for g, items in groups.items()
    ]


RFLP = """
MATCH (a:Node)-[r:PERFORMS|OWNS|ALLOCATED_TO|SPECIALIZES]->(b:Node)
WHERE (type(r) = 'PERFORMS' AND a:usecase AND b:feature)
   OR (type(r) = 'OWNS' AND (a:feature OR a:function) AND b:function)
   OR (type(r) = 'ALLOCATED_TO' AND a:function AND b:component)
   OR (type(r) = 'ALLOCATED_TO' AND a:component AND b:physical)
   OR (type(r) IN ['OWNS', 'SPECIALIZES'] AND a:physical AND b:physical)
RETURN a.key AS src, b.key AS dst, type(r) = 'SPECIALIZES' AS reuse"""
PHYSICAL_BRANCH = "Physical breakdown"
# the product a tree is rooted at: the first top-level logical component of the project or platform
PRODUCT = """
MATCH (:Package)-[:OWNS]->(n:component) WHERE coalesce(n.platform, false) = $platform
RETURN n.key AS key ORDER BY n.key LIMIT 1"""
# a project RFLP element and the platform one it specializes, is typed by or is a variant of
RFLP_USES = """
MATCH (a:usecase|feature|function|component|physical)-[:SPECIALIZES|TYPED_BY|VARIANT_OF*1..3]->
  (b:usecase|feature|function|component|physical)
WHERE NOT coalesce(a.platform, false) AND b.platform
RETURN DISTINCT a.key AS a, b.key AS b"""
RFLP_NODES = """
MATCH (n:usecase|feature|function|component|physical)
RETURN n.key AS key, coalesce(CASE WHEN n:usecase THEN n.title END, n.name, n.title, n.key) AS name,
  head([l IN labels(n) WHERE l IN $types]) AS kind, n.domain AS domain, coalesce(n.platform, false) AS platform"""


def rflp_tree(graph, platform: bool = False) -> list[dict]:
    """The product (project or platform) > use case > feature > function (nested) > logical >
    physical (its parts, and the variant a project part selects). A project feature also lists
    the platform functions it inherits. Below the use cases, the product's physical breakdown:
    its top-level parts and their assemblies. A shared feature or function repeats; a logical or
    physical component is expanded once (a part in the breakdown), later rows carry `again`, the
    branch it is expanded in. Each node lists the elements on the other side it uses or is used
    by (`uses`)."""
    every = {r["key"]: r for r in _read(graph, RFLP_NODES, types=NEED_TYPES)}
    info = {k: r for k, r in every.items() if r["platform"] == platform}
    kids, uses, inherited = {}, {}, {}
    for r in _read(graph, RFLP):
        if r["src"] in every and r["dst"] in every:
            # a part shows the part it specializes, a project part the platform variant it selects
            (inherited if r["reuse"] else kids).setdefault(r["src"], []).append(
                r["dst"]
            )
    for r in _read(graph, RFLP_USES):
        mine, other = (r["b"], r["a"]) if platform else (r["a"], r["b"])
        uses.setdefault(mine, []).append(other)
        # a project feature does what the platform feature it specializes does
        if not platform and every[r["a"]]["kind"] == every[r["b"]]["kind"] == "feature":
            inherited.setdefault(r["a"], []).extend(kids.get(r["b"], []))
    expanded = {}  # a logical or physical component -> the branch it is expanded in

    def node(key, seen, branch):
        n = dict(every[key])
        n["uses"] = sorted(uses.get(key, []))
        if n["kind"] in ("component", "physical"):
            if key in expanded:
                return n | {"children": [], "again": expanded[key]}
            expanded[key] = branch
        # the other side's elements show only below what is reused from it
        own = [k for k in kids.get(key, []) if k in info or n["platform"] != platform]
        n["children"] = [
            node(k, seen | {key}, branch)
            for k in sorted(own + inherited.get(key, []))
            if k not in seen
        ]
        return n

    ucs = sorted(k for k, v in info.items() if v["kind"] == "usecase")
    found = _read(graph, PRODUCT, platform=platform)
    if not found or found[0]["key"] not in info:
        return [node(k, frozenset(), every[k]["name"]) for k in ucs]
    root = found[0]["key"]
    expanded[root] = info[root]["name"]
    # the physical breakdown is built first, so each part is expanded there, its assemblies
    # included, and its rows under logical components refer to it
    tops = [
        r["key"]
        for r in _read(graph, PRODUCT_PHYSICAL)
        if r["key"] in every and (not platform or r["key"] in info)
    ]
    parts = [node(k, frozenset({root}), PHYSICAL_BRANCH) for k in tops]
    branches = [node(k, frozenset({root}), every[k]["name"]) for k in ucs]
    breakdown = {
        "key": None,
        "name": PHYSICAL_BRANCH,
        "kind": "group",
        "platform": False,
        "uses": [],
        "children": parts,
    }
    return [
        dict(
            info[root],
            uses=sorted(uses.get(root, [])),
            children=branches + ([breakdown] if parts else []),
        )
    ]


# V-model: need type -> (level, side)
V_PLACE = {
    "crs": (1, "left"),
    "acctest": (1, "right"),
    "ctr": (1, "right"),
    "usecase": (2, "left"),
    "sysreq": (2, "left"),
    "constraint": (2, "left"),
    "systest": (2, "right"),
    "feature": (3, "left"),
    "function": (3, "left"),
    "component": (4, "left"),
    "swreq": (4, "left"),
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
V_EDGES = "SATISFIES|REALIZES|MATCHES|PARTIAL_MATCHES|PERFORMS|OWNS|ALLOCATED_TO|VERIFIES|TESTS|IMPLEMENTS|APPLIES_TO"


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


LAYER_TITLES = {
    "R": "Requirements",
    "F": "Functional",
    "L": "Logical",
    "P": "Physical",
    "V": "Verification",
}
# ownership once, as the declared owned_by link; a link instance is platform when its source is
META_EDGES = """
MATCH (a:Need)-[r]->(b:Need) WHERE type(r) <> 'OWNS'
RETURN head([l IN labels(a) WHERE l IN $types]) AS src, type(r) AS type,
  head([l IN labels(b) WHERE l IN $types]) AS dst, a.key AS a, b.key AS b,
  coalesce(a.platform, false) AS platform
ORDER BY a, b"""
META_NODES = """
MATCH (n:Need) RETURN head([l IN labels(n) WHERE l IN $types]) AS type, n.key AS key,
  coalesce(n.platform, false) AS platform ORDER BY key"""


def _rule_types(schema):
    t = schema.get("properties", {}).get("type", {})
    return t["enum"] if "enum" in t else [t["const"]]


def metamodel(graph, project: Path) -> dict:
    """The project's need types by RFLP layer, the links between them, and the rules on each."""
    conf = tomllib.loads((project / "docs" / "ubproject.toml").read_text())["needs"]
    schemas = json.loads((project / "docs" / "schemas.json").read_text())["schemas"]
    types = {t["directive"]: t["title"] for t in conf["types"]}
    declared = conf.get("links", {})
    instances = {t: [] for t in types}
    platform = dict.fromkeys(types, 0)
    for r in _read(graph, META_NODES, types=list(types)):
        if r["type"]:
            instances[r["type"]].append(r["key"])
            platform[r["type"]] += r["platform"]
    edges = {}

    def edge(src, link, dst):
        return edges.setdefault(
            (src, link, dst),
            {"instances": [], "platform": 0, "rules": [], "declared": link in declared},
        )

    for r in _read(graph, META_EDGES, types=list(types)):
        if r["src"] and r["dst"]:
            e = edge(r["src"], r["type"].lower(), r["dst"])
            e["instances"].append([r["a"], r["b"]])
            e["platform"] += r["platform"]
    node_rules = {t: [] for t in types}
    # a rule's link check is an edge from the selected type (network) or into it (network_back);
    # its local check (or a rule with no link check) is on the type; a rule may have both
    for rule in schemas:
        selected, checks = _rule_types(rule["select"]), rule["validate"]
        linked = False
        for direction in ("network", "network_back"):
            for link, check in checks.get(direction, {}).items():
                linked = True
                for s in selected:
                    for o in _rule_types(check["contains"]["local"]):
                        ends = (s, o) if direction == "network" else (o, s)
                        edge(ends[0], link, ends[1])["rules"].append(rule["id"])
        if "local" in checks or not linked:
            for s in selected:
                node_rules[s].append(rule["id"])
    used = {link for (_, link, _), e in edges.items() if e["instances"]}
    # a project-added need type has no RFLP layer: it goes under "?"
    layers = {t: LAYERS.get(t, "?") for t in types}
    titles = LAYER_TITLES | ({"?": "Other"} if "?" in layers.values() else {})
    nodes = [
        {
            "key": f"layer:{lv}",
            "name": f"{lv} · {title}",
            "kind": "layer",
            "parent": None,
            "count": sum(len(instances[t]) for t in types if layers[t] == lv),
        }
        for lv, title in titles.items()
    ] + [
        {
            "key": f"type:{t}",
            "name": title,
            "kind": t,
            "parent": f"layer:{layers[t]}",
            "count": len(instances[t]),
            "platform": platform[t],
            "instances": instances[t],
            "rules": node_rules[t],
        }
        for t, title in types.items()
    ]
    return {
        "kind": "metamodel",
        "focus": None,
        "nodes": nodes,
        "edges": [
            {
                "src": f"type:{s}",
                "dst": f"type:{d}",
                "type": link.upper(),
                "label": f"{declared.get(link, {}).get('outgoing', link)} ({len(e['instances'])}"
                + (f", {e['platform']} platform)" if e["platform"] else ")"),
                "count": len(e["instances"]),
                "unused": not e["instances"],
                **e,
            }
            for (s, link, d), e in sorted(edges.items())
        ],
        "unused_links": sorted(set(declared) - used),
        "reason": None,
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
