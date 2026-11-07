<h1 align="center">sysml2-kit</h1>

<p align="center"><b>Model-based systems engineering with SysML v2 and sphinx-needs, driven from Claude Code.</b><br>
The <code>.sysml</code> files are the model; sphinx-needs is where traceability is checked, from customer requirements to test results.</p>

<p align="center">
<a href="https://github.com/MichaelD-42/sysml2-kit/actions/workflows/ci.yml"><img src="https://github.com/MichaelD-42/sysml2-kit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a><br>
<a href="examples/vehicle">Example project</a> ·
<a href="plugins/sysml-rflp/skills/rflp-method/references/structure.md">RFLP structure and rules</a> ·
<a href="plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml">SysML patterns</a>
</p>

## Why sysml2-kit

SysML v2 was adopted in 2025, so a language model asked to write it produces something that looks right and names things that do not exist. And a model on its own does not tell you whether every customer requirement ends up satisfied by a component and verified by a test. sysml2-kit closes both gaps. Agents write the model with a checker in the loop, a hook lints every `.sysml` file they edit, and the model is exported into sphinx-needs, where the RFLP rules (Requirements → Functional → Logical) fail the docs build when a link is missing.

The method is fixed and documented: customer requirements (CRS) → use cases and system requirements (UC/SR) → functions (F) → logical components (LC) → system and acceptance tests (STC/ATC) → test results. Each layer has its own agent, and the workflow stops for your approval between layers.

It is not a modeling GUI and it does not simulate. The physical layer (software, hardware, code) stays out of the SysML model; it lives in sphinx-needs next to the code. The toolchain is Python and Rust only, with no Java or Eclipse.

## What you get

- **Plugin `sysml-rflp`** ([`plugins/sysml-rflp/`](plugins/sysml-rflp)): skills to scaffold (`sysml-init`), author (`sysml-author`), lint (`sysml-lint`) and document (`sysml-docs`) a model, and to run the RFLP workflow (`rflp`, `rflp-method`). There is an agent per layer plus a reviewer, a hook that runs `sysml check` after every edit, the `sysml` MCP server, and a project template.
- **Python package `sysml2kit`** ([`src/`](src/sysml2kit)): turns `sysml export` JSON into sphinx-needs needs, and renders use case diagrams and the RFLP trace graph as SVG. Standard library only.
- **Example [`examples/vehicle/`](examples/vehicle)**: a complete chain from CRS to test results, and the acceptance fixture for the toolkit.

The docs build is the traceability report. Need tables, the trace graph and internal diagrams come out of the model, and `sphinx-build -W` fails on any RFLP rule the model breaks: a customer requirement nothing satisfies, a function allocated to no component, a requirement no test verifies.

## For agents

The `sysml` MCP server answers from the language's own standard library, not from what a model remembers. To write a model there are `check`, `notation`, `visible_names` and `library_search`. To read one there are `outline`, `find` and `relations`, so an agent queries the model instead of opening files:

```text
find       { "kind": "ActionUsage", "without": "allocated_to" }
→ VehicleFunctions::operateVehicle   F-001   functions.sysml:4

relations  { "element": "SR-001" }
→ VehicleRequirements::range
    incoming  satisfies  VehicleLogical::vehicle::energyStore (LC-003)   architecture.sysml:29
    incoming  verifies   VehicleSystemTests::rangeTest (STC-001)         system_tests.sysml:6
    outgoing  annotated_by  Trace::Satisfies                             system_requirements.sysml:7
```

`find` filters by metaclass, containing element, name or short name, and by a relation the element lacks. `relations` lists every link of one element in both directions: satisfy, verify, allocate, perform, connect, succession, typing, specialization, redefinition, imports, metadata. Both take a qualified name or a short name. The plugin starts the server on the project's `model/` directory.

## Quick start

You need Rust (cargo) and Python 3.10+. In Claude Code:

```text
/plugin marketplace add MichaelD-42/sysml2-kit
/plugin install sysml-rflp@sysml2-kit
```

Then ask Claude to set up a SysML project. `sysml-init` scaffolds the pipeline, and `make tools` installs the `sysml` CLI (built with cargo from the fork's `main`) and the Python requirements (Sphinx, sphinx-needs, ub-test-reports, sysml2kit). Add customer requirements and ask for the RFLP workflow; `make all` builds the docs and checks the rules.

## Pipeline

```text
model/**/*.sysml ── sysml check ───────────────────────────── lint gate
       ├─ sysml export ─► model.json ─ sysml2kit needs ─► model-needs.json ─┐
       ├─ sysml2kit usecases / sysml diagram --internal ─► *.svg            ├─ needimport ─► sphinx-build -b needs
test-results/*.xml ─ test-reports build needs ─► results-needs.json ────────┘        │
docs/**/*.rst (CRS, ATC) ───────────────────────────────────────────────────────────┤
                                     sysml2kit trace ◄─ needs.json ◄────────────────┘
                                            └─► trace.svg ─► sphinx-build -W -b html (RFLP rules = schemas.json)
```

Need types, link types, fields and the RFLP rules live in `docs/ubproject.toml` and `docs/schemas.json`, which Sphinx reads via `needs_from_toml` and ubCode reads directly. The structure and rules are documented in [`structure.md`](plugins/sysml-rflp/skills/rflp-method/references/structure.md).

### What `sysml export` gives the bridge

A flat JSON array of elements with `@type`, `@id` and every metamodel property; references are `{"@id": ...}`. `sysml2kit needs` reads `declaredShortName` (not `shortName`, which implicit features inherit), `name`, `qualifiedName`, `owner`, `documentation`; `SatisfyRequirementUsage.satisfyingFeature/satisfiedRequirement`; `Verification*.verifiedRequirement`; `AllocationUsage.relatedFeature` (`[source, target]`); `PerformActionUsage` → `ReferenceSubsetting.referencedFeature`; `MetadataUsage` typed by `Trace::Realizes/Satisfies/Verifies` and the string literals under it. The export has no source positions; the bridge finds `<'ID'>` in the model text.

## Tools and versions

| Tool | Version | Role |
|---|---|---|
| `sysml` (sysmlv2-cli) | fork [MichaelD-42/sysml-v2-rs](https://github.com/MichaelD-42/sysml-v2-rs) `main` (0.1.4 + fixes, `find`/`relations` MCP tools) | parse, resolve, validate, export, internal diagrams, MCP server |
| sphinx-needs | 9.2.0 | needs, links, schema rules |
| ub-test-reports | 2.0.0 | JUnit → needs |
| sysml2kit | this repo | export → needs, use case and trace diagrams |

The fork fixes one bug in upstream sysmlv2-cli 0.1.4: a parenthesised sequence `("a", "b")` kept only its first element, so `@Satisfies { need = ("CRS-001", "CRS-002"); }` silently lost links. With the fix, the OMG corpus still checks clean. It also adds the `find` and `relations` MCP tools.

The pipeline was chosen by an evaluation on 2026-11-07, Python or Rust only, against the OMG SysML-v2-Release 2026-09.1 corpus (252 files):

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
- `make tools` and CI follow the fork's `main`, so a push there changes what every build installs.

## Development

```sh
PYTHONPATH=src python -m unittest discover -s tests        # bridge and renderers
python tests/acceptance.py                                  # example build + mutations (needs the tools)
python tests/omg_corpus.py                                  # OMG release corpus through the pipeline
claude plugin validate .                                    # marketplace and plugin manifests
ruff check . && ruff format --check .                      # lint and format (CI pins ruff 0.17.4)
```

## License

[MIT](LICENSE) © Michael Dold
