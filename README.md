<h1 align="center">sysml2-kit</h1>

<p align="center"><b>Model-based systems engineering with SysML v2 and sphinx-needs, driven from Claude Code.</b><br>
The <code>.sysml</code> files are the model; sphinx-needs is where traceability is checked, from customer requirements to test results.</p>

<p align="center">
<a href="https://github.com/MichaelD-42/sysml2-kit/actions/workflows/ci.yml"><img src="https://github.com/MichaelD-42/sysml2-kit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a><br>
<a href="examples/window-switch-rfq">RFQ example</a> ·
<a href="examples/window-switch-platform">Platform example</a> ·
<a href="plugins/sysml-rflp/skills/rflp-method/references/structure.md">RFLP structure and rules</a> ·
<a href="plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml">SysML patterns</a>
</p>

## Why sysml2-kit

SysML v2 was adopted in 2025, so a language model asked to write it produces something that looks right and names things that do not exist. And a model on its own does not tell you whether every customer requirement ends up satisfied by a component and verified by a test. sysml2-kit closes both gaps. Agents write the model with a checker in the loop, a hook lints every `.sysml` file they edit, and the model is exported into sphinx-needs, where the RFLP rules (Requirements → Functional → Logical → Physical) fail the docs build when a link is missing.

The method is fixed and documented, and built for a supplier answering a customer RFQ: customer requirements (CRS, Markdown) → use cases and system requirements (UC/SR) → features and functions (FEAT/F) → logical components and interfaces (LC/LI) → physical components and interfaces in mechanical, electrical or software (PC/PI) → system and acceptance tests (STC/ATC) → test results. The supplier's platform (reusable features, components and variants) is a separate project that an RFQ project imports and reuses by subsetting. The docs show per customer requirement which feature meets it, how much comes from the platform (derived from the model, never claimed), and whether the match is partial; requirements no component can meet are answered by compliance statements (CST). Every customer requirement carries a class (functional, non-functional, constraint, information): plain values become constraints (CON) in the model, and the customer's own tests (CTR) are implemented by the supplier's system and acceptance tests. Each layer has its own agent, an interview skill asks the user only what the inputs leave open, and the workflow stops for your approval between layers. Terms and abbreviations are in the [glossary](glossary.md).

It is not a modeling GUI and it does not simulate. Software components keep linking to code and tests in sphinx-needs. The toolchain is Python and Rust only, with no Java or Eclipse.

## What you get

- **Plugin `sysml-rflp`** ([`plugins/sysml-rflp/`](plugins/sysml-rflp)): skills to scaffold (`sysml-init`), author (`sysml-author`), lint (`sysml-lint`) and document (`sysml-docs`) a model, to run the RFLP workflow (`rflp`, `rflp-method`), and to answer an RFQ with an interview per layer (`rfq`, which also captures a platform bottom-up). There is an agent per layer (requirements, functional, logical, physical, test) plus a reviewer, a hook that runs `sysml check` and the bridge after every edit (language errors, duplicate ids, unlinked ends, vague requirement texts), a session-start check for missing tools, the `sysml` MCP server, and a project template.
- **Python package `sysml2kit`** ([`src/`](src/sysml2kit)): turns `sysml export` JSON into sphinx-needs needs, evaluates every constraint against the attribute values its part states or inherits (failing when one does not hold), warns on system requirement texts without exactly one `shall` or with a vague term, lists RFLP rule violations by layer (`sysml2kit gaps`), derives realization degree per logical component and feature and writes the compliance and realization tables (`sysml2kit compliance`), and renders use case diagrams and the RFLP trace graph as SVG, where a click on an element opens its need in the docs. Standard library only.
- **Example [`examples/window-switch-platform/`](examples/window-switch-platform)**: a platform captured bottom-up, a door window-lifter switch product line on LIN (mechanics, electronics, firmware with SW components and units) with a one-key and a four-key module and two backlight colours as variations, platform limits as constraints, from PRQ to test results.
- **Example [`examples/window-switch-rfq/`](examples/window-switch-rfq)**: an RFQ project on the window-switch platform (its Makefile points `PLATFORM` at the sibling `window-switch-platform/`; a real project has the platform as a git submodule at `platform/`): an OEM's classified customer requirements and customer test requirements for the window switches of the driver and passenger doors. Functional requirements are matched by platform features, non-functional ones and constraints are satisfied by constraints over the platform's rated attributes, each door selects a key module and a backlight, and tests implement the customer's test requirements. It has a partial match and a partial satisfaction with the gaps stated, a not-offered requirement, a commercial statement, a test deviation, and the compliance table. It is the acceptance fixture for the toolkit.

The docs build is the traceability report. Need tables, the trace graph and internal diagrams come out of the model, and `sphinx-build -W` fails on any RFLP rule the model breaks: a customer requirement nothing satisfies, a function allocated to no component, a logical component allocated to no physical one, a requirement no test verifies.

