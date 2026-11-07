"""SysML v2 interchange JSON (`sysml export`) -> sphinx-needs needs.json.

Every element with a declared short name becomes a need whose id is that short name.
Links inside the model come from native SysML; links to needs written outside the model
(e.g. customer requirements in RST) come from `Trace` metadata (see templates/model/trace.sysml).
"""

import json
import re
from pathlib import Path

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
    "VerificationCaseDefinition": "systest",
    "VerificationCaseUsage": "systest",
}
LINK_TYPES = ("satisfies", "realizes", "verifies", "allocated_to", "owned_by")
# Trace metadata definition (qualified, so another library's `Satisfies` is not a trace link) -> link type
TRACE_METADATA = {
    "Trace::Satisfies": "satisfies",
    "Trace::Realizes": "realizes",
    "Trace::Verifies": "verifies",
}
COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
# reStructuredText inline markup; doc text is plain text, so these are escaped
RST_INLINE = re.compile(r"([\\*`_|])")


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
            lambda m: re.sub(r"[^\n]", " ", m.group()), Path(path).read_text()
        )
        for lineno, line in enumerate(text.splitlines(), 1):
            for quoted, plain in re.findall(r"<'([^']+)'>|<([A-Za-z_][\w-]*)>", line):
                locations.setdefault(quoted or plain, f"{path}:{lineno}")
    return locations


def convert(elements, locations):
    by_id = {e["@id"]: e for e in elements}
    errors = []
    needs = {}
    need_of = {}  # element @id -> need id

    def name_of(element_id):
        e = by_id.get(element_id, {})
        return e.get("qualifiedName") or e.get("name") or element_id

    for e in elements:
        # declared, not derived: implicit features (e.g. allocation ends) inherit the shortName they reference
        short = e.get("declaredShortName")
        if not short:
            continue
        kind = NEED_TYPES.get(e["@type"])
        if kind is None:
            errors.append(
                f"{short} ({e.get('qualifiedName')}): no need type for {e['@type']}; "
                f"add it to NEED_TYPES or remove the short name"
            )
            continue
        if short in needs:
            errors.append(
                f"duplicate id {short}: {needs[short]['qualified_name']} and {e.get('qualifiedName')}"
            )
            continue
        docs = [by_id[d]["body"] for d in refs(e, "documentation") if d in by_id]
        needs[short] = {
            "id": short,
            "type": kind,
            "title": e.get("name") or short,
            "content": RST_INLINE.sub(r"\\\1", "\n\n".join(docs)),
            "qualified_name": e.get("qualifiedName") or "",
            "sysml_kind": e["@type"],
            "source": locations.get(short, ""),
            **{link: [] for link in LINK_TYPES},
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

    def strings_under(element_id):
        """All string literal values in an expression tree, in model order."""
        e = by_id.get(element_id, {})
        found = [e["value"]] if e.get("@type") == "LiteralString" else []
        for child in refs(e, "ownedElement") + refs(e, "ownedRelationship"):
            found += strings_under(child)
        return list(dict.fromkeys(found))

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
        elif t == "PerformActionUsage":
            # `perform f;` inside a use case: the function realizes the use case
            use_case = owning_need(e["@id"])
            if use_case and needs[need_of[use_case]]["type"] == "usecase":
                for sub in refs(e, "ownedReferenceSubsetting"):
                    link(
                        "realizes",
                        ref(by_id[sub], "referencedFeature"),
                        use_case,
                        "perform",
                    )
        elif t == "MetadataUsage":
            types = [by_id.get(m, {}).get("qualifiedName") for m in refs(e, "type")]
            link_type = next(
                (TRACE_METADATA[n] for n in types if n in TRACE_METADATA), None
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
            targets = strings_under(e["@id"])
            if not targets:
                errors.append(f"{src}: @{types[0]} names no need")
            needs[src][link_type] += targets

    children = set()
    for element_id, short in need_of.items():
        parent = owning_need(element_id)
        if parent:
            needs[short]["owned_by"].append(need_of[parent])
            # a component owning only ports is still a leaf component
            if needs[need_of[parent]]["type"] == needs[short]["type"]:
                children.add(need_of[parent])

    for need in needs.values():
        for key in LINK_TYPES:
            need[key] = sorted(set(need[key]))
        # leaf functions/components carry allocation rules (see schemas.json)
        need["leaf"] = need["id"] not in children

    if errors:
        raise BridgeError("\n".join(errors))
    return {"current_version": "", "versions": {"": {"needs": needs}}}


def write_needs(export_path, out_path, model_files):
    elements = json.loads(Path(export_path).read_text())
    if not isinstance(elements, list) or not all(
        "@id" in e and "@type" in e for e in elements
    ):
        raise BridgeError(
            f"{export_path}: not SysML v2 interchange JSON (expected a list of elements with @id/@type)"
        )
    result = convert(elements, source_locations(model_files))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(result, indent=2, sort_keys=True))
    return len(result["versions"][""]["needs"])
