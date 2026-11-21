# RFLP structure: customer requirement to acceptance test

Requirements → Functional → Logical → Physical, verified on the right side of the V. R, F, L and P are in the SysML model (customer requirements, statements and software requirements are Markdown needs); software PCs also link to code and tests in sphinx-needs.

## Artifacts

| Layer | Artifact | Id | Written in | Outgoing links |
|---|---|---|---|---|
| R | Customer requirement | `CRS-nnn` | Markdown (MyST) `crs` directive, `docs/customer/`; `:class:` functional, non-functional, constraint or information | none |
| R | Platform requirement | `PRQ-nnn` | Markdown `prq` directive, in the platform project; `:class:` as for CRS | none |
| R | Customer test requirement | `CTR-nnn` | Markdown `ctr` directive, `docs/customer/`; `:purpose:` verification or validation, `:method:` test, analysis, inspection or demonstration | `applies_to` → CRS/PRQ (`:applies_to:`) |
| R | Compliance statement | `CST-nnn` | Markdown `cst` directive, in the RFQ project | answers → CRS; `compliance`: comply, partial, not-comply |
| R | Use case | `UC-nnn` | SysML `use case` | realizes → CRS (`@Realizes`) |
| R | System requirement | `SR-nnn` | SysML `requirement` usage, text in `doc` | satisfies → CRS (`@Satisfies`) |
| R | Constraint | `CON-nnn` | SysML `constraint` usage over a part attribute, owned by the part it limits | satisfies → CRS (`@Satisfies`; `partial = true` for a partial one) |
| F | Feature | `FEAT-nnn` | SysML `#Feature action`, noun name | realizes → UC (native: `perform` in the use case); matches → CRS (`@Matches`) |
| F | Function / sub-function | `F-nnn` | SysML `action` nested in a feature or function | owned_by → FEAT/F |
| L | Logical component | `LC-nnn` | SysML `part` usage tree | satisfies → SR (native `satisfy`) |
| L | Logical interface | `LI-nnn` | SysML `port` on a logical component | none |
| L | Allocation | none | SysML `allocate <function> to <component>` | F allocated_to → LC |
| P | Physical component | `PC-nnn` | SysML `#Mechanical`, `#Electrical` or `#Software part` | LC allocated_to → PC (`allocate`); specializes → platform PC (`:>`) |
| P | Physical interface | `PI-nnn` | SysML `port` on a PC, same domain keywords | LI allocated_to → PI (`allocate`) |
| V | System test case | `STC-nnn` | SysML `verification` | verifies → SR (native `verify`) or constraint (`@Verifies`); implements → CTR (`@Implements`) |
| V | Acceptance test case | `ATC-nnn` | Markdown or RST `acctest` | verifies → CRS, UC; implements → CTR (`:implements:`) |
| V | Test result | generated | JUnit XML, `<property name="verifies" value="STC-001"/>` | tests → STC/ATC |
| P | Software requirement | `SWR-nnn` | Markdown or RST `swreq` | satisfies → SR, realizes → software PC (no rules) |

Keywords `#Feature`, `#Mechanical`, `#Electrical`, `#Software` and the metadata `@Matches`, `@Satisfies`, `@Verifies`, `@Implements` are in `model/trace.sysml` (package `Trace`). A part or port without a domain keyword is logical. The id prefix must agree with the kind (`PC-` on a domain part, `FEAT-` on a `#Feature` action); the bridge errors otherwise. Exactly one domain keyword per element.

Rule of thumb: a link between two model elements is native SysML; a link that leaves the model uses `Trace` metadata, one annotation per target need.

## Model layout

