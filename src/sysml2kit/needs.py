"""SysML v2 interchange JSON (`sysml export`) -> sphinx-needs needs.json.

Every element with a declared short name becomes a need whose id is that short name.
Links inside the model come from native SysML; links to needs written outside the model
(e.g. customer requirements in RST) come from `Trace` metadata (see templates/model/trace.sysml).
"""

import json
import re
from pathlib import Path

from sysml2kit.constraints import Model, Unevaluable
from sysml2kit.reuse import closure, reuse

# SysML metaclass -> need type. A short-named element of any other kind is an error.
NEED_TYPES = {
    "UseCaseDefinition": "usecase",
    "UseCaseUsage": "usecase",
    "RequirementDefinition": "sysreq",
    "RequirementUsage": "sysreq",
    "ActionDefinition": "function",
    "ActionUsage": "function",
    "PartDefinition": "component",
    "PartUsage": "component",
    "PortDefinition": "interface",
    "PortUsage": "interface",
    "InterfaceDefinition": "interface",
    "InterfaceUsage": "interface",
    "ConnectionUsage": "interface",
    "VerificationCaseDefinition": "systest",
    "VerificationCaseUsage": "systest",
    "ConstraintUsage": "constraint",
}
# (metaclass, `#keyword` metadata) -> need type, where the keyword changes the type NEED_TYPES gives
KEYWORD_TYPES = {
    ("ActionUsage", "Trace::Feature"): "feature",
    ("ActionDefinition", "Trace::Feature"): "feature",
    **{
        (kind, domain): need
        for domain in ("Trace::Mechanical", "Trace::Electrical", "Trace::Software")
        for kind, need in (
            ("PartUsage", "physical"),
            ("PartDefinition", "physical"),
            ("PortUsage", "physinterface"),
            ("PortDefinition", "physinterface"),
        )
    },
    # an assembly is physical across domains: the product as built, with no domain of its own
    ("PartUsage", "Trace::Assembly"): "physical",
    ("PartDefinition", "Trace::Assembly"): "physical",
}
# an RFQ derives these itself; the platform realizes them at P, never by specialization
DERIVED = ("feature", "function", "component", "interface")
DOMAINS = {
    "Trace::Mechanical": "ME",
    "Trace::Electrical": "EE",
    "Trace::Software": "SW",
}
# need type -> id prefix; an id may carry a platform tag in front (`PLT1-PC-1`)
PREFIXES = {
    "usecase": "UC",
    "sysreq": "SR",
    "feature": "FEAT",
    "function": "F",
    "component": "LC",
    "interface": "LI",
    "physical": "PC",
    "physinterface": "PI",
    "systest": "STC",
    "constraint": "CON",
}
KIND_NAMES = {
    "usecase": "a use case",
    "sysreq": "a system requirement",
    "feature": "a feature",
    "function": "a function",
    "component": "a logical component",
    "interface": "a logical interface",
    "physical": "a physical component",
    "physinterface": "a physical interface",
    "systest": "a system test",
    "constraint": "a constraint",
}
LINK_TYPES = (
    "satisfies",
    "realizes",
    "verifies",
    "allocated_to",
    "owned_by",
    "specializes",
    "matches",
    "partial_matches",
    "implements",
    "partial_satisfies",
    "connects",
)
# need keys the bridge sets itself; metadata may not overwrite them (`domain` it may)
RESERVED_FIELDS = {
    "id",
    "type",
    "title",
    "content",
    "qualified_name",
    "sysml_kind",
    "source",
    "platform",
    "variant",
    "modified",
    "reuse",
    "leaf",
}
# connector usages whose two ends become a `connects` link to the needs that own them
CONNECTORS = ("InterfaceUsage", "ConnectionUsage")
# relationships whose `specific` end specializes the `general` end
SPECIALIZATIONS = ("Subsetting", "Redefinition", "Subclassification", "FeatureTyping")
# Trace metadata definition (qualified, so another library's `Satisfies` is not a trace link) -> link type
TRACE_METADATA = {
    "Trace::Satisfies": "satisfies",
    "Trace::Realizes": "realizes",
    "Trace::Verifies": "verifies",
    "Trace::Matches": "matches",
    "Trace::Implements": "implements",
}
# link types whose metadata may carry `partial = true`, -> the link type that records it
PARTIAL_LINKS = {"matches": "partial_matches", "satisfies": "partial_satisfies"}
# strings first, so `"http://x"` is not a comment; multi-line note `//* */` before `//`, or `//` would take only its first line
COMMENT = re.compile(r'"(?:\\.|[^"\\])*"|//\*.*?\*/|/\*.*?\*/|//[^\n]*', re.DOTALL)
# reStructuredText inline markup; doc text is plain text, so these are escaped
RST_INLINE = re.compile(r"([\\*`_|])")

