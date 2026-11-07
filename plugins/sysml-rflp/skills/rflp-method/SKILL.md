---
name: rflp-method
description: The RFLP (Requirements, Functional, Logical) structure this plugin uses, from customer requirements to acceptance tests - artifact kinds, ids, where each is written, required links and quality criteria. Use when deciding where something belongs, which link to use, or why an RFLP rule fails.
---

# RFLP method

Read `references/structure.md` before creating or reviewing RFLP artifacts. It holds:

- the artifact table (CRS, UC, SR, F, LC, LI, STC, ATC, test results, SWR) with id prefixes, where each is written (RST or SysML) and its outgoing links;
- the model layout (one package per layer and file, system-prefixed package names);
- the rule table with the layer each rule gates (rule ids match `docs/schemas.json`);
- writing-quality criteria the reviewer applies.

Two principles decide most questions:

1. **One home per item.** Customer requirements and acceptance tests are RST; use cases, system requirements, functions, logical architecture and system tests are SysML. Generated needs are never edited by hand.
2. **Links inside the model are native SysML; links leaving it are `Trace` metadata.** `perform`, `satisfy`, `allocate`, `verify` inside the model; `@Realizes` / `@Satisfies` / `@Verifies { need = "CRS-001"; }` to RST needs.

For SysML syntax use the `sysml-author` skill; to run the whole method layer by layer use the `rflp` skill.
