---
name: sysml-docs
description: Build the sphinx-needs documentation from the SysML model, report RFLP rule violations, broken links and coverage gaps, add diagrams and test results. Use when the user asks to build or check the docs, traceability, coverage, or to add a diagram or test results.
---

# Docs build

`make all` = `sysml check` → `sysml export` → `sysml2kit needs` (model needs) → `test-reports build needs` (JUnit results) → diagrams → `sphinx-build -b needs` → `sysml2kit trace` → `sphinx-build -W -b html`. Output: `docs/_build/html/index.html`.

## Build and report

1. `make all`; missing tools: `make tools`. Mid-workflow, `make docs STRICT=` reports violations without failing.
2. Read failures by stage:
   - `sysml check`: model error → `sysml-lint`.
   - `sysml2kit:` lines: duplicate id, short name on an unmapped kind, a satisfy/allocate/perform end without a short name, or Trace metadata on an element without one. Fix the model.
   - `sysml2kit: warning:` lines: a system requirement text without exactly one `shall`, or with a vague term (TBD, etc., as appropriate, user-friendly, fast). The build still passes; the reviewer blocks on them.
   - `has schema violations` with a rule id (`crs-satisfied`, ...): an RFLP rule; see `rflp-method` for its meaning and layer. `sysml2kit gaps build/needs [--layer R|F|L|V]` lists them one per line with layer and file:line, and exits 1 while any remain.
   - `unknown outgoing link 'X'`: an RST need or Trace metadata names an id that does not exist.
3. Coverage: the tables in `docs/_build/html/traceability.html`; the trace graph is `docs/_generated/trace.svg`.

## Diagrams

- Use case diagrams are generated per subject: `docs/_generated/usecases-<subject>.svg`.
- Internal structure of a usage tree (functions grouped by use case, components with ports and connections): add its qualified name to `DIAGRAMS` in the `Makefile` → `docs/_generated/<name>.svg`.
- Embed in `docs/model.rst`: use case diagrams with `.. raw:: html` and `:file: _generated/usecases-<subject>.svg`, so each use case links to its need (an `.. image::` would make the links dead); internal diagrams with `.. image:: _generated/<name>.svg` and an `:alt:`.

## Test results

Put JUnit XML in `test-results/`. Each `<testcase>` needs `<property name="verifies" value="STC-001"/>` (or an ATC id); it becomes a `testresult` need linked to that test case.
