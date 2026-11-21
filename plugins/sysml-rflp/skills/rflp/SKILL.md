---
name: rflp
description: Run the RFLP workflow - derive use cases and system requirements from customer requirements, then features and functions, then logical architecture, then physical components, then system and acceptance tests - one layer at a time with a review and the user's approval between layers. Use when the user asks to model a system from customer requirements, to "do RFLP", or to continue an RFLP model to the next layer.
---

# RFLP workflow

Precondition: an initialized project (`sysml-init` skill), customer requirements in `docs/customer/*.md`, and `make lint` passing. Read the `rflp-method` skill first.

Work one layer at a time. Never start a layer before the user approved the previous one: a wrong use case propagates into every function and component below it.

| Step | Agent | Produces | Gate rules (must have no violations) |
|---|---|---|---|
| 1 R | `requirements-analyst` | UC, SR, CST for commercial and not-offered CRS | `crs-satisfied`, `usecase-realizes`, `sysreq-satisfies`, `cst-compliance` |
| 2 F | `functional-architect` | FEAT, F (nested), `perform` in UCs | `usecase-realized`, `feature-realizes` |
| 3 L | `logical-architect` | LC, LI, connections, `allocate` F to LC, `satisfy` | `function-allocated`, `component-used`, `sysreq-satisfied` |
| 4 P | `physical-architect` | PC, PI, `allocate` LC to PC and LI to PI | `logical-allocated`, `physical-used` |
| 5 V | `test-designer` | STC (SysML), ATC (Markdown or RST) | all remaining: `systest-verifies`, `acctest-verifies`, `sysreq-verified`, `usecase-verified`, `crs-verified`; plus the compliance findings of `sysml2kit compliance` |

A CRS with `:scope: commercial` or `:scope: not-offered` is exempt from `crs-satisfied` and `crs-verified`; it needs a compliance statement (CST) instead. Platform needs are never rule-checked here; the platform's own build checks them.

For each step:

1. Hand the layer to its agent with the scope (all CRS, or the ones the user named).
   At P, after the `physical-architect` and before the review, the main session states coverage with the user as described under Matching in the `rfq` skill, so the reuse status exists.
2. Run the `rflp-reviewer` agent on that layer. It runs `make lint`, `make docs STRICT=` and `sysml2kit gaps build/needs --layer <X>` (the gate rules of this layer and earlier ones; at V also `sysml2kit compliance`), and reviews writing quality.
3. Fix blocking findings (via the authoring agent), re-review, up to 3 rounds.
4. Show the user: what was added (ids and one-line titles), the trace diagram `docs/_generated/trace.svg`, and the reviewer's remaining findings. Ask for approval, changes, or stop. Do not continue without an answer.

After step 5, `make all` (strict) must pass. Report coverage from `docs/_build/html/traceability.html` and the reuse table from `docs/_build/html/compliance.html`.

For an RFQ with an interview per layer use the `rfq` skill, which runs these steps.

Re-entering: to change an upstream layer later, edit it, then re-run the review for every layer below it; rule violations show what the change broke.
