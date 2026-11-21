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


def descendants(needs, into=lambda need: True):
    """Return below(start): start plus its owned_by descendants, entering only children `into` accepts."""
    kids = {}
    for n, v in needs.items():
        for parent in v.get("owned_by", []) if into(v) else []:
            kids.setdefault(parent, []).append(n)

    def below(start):
        seen, todo = set(), [start]
        while todo:
            n = todo.pop()
            if n not in seen and n in needs:
                seen.add(n)
                todo += kids.get(n, [])
        return seen

    return below


def function_components(needs, feature_id):
    """Per leaf function of a feature (own or inherited): the components it is allocated to."""
    below = descendants(needs)

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
        out[fn] = components
    return out


def chain_components(needs, feature_id):
    """Components in a feature's chain: those its leaf functions reach, plus their descendants."""
    below = descendants(needs)
    return set().union(
        *(
            below(lc)
            for lcs in function_components(needs, feature_id).values()
            for lc in lcs
        )
    )


def _function_reach(needs, feature_id):
    """Per leaf function: (physical need ids reached, variations reached without a selection)."""
    below = descendants(needs)
    # variants are reached only by allocation to one, or to a part specializing one
    assembly = descendants(needs, lambda n: not n.get("variant"))
    variations = {p for n in needs.values() if n.get("variant") for p in n["owned_by"]}
    out = {}
    for fn, components in function_components(needs, feature_id).items():
        pcs = set()
        for lc in components:
            for part in below(lc):
                for pc in needs[part].get("allocated_to", []):
                    if needs[pc]["type"] == "physical":
                        # an assembly reaches its parts
                        pcs |= {
                            i for i in assembly(pc) if needs[i]["type"] == "physical"
                        }
        out[fn] = (pcs, pcs & variations)
    return out


def function_pcs(needs, feature_id):
    """Per leaf function of a feature (own or inherited): the physical need ids it reaches.

    A function reaching a variation without a selected variant reaches none."""
    return {
        fn: set() if unselected else pcs
        for fn, (pcs, unselected) in _function_reach(needs, feature_id).items()
    }


def unselected_variations(needs, feature_id):
    """Variations a feature's functions reach without a selected variant."""
    return set().union(*(u for _, u in _function_reach(needs, feature_id).values()))


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
