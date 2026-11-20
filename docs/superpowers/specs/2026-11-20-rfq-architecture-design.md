# RFQ system architecture with sysml2-kit: design

Date: 2026-11-20. Status: draft, awaiting the user's approval. Builder check done; decisions taken without the user are marked "decision".

## Intent

A supplier answers a customer RFQ. Claude reads the customer requirements (sphinx-needs in Markdown), the supplier's platform requirements and the RFQ documents, interviews the user to fill gaps, and builds a SysML v2 system architecture from the problem space down to physical components across mechanical, electrical and software engineering. The architecture is put together from the supplier's existing platforms and technologies, with variants, so the docs build shows which customer requirement is met by which platform feature, which only partly, and which needs new development. Code, artifacts and tests stay traced through sphinx-needs as today.

This is still RFLP. The chain the user models is R (customer requirement, use case) → F (feature, function, sub-function) → L (logical component, logical interface) → P (physical component). What changes against today's kit: a Feature layer, nested sub-functions, the P layer moves into the SysML model with an engineering domain, a platform library with variants, a matching status, Markdown customer requirements, and an interview workflow.

## Goals

- Claude builds the model layer by layer from the RFQ inputs and the user's answers, with the existing checker hook, bridge and gap list in the loop, and the user's approval between layers (as the `rflp` skill does today).
- A reusable platform model (features, functions, components, interfaces, variants) that each RFQ project imports instead of remodeling.
- RFQ matching visible in the docs build: per customer requirement, the feature(s) that cover it, how much of the solution is reused from the platform (derived from the model), and whether the match is only partial; or, for a requirement no feature can meet, a textual compliance statement.
- Physical components and interfaces carry their domain (ME, EE, SW); software ones keep linking to code and tests in sphinx-needs.
- The docs build stays the traceability report: `sphinx-build -W` fails on a broken RFLP rule.

## Non-goals

- No modeling GUI, no simulation, no cost estimation. Syside, Aliot or any editor works on the same files; the kit does not depend on one.
- No general method engine: one method, defined in the kit (approach 2 rejected below).
- No adoption of SYSMOD, OOSEM or RAWP as metamodel. SYSMOD's problem-space questions and its question → create → validate pattern are borrowed for the interview, as prose in the skill, not by importing `SYSMOD4AI.sysml` (it does not parse with the kit's checker: multi-line string literals).
- No ReqIF/Excel import in this round; customer requirements arrive as sphinx-needs Markdown.

## Anti-goals

- A compliance answer the model cannot back: a `platform` status on a requirement whose feature has no allocated physical component is wrong, not optimistic.
- Invented numbers. A value the RFQ or the user did not give is an open question, as the requirements analyst already does.
- RFQ-specific ids or links written into the platform library.

## Approaches

1. **Rework the kit's RFLP method into this chain** (chosen). Extend the layers, bridge, rules and agents in place; migrate the vehicle example and acceptance tests. Least code: checker hook, bridge, MCP `find`/`relations`, gap list and trace graph all carry over.
2. **Configurable method** (layers, need types and rules from a config file) so the old and new chains coexist. Rejected: only pays if someone still needs the old chain; nobody does.
3. **SYSMOD metamodel with the chain mapped onto it.** Rejected: SYSMOD has no Feature, no engineering domain and no variant model; every layer would fight it.

## Layers and artifacts

