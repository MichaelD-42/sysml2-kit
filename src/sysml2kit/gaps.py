"""RFLP rule violations from a `sphinx-build -b needs` run, by layer, with where to fix them."""

LAYERS = "RFLV?"  # ? = a rule not in RULE_LAYERS (one a project added); always reported
# rule id (docs/schemas.json) -> the layer it gates (rflp-method structure.md)
RULE_LAYERS = {
    "crs-satisfied": "R",
    "usecase-realizes": "R",
    "sysreq-satisfies": "R",
    "usecase-realized": "F",
    "function-allocated": "L",
    "component-used": "L",
    "sysreq-satisfied": "L",
    "systest-verifies": "V",
    "acctest-verifies": "V",
    "sysreq-verified": "V",
    "usecase-verified": "V",
    "crs-verified": "V",
}


def gaps(violations, needs, layer=None):
    """[(layer, rule, need id, location, message)] from schema_violations.json and the needs.

    With a layer, only rules gating that layer or an earlier one (later layers are expected to fail),
    and rules of unknown layer.
    """
    found = []
    for need_id, warnings in violations.get("validation_warnings", {}).items():
        need = needs.get(need_id, {})
        where = need.get("source") or (
            f"docs/{need['docname']}.rst:{need.get('lineno')}"
            if need.get("docname")
            else ""
        )
        for w in warnings:
            rule = w["details"]["schema_path"].split("[")[0]
            rule_layer = RULE_LAYERS.get(rule, "?")
            if (
                layer
                and rule_layer != "?"
                and LAYERS.index(rule_layer) > LAYERS.index(layer)
            ):
                continue
            found.append(
                (rule_layer, rule, need_id, where, w["details"]["validation_msg"])
            )
    return sorted(found, key=lambda g: (LAYERS.index(g[0]), g[1], g[2]))