# writing rules for system requirements that need no judgment (rflp-method structure.md)
SHALL = re.compile(r"\bshall\b", re.IGNORECASE)
VAGUE = re.compile(
    r"\b(TBD|etc\.|as appropriate|user-friendly|fast)(?!\w)", re.IGNORECASE
)


class BridgeError(Exception):
    pass


def ref(element, key):
    """The @id a single-valued reference points to, or None."""
    value = element.get(key)
    return value["@id"] if value else None


def refs(element, key):
    value = element.get(key) or []
    return [v["@id"] for v in (value if isinstance(value, list) else [value])]


def source_locations(model_files):
    """Map short name -> 'file:line'. The export carries no source positions, so find `<'ID'>` in the text."""
    locations = {}
    for path in model_files:
        # blank out comments (keeping newlines, so line numbers hold): a short name mentioned in a comment is not its declaration
        text = COMMENT.sub(
            lambda m: (
                m.group()
                if m.group().startswith('"')
                else re.sub(r"[^\n]", " ", m.group())
            ),
            Path(path).read_text(),
        )
        for lineno, line in enumerate(text.splitlines(), 1):
            for quoted, plain in re.findall(r"<'([^']+)'>|<([A-Za-z_][\w-]*)>", line):
                locations.setdefault(quoted or plain, f"{path}:{lineno}")
    return locations


def platform_dir(project):
    """The platform project's directory, as the project's Makefile names it (`PLATFORM := ...`)."""
    makefile = Path(project) / "Makefile"
    text = makefile.read_text() if makefile.is_file() else ""
    m = re.search(r"^PLATFORM\s*:?=\s*(\S+)", text, re.MULTILINE)
    return Path(project) / (m[1] if m else "platform")


def normalize(elements):
    """Read a sysml 0.2 export as the kit reads a 0.1.4 one; changes the elements in place and returns them.

    0.2 writes `owner` and `ownedElement` as the specification derives them: a relationship has
    neither (it has `owningRelatedElement` and `ownedRelatedElement`), and an element's
    `ownedElement` leaves out the relationships it owns. The kit follows both."""
    for e in elements:
        if not e.get("owner") and e.get("owningRelatedElement"):
            e["owner"] = e["owningRelatedElement"]
        owned = list(e.get("ownedElement") or []) + list(
            e.get("ownedRelatedElement") or []
        )
        owned += e.get("ownedRelationship") or []
        e["ownedElement"] = list({o["@id"]: o for o in owned}.values())
    return elements


