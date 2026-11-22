# RFQ realization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The RFQ owns its F and L layers; each RFQ logical component gets a derived realization degree (full, partial, new, incomplete) from the physical parts allocated to it, with `#Modified` marking changed platform parts.

**Architecture:** The bridge (`needs.py`) rejects RFQ F/L elements that specialize the platform and records `#Modified`; `reuse.py` computes degrees per part, component and feature; `compliance.py` reports them and writes a realization table. The window-switch RFQ example is rebuilt on its own functions and components.

**Tech Stack:** Python 3 (unittest), SysML v2 via `sysml` 0.2.0-kit.3, sphinx-needs, the demo explorer (Python + ES modules, node:test).

**Spec:** `docs/superpowers/specs/2026-11-22-rfq-realization-design.md`

## Global Constraints

- Degree values, exactly: `full`, `partial`, `new`, `incomplete`; worst first `incomplete`, `new`, `partial`, `full`. They replace `platform`, `variant`, `modified`.
- Bridge error texts, exactly:
  - `<id>: specializes the platform's <platform id>; an RFQ derives its own <type>s and the platform realizes them at P` (`<type>` = feature, function, logical component, logical interface)
  - `<id>: #Modified needs a platform part to modify; a part of its own is new`
- `#Modified` is `metadata def Modified;` in `Trace`; it combines with one domain keyword or `#Assembly`.
- The platform example is unchanged. What the RFQ offers the customer is unchanged (same CST, same compliance values).
- Tools on PATH for builds and tests: `PATH=/tmp/claude-1000/-home-michael-workspace-sysml2-kit/1bccc778-ab41-4e19-bdc0-61221a39d7f1/scratchpad/sysml-020k3/bin:$PWD/.venv/bin:$PATH`.
- Commit only when the user asks (user's standing rule); the commit steps below are where a commit would go.

## Review Focus

- A platform-tagged RFQ build where an RFQ part subsets a platform part only through an inherited ref part (`:>> keyCaps :> WindowSwitchPhysical::keyCaps`): degree must still be `full`/`partial`, not `new`. Test in Task 2.
- `#Modified` on a part whose platform specialization is two hops away (RFQ part :> RFQ part :> platform part): accepted. Test in Task 1.
- The platform's own build (no platform files): the specialization error must not fire, and every degree is `new`. Test in Task 1 and Task 2.
- A composite component whose leaves include an `incomplete` one: composite is `incomplete`. Test in Task 2.
- The realization table with a component allocated to nothing: row present, degree `incomplete`, parts cell empty. Test in Task 3.

---

### Task 1: Bridge — `#Modified` and the specialization error

**Files:**
- Modify: `src/sysml2kit/needs.py` (`convert`)
- Modify: `model/trace.sysml` in `examples/window-switch-rfq`, `examples/window-switch-platform`, `plugins/sysml-rflp/templates/project` (add `metadata def Modified;` after `Assembly`, with the keyword comment extended)
- Modify: `docs/ubproject.toml` in both examples and the template: `[needs.fields.modified]` (description "A platform part this project changes (#Modified)", nullable), `reuse` description "Realization: full, partial, new or incomplete"
- Test: `tests/test_needs.py`

**Interfaces:**
- Produces: every need has `"modified": bool` (true only with `Trace::Modified`).

- [ ] **Step 1: Write failing tests** in `KeywordTest` / `PlatformVariantTest` using the existing `el`, `keyword`, `rel` helpers:
  - `test_modified_keyword_marks_a_physical_part`: `#Electrical #Modified` part subsetting a platform part → `needs["PC-1"]["modified"] is True`; an untagged part → `False`.
  - `test_modified_needs_a_platform_part`: `#Modified` on a project part specializing only project parts → error text above with `PC-1`.
  - `test_modified_through_a_project_part_reaches_the_platform`: PC-2 :> PC-1 :> platform WSW-PC-1, `#Modified` on PC-2 → no error.
  - `test_modified_on_a_non_physical_need_is_an_error`: on a logical component → same error text.
  - `test_project_feature_specializing_the_platform_is_an_error`: FEAT-1 :> platform WSW-FEAT-1 with platform files → `FEAT-1: specializes the platform's WSW-FEAT-1; an RFQ derives its own features and the platform realizes them at P`; same for a component (`logical components`).
  - `test_platform_build_has_no_specialization_error`: same model, no platform files → no error.
  - `test_physical_part_may_specialize_the_platform`: PC :> platform PC → no error.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tests.test_needs -v` → the new tests FAIL.
- [ ] **Step 3: Implement** in `convert`: `"modified": "Trace::Modified" in tags` in the need dict; after the specialization links are built, for each non-platform need when `platform_files` is set: error if its type is feature/function/component/interface and a direct `specializes` target is platform (name the first such target, sorted). For each need with `modified`: error unless type is physical and `closure(needs, id, "specializes")` contains a platform need (in a platform build, where nothing is platform, `#Modified` is an error too). Errors go through the existing `errors` list.
- [ ] **Step 4: Run** the test module → PASS; `.venv/bin/python -m unittest discover tests` → no other test broken.
- [ ] **Step 5: Commit** `feat(bridge): #Modified, RFQ F/L may not specialize the platform`.

### Task 2: Degrees in `reuse.py`

**Files:**
- Modify: `src/sysml2kit/reuse.py`
- Modify: `src/sysml2kit/needs.py` (write `reuse` on components too)
- Test: `tests/test_reuse.py`

**Interfaces:**
- Consumes: `modified` from Task 1.
- Produces:
  - `part_reuse(needs, part) -> "full" | "partial" | "new"`
  - `component_pcs(needs, lc) -> set[str]`: physical parts a leaf component reaches (assemblies expanded, variant rules applied; a variation without selection reaches none)
  - `component_reuse(needs, lc) -> degree`: leaf from its parts (none → `incomplete`); composite = worst of its leaf descendants
  - `reuse(needs) -> {id: degree}` for every feature and component
  - `constraint_reuse(needs, con_id)` returns the new values
  - `WORST_FIRST = ["incomplete", "new", "partial", "full"]` moves here from `compliance.py` (compliance imports it)

- [ ] **Step 1: Update and add tests.** Rename expectations in existing tests: `platform`/`variant` → `full`, `modified` → `partial`. Add:
  - `test_modified_part_is_partial`: PC `modified=True` specializing a platform part → `part_reuse == "partial"`, feature `partial`.
  - `test_component_degree_from_its_parts`: LC to (platform PC, new PC) → `component_reuse == "partial"`; to new only → `new`; to nothing → `incomplete`.
  - `test_composite_is_worst_of_leaves`: composite LC owning a `full` and an `incomplete` leaf → `incomplete`; owning `full` and `partial` → `partial`.
  - `test_feature_is_worst_of_its_components`: two functions on a `full` and a `partial` LC → `partial`.
  - `test_reuse_covers_components`: `reuse(needs)` has the LC key.
  - `test_part_via_inherited_ref_part_is_full`: project PC whose `specializes` holds a platform PC (the ref-part hop is not a need) → `full`.
  - `test_platform_build_is_new`: nothing platform → feature and LC `new`.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tests.test_reuse -v` → FAIL.
- [ ] **Step 3: Implement.** Extract the per-component loop of `_function_reach` into `_component_reach(needs, lc) -> (pcs, unselected)`; `_function_reach` unions it over a function's components; `component_pcs` returns `set()` if unselected else pcs. `part_reuse`: `partial` if `modified`, else `full` if the chain reaches a platform need, else `new`, then the assembly combination; `_combine`: `{"new"}` → new, `{"full"}` → full, else partial. Feature degree: `incomplete` if any leaf function reaches no part (as today), else the worst `component_reuse` over the components `function_components` returns for it. In `needs.py` the existing `reuse(needs)` loop already writes `reuse` for every id it returns.
- [ ] **Step 4: Run** test module → PASS.
- [ ] **Step 5: Commit** `feat(reuse): realization degree per part, component and feature`.

### Task 3: Compliance values and the realization table

**Files:**
- Modify: `src/sysml2kit/compliance.py`, `src/sysml2kit/cli.py` (pass the rows)
- Modify: `examples/window-switch-rfq/docs/compliance.md`, `plugins/sysml-rflp/templates/project/docs/compliance.md` (intro: "…their reuse, the compliance statements that answer it, and per logical component how far the platform realizes it.")
- Test: `tests/test_compliance.py`

**Interfaces:**
- Consumes: `component_reuse`, `WORST_FIRST` from Task 2.
- Produces: `realization_rows(needs) -> list[tuple[str, str, str, list[tuple[str, str, str]]]]` = (lc, title, degree, parts); parts are the component's direct `allocated_to` targets of type physical, sorted, each (id, title, note): `modified <platform ids>` if `modified`, `new` if `part_reuse == "new"`, `<platform ids>` for a project part specializing platform parts, `""` for a platform part. Platform ids = platform needs in its specializes closure, sorted, comma-joined. Rows: every non-platform component, id order.
  `table_md(rows, ctrs=(), realization=())` appends `| Component | Title | Degree | Physical parts |`; a part renders as ``{need}`PC-112` keyCaps (modified WSW-PC-002)`` (no parentheses when the note is empty).

- [ ] **Step 1: Tests:** `test_realization_rows` (LC with a modified, a new and a platform part → the three notes and degree `partial`); `test_realization_row_without_parts` (`incomplete`, `[]`); `test_table_has_realization_table` (header line and one rendered row in `table_md` output); update `test_worst_reuse_wins` and `test_constraint_on_a_part_specializing_a_variant_is_variant` (rename to `..._is_full`) to the new values.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tests.test_compliance -v` → FAIL.
- [ ] **Step 3: Implement** `realization_rows`, the `table_md` parameter, and in `cli.py` `table_md(rows, ctr_rows(needs), realization_rows(needs))`.
- [ ] **Step 4: Run** `.venv/bin/python -m unittest discover tests` → PASS.
- [ ] **Step 5: Commit** `feat(compliance): realization table per logical component`.

### Task 4: Rebuild the window-switch RFQ on its own F and L

**Files:**
- Modify: `examples/window-switch-rfq/model/functional/features.sysml`, `logical/architecture.sysml`, `physical/components.sysml`, `docs/conf.py`
- Modify: `tests/acceptance.py`

Content, per the spec's Example section:
- F: FEAT-101..104 drop `:> WindowSwitchFeatures::…`, keep `@Matches` and docs, own F-101..F-113 mirroring WSW-F-001..013 (names, docs, `in`/`out` KeyState, flows, successions; `private import WindowSwitchItems::*;`). The package doc says the RFQ derives its own functions.
- L: LC-100 `OEM_WindowSwitch` (no `:>`) owning LC-101 keySensing … LC-106 enclosure with LI-101..LI-109 and the platform's three connects; allocations of F-101..113 mirroring the platform's; satisfies as today with `partNumberLabel` by `OEM_WindowSwitch.enclosure`. Doc: the RFQ's logical breakdown, realized at P.
- P: in PC-100 add `#Mechanical #Modified part <'PC-112'> oemKeyCaps :>> keyCaps :> WindowSwitchPhysical::keyCaps` (doc: platform caps with the OEM's symbol set; new laser-etching program, BOM WSW-CAP-200 modified) and `#Mechanical part <'PC-113'> partNumberLabel` (doc: printed label with the door's OEM part number in plain text and Data Matrix, new). Allocations: `OEM_WindowSwitch to oemWindowSwitch`; the existing four variant allocations; the rest mirroring the platform's list with RFQ components and platform parts (`WindowSwitchPhysical::pcb.microcontroller`, firmware SW components, connector), enclosure to `WindowSwitchPhysical::housing`, `WindowSwitchPhysical::seal`, `oemWindowSwitch.oemKeyCaps`, `oemWindowSwitch.partNumberLabel`; LI to PI mirroring the platform's four.
- `conf.py`: `project = "Window switch RFQ (sysml2-kit example)"`.

- [ ] **Step 1: Acceptance updates first.** In `compliance_rows`: kinds `full` (`c[4] == "full"`), `partial reuse` (`c[4] == "partial"`), keep partial/statement-only; add a check that the realization table lists `LC-106` as `partial` with `PC-112` and `(new)`. Mutations: keep the LC-199 one but anchor on LC-100's new doc ending; add
  - "an RFQ feature specializing a platform feature fails the bridge": append ` :> WindowSwitchFeatures::windowControl` to FEAT-101's declaration → `FEAT-101: specializes the platform's WSW-FEAT-001`;
  - "#Modified on a part of its own fails the bridge": `#Mechanical part <'PC-113'>` → `#Mechanical #Modified part <'PC-113'>` → `PC-113: #Modified needs a platform part to modify`;
  - "a component realized by new parts only is new": allocate LC-106 only to PC-113 (drop its other enclosure allocations) → the build passes and `docs/_generated/compliance.md` has the LC-106 row with `new` (check the file, like the variant check reads the table).
- [ ] **Step 2: Rewrite the three model files and conf.py** as above.
- [ ] **Step 3: Run** `make -C examples/window-switch-rfq all` with the tools on PATH → passes; `docs/_generated/compliance.md` shows LC-106 `partial`, LC-100 `partial`, the other leaves `full`, FEAT-101 rows `partial`.
- [ ] **Step 4: Run** `.venv/bin/python tests/acceptance.py` → every check ok (it builds the platform too).
- [ ] **Step 5: Commit** `feat(example): window-switch RFQ owns its functions and components`.

### Task 5: Explorer

**Files:**
- Modify: `demo/explorer/graph.py` (add `"modified"` to the loaded fields), `demo/static/js/layout.js` (tag `modified` when `node.modified`)
- Modify: demo tests that name RFQ ids whose meaning changed (`demo/tests/test_views.py` lines ~287, ~378: the RFQ chain is now `FEAT-101 → F-101 → LC-101`, and LC-100 no longer uses WSW-LC-001)
- Test: `demo/tests/js/layout.test.mjs`, `demo/tests/test_views.py`

- [ ] **Step 1: Tests:** layout test `modified part gets a modified tag`; views test `test_allocation_shows_degree`: `allocation` of `LC-106` has the focus node with `reuse == "partial"` and PC-112 with `modified`. Fix the stale id expectations.
- [ ] **Step 2: Run** `cd demo && make test` (or the Python and node test commands its Makefile names) → new tests FAIL.
- [ ] **Step 3: Implement** the field and the tag (`reuse: partial` already renders from `node.reuse`).
- [ ] **Step 4: Run** demo tests → PASS.
- [ ] **Step 5: Commit** `feat(demo): realization degree and modified parts in the allocation view`.

### Task 6: Method docs, skills, agents

**Files:**
- Modify: `plugins/sysml-rflp/skills/rflp-method/references/structure.md` (Platform section: RFQ owns F/L, realization at P, `#Modified`, degree derivation replacing the reuse-status bullet, both bridge errors), `skills/rfq/SKILL.md` (status names, realization table in the P and V reports), `skills/sysml-author/SKILL.md` and `references/patterns.sysml` (no `:>` for features/LCs in an RFQ; `#Modified` example), `agents/functional-architect.md`, `agents/logical-architect.md` (derive own, do not subset platform), `agents/physical-architect.md` (realize RFQ LCs; `#Modified` with a doc saying what changes; report degrees), `agents/rflp-reviewer.md` (checks: no F/L subsetting, `#Modified` doc), `glossary.md` (realization degree, `#Modified`), `README.md` only where it names reuse statuses.

- [ ] **Step 1:** `grep -rn "platform, variant\|variant, modified\|:> WindowSwitchFeatures\|:> ACME_WindowSwitch\|inherits its" plugins README.md glossary.md` → list of stale lines.
- [ ] **Step 2:** Rewrite each to the spec; status names as in Global Constraints.
- [ ] **Step 3:** Re-run the grep → no hits; `.venv/bin/python -m unittest tests.test_template` → PASS.
- [ ] **Step 4: Commit** `docs(plugin): RFQ-owned F/L and realization degrees`.
