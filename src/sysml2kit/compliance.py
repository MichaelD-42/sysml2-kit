"""Compliance table: per customer requirement, the features and statements that answer it."""

from .reuse import (
    WORST_FIRST,
    chain_components,
    closure,
    component_reuse,
    constraint_reuse,
    part_reuse,
    reuse,
    reused_pcs,
    unselected_variations,
)

MET = "partial match without a system requirement stating what is met"
NO_PARTIAL_CST = "partial, but no partial compliance statement answers it"
# classes a constraint can answer, and classes that must be verified
CONSTRAINED = ("non-functional", "constraint")
TECHNICAL = ("functional", *CONSTRAINED)
NOT_VERIFIED = "not verified (no acceptance test, no implemented CTR applying to it)"


def compliance(needs):
    """Return (rows, findings); a row is (crs, title, class_, features, reuse, partial, statements, domains, constraints)."""
    status = {
        f: n.get("reuse") or None for f, n in needs.items() if n["type"] == "feature"
    }
    if not all(status.values()):
        computed = reuse(needs)
        status = {f: s or computed[f] for f, s in status.items()}
    ctrs = ctr_rows(needs)
    rows, findings = [], []
    for crs, need in sorted(needs.items()):
        if need["type"] != "crs":
            continue
        class_ = need.get("class", "")
        full = [f for f in status if crs in needs[f].get("matches", [])]
        part = [f for f in status if crs in needs[f].get("partial_matches", [])]
        features = sorted(set(full + part))
        constraints = sorted(
            c
            for c, n in needs.items()
            if n["type"] == "constraint" and crs in n.get("satisfies", [])
        )
        partial_cons = [
            c for c in constraints if crs in needs[c].get("partial_satisfies", [])
        ]
        statements = _statements(needs, crs)
        pcs = set().union(*(reused_pcs(needs, f) for f in features))
        pcs |= {
            o for c in constraints for o in needs[c].get("owned_by", []) if o in needs
        }
        domains = sorted({needs[p]["domain"] for p in pcs if needs[p].get("domain")})
        worst = min(
            [status[f] for f in features]
            + [constraint_reuse(needs, c) for c in constraints],
            key=WORST_FIRST.index,
            default="",
        )
        rows.append(
            (
                crs,
                need["title"],
                class_,
                features,
                worst,
                bool(part or partial_cons),
                statements,
                domains,
                constraints,
            )
        )
        if class_ == "information":
            continue
        # a textual SR answers what the model cannot express as a constraint
        satisfiers = constraints or any(
            n["type"] == "sysreq" and crs in n.get("satisfies", [])
            for n in needs.values()
        )
        answered = features or statements or (satisfiers and class_ in CONSTRAINED)
        findings += _answer_findings(crs, need, answered, statements)
        for f in features:
            if status[f] == "incomplete":
                findings.append(
                    f"{crs}: matched, but its chain reaches no physical component"
                )
                break
        for v in sorted(
            set().union(*(unselected_variations(needs, f) for f in features))
        ):
            findings.append(f"{crs}: variation {v} reached without a selected variant")
        if any(not _met_stated(needs, crs, f) for f in part):
            findings.append(f"{crs}: {MET}")
        elif features:
            findings += [
                f"{crs}: system requirement {sr} is satisfied outside the chain of its matching features"
                for sr in _satisfied_outside(needs, crs, features)
            ]
        # what is met is in the model (a constraint, or an SR in the chain); the gap goes to the customer
        if (part or partial_cons) and ("partial" not in dict(statements).values()):
            findings.append(f"{crs}: {NO_PARTIAL_CST}")
    implemented = {c for c, *_, tests, _ in ctrs if tests}
    for req, need in sorted(needs.items()):
        if (
            need["type"] in ("crs", "prq")
            and not need.get("scope")
            and need.get("class") in TECHNICAL
            and not any(
                n["type"] == "acctest" and req in n.get("verifies", [])
                for n in needs.values()
            )
            and not any(req in needs[c].get("applies_to", []) for c in implemented)
        ):
            findings.append(f"{req}: {NOT_VERIFIED}")
    for ctr, *_, tests, statements in ctrs:
        if needs[ctr].get("scope"):
            # a scoped CTR is answered by a CST only, even when a test implements it
            findings += _answer_findings(ctr, needs[ctr], statements, statements)
        elif not tests:
            findings.append(f"{ctr}: not implemented")
    return rows, findings


