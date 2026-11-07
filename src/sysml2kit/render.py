"""SVG renderers for what the SysML diagram tool does not draw: use case diagrams and the RFLP trace graph."""

from xml.sax.saxutils import escape

FONT = 'font-family="Arial, Helvetica, sans-serif" font-size="12"'
CHAR_W = 7  # approximate width of one 12px Arial character
STYLE = """<style>
.box { fill: #ffffff; stroke: #333333; stroke-width: 1; }
.line { fill: none; stroke: #333333; stroke-width: 1; }
.muted { fill: #555555; font-size: 10px; }
.title { font-weight: bold; }
</style>"""


def _svg(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" {FONT}>\n{STYLE}\n'
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def _text(x, y, text, cls="", anchor="middle"):
    c = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}"{c}>{escape(text)}</text>'
    )


# --- use case diagram -------------------------------------------------------------------------


def use_cases(elements):
    """[(subject title, [(use case need id, name, [actor names])])] from SysML interchange JSON.

    Use cases are grouped by subject name and type: untyped `subject vehicle;` in several use
    cases is one subject, while `vehicle : Car` and `vehicle : Truck` are two, titled with their type.
    """
    by_id = {e["@id"]: e for e in elements}

    def member(membership):
        target = membership.get("ownedMemberElement") or membership.get(
            "ownedRelatedElement"
        )
        target = target[0] if isinstance(target, list) and target else target
        return by_id.get(target["@id"], {}) if target else {}

    def member_name(membership):
        return member(membership).get("name")

    def subject_key(membership):
        subject = member(membership)
        types = subject.get("type") or []
        types = types if isinstance(types, list) else [types]
        typed = [by_id[t["@id"]] for t in types if t["@id"] in by_id]
        return subject.get("name"), (
            typed[0].get("qualifiedName") or typed[0].get("name") if typed else None
        )

    subjects = {}
    for e in elements:
        if e["@type"] not in ("UseCaseUsage", "UseCaseDefinition"):
            continue
        memberships = [
            by_id[m["@id"]] for m in e.get("ownedMembership", []) if m["@id"] in by_id
        ]
        name, type_ = next(
            (subject_key(m) for m in memberships if m["@type"] == "SubjectMembership"),
            (None, None),
        )
        subject = (name or "system", type_)
        actors = [
            member_name(m) for m in memberships if m["@type"] == "ActorMembership"
        ]
        subjects.setdefault(subject, []).append(
            # a use case without a short name is still drawn, with an empty id line
            (
                e.get("declaredShortName") or "",
                e.get("name") or "",
                [a for a in actors if a],
            )
        )
    names = [name for name, _ in subjects]
    # the type goes into the title only where the name alone would merge two subjects
    return sorted(
        (f"{name} : {type_}" if type_ and names.count(name) > 1 else name, sorted(ucs))
        for (name, type_), ucs in subjects.items()
    )


def use_case_svg(subject, cases):
    """One diagram: actors left, the subject boundary with its use cases right, associations between."""
    actors = list(dict.fromkeys(a for _, _, acts in cases for a in acts))
    oval_w = max(160, max(CHAR_W * max(len(n), len(i) + 6) + 40 for i, n, _ in cases))
    oval_h, gap = 54, 24
    actor_x = max(
        70, CHAR_W * max((len(a) for a in actors), default=0) / 2 + 10
    )  # long names stay inside
    box_x, box_y = actor_x + 100, 20
    box_w, box_h = oval_w + 80, 50 + len(cases) * (oval_h + gap)
    width, height = box_x + box_w + 20, max(box_y + box_h + 20, 60 + len(actors) * 110)
    body = [
        f'<rect class="box" x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}"/>',
        _text(box_x + box_w / 2, box_y + 22, subject, "title"),
    ]
    centers = []  # by position: ids may be empty
    for k, (need_id, name, _) in enumerate(cases):
        cx, cy = box_x + box_w / 2, box_y + 50 + oval_h / 2 + k * (oval_h + gap)
        centers.append((cx, cy))
        body += [
            f'<ellipse class="box" cx="{cx:.0f}" cy="{cy:.0f}" rx="{oval_w / 2:.0f}" ry="{oval_h / 2}"/>',
            _text(cx, cy - 2, name, "title"),
            _text(cx, cy + 14, need_id, "muted"),
        ]
    step = (height - 40) / max(len(actors), 1)
    for k, actor in enumerate(actors):
        x, y = actor_x, 20 + step * k + step / 2 - 30  # head center
        body += [
            f'<circle class="box" cx="{x}" cy="{y:.0f}" r="9"/>',
            f'<path class="line" d="M{x},{y + 9:.0f} v22 M{x - 14},{y + 16:.0f} h28 M{x},{y + 31:.0f} l-12,18 M{x},{y + 31:.0f} l12,18"/>',
            _text(x, y + 66, actor),
        ]
        for (_, _, acts), (cx, cy) in zip(cases, centers):
            if actor in acts:
                body.append(
                    f'<path class="line" d="M{x + 16},{y + 20:.0f} L{cx - oval_w / 2:.0f},{cy:.0f}"/>'
                )
    return _svg(width, round(height), body)


