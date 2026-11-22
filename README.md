<h1 align="center">sysml2-kit</h1>

<p align="center"><b>Model-based systems engineering with SysML v2 and sphinx-needs, driven from Claude Code.</b><br>
The <code>.sysml</code> files are the model; sphinx-needs is where traceability is checked, from customer requirements to test results.</p>

<p align="center">
<a href="https://github.com/MichaelD-42/sysml2-kit/actions/workflows/ci.yml"><img src="https://github.com/MichaelD-42/sysml2-kit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a><br>
<a href="examples/seat-switch-rfq">RFQ example</a> ·
<a href="examples/seat-switch-platform">Platform example</a> ·
<a href="plugins/sysml-rflp/skills/rflp-method/references/structure.md">RFLP structure and rules</a> ·
<a href="plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml">SysML patterns</a>
</p>

## Why sysml2-kit

SysML v2 was adopted in 2025, so a language model asked to write it produces something that looks right and names things that do not exist. And a model on its own does not tell you whether every customer requirement ends up satisfied by a component and verified by a test. sysml2-kit closes both gaps. Agents write the model with a checker in the loop, a hook lints every `.sysml` file they edit, and the model is exported into sphinx-needs, where the RFLP rules (Requirements → Functional → Logical → Physical) fail the docs build when a link is missing.

The method is fixed and documented, and built for a supplier answering a customer RFQ: customer requirements (CRS, Markdown) → use cases and system requirements (UC/SR) → features and functions (FEAT/F) → logical components and interfaces (LC/LI) → physical components and interfaces in mechanical, electrical or software (PC/PI) → system and acceptance tests (STC/ATC) → test results. The supplier's platform (reusable features, components and variants) is a separate project that an RFQ project imports and reuses by subsetting. The docs show per customer requirement which feature meets it, how much comes from the platform (derived from the model, never claimed), and whether the match is partial; requirements no component can meet are answered by compliance statements (CST). Every customer requirement carries a class (functional, non-functional, constraint, information): plain values become constraints (CON) in the model, and the customer's own tests (CTR) are implemented by the supplier's system and acceptance tests. Each layer has its own agent, an interview skill asks the user only what the inputs leave open, and the workflow stops for your approval between layers. Terms and abbreviations are in the [glossary](glossary.md).

It is not a modeling GUI and it does not simulate. Software components keep linking to code and tests in sphinx-needs. The toolchain is Python and Rust only, with no Java or Eclipse.

## What you get

- **Plugin `sysml-rflp`** ([`plugins/sysml-rflp/`](plugins/sysml-rflp)): skills to scaffold (`sysml-init`), author (`sysml-author`), lint (`sysml-lint`) and document (`sysml-docs`) a model, to run the RFLP workflow (`rflp`, `rflp-method`), and to answer an RFQ with an interview per layer (`rfq`, which also captures a platform bottom-up). There is an agent per layer (requirements, functional, logical, physical, test) plus a reviewer, a hook that runs `sysml check` and the bridge after every edit (language errors, duplicate ids, unlinked ends, vague requirement texts), a session-start check for missing tools, the `sysml` MCP server, and a project template.
- **Python package `sysml2kit`** ([`src/`](src/sysml2kit)): turns `sysml export` JSON into sphinx-needs needs, warns on system requirement texts without exactly one `shall` or with a vague term, lists RFLP rule violations by layer (`sysml2kit gaps`), derives reuse status and writes the compliance table (`sysml2kit compliance`), and renders use case diagrams and the RFLP trace graph as SVG, where a click on an element opens its need in the docs. Standard library only.
- **Example [`examples/seat-switch-platform/`](examples/seat-switch-platform)**: a platform captured bottom-up, a seat adjustment switch product line (mechanics, electronics, firmware, with cybersecurity, production and workshop needs) with mirrored housings and four button sets as variations, platform limits as constraints, from PRQ to test results.
- **Example [`examples/seat-switch-rfq/`](examples/seat-switch-rfq)**: an RFQ project on the seat-switch platform (imported through `platform/`, a symlink here, a git submodule in a real project): an OEM's classified customer requirements and customer test requirements for the switches of four seat positions. Functional requirements are matched by platform features, non-functional ones and constraints are satisfied by constraints over the platform's rated attributes, each seat position selects a housing side and a button set, and tests implement the customer's test requirements. It has a partial satisfaction with the gap stated, a not-offered requirement, a commercial statement, a test deviation, and the compliance table. It is the acceptance fixture for the toolkit.

The docs build is the traceability report. Need tables, the trace graph and internal diagrams come out of the model, and `sphinx-build -W` fails on any RFLP rule the model breaks: a customer requirement nothing satisfies, a function allocated to no component, a logical component allocated to no physical one, a requirement no test verifies.

## For agents