```
model/trace.sysml                         Trace metadata (from the template, do not edit)
model/requirements/use_cases.sysml        package <Sys>UseCases
model/requirements/system_requirements.sysml  package <Sys>Requirements
model/functional/features.sysml           package <Sys>Features (features and their functions)
model/logical/architecture.sysml          package <Sys>Logical (components, ports, connections, allocations, satisfy)
model/physical/components.sysml           package <Sys>Physical (PCs, PIs, allocate LC to PC)
model/verification/system_tests.sysml     package <Sys>SystemTests
docs/customer/requirements.md            CRS
docs/customer/statements.md               CST
docs/acceptance/*.md                      ATC (RST also works)
platform/                                 the supplier's platform project (git submodule; see below)
test-results/*.xml                        JUnit results
```

Prefix package names with the system name; `UseCases`, `Requirements` and similar collide with the standard library.

## Requirement classes, constraints, customer test requirements

Classify every CRS and PRQ (`:class:`; rule `crs-class`). The class decides what the supplier owes:

- `functional`: a feature matches it (`@Matches`) and an SR or a constraint satisfies it.
- `non-functional` and `constraint`: a `CON-` constraint in the model satisfies it. A plain value (a mass, a speed, a voltage) is a constraint over a part attribute, never a bare attribute. Write a textual SR only for what the model cannot express.
- `information`: no obligation. No rule or compliance finding applies; nothing needs to satisfy, match, answer or verify it.

A constraint that satisfies a CRS only in part (`@Satisfies { need = "CRS-nnn"; partial = true; }`) needs an SR that satisfies the same CRS and states the gap.

CTRs are the customer's own test requirements, captured as written (`ctr` directive, `:applies_to:` the CRS or PRQ they test). The supplier does not rewrite them: its tests implement them, with `@Implements { need = "CTR-nnn"; }` in a system test or `:implements:` in an acceptance test. A CTR counts toward verifying every CRS it `applies_to`, whatever its scope. A system test verifies an SR or a constraint (`@Verifies`), or implements a CTR; an acceptance test verifies a CRS or UC, or implements a CTR. A CTR with `:scope: commercial` or `not-offered` needs a CST answer instead of an implementing test, and still needs that CST when a test implements it.

## Platform, variants, matching

The platform is the supplier's own project with this same layout (its PRQ play the role of CRS), in `<project>/platform/` as a git submodule (`git submodule add <platform repo> platform`; the repo examples use a symlink). Its ids carry a tag before the type prefix (`EDU-FEAT-001`, `EDU-PC-004`). `make` loads its model next to `model/`; its elements become needs with `platform: true`, which RFQ builds never rule-check (the platform's own build does).

- Reuse is subsetting: `part <'PC-001'> driveMotor :> EDrivePhysical::motor::motor80kW;` or `#Feature action <'FEAT-010'> acc :> PlatformFeatures::cruise;`. The bridge turns it into a `specializes` link; the coverage chain follows it into the platform.
- Variants are native `variation` / `variant` members in the platform; the RFQ part subsets one variant to select it. A chain that reaches a variation without such a selection reaches no PC there: the feature is `incomplete`.
- `@Matches { need = "CRS-001"; }` in a feature states that it covers that CRS; `partial = true` says only in part, and then an SR that satisfies the CRS must be satisfied by a component in the feature's chain (it states the gap).
- Reuse status per matched feature is derived from the chain feature → leaf functions → LC → PC, never written: `platform` (all PCs from the platform, no variant), `variant` (all from the platform, at least one a selected variant), `modified` (some platform, some new), `new` (no platform PC), `incomplete` (a leaf function reaches no PC). On a CRS: the worst of its features.
- A CRS with `:scope: commercial` (terms, delivery, warranty) or `:scope: not-offered` (a technical CRS the supplier does not meet at all) is exempt from `crs-satisfied` and from the not-verified finding and must be answered by a CST; for `not-offered` the CST is `not-comply`. A technical CRS met in part keeps empty scope: an SR states what is met, a feature or constraint covers it partially, a CST is optional. Adding `:scope:` is the one permitted edit to a customer's CRS. `sysml2kit compliance` runs at the V gate, fails the build, and reports (exact texts): `<CRS>: not answered` (nothing matches, satisfies or answers it); `<CRS>: not offered, but its statement is not not-comply`; `<CRS>: matched, but its chain reaches no physical component`; `<CRS>: variation <V> reached without a selected variant`; `<CRS>: partial match without a system requirement stating the gap`; `<CRS>: partial satisfaction without a system requirement stating the gap`; `<CRS>: not verified (no acceptance test, no implemented CTR applying to it)` (class functional, non-functional or constraint, empty scope; applies to PRQ too); `<CTR>: not implemented`; and for a CTR with scope, `<CTR>: not answered` or `not offered, but its statement is not not-comply` even when a test implements it.

