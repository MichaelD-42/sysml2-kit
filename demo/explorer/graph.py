"""A kit project's SysML v2 export and needs as a property graph: nodes and edges, no database."""

import re
from dataclasses import dataclass, field

# need type -> RFLP layer
LAYERS = {
    **dict.fromkeys(
        ("crs", "prq", "cst", "usecase", "sysreq", "swreq", "constraint"), "R"
    ),
    **dict.fromkeys(("feature", "function"), "F"),
    **dict.fromkeys(("component", "interface"), "L"),
    **dict.fromkeys(("physical", "physinterface"), "P"),
    **dict.fromkeys(("ctr", "systest", "acctest", "testresult"), "V"),
}
NEED_FIELDS = (
    "title",
    "content",
    "class",
    "purpose",
    "method",
    "domain",
    "platform",
    "variant",
    "reuse",
    "docname",
    "result",
)
# usages that are edges or annotations, not things: nodes only when a need names them
NOT_NODES = {
    "ReferenceUsage",
    "MetadataUsage",
    "MetadataDefinition",
    "ConjugatedPortDefinition",
    "AllocationUsage",
    "SatisfyRequirementUsage",
    "PerformActionUsage",
    "ConnectionUsage",
    "InterfaceUsage",
    "FlowUsage",
    "SuccessionAsUsage",
    "BindingConnectorAsUsage",
}
# a connector's first two related features are its ends
CONNECTORS = {
    "ConnectionUsage": "CONNECTS",
    "InterfaceUsage": "CONNECTS",
    "FlowUsage": "FLOW",
    "SuccessionAsUsage": "SUCCESSION",
}
# (metaclass, source field, target field) -> edge type, for relationships between two elements
RELATIONSHIPS = {
    "FeatureTyping": ("typedFeature", "type", "TYPED_BY"),
    "Subsetting": ("subsettingFeature", "subsettedFeature", "SPECIALIZES"),
    "Redefinition": ("redefiningFeature", "redefinedFeature", "SPECIALIZES"),
    "Subclassification": ("subclassifier", "superclassifier", "SPECIALIZES"),
}
VALUE = re.compile(r"\s*(-?\d+(?:\.\d+)?)\s*\[\s*'?([^\]']+?)'?\s*\]\s*")


@dataclass
class Node:
    key: str
    labels: list[str]
    props: dict


@dataclass
class Edge:
    src: str
    type: str
    dst: str
    props: dict = field(default_factory=dict)


@dataclass
class Graph:
    nodes: dict[str, Node]
    edges: list[Edge]


def ref(value):
    """The @id a reference points to (one reference or the first of a list), or None."""
    if isinstance(value, list):
        value = value[0] if value else None
    return value["@id"] if value else None


def number(text):
    return float(text) if "." in text else int(text)