def ctr_rows(needs):
    """A row per customer test requirement: (ctr, title, purpose, method, implemented_by, statements)."""
    return [
        (
            ctr,
            need["title"],
            need.get("purpose", ""),
            need.get("method", ""),
            sorted(
                t
                for t, n in needs.items()
                if n["type"] in ("systest", "acctest")
                and ctr in n.get("implements", [])
            ),
            _statements(needs, ctr),
        )
        for ctr, need in sorted(needs.items())
        if need["type"] == "ctr"
    ]


def _statements(needs, need_id):
    return sorted(
        (c, n.get("compliance", ""))
        for c, n in needs.items()
        if n["type"] == "cst" and need_id in n.get("answers", [])
    )


def _answer_findings(need_id, need, answered, statements):
    """Not answered at all, or not offered with a statement other than not-comply."""
    if not answered:
        return [f"{need_id}: not answered"]
    if need.get("scope") == "not-offered" and (
        not statements or any(value != "not-comply" for _, value in statements)
    ):
        return [f"{need_id}: not offered, but its statement is not not-comply"]
    return []


def _met_stated(needs, crs, feature):
    """An SR satisfying the CRS is itself satisfied by a component in the feature's chain."""
    chain = chain_components(needs, feature)
    return any(
        n["type"] == "sysreq"
        and crs in n.get("satisfies", [])
        and any(sr in needs[c].get("satisfies", []) for c in chain)
        for sr, n in needs.items()
    )


def _satisfied_outside(needs, crs, features):
    """SRs satisfying the CRS whose satisfying components all lie outside every matching feature's chain."""
    chain = set().union(*(chain_components(needs, f) for f in features))
    satisfiers = {}
    for c, n in needs.items():
        for sr in n.get("satisfies", []):
            satisfiers.setdefault(sr, set()).add(c)
    return sorted(
        sr
        for sr, n in needs.items()
        if n["type"] == "sysreq"
        and crs in n.get("satisfies", [])
        and satisfiers.get(sr)
        and not satisfiers[sr] & chain
    )


def realization_rows(needs):
    """Per project logical component: (id, title, degree, [(part id, title, note)]) for the parts it is allocated to."""

    def note(pc):
        if not needs[pc]["platform"] and needs[pc].get("modified"):
            prefix = "modified "
        elif part_reuse(needs, pc) == "new":
            return "new"
        else:
            prefix = ""
        platform = {
            i for i in closure(needs, pc, "specializes") - {pc} if needs[i]["platform"]
        }
        # a selected variant names the part; its variation would only repeat it
        owners = {o for i in platform if needs[i].get("variant") for o in needs[i]["owned_by"]}
        return prefix + ", ".join(sorted(platform - owners))

    return [
        (
            lc,
            n["title"],
            component_reuse(needs, lc),
            [
                (pc, needs[pc]["title"], note(pc))
                for pc in sorted(n.get("allocated_to", []))
                if needs.get(pc, {}).get("type") == "physical"
            ],
        )
        for lc, n in sorted(needs.items())
        if n["type"] == "component" and not n["platform"]
    ]


def table_md(rows, ctrs=(), realization=()):
    """MyST Markdown tables (requirements, CTRs if any, realization if any), every need linked with the need role."""

    def cell(text):
        return str(text).replace("|", "\\|")

    def links(ids):
        return ", ".join(f"{{need}}`{i}`" for i in ids)

    def statement_links(statements):
        return ", ".join(f"{{need}}`{i}` ({value})" for i, value in statements)

    out = [
        "| Requirement | Title | Class | Features | Reuse | Partial | Statements | Domains | Constraints |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for crs, title, class_, features, worst, partial, statements, domains, cons in rows:
        out.append(
            f"| {links([crs])} | {cell(title)} | {class_} | {links(features)} | {worst} "
            f"| {'yes' if partial else ''} | {statement_links(statements)} "
            f"| {cell(', '.join(domains))} | {links(cons)} |"
        )
    if ctrs:
        out += [
            "",
            "| Customer test requirement | Title | Purpose | Method | Implemented by | Statements |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for ctr, title, purpose, method, tests, statements in ctrs:
            out.append(
                f"| {links([ctr])} | {cell(title)} | {purpose} | {method} "
                f"| {links(tests)} | {statement_links(statements)} |"
            )
    if realization:
        out += [
            "",
            "| Component | Title | Degree | Physical parts |",
            "| --- | --- | --- | --- |",
        ]
        for lc, title, degree, parts in realization:
            cells = ", ".join(
                f"{{need}}`{pc}` {cell(name)}" + (f" ({n})" if n else "")
                for pc, name, n in parts
            )
            out.append(f"| {links([lc])} | {cell(title)} | {degree} | {cells} |")
    return "\n".join(out) + "\n"
