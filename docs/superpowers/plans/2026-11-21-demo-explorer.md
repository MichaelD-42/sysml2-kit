# Model Explorer Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local web app that loads a kit RFQ project into Neo4j, shows it in nine interactive views, and answers questions about it through the Claude Agent SDK.

**Architecture:** The kit's examples are enriched first (attributes, constraints, items, flows, a drive-unit assembly, a vehicle context). `demo/` is a separate Python project: a loader turns `build/model.json` + `build/needs/needs.json` into a Neo4j graph with a vector and a full-text index; a FastAPI server exposes tree, element, view, search, Cypher, ask and reload endpoints; the agent runs the Agent SDK with in-process tools plus the `sysml` MCP server; a build-free page lays views out with vendored ELK.js and draws SVG.

**Tech Stack:** Python 3.12, uv, FastAPI + uvicorn, `neo4j` driver 5.x, `fastembed` (`BAAI/bge-small-en-v1.5`, 384 dims), `claude-agent-sdk`, Neo4j Community 5.x via podman, ES modules + vendored `elkjs` (`elk.bundled.js`), `node --test` for pure JS modules.

**Spec:** `docs/superpowers/specs/2026-11-21-demo-explorer-design.md`

## Global Constraints

- All demo code under `demo/` with its own `demo/pyproject.toml`; the `sysml2kit` package gains no dependency and no change.
- After Task 1 every kit check stays green: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests`, `python tests/acceptance.py`, `python tests/omg_corpus.py`, `make -C examples/vehicle all`, `make -C examples/edrive-platform all`, `ruff check . && ruff format --check .`.
- PATH for kit runs: `PATH=/home/michael/workspace/sysml-v2-rs/target/release:/home/michael/workspace/sysml2-kit/.venv/bin:$PATH`.
- Read-only: the agent and `POST /api/cypher` can never write to Neo4j; only the loader writes.
- No secrets in source: `NEO4J_URI` (default `bolt://localhost:7687`), `NEO4J_USER` (default `neo4j`), `NEO4J_PASSWORD` (required, no default) from the environment. Claude auth is whatever Claude Code has; nothing in code reads or sets it.
- No network at run time: JS vendored under `demo/static/vendor/`; the embedding model cached by `make -C demo setup` into `demo/.cache/fastembed` (git-ignored).
- Server binds `127.0.0.1:8000` only; `compose.yaml` publishes Neo4j on `127.0.0.1` only.
- The agent has no built-in Claude Code tools (no Bash, file, web tools); only `mcp__kit__*` and `mcp__sysml__*`.
- Answers cite element/need ids; ids that do not resolve in the graph are marked in the page.
- Every commit ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push.
- Demo tests: `cd demo && uv run python -m unittest discover -s tests`; tests needing Neo4j skip with the message `Neo4j not reachable at <uri>` when it is not running. Not added to CI.

## Review Focus

- Focus on an id that does not exist, or on an element a view does not apply to (activity of a part) → HTTP 404 / an empty view with a `reason`, never a 500. Pinned in Task 4 and Task 5.
- Cypher panel given a write (`CREATE`, `MERGE`, `DELETE`, `CALL db.*` that writes, `LOAD CSV`) → rejected with the Neo4j error text, graph unchanged. Pinned in Task 5.
- Search for an exact id (`PC-001`, `EDU-PC-003`) → that element ranks first (full-text beats embeddings for ids). Pinned in Task 3.
- Reload while a model file has a syntax error → `make` fails, the old graph stays loaded, the error text is returned. Pinned in Task 5.
- Ask while Neo4j or Claude is unavailable → the stream ends with an `error` event the page shows, not a hung spinner. Pinned in Task 6 (tool side) and Task 7 (page side).

---

### Task 1: Enrich the examples

**Files:**
- Modify: `examples/edrive-platform/model/physical/components.sysml`, `examples/edrive-platform/model/logical/architecture.sysml`, `examples/edrive-platform/model/functional/features.sysml`
- Modify: `examples/vehicle/model/physical/components.sysml`, `examples/vehicle/model/logical/architecture.sysml`, `examples/vehicle/model/functional/features.sysml`, `examples/vehicle/model/requirements/system_requirements.sysml`
- Create: `examples/vehicle/model/context.sysml`, `examples/edrive-platform/model/items.sysml`
- Modify: `examples/vehicle/Makefile` (`DIAGRAMS` if a listed name moves), `tests/acceptance.py` (only anchors that the restructuring moves)
- Test: `demo/tests/test_example.py` (create `demo/` with only `demo/tests/__init__.py` and this file here; Task 2 adds the project)

