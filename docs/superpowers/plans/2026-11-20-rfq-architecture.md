# RFQ System Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend sysml2-kit's RFLP method to the chain Use Case → Feature → Function/Sub-Function → Logical Component/Interface → Physical Component (ME/EE/SW), with a platform library, variants, a model-derived RFQ compliance table and an interview workflow.

**Architecture:** Part A fixes the parser in the `sysml` fork (`/home/michael/workspace/sysml-v2-rs`) so variant members can carry ids, and releases tag `v0.1.4-kit.2`. Part B extends the kit in place, with a standalone example product model (`examples/edrive-platform`) that the vehicle RFQ example imports as its platform: the bridge (`src/sysml2kit/needs.py`) classifies need types by metaclass plus `#keyword` metadata, marks platform and variant needs, adds `specializes`/`matches` links and computes each feature's reuse status; a new `sysml2kit compliance` command rolls matches up per customer requirement after the first Sphinx pass; templates, rules, agents and skills follow; `examples/vehicle` is migrated and stays the acceptance fixture.

**Tech Stack:** Rust (fork parser, `cargo test`), Python 3.10+ standard library (`unittest`), Sphinx + sphinx-needs 9.2.0 + myst-parser, SysML v2 textual notation.

**Spec:** `docs/superpowers/specs/2026-11-20-rfq-architecture-design.md`

## Global Constraints