| Layer | Artifact | Id | Written in | Outgoing links |
|---|---|---|---|---|
| R | Customer requirement | `CRS-nnn` | sphinx-needs Markdown (MyST) | none |
| R | Platform requirement | `PRQ-nnn` | sphinx-needs Markdown, in the platform repo | none |
| R | Compliance statement | `CST-nnn` | sphinx-needs Markdown, in the RFQ project | answers → CRS |
| R | Use case | `UC-nnn` | SysML `use case` | realizes → CRS (`@Realizes`) |
| R | System requirement | `SR-nnn` | SysML `requirement` | satisfies → CRS (`@Satisfies`) |
| F | Feature | `FEAT-nnn` | SysML `#Feature action`, noun name | realizes → UC (`perform` in the use case); matches → CRS (see Matching) |
| F | Function / sub-function | `F-nnn` | SysML `action` owned by a feature or function | owned_by → FEAT/F |
| L | Logical component | `LC-nnn` | SysML `part` | satisfies → SR (`satisfy`) |
| L | Logical interface | `LI-nnn` | SysML `port` on an LC | none |
| L | Allocation | none | `allocate <F> to <LC>` | F allocated_to → LC |
| P | Physical component | `PC-nnn` | SysML `#Mechanical`/`#Electrical`/`#Software part` | LC allocated_to → PC |
| P | Physical interface | `PI-nnn` | SysML `port` on a PC, same domain keywords | realizes → LI (`@Realizes` or allocation, builder's call) |
| V | System / acceptance test, result | `STC`/`ATC`/generated | as today | as today |

Feature as a tagged `action`: a feature is "what the product does", fulfils a use case, and owns the functions that make it up, so action nesting gives sub-functions, `perform` gives the use case link and `allocate` keeps working. The name is a noun (`adaptiveCruiseControl`). The keyword `#Feature` is a metadata definition in `trace.sysml` (renamed or kept; builder's call) and avoids the SysML term "feature". Verified: `#Feature action <'FEAT-001'> x { action <'F-001'> y; }` checks clean and the export carries a `MetadataUsage` typed `…::Feature` annotating `FEAT-001`.

Domain: `#Mechanical`, `#Electrical`, `#Software` on physical parts and ports. The bridge writes a `domain` field (`ME`/`EE`/`SW`) and the need type `physical` / `physinterface`. A part or port without one of these keywords stays logical. Software PCs are the link target for today's `SWR` needs and code/test traces.

System requirements stay (between CRS and LC, as today; confirmed by the user). An SR is a SysML `requirement` whose substance is its `doc` text; it does not have to be broken down into model structure. Requirements that no architecture element can meet (commercial terms, delivery, process, certification) stay textual and are answered by a compliance statement (below), not forced into the model.

## Bridge changes (`sysml2kit needs`)

Today the need type comes from the metaclass alone. It becomes metaclass plus keyword: `ActionUsage` + `#Feature` → `feature`; `PartUsage` + domain keyword → `physical`; `PortUsage` + domain keyword → `physinterface`; otherwise as today. The id prefix must agree with the derived type (error otherwise, at edit time through the hook). New fields: `domain`, `reuse`, `partial`, `variant` (true for a variant member), `platform` (true for an element from the platform library). Sub-functions need no change: `owned_by` and `leaf` already handle nesting.

## Platform library and variants

The platform is the supplier's technology components and product lines. Today it is a collection of physical components with their BOM, layout and code; the user will model the layers above (features, functions, logical) over time. So the design must work with a platform that holds only PCs: an RFQ project then draws its own features, functions and LCs and allocates its LCs to platform PCs. As the platform gains upper layers, RFQ features specialize platform features instead. Each PC links to its BOM, layout and code artifacts through sphinx-needs, as software components do to code today.

Capturing the platform is a second use of the same workflow, bottom-up: start from the BOM/code and existing documents, create the PCs, then interview the user upward for what each component does (LC, functions) and what is sold (features, variants).

The platform is its own repo (a sphinx-needs + SysML project with the same layout), so its requirements, tests and results stay with it. An RFQ project pulls it in as a git submodule or a sysand package (builder's call; sysand is Sensmetry's SysML package manager, `sysand add`). `make` loads `model/` plus the platform model path. Platform elements become needs in the RFQ docs with `platform: true`.

Variants use native SysML v2 `variation`/`variant` in the platform: a variation feature or part with its variant members; the RFQ model selects one by redefinition. Verified: `variation part sensor : Sensor { variant part lidar : Lidar; … }` checks clean. Known blocker: `variant part <'PC-002'> radar;` (a variant with a short name) fails to parse in the fork `v0.1.4-kit.1`. The spec's variant member grammar admits a full usage declaration, so this is a parser bug to fix in the fork (new tag, as was done for sequence expressions) before variants can be needs.

Rules apply only to what the RFQ selects: an unselected variant is not "a component without allocated function". How "selected" is determined (the redefinition target in the RFQ model) is the builder's call; the bridge marks unselected variants so the schemas can exclude them.

Rule scope (decision, not from the user): one template and one rule set for both project kinds. In the platform project, PRQ plays the role CRS plays in an RFQ project (the CRS rules select `crs` or `prq`). In an RFQ build, the RFLP rules select only needs with `platform: false`; platform needs are referenced, and the platform's own build checks them. So an unused platform feature never fails `feature-realizes` in an RFQ build.

Ids across the boundary (decision): platform ids carry a platform tag before the type prefix (`PLT1-FEAT-001`, `PLT1-PC-004`); `id_regex` becomes `^([A-Z][A-Z0-9]*-)?FEAT-[0-9]{3,}$` and so on. The bridge adds a `specializes` link for subclassification, subsetting and redefinition between two needs. An RFQ feature specializing a platform feature inherits its chain: coverage checks follow `specializes` into the platform needs. A selected variant needs no RFQ id; the RFQ part that redefines it does.

## Matching

The RFQ project (never the platform) states coverage on its own features with metadata, one annotation per CRS:

```sysml
#Feature action <'FEAT-010'> acc :> Platform::adaptiveCruiseControl {
    @Matches { need = "CRS-004"; }
}
```

The reuse status is derived, not claimed (decision; it follows from the anti-goal and from a platform that is mostly PCs today). The bridge follows each matched feature down its chain (feature → leaf functions → LC → PC, through `specializes` into platform needs) and computes:

- `platform`: every PC reached is a platform PC, no variant involved;
- `variant`: every PC reached is a platform PC, at least one through a selected variant;
- `modified`: some PCs reached are platform, some new;
- `new`: no platform PC reached;
- `incomplete`: the chain does not reach a PC. The build fails on this once the P layer is in the gate.

Separately, `@Matches { need = "CRS-004"; partial = true; }` states that the feature meets the requirement only in part (a value not reached, a condition excluded); a partial match must satisfy at least one SR whose text states the gap.

Storage: the bridge writes a `matches` link from feature to CRS and, on the CRS, the computed fields `reuse` (worst over its features: new > modified > variant > platform) and `partial`. The compliance table reads them.

Compliance statement (`CST-nnn`, sphinx-needs Markdown in the RFQ project): answers a CRS that no feature can meet, with a `compliance` field (`comply`, `partial`, `not-comply`) and the supplier's text. `crs-matched` becomes: every CRS is matched by a feature or answered by a CST.

Rules added: every CRS is matched by at least one feature (`crs-matched`); every feature realizes a use case (`feature-realizes`); every leaf function is allocated (existing rule, now including sub-functions); every leaf LC is allocated to at least one PC (`logical-allocated`); every PC has a domain (by construction) and at least one LC allocated (`physical-used`). The status checks above run in the bridge, since they cross several link types. The docs get a compliance table: CRS, matched features, status, domains involved, gaps.

## Interview workflow

A new skill (`rfq`) drives the RFLP workflow for an RFQ, replacing `rflp`'s entry point: read the inputs, then per layer ask → create → validate. Questions per layer live as Markdown references in the skill (problem statement, stakeholders, system boundary and context, external interfaces, operating conditions, quantities without values, variant choices). Claude asks only what the inputs do not answer, one topic at a time, records answers as model content or open questions, runs the layer's agent, the reviewer and `sysml2kit gaps --layer`, and stops for the user's approval. A `physical-architect` agent is added for the P layer; the `functional-architect` agent writes features and sub-functions; the `logical-architect` adds logical-to-physical allocation hand-off.

RFQ documents other than CRS (PDF, Word, drawings) are read by Claude as context; facts taken from them are cited in the interview, not silently turned into requirements.

## Migration

`examples/vehicle` moves to the new chain (features, PCs with domains, CRS in Markdown, a small platform with one variation) and stays the acceptance fixture. `structure.md`, the glossary, need types in `ubproject.toml`, `schemas.json`, `gaps.RULE_LAYERS` (adds `P`) and the README follow. The docs template adds `myst-parser`.

## Left to the builder

- Name of the metadata package for `#Feature`, domain keywords and `@Matches` (extend `Trace` or a new `Rfq` package).
- Physical interface → logical interface link form.
- Submodule vs sysand for the platform; how the Makefile passes the platform path to `sysml check` and export.
- How unselected variants are detected and excluded from rules.
- The fork fix for short names on variant members.
