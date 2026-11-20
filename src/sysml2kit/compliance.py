"""Compliance table: per customer requirement, the features and statements that answer it."""

from .reuse import chain_components, reuse, reused_pcs

WORST_FIRST = ["incomplete", "new", "modified", "variant", "platform"]
GAP = "partial match without a system requirement stating the gap"


def compliance(needs):
    """Return (rows, findings); a row is (crs, title, features, reuse, partial, statements, domains)."""
    status = {
        f: n.get("reuse") or None for f, n in needs.items() if n["type"] == "feature"
    }
    if not all(status.values()):
        computed = reuse(needs)
        status = {f: s or computed[f] for f, s in status.items()}
    rows, findings = [], []
    for crs, need in sorted(needs.items()):
        if need["type"] != "crs":
            continue
        full = [f for f in status if crs in needs[f].get("matches", [])]
        part = [f for f in status if crs in needs[f].get("partial_matches", [])]
        features = sorted(set(full + part))
        statements = sorted(
            (c, n.get("compliance", ""))
            for c, n in needs.items()
            if n["type"] == "cst" and crs in n.get("answers", [])
        )
        pcs = set().union(*(reused_pcs(needs, f) for f in features))
        domains = sorted({needs[p]["domain"] for p in pcs if needs[p].get("domain")})
        worst = min((status[f] for f in features), key=WORST_FIRST.index, default="")
        rows.append(
            (crs, need["title"], features, worst, bool(part), statements, domains)
        )
        if not features and not statements:
            findings.append(f"{crs}: not answered")
        for f in features:
            if status[f] == "incomplete":
                findings.append(
                    f"{crs}: matched, but its chain reaches no physical component"
                )
                break
        if any(not _gap_stated(needs, crs, f) for f in part):
            findings.append(f"{crs}: {GAP}")
    return rows, findings


def _gap_stated(needs, crs, feature):
    """An SR satisfying the CRS is itself satisfied by a component in the feature's chain."""
    chain = chain_components(needs, feature)
    return any(
        n["type"] == "sysreq"
        and crs in n.get("satisfies", [])
        and any(sr in needs[c].get("satisfies", []) for c in chain)
        for sr, n in needs.items()
    )


def table_md(rows):
    """MyST Markdown table, every need linked with the need role."""

    def cell(text):
        return str(text).replace("|", "\\|")

    def links(ids):
        return ", ".join(f"{{need}}`{i}`" for i in ids)

    def statement_links(statements):
        return ", ".join(f"{{need}}`{i}` ({value})" for i, value in statements)

    out = [
        "| Requirement | Title | Features | Reuse | Partial | Statements | Domains |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for crs, title, features, worst, partial, statements, domains in rows:
        out.append(
            f"| {links([crs])} | {cell(title)} | {links(features)} | {worst} "
            f"| {'yes' if partial else ''} | {statement_links(statements)} | {cell(', '.join(domains))} |"
        )
    return "\n".join(out) + "\n"
