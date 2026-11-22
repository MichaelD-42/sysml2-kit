# Window-switch example Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the seat-switch examples with a window-switch platform and RFQ that keep every element kind and every acceptance mutation.

**Architecture:** Copy each seat-switch project's scaffolding (Makefile, docs config, schemas, `trace.sysml`) unchanged apart from names; rewrite the content files (model, customer and platform docs, tests, JUnit results) for the window switch; then retarget everything that names seat-switch ids.

**Tech Stack:** SysML v2 (`sysml` CLI), sphinx-needs, `sysml2kit`, Python unittest, node:test.

**Spec:** `docs/superpowers/specs/2026-11-22-window-switch-example-design.md`

## Global Constraints

- Platform ids carry `WSW-`; RFQ ids are untagged; prefixes per `structure.md` (`PC-`, `LC-`, `FEAT-`, `F-`, `SR-`, `CON-`, `STC-`, `ATC-`, `CRS-`, `CST-`, `CTR-`, `PRQ-`, `SWR-`, `PI-`, `LI-`, `UC-`).
- Sizes near a third of the seat switch; soft.
- Build with `PATH=<sysml bin>:<repo>/.venv/bin:$PATH make -C examples/<project>`.

## Review Focus

- A mutation's `old` text no longer present: `replace()` asserts it, so a stale mutation fails loudly.
- Platform rules run on the platform build; RFQ rules skip platform needs: an RFQ-only check must not depend on a platform element's rule.
- The explorer default focus (`LC-100`, first project part) still lands on the product.
- `make` incremental: the use-case SVG named after the subject.
- Demo tests asserting counts (positions, shared parts) re-derived for two positions.

---

### Task 1: Platform project
Files: `examples/window-switch-platform/**` (copied scaffolding, new content). Done when `make` passes there with no rule violation and the compliance table builds.

### Task 2: RFQ project
Files: `examples/window-switch-rfq/**`. Done when `make` passes, `docs/_generated/compliance.md` shows comply, partial, not offered, commercial and information rows.

### Task 3: Acceptance suite
Files: `tests/acceptance.py`, `tests/test_template.py`. Retarget `EXAMPLE`, every mutation, `information()`, `incremental()`, `hook()`. Done when `python tests/acceptance.py` passes all.

### Task 4: Demo and docs
Files: `demo/tests/*`, `demo/Makefile`, `demo/explorer/prompt.md`, `demo/README.md`, `README.md`, `glossary.md`, `.github/workflows/ci.yml`, `structure.md`, `platform-capture.md`, three agents. Done when `make -C demo test` and `node --test demo/tests/js/` pass.

### Task 5: Remove the seat switch
Delete `examples/seat-switch-*`; `git grep -i seat` shows only historical docs.