## For agents

The `sysml` MCP server answers from the language's own standard library, not from what a model remembers. To write a model there are `check`, `notation`, `visible_names`, `library_search` and `rename` (which answers the edits and writes nothing). To read one there are `outline`, `find`, `relations`, `definition`, `references` and `impact` (what a change reaches, breadth first), so an agent queries the model instead of opening files. Every tool only reads, and answers as structured JSON with snake_case keys:

```text
find       { "kind": "ActionUsage", "without": "allocated_to" }
→ WindowSwitchRfqFeatures::windowKeys         FEAT-101   features.sysml:8
  WindowSwitchRfqFeatures::childLock          FEAT-102   features.sysml:15
  WindowSwitchRfqFeatures::nightDesign        FEAT-103   features.sysml:20
  ... (4 found)

relations  { "element": "SR-106" }
→ WindowSwitchRfqRequirements::partNumberLabel
    incoming  satisfies  WindowSwitchRfqLogical::OEM_WindowSwitch (LC-100)            architecture.sysml:21
    incoming  verifies   WindowSwitchRfqSystemTests::labelInspection (STC-111)      system_tests.sysml:59
    outgoing  annotated_by  Trace::Satisfies                                        system_requirements.sysml:28
```

`find` filters by metaclass, containing element, name or short name, and by a relation the element lacks. `relations` lists every link of one element in both directions: satisfy, verify, allocate, perform, connect, succession, typing, specialization, redefinition, imports, metadata. Both take a qualified name or a short name. The plugin starts the server with `make -s mcp`, which hands it the project and the platform the Makefile names (`PLATFORM`), so it reads the same model `make` builds, a submodule or a checkout beside the project.

## Quick start

You need Rust (cargo), Python 3.10+ and make. In Claude Code:

```text
/plugin marketplace add MichaelD-42/sysml2-kit
/plugin install sysml-rflp@sysml2-kit
```

Then ask Claude to set up a SysML project. `sysml-init` scaffolds the pipeline, and `make tools` installs the `sysml` CLI (built with cargo from the fork at the tag the Makefile pins) and the Python requirements (Sphinx, sphinx-needs, ub-test-reports, sysml2kit). If you have a platform repo, add it with `git submodule add <platform repo> platform`. Add customer requirements (`docs/customer/*.md`) and ask for the `rfq` workflow, or the `rflp` workflow without the interview; `make all` builds the docs and checks the rules.

## Model explorer demo

[`demo/`](demo) is a local web app over a kit project: twelve views generated from the model, search and a chat in which Claude answers from an in-memory graph of the model. `make -C demo demo` starts it on the window-switch RFQ example; [`demo/README.md`](demo/README.md) has the steps, the HTTP API and the graph schema, and the notes for integrating it into your own tools.

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
- `Makefile`: copy from the template and keep your `DIAGRAMS` line. It names the platform with `PLATFORM := platform` (the submodule); a project whose platform is checked out elsewhere sets the path there. Replace a `platform` symlink with that: Git for Windows checks a symlink out as a text file unless symlinks are enabled. The Makefile's `mcp` target starts the MCP server, and the plugin runs it (`make -s mcp`), so without it the server does not start.
- `model/trace.sysml`: add `metadata def Assembly;`, or copy it from the template. The product as built is an `#Assembly part <'PC-nnn'>` (no domain); a platform's switch assembly becomes one, and an RFQ's subsets it.
- No logical component is typed by a physical definition. Move rated values and the constraints over them from logical components to the physical part they describe (the assembly for the product as a whole). The bridge now evaluates every constraint and fails on one that does not hold.
- Per-configuration differences (one switch per seat position) are assemblies that subset the program's assembly and select variants, not extra logical components or functions. In an RFQ build the platform's own allocations to its variants no longer select them: subset the variant from a project part (or allocate a project component to it), or the finding `variation <V> reached without a selected variant` appears.
- A partially met CRS (partial match or `partial = true` constraint) needs a CST with `:compliance: partial` (finding `partial, but no partial compliance statement answers it`). A partial match still needs an SR in the feature's chain, now stating what is met (`partial match without a system requirement stating what is met`); a partial constraint no longer needs an SR. Delete SRs that only restated a partial constraint's gap.
- New finding `<CRS>: system requirement <SR> is satisfied outside the chain of its matching features`: every SR satisfying a matched CRS must be satisfied by a component that a matching feature's functions reach.

- `docs/ubproject.toml`: add the link `connects` (copy from the template). A `connect` or `interface` usage with a short name is now an interface need whose `connects` names the needs that own its two ends; `ConnectionUsage` maps to `interface`.
- New and optional: `sysml2kit needs --map <file>` and `sysml2kit myst <needs.json> <out.md> --map <file>` adapt the bridge to a project's own method (need types, id patterns, metadata as links or fields) and write the needs as MyST directives for projects that keep needs in Markdown. The map is JSON with the keys `keywords`, `ids`, `metadata_links`, `metadata_fields` (read by `needs`) and `types`, `links`, `fields` (read by `myst`).

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

