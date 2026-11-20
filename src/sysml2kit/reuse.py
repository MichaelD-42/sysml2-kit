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


def function_pcs(needs, feature_id):
    """Per leaf function of a feature (own or inherited): the physical need ids it reaches."""
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
    out = {}
    for fn in functions:
        components = set()
        for target in needs[fn].get("allocated_to", []):
            # a composite target keeps its own allocation; its leaf descendants add theirs
            components |= of_type([target], "component") | of_type(
                below(target), "component", leaf=True
            )
        pcs = set()
        for lc in components:
            for part in below(lc):
                for pc in of_type(needs[part].get("allocated_to", []), "physical"):
                    pcs |= of_type(
                        below(pc), "physical"
                    )  # an assembly reaches its parts
        out[fn] = pcs
    return out


def reused_pcs(needs, feature_id):
    """Physical need ids a feature reaches through its (inherited) functions and components."""
    return set().union(*function_pcs(needs, feature_id).values())


def reuse(needs):
    """Map each feature id to platform, variant, modified, new or incomplete."""

    def chain(pc):
        return [needs[i] for i in closure(needs, pc, "specializes")]

    out = {}
    for fid, feature in needs.items():
        if feature["type"] != "feature":
            continue
        per_function = function_pcs(needs, fid).values()
        pcs = set().union(*per_function)
        platform = [any(n["platform"] for n in chain(pc)) for pc in pcs]
        if not pcs or not all(per_function):
            out[fid] = "incomplete"
        elif all(platform):
            variant = any(n["variant"] for pc in pcs for n in chain(pc))
            out[fid] = "variant" if variant else "platform"
        else:
            out[fid] = "modified" if any(platform) else "new"
    return out