## Rules (docs/schemas.json, enforced by `make all` and ubCode)

| Rule id | Layer gate | Rule |
|---|---|---|
| `crs-class` | R | every CRS and PRQ has a class |
| `crs-satisfied` | R | every CRS of class functional, non-functional or constraint with empty scope is satisfied by at least one SR or constraint |
| `constraint-satisfies` | R | every constraint satisfies at least one CRS |
| `usecase-realizes` | R | every UC realizes at least one CRS |
| `sysreq-satisfies` | R | every SR satisfies at least one CRS |
| `cst-compliance` | R | every CST has a compliance value (comply, partial or not-comply) |
| `usecase-realized` | F | every UC is realized by at least one feature |
| `feature-realizes` | F | every feature realizes at least one UC |
| `function-allocated` | L | every leaf function is allocated to exactly one component |
| `component-used` | L | every leaf logical component has at least one function allocated |
| `sysreq-satisfied` | L | every SR is satisfied by at least one component |
| `logical-allocated` | P | every leaf logical component is allocated to at least one PC |
| `physical-used` | P | every leaf PC has at least one logical component allocated |
| `systest-verifies` | V | every STC that implements nothing verifies at least one SR or constraint |
| `systest-implements` | V | every STC with `implements` links implements at least one CTR |
| `constraint-verified` | V | every constraint is verified by at least one STC |
| `ctr-implemented` | V | every CTR with empty scope is implemented by at least one STC or ATC |
| `acctest-verifies` | V | every ATC that implements nothing verifies a CRS or UC |
| `acctest-implements` | V | every ATC with `implements` links implements at least one CTR |
| `sysreq-verified` | V | every SR is verified by at least one STC |
| `usecase-verified` | V | every UC is verified by at least one ATC |

CRS and PRQ verification is not a schema rule: it is the computed compliance finding `<CRS>: not verified (no acceptance test, no implemented CTR applying to it)`, run by `sysml2kit compliance` at the V gate. `sysml2kit gaps` does not show it.

In an RFQ build the rules select only needs with `platform: false`. In the platform project `prq` needs take CRS's place in these rules.

"Leaf" means no child of the same type (a component that owns only ports is a leaf).

## Writing quality (the reviewer checks these; `sysml2kit` warns on an SR without exactly one `shall` or with TBD, etc., as appropriate, user-friendly, fast)

- **CRS** are the customer's words. Do not rewrite them; ask when one is ambiguous.
- **UC**: verb phrase from the actor's view (`commute`, `transportOnTrailer`), with subject and actors.
- **SR**: one `shall` per requirement; verifiable (a number with a unit, or an observable yes/no); solution-free (no component names, no technology); no TBD, "etc.", "as appropriate", "user-friendly", "fast".
- **FEAT**: a noun for what the product offers (`travelRange`, `adaptiveCruiseControl`), not a verb phrase.
- **F**: verb + noun, solution-neutral (`storeEnergy`, not `chargeBattery` unless the battery is a given constraint); nest sub-functions under the function they refine.
- **LC**: technology-neutral role (`energyStore`, not `liIonPack48V`); each leaf has a purpose (an allocated function).
- **PC/PI**: one domain keyword; the `doc` names the BOM item, drawing or code module; a platform part is reused with `:>` before a new one is created.
- **STC/ATC**: the `doc` says the procedure and the pass criterion.