def convert(elements, locations, platform_files=(), warnings=None, mapping=None):
    """needs.json content; a constraint that does not hold is an error, one that cannot be evaluated a warning.

    `mapping` (see `load_mapping`) adapts the bridge to a project's own method: `keywords` maps
    keyword metadata to a need type, `ids` a need type to the id pattern it must match,
    `metadata_links` and `metadata_fields` metadata to a link type or a field taking its strings."""
    mapping = mapping or {}
    keyword_map = mapping.get("keywords", {})
    id_patterns = mapping.get("ids", {})
    trace_metadata = {**TRACE_METADATA, **mapping.get("metadata_links", {})}
    field_metadata = mapping.get("metadata_fields", {})
    link_types = tuple(dict.fromkeys(LINK_TYPES + tuple(trace_metadata.values())))
    elements = normalize(elements)
    by_id = {e["@id"]: e for e in elements}
    errors = []
    needs = {}
    need_of = {}  # element @id -> need id

    def name_of(element_id):
        e = by_id.get(element_id, {})
        return e.get("qualifiedName") or e.get("name") or element_id

    keywords = {}  # element @id -> qualified names of the metadata applied to it
    for e in elements:
        if e["@type"] == "MetadataUsage":
            names = {by_id.get(m, {}).get("qualifiedName") for m in refs(e, "type")}
            names.discard(None)  # type not in the export or unnamed
            for annotated in refs(e, "annotatedElement"):
                keywords.setdefault(annotated, set()).update(names)

    for e in elements:
        # declared, not derived: implicit features (e.g. allocation ends) inherit the shortName they reference
        short = e.get("declaredShortName")
        if not short:
            continue
        kind = NEED_TYPES.get(e["@type"])
        tags = keywords.get(e["@id"], set())
        kind = next(
            (
                KEYWORD_TYPES[e["@type"], k]
                for k in sorted(tags)
                if (e["@type"], k) in KEYWORD_TYPES
            ),
            kind,
        )
        kind = next((keyword_map[k] for k in sorted(tags) if k in keyword_map), kind)
        domains = sorted(tags & DOMAINS.keys())
        if len(domains) > 1:
            errors.append(
                f"{short}: one domain keyword allowed, found {' and '.join(domains)}"
            )
            continue
        if domains and "Trace::Assembly" in tags:
            errors.append(f"{short}: an assembly takes no domain keyword")
            continue
        if kind is None:
            errors.append(
                f"{short} ({e.get('qualifiedName')}): no need type for {e['@type']}; "
                f"add it to NEED_TYPES or remove the short name"
            )
            continue
        if kind in id_patterns:
            if not re.fullmatch(id_patterns[kind], short):
                errors.append(f"{short}: a {kind} id matches {id_patterns[kind]}")
                continue
        elif kind in PREFIXES and not re.fullmatch(
            rf"([A-Z][A-Z0-9]*-)?{PREFIXES[kind]}-\d+", short
        ):
            errors.append(
                f"{short}: {KIND_NAMES[kind]}'s id starts with {PREFIXES[kind]}-"
            )
            continue
        if short in needs:
            errors.append(
                f"duplicate id {short}: {needs[short]['qualified_name']} and {e.get('qualifiedName')}"
            )
            continue
        docs = [by_id[d]["body"] for d in refs(e, "documentation") if d in by_id]
        # a use case's `objective { doc /* The driver wants to ... */ }` is its title
        objective = [
            by_id[d]["body"]
            for m in refs(e, "ownedRelationship")
            if kind == "usecase"
            and by_id.get(m, {}).get("@type") == "ObjectiveMembership"
            for r in refs(by_id[m], "ownedElement")
            for d in refs(by_id.get(r, {}), "documentation")
            if d in by_id
        ]
        needs[short] = {
            "id": short,
            "type": kind,
            "domain": DOMAINS[domains[0]] if domains else "",
            "title": " ".join(objective) or e.get("name") or short,
            "content": RST_INLINE.sub(r"\\\1", "\n\n".join(docs)),
            "qualified_name": e.get("qualifiedName") or "",
            "sysml_kind": e["@type"],
            "source": locations.get(short, ""),
            "platform": locations.get(short, "").rpartition(":")[0]
            in set(platform_files),
            "variant": by_id.get(ref(e, "owningRelationship"), {}).get("@type")
            == "VariantMembership",
            "modified": "Trace::Modified" in tags,
            **{link: [] for link in link_types},
        }
        need_of[e["@id"]] = short

    def owning_need(element_id):
        """@id of the nearest owner (excluding the element itself) that is a need."""
        owner = ref(by_id[element_id], "owner")
        while owner and owner in by_id:
            if owner in need_of:
                return owner
            owner = ref(by_id[owner], "owner")
        return None

    def link(link_type, src_id, dst_id, via):
        # Traceability must be visible in the docs: both ends need short names.
        src, dst = need_of.get(src_id), need_of.get(dst_id)
        if src and dst:
            needs[src][link_type].append(dst)
        elif src or dst:
            missing = dst_id if src else src_id
            errors.append(
                f"{via}: {link_type} end {name_of(missing)} has no short name, so the link cannot appear in the docs"
            )

    def all_under(element_id):
        """@ids of every element in the tree below element_id."""
        e = by_id.get(element_id, {})
        found = []
        for child in refs(e, "ownedElement") + refs(e, "ownedRelationship"):
            found += [child, *all_under(child)]
        return found

    def strings_under(element_id):
        """All string literal values in an expression tree, in model order."""
        e = by_id.get(element_id, {})
        found = [e["value"]] if e.get("@type") == "LiteralString" else []
        for child in refs(e, "ownedElement") + refs(e, "ownedRelationship"):
            found += strings_under(child)
        return list(dict.fromkeys(found))

    generals = {}  # element @id -> @ids it specializes (subsetting, redefinition, typing)
    for e in elements:
        t = e["@type"]
        if t == "SatisfyRequirementUsage":
            link(
                "satisfies",
                ref(e, "satisfyingFeature"),
                ref(e, "satisfiedRequirement"),
                "satisfy",
            )
        elif t in ("VerificationCaseDefinition", "VerificationCaseUsage"):
            for req in refs(e, "verifiedRequirement"):
                link("verifies", e["@id"], req, name_of(e["@id"]))
        elif t == "AllocationUsage":
            ends = refs(e, "relatedFeature")
            if len(ends) == 2:
                link("allocated_to", ends[0], ends[1], "allocate")
        elif t in CONNECTORS and e["@id"] in need_of:
            # each end is a port or part; the need is the end itself or its nearest owning need
            for end in refs(e, "relatedFeature"):
                target = end if end in need_of else owning_need(end)
                link("connects", e["@id"], target or end, need_of[e["@id"]])
        elif t == "PerformActionUsage":
            # `perform f;` inside a use case or a feature: f realizes it
            use_case = owning_need(e["@id"])
            if use_case and needs[need_of[use_case]]["type"] in ("usecase", "feature"):
                for sub in refs(e, "ownedReferenceSubsetting"):
                    link(
                        "realizes",
                        ref(by_id[sub], "referencedFeature"),
                        use_case,
                        "perform",
                    )
        elif t == "MetadataUsage":
            types = [by_id.get(m, {}).get("qualifiedName") for m in refs(e, "type")]
            # keyword metadata (`#Feature`) types a need above; it is not a trace link
            field = next(
                (field_metadata[n] for n in types if n in field_metadata), None
            )
            if field:
                annotated = refs(e, "annotatedElement")
                src = need_of.get(annotated[0]) if annotated else None
                values = strings_under(e["@id"])
                if not src or len(values) != 1:
                    errors.append(
                        f"@{types[0]}: needs a short-named element and one string"
                    )
                elif field in RESERVED_FIELDS or field in link_types:
                    errors.append(f"{src}: field {field} is the bridge's own")
                else:
                    needs[src][field] = values[0]
                continue
            link_type = next(
                (trace_metadata[n] for n in types if n in trace_metadata), None
            )
            if not link_type:
                continue
            annotated = refs(e, "annotatedElement")
            src = need_of.get(annotated[0]) if annotated else None
            if not src:
                errors.append(
                    f"@{types[0]} on {name_of(annotated[0]) if annotated else '?'}: annotated element has no short name"
                )
                continue
            if platform_files and needs[src]["platform"]:
                continue  # the platform's own build checks these; outside ids do not exist in an RFQ build
            targets = strings_under(e["@id"])
            if not targets:
                errors.append(f"{src}: @{types[0]} names no need")
            if link_type == "matches" and needs[src]["type"] != "feature":
                errors.append(f"{src}: only a feature matches a customer requirement")
                continue
            if link_type in PARTIAL_LINKS and any(
                by_id.get(c, {}).get("@type") == "LiteralBoolean"
                and by_id[c]["value"] is True
                for c in all_under(e["@id"])
            ):
                needs[src][PARTIAL_LINKS[link_type]] += targets
            needs[src][link_type] += targets
        elif t in SPECIALIZATIONS and not e.get("isImplied"):
            generals.setdefault(ref(e, "specific"), []).append(ref(e, "general"))

    def general_needs(element_id):
        """Needs an element specializes; through a general without a short name (an inherited
        `ref part keyCaps :> Platform::keyCaps`) to the needs that one specializes."""
        found, seen, todo = [], set(), list(generals.get(element_id, []))
        while todo:
            g = todo.pop()
            if g in seen:
                continue
            seen.add(g)
            if g in need_of:
                found.append(need_of[g])
            else:
                todo += generals.get(g, [])
        return found

    for element_id, short in need_of.items():
        needs[short]["specializes"] += [
            g for g in general_needs(element_id) if g != short
        ]

    children = set()
    for element_id, short in need_of.items():
        parent = owning_need(element_id)
        if parent:
            needs[short]["owned_by"].append(need_of[parent])
            # a component owning only ports is still a leaf component
            if needs[need_of[parent]]["type"] == needs[short]["type"]:
                children.add(need_of[parent])

    for need in needs.values():
        for key in link_types:
            # a connector's ends are ordered (source, then target); every other link is a set
            need[key] = (
                list(dict.fromkeys(need[key]))
                if key == "connects"
                else sorted(set(need[key]))
            )
    for need in needs.values():
        # leaf functions/components carry allocation rules (see schemas.json); subsetting a composite inherits its children
        need["leaf"] = not children & {
            i
            for i in closure(needs, need["id"], "specializes")
            if needs[i]["type"] == need["type"]
        }

    for need in needs.values():
        if platform_files and not need["platform"] and need["type"] in DERIVED:
            general = sorted(i for i in need["specializes"] if needs[i]["platform"])
            if general:
                errors.append(
                    f"{need['id']}: specializes the platform's {general[0]}; an RFQ derives its own "
                    f"{KIND_NAMES[need['type']][2:]}s and the platform realizes them at P"
                )
        if need["modified"] and not (
            need["type"] == "physical"
            and any(
                needs[i]["platform"] for i in closure(needs, need["id"], "specializes")
            )
        ):
            errors.append(
                f"{need['id']}: #Modified needs a platform part to modify; a part of its own is new"
            )

    def is_platform(element_id, default):
        """Whether the nearest need owning the element (or the element) is the platform's."""
        nearest = element_id if element_id in need_of else owning_need(element_id)
        return needs[need_of[nearest]]["platform"] if nearest else default

    model = Model(elements)
    for element_id, short in need_of.items():
        if needs[short]["type"] != "constraint":
            continue
        owner = ref(by_id[element_id], "owner")
        for context in model.contexts(element_id):
            if platform_files and is_platform(context, needs[short]["platform"]):
                continue  # the platform's own build evaluates its parts
            where = (
                ""
                if context == owner
                else f" in {need_of.get(context) or name_of(context)}"
            )
            try:
                holds, text, values = model.check(element_id, context)
            except Unevaluable as err:
                if warnings is not None:
                    warnings.append(f"{short}{where}: not evaluated: {err}")
                continue
            if not holds:
                stated = ", ".join(f"{k} = {v}" for k, v in values.items())
                errors.append(f"{short}{where}: does not hold: {text} ({stated})")

    status = reuse(needs)
    for need in needs.values():
        need["reuse"] = status.get(need["id"], "")

    if errors:
        raise BridgeError("\n".join(errors))
    return {"current_version": "", "versions": {"": {"needs": needs}}}


