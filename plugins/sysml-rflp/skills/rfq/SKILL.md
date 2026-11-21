---
name: rfq
description: Answer a customer RFQ with a SysML v2 system architecture - read the customer requirements, interview the user for what they leave open, and build R, F, L and P layer by layer from the supplier's platform, ending with the compliance table. Use when the user has an RFQ or customer requirements to quote against, or says "do the RFQ", "match this against our platform".
---

# RFQ workflow

The `rflp` workflow with an interview in front of each layer. Read `rflp-method` first (`references/structure.md`: artifacts, links, rules). Questions per layer are in `references/questions.md`.

Precondition: an initialized project (`sysml-init`), `make lint` passing. Platform in `platform/` if the supplier has one (`git submodule add <platform repo> platform`).

## Inputs

- Customer requirements: `docs/customer/*.md`, `crs` directives (MyST). Never rewrite them.
- Platform: `platform/docs/platform/*.md` (PRQ), `platform/model/` (features, LCs, PCs, variants). Read it with the `find` and `relations` MCP tools, not by opening every file.
- Other RFQ documents (PDF, Word, drawings, specs): read as context. Cite what you took from them when you ask ("the spec on page 4 gives 400 V; is that the supply?"). Never turn a fact from them into a requirement without the user's yes.

If there are no CRS yet, stop and ask the user for them, or to name the document to extract them from; write the `crs` directives only after the user confirms the wording.

## Per layer: ask, create, validate

For each of R, F, L, P (the `rflp` steps 1 to 4):

1. Ask. Go through the topics of this layer in `references/questions.md`. Skip every topic the inputs already answer; ask only what is left open, one topic at a time, and wait for each answer. Never invent a value: an unanswered quantity goes into the model as a placeholder and onto the open-question list.
2. Create. Hand the layer and the answers to its agent (`requirements-analyst`, `functional-architect`, `logical-architect`, `physical-architect`). After R and F, tell the agent which platform features and PCs exist so it specializes and reuses instead of redrawing.
3. Match (P only). After the `physical-architect` and before the review, state coverage as described under Matching, so the reuse status exists.
4. Validate. Run the `rflp-reviewer` agent on the layer; fix blocking findings through the authoring agent, up to 3 rounds.
5. Approve. Show the user what was added (ids, one-line titles), the open questions, and for P the reuse status per matched feature. Stop. Do not start the next layer without a yes.

## Matching

At step 3 of P, once the chain reaches physical components, the main session (not an agent) states with the user what each customer requirement is met by, and writes the claims the user agrees to into the features: `@Matches { need = "CRS-001"; }` inside the feature that covers it, one per CRS; add `partial = true` when the feature meets it only in part (value not reached, condition excluded). A partial match needs an SR that states the gap, satisfied by a component in that feature's chain. Write only claims the user agrees with; the reuse status (platform, variant, modified, new, incomplete) is derived from the chain, never written.

A CRS no feature can meet (commercial terms, delivery, certification, or a technical gap) is answered by a compliance statement: a `cst` directive in `docs/customer/statements.md` with `:answers:` and `:compliance:` (`comply`, `partial`, `not-comply`). The compliance value is the user's decision.

## Finish

Run the V layer like the others: `test-designer`, then `rflp-reviewer` (including `sysml2kit compliance`). Show the user the tests added, `docs/_generated/compliance.md` (per CRS: matched features, reuse, partial, statements, domains) and the open questions that remain. Ask for approval; only after a yes run the final `make all`.
