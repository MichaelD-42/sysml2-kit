# sysml2-kit

A Claude Code plugin marketplace for model-based systems engineering with SysML v2 and sphinx-needs. The `.sysml` files are the source of truth for the model; sphinx-needs is where traceability is evaluated, from customer requirements to test results.

- **Plugin `sysml-rflp`** (`plugins/sysml-rflp/`): skills to author, lint, render and document SysML v2 models; the RFLP method (Requirements → Functional → Logical) with agents for each layer, a reviewer, and a layer-by-layer workflow with approval gates; a hook that lints `.sysml` files after every edit; the `sysml` MCP server; a project template.
- **Python package `sysml2kit`** (`src/`): turns `sysml export` JSON into sphinx-needs needs, and renders use case diagrams and the RFLP trace graph as SVG. Standard library only.
- **Example `examples/vehicle/`**: a complete RFLP chain (CRS → UC/SR → F → LC → STC/ATC → test results) and the acceptance fixture for the toolkit.

## Install

```sh
claude plugin marketplace add MichaelD-42/sysml2-kit
claude plugin install sysml-rflp@sysml2-kit
```

In a project, the `sysml-init` skill scaffolds the pipeline; `make tools` installs the tools: the `sysml` CLI (Rust, built with cargo from the pinned fork below) and the Python requirements (Sphinx, sphinx-needs, ub-test-reports, sysml2kit). Then `make all`.

## Pipeline

```
model/**/*.sysml ── sysml check ───────────────────────────── lint gate
       ├─ sysml export ─► model.json ─ sysml2kit needs ─► model-needs.json ─┐
       ├─ sysml2kit usecases / sysml diagram --internal ─► *.svg            ├─ needimport ─► sphinx-build -b needs
test-results/*.xml ─ test-reports build needs ─► results-needs.json ────────┘        │
docs/**/*.rst (CRS, ATC) ───────────────────────────────────────────────────────────┤
                                     sysml2kit trace ◄─ needs.json ◄────────────────┘
                                            └─► trace.svg ─► sphinx-build -W -b html (RFLP rules = schemas.json)
```

Need types, link types, fields and the RFLP rules live in `docs/ubproject.toml` and `docs/schemas.json`, which Sphinx reads via `needs_from_toml` and ubCode reads directly. The structure and rules are documented in `plugins/sysml-rflp/skills/rflp-method/references/structure.md`.

## Tools and versions

| Tool | Version | Role |
|---|---|---|
| `sysml` (sysmlv2-cli) | fork [MichaelD-42/sysml-v2-rs](https://github.com/MichaelD-42/sysml-v2-rs) `main` (0.1.4 + fixes, `find`/`relations` MCP tools) | parse, resolve, validate, export, internal diagrams, MCP server |
| sphinx-needs | 9.2.0 | needs, links, schema rules |
| ub-test-reports | 2.0.0 | JUnit → needs |
| sysml2kit | this repo | export → needs, use case and trace diagrams |

The fork fixes one bug in upstream sysmlv2-cli 0.1.4: a parenthesised sequence `("a", "b")` kept only its first element, so `@Satisfies { need = ("CRS-001", "CRS-002"); }` silently lost links. With the fix, the OMG corpus below still checks clean.

### What `sysml export` gives the bridge

A flat JSON array of elements with `@type`, `@id` and every metamodel property; references are `{"@id": ...}`. `sysml2kit needs` reads `declaredShortName` (not `shortName`, which implicit features inherit), `name`, `qualifiedName`, `owner`, `documentation`; `SatisfyRequirementUsage.satisfyingFeature/satisfiedRequirement`; `Verification*.verifiedRequirement`; `AllocationUsage.relatedFeature` (`[source, target]`); `PerformActionUsage` → `ReferenceSubsetting.referencedFeature`; `MetadataUsage` typed by `Trace::Realizes/Satisfies/Verifies` and the string literals under it. The export has no source positions; the bridge finds `<'ID'>` in the model text.

## Tests

```sh
PYTHONPATH=src python -m unittest discover -s tests        # bridge and renderers
python tests/acceptance.py                                  # example build + mutations (needs the tools)
python tests/omg_corpus.py                                  # OMG release corpus through the pipeline
claude plugin validate .                                    # marketplace and plugin manifests
```

## Tool evaluation (2026-11-07)

Constraint: Python or Rust only. Yardstick: the OMG SysML-v2-Release 2026-09.1 corpus (252 files).

| Tool | Parse | Semantic check on valid OMG models | Export | SVG |
|---|---|---|---|---|
| **sysmlv2-cli 0.1.4** (Rust) | 252/252 | training, validation, examples: 100% resolved, 0 violations | standard API JSON | definitions, internal, sequence |
| syster-cli 0.5.1-alpha (Rust) | ok | false errors in the OMG library itself and in 11 corpus files; crashes on validation; unreliable exit code | XMI/JSON-LD | no |
| sysmlpy 0.105.0 (Python) | 249/252 | 36 of 54 validation files with false errors; ~53 s/file with library | grammar parse tree | PlantUML (needs Java) |
| sysml-v2-parser (Rust) | not tested | parser only | – | – |

There is no OMG Pilot Implementation gate (Java/Eclipse is out); the corpus run is the substitute.

## Known limits

- `sysml` accepts `satisfy`/`allocate` ends that are definitions; the spec types them as features. Model traced elements as usages (the authoring skill says so); the tool will not stop you.
- Its built-in standard library is 2026-05, not the 2026-09.1 release.
- No derive/refine mapping: SysML v2 has no `refine` keyword.
- ubCode support for `network_back` schema rules is untested here.
