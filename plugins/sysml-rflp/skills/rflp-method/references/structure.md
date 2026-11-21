# RFLP structure: customer requirement to acceptance test

Requirements → Functional → Logical → Physical, verified on the right side of the V. R, F, L and P are in the SysML model (customer requirements, statements and software requirements are Markdown needs); software PCs also link to code and tests in sphinx-needs.

## Artifacts

| Layer | Artifact | Id | Written in | Outgoing links |
|---|---|---|---|---|
| R | Customer requirement | `CRS-nnn` | Markdown (MyST) `crs` directive, `docs/customer/` | none |
| R | Platform requirement | `PRQ-nnn` | Markdown `prq` directive, in the platform project | none |
| R | Compliance statement | `CST-nnn` | Markdown `cst` directive, in the RFQ project | answers → CRS; `compliance`: comply, partial, not-comply |
| R | Use case | `UC-nnn` | SysML `use case` | realizes → CRS (`@Realizes`) |
| R | System requirement | `SR-nnn` | SysML `requirement` usage, text in `doc` | satisfies → CRS (`@Satisfies`) |
| F | Feature | `FEAT-nnn` | SysML `#Feature action`, noun name | realizes → UC (native: `perform` in the use case); matches → CRS (`@Matches`) |
| F | Function / sub-function | `F-nnn` | SysML `action` nested in a feature or function | owned_by → FEAT/F |
| L | Logical component | `LC-nnn` | SysML `part` usage tree | satisfies → SR (native `satisfy`) |
| L | Logical interface | `LI-nnn` | SysML `port` on a logical component | none |
| L | Allocation | none | SysML `allocate <function> to <component>` | F allocated_to → LC |
| P | Physical component | `PC-nnn` | SysML `#Mechanical`, `#Electrical` or `#Software part` | LC allocated_to → PC (`allocate`); specializes → platform PC (`:>`) |
| P | Physical interface | `PI-nnn` | SysML `port` on a PC, same domain keywords | LI allocated_to → PI (`allocate`) |
| V | System test case | `STC-nnn` | SysML `verification` | verifies → SR (native `verify`) |
| V | Acceptance test case | `ATC-nnn` | Markdown or RST `acctest` | verifies → CRS, UC |
| V | Test result | generated | JUnit XML, `<property name="verifies" value="STC-001"/>` | tests → STC/ATC |
| P | Software requirement | `SWR-nnn` | Markdown or RST `swreq` | satisfies → SR, realizes → software PC (no rules) |

Keywords `#Feature`, `#Mechanical`, `#Electrical`, `#Software` and `@Matches` are in `model/trace.sysml` (package `Trace`). A part or port without a domain keyword is logical. The id prefix must agree with the kind (`PC-` on a domain part, `FEAT-` on a `#Feature` action); the bridge errors otherwise. Exactly one domain keyword per element.

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

## Platform, variants, matching

The platform is the supplier's own project with this same layout (its PRQ play the role of CRS), in `<project>/platform/` as a git submodule (`git submodule add <platform repo> platform`; the repo examples use a symlink). Its ids carry a tag before the type prefix (`EDU-FEAT-001`, `EDU-PC-004`). `make` loads its model next to `model/`; its elements become needs with `platform: true`, which RFQ builds never rule-check (the platform's own build does).

- Reuse is subsetting: `part <'PC-001'> driveMotor :> EDrivePhysical::motor::motor80kW;` or `#Feature action <'FEAT-010'> acc :> PlatformFeatures::cruise;`. The bridge turns it into a `specializes` link; the coverage chain follows it into the platform.
- Variants are native `variation` / `variant` members in the platform; the RFQ part subsets one variant to select it.
- `@Matches { need = "CRS-001"; }` in a feature states that it covers that CRS; `partial = true` says only in part, and then an SR that satisfies the CRS must be satisfied by a component in the feature's chain (it states the gap).
- Reuse status per matched feature is derived from the chain feature → leaf functions → LC → PC, never written: `platform` (all PCs from the platform, no variant), `variant` (all from the platform, at least one a selected variant), `modified` (some platform, some new), `new` (no platform PC), `incomplete` (a leaf function reaches no PC). On a CRS: the worst of its features.
- A CRS with `:scope: commercial` is exempt from `crs-satisfied` and `crs-verified` and must be answered by a CST. `sysml2kit compliance` reports a CRS that is neither matched nor answered, an incomplete chain, and a partial match with no SR stating the gap; the V gate includes these.

## Rules (docs/schemas.json, enforced by `make all` and ubCode)

| Rule id | Layer gate | Rule |
|---|---|---|
| `crs-satisfied` | R | every non-commercial CRS is satisfied by at least one SR |
| `usecase-realizes` | R | every UC realizes at least one CRS |
| `sysreq-satisfies` | R | every SR satisfies at least one CRS |
| `usecase-realized` | F | every UC is realized by at least one feature |
| `feature-realizes` | F | every feature realizes at least one UC |
| `function-allocated` | L | every leaf function is allocated to exactly one component |
| `component-used` | L | every leaf logical component has at least one function allocated |
| `sysreq-satisfied` | L | every SR is satisfied by at least one component |
| `logical-allocated` | P | every leaf logical component is allocated to at least one PC |
| `physical-used` | P | every leaf PC has at least one logical component allocated |
| `systest-verifies` | V | every STC verifies at least one SR |
| `acctest-verifies` | V | every ATC verifies a CRS or UC |
| `sysreq-verified` | V | every SR is verified by at least one STC |
| `usecase-verified` | V | every UC is verified by at least one ATC |
| `crs-verified` | V | every non-commercial CRS is verified by at least one ATC |

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
