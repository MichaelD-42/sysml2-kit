---
name: sysml-author
description: Create and change SysML v2 models (.sysml files) - use cases, requirements, actions, parts, ports, allocations, satisfy/verify, Trace metadata links to sphinx-needs. Use when writing or editing any .sysml file.
---

# SysML v2 authoring

`references/patterns.sysml` is a checked example of every construct the pipeline maps; copy from it. The `sysml` MCP server answers syntax and name questions: `notation` (how to write a construct), `visible_names` (what resolves at a point), `outline`, `library_search`, `check`.

## Conventions

- One package per layer and file, system-prefixed (`VehicleFunctions`), never a bare library-like name (`UseCases`).
- Elements that become needs get a declared short name `<'SR-012'>`; prefix by kind (see `rflp-method`). Next free number: `grep -rhoE "<'SR-[0-9]+'>" model | sort -V | tail -1`. Never reuse or renumber an id; docs link to it.
- Every short-named element has `doc /* ... */`; it becomes the need text.
- Model traced elements as usages (`requirement <'SR-001'> range { ... }`, `action <'F-002'> propel;`, `part <'LC-002'> powertrain;`). `satisfy`, `allocate` and `perform` must point at usages, and both ends need short names.
- Links to RST needs: `@Realizes { need = "CRS-001"; }` / `@Satisfies` / `@Verifies`, after `private import Trace::*;`.
- Keywords cannot be names (`loop`, `state`, `action`, `port`, `in`, `out`, `then`, `first`, `entry`, `do`, `exit`, ...).

## Rule

The plugin runs `sysml check` after every `.sysml` write and shows errors; fix them before moving on (`sysml-lint` skill for the loop). Before finishing, run `make all` (or `make docs STRICT=` mid-workflow).
