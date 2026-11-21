# Model explorer demo — design

## Intent

A local web app that shows what sysml2-kit can do, and doubles as a reference for integrating a kit project into a real application. It opens an RFQ project (default `examples/vehicle`, which imports `examples/edrive-platform`), shows the model in several interactive diagram views, and lets a person ask questions about the product in plain language. Claude, run through the Claude Agent SDK, answers from the model and its needs, not from memory.

The questions it is built for are the ones a person or an agent asks to understand a product: navigating its composition and hierarchy ("what is the drive unit made of?", "where does the inverter sit?"), and asking about non-functional attributes and constraints ("what limits the 80 kW motor?", "which requirements constrain the cooling?"). Answering them takes semantic search to find where to start plus graph traversal to follow structure and trace links, so the model goes into Neo4j with a vector index.

Audience: people being shown the kit (colleagues, customers, MBSE practitioners), and developers who will copy the server to integrate a kit project into their own tools. The second group means the server's HTTP API and the loader are part of the deliverable, not just the page.

## Goals

- Nine views, all generated from the model, never drawn by hand: system context, system boundary, interfaces, activity, composition, variants, use cases, traceability, compliance.
- Dynamic: one focus element shared by all views. Selecting an element anywhere (a view, the hierarchy tree, a search hit, an id in a chat answer) moves the focus, and each view re-scopes to it — the activity of the selected function, the interfaces of the selected part, the trace chain through the selected requirement. Double-click drills down; a breadcrumb shows the composition path and goes back up.
- Search box for people: hybrid semantic + full-text search over elements and needs; hits show their type, id and owner, and selecting one focuses it.
- Ask panel: a chat with an agent that has a semantic search tool, a read-only Cypher tool, and the existing `sysml` MCP tools (`find`, `relations`, `outline`). Answers stream, cite element and need ids, and every cited id is a link that focuses the element.
- Cypher panel: a read-only query editor with a handful of example queries (composition of a part, all constraints on a part and its ancestors, CRS without a platform match, interfaces by domain), results as a table whose ids are links.
- A richer e-drive example, so the views and answers have content (see "Example enrichment").
- One command to run it locally: start Neo4j, build the project, load it, serve.

## Non-goals

- Editing the model from the page. The agent and the Cypher panel are read-only.
- Users, login, hosting, publishing. It runs on localhost for the person running it.
- Full conformance to the SysML v2 graphical notation. The views borrow its conventions (see "Views") and stop there.
- Live sync with the `.sysml` files. Reload is an explicit action (a button and an endpoint that rebuild and reload).
- Any change to the `sysml2kit` package's dependencies. It stays standard library only.

## Anti-goals (a failure even if it works)

- Answers not grounded in the model: an answer that states a value, part or requirement without a tool result behind it. The system prompt requires citing ids from tool results, and the answer renderer marks ids it cannot resolve in the graph.
- A demo that needs the network while it runs. JavaScript libraries are vendored; the embedding model is downloaded once at install and cached.
- Secrets in source. The Neo4j password comes from the environment; Claude auth is whatever Claude Code already has.
- Views that look empty or toy-like because the model is thin. That is why the example is enriched first.

## Constraints

- Machine: podman (emulating `docker`), node without npm, uv, Claude Code 2.1.325. So no frontend build step: plain HTML, CSS and ES modules, with vendored libraries.
- Claude auth: the Agent SDK uses Claude Code's own authentication. Running it on the owner's Pro/Max login, on their machine, operated by them, is the use Anthropic's terms describe ("ordinary, individual usage of Claude Code and the Agent SDK", legal-and-compliance page, read 2026-11-21). Anthropic directs developers building products or services on the SDK to API keys and forbids routing other users' requests through plan credentials. So: the demo is never handed to others to operate on the owner's login, and the README tells integrators to set `ANTHROPIC_API_KEY`. No code depends on which auth is used.
- The kit's own pipeline must stay green after the example enrichment: unit tests, `tests/acceptance.py`, `sphinx-build -W` of both examples, `sysml2kit gaps`, the OMG corpus.
- Neo4j Community 5.x (vector indexes need 5.11 or later), run as a container. It is GPLv3 and runs as a separate service, so it does not affect the kit's MIT license.

## Approaches

Considered for the query side:

