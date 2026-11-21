# Explorer: requirement and RFLP trees, V-model view — short design

## Intent

The demo must show the link between the sphinx-needs (textual requirements) and the SysML model, not only inside the trace view. The left column gets two navigation trees in place of the package tree, and a V-model view shows the left leg (requirements down to physical parts) against the right leg (tests and results) for the RFQ.

## Approaches

- Trees replace the package tree (chosen, owner approved): the package tree follows files, not the method; Composition and the breadcrumb cover file structure.
- Keep the package tree as a third collapsed section: rejected for now, more clutter than value in a demo.
- V-model as a new view kind laid out by a dedicated pure layout function (chosen, my call) rather than through ELK: the V's geometry is fixed (levels and legs), ELK's layered layout cannot hold it.

## Requirements tree (top)

Groups by need document section (`sections[0]` of the need, e.g. "Customer requirements", "Compliance statements", "Acceptance tests"); system requirements (model RequirementUsages with a need id) form a "System requirements" group. Each requirement expands to its links, labelled by kind and direction: satisfied by, realized by, matched by (partial marked), answered by, verified by, requires, and outgoing satisfies / verifies for SRs and tests. Every linked element is a focus link.

## Model tree (below)

RFLP chain: use case → features it performs → functions owned by the feature (sub-functions nested) → logical components each leaf function is allocated to → physical components each logical component is allocated to. A node reached twice appears twice. Rows show id, name, ME/EE/SW colour on physical parts, a platform marker. Platform use cases and features (imported) appear after the project's own.

## Cross-highlight

The focus marks its rows in both trees; additionally every requirement row linked to the focus (one need-link hop) and every model row the focused requirement links to get a secondary mark. Both trees open the ancestors of marked rows.

## V-model view (my calls)

New view kind `vmodel`. Levels top to bottom, left leg → right leg:

1. Customer requirements (CRS) ↔ acceptance tests (ATC) and their results
2. System: use cases and system requirements (UC, SR) ↔ system tests (STC) and their results
3. Function: features and functions (FEAT, F) ↔ — (no tests at this level in the examples; shown empty)
4. Logical components (LC) ↔ — (integration tests; empty)
5. Bottom: physical components (PC), the realisation

Edges: down the left leg the need links between adjacent levels (satisfies, realizes, matches, allocated_to); across, `VERIFIES` from a test to the left-leg element, and `TESTS` from a result to its test, with the result's outcome (pass/fail) as colour. Focus: none (whole RFQ, project elements only) or a CRS (its chain only, reusing the trace query's reach). Empty right-leg levels show a dashed placeholder, so the gap is visible rather than hidden.

## Server and graph

- Loader keeps `docname` and `section` (`sections[0]`) on need nodes; test results keep their outcome property as `result` if the needs carry one.
- `GET /api/tree?kind=packages|requirements|rflp` (default `packages`, still fetched for names and the breadcrumb; an unknown kind → 400).
- A CRS-focused chain does not walk through a shared use case (it would pull in other requirements' chains); the trace view follows the same rule.
- The V draws links between neighbouring levels and across the legs; a feature's match to customer requirements is a tag on the feature box.
- `views.KINDS` gains `vmodel`; nodes carry `level` (1–5) and `side` (`left`, `right`, `bottom`).

## Tests

- graph: a need node carries docname and section.
- trees: CRS-003 lists satisfied by SR-005, matched by FEAT-002 (partial), verified by ATC-003; the RFLP tree has UC-001 → FEAT-002 → F-006 → LC-006 → a PC and UC-001 → FEAT-002 → F-007 → LC-007 → PC-001.
- vmodel: default has CRS at level 1 left, ATC at level 1 right, SR-005 at level 2 left with STC-005 at level 2 right, PC-001 at bottom; focus CRS-003 excludes CRS-001; empty right levels reported.
- JS: the V layout places levels top-down, left leg left of right leg, bottom centred; tree rendering escapes names; cross-highlight marks linked rows.

## Plan (small change, done in session, one review at the end)

1. Graph: docname, section, result on needs. 2. Tree queries + endpoint. 3. V-model query. 4. Page: two trees, cross-highlight, V layout and render. 5. Review, fix, browser check.
