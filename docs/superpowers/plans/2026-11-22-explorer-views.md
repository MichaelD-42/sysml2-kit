# Explorer per-element views Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Each element offers only its own diagrams plus scoped big-picture ones; model-wide views move to a header menu; two-column layout.

**Architecture:** Server (`demo/explorer/views.py`) gains the `allocation` kind, a use-case branch in the activity query, interfaces for actions, and focus scoping for `vmodel` (any need) and `compliance` (a CRS/PRQ). Client (`render.js`) maps an element to `{own, context}` tab groups; `main.js` keeps model-wide views in a header menu and tracks whether the current view is whole or scoped.

**Tech Stack:** Python 3 / FastAPI / Cypher (Relate), vanilla ES modules, ELK, `node:test`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-22-explorer-views-design.md`

## Global Constraints

- Header menu label: `System Model`; items Product overview, Compliance, V-model, Meta-model, each whole (no focus).
- Tab groups labelled `This element` and `In context`.
- Run tests with `make -C demo test` and `node --test demo/tests/js/`.

## Review Focus

- A physical part that is neither a variation, a variant nor a selecting part must not show a Variants tab (probe the view, drop the tab on `reason`).
- Selecting another element while a scoped V-model/compliance is shown re-scopes it; while a whole view from the menu is shown, it only highlights.
- An element with no applicable views (a package) still shows Traceability.
- A use case whose performed features have no functions gives the activity `reason`, not an empty canvas.
- A scoped V-model for an element that reaches no CRS falls back to its own chain (the element itself), not the whole V.

---

### Task 1: Server views

**Files:** Modify `demo/explorer/views.py`; Test `demo/tests/test_views.py` (RFQ class with `self.view`).

**Produces:** `GET /api/view/allocation?focus=LC`, `activity` for a `UseCaseUsage`, `interfaces` for an `ActionUsage`, `vmodel?focus=<any need>` scoped, `compliance?focus=CRS` scoped.

- [ ] Tests: `test_activity_of_a_use_case` (UC-101: nodes include FEAT keys it performs as groups, `SSW-F-005` with a feature parent); `test_allocation_of_a_logical_component` (SSW-LC-007: functions allocated to it, PC-101 among the targets, ALLOCATED_TO edges); `test_interfaces_of_a_function` (SSW-F-011: its LC and that LC's ports in nodes); `test_vmodel_scoped_to_a_physical_part` (PC-101: fewer nodes than the whole V, includes a CRS); `test_compliance_of_one_requirement` (CRS-301: rows == [CRS-301]).
- [ ] Run, see them fail.
- [ ] Implement: `ALLOCATION` query (`allocation` in `KINDS`, `QUERIES`, `DEFAULTS`=first project component, `REASONS`); generic `ACTIVITY` rooting at performed features for a use case; `INTERFACES` taking allocated components as parts when the focus is an action (`SUBJECTS["interfaces"]` stays for ports); `V_REACH` generalised to the CRS the focus reaches through `NEED_LINKS` (the focus's own chain when none); compliance filtered by `focus`.
- [ ] Run all Python tests, pass; update `test_vmodel_of_another_focus_is_the_whole_v` to the scoped behaviour.

### Task 2: Client tab mapping and menu

**Files:** Modify `demo/static/js/render.js`, `demo/static/js/main.js`, `demo/static/index.html`; Test `demo/tests/js/views.test.mjs`.

**Produces:** `viewsFor(node) -> {own: string[], context: string[]}`, `MENU` exported list, `drillKind` uses `own[0]`.

- [ ] Tests per spec table: usecase `{own:[usecases, activity], context:[vmodel]}`; action `{own:[activity], context:[interfaces]}`; logical `{own:[context, allocation], context:[interfaces, vmodel]}`; physical `{own:[composition, variants], context:[interfaces, vmodel]}`; port `{own:[interfaces], context:[]}`; CRS (has `class`, no kind) `{own:[trace], context:[vmodel, compliance]}`; SR/constraint/test/CTR `{own:[trace], context:[vmodel]}`; package `{own:[trace], context:[]}`.
- [ ] Implement; remove `ALWAYS`/`offered`; header `Meta-model` menu; tabs in two groups; `current.whole` decides `show(kind, whole ? null : key)`.
- [ ] Run JS tests, pass.

### Task 3: Layout

**Files:** Modify `demo/static/index.html`, `demo/static/app.css`, `demo/static/js/main.js`.

- [ ] Two columns (tree, view); Ask/Search aside becomes a slide-over toggled by a header `Ask / Search` button; title line (name, kind, id, breadcrumb) above tabs; doc and links in a collapsed `Details` below the canvas; zoom floats on the canvas; legend only on domain-coloured views; note hidden when empty.
- [ ] Verify in the browser pane at 800×600: canvas takes most of the view; screenshot.