A flat JSON array of elements with `@type`, `@id` and every metamodel property; references are `{"@id": ...}`. Since sysml 0.2 a relationship carries `owningRelatedElement` and `ownedRelatedElement` instead of `owner` and `ownedElement`, and an element's `ownedElement` leaves out its relationships, as the specification derives them; `sysml2kit` reads both shapes (`normalize` in `needs.py`). `sysml2kit needs` reads `declaredShortName` (not `shortName`, which implicit features inherit), `name`, `qualifiedName`, `owner`, `documentation`; `SatisfyRequirementUsage.satisfyingFeature/satisfiedRequirement`; `Verification*.verifiedRequirement`; `AllocationUsage.relatedFeature` (`[source, target]`); `PerformActionUsage` → `ReferenceSubsetting.referencedFeature`; `MetadataUsage` typed by `Trace::Realizes/Satisfies/Verifies/Matches/Implements` and the string literals under it, and keyword metadata `Trace::Feature/Mechanical/Electrical/Software/Assembly`, which with the metaclass decide the need type (`#Feature action` → feature, `#Electrical part` → physical component, `#Assembly part` → physical component without a domain); a constraint's body is evaluated from the expression tree the export carries (`OperatorExpression.operator`, `FeatureReferenceExpression.referent`, literals, `FeatureValue`), each referent taken as the context sees it through subsetting, typing and redefinition; subsetting (`:>`) becomes a `specializes` link. The export has no source positions; the bridge finds `<'ID'>` in the model text, skipping comments and string literals.

## Tools and versions

| Tool | Version | Role |
|---|---|---|
| `sysml` (sysmlv2-cli) | fork [MichaelD-42/sysml-v2-rs](https://github.com/MichaelD-42/sysml-v2-rs) tag `v0.2.0-kit.3` (upstream 0.2.0 + ids on variant members; `relations` and `trace` credit nothing for a `satisfy` whose `by` end does not resolve; several `--project` roots for the MCP server) | parse, resolve, validate, export, internal diagrams, MCP server |
| sphinx-needs | 9.2.0 | needs, links, schema rules |
| ub-test-reports | 2.0.0 | JUnit → needs |
| sysml2kit | this repo | export → needs, use case and trace diagrams |

The fork carries one fix upstream does not have: a variant member with a short name (`variant part <'PC-002'> radar;`) fails to parse upstream, so platform variants could not be needs. Two earlier fork changes are upstream since 0.2.0: a parenthesised sequence `("a", "b")` keeping all its elements (before, `@Satisfies { need = ("CRS-001", "CRS-002"); }` silently lost links), and the `find` and `relations` MCP tools. With the fix, the OMG corpus still checks clean.

0.2.0 checks more than 0.1.4 did. A name declared twice in one namespace is an error, inherited members included: a constraint named like one the part inherits (`keyDurability` on a part subsetting the platform assembly, which already has one) fails `make lint`. `sysml diagram` refuses a model with unresolved names, so the Makefile passes the platform model to it as it does to `check` and `export`. And `variant w;` without a kind keyword now refers to an existing usage instead of declaring one; write `variant part w;`.

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
- The constraint evaluator reads the expression tree the parser resolved and covers `and`, `or`, `xor`, `not`, comparisons, unary minus, quantities (`5 [N]`), strings, booleans and feature chains; it has no arithmetic. Quantities in different units are converted as the standard library defines its units (`unitConversion` by prefix or convention, unit expressions such as `kg*m/s^2`), from a table of the library's 831 units in `sysml2kit/units.json`; quantities of different dimensions, and temperatures in different units (the library's conversions carry no offset, so `°C` against `K` would be wrong for absolute temperatures), are `not evaluated`. Anything else, or a value nobody states, is a `not evaluated` warning. A constraint is evaluated in its owner and again in every part that specializes the owner, with that part's own (redefined) values, unless the part redefines the constraint; an RFQ build skips the platform's own parts.
- ubCode support for `network_back` schema rules is untested here.
- The platform is pulled in as a git submodule, or as a checkout the Makefile's `PLATFORM` names, only; sysand packages are not supported. The realization degree follows allocations and `specializes` links into the platform, so reuse written any other way (copying a platform part) counts as new.
- Reuse is about platform components, not whether a requirement's value is met (that is `partial`).
- Document inputs other than the Markdown CRS (PDF, Word, drawings) are read by Claude as context; there is no ReqIF or Excel import.
- `make tools` and CI build the fork tag in `SYSML_TAG`. To take a newer fork commit, tag it, change `SYSML_TAG` in the template and example Makefiles, regenerate the unit table (`python -m sysml2kit.units`, with that `sysml` on `PATH`) and release; CI reads the tag from the template Makefile and fails when the table no longer matches its library.

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
