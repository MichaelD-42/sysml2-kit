# Model explorer demo

A local web app over a kit project. It loads the project's SysML v2 model and needs into Neo4j, draws nine views of it, and answers questions about the product through Claude, which queries the graph instead of answering from memory. It opens `examples/vehicle` (which imports `examples/edrive-platform`) by default. It runs on localhost for the person running it: no login, no hosting, and nothing on the page writes to the model.

## Run it

You need the kit's tools on `PATH` (`sysml`, `sysml2kit`, `sphinx-build`, `make tools` in a project installs them), uv, make, podman or docker, and Claude Code, logged in. Neo4j runs as a container from [`compose.yaml`](compose.yaml), bound to localhost.

```sh
export NEO4J_PASSWORD=...     # the password Neo4j is created with; never commit it
make -C demo setup            # uv sync, and downloads the embedding model once
make -C demo demo             # http://127.0.0.1:8000
```

`make -C demo demo` starts Neo4j (`podman compose`, else `docker compose`), waits up to 60 s for Bolt, builds the project with `make docs STRICT=` (so rule violations are reported, not fatal), loads it and serves. Use another project with `PROJECT=path/to/project`. Stop Neo4j with `make -C demo down`; `podman compose down -v` also drops the data. The project's `build/model.json` and `build/needs/needs.json` must exist, which the build above writes. After editing the model, the "Rebuild and reload" button (or `POST /api/reload`) rebuilds and reloads.

After setup the page needs no network except the Claude connection for the ask panel; the JavaScript libraries are vendored.

## Demo script

About ten minutes, without leaving the page. Open the vehicle RFQ. Show the system context, then drill into the drive unit's boundary: battery, vehicle control unit, cooling and chassis around it. Show the interfaces coloured by domain (ME, EE, SW), the activity of propulsion, and the variants view with the 80 kW selection. Ask "which constraints apply to the drive motor, and where do they come from?". The answer cites the motor's attributes, the constraint and the CRS behind them, each as a link; click one and every view follows. Then open the Cypher panel and run the same question as a query.

One focus element is shared by all views. Selecting an element anywhere (a view, the tree, a search hit, an id in an answer) moves the focus; double-click drills down, and the breadcrumb goes back up.

## HTTP API

All JSON, read-only except reload. Errors are `{"error": "..."}`: 400 for a bad value or query, 404 for an unknown key. Request validation errors (a missing field, `k` out of range) are 422 `{"detail": ...}`. The POST endpoints need `Content-Type: application/json` and answer 415 `{"detail"}` without it, so a cross-site form cannot trigger them. A `Host` header other than `127.0.0.1` or `localhost` gets 400, against DNS rebinding.

- `GET /api/tree`: the composition hierarchy for the tree panel.
- `GET /api/keys`: every node key, for resolving ids in answers.
- `GET /api/element/{key}`: one element or need with its properties and direct edges.
- `GET /api/view/{kind}?focus={key}`: nodes and edges of one view, laid out by the client. `kind` is `context`, `boundary`, `interfaces`, `activity`, `composition`, `variants`, `usecases`, `trace` or `compliance`. Without `focus`, the structure views open on `VehicleLogical::vehicle` if the project has it, else on the first top-level part a package owns that is not a platform need (by key); activity opens on the project feature with the most actions (propulsion, `FEAT-002`, for the vehicle); variants, use cases and trace open on the first project variation, use case and CRS by key.
- `GET /api/search?q=&k=`: hybrid semantic and full-text hits, `k` from 1 to 50 (default 10).
- `GET /api/cypher/examples`: the example queries.
- `POST /api/cypher` with `{"query", "params"}`: one query in a read-access transaction, with a row limit and a timeout.
- `POST /api/ask` with `{"question"}`: server-sent events: `text`, `tool` (name and short summary), `done` or `error`.
- `POST /api/reload`: runs `make docs STRICT=` in the project, then the loader. 200 `{"nodes", "edges"}`; 409 while another reload runs, 422 with the build log's tail if the build fails (the graph is kept), 500 if the load fails. The page sends an empty JSON body `{}`.

## Graph schema

Every node has the label `Node` and a unique `key`. Model elements also have `Element` and their metaclass (`PartUsage`, `ActionUsage`, `ConstraintUsage`, ...). Needs have `Need` and their need type (`crs`, `sysreq`, `function`, `component`, `physical`, `systest`, `testresult`, ...). A model element that is a need has all of these, and its key is the need id; needs that are not model elements (CRS, CST, PRQ, test results) are `Need` nodes only.

Properties: `key`, `uid` (export `@id`), `name`, `qualifiedName`, `shortName`, `kind`, `isVariation`, `doc`, `searchText`. Needs add `title`, `content`, `domain` (ME/EE/SW), `platform`, `variant`, `reuse`, `layer` (R/F/L/P/V) and `source`. Attribute usages carry `value` and `unit`; constraint usages carry `expression`. The loader reads values and expressions from the export's text bodies and does not evaluate them.

Edges: `OWNS`, `TYPED_BY`, `SPECIALIZES` (subsetting, redefinition and subclassification; implied ones are dropped), `CONNECTS`, `FLOW` (property `item`), `SUCCESSION`, `PERFORMS`, `SUBJECT`, `REQUIRES` (a requirement's `require constraint`), plus each needs link type in upper case: `SATISFIES`, `ALLOCATED_TO`, `VERIFIES`, `REALIZES`, `MATCHES`, `PARTIAL_MATCHES`, `ANSWERS`, `TESTS` and so on. Indexes: a vector index (384 dimensions, `BAAI/bge-small-en-v1.5` through fastembed) and a full-text index, merged by rank in search.

## Integrating

Copy `explorer/` into your application and point it at a project directory. `load.py` builds the graph from the project's build output and has no web dependency; `graph.py` is the pure transformation, `views.py`, `search.py` and `cypher.py` are the queries, `server.py` is a thin FastAPI layer, and `agent.py` is the Claude setup, short enough to read in one sitting. The agent has three in-process graph tools (`semantic_search`, `cypher`, `element`) and four tools from the `sysml` MCP server (`outline`, `find`, `relations`, `check`). It has no built-in file, shell or web tools. `prompt.md` holds its instructions, including the rule to cite ids from tool results. Each tool call the agent makes is shown as a tool event in the Ask panel above the answer, with the first 120 characters of its input, so its Cypher queries are visible.

Limit: the `sysml` MCP tools accept file paths, so the agent can read SysML files outside the project, read-only. Run it only where that is acceptable, or replace those tools with graph queries.

Authentication: the demo uses Claude Code's own login, which is the individual use Anthropic's terms allow when you run it yourself on your own machine. An application that other people use must not route their requests through your plan login. Set `ANTHROPIC_API_KEY` from the Claude Console instead; see Anthropic's legal-and-compliance page, "Authentication and credential use". No code in `explorer/` depends on which one is used.

## Tests

```sh
make -C demo test
```

The tests need a reachable Neo4j (`NEO4J_URI`, and `NEO4J_AUTH=none` for a disposable instance without a password) and skip the graph tests when none answers. No test calls a model; run the demo script by hand to check the ask panel.