def text_findings(needs):
    """Warnings for system requirement texts: not exactly one `shall`, or a vague term."""
    findings = []
    for need_id, need in sorted(needs.items()):
        if need["type"] != "sysreq":
            continue
        where = f"{need_id} ({need['source']})" if need.get("source") else need_id
        shalls = len(SHALL.findall(need["content"]))
        if shalls != 1:
            findings.append(f"{where}: {shalls} 'shall' in the text; state exactly one")
        for term in sorted(set(VAGUE.findall(need["content"])), key=str.lower):
            findings.append(f"{where}: vague term '{term}'")
    return findings


def load_mapping(path):
    """A project's mapping file (JSON), or {} for the kit's own method; see `convert` and `myst.to_myst`."""
    if not path:
        return {}
    mapping = json.loads(Path(path).read_text())
    known = {
        "keywords",
        "ids",
        "metadata_links",
        "metadata_fields",
        "types",
        "links",
        "fields",
    }
    unknown = sorted(set(mapping) - known)
    if unknown:
        raise BridgeError(f"{path}: unknown keys {', '.join(unknown)}")
    return mapping


def write_needs(
    export_path, out_path, model_files, platform_files=(), warnings=None, mapping=None
):
    elements = json.loads(Path(export_path).read_text())
    if not isinstance(elements, list) or not all(
        "@id" in e and "@type" in e for e in elements
    ):
        raise BridgeError(
            f"{export_path}: not SysML v2 interchange JSON (expected a list of elements with @id/@type)"
        )
    result = convert(
        elements, source_locations(model_files), platform_files, warnings, mapping
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(result, indent=2, sort_keys=True))
    return result["versions"][""]["needs"]
