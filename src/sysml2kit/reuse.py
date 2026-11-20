"""Platform reuse status of each feature, derived from the needs graph."""


def closure(needs, start, link):
    """`start` plus everything reachable through `link`; keeps a visited set."""
    seen, todo = set(), [start]
    while todo:
        n = todo.pop()
        if n in seen or n not in needs:
            continue
        seen.add(n)
        todo += needs[n].get(link, [])
    return seen


def reused_pcs(needs, feature_id):
    """Physical need ids a feature reaches through its (inherited) functions and components."""
    kids = {}
    for n, v in needs.items():
        for parent in v.get("owned_by", []):
            kids.setdefault(parent, []).append(n)

    def below(start):  # start plus its owned_by descendants
        seen, todo = set(), [start]
        while todo:
            n = todo.pop()
            if n not in seen and n in needs:
                seen.add(n)
                todo += kids.get(n, [])
        return seen

    def of_type(ids, type_, leaf=False):
        return {
            i
            for i in ids
            if needs[i]["type"] == type_ and (needs[i]["leaf"] or not leaf)
        }

    functions = set()
    for f in closure(needs, feature_id, "specializes"):
        functions |= of_type(below(f), "function", leaf=True)
    components = set()
    for fn in functions:
        for target in needs[fn].get("allocated_to", []):
            components |= of_type(below(target), "component", leaf=True)
    pcs = set()
    for lc in components:
        for part in below(lc):
            pcs |= of_type(needs[part].get("allocated_to", []), "physical")
    return pcs


def reuse(needs):
    """Map each feature id to platform, variant, modified, new or incomplete."""

    def chain(pc):
        return [needs[i] for i in closure(needs, pc, "specializes")]

    out = {}
    for fid, feature in needs.items():
        if feature["type"] != "feature":
            continue
        pcs = reused_pcs(needs, fid)
        platform = [any(n["platform"] for n in chain(pc)) for pc in pcs]
        if not pcs:
            out[fid] = "incomplete"
        elif all(platform):
            variant = any(n["variant"] for pc in pcs for n in chain(pc))
            out[fid] = "variant" if variant else "platform"
        else:
            out[fid] = "modified" if any(platform) else "new"
    return out
