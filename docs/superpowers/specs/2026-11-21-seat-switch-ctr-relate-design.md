# Seat-switch examples, customer test requirements, constraint links, Relate backend — design

## Intent

The demo is for an audience that builds automotive HMI components, and the kit's method must match how their customers actually write RFQs. Three changes follow from the owner's review of the demo:

1. The demo runs where there is no Docker: Neo4j is replaced by Relate (Neo4j's embedded graph database), and the Cypher panel goes — only the agent queries Cypher.
2. The kit's requirement model grows to what real OEM specifications contain: customer requirements classified as functional, non-functional, constraint or information; customer-given verification and validation requirements (environmental, durability, EMC tests…) as their own need type, linked to the supplier's own test measures; non-functional requirements and constraints satisfied directly by constraints in the model. Textual system requirements are written only for what the model cannot express.
3. The e-drive/vehicle examples are replaced by a seat adjustment switch: a platform (the supplier's seat-switch product line) and an RFQ project (an OEM's request for the switches of one car).

## Goals

- `make -C demo demo` needs no container and no database password.
- Every customer requirement carries a class; functional, non-functional and constraint requirements must be covered, information is never a coverage obligation.
- A customer's non-functional requirement or constraint can be satisfied by a model constraint (with an id, so the link is a sphinx-needs link), including plain values (`ipRating == "IP5K4"`), and that counts as coverage.
- Customer test requirements (CTR) exist as needs; each is implemented by at least one supplier test case or answered by a compliance statement.
- A realistic seat-switch RFQ (40–60 customer requirements across the four classes, 8–12 CTRs) that exercises reuse, variants per seat position, a partial match, a not-offered requirement and a commercial statement.
- The demo's trees and V-model show the new types and links, and a meta-model view shows the method itself.

## Non-goals

- Importing customer documents (Word/PDF/ReqIF) into sphinx-needs: the customer requirements are assumed already converted.
- Assessing information items for hidden requirements: handled in another repository. Here information is just information.
- Keeping the e-drive/vehicle examples: they are removed.
- Supporting Neo4j and Relate side by side.

## Anti-goals

- A customer's text edited beyond the permitted fields. Permitted supplier edits to a customer need: `:scope:` (existing) and `:class:` (new). Customer test requirements carry the customer's text unchanged.
- Coverage that can be claimed without a model element or test behind it.
- A demo that looks toy-like: the seat-switch example must read like a real RFQ to an HMI supplier.

## Constraints

- Kit runtime stays standard library only; the bridge (`sysml2kit`) and rules change, the toolchain does not.
- `sysml` fork as pinned (`v0.1.4-kit.2`); everything new must check clean with it.
- sphinx-needs 9.2 rules: `not` is not allowed in `select` (use enum values and `==` as the existing `scope` rules do).
- Relate 1.2.0 (`relate-db` on PyPI, Apache-2.0, in-process, Cypher 25, vector and full-text indexes). Its database object is thread-affine; it has no read-transaction mode.
- All kit checks green at the end: unit suite, `tests/acceptance.py`, `tests/omg_corpus.py`, `make all` on both examples, ruff, plugin validate; demo suite and JS tests.

## Approaches

- **Customer V&V requirements as a field on the CRS vs. a need type (chosen: need type, owner's decision).** OEMs specify test programmes (environmental per their standard, durability, EMC) as their own objects, often spanning many requirements; the supplier's test cases implement them. A field cannot carry that.
- **Constraint links via a constraint id vs. via the bridge exporting any annotated element (chosen: ids).** Ids are the kit's existing pattern, give stable sphinx-needs links, and make the constraint visible in trees and the compliance table. The bridge change is limited to a new need type.
- **Plain-value non-functional requirements linked to the attribute vs. a constraint over it (chosen: constraint, owner agreed).** A constraint states what the design must be and can fail; an attribute states what it is.
- **Relate only vs. Relate and Neo4j (chosen: Relate only).** Same Cypher; one backend to test; integrators who need a server use `relate serve` (Bolt). Risk: Relate 1.2.0 is two days old.
- **Replace vs. add the example (chosen: replace, owner's decision).**

## Part 1 — Demo backend (do first; independent)

- `demo/explorer/db.py` (new): a small adapter over one `relate.Database()` (in memory) that runs every call on one dedicated worker thread (a single-thread executor), exposing what the code uses today: `execute_query(query, params) -> records` (records indexable by name and position), a `write(fn)` transaction, and `read_only(query, params, limit, timeout)` for the agent's Cypher tool.
- Read-only for the agent: run the query inside a transaction that is always rolled back, and reject statements the planner classifies as writes (check what `QueryResult.query_type` reports via `EXPLAIN`; schema and procedure writes included). Test with CREATE, MERGE, SET, DELETE, CREATE INDEX and a write procedure if Relate has one.
- Spike result (2026-11-21, recorded): 13 of 15 view runs return identical results to Neo4j; `interfaces` and `composition` fail on the `PARTS` fragment (a path variable bound over a quantified pattern, `UndefinedVariable: p`) — rewrite it; `db.index.fulltext.queryNodes` takes two arguments (drop the options map, use `LIMIT`); vector index creation, `db.index.vector.queryNodes`, `SEARCH`, the key constraint and `db.awaitIndexes` work.
- The graph is rebuilt in memory at server start and on reload (load is ~0.02 s plus embedding).
- Remove: the Cypher panel (page, `POST /api/cypher`, `GET /api/cypher/examples`, their tests), `compose.yaml`, the Neo4j driver dependency, `NEO4J_*` settings, the Bolt wait in the Makefile, the disposable-Neo4j test setup. The agent keeps its `cypher` tool (via `read_only`) and the example queries move into `prompt.md` as guidance.
- README: run with `make -C demo setup && make -C demo demo`; the integration section names `relate serve` for a server.

## Part 2 — Kit method

Need types and fields (template `ubproject.toml`, `schemas.json`, bridge, docs):

- `crs` gains field `class`: enum `functional`, `non-functional`, `constraint`, `information`; required on every CRS (rule `crs-class`). Existing `scope` stays (`""`, `commercial`, `not-offered`).
- New customer type `ctr` (Customer test requirement), prefix `CTR-`, in Markdown like CRS. Fields: `purpose` enum `verification`, `validation`; `method` enum `test`, `analysis`, `inspection`, `demonstration`. Optional link `applies_to` → CRS (many). Rule `ctr-implemented`: every CTR is implemented by at least one supplier test case (`systest` or `acctest`) or answered by a CST.
- Supplier test cases (`systest`, `acctest`) gain link `implements` → CTR. In the model: `@Implements { need = "CTR-004"; }` metadata on a verification usage (add `metadata def Implements` to `trace.sysml`).
- New model need type `constraint`, prefix `CON-`, from a `ConstraintUsage` with a short id (bridge `NEED_TYPES`). Layer R. It carries `@Satisfies { need = "CRS-…"; }` like a system requirement.
- Coverage rules, by class (replacing `crs-satisfied`'s current single condition):
  - functional: satisfied by a `sysreq` or a `constraint`, and matched by a feature (existing `crs-matched`), as today;
  - non-functional and constraint: satisfied by a `constraint` or a `sysreq`;
  - information: no satisfied/matched/verified rule;
  - `scope: commercial|not-offered` keep their existing exemptions and CST rules.
- Only functional CRS must be matched by a feature. Non-functional and constraint CRS limit the solution space (owner): they are satisfied by constraints, not matched by features. Their reuse status in the compliance table comes from the part their satisfying constraint is owned by (platform part or a part specializing one → `platform`/`variant`; otherwise `new`); the "not answered" finding accepts a constraint link as an answer.
- Partial satisfaction of a non-functional or constraint CRS: `@Satisfies { need = "CRS-…"; partial = true; }` on the constraint (add `partial : Boolean[0..1]` to `Satisfies` in `trace.sysml`), with a system requirement stating the gap — the same gap rule as for partial feature matches.
- Verification (owner agreed):
  - a system test verifies a system requirement or a constraint (`@Verifies { need = "CON-…"; }` on the verification usage — native `verify` only takes requirements), or implements a CTR; `systest-verifies` becomes "verifies a sysreq or constraint, or implements a CTR";
  - a CRS (functional, non-functional, constraint, empty scope) counts as verified when an acceptance test verifies it, or when a CTR that `applies_to` it is implemented by a test (`crs-verified` gains that route — a computed check in `compliance.py`/`gaps.py` if sphinx-needs rules cannot follow the two-hop link);
  - `constraint-verified`: every non-platform constraint that satisfies a CRS or PRQ is verified by a system test.
- Platform requirements (`prq`) get `class` too, under the same rules as CRS (`crs-class` and the class rules select `crs` and `prq`).
- Rules on the constraint need itself: a non-platform `CON-` must satisfy a CRS or PRQ (`constraint-satisfies`). By the authoring pattern it is owned by the part (or part definition) whose attributes it constrains; not enforced by a rule. In an RFQ build the bridge drops platform `@Satisfies` links (existing behaviour), so RFQ CRS are satisfied by `CON-`s declared in the RFQ model, typically over platform attributes.
- `gaps.py` maps the new rules to layers (`crs-class`, `ctr-implemented` → R/V as fits; the existing test enforces every rule has a layer).
- `compliance.py`: the table shows each CRS's class; constraint links count as satisfying; CTR rows get their own small table (CTR, purpose, method, implementing tests or statement).
- Method docs: `structure.md`, `glossary.md`, `requirements-analyst.md`, `test-designer.md` (implements CTRs), `rfq/SKILL.md` and `references/questions.md` (classify each CRS; capture CTRs; a non-functional/constraint CRS is answered by a model constraint, a textual SR only for what the model cannot express), `sysml-author/references/patterns.sysml` (constraint with id and `@Satisfies`; verification with `@Implements`). README "Upgrading" section lists the new fields and rules.

## Part 3 — Seat-switch examples (replace e-drive and vehicle)

Directories `examples/seat-switch-platform/` (platform, id tag `SSW-`) and `examples/seat-switch-rfq/` (RFQ project, `platform` symlink to the platform). The old directories, their README/CI references and acceptance anchors are removed or replaced.

**Platform: seat adjustment switch product line.**
- Features: seat adjustment input (fore/aft, height, recline, lumbar), comfort function input (massage, heating, cooling), illumination (night design), vehicle communication (LIN), diagnostics.
- Logical: keypad, position sensing, switch controller, LIN communication, illumination, enclosure.
- Physical, one domain each: ME housing (left-hand / right-hand mirrored — clip position), knob and caps, seal; EE PCB with hall sensors or tact switches, LIN transceiver, LEDs; SW switch firmware.
- Variations: `housing` (LH, RH — mirrored parts); `buttonSet` (base, heating, heating + cooling, massage + heating + cooling).
- Attributes and constraints (with `CON-` ids where a platform requirement needs them): actuation force, travel, haptic profile, operating voltage, temperature range, IP class, ESD, durability cycles, luminance, LIN version.
- Platform PRQs, use cases, firmware SWRs, system tests, JUnit results, as the e-drive platform had.

**RFQ: an OEM's seat switches for one car.**
- Positions: driver, co-driver, rear left, rear right. Each is an RFQ part that selects a housing variant (mirrored by side) and a button set (e.g. driver: LH, massage + heating + cooling; co-driver: RH, heating + cooling; rear: LH/RH, heating).
- The example covers all three engineering domains (ME, EE, SW) and cybersecurity, plus production and workshop requirements. Topics are sphinx-needs `tags` on the CRS (`cybersecurity`, `production`, `workshop`), not new classes; cybersecurity is cross-cutting, not a fourth engineering domain.
  - Cybersecurity: authenticated firmware update (signed images, secure boot in the firmware), protected diagnostic access (security access before writing), no open debug interface in series parts, LIN message plausibility.
  - Production: end-of-line test of every key and LED, flashing and variant coding at end of line, DMC traceability label, mistake-proofing so a left-hand housing cannot be fitted on a right-hand part.
  - Workshop: fault memory readable via diagnostics, software update in the workshop over the vehicle bus, switch replaceable without removing the seat, spare-part numbering per variant.
- 40–60 CRS across the classes, written like an OEM spec (numbered, terse, some long): functional (adjustment directions, comfort buttons, feedback, illumination modes, LIN signals, diagnostics), non-functional (actuation force window, haptic feedback, response time, luminance and colour, durability), constraint (IP class, −40 … +85 °C, 9–16 V, LIN 2.2, ESD ±8 kV, mass, envelope, materials), information (SOP, volumes, mounting location, applicable OEM standards list).
- 8–12 CTRs: environmental test programme per the OEM standard, durability per key, haptic measurement, EMC, ESD, ingress, validation in vehicle (purpose validation).
- Coverage: functional CRS matched by features (some fully from platform, one partial — e.g. the OEM asks for more durability cycles than the platform is rated for, with an SR stating the gap), non-functional and constraint CRS satisfied by `CON-` constraints in the model (plain values as constraints), at least one textual SR for something the model cannot express, one `not-offered` CRS with a not-comply CST, one `commercial` CRS with a CST.
- CTRs implemented by the RFQ's system and acceptance tests (`@Implements` / `:implements:`), with JUnit results.
- `make all` green; compliance table shows classes, reuse and CTRs.

**Tests and fixtures that move with the example:** `tests/acceptance.py` (baselines and mutations re-anchored on the seat switch; new mutations: drop a CRS class → `crs-class`; unlink a CTR → `ctr-implemented`; a non-functional CRS with only an attribute and no constraint → not satisfied), `tests/test_template.py`, demo tests (`demo/tests` keys pinned to vehicle ids move to seat-switch ids), README, CI paths.

## Demo changes that follow Part 2 and 3

- Requirements tree: CTRs in their own group ("Customer test requirements"), each listing `implemented by` tests and `applies to` CRS; CRS rows show their class.
- V-model: CTRs on the right leg at level 1 (verification) with the supplier tests that implement them; a CRS row shows its verification route.
- Default focus and prompt text name the seat switch.

## Part 4 — Meta-model view in the demo

A new view kind `metamodel` ("Meta-model") that shows the kit's method as a diagram, so the audience sees the rules behind the model before the model itself.

- Nodes: the need types of the loaded project (crs, ctr, prq, cst, usecase, feature, function, component, interface, physical, physinterface, constraint, sysreq, systest, acctest, testresult), grouped by RFLP layer (R, F, L, P, V) as frames, each with its instance count in this project.
- Edges: the link types between need types — declared ones from the project's `docs/ubproject.toml` (link names) combined with what the graph actually holds (`MATCH (a:Need)-[r]->(b:Need)` grouped by need type and relationship type), each labelled with the link name and its instance count; a declared link with no instances is drawn dashed.
- Rules: each edge or node that a `docs/schemas.json` rule constrains carries the rule id as a tag (e.g. `crs-verified`), so the meta-model doubles as a map of what the docs build enforces.
- Interaction: clicking a type lists its instances in the inspector (each a focus link); clicking an edge lists the link instances. The view ignores the focus otherwise.
- Data: server reads the project's `ubproject.toml` and `schemas.json` (standard library `tomllib`, `json`) plus one graph query; no new dependency. Laid out with ELK like the other views (layers as frames).
- Tests: the vehicle-free seat-switch RFQ shows `crs → constraint` (satisfies) and `systest → ctr` (implements) with non-zero counts; a declared link with no instances is marked unused; rule ids attach to the right edges.

## Order

Part 1 → Part 2 → Part 3 → Part 4 (Part 3 needs Part 2's fields; demo tests move with Part 3; the meta-model view shows Part 2's types and is tested on Part 3's example).

## Left to the builder

Exact customer requirement texts and values (plausible for an automotive seat switch), id numbering, the OEM standard names (fictional: no real OEM's standard or branding), layout of the CTR table, Relate adapter internals.
