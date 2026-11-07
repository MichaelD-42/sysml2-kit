---
name: rflp
description: Run the RFLP workflow - derive use cases and system requirements from customer requirements, then functions, then logical architecture, then system and acceptance tests - one layer at a time with a review and the user's approval between layers. Use when the user asks to model a system from customer requirements, to "do RFLP", or to continue an RFLP model to the next layer.
---

# RFLP workflow

Precondition: an initialized project (`sysml-init` skill), customer requirements in `docs/customer/*.rst`, and `make lint` passing. Read the `rflp-method` skill first.

Work one layer at a time. Never start a layer before the user approved the previous one: a wrong use case propagates into every function and component below it.

| Step | Agent | Produces | Gate rules (must have no violations) |
|---|---|---|---|
| 1 R | `requirements-analyst` | UC, SR | `crs-satisfied`, `usecase-realizes`, `sysreq-satisfies` |
| 2 F | `functional-architect` | F, `perform` in UCs | `usecase-realized` |
| 3 L | `logical-architect` | LC, LI, connections, `allocate`, `satisfy` | `function-allocated`, `component-used`, `sysreq-satisfied` |
| 4 V | `test-designer` | STC (SysML), ATC (RST) | all remaining: `systest-verifies`, `acctest-verifies`, `sysreq-verified`, `usecase-verified`, `crs-verified` |

For each step:

1. Hand the layer to its agent with the scope (all CRS, or the ones the user named).
2. Run the `rflp-reviewer` agent on that layer. It runs `make lint` and `make docs STRICT=`, filters schema violations to the gate rules, and reviews writing quality.
3. Fix blocking findings (via the authoring agent), re-review, up to 3 rounds.
4. Show the user: what was added (ids and one-line titles), the trace diagram `docs/_generated/trace.svg`, and the reviewer's remaining findings. Ask for approval, changes, or stop. Do not continue without an answer.

After step 4, `make all` (strict) must pass. Report coverage from `docs/_build/html/traceability.html`.

Re-entering: to change an upstream layer later, edit it, then re-run the review for every layer below it; rule violations show what the change broke.
