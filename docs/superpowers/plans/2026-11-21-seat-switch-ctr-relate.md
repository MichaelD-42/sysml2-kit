# Seat-switch, CTR, constraint links, Relate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the demo to Relate (no Docker) without a Cypher panel, extend the kit's method with requirement classes, customer test requirements and constraint needs, replace the examples with a seat-switch platform and RFQ, add a meta-model view, and review ASPICE coverage.

**Architecture:** Part 1 changes only `demo/`. Part 2 changes the kit (bridge `src/sysml2kit/needs.py`, `compliance.py`, `gaps.py`, the project template, method docs). Part 3 replaces `examples/edrive-platform` and `examples/vehicle` with `examples/seat-switch-platform` and `examples/seat-switch-rfq` and re-anchors every test on them. Part 4 adds a view to the demo. Part 5 writes a review document.

**Tech Stack:** Python 3.12 (kit: standard library only; demo: uv, FastAPI, `relate-db` 1.2.0, fastembed, claude-agent-sdk), sphinx-needs 9.2 with `ubproject.toml`/`schemas.json`, SysML v2 via the `sysml` fork, ES modules + ELK.js.

**Spec:** `docs/superpowers/specs/2026-11-21-seat-switch-ctr-relate-design.md`

## Global Constraints

- Kit runtime (`src/sysml2kit`) stays standard library only.
- Template changes go to `plugins/sysml-rflp/templates/project/` and byte-identically to both examples' copies (`tests/test_template.py`).
- sphinx-needs rules: no `not` in `select`; use enums and `==` (as the `scope` rules do).
- Permitted supplier edits to a customer need: `:scope:` and `:class:` only. CTR text is the customer's, unchanged.
- No real OEM name, brand or standard in the examples; standards are fictional (e.g. "OEM-ENV-100").
- Demo: no container, no database password; Relate in memory, all database calls on one worker thread; the agent's Cypher can never write.
- Every commit ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push.
- Kit checks (from the repo root, PATH incl. `/home/michael/workspace/sysml-v2-rs/target/release` and `.venv/bin`): `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests`, `python tests/acceptance.py`, `python tests/omg_corpus.py`, `make -C examples/<each> all`, `ruff check . && ruff format --check .`, `claude plugin validate .` and `./plugins/sysml-rflp`. Demo checks: `cd demo && uv run python -m unittest discover -s tests`, `node --test demo/tests/js/`.
- ASPICE (Part 5): cite process ids and short names only; never reproduce VDA QMC base-practice or outcome text.

## Review Focus

- A non-functional CRS satisfied only by an attribute value (no constraint) → reported not satisfied, not silently covered. Pinned in Task 4 and Task 9 (acceptance mutation).
- A CRS whose only verification is a CTR that applies to it and is implemented → counts as verified; a CTR that applies but is not implemented → not verified. Pinned in Task 5.
- An `information` CRS → no coverage finding of any kind. Pinned in Task 4 and Task 5.
- The agent's Cypher with a write (CREATE, MERGE, SET, DELETE, CREATE INDEX) → rejected, graph unchanged. Pinned in Task 2.
- A request handled on a FastAPI worker thread → still reaches the Relate database (no WrongThread error). Pinned in Task 1.

---

## Part 1 — Demo backend

### Task 1: Relate adapter and port of loader, search and views

**Files:**
- Create: `demo/explorer/db.py`
- Modify: `demo/explorer/load.py`, `demo/explorer/search.py`, `demo/explorer/views.py` (the `PARTS` fragment, `_read`), `demo/explorer/server.py` (startup, keys, ask connectivity check), `demo/explorer/agent.py` (tool calls go through `db`), `demo/pyproject.toml` (drop `neo4j`, add `relate-db==1.2.0`), `demo/tests/support.py`, all `demo/tests/test_*.py` that build a driver
- Delete: `demo/compose.yaml`
- Test: `demo/tests/test_db.py`

