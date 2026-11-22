---
name: sysml-author
description: Create and change SysML v2 models (.sysml files) - use cases, requirements, actions, parts, ports, allocations, satisfy/verify, Trace metadata links to sphinx-needs. Use when writing or editing any .sysml file.
---

# SysML v2 authoring

`references/patterns.sysml` is a checked example of every construct the pipeline maps; copy from it. The `sysml` MCP server answers syntax and name questions: `notation` (how to write a construct), `visible_names` (what resolves at a point), `outline`, `library_search`, `check`. To read an existing model, use `find` (elements by kind, namespace, name, or a relation they lack: `kind: RequirementUsage, without: verifies`), `relations` (every link of one element both ways, by qualified or short name), `definition` and `references` (where a name is declared and used) and `impact` (what a change to an element reaches) instead of opening files. To rename, ask `rename` for the edits (it writes nothing) and apply them. The server reads what `make` builds: the project and the platform the Makefile names (`make -s mcp`). If its `check` reports platform names as unresolved, Claude was started outside the project or the Makefile lacks the `mcp` target; then `relations` and `trace` miss links into the platform (`sysml2kit gaps` never does). If the server says it has no tool `find` or `impact`, the installed `sysml` predates these tools: run `make tools`.

## Conventions

- One package per layer and file, system-prefixed (`VehicleFunctions`), never a bare library-like name (`UseCases`).
- Elements that become needs get a declared short name `<'SR-012'>`; prefix by kind (see `rflp-method`). Next free number: `grep -rhoE "<'SR-[0-9]+'>" model | sort -V | tail -1`. Never reuse or renumber an id; docs link to it.
- Every short-named element has `doc /* ... */`; it becomes the need text.
- Model traced elements as usages (`requirement <'SR-001'> range { ... }`, `action <'F-002'> propel;`, `part <'LC-002'> powertrain;`). `satisfy`, `allocate` and `perform` must point at usages, and both ends need short names.
- Links to RST needs: `@Realizes { need = "CRS-001"; }` / `@Satisfies` / `@Verifies`, after `private import Trace::*;`.
- Keywords from `Trace` set the kind: `#Feature action` (noun name), `#Mechanical`/`#Electrical`/`#Software` on `part` and `port` (exactly one), `#Assembly` on the part that is the product as built (no domain); the id prefix must match (`FEAT-`, `PC-`, `PI-`). Reuse a platform part or variant by subsetting, `part <'PC-001'> x :> Platform::a::b;`, not by redefining it; `:>>` only fills a slot the part inherits (`part <'PC-002'> y :>> housing :> Platform::housing::housingLH;`). Constraints sit on physical parts, never on a logical component, and must hold for the values the part states (the bridge evaluates them). `@Matches { need = "CRS-001"; partial = true; }` states a feature's coverage.
- Keywords cannot be names (`loop`, `state`, `action`, `port`, `in`, `out`, `then`, `first`, `entry`, `do`, `exit`, ...).
- A name is declared once per namespace, inherited members included: a constraint or part on a part that subsets a platform part must not reuse a name the platform part already has (`check` reports it at the second declaration). A variant member names its kind: `variant part w;` declares one, bare `variant w;` refers to an existing usage.

## Rule

The plugin runs `sysml check` after every `.sysml` write, then the bridge (`sysml export` + `sysml2kit needs`), and shows errors: language errors, duplicate ids, link ends without a short name, and requirement texts without exactly one `shall` or with a vague term. Fix them before moving on (`sysml-lint` skill for the loop). Before finishing, run `make all` (or `make docs STRICT=` mid-workflow).