**Interfaces:**
- Produces: the element names below, which later tasks' tests and the demo script use verbatim.

Rules: new elements get a short id only when they belong in the trace, and then they must satisfy every RFLP rule. Attributes, constraints, items, interface definitions, flows, context parts and assemblies get no id. Existing ids keep their meaning. Units from `ISQ`/`SI` (probe on 2026-11-21: `attribute ratedPower : PowerValue = 80 [kW];` checks clean and exports `80 [kW]` as a `TextualRepresentation`).

Content to add (values plausible for a passenger-car e-drive; the names are pinned, the numbers are the builder's within these):

- `EDrive` items (`items.sysml`, package `EDriveItems`): `item def ElectricPower`, `item def ShaftTorque`, `item def TorqueRequest`, `item def Coolant`; `interface def HighVoltageInterface`, `interface def CanInterface`, `interface def CoolantInterface`, `interface def MountInterface`, each with two typed ends.
- Platform physical attributes: on `motor` the variation: `ratedPower`, `peakTorque`, `mass`, `maxSpeed`, redefined per variant (`motor50kW`: 50 kW; `motor80kW`: 80 kW); `inverter`: `dcLinkVoltage = 400 [V]`, `maxCoolantTemperature`; `housing`: `ipRating : String = "IP67"`, `mass`. Constraints: on `motor` `constraint peakTorqueLimit { peakTorque <= <value> [N*m] }`; on `inverter` `constraint coolantDerating { ... maxCoolantTemperature ... }`.
- Platform physical assembly: `part eDriveUnit` (no id) owning references to `motor`, `inverter`, `controllerFirmware`, `housing` with ports `hvIn`, `canBus`, `coolantIn`, `coolantOut`, `mount`, and inner connections typed by the interface defs.
- Functional flows: action parameters and `flow` between `convertPower` and `produceTorque` (item `ElectricPower`) in both examples; `receiveTorqueRequest` takes `TorqueRequest`.
- Logical flows: the vehicle's `connect energyStore.powerOut to powertrain.powerIn` becomes a `flow of ElectricPower` (or an interface usage of `HighVoltageInterface` carrying it).
- Vehicle physical: `part driveUnit :> EDrivePhysical::eDriveUnit` (no id, inside `vehicleAssembly`, so its qualified name is `VehiclePhysical::vehicleAssembly::driveUnit`) holding `PC-001 driveMotor` (qualified name `VehiclePhysical::vehicleAssembly::driveUnit::driveMotor`) (still `:> motor::motor80kW`, still allocated from `LC-007`); new unnumbered vehicle parts `vehicleControlUnit` and `coolingCircuit`; `part vehicleAssembly` (no id) containing `driveUnit`, references to `tractionBattery` and `ladderFrame`, `vehicleControlUnit`, `coolingCircuit`, and the connections to `driveUnit`'s five ports (HV from battery, CAN from VCU, coolant in/out from cooling circuit, mount to ladder frame).
- Vehicle context (`context.sysml`, package `VehicleContext`): `part vehicleContext` with `part vehicle :> VehicleLogical::vehicle`, `part driver`, `part passenger`, `part trailer`, `part chargingStation`, `part road`, and connections from each to `vehicle`.
- Requirement constraint: `SR-005 acceleration` gets `subject vehicle`, `attribute accelerationTime : TimeValue` and `require constraint { accelerationTime <= 10 [s] }`.
- Short `doc` on each new part, interface def and item def.

- [ ] **Step 1: Write the failing structure test** `demo/tests/test_example.py`, standard library only, exporting the vehicle project with `sysml export` (model files + platform files without `platform/model/trace.sysml`, same selection as the Makefile) into a temp file:

```python
class EnrichedExampleTest(unittest.TestCase):
    def test_attributes_with_units(self):
        values = texts_of_attribute_values(export, "EDrivePhysical::motor::motor80kW")
        self.assertIn("ratedPower", values)
        self.assertRegex(values["ratedPower"], r"^80 \[kW\]$")

    def test_constraints(self):
        self.assertTrue(named(export, "ConstraintUsage", "peakTorqueLimit"))
        self.assertTrue(named(export, "ConstraintUsage", "coolantDerating"))

    def test_requirement_constraint_on_sr005(self):
        self.assertTrue(
            requirement_constraints(export, "VehicleRequirements::acceleration")
        )

    def test_drive_unit_boundary(self):
        self.assertEqual(
            port_names(export, "VehiclePhysical::vehicleAssembly::driveUnit"),
            {"hvIn", "canBus", "coolantIn", "coolantOut", "mount"},
        )
        self.assertGreaterEqual(
            connections_touching(export, "VehiclePhysical::vehicleAssembly::driveUnit"),
            5,
        )

    def test_context(self):
        self.assertEqual(
            part_names(export, "VehicleContext::vehicleContext"),
            {"vehicle", "driver", "passenger", "trailer", "chargingStation", "road"},
        )

    def test_flows(self):
        self.assertGreaterEqual(
            count(export, "FlowUsage") + count(export, "SuccessionFlowUsage"), 3
        )
```

Helpers walk `owningRelationship`/`ownedMember`-style refs in the export; port names and inherited ports come through the `:> eDriveUnit` subsetting (use the export's `feature` / `inheritedMember` refs if present, else declare the ports on `driveUnit` too — say which in the report). The exact metaclass names for flows come from the export; check them on a probe first.

- [ ] **Step 2: Run** `PATH=... python3 -m unittest demo.tests.test_example -v` from the repo root. Expected: FAIL (names missing).
- [ ] **Step 3: Enrich the models** as listed above. Run `sysml check` on both projects after each file.
- [ ] **Step 4: Run** the structure test → PASS; then every check in Global Constraints → all green. If an RFLP rule fires on a new element, fix the model (link it or drop its id), never the rule.
- [ ] **Step 5: Commit** `feat(examples): attributes, constraints, flows, drive-unit assembly and vehicle context`.

### Task 2: Demo project and loader

**Files:**
- Create: `demo/pyproject.toml`, `demo/compose.yaml`, `demo/Makefile`, `demo/.gitignore` (`.cache/`), `demo/explorer/__init__.py`, `demo/explorer/graph.py`, `demo/explorer/load.py`
- Create: `demo/tests/fixtures/model.json`, `demo/tests/fixtures/needs.json` (small, hand-written: a part with a port and an attribute `80 [kW]`, a variation with two variants, an action pair with a succession and a flow, a requirement with a `require constraint`, an implied subsetting, a CRS need, a PC need linked by `allocated_to` and `specializes`)
- Test: `demo/tests/test_graph.py`, `demo/tests/test_load.py`

**Interfaces:**
- Produces:
  - `graph.build(export: list[dict], needs: dict[str, dict]) -> Graph`, where `Graph = dataclass(nodes: dict[str, Node], edges: list[Edge])`, `Node = dataclass(key: str, labels: list[str], props: dict)`, `Edge = dataclass(src: str, type: str, dst: str, props: dict)`. Node key: the need id when the element has one, else the export `@id`.
  - Node props: `key, uid, name, qualifiedName, shortName, kind` (metaclass), `doc, source` (`file:line` from the need, when there is one), `layer, domain, platform, variant, reuse, title, content` (from the need), `value, unit` (attributes, split from the value text: number then the bracketed unit; a string literal keeps `value` and no unit), `expression` (constraints), `searchText`.
  - Labels: `Element` + the metaclass for model elements; `Need` + need type for needs that are not model elements; model elements that are needs also get `Need` and the need type.
  - Edge types: `OWNS, TYPED_BY, SPECIALIZES, CONNECTS, FLOW` (prop `item`), `SUCCESSION, PERFORMS, REQUIRES` (requirement → constraint), `SUBJECT`, and each needs link field upper-cased (`SATISFIES, ALLOCATED_TO, VERIFIES, REALIZES, MATCHES, PARTIAL_MATCHES, ANSWERS, TESTS, …`), never the `_back` fields. Implied relationships are dropped. `SPECIALIZES` from the needs and from the export are deduplicated.
  - `load.write(graph: Graph, driver) -> None`: one transaction, `MATCH (n) DETACH DELETE n` first, then nodes and edges in batches of 500 with `UNWIND`; then `load.indexes(driver, dims: int)`.
  - `load.main(argv)`: `python -m explorer.load <project-dir>` reads `<project>/build/model.json` and `<project>/build/needs/needs.json`, builds, embeds (Task 3), writes, prints `loaded N nodes, M edges`.
- `searchText` = `name`, `kind`, `doc`, owner path, `value unit` of owned attributes, and `content` of needs linked by any edge, joined by newlines (built in `graph.build` after edges exist).

- [ ] **Step 1: Write failing tests** in `test_graph.py` against the fixtures: node for the attribute has `value == 80` and `unit == "kW"`; the implied subsetting produces no edge; the requirement has a `REQUIRES` edge to the constraint with `expression` set; the PC node has labels `Element`, `PartUsage`, `Need`, `physical`; the CRS is a `Need`-only node; a `SUCCESSION` and a `FLOW` with `item` exist; no edge type ends in `_BACK`; the PC's `searchText` contains the CRS-linked SR's text when linked.
- [ ] **Step 2: Run** `cd demo && uv run python -m unittest tests.test_graph -v` → FAIL (module missing).
- [ ] **Step 3: Implement** `pyproject.toml` (deps: `fastapi`, `uvicorn`, `neo4j>=5.11,<6`, `fastembed`, `claude-agent-sdk`, and `sysml2kit` as an editable path dependency on `..` via `[tool.uv.sources]`; no dev deps beyond stdlib unittest), `compose.yaml` (`neo4j:5-community`, `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?set NEO4J_PASSWORD}`, ports `127.0.0.1:7474:7474` and `127.0.0.1:7687:7687`, named volume), and `graph.build`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Write failing** `test_load.py` (skips without Neo4j): after `write`, `MATCH (n) RETURN count(n)` equals `len(graph.nodes)`; a second `write` does not double it.
- [ ] **Step 6: Implement** `load.write`, `load.main`. Run against the vehicle example after `make -C examples/vehicle docs`: prints the counts. Run tests → PASS.
- [ ] **Step 7: Commit** `feat(demo): graph model and Neo4j loader`.

### Task 3: Search

**Files:**
- Create: `demo/explorer/search.py`
- Modify: `demo/explorer/load.py` (embed and index), `demo/Makefile` (`setup` target caching the model)
- Test: `demo/tests/test_search.py`

**Interfaces:**
- Consumes: `Graph`, `load.write`.
- Produces:
  - `search.Embedder` with `embed(texts: list[str]) -> list[list[float]]` and `dims: int` (384), cache dir `demo/.cache/fastembed`.
  - `load.indexes(driver, dims)`: vector index `element_embedding` on `:Element(embedding)` and `:Need(embedding)` (cosine), full-text index `element_text` on `name, shortName, title, searchText` for labels `Element|Need`.
  - `search.search(driver, embedder, q: str, k: int = 10) -> list[Hit]`, `Hit = dict(key, name, kind, shortName, owner, score, snippet)`. Reciprocal-rank fusion of the vector and full-text result lists (k=60), full-text query escaped with Lucene escaping; a query that is exactly a node `key` returns that node first.
  - `search.neighbourhood(driver, key: str) -> dict` (the node plus 1-hop edges), used by the agent tool.

- [ ] **Step 1: Write failing tests** (skip without Neo4j; load the vehicle example once in `setUpClass`): `search(..., "PC-001")[0]["key"] == "PC-001"`; `search(..., "EDU-PC-003")[0]["key"] == "EDU-PC-003"`; a natural query `"what limits motor torque"` has `peakTorqueLimit` in the top 5; a query with Lucene syntax characters (`"torque AND (" `) returns without raising.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** embedder, indexes, search, neighbourhood; `make -C demo setup` runs `uv sync` and downloads the model once.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(demo): hybrid semantic and full-text search`.

### Task 4: Views

**Files:**
- Create: `demo/explorer/views.py`
- Test: `demo/tests/test_views.py`

**Interfaces:**
- Produces: `views.view(driver, kind: str, focus: str | None, needs_path: Path | None = None) -> dict` (`needs_path` used by compliance only) with `{"kind", "focus", "nodes": [{key, name, kind, shortName, domain, layer, platform, variant, reuse, compartments: {attributes: [...], ports: [...]}, parent}], "edges": [{src, dst, type, label}], "reason"}`; `reason` is a non-empty string exactly when `nodes` is empty. `parent` nests nodes (frames, ports on borders). `views.KINDS = ("context", "boundary", "interfaces", "activity", "composition", "variants", "usecases", "trace", "compliance")`. Unknown kind → `ValueError`; unknown focus → `KeyError`. Default focus when `None`: `VehicleLogical::vehicle` for context/boundary/composition/interfaces, the first feature for activity, the first variation for variants, the first use case for usecases, the first CRS for trace; compliance ignores focus.
  - `views.tree(driver) -> list[dict]`: nested `{key, name, kind, children}` over `OWNS` from the packages down to parts, actions, ports, use cases and requirements.
- One Cypher query per kind, defined in `views.py` as module constants. Semantics per kind are the spec's "Views" section; additionally: context of X = X, the parts that `SPECIALIZES` X, their owners' other parts connected to them, and actors of use cases whose subject is X; boundary = X's ports, its direct parts with their ports, connections among them, and the parts outside X connected to X's ports; activity = actions owned by the focus with `SUCCESSION` and `FLOW`, plus each action's `ALLOCATED_TO` component as `lane`; variants = variation, variants with differing attribute values, and the RFQ parts that `SPECIALIZES` a variant (marked `selected`); trace = the focus plus everything within 6 hops over need-link edges, each node with `layer`; compliance = not a Cypher query: `views.compliance_rows(needs_path: Path) -> list[dict]` maps `sysml2kit.compliance.compliance(needs)` rows to `{crs, title, features, reuse, partial, statements, domains}` and adds its findings as `{"findings": [...]}`; `view(..., "compliance", ...)` takes them from the server's project. Reuse the kit's function, never reimplement it.

- [ ] **Step 1: Write failing tests** (skip without Neo4j, vehicle loaded): context default contains `driver`, `trailer`, `chargingStation`, `road`; boundary of `VehiclePhysical::vehicleAssembly::driveUnit` has the five ports and neighbours `tractionBattery`, `vehicleControlUnit`, `coolingCircuit`, `ladderFrame`; activity of `F-002` has a `SUCCESSION` `F-006 → F-007` and a `FLOW` labelled `ElectricPower`; variants of `EDU-PC-001` marks `EDU-PC-003` selected and `EDU-PC-002` not; trace of `CRS-003` reaches `SR-005`, `LC-007`, `PC-001`, `STC-005`; compliance rows equal the CRS ids in `compliance.md`; activity of `PC-001` returns empty `nodes` with a `reason`; `view(..., "nope", None)` raises `ValueError`; `view(..., "trace", "NOPE-1")` raises `KeyError`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `views.view` and `views.tree`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(demo): view queries`.

### Task 5: HTTP server

**Files:**
- Create: `demo/explorer/server.py`, `demo/explorer/cypher.py`
- Test: `demo/tests/test_server.py`, `demo/tests/test_cypher.py`

**Interfaces:**
- Consumes: `views.view`, `views.tree`, `search.search`, `load.main`.
- Produces:
  - `cypher.run_read(driver, query: str, params: dict | None = None, limit: int = 500, timeout_s: float = 10) -> dict` → `{"columns": [...], "rows": [[...]], "truncated": bool}`; runs in `session.execute_read` with `neo4j.Query(query, timeout=timeout_s)`; nodes serialised as `{key, name, kind}`, relationships as `{type, src, dst}`. Raises `cypher.CypherError(message)` with the Neo4j message on any failure.
  - `server.app` (FastAPI), `server.create_app(driver, embedder, project: Path, agent_factory) -> FastAPI` for tests. Endpoints exactly as in the spec: `GET /api/tree`, `GET /api/element/{key}`, `GET /api/view/{kind}?focus=`, `GET /api/search?q=&k=`, `POST /api/cypher` (`{"query", "params"}`), `POST /api/ask` (Task 6), `POST /api/reload`, plus `GET /` serving `demo/static/`. `ValueError` → 400, `KeyError` → 404, `CypherError` → 400 with `{"error": message}`.
  - Reload: runs `make -C <project> docs STRICT=` (captures output), and only on exit code 0 runs the loader; on failure returns 422 `{"error": "<last 40 lines of make output>"}` and leaves the graph as it was. A lock rejects a second concurrent reload with 409.
  - Entry point: `python -m explorer.server <project-dir>` binds `127.0.0.1:8000`.
- Example queries for the Cypher panel: `GET /api/cypher/examples` → list of `{title, query}`, at least: composition of a part, constraints on a part and its ancestors (via `REQUIRES` and `SATISFIES`), CRS whose features are not all `platform`, interfaces by domain.

- [ ] **Step 1: Write failing tests**: `test_cypher.py` (Neo4j): `run_read` of `CREATE (n:X) RETURN n` raises `CypherError` and `MATCH (n:X) RETURN count(n)` is 0 afterwards; same for `MERGE`, `MATCH (n) DETACH DELETE n`, `LOAD CSV FROM 'file:///x' AS r RETURN r`; a query returning 600 rows gives 500 and `truncated: true`; every example query runs without error. `test_server.py` (FastAPI `TestClient`, Neo4j): `/api/view/trace?focus=NOPE-1` → 404; `/api/view/nope` → 400; `/api/element/PC-001` → 200 with `qualifiedName == "VehiclePhysical::vehicleAssembly::driveUnit::driveMotor"`; reload against a temp copy of the vehicle project with a syntax error injected → 422 and node count unchanged.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `cypher.py`, `server.py`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(demo): HTTP API with read-only Cypher and reload`.

### Task 6: Agent

**Files:**
- Create: `demo/explorer/agent.py`, `demo/explorer/prompt.md`
- Modify: `demo/explorer/server.py` (`POST /api/ask`)
- Test: `demo/tests/test_agent.py`

**Interfaces:**
- Consumes: `search.search`, `search.neighbourhood`, `cypher.run_read`.
- Produces:
  - Tool functions, plain and testable without the SDK: `agent.semantic_search(driver, embedder, q, k=8) -> str`, `agent.cypher(driver, query) -> str`, `agent.element(driver, key) -> str` — each returns JSON text; errors return `{"error": ...}` text, never raise.
  - `agent.options(project: Path, driver, embedder) -> ClaudeAgentOptions`: in-process MCP server `kit` (`create_sdk_mcp_server`) with tools `semantic_search`, `cypher`, `element`; stdio MCP server `sysml` = `sysml mcp --project <project>/model` (check whether the platform model resolves through the `platform` symlink without the duplicate `Trace` package; if not, say so in the report and pass what works); `system_prompt` from `prompt.md`; `allowed_tools` = `mcp__kit__semantic_search`, `mcp__kit__cypher`, `mcp__kit__element`, `mcp__sysml__outline`, `mcp__sysml__find`, `mcp__sysml__relations`, `mcp__sysml__check`; a `can_use_tool` callback denying every tool whose name does not start with `mcp__kit__` or `mcp__sysml__`; `max_turns=12`.
  - `agent.ask(options, question: str) -> AsyncIterator[dict]` yielding events `{"type": "text", "text"}`, `{"type": "tool", "name", "summary"}` (summary: the tool input, 120 chars max), `{"type": "done"}`, `{"type": "error", "message"}`. Any exception becomes one `error` event followed by end of stream.
  - `POST /api/ask` `{"question"}` → `text/event-stream`, one SSE event per yielded dict (JSON data).
- `prompt.md` states: the RFLP layers and id prefixes, the graph schema (labels, edge types, key properties), that answers come only from tool results, that every element or need mentioned is cited as its key in backticks, and that the agent is read-only.

- [ ] **Step 1: Write failing tests**: tool functions against Neo4j (`element("PC-001")` JSON has `key`; `cypher("CREATE (n) RETURN n")` JSON has `error`; `semantic_search("motor")` returns a list); `options(...)`: `can_use_tool("Bash", ...)` denies, `can_use_tool("mcp__kit__cypher", ...)` allows, `allowed_tools` contains no built-in tool name; `ask` with a stub client whose `receive` raises → yields exactly one `error` event then stops. No test calls Claude.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** against the installed `claude-agent-sdk` version (check its names: `ClaudeAgentOptions`, `ClaudeSDKClient`, `create_sdk_mcp_server`, `tool`, `can_use_tool` return types; adapt the names above if the installed version differs and report it).
- [ ] **Step 4: Run** → PASS. Then one manual call: `uv run python -c` asking "which constraints apply to the drive motor, and where do they come from?" against the loaded vehicle; paste the answer into the report; it must cite `PC-001` and `SR-005`.
- [ ] **Step 5: Commit** `feat(demo): read-only Claude agent over the model graph`.

### Task 7: Page

**Files:**
- Create: `demo/static/index.html`, `demo/static/app.css`, `demo/static/js/main.js`, `demo/static/js/state.js`, `demo/static/js/api.js`, `demo/static/js/layout.js`, `demo/static/js/render.js`, `demo/static/js/panels.js`, `demo/static/vendor/elk.bundled.js` (elkjs 0.9.3, with its licence header)
- Test: `demo/tests/js/layout.test.mjs`, `demo/tests/js/state.test.mjs`, `demo/tests/js/citations.test.mjs`

**Interfaces:**
- Consumes: the HTTP API from Tasks 5 and 6.
- Produces:
  - `state.js`: `focus` store with `setFocus(key)`, `subscribe(fn)`, a breadcrumb from the element's owner path; `history` for back.
  - `layout.js`: `toElk(view) -> elkGraph` (pure: nested `children` from `parent`, ports from `compartments.ports` as ELK ports, edges), `fromElk(laid) -> positioned` (pure).
  - `render.js`: SVG for each node kind — «keyword» header and attribute compartment for parts, port squares on borders, rounded rectangles for actions, stick figures for actors, ellipses for use cases, frames for subjects and boundaries; ME/EE/SW colours as CSS custom properties; click → `setFocus`, double-click → drill down (focus the element and switch to composition or activity as fits).
  - `panels.js`: tree, search box (debounced 200 ms), Cypher panel (examples dropdown, editor, results table with key links), ask panel (SSE via `fetch` + reader, renders text, tool events as a small list, `error` events as an inline error, re-enables input on `done` or `error` or a dropped stream), compliance table.
  - In `panels.js`: `linkCitations(text, knownKeys) -> html` turns backticked keys into focus links and marks unknown ones with class `unresolved`.
- Layout: three columns on desktop (tree | view with kind tabs and breadcrumb | ask/search/Cypher tabs), stacked under 900 px. Colours specific to the project (engineering-drawing feel: dark slate canvas option, blueprint accents); none of: cream/off-white backgrounds, pill-shaped buttons, monospace labels as decoration, numbered section labels.

- [ ] **Step 1: Write failing JS tests** (`node --test demo/tests/js/`): `toElk` nests a port under its part and an action under its frame; `fromElk` keeps keys; `setFocus` notifies subscribers once per change and not for the same key; `linkCitations("see \`PC-001\` and \`NOPE\`", new Set(["PC-001"]))` links `PC-001` and marks `NOPE` `unresolved`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** the page and modules.
- [ ] **Step 4: Run** JS tests → PASS. Start the server against the loaded vehicle and walk the demo script in the browser pane: every view renders for its default focus, focus follows clicks across views, search `PC-001` focuses it, an example Cypher query renders a table, an ask streams and its citations focus elements, stopping Neo4j mid-ask shows an inline error and re-enables input. Take one screenshot per view into the report.
- [ ] **Step 5: Commit** `feat(demo): explorer page with nine views, search, Cypher and ask panels`.

### Task 8: Run command and docs

**Files:**
- Modify: `demo/Makefile` (`demo` target), `README.md` (one short "Model explorer demo" section linking `demo/README.md`)
- Create: `demo/README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: `make -C demo demo PROJECT=../examples/vehicle` (default `PROJECT`): `podman compose up -d` (or `docker compose`, whichever exists), wait until Bolt answers (60 s max, then fail with a message), `make -C $(PROJECT) docs STRICT=`, load, serve.

- [ ] **Step 1: Write** `demo/README.md`: prerequisites, `NEO4J_PASSWORD`, `make -C demo setup` then `make -C demo demo`, the demo script from the spec, the HTTP API (one line per endpoint), the graph schema (labels, edge types, key properties), integrating (copy `explorer/`, point it at your project; auth: the demo runs on the operator's Claude Code login; any app used by others must set `ANTHROPIC_API_KEY` from Claude Console — Anthropic's legal-and-compliance page, "Authentication and credential use").
- [ ] **Step 2: Run** from a clean state (`podman compose down -v`): `make -C demo setup && make -C demo demo` → server up on `http://127.0.0.1:8000`, page loads. Then the demo tests and the full kit check list from Global Constraints → green.
- [ ] **Step 3: Commit** `docs(demo): run command, demo script, API and integration notes`.