**Interfaces:**
- Produces `db.Graph` (one per process):
  - `Graph()` opens `relate.Database()` in memory on a dedicated single-thread executor; every method below runs there.
  - `query(cypher: str, **params) -> list[dict]` — rows as dicts (position access via `list(row.values())[i]` is the caller's business; replace `records[0][0]`-style uses).
  - `write(statements: Callable[[Callable[[str, dict], None]], None]) -> None` — runs a function that issues statements inside one transaction (commit on success, rollback on exception).
  - `read_only(cypher: str, params: dict | None, limit: int, timeout_s: float) -> dict` — `{"columns", "rows", "truncated"}`; implemented in Task 2, a stub raising `NotImplementedError` here.
  - `close()`.
- `load.load(project, graph, embedder) -> (nodes, edges)`, `search.search(graph, embedder, q, k)`, `search.neighbourhood(graph, key)`, `views.view(graph, kind, focus, needs_path=None)`, `views.tree/requirements_tree/rflp_tree(graph)` keep their names; the first argument becomes a `db.Graph`.
- Spike facts (2026-11-21): `db.index.fulltext.queryNodes(name, query)` takes two arguments (use `LIMIT`); vector index DDL, `db.index.vector.queryNodes`, the key constraint and `db.awaitIndexes` work; `PARTS` fails with `UndefinedVariable: p` (a path variable over a quantified pattern) — rewrite it without binding `p` (e.g. collect the walked nodes with a `COLLECT {}` over an explicit variable-length pattern, or walk in Python).

- [ ] **Step 1: Write failing tests** `demo/tests/test_db.py`: `query("RETURN 1 AS x") == [{"x": 1}]`; a `query` called from a `threading.Thread` other than the creator succeeds; `write` that raises leaves the node count unchanged. Port `support.py` to build a `db.Graph` and load the vehicle example (no skip, no env vars).
- [ ] **Step 2: Run** `cd demo && uv run python -m unittest tests.test_db -v` → FAIL (module missing).
- [ ] **Step 3: Implement** `db.py`; port load/search/views/server/agent; rewrite `PARTS`; fix the full-text call.
- [ ] **Step 4: Run** the whole demo suite → every test that passed on Neo4j passes (view counts identical: context 7/8, boundary of driveUnit 28/7, trace CRS-003 12/13, vmodel CRS-003 14/17, interfaces 9/1, composition 7/6).
- [ ] **Step 5: Commit** `feat(demo): Relate in place of Neo4j`.

### Task 2: Cypher panel out, agent Cypher read-only

**Files:**
- Modify: `demo/explorer/db.py` (`read_only`), `demo/explorer/cypher.py` (keep `plain()` only if still used, else delete the module), `demo/explorer/server.py` (remove `POST /api/cypher`, `GET /api/cypher/examples`), `demo/explorer/agent.py` (`cypher` tool → `graph.read_only`), `demo/explorer/prompt.md` (the former example queries as guidance), `demo/static/index.html`, `demo/static/js/{main,panels,api}.js` (remove the Cypher tab and its code), `demo/Makefile` (no compose, no Bolt wait, no password check), `demo/README.md`
- Test: `demo/tests/test_agent.py`, `demo/tests/test_server.py` (remove Cypher endpoint tests; assert 404 on `/api/cypher`)

**Interfaces:**
- `db.Graph.read_only(...)`: run the query in a transaction that is always rolled back; before that, reject statements the planner classifies as writes (use `EXPLAIN` and the result's `query_type`, or reject on Relate's write statistics after execution — whichever Relate exposes reliably; schema DDL and write procedures included). Raise `db.ReadOnlyError(message)`.

- [ ] **Step 1: Write failing tests**: `read_only` of `CREATE (n:X) RETURN n`, `MERGE (n:X) RETURN n`, `MATCH (n:Node) SET n.x = 1`, `MATCH (n:Node) DETACH DELETE n`, `CREATE INDEX i FOR (n:X) ON (n.y)` each raise `ReadOnlyError` and the node count and index list are unchanged; a 600-row read returns 500 rows and `truncated`; `agent.cypher(graph, "CREATE (n) RETURN n")` returns JSON with `error`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**; remove the panel, endpoints and their tests; README and Makefile updated (`make -C demo setup && make -C demo demo`; integration via `relate serve` for a server).
- [ ] **Step 4: Run** demo suite and `node --test demo/tests/js/` → PASS; start the server and load `/` → no Cypher tab, no console errors.
- [ ] **Step 5: Commit** `feat(demo): agent-only Cypher, panel removed, no container`.

## Part 2 — Kit method

### Task 3: Bridge and template: classes, CTR, constraint needs, new links

**Files:**
- Modify: `src/sysml2kit/needs.py` (`NEED_TYPES["ConstraintUsage"] = "constraint"`, `PREFIXES["constraint"] = "CON"`, `KIND_NAMES`, `LINK_TYPES` += `implements`, `partial_satisfies`; `TRACE_METADATA` += `Trace::Implements: implements`; `@Satisfies { partial = true; }` adds the target to `partial_satisfies` as well, like `@Matches`)
- Modify: `plugins/sysml-rflp/templates/project/docs/ubproject.toml` (types `ctr` prefix `CTR-`, `constraint` prefix `CON-`; fields `class` enum `["functional","non-functional","constraint","information"]` default `""`, `purpose` enum `["","verification","validation"]`, `method` enum `["","test","analysis","inspection","demonstration"]`; links `implements`, `applies_to`, `partial_satisfies`; every new id_regex keeps the platform tag group)
- Modify: `plugins/sysml-rflp/templates/project/model/trace.sysml` (`metadata def Implements { attribute need : String[1..*]; }`; `Satisfies` gains `attribute partial : Boolean[0..1];`) — and the examples' copies
- Test: `tests/test_needs.py`, `tests/test_template.py`

- [ ] **Step 1: Write failing tests** in `tests/test_needs.py`: a `ConstraintUsage` with short name `CON-001` becomes need type `constraint`; `@Satisfies { need = "CRS-001"; partial = true; }` on it yields `satisfies == ["CRS-001"]` and `partial_satisfies == ["CRS-001"]`; `@Implements { need = "CTR-001"; }` on a verification yields `implements == ["CTR-001"]`; prefix mismatch (`constraint <'SR-9'>`) is a bridge error as for other types.
- [ ] **Step 2: Run** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_needs -v` → FAIL.
- [ ] **Step 3: Implement**; mirror template files into both current examples (they are replaced in Part 3, but must stay green until then).
- [ ] **Step 4: Run** unit suite and `tests/test_template.py` → PASS; `make -C examples/vehicle all` still green.
- [ ] **Step 5: Commit** `feat: constraint needs, customer test requirements, requirement classes in the bridge and template`.

### Task 4: Rules by class

**Files:**
- Modify: template `docs/schemas.json` (and example copies), `src/sysml2kit/gaps.py` (`RULE_LAYERS`)
- Test: `tests/test_gaps.py` (every rule has a layer), `tests/acceptance.py` (temporary mutations on the current vehicle example, re-anchored in Task 9)

Rules (ids exact):
- `crs-class` (R): select `type in [crs, prq]`; require `class` non-empty.
- `crs-satisfied` (R): select `type in [crs, prq]`, `scope == ""`, `class in [functional, non-functional, constraint]`; require a `satisfies` back link from a `sysreq` or a `constraint`.
- `constraint-satisfies` (R): select `type == constraint`, `platform == false`; require `satisfies` to a `crs` or `prq`.
- `constraint-verified` (V): select `type == constraint`, `platform == false`; require a `verifies` back link from a `systest`.
- `ctr-implemented` (V): select `type == ctr`, `scope == ""`; require an `implements` back link from a `systest` or `acctest` (a CST answer is accepted via `scope: not-offered|commercial` + `cst` `answers`, as for CRS).
- `systest-verifies` (V): a non-platform `systest` verifies a `sysreq` or `constraint`, or implements a `ctr`.
- `crs-verified` leaves `schemas.json` (its CTR route is two hops) and becomes a computed check in Task 5.
- `information` CRS: selected by no satisfied/verified rule.

- [ ] **Step 1: Write failing acceptance mutations** on the current vehicle example: drop `:class:` from a CRS → build fails on `crs-class`; a constraint `CON-` that satisfies nothing → `constraint-satisfies`; set a CRS to `:class: information` and remove its SR link → build passes.
- [ ] **Step 2: Run** `python tests/acceptance.py` → those mutations FAIL (rules absent).
- [ ] **Step 3: Implement** the rules (if sphinx-needs 9.2 cannot express an OR across link sources, split into two rules or compute in `gaps.py`; say which in the report); add `:class:` to every CRS/PRQ in the current examples so they stay green.
- [ ] **Step 4: Run** acceptance, unit suite (`test_every_rule_in_the_schema_has_a_layer`), both `make all` → PASS.
- [ ] **Step 5: Commit** `feat: coverage rules by requirement class, constraint and CTR rules`.

### Task 5: Compliance: classes, constraint reuse, partial constraints, CTRs, verification route

**Files:**
- Modify: `src/sysml2kit/compliance.py`, `src/sysml2kit/reuse.py` (helper for a constraint's owning part reuse), `src/sysml2kit/cli.py` (the table file gains the CTR table)
- Test: `tests/test_compliance.py`, `tests/test_reuse.py`

**Interfaces:**
- Row becomes `(crs, title, class_, features, reuse, partial, statements, domains, constraints)`; `table_md` adds a Class column and a Constraints column; a second table lists CTRs `(ctr, title, purpose, method, implemented_by, statements)`.
- `reuse.constraint_reuse(needs, con_id) -> str` — `platform`/`variant` if the constraint's owner part (via `owned_by`) is, or specializes, a platform part (variant if any variant in the chain), else `new`; `incomplete` if it has no owner part.
- Findings (exact text): `<CRS>: not answered` (now also satisfied by a constraint counts as an answer for non-functional/constraint); `<CRS>: not verified (no acceptance test, no implemented CTR applying to it)`; `<CRS>: partial satisfaction without a system requirement stating the gap`; `<CTR>: not implemented`. No finding for `class == information`.

- [ ] **Step 1: Write failing tests** with small need dicts: a non-functional CRS satisfied by `CON-1` owned by a platform PC → reuse `platform`, no not-answered finding; the same CON owned by an RFQ part specializing a variant → `variant`; CRS verified only via `CTR-1 applies_to CRS` + `STC-1 implements CTR-1` → no not-verified finding; CTR without implementer → `CTR-1: not implemented` and the CRS not verified; partial constraint satisfaction without a gap SR → the gap finding, with one → none; an information CRS with no links → no finding; `|` in titles escaped in both tables.
- [ ] **Step 2: Run** `... -m unittest tests.test_compliance tests.test_reuse -v` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** unit suite and acceptance → PASS.
- [ ] **Step 5: Commit** `feat: compliance by class, constraint reuse, CTR table, verification via CTRs`.

### Task 6: Method docs, agents, skills

**Files:**
- Modify: `plugins/sysml-rflp/skills/rflp-method/references/structure.md`, `glossary.md`, `plugins/sysml-rflp/agents/requirements-analyst.md`, `test-designer.md`, `physical-architect.md` (constraints over part attributes), `plugins/sysml-rflp/skills/rfq/SKILL.md`, `references/questions.md`, `plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml`, `README.md` (what you get; "Upgrading from 0.2.x": new fields, types, rules, `trace.sysml` additions)
- Test: `claude plugin validate .` and `./plugins/sysml-rflp`; `patterns.sysml` checks clean with `sysml check`

Content (exact rules to state): classify every CRS/PRQ; functional → feature match + SR/constraint; non-functional and constraint → a `CON-` constraint in the model (plain values as constraints, never a bare attribute), a textual SR only for what the model cannot express; information → no obligation; CTRs captured as written, implemented by the supplier's tests via `@Implements`/`:implements:`; a system test verifies an SR or a constraint (`@Verifies`) or implements a CTR; partial constraint satisfaction needs an SR stating the gap.

- [ ] **Step 1:** Update the docs; add to `patterns.sysml` a constraint with id and `@Satisfies`, a partial one, and a verification with `@Implements` and `@Verifies { need = "CON-…"; }`.
- [ ] **Step 2: Run** `sysml check plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml` and plugin validate → clean.
- [ ] **Step 3: Commit** `docs: method for requirement classes, constraints and customer test requirements`.

## Part 3 — Seat-switch examples

### Task 7: Seat-switch platform (replaces edrive-platform)

**Files:**
- Create: `examples/seat-switch-platform/` with the same layout as `examples/edrive-platform/` (Makefile, requirements.txt, `.gitignore`, `docs/` with template config copies, `index.rst`, `model.rst`, `traceability.rst`, `compliance.md`, `docs/platform/requirements.md` (PRQ), `docs/software/requirements.md` (SWR), `docs/acceptance/tests.md`), `model/` (`trace.sysml` copy, `items.sysml`, `requirements/{use_cases,system_requirements}.sysml`, `functional/features.sysml`, `logical/architecture.sysml`, `physical/components.sysml`, `verification/system_tests.sysml`), `test-results/junit.xml`
- Delete: `examples/edrive-platform/` (in Task 9, once nothing references it)

Content (ids tagged `SSW-`):
- PRQ with classes (functional, non-functional, constraint).
- Use cases: adjust seat, operate comfort functions, diagnose and update in the workshop, produce and test at end of line.
- Features (`#Feature action`): seatAdjustmentInput, comfortFunctionInput, nightDesignIllumination, vehicleCommunication, diagnostics, secureUpdate; functions under each (e.g. detect key press, debounce, map to LIN signal, verify image signature).
- Logical: keypad, positionSensing, switchController, linCommunication, illumination, enclosure, with ports and connections.
- Physical (one domain each): ME `housing` variation with variants `housingLH`, `housingRH` (mirrored, clip position), `knob`, `buttonCaps`, `seal`; EE `pcb`, `hallSensors`, `linTransceiver`, `leds`, `buttonSet` variation with variants `base`, `heating`, `heatingCooling`, `massageHeatingCooling` (keys and LEDs on the PCB); SW `switchFirmware` (secure boot, security access, LIN stack, diagnostics).
- `part def SwitchAssembly` with attributes (actuation force, travel, operating voltage, temperature range, IP class, ESD level, durability cycles, luminance, LIN version) and `CON-` constraints over them satisfying the PRQ (plain values as constraints).
- System tests (`verification <'SSW-STC-…'>`) verifying SRs and `@Verifies` constraints; firmware SWRs with JUnit results.

- [ ] **Step 1:** Build the model and docs file by file, running `sysml check model` after each.
- [ ] **Step 2: Run** `make -C examples/seat-switch-platform all` → green (no rule violation, compliance table empty as a platform has no CRS).
- [ ] **Step 3: Commit** `feat(examples): seat-switch platform`.

### Task 8: Seat-switch RFQ (replaces vehicle)

**Files:**
- Create: `examples/seat-switch-rfq/` with the vehicle example's layout; `platform` symlink → `../seat-switch-platform`; `docs/customer/requirements.md` (CRS), `docs/customer/test-requirements.md` (CTR), `docs/customer/statements.md` (CST), `docs/acceptance/tests.md`, `model/` incl. `context.sysml` (the seat, seat ECU via LIN, occupant, workshop tester, end-of-line tester), `test-results/junit.xml`

Content:
- 40–60 CRS, numbered like an OEM spec, each with `:class:`; tags `cybersecurity`, `production`, `workshop` where they apply; the spec's topics: adjustment directions, comfort buttons per position, haptics and actuation force, illumination, LIN signals and diagnostics, temperature/voltage/IP/ESD/EMC constraints, mass and envelope, materials, durability, cybersecurity (signed update, secure boot, security access, no debug port, LIN plausibility), production (EOL test, flashing and variant coding at EOL, DMC label, LH/RH mistake-proofing), workshop (fault memory, update over the bus, replaceable without removing the seat, spare-part numbers), information (SOP, volumes, mounting, list of applicable fictional OEM standards).
- 8–12 CTR (`:purpose:`, `:method:`, `:applies_to:`): environmental programme per "OEM-ENV-100", durability per key, haptic measurement, EMC per "OEM-EMC-200", ESD, ingress, cybersecurity penetration test, in-vehicle validation (purpose validation).
- Model: positions `driverSwitch`, `coDriverSwitch`, `rearLeftSwitch`, `rearRightSwitch`, each `:>` the platform switch selecting `housingLH`/`housingRH` and a button set (driver: massageHeatingCooling; co-driver: heatingCooling; rear: heating); features matching functional CRS (fully from the platform except one partial: the OEM's durability above the platform rating with an SR stating the gap — via `@Satisfies { partial = true; }` on the RFQ constraint), `CON-` constraints in the RFQ model over platform attributes satisfying non-functional and constraint CRS, at least one textual SR for what the model cannot express (e.g. material compliance documentation), one `scope: not-offered` CRS (e.g. capacitive touch) with a not-comply CST, one `scope: commercial` CRS (warranty) with a CST.
- System and acceptance tests with `@Implements`/`:implements:` for every CTR, `@Verifies` for every RFQ constraint, JUnit results.

- [ ] **Step 1:** Build model and docs, `sysml check` after each file.
- [ ] **Step 2: Run** `make -C examples/seat-switch-rfq all` → green; the compliance table shows classes, reuse per CRS, the partial row, the CST rows and the CTR table; no finding.
- [ ] **Step 3: Commit** `feat(examples): seat-switch RFQ`.

### Task 9: Re-anchor kit tests and docs; remove the old examples

**Files:**
- Modify: `tests/acceptance.py` (baselines on both seat-switch examples; every existing mutation re-anchored; new mutations: drop a CRS `:class:` → `crs-class`; remove a CTR's implementer → `ctr-implemented`; replace a non-functional CRS's constraint with a bare attribute → `crs-satisfied`; an information CRS without links → green), `tests/test_template.py` (paths), `README.md` (examples section, MCP example output from the new RFQ), `.github/workflows/ci.yml` (paths), `glossary.md` if it names the old examples
- Delete: `examples/edrive-platform/`, `examples/vehicle/`

- [ ] **Step 1:** Re-anchor and add mutations; run `python tests/acceptance.py` → all ok.
- [ ] **Step 2:** Delete the old examples; `grep -rn "edrive\|examples/vehicle" --exclude-dir=.git --exclude-dir=docs/superpowers .` → only history-free hits (none outside `docs/superpowers`).
- [ ] **Step 3: Run** every kit check from Global Constraints → green.
- [ ] **Step 4: Commit** `test: kit acceptance on the seat-switch examples; old examples removed`.

### Task 10: Demo on the seat switch

**Files:**
- Modify: `demo/explorer/views.py` (default focus no longer `VehicleLogical::vehicle`; requirements tree: CTR group with `implemented by` and `applies to`, CRS class shown; V-model: CTR on the right leg at level 1 with implementing tests, `implements` edges), `demo/explorer/graph.py` (`LAYERS` += `ctr`: V, `constraint`: R; `NEED_FIELDS` += `class`, `purpose`, `method`), `demo/explorer/prompt.md`, `demo/Makefile` (`PROJECT ?= ../examples/seat-switch-rfq`), `demo/README.md` (demo script on the seat switch), all `demo/tests/*` keys, `demo/tests/test_example.py` (structure assertions on the seat switch), `demo/static/js/*` (class badge in the tree, CTR in the V)
- Test: demo suite, JS tests, browser walk

- [ ] **Step 1: Write failing tests** re-pinned on seat-switch ids: requirements tree has groups Customer requirements, Customer test requirements, System requirements; a CTR lists `implemented by` a test; V-model default has a CTR at (1, right) and an `IMPLEMENTS` edge; variants view of the platform `housing` marks the RFQ's selected variant; boundary of the driver switch shows its LIN and supply ports.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** demo suite and JS tests → PASS; walk the demo script in the browser (trees, V, variants, ask "which constraints apply to the driver switch's housing and where do they come from?").
- [ ] **Step 5: Commit** `feat(demo): seat-switch RFQ, CTRs in trees and the V`.

## Part 4 — Meta-model view

### Task 11: Meta-model view

**Files:**
- Modify: `demo/explorer/views.py` (`KINDS` += `metamodel`; `metamodel(graph, project) -> view`), `demo/explorer/server.py` (pass the project path), `demo/static/js/main.js` (tab "Meta-model"; clicking a type or edge lists instances in the inspector), `demo/static/js/layout.js` (layers as frames)
- Test: `demo/tests/test_views.py`, a JS test for the type/edge listing if logic is pure

**Interfaces:**
- `views.metamodel(graph, project: Path) -> dict` — nodes: one per need type present in `docs/ubproject.toml` (`kind` = type, `parent` = its layer frame `layer:R` … `layer:V`, `count` = instances in the graph); edges: per (source type, link, target type) — from the graph (`MATCH (a:Need)-[r]->(b:Need)` grouped by need type and relationship type) united with the declared links of `ubproject.toml`, each with `count` and `unused` (declared, zero instances), and `rules` = ids of `docs/schemas.json` rules whose select type and required link match the edge (and node-level rules on the node).
- Read with `tomllib` and `json`.

- [ ] **Step 1: Write failing tests** on the seat-switch RFQ: edge `constraint -satisfies-> crs` with count > 0 and rule `crs-satisfied`; edge `systest -implements-> ctr` with count > 0 and rule `ctr-implemented`; a declared link with no instance has `unused: true`; node `crs` has rule `crs-class`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** demo suite → PASS; check the view in the browser.
- [ ] **Step 5: Commit** `feat(demo): meta-model view`.

## Part 4b — Owner feedback from the demo walk (runs before Part 5)

Owner input, 2026-11-21. Definitions (verbatim): a use case describes what you can do with the system; a feature is a capability/property of the system to fulfil a use case, someone finds valuable (usually a noun); a function is how a feature is implemented (needs a verb); a logical component is an abstract, solution-free component of the system; a physical component is a physical component of the system that is part of the solution. SW architecture and design are physical components: SW components and SW units (owner: "components and units").

### Task 13: Method: definitions, use case titles, SW architecture and design

**Files:**
- Modify: `glossary.md`, `plugins/sysml-rflp/skills/rflp-method/references/structure.md`, `plugins/sysml-rflp/agents/{requirements-analyst,functional-architect,logical-architect,physical-architect}.md` (whichever exist), `plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml`; kit code only if a rule or the bridge blocks the pattern (then a failing test first).

Content: the five definitions verbatim; use case title pattern "The <actor> wants to <goal>" (e.g. "The driver wants to adjust the seat position") as the need title, the short identifier stays the model name; software as physical components: `#Software` SW components owned by the firmware part, `#Software` SW units owned by their component, SW component interfaces as ports and connections, logical components allocated to SW components, each software requirement (SWR) linked to the SW component or unit implementing it, unit verification by SWR tests (JUnit). `patterns.sysml` gains a firmware with one component and two units; `sysml check` clean.

- [ ] Step 1: tests first for any kit change (bridge/rules) the SW pattern needs; Step 2: docs; Step 3: checks (unit suite, acceptance, plugin validate, `sysml check` patterns); Step 4: commit `docs: definitions, use case titles, software architecture and design as physical components`.

### Task 14: Seat-switch examples: use case titles, electrical detail, connector, SW architecture and design

**Files:** `examples/seat-switch-platform/**`, `examples/seat-switch-rfq/**`, `tests/acceptance.py` if anchors move.

Content: every use case (platform and RFQ) titled by the pattern; every element checked against the definitions; electrical physical components at the level of switch contacts, microcontroller, LEDs and LED drivers, Hall sensors, LIN transceiver, supply/protection; a vehicle connector (`#Electrical`) with pins and a defined pin mapping (supply KL30, ground KL31, LIN), pins bound to the PCB supply and the LIN transceiver, the assembly's `lin`/`supply` ports reaching the vehicle through the connector, RFQ context showing the harness connection; firmware broken into SW components (boot manager/secure boot, input processing, illumination control, LIN stack, diagnostics incl. security access, update manager) and SW units under each, with ports/connections, LC allocations, SWRs linked to components/units, SWR tests on units. Both `make all` green, no compliance finding, acceptance green.

LIN, what the model needs (controller check of the current model: one generic `LinFrame` item, `LinPort` straight from the transceiver to the firmware, no ground, no frames, signals, node address or sleep/wake):
- Connector and pins: the RFQ asks for a 6-pin connector carrying supply, ground and LIN (CRS text, chapter 1). Pin mapping: 1 KL30 supply, 2 KL31 ground (also the LIN reference), 3 LIN bus, 4–6 not used (state it). LIN wake-up runs on the bus, so there is no separate wake line.
- Electrical chain: connector LIN pin → ESD protection → LIN transceiver bus pin. Transceiver to microcontroller over TxD/RxD (UART) plus an enable/wake line, which are not LIN ports. Transceiver supplied from KL30, with reverse-polarity protection on KL30 and a voltage regulator for the microcontroller.
- Items and signals instead of one generic frame: a status frame published by the switch (knob directions, comfort key states, alive counter, error bit); a command frame published by the seat control unit (dimming level, comfort level indication); diagnostic frames (master request 0x3C, slave response 0x3D) carrying UDS for diagnostics and reflash; go-to-sleep and wake-up. The frame/signal layout is defined by the customer's LDF, and the model names frames and signals only, not bit positions.
- Node configuration: LIN 2.2A, 19.2 kbit/s, enhanced checksum, a node address (NAD) and frame identifiers. Four switches on the seat LIN need distinct NADs: assign them per position in the RFQ, set by variant coding at end of line, which ties to the production requirement.
- SW: the LIN stack SW component has units LIN driver (UART, break/sync detection), protocol (PID, checksum, frame handling), signal interface (pack and unpack per LDF), node configuration (NAD, LIN 2.2A configuration services), transport layer (for UDS) and network management (sleep/wake).
- Constraints from existing CRS: LIN 2.2A (already a constraint), quiescent current with the bus asleep, frame plausibility (checksum, alive counter). Add baud rate and checksum type as platform-rated attributes only where a requirement asks for them.

- [ ] Step 1: platform; Step 2: RFQ; Step 3: all kit checks; Step 4: commit `feat(examples): use case titles, electrical detail, connector pin mapping, software architecture and design`.

### Task 15: Demo: diagrams per element type, platform section, System Architecture title

**Files:** `demo/explorer/views.py`, `demo/explorer/server.py` (tree kind `platform`), `demo/static/{index.html,js/*}`, `demo/tests/*`.

Content: offer only the view kinds that apply to the selected element (use case: use cases, traceability; feature/function: activity, traceability; logical component: context, boundary, interfaces, composition, traceability; physical component incl. SW components/units and the connector: boundary, interfaces, composition, variants, traceability; requirement/constraint/CTR: traceability, V-model; compliance, V-model overview and meta-model always); check each element type renders sensibly in each offered view and fix what does not (e.g. pins and the pin mapping in boundary/interfaces, SW components and units in composition); left column: Requirements, System Architecture (renamed from "Model: use case > …", the RFQ's own RFLP tree), Platform (the platform's RFLP tree). Tests pinned on seat-switch ids; JS tests for the applicability map.

- [ ] Step 1: failing tests; Step 2: implement; Step 3: demo suite, JS tests, browser walk; Step 4: commit `feat(demo): views per element type, platform section`.

## Part 5 — ASPICE review

### Task 12: ASPICE review document

**Files:**
- Create: `docs/aspice-review.md`

Content: for SYS.1–SYS.5, SWE.1–SWE.6, HWE.1–HWE.4 (Automotive SPICE 4.0), a table: process id and short name | kit types and links that serve it | rules that demonstrate its traceability/consistency expectations | gap. Then: gaps (no software/hardware requirement levels below the system beyond the platform's SWR, release/baseline, verification measure selection, process/management/support processes out of reach), a recommendation on an ASPICE overlay for the meta-model view (process ids on types/links, coverage per expectation from the rules, what it needs, and that it shows evidence of traceability, not an assessment). Paraphrase only; no VDA QMC text.

- [ ] **Step 1:** Write the review against the finished meta-model (Task 11's view and `schemas.json`).
- [ ] **Step 2:** Self-check: every process row cites a kit type/link or states a gap; no sentence copies standard text.
- [ ] **Step 3: Commit** `docs: ASPICE traceability review of the kit's meta-model`.