def build(export, needs):
    by_id = {e["@id"]: e for e in export}
    by_name = {e["qualifiedName"]: e for e in export if e.get("qualifiedName")}
    need_of = {  # element @id -> its need
        by_name[n["qualified_name"]]["@id"]: n
        for n in needs.values()
        if n.get("qualified_name") in by_name
    }
    subjects = {
        ref(e["ownedSubjectParameter"])
        for e in export
        if e["@type"] == "SubjectMembership"
    }

    def in_metadata(eid):
        while eid in by_id:
            if by_id[eid]["@type"] in ("MetadataDefinition", "MetadataUsage"):
                return True
            eid = ref(by_id[eid].get("owner"))
        return False

    def is_node(e):
        if in_metadata(e["@id"]) and e["@id"] not in need_of:
            return False
        if e["@id"] in need_of or e["@id"] in subjects:
            return True
        kind = e["@type"]
        named = e.get("qualifiedName") or kind == "ConstraintUsage"
        thing = kind == "Package" or kind.endswith(("Usage", "Definition"))
        return bool(named and thing and kind not in NOT_NODES)

    uid_key = {
        e["@id"]: need_of[e["@id"]]["id"] if e["@id"] in need_of else e["@id"]
        for e in export
        if is_node(e)
    }

    def owner_node(eid):
        """The nearest node at or above an element."""
        while eid:
            if eid in uid_key:
                return uid_key[eid]
            eid = ref(by_id[eid].get("owner")) if eid in by_id else None

    def body(e):
        reps = e.get("textualRepresentation") or []
        return by_id[reps[0]["@id"]]["body"] if reps else None

    docs = {
        ref(e.get("owner")): e["body"]
        for e in export
        if e["@type"] == "Documentation" and e.get("body")
    }

    def value(e):
        """(value, unit) of an attribute from its feature value's text."""
        for child in e.get("ownedElement") or []:
            fv = by_id[child["@id"]]
            if fv["@type"] != "FeatureValue":
                continue
            v = by_id[ref(fv["value"])]
            text = body(v)
            if text and (m := VALUE.fullmatch(text)):
                return number(m[1]), m[2]
            return v.get("value", text), None
        return None, None

    nodes = {}
    for e in export:
        if e["@id"] not in uid_key:
            continue
        key = uid_key[e["@id"]]
        props = {
            "key": key,
            "uid": e["@id"],
            "name": e.get("name"),
            "qualifiedName": e.get("qualifiedName"),
            "shortName": e.get("shortName"),
            "kind": e["@type"],
            "isVariation": e.get("isVariation"),
            "doc": docs.get(e["@id"]),
        }
        labels = ["Node", "Element", e["@type"]]
        if (n := need_of.get(e["@id"])) is not None:
            labels += ["Need", n["type"]]
            props |= {f: n[f] for f in NEED_FIELDS if n.get(f) not in (None, "")}
            props["layer"] = LAYERS.get(n["type"])
            props["source"] = n.get("source")
        if e["@type"] == "AttributeUsage":
            props["value"], props["unit"] = value(e)
        if e["@type"] == "ConstraintUsage":
            props["expression"] = next(
                (
                    body(by_id[c["@id"]])
                    for c in e.get("ownedElement") or []
                    if by_id[c["@id"]]["@type"].endswith("Expression")
                ),
                None,
            )
        nodes[key] = Node(key, labels, props)
    exported = {n["id"] for n in need_of.values()}
    for n in needs.values():
        if n["id"] in exported:
            continue
        props = {"key": n["id"], "layer": LAYERS.get(n["type"])}
        props |= {f: n[f] for f in NEED_FIELDS if n.get(f) not in (None, "")}
        props["source"] = n.get("source")
        # the outermost section: a document's numbered chapters group under its title
        props["section"] = (n.get("sections") or [None])[-1]
        nodes[n["id"]] = Node(n["id"], ["Node", "Need", n["type"]], props)

    edges = []

    def add(src, type, dst, **props):
        if src and dst and src != dst and src in nodes and dst in nodes:
            edges.append(Edge(src, type, dst, props))

    for e in export:
        kind = e["@type"]
        if e["@id"] in uid_key:
            add(owner_node(ref(e.get("owner"))), "OWNS", uid_key[e["@id"]])
        if kind in RELATIONSHIPS and not e.get("isImplied"):
            s, t, name = RELATIONSHIPS[kind]
            add(uid_key.get(ref(e.get(s))), name, uid_key.get(ref(e.get(t))))
        elif kind in CONNECTORS and len(e.get("relatedFeature") or []) >= 2:
            a, b = (owner_node(r["@id"]) for r in e["relatedFeature"][:2])
            props = {}
            if kind == "FlowUsage":
                payload = [
                    by_id[c["@id"]]
                    for c in e["ownedElement"]
                    if by_id[c["@id"]]["@type"] == "PayloadFeature"
                ]
                typing = [
                    by_id[c["@id"]]
                    for p in payload
                    for c in p["ownedElement"]
                    if by_id[c["@id"]]["@type"] == "FeatureTyping"
                ]
                if typing:
                    props["item"] = by_id[ref(typing[0]["type"])].get("name")
            add(a, CONNECTORS[kind], b, **props)
        elif kind == "RequirementConstraintMembership":
            add(
                owner_node(ref(e.get("owner"))),
                "REQUIRES",
                uid_key.get(ref(e.get("ownedConstraint"))),
            )
        elif kind == "SubjectMembership":
            add(
                owner_node(ref(e.get("owner"))),
                "SUBJECT",
                uid_key.get(ref(e.get("ownedSubjectParameter"))),
            )
        elif kind == "PerformActionUsage":
            sub = next(
                (
                    by_id[c["@id"]]
                    for c in e["ownedElement"]
                    if by_id[c["@id"]]["@type"] == "ReferenceSubsetting"
                ),
                None,
            )
            add(
                owner_node(ref(e.get("owner"))),
                "PERFORMS",
                uid_key.get(ref(sub["target"])) if sub else None,
            )
    for n in needs.values():
        for name, targets in n.items():
            if name.endswith("_back") or not isinstance(targets, list):
                continue
            for t in targets:
                if isinstance(t, str) and t in nodes:
                    add(n["id"], name.upper(), t)

    seen, unique = set(), []
    for edge in edges:
        k = (edge.src, edge.type, edge.dst, tuple(sorted(edge.props.items())))
        if k not in seen:
            seen.add(k)
            unique.append(edge)

    # searchText: the node's own words, its attributes and the text of what it links to
    children = {}
    for edge in unique:
        if edge.type == "OWNS":
            children.setdefault(edge.src, []).append(nodes[edge.dst])
    linked = {}
    for edge in unique:
        linked.setdefault(edge.src, []).append(edge.dst)
        linked.setdefault(edge.dst, []).append(edge.src)
    for key, node in nodes.items():
        p = node.props
        owner_path = (p.get("qualifiedName") or "").rpartition("::")[0]
        attrs = (
            [
                f"{c.props['value']} {c.props.get('unit') or ''}".strip()
                for c in children.get(key, [])
                if c.props["kind"] == "AttributeUsage"
                and c.props.get("value") is not None
            ]
            if "kind" in p
            else []
        )
        parts = [p.get("name"), p.get("kind"), p.get("doc"), owner_path, *attrs]
        parts += [
            nodes[o].props.get("content") for o in dict.fromkeys(linked.get(key, []))
        ]
        p["searchText"] = "\n".join(str(x) for x in parts if x)
    return Graph(nodes, unique)
