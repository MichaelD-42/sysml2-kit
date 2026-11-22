"""Realization degree of each feature and logical component, derived from the needs graph."""

WORST_FIRST = ["incomplete", "new", "partial", "full"]


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


def _reach_context(needs):
    below = descendants(needs)
    # variants are reached only by allocation to one, or to a part specializing one
    assembly = descendants(needs, lambda n: not n.get("variant"))
    variations = {p for n in needs.values() if n.get("variant") for p in n["owned_by"]}
    # the project selects a platform variant by allocating to it or subsetting it; the platform's own allocations offer them all
    selected = {
        v
        for n, need in needs.items()
        if not need["platform"]
        for v in [*need.get("allocated_to", []), *closure(needs, n, "specializes")]
    }
    return below, assembly, variations, selected


def _component_reach(needs, lc, context):
    """(physical need ids a component and its descendants reach, variations reached without a selected variant)."""
    below, assembly, variations, selected = context
    pcs, offered = set(), set()
    for part in below(lc):
        for pc in needs[part].get("allocated_to", []):
            if needs[pc]["platform"] and needs[pc]["variant"] and pc not in selected:
                offered |= set(needs[pc]["owned_by"]) & variations
            elif needs[pc]["type"] == "physical":
                # an assembly reaches its parts
                pcs |= {i for i in assembly(pc) if needs[i]["type"] == "physical"}
    unselected = set()
    for pc in pcs:
        # a part that is or specializes a variation, but no variant of it, selects nothing
        chain = closure(needs, pc, "specializes")
        if not any(needs[i]["variant"] for i in chain):
            unselected |= chain & variations
    covered = {
        o
        for pc in pcs
        for i in closure(needs, pc, "specializes")
        if needs[i]["variant"]
        for o in needs[i]["owned_by"]
    }
    return pcs, unselected | offered - covered


def _function_reach(needs, feature_id, context=None):
    """Per leaf function: (physical need ids reached, variations reached without a selection)."""
    context = context or _reach_context(needs)
    out = {}
    for fn, components in function_components(needs, feature_id).items():
        pcs, unselected = set(), set()
        for lc in components:
            p, u = _component_reach(needs, lc, context)
            pcs |= p
            unselected |= u
        out[fn] = (pcs, unselected)
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


def component_pcs(needs, lc, context=None):
    """Physical need ids a component reaches; none when it reaches a variation without a selected variant."""
    pcs, unselected = _component_reach(needs, lc, context or _reach_context(needs))
    return set() if unselected else pcs


def component_reuse(needs, lc, context=None):
    """full, partial, new or incomplete: a leaf by its parts, a composite by its leaves (incomplete if one is)."""
    context = context or _reach_context(needs)
    if not needs[lc]["leaf"]:
        leaves = [
            i
            for i in context[0](lc)
            if i != lc and needs[i]["type"] == "component" and needs[i]["leaf"]
        ]
        degrees = {component_reuse(needs, i, context) for i in leaves}
        return "incomplete" if not degrees or "incomplete" in degrees else _combine(degrees)
    pcs = component_pcs(needs, lc, context)
    return _combine({part_reuse(needs, p) for p in pcs}) if pcs else "incomplete"


def reuse(needs):
    """Map each feature and logical component id to full, partial, new or incomplete."""
    context = _reach_context(needs)
    out = {}
    for fid, n in needs.items():
        if n["type"] == "component":
            out[fid] = component_reuse(needs, fid, context)
        elif n["type"] == "feature":
            reach = _function_reach(needs, fid, context).values()
            if not reach or any(u or not p for p, u in reach):
                out[fid] = "incomplete"
            else:
                out[fid] = _combine(
                    {part_reuse(needs, pc) for p, _ in reach for pc in p}
                )
    return out


def constraint_reuse(needs, con_id):
    """full, partial or new by the part owning the constraint; incomplete without one."""
    owners = [
        o
        for o in needs[con_id].get("owned_by", [])
        if o in needs and needs[o]["type"] in ("physical", "component")
    ]
    if not owners:
        return "incomplete"
    return _combine({part_reuse(needs, o) for o in owners})


def part_reuse(needs, part):
    """full, partial or new by the part's specializations and #Modified; an assembly (no domain) adds its parts'."""
    chain = closure(needs, part, "specializes")
    own = set()
    if needs[part].get("modified"):
        own.add("partial")
    elif any(needs[i]["platform"] for i in chain):
        own.add("full")
    # an assembly has the parts it owns and those it inherits from project parts it specializes
    owners = {i for i in chain if not needs[i]["platform"]}
    parts = (
        [
            i
            for i, n in needs.items()
            if owners & set(n["owned_by"]) and n["type"] == "physical"
        ]
        if needs[part]["type"] == "physical" and not needs[part].get("domain")
        else []
    )
    # an assembly that subsets nothing is only an arrangement: its parts decide
    return _combine(own | {part_reuse(needs, p) for p in parts} or {"new"})


def _combine(statuses):
    if statuses in ({"new"}, {"full"}):
        return next(iter(statuses))
    return "partial"