The `sysml` MCP server answers from the language's own standard library, not from what a model remembers. To write a model there are `check`, `notation`, `visible_names` and `library_search`. To read one there are `outline`, `find` and `relations`, so an agent queries the model instead of opening files:

```text
find       { "kind": "ActionUsage", "without": "allocated_to" }
→ SeatSwitchRfqFeatures::seatAdjustment   FEAT-101   features.sysml:11
  SeatSwitchRfqFeatures::comfortKeys      FEAT-102   features.sysml:17
  SeatSwitchRfqFeatures::nightDesign      FEAT-103   features.sysml:28
  ... (6 found)

relations  { "element": "SR-119" }
→ SeatSwitchRfqRequirements::durabilityGap
    incoming  satisfies  SeatSwitchRfqLogical::OEM_SeatSwitch (LC-100)              architecture.sysml:134
    incoming  verifies   SeatSwitchRfqSystemTests::keyDurabilityTest (STC-103)    system_tests.sysml:19
    outgoing  annotated_by  Trace::Satisfies                                       system_requirements.sysml:86
```

`find` filters by metaclass, containing element, name or short name, and by a relation the element lacks. `relations` lists every link of one element in both directions: satisfy, verify, allocate, perform, connect, succession, typing, specialization, redefinition, imports, metadata. Both take a qualified name or a short name. The plugin starts the server on the project's `model/` directory.

## Quick start

You need Rust (cargo), Python 3.10+ and make. In Claude Code:

```text
/plugin marketplace add MichaelD-42/sysml2-kit
/plugin install sysml-rflp@sysml2-kit
```

Then ask Claude to set up a SysML project. `sysml-init` scaffolds the pipeline, and `make tools` installs the `sysml` CLI (built with cargo from the fork at the tag the Makefile pins) and the Python requirements (Sphinx, sphinx-needs, ub-test-reports, sysml2kit). If you have a platform repo, add it with `git submodule add <platform repo> platform`. Add customer requirements (`docs/customer/*.md`) and ask for the `rfq` workflow, or the `rflp` workflow without the interview; `make all` builds the docs and checks the rules.

## Model explorer demo

[`demo/`](demo) is a local web app over a kit project: twelve views generated from the model, search and a chat in which Claude answers from an in-memory graph of the model. `make -C demo demo` starts it on the seat-switch RFQ example; [`demo/README.md`](demo/README.md) has the steps, the HTTP API and the graph schema, and the notes for integrating it into your own tools.

## Upgrading from 0.1.x

An existing project needs these changes before it builds with 0.2:

- `docs/ubproject.toml` and `docs/schemas.json`: copy from the template (new need types feature, physical component and interface, CST and PRQ; new fields such as `scope`, `compliance`, `platform`, `variant`; new links such as `matches`, `answers`, `specializes`; the new rules).
- `model/trace.sysml`: add the `Feature`, `Mechanical`, `Electrical`, `Software` and `Matches` metadata and the `ScalarValues::Boolean` import, or copy it from the template.
- `requirements.txt`: add `myst-parser` and pin `sysml2kit` to the new tag; `docs/conf.py`: add `myst_parser` to `extensions`, plus the template's `exclude_patterns` and `myst_enable_extensions`.
- `docs/index.rst`: add `compliance` to the toctree, and copy `docs/compliance.md` from the template.
- `Makefile`: copy from the template and keep your `DIAGRAMS` line.
- The model itself: the new F and P gates fail until each function tree sits under a feature (`#Feature action <'FEAT-nnn'>`) and every leaf logical component is allocated to a physical component (`#Mechanical|#Electrical|#Software part <'PC-nnn'>`).

## Upgrading from 0.2.x

Requirement classes, constraints and customer test requirements change the rules. An existing project needs:

- `docs/ubproject.toml` and `docs/schemas.json`: copy from the template. New need types `ctr` (`CTR-`) and `constraint` (`CON-`); new fields `class` (on CRS and PRQ), `purpose` and `method` (on CTR); new links `implements`, `applies_to`, `partial_satisfies`; new rules `crs-class`, `constraint-satisfies`, `constraint-verified`, `ctr-implemented`, `systest-implements`, `acctest-implements`. `crs-satisfied` is selected by class and accepts an SR or a constraint; `systest-verifies` and `acctest-verifies` apply to tests that implement nothing.
- `crs-verified` is gone from `schemas.json`. CRS and PRQ verification is now the computed finding `<CRS>: not verified (no acceptance test, no implemented CTR applying to it)` of `sysml2kit compliance`, which runs at the V gate and fails the build; `sysml2kit gaps` no longer lists it.
- `model/trace.sysml`: add the `Implements` metadata (`need : String[1..*]`), and `partial` on `Satisfies`, or copy it from the template.
- Every CRS and PRQ needs a `:class:` (`functional`, `non-functional`, `constraint` or `information`). Plain values move from bare attributes or textual SRs into `CON-` constraints; `information` carries no obligation.
- Customer tests become `ctr` directives with `:applies_to:`, implemented by STC (`@Implements`) or ATC (`:implements:`).
- Software architecture: new rules `swcomponent-used` (every SW component has a logical component allocated) and `software-used` (a top-level `#Software` PC without SW components has one), and `physical-used` now covers only mechanical and electrical leaf PCs. A project whose firmware owns `#Software` parts must allocate its logical components to those SW components, not to the units under them.
- A use case's need title comes from the doc of its `objective` (`objective { doc /* The driver wants to ... */ }`), otherwise from its name.
- A software requirement links to the SW component or unit implementing it with `:allocated_to:`.