- **A. Neo4j with a vector index (chosen).** A loader reads the project's `sysml export` JSON and needs JSON into Neo4j and writes one search text per node, embedded by a local model into a Neo4j vector index. The agent and the page use the same semantic search, Cypher and element endpoints. Gives Cypher (wanted) and is what a real application would integrate with. Costs a container and a reload after each model rebuild.
- **B. Embedded, no database.** An in-memory graph in the Python server with sqlite-vec for vectors and fixed query tools. One install, no container, but no Cypher and little to show integrators.
- **C. Agent only.** No index; the agent uses the `sysml` MCP tools and reads the needs. No infrastructure, but no search for people and no path to a large platform catalog.

The owner picked A ("always wanted to play with that one").

## Architecture

All new code lives in `demo/` at the repository root, with its own `pyproject.toml` (Python, managed with uv). The kit is untouched except for the example enrichment.

- `demo/compose.yaml`: Neo4j Community 5.x with the password from `NEO4J_PASSWORD`, data in a named volume, bound to localhost only.
- `demo/explorer/load.py`: the loader. Input: a kit project directory. It runs nothing itself; it reads `build/model.json` (the `sysml export` of model plus platform) and `build/needs/needs.json`, which `make` in the project already writes. It clears the database and writes the graph described below in one transaction, then builds the indexes.
- `demo/explorer/server.py`: the HTTP server (framework is the builder's call; it must stream, for the chat). Endpoints, all JSON and all read-only except reload:
  - `GET /api/tree` — composition hierarchy for the tree panel.
  - `GET /api/element/{id}` — one element or need with its attributes, owner path, and direct links.
  - `GET /api/view/{kind}?focus={id}` — the nodes and edges of one view for a focus, laid out on the client.
  - `GET /api/search?q=` — hybrid search hits.
  - `POST /api/cypher` — runs one query in a read-access transaction with a row limit and a timeout.
  - `POST /api/ask` — streams the agent's answer (server-sent events): text deltas, tool calls (name and a short summary, shown in the panel so people see the agent query the model), and the final answer.
  - `POST /api/reload` — runs `make` in the project, then the loader.
- `demo/explorer/agent.py`: the Agent SDK setup, kept small so an integrator can read it in one sitting. In-process tools `semantic_search`, `cypher` (same read-only guard as the endpoint) and `element`, plus the `sysml` MCP server over stdio pointed at the project. No file, shell or web tools. The system prompt states the RFLP layers, the graph schema and the citation rule.
- `demo/static/`: the page — `index.html`, ES modules, vendored ELK.js for layout. The server computes view content from the graph; the client lays it out with ELK and draws SVG.
- `demo/README.md`: run it, the demo script (below), the HTTP API, the graph schema, and how to integrate (including the API-key note).
- `make demo` (in `demo/Makefile`): `podman compose up -d`, `make -C <project>`, load, serve on `http://localhost:8000`.

## Graph

Nodes come from the export's elements, not its relationship elements: definitions and usages a person would name (parts, ports, actions, use cases, actors, attributes, constraints, requirements, interfaces, items, connections, flows, successions, metadata as properties). Each `:Element` node gets a second label for its metaclass (`:PartUsage`, `:ActionUsage`, …) and the properties `uid` (export `@id`), `name`, `qualifiedName`, `shortName` (the need id such as `PC-001`, when there is one), `doc`, `file`, `line`, and from the needs: `layer` (R/F/L/P/V), `domain` (ME/EE/SW), `platform`, `variant`, `reuse`. Attribute usages become nodes with `value` and `unit` so constraints and non-functional values can be queried.

Needs that are not model elements (CRS, CST, PRQ, test cases and results from Markdown and JUnit) become `:Need` nodes keyed by need id; model elements that are needs carry the same id in `shortName`, so the two meet on it.

Edges: `OWNS` (owning membership), `TYPED_BY`, `SPECIALIZES` (subclassification, subsetting, redefinition — `isImplied` ones dropped), `CONNECTS` (connection ends, to ports), `FLOW` (with item type), `SUCCESSION` (first → then), `PERFORMS`, and every needs link type as its own edge in upper case (`SATISFIES`, `ALLOCATED_TO`, `VERIFIES`, `REFINES`, `SPECIALIZES` already covered, `MATCHES`, `PARTIAL_MATCHES`, `ANSWERS`, …).

Search text per node: name, metaclass keyword, doc, owner path, attribute values with units, and the texts of needs linked to it. Embedded with a small local model (default: fastembed `BAAI/bge-small-en-v1.5`, 384 dimensions) into a vector index; a full-text index on name, `shortName` and the search text catches ids and exact terms. Hybrid search merges both by rank.

## Views

Notation borrows SysML v2 conventions: rectangles with a «keyword» header and compartments, ports as small squares on the border, actions as rounded rectangles, actors as stick figures, use cases as ellipses, the subject as a frame. ME/EE/SW have one colour each, used wherever a domain applies.

1. **System context** — the system of interest as a black box, actors and external systems around it, the connections and flows crossing between them. Focus: the system of interest, the vehicle.
2. **System boundary** — the system's frame with its boundary ports on the edge, its direct parts inside, and the connections from parts to boundary ports.
3. **Interfaces** — parts of the focus with their ports and connections, item types on the connections, coloured by domain; interface definitions listed with their ends.
4. **Activity** — actions of the focus function with successions (control flow) and flows (object flow, item named); optional swimlanes by the component each action is allocated to.
5. **Composition** — the part hierarchy below the focus, logical or physical, with an attributes compartment (value and unit).
6. **Variants** — variations, their variants and attribute differences, and which variant the RFQ selects (the part that subsets it); an unselected variation is marked.
7. **Use cases** — subject, actors, use cases, includes.
8. **Traceability** — the RFLP chain through the focus: CRS → SR/FEAT → F → LC → PC → tests and results, with reuse status.
9. **Compliance** — the compliance table, each row's ids as links.

## Example enrichment

Done in the kit's examples, through the kit's own conventions, before the demo is built:

- Attributes with values and units on the main parts (rated and peak power, peak torque, mass, max speed, DC-link voltage, coolant temperature limit, IP rating), and different values on the 50 kW and 80 kW variants.
- A few constraints (for example peak torque against the motor's limit, coolant temperature against the inverter's derating limit).
- `doc` comments on the main parts, actions and use cases.
- Item definitions (torque, electric power, CAN frame, coolant) and interface definitions; flows in the main actions.
- The vehicle stays the system of interest (owner's choice). Its context gets external actors and systems: driver, passenger, trailer, charging station, road.
- A physical drive-unit assembly in the RFQ (`driveUnit`, subsetting the platform's `eDrive`) owning the motor, inverter and control software parts, so the composition view has depth. Its boundary view shows its neighbours inside the vehicle: traction battery, vehicle control unit, cooling circuit, chassis (the VCU and cooling circuit are new vehicle parts).

The enriched examples must keep every kit check green. Every new element that the RFLP rules cover gets its links, so the docs build still passes.

## Demo script (success)

In about ten minutes, without leaving the page: open the vehicle RFQ; system context, then drill into the drive unit's boundary (battery, VCU, cooling, chassis around it); interfaces coloured by domain; the activity of propulsion; the variant view showing the 80 kW selection; ask "which constraints apply to the drive motor, and where do they come from?" and get an answer that cites the motor's attributes, the constraint and the CRS behind them, each a link; click one and every view follows; open the Cypher panel and run the same question as a query.

## Tests

- Loader against a small fixture export plus needs file: node and edge counts, labels, attribute values, implied relationships dropped. Runs without Neo4j where possible (the loader builds its statements from plain data first).
- View queries, search and the read-only Cypher guard against a live Neo4j; skipped with a message when none is reachable.
- Agent tools tested directly, without Claude. No test calls a model; a scripted smoke run of the demo script is manual and documented.
- CI (builder's call, recorded): the existing `ruff` job already covers `demo/`; the demo's tests run locally only and are not added to CI, since they need a Neo4j service and the embedding model.

## Constraints and the CRS behind them (builder's call, recorded)

Constraints and attributes stay plain model elements; the kit gets no new need type. A constraint reaches a customer requirement through the graph: the system requirement that states it holds it as a `require constraint` (for example SR-005 acceleration requires the peak-torque constraint), and the SR traces to its CRS as today. The loader turns `require constraint` membership into a `REQUIRES` edge, and the agent and the traceability view follow it.

## Open risks for the builder to check first

- Checked 2026-11-21 with a probe model: the fork's `check` accepts ISQ-typed attributes with units and constraint expressions, and `export` carries `Documentation.body`, the attribute value as a `TextualRepresentation` body (`80 [kW]`) and the constraint body likewise (`peakTorque <= 310 [N*m]`). The loader reads values and constraints from those texts (number and unit split from the value text); it does not evaluate expressions.
- Whether the Agent SDK version installed works with Claude Code 2.1.325's auth from a Python server process.

## Left to the builder

The web framework, ELK layout options, colours, exact property names, search ranking weights, the system prompt's wording, and the example's exact attribute values (plausible for a passenger-car e-drive).