# --- RFLP trace graph -------------------------------------------------------------------------

COLUMNS = ["crs", "usecase", "sysreq", "function", "component", "systest", "acctest"]
COLUMN_TITLES = {
    "crs": "Customer req.",
    "usecase": "Use cases",
    "sysreq": "System req.",
    "function": "Functions",
    "component": "Logical components",
    "systest": "System tests",
    "acctest": "Acceptance tests",
}
EDGES = {
    "satisfies": "#1f6fb2",
    "realizes": "#2e8b57",
    "verifies": "#b5651d",
    "allocated_to": "#7a4fb0",
}


def trace_svg(needs):
    """Trace graph of the needs (id -> need dict, as in needs.json) across the RFLP columns."""
    box_w, box_h, col_gap, row_gap, top = 170, 36, 60, 18, 60
    columns = [c for c in COLUMNS if any(n["type"] == c for n in needs.values())]
    pos = {}
    body = []
    for col, need_type in enumerate(columns):
        x = 20 + col * (box_w + col_gap)
        body.append(_text(x + box_w / 2, 30, COLUMN_TITLES[need_type], "title"))
        for row, need_id in enumerate(
            sorted(i for i, n in needs.items() if n["type"] == need_type)
        ):
            y = top + row * (box_h + row_gap)
            pos[need_id] = (x, y)
            title = needs[need_id].get("title", "")
            max_chars = (box_w - 10) // CHAR_W
            title = title if len(title) <= max_chars else title[: max_chars - 1] + "…"
            body += [
                f'<rect class="box" x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="3"/>',
                _text(x + 6, y + 14, need_id, "muted", "start"),
                _text(x + 6, y + 29, title, "", "start"),
            ]
    edges = []
    for src, need in needs.items():
        for link, color in EDGES.items():
            for dst in need.get(link) or []:
                if src in pos and dst in pos:
                    (sx, sy), (dx, dy) = pos[src], pos[dst]
                    sy, dy = sy + box_h / 2, dy + box_h / 2
                    if sx == dx:  # same column: loop out to the right
                        x = sx + box_w
                        d = f"M{x},{sy:.0f} C{x + 30},{sy:.0f} {x + 30},{dy:.0f} {x},{dy:.0f}"
                    else:
                        x1, x2 = (sx + box_w, dx) if sx < dx else (sx, dx + box_w)
                        if (
                            abs(dx - sx) == box_w + col_gap
                        ):  # adjacent columns: one curve
                            mid = (x1 + x2) / 2
                            d = f"M{x1},{sy:.0f} C{mid:.0f},{sy:.0f} {mid:.0f},{dy:.0f} {x2},{dy:.0f}"
                        else:
                            # skip columns along the free strip above the target row, never under a box
                            # a per-edge offset keeps parallel edges apart instead of merging into a bus
                            spread = (len(edges) % 5 - 2) * 3
                            step = (col_gap / 2 + spread) * (1 if sx < dx else -1)
                            lane = dy - box_h / 2 - row_gap / 2 + spread
                            d = (
                                f"M{x1},{sy:.0f} H{x1 + step:.0f} V{lane:.0f} "
                                f"H{x2 - step:.0f} V{dy:.0f} H{x2}"
                            )
                    edges.append(f'<path class="line" style="stroke:{color}" d="{d}"/>')
    rows = max(
        (sum(n["type"] == c for n in needs.values()) for c in columns), default=0
    )
    height = top + rows * (box_h + row_gap) + 50
    width = max(20 + len(columns) * (box_w + col_gap), 520)
    legend = [
        f'<path class="line" style="stroke:{color}" d="M{20 + k * 130},{height - 22} h24"/>'
        + _text(20 + k * 130 + 30, height - 18, link.replace("_", " "), "", "start")
        for k, (link, color) in enumerate(EDGES.items())
    ]
    return _svg(width, height, edges + body + legend)