- `sysml2kit` stays standard library only.
- Need ids: `CRS-`, `PRQ-`, `CST-`, `UC-`, `SR-`, `FEAT-`, `F-`, `LC-`, `LI-`, `PC-`, `PI-`, `STC-`, `ATC-`, `SWR-` + 3 or more digits; model ids may carry a platform tag before the prefix: `^([A-Z][A-Z0-9]*-)?FEAT-[0-9]{3,}$` (same shape per type).
- Domain keywords map `#Mechanical` → `ME`, `#Electrical` → `EE`, `#Software` → `SW`.
- Reuse values, worst first: `new` > `modified` > `variant` > `platform`; plus `incomplete` (no PC reached).
- CST `compliance` values: `comply`, `partial`, `not-comply`.
- The platform model lives at `<project>/platform/model` (git submodule `platform/`; decision for the spec's "submodule vs sysand"). A project without `platform/model` builds as before.
- Platform files carry no RFQ ids or links (spec anti-goal).
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Template and example share files byte for byte except the Makefile's `DIAGRAMS` (enforced by `tests/test_template.py`); every template change is mirrored in `examples/vehicle`.

## Review Focus

- A model that uses none of the new keywords (today's vehicle model before migration) must convert exactly as before: no new errors, types unchanged. Pinned in Task B1 (`test_untagged_model_converts_as_before`).
- A feature whose chain mixes an RFQ-redefined platform PC and a new PC must be `modified`, not `platform`: redefinition counts as reuse, a new part does not. Pinned in Task B3 (`test_mixed_chain_is_modified`).
- A cycle in `specializes` or `owned_by` (a malformed but checkable model) must not hang the reuse walk. Pinned in Task B3 (`test_cycle_terminates`).
- A CRS answered by both a feature and a CST, or matched only partially by every feature, must show in the compliance table and not count as unanswered. Pinned in Task B4 (`test_feature_and_statement_both_listed`, `test_partial_only_is_answered_but_flagged`).
- Editing a `.sysml` file in a project with `platform/model` must lint against the platform too, or every import of a platform element is an "unresolved" error at edit time. Pinned in Task B5 (`test_hook_includes_platform_model`).

---

## Part A: fork

### Task A1: ids and names on variant members

The parser's `kw_usage` (`crates/sysml-syntax/src/parser.rs:609`) handles `variant`, then expects a short name and a name directly; for `variant part <'PC-002'> radar;` the kind keyword `part` comes first, so `<` is unexpected. The spec's `VariantUsageElement` admits a full usage (`PartUsage = OccurrenceUsagePrefix 'part' Usage`, which includes `Identification`). The model builder already builds `variant part radar;` as a `PartUsage` under a `VariantMembership`, so only the parser changes.

**Files:**
- Modify: `crates/sysml-syntax/src/parser.rs` (`kw_usage`)
- Test: `crates/sysml-syntax/tests/variant_members.rs` (new)
- Test: `crates/sysml-cli` export test or `crates/sysml-model` test asserting the element (choose where existing export tests live)

**Interfaces:**
- Produces: `sysml check` accepts `variant <kind keywords> <'id'> name …;`; `sysml export` gives that usage `declaredShortName` and an `owningRelationship` of `@type` `VariantMembership`.

- [ ] **Step 1: Write the failing parser test** in `variant_members.rs`, same style as `tests/prefix_metadata.rs` (a table of source snippets, each must `parse` without errors):
  `variation part def S { variant part <'PC-002'> radar; }`, `variant part <'PC-002'> radar : Radar;`, `variant action <'F-9'> a;`, `variant #Electrical part <'PC-3'> ecu;`, `variant part radar;` (still parses), `variant x;` (variant reference, still parses).
- [ ] **Step 2: Run** `cargo test -p sysml-syntax --test variant_members`. Expected: FAIL on the snippets with `<'…'>` after a kind keyword.
- [ ] **Step 3: Fix `kw_usage`**: when the bumped keyword is `VARIANT_KW`, after `opt_prefix_metadata()` accept modifier keywords and, if `self.current().is_def_kind_kw()`, call `self.def_kind_keywords()` and then `opt_prefix_metadata()` again, before `opt_short_name()`/`opt_decl_name()`. Check that the resulting CST still lowers to the same element kind (the builder decides the kind from the keyword token inside `USAGE`; adjust only if a model test shows otherwise).
- [ ] **Step 4: Write the model/export test**: `package P { part def S; variation part def V { variant part <'PC-002'> radar; } }` builds an element with short name `PC-002`, name `radar`, kind `PartUsage`, owned through a `VariantMembership`.
- [ ] **Step 5: Run** `cargo test --workspace` and the corpus test (`cargo test -p sysml-corpus` or the repo's documented corpus command). Expected: PASS, corpus unchanged.
- [ ] **Step 6: Commit** on a branch `fix/variant-member-ids`: `fix: accept ids and names on variant members`.
- [ ] **Step 7: Release**: after the user approves merging and pushing, merge to `main`, tag `v0.1.4-kit.2`, push the tag. (Pushing needs the user's go-ahead; stop and ask.)

### Task A2: pin the kit to the new fork tag

**Files:**
- Modify: `plugins/sysml-rflp/templates/project/Makefile:10`, `examples/vehicle/Makefile:10` (`SYSML_TAG = v0.1.4-kit.2`)
- Modify: `README.md` (Tools and versions table: tag and one line "accepts ids on variant members")

- [ ] **Step 1:** Change both `SYSML_TAG` lines and the README row.
- [ ] **Step 2: Run** `PYTHONPATH=src python -m unittest discover -s tests`. Expected: PASS (`test_template` keeps both Makefiles in sync).
- [ ] **Step 3: Commit**: `chore: pin sysml fork v0.1.4-kit.2`.

---

## Part B: kit

### Task B1: need types from keywords, domain, prefix agreement

**Files:**
- Modify: `src/sysml2kit/needs.py`
- Modify: `plugins/sysml-rflp/templates/project/model/trace.sysml` and `examples/vehicle/model/trace.sysml`
- Test: `tests/test_needs.py`

**Interfaces:**
- Produces in `trace.sysml` (package `Trace`): `metadata def Feature;`, `metadata def Mechanical;`, `metadata def Electrical;`, `metadata def Software;`, `metadata def Matches { attribute need : String[1..*]; attribute partial : ScalarValues::Boolean[0..1]; }`.
- Produces in `needs.py`: `KEYWORD_TYPES = {("ActionUsage", "Trace::Feature"): "feature", ("ActionDefinition", "Trace::Feature"): "feature", ("PartUsage", <domain>): "physical", ("PartDefinition", <domain>): "physical", ("PortUsage", <domain>): "physinterface", ("PortDefinition", <domain>): "physinterface"}`; `DOMAINS = {"Trace::Mechanical": "ME", "Trace::Electrical": "EE", "Trace::Software": "SW"}`; `PREFIXES = {"usecase": "UC", "sysreq": "SR", "feature": "FEAT", "function": "F", "component": "LC", "interface": "LI", "physical": "PC", "physinterface": "PI", "systest": "STC"}`; every need gets field `domain` (`"ME"|"EE"|"SW"|""`).

- [ ] **Step 1: Write failing tests** in `ConvertTest`:
  - `test_feature_keyword_makes_a_feature`: an `ActionUsage` `FEAT-1` annotated by a `MetadataUsage` typed `Trace::Feature` → type `feature`; its owned `ActionUsage` `F-1` stays `function` with `owned_by == ["FEAT-1"]` and `leaf` true.
  - `test_domain_keyword_makes_a_physical_component`: `PartUsage` `PC-1` with `Trace::Electrical` → type `physical`, `domain == "EE"`; `PortUsage` `PI-1` with `Trace::Mechanical` → `physinterface`, `domain == "ME"`.
  - `test_two_domains_is_an_error`: `PC-1` with both `Electrical` and `Software` → `BridgeError` mentioning `PC-1` and both keywords.
  - `test_prefix_must_match_type`: a `PartUsage` `LC-1` with `Trace::Electrical` → `BridgeError` "LC-1: a physical component's id starts with PC-"; a platform-tagged `PLT1-PC-1` with `Electrical` is accepted.
  - `test_untagged_model_converts_as_before`: `model()` from the existing fixture converts to the same types as today and `domain == ""` everywhere.
- [ ] **Step 2: Run** `PYTHONPATH=src python -m unittest tests.test_needs -v`. Expected: the new tests FAIL.
- [ ] **Step 3: Implement** in `convert`: before the type loop, collect `keywords[element_id] -> set of metadata qualified names` from every `MetadataUsage`'s `type` and `annotatedElement` (the trace-link loop already reads these; share the lookup). Type = `KEYWORD_TYPES` hit for (metaclass, keyword), else `NEED_TYPES`. Check the prefix with `re.fullmatch(rf"([A-Z][A-Z0-9]*-)?{PREFIXES[kind]}-\d+", short)` only for types in `PREFIXES`; existing fixtures use `UC-1` style ids, so the digit count is not checked here (the `id_regex` in `ubproject.toml` checks 3+ digits). Keyword metadata is not a trace link; skip it in the `MetadataUsage` branch.
- [ ] **Step 4: Run** the tests. Expected: PASS, all old tests too.
- [ ] **Step 5: Commit**: `feat: feature and physical need types from keywords`.

### Task B2: platform, variants, specializes, matches

**Files:**
- Modify: `src/sysml2kit/needs.py`, `src/sysml2kit/cli.py`
- Test: `tests/test_needs.py`

**Interfaces:**
- Consumes: B1's `keywords` lookup and `Trace::Matches`.
- Produces: `convert(elements, locations, platform_files=())` (new keyword argument, a collection of file paths); `write_needs(export_path, out_path, model_files, platform_files=())`; CLI `sysml2kit needs <export> <out> <files…> [--platform <file>…]`. New need fields: `platform` (bool: its `source` file is in `platform_files`), `variant` (bool: its `owningRelationship` has `@type` `VariantMembership`). New link types in `LINK_TYPES`: `specializes`, `matches`, `partial_matches`.

- [ ] **Step 1: Write failing tests**:
  - `test_platform_flag_from_source_file`: locations `{"PLT1-PC-1": "platform/model/p.sysml:3", "PC-1": "model/a.sysml:1"}`, `platform_files={"platform/model/p.sysml"}` → `PLT1-PC-1.platform` true, `PC-1.platform` false.
  - `test_variant_member_is_marked`: a `PartUsage` whose `owningRelationship` is a `VariantMembership` element → `variant` true.
  - `test_specializes_from_subsetting_redefinition_typing`: `Redefinition`/`Subsetting`/`Subclassification`/`FeatureTyping` elements with `specific`/`general` refs between two needs → `specializes` link specific → general; `isImplied: true` relationships are ignored; an end without a short name is skipped silently (no `BridgeError`).
  - `test_matches_and_partial`: `@Matches { need = "CRS-1"; }` on `FEAT-1` → `matches == ["CRS-1"]`; with a `LiteralBoolean` `true` under it → `partial_matches == ["CRS-1"]` and `matches == ["CRS-1"]`; `@Matches` on a non-feature → `BridgeError` "only a feature matches a customer requirement".
- [ ] **Step 2: Run** tests. Expected: FAIL.
- [ ] **Step 3: Implement**: `specializes` via the relationship elements' `specific`/`general` (verified keys in `sysml export`); `Trace::Matches` added to `TRACE_METADATA` as `matches`, with the `partial` flag read from a `LiteralBoolean` under the metadata usage (the `need` strings are read by the existing `strings_under`). `cli.py`: add `--platform` (nargs `*`) to the `needs` subcommand and pass it through.
- [ ] **Step 4: Run** tests. Expected: PASS.
- [ ] **Step 5: Commit**: `feat: platform and variant needs, specializes and matches links`.

### Task B3: reuse status per feature

**Files:**
- Create: `src/sysml2kit/reuse.py`
- Modify: `src/sysml2kit/needs.py` (call it at the end of `convert`)
- Test: `tests/test_reuse.py` (new)

**Interfaces:**
- Consumes: needs dict from B1/B2 (fields `type`, `platform`, `variant`, links `owned_by`, `allocated_to`, `specializes`).
- Produces: `reuse(needs: dict) -> dict[str, str]` (feature id → one of `platform`, `variant`, `modified`, `new`, `incomplete`); `convert` writes it as field `reuse` on each feature (other needs get `""`).

The walk, which the tests determine except for this order:

```text
functions(feature)   = leaf functions owned (transitively, via owned_by) by the feature
                       or by any need it specializes (transitively)
components(function) = needs it is allocated_to, plus their leaf component descendants
physicals(lc)        = physical needs lc is allocated_to (transitively through owned_by children)
platform_pc(pc)      = pc.platform, or pc specializes (transitively) a platform physical
via_variant(pc)      = pc.variant, or pc specializes (transitively) a variant physical
status: no pc reached -> incomplete; all platform_pc -> variant if any via_variant else platform;
        some platform_pc -> modified; none -> new
```

Every transitive step keeps a visited set.

- [ ] **Step 1: Write failing tests** in `tests/test_reuse.py`, building needs dicts directly (helper like `test_render.need`): `test_platform_chain`, `test_variant_chain` (RFQ PC specializes a platform variant PC), `test_mixed_chain_is_modified`, `test_all_new_is_new`, `test_no_physical_is_incomplete`, `test_inherited_functions_count` (RFQ feature specializes a platform feature whose function is allocated to a platform LC allocated to a platform PC → `platform`), `test_cycle_terminates` (two features specializing each other, and an `owned_by` loop, return within the test; status `incomplete`).
- [ ] **Step 2: Run** `PYTHONPATH=src python -m unittest tests.test_reuse -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `reuse` and call it from `convert`.
- [ ] **Step 4: Run** all unit tests. Expected: PASS.
- [ ] **Step 5: Commit**: `feat: derive each feature's platform reuse`.

### Task B4: `sysml2kit compliance`

Runs after the first Sphinx pass, where the CRS and CST needs (Markdown) and the model needs are in one `needs.json`, like `sysml2kit trace`.

**Files:**
- Create: `src/sysml2kit/compliance.py`
- Modify: `src/sysml2kit/cli.py`
- Test: `tests/test_compliance.py` (new)

**Interfaces:**
- Consumes: `build/needs/needs.json` (the needs dict as in `trace`); fields from B2/B3; CST needs with `answers` link and `compliance` field.
- Produces: `compliance(needs: dict) -> tuple[list[Row], list[str]]` where `Row = (crs_id, title, features: list[str], reuse: str, partial: bool, statements: list[str], domains: list[str])` and the list is findings; `table_md(rows) -> str` (a MyST Markdown table with need links `` {need}`CRS-001` ``); CLI `sysml2kit compliance <needs.json> <out.md> [--warn-only]` writes the table and prints findings, exit 1 on findings unless `--warn-only`.

Findings (one line each, `<id>: <message>`):
- CRS neither matched by a feature (`matches`) nor answered by a CST: "not answered".
- feature with reuse `incomplete` that matches a CRS: "matched, but its chain reaches no physical component".
- a feature lists the CRS in `partial_matches`, but no SR that `satisfies` that CRS is satisfied by a component in the feature's chain: "partial match without a system requirement stating the gap".

Row `reuse` = worst over its features (`new` > `modified` > `variant` > `platform`; `incomplete` ranks worst of all); `partial` true if any matching feature lists it in `partial_matches`; `domains` = sorted union of the `domain` of the PCs in the features' chains (B3 exposes the PCs reached: produce `reused_pcs(needs, feature_id) -> set[str]` in `reuse.py` and reuse it here).

- [ ] **Step 1: Write failing tests**: `test_platform_feature_row`, `test_worst_reuse_wins`, `test_unanswered_crs_is_a_finding`, `test_feature_and_statement_both_listed`, `test_partial_only_is_answered_but_flagged` (row `partial` true; finding only if no gap SR), `test_incomplete_match_is_a_finding`, `test_table_links_each_need`.
- [ ] **Step 2: Run** tests. Expected: FAIL.
- [ ] **Step 3: Implement** `compliance`, `table_md`, the CLI subcommand.
- [ ] **Step 4: Run** all unit tests. Expected: PASS.
- [ ] **Step 5: Commit**: `feat: compliance table from matches and statements`.

### Task B5: template, rules, Makefile, hook

**Files:**
- Modify (template and example, identically): `docs/ubproject.toml`, `docs/schemas.json`, `docs/conf.py`, `requirements.txt`, `Makefile`; create `docs/compliance.md`; add it to `docs/index.rst` toctree.
- Modify: `src/sysml2kit/gaps.py`, `plugins/sysml-rflp/scripts/lint_on_edit.py`
- Test: `tests/test_gaps.py`, `tests/test_hook.py` (new; or extend `tests/acceptance.py` `hook` if a unit test cannot run without `sysml`)

**Interfaces:**
- `ubproject.toml`: types `prq` (PRQ-), `cst` (CST-), `feature` (FEAT-, "Feature"), `physical` (PC-, "Physical component"), `physinterface` (PI-, "Physical interface"); links `specializes`, `matches`, `partial_matches`, `answers`; fields `domain`, `reuse`, `variant` (boolean), `platform` (boolean), `compliance` (CST only, enum per Global Constraints); every model type's `id_regex` gets the optional tag group.
- `schemas.json`: every rule's `select` adds `"platform": {"const": false}` for model needs (so platform needs are never checked in an RFQ build; in the platform's own build `--platform` is empty and everything is `false`). Rules on `crs` also select `prq`. `usecase-realized` → realized by a `feature` (feature `realizes` via `perform`). New: `feature-realizes` (F: every feature realizes ≥1 use case), `logical-allocated` (P: every leaf component allocated_to ≥1 physical), `physical-used` (P: every leaf physical has ≥1 incoming `allocated_to` from a component). `crs-satisfied` stays.
- `gaps.py`: `LAYERS = "RFLPV?"`; `RULE_LAYERS` adds `feature-realizes: "F"`, `logical-allocated: "P"`, `physical-used: "P"`.
- `Makefile`: `PLATFORM_MODEL := $(shell test -d platform/model && find platform/model -name '*.sysml' | sort)`; `lint` checks `model $(if $(PLATFORM_MODEL),platform/model)`; export and `sysml2kit needs` get `$(MODEL) $(PLATFORM_MODEL)` and `--platform $(PLATFORM_MODEL)`; `docs` runs `$(SYSML2KIT) compliance build/needs/needs.json $(GEN)/compliance.md $(if $(STRICT),,--warn-only)` after the `needs` pass. `conf.py`: `extensions = ["myst_parser", "sphinx_needs"]`, MyST `colon_fence`. `requirements.txt`: `myst-parser` pinned to the current release.
- Hook: when `<project>/platform/model` exists, `sysml check` and export include it, and the bridge gets `--platform`.

- [ ] **Step 1: Write failing tests**: in `test_gaps.py`, `test_physical_rules_are_in_p` and keep `test_every_rule_in_the_schema_has_a_layer` passing with the new rules; `test_hook_includes_platform_model` (run `lint_on_edit.py` with a stub `sysml` on `PATH` that records its arguments; assert `platform/model` is among them).
- [ ] **Step 2: Run** unit tests. Expected: new tests FAIL.
- [ ] **Step 3: Implement** the files above.
- [ ] **Step 4: Run** unit tests, `claude plugin validate .`, `ruff check . && ruff format --check .`. Expected: PASS.
- [ ] **Step 5: Commit**: `feat: P layer, platform model and compliance in the project template`.

### Task B6a: example product model `examples/edrive-platform`

A standalone platform project: an electric drive product line, captured as `references/platform-capture.md` describes, so it doubles as the worked example of that mode. It builds on its own with `make all` (strict) under the same template and rules, PRQ in the role of CRS.

**Files:**
- Create: `examples/edrive-platform/` from the template (`Makefile`, `requirements.txt`, `docs/`, `model/trace.sysml` byte-identical to the template's; `tests/test_template.py` extended to compare this example too)
- Create: `docs/platform/requirements.md` (PRQ), `model/requirements/use_cases.sysml`, `model/requirements/system_requirements.sysml`, `model/functional/features.sysml`, `model/logical/architecture.sysml`, `model/physical/components.sysml`, `model/verification/system_tests.sysml`, `test-results/junit.xml`, `docs/software/requirements.md` (SWR for the software PCs)
- Modify: `tests/acceptance.py` (build this example clean before the vehicle one)

Content: every id tagged `EDU-` (e.g. `EDU-FEAT-001`). 3–4 PRQ; 2 use cases (drive the vehicle, recover braking energy); features `tractionDrive`, `regenerativeBraking`; functions with at least one sub-function level; LCs `motor`, `inverter`, `driveController`, `housing`; PCs in all three domains: `#Electrical` motor with a `variation` of two `variant part`s (`EDU-PC-…` `motor50kW`, `motor80kW`), `#Electrical` inverter, `#Software` controller firmware (linked from an SWR need), `#Mechanical` housing; one PI per domain allocated from an LI; each PC's `doc` names its BOM part number (BOM, layout and code artifacts are not need types in this round). STCs and a JUnit result so the V layer passes.

- [ ] **Step 1: Extend `tests/acceptance.py`**: `examples/edrive-platform` must pass `make all`; one mutation must fail it (remove the housing's `#Mechanical` keyword → prefix error).
- [ ] **Step 2: Run** `python tests/acceptance.py`. Expected: FAIL (example missing).
- [ ] **Step 3: Write** the example.
- [ ] **Step 4: Run** `python tests/acceptance.py` and the unit tests. Expected: PASS.
- [ ] **Step 5: Commit**: `feat: example e-drive product line platform`.

### Task B6: migrate `examples/vehicle`

**Files:**
- Modify: `examples/vehicle/model/**`, `examples/vehicle/docs/**`
- Create: `examples/vehicle/platform` as a relative symlink to `../edrive-platform` (stands in for the submodule; shortcut: symlinks need Linux/macOS or Git with symlink support on Windows, fine for the CI runner), `examples/vehicle/docs/customer/requirements.md` (replacing `requirements.rst`), `examples/vehicle/docs/customer/statements.md`
- Modify: `tests/acceptance.py`

Content: the platform is the Task B6a e-drive product line (needs Task A1's tag for its variants). The vehicle's powertrain uses it: one LC allocated to the platform inverter (`platform`), one to an RFQ part redefining `motor80kW` (`variant`). Each existing function tree sits under a `#Feature action` (noun names, e.g. `FEAT-001 travelRange`); the logical components are allocated to PCs, one of them redefining a platform variant, one a new `#Mechanical` part; one CRS is commercial (warranty) and answered by `CST-001`; one feature carries a partial match with its gap SR. Expected compliance table: at least one row each of `platform`/`variant`, `modified` or `new`, a partial row and a CST row.

- [ ] **Step 1: Update `tests/acceptance.py`** first: the clean build must pass and produce `docs/_generated/compliance.md`; new mutations that must fail `make all`: drop the CST (finding "not answered"), remove an LC → PC allocation (`logical-allocated`), drop the gap SR's `satisfies` (partial finding), remove the `#Feature` keyword from a feature (prefix error from the bridge). Keep the existing mutations, re-targeted to the new files.
- [ ] **Step 2: Run** `python tests/acceptance.py`. Expected: FAIL (example not migrated).
- [ ] **Step 3: Migrate** the example as described.
- [ ] **Step 4: Run** `python tests/acceptance.py` and `python tests/omg_corpus.py`. Expected: PASS.
- [ ] **Step 5: Commit**: `feat: vehicle example on the RFQ chain with a platform`.

### Task B7: agents, skills, docs

**Files:**
- Modify: `plugins/sysml-rflp/agents/functional-architect.md` (features as `#Feature action` with noun names owning functions and sub-functions; `perform` the feature in the use case), `logical-architect.md` (stops at LCs and LIs; may allocate to existing platform PCs only via the physical architect), `rflp-reviewer.md` (runs `sysml2kit compliance` too; checks noun feature names, domains), `requirements-analyst.md` (CRS in Markdown; CST for requirements no architecture element can meet)
- Create: `plugins/sysml-rflp/agents/physical-architect.md` (P layer: PCs/PIs with exactly one domain keyword, `allocate` LC to PC and LI to PI (decision for the spec's open "PI → LI link form": a native allocation, which the bridge already turns into `allocated_to`), reuse platform PCs by redefinition or variant selection before creating new ones, links software PCs to SWR needs)
- Modify: `plugins/sysml-rflp/skills/rflp/SKILL.md` (step table gains P between L and V with `physical-architect` and gate rules `logical-allocated`, `physical-used`; V gate adds the compliance findings)
- Create: `plugins/sysml-rflp/skills/rfq/SKILL.md` and `references/questions.md`, `references/platform-capture.md`
- Modify: `plugins/sysml-rflp/skills/rflp-method/references/structure.md` (artifact table and rules from the spec), `plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml` (feature, domain keyword, variation/variant, redefining a platform variant, `@Matches`), `plugins/sysml-rflp/skills/sysml-init/SKILL.md` (optional `git submodule add <platform repo> platform`), `glossary.md`, `README.md`

`rfq` skill content (from the spec's interview section): inputs (CRS Markdown, PRQ in the platform, other RFQ documents read as cited context); per layer ask → create → validate, asking only what the inputs leave open, one topic at a time; question topics per layer in `references/questions.md`: problem statement, stakeholders, system boundary and context, external interfaces, operating conditions, quantities without values, variant choices, commercial requirements that need a CST; then run the `rflp` steps R, F, L, P, V with approval between layers; finish with the compliance table. `references/platform-capture.md`: bottom-up mode for the platform repo: from BOM/code/documents create tagged PCs, then interview upward for LCs, functions, features and variants.

- [ ] **Step 1: Write** the agent, skill and reference files.
- [ ] **Step 2: Check** `patterns.sysml` with `sysml check plugins/sysml-rflp/skills/sysml-author/references/patterns.sysml` (plus `trace.sysml` if it imports `Trace`). Expected: 0 errors.
- [ ] **Step 3: Run** `claude plugin validate . && claude plugin validate ./plugins/sysml-rflp`. Expected: PASS.
- [ ] **Step 4: Dry run** (manual): in a scratch copy of the template with the example's platform, ask Claude to run the `rfq` skill on two CRS and confirm it asks only about what the CRS leave open and stops for approval after R. Note the result in the PR description.
- [ ] **Step 5: Commit**: `feat: rfq interview skill and physical architect`.

### Task B8: release

- [ ] **Step 1:** Bump the version in `pyproject.toml`, the plugin manifest and the template pin to `0.2.0` (`test_template.ReleaseVersionTest` keeps them equal); add the README "Known limits" line: reuse is about platform components, not whether a requirement's value is met (that is `partial`).
- [ ] **Step 2: Run** the full Development commands from the README. Expected: all PASS.
- [ ] **Step 3: Commit**: `Release 0.2.0`. Pushing and the PR wait for the user.