## Pipeline

```text
model/**/*.sysml + platform/model/**/*.sysml ── sysml check ── lint gate
       ├─ sysml export ─► model.json ─ sysml2kit needs ─► model-needs.json ─┐
       ├─ sysml2kit usecases / sysml diagram --internal ─► *.svg            ├─ needimport ─► sphinx-build -b needs
test-results/*.xml ─ test-reports build needs ─► results-needs.json ────────┘        │
docs/**/*.md|rst (CRS, PRQ, CST, ATC) ──────────────────────────────────────────────┤
          sysml2kit trace ─► trace.svg ◄─ needs.json ◄──────────────────────────────┤
          sysml2kit compliance ─► compliance.md ◄───────────────────────────────────┘
                       └─► sphinx-build -W -b html (RFLP rules = schemas.json, reuse and compliance findings)
```

The platform model is loaded next to the RFQ's `model/`; its elements become needs with `platform: true`, which the RFQ build does not rule-check (the platform's own build does). Need types, link types, fields and the RFLP rules live in `docs/ubproject.toml` and `docs/schemas.json`, which Sphinx reads via `needs_from_toml` and ubCode reads directly. The structure and rules are documented in [`structure.md`](plugins/sysml-rflp/skills/rflp-method/references/structure.md).

### What `sysml export` gives the bridge

A flat JSON array of elements with `@type`, `@id` and every metamodel property; references are `{"@id": ...}`. `sysml2kit needs` reads `declaredShortName` (not `shortName`, which implicit features inherit), `name`, `qualifiedName`, `owner`, `documentation`; `SatisfyRequirementUsage.satisfyingFeature/satisfiedRequirement`; `Verification*.verifiedRequirement`; `AllocationUsage.relatedFeature` (`[source, target]`); `PerformActionUsage` → `ReferenceSubsetting.referencedFeature`; `MetadataUsage` typed by `Trace::Realizes/Satisfies/Verifies/Matches/Implements` and the string literals under it, and keyword metadata `Trace::Feature/Mechanical/Electrical/Software`, which with the metaclass decide the need type (`#Feature action` → feature, `#Electrical part` → physical component); subsetting (`:>`) becomes a `specializes` link. The export has no source positions; the bridge finds `<'ID'>` in the model text, skipping comments and string literals.

## Tools and versions

| Tool | Version | Role |
|---|---|---|
| `sysml` (sysmlv2-cli) | fork [MichaelD-42/sysml-v2-rs](https://github.com/MichaelD-42/sysml-v2-rs) tag `v0.1.4-kit.2` (0.1.4 + fixes, accepts ids on variant members, `find`/`relations` MCP tools) | parse, resolve, validate, export, internal diagrams, MCP server |
| sphinx-needs | 9.2.0 | needs, links, schema rules |
| ub-test-reports | 2.0.0 | JUnit → needs |
| sysml2kit | this repo | export → needs, use case and trace diagrams |

The fork fixes two bugs in upstream sysmlv2-cli 0.1.4. A parenthesised sequence `("a", "b")` kept only its first element, so `@Satisfies { need = ("CRS-001", "CRS-002"); }` silently lost links. And a variant member with a short name (`variant part <'PC-002'> radar;`) failed to parse, so platform variants could not be needs. With the fixes, the OMG corpus still checks clean. The fork also adds the `find` and `relations` MCP tools.

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
- The platform is pulled in as a git submodule (or symlink) only; sysand packages are not supported. Reuse status follows the chain feature → functions → LC → PC through `specializes` links, so reuse written any other way (copying a platform part) counts as new.
- Reuse is about platform components, not whether a requirement's value is met (that is `partial`).
- Document inputs other than the Markdown CRS (PDF, Word, drawings) are read by Claude as context; there is no ReqIF or Excel import.
- `make tools` and CI build the fork tag in `SYSML_TAG`. To take a newer fork commit, tag it, change `SYSML_TAG` in the template and example Makefiles and release; CI reads the tag from the template Makefile.

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
