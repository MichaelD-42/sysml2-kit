# RFLP structure: customer requirement to acceptance test

Requirements → Functional → Logical → Physical, verified on the right side of the V. R, F, L and P are in the SysML model (customer requirements, statements and software requirements are Markdown needs); software PCs also link to code and tests in sphinx-needs.

## Definitions

- A use case describes what you can do with the system.
- A feature is a capability/property of the system to fulfil a use case, someone finds valuable (usually a noun).
- A function is how a feature is implemented (needs a verb).
- A logical component is an abstract, solution-free component of the system.
- A physical component is a physical component of the system that is part of the solution. The product as built, across domains, is a physical assembly.

SW architecture and design are physical components: SW components and SW units.

## Artifacts

| Layer | Artifact | Id | Written in | Outgoing links |
|---|---|---|---|---|
| R | Customer requirement | `CRS-nnn` | Markdown (MyST) `crs` directive, `docs/customer/`; `:class:` functional, non-functional, constraint or information | none |
| R | Platform requirement | `PRQ-nnn` | Markdown `prq` directive, in the platform project; `:class:` as for CRS | none |
| R | Compliance statement | `CST-nnn` | Markdown `cst` directive, in the RFQ project; required for a commercial, not-offered or partially met CRS | answers → CRS; `compliance`: comply, partial, not-comply |
| R | Use case | `UC-nnn` | SysML `use case`; its `objective` doc is the need title | realizes → CRS (`@Realizes`) |
| R | System requirement | `SR-nnn` | SysML `requirement` usage, text in `doc` | satisfies → CRS (`@Satisfies`) |
| R | Constraint | `CON-nnn` | SysML `constraint` usage over a physical part's attribute, owned by the physical part it limits (an assembly for the product as a whole); evaluated by the bridge | satisfies → CRS (`@Satisfies`; `partial = true` for a partial one) |
| F | Feature | `FEAT-nnn` | SysML `#Feature action`, noun name | realizes → UC (native: `perform` in the use case); matches → CRS (`@Matches`) |
| F | Function / sub-function | `F-nnn` | SysML `action` nested in a feature or function | owned_by → FEAT/F |
| L | Logical component | `LC-nnn` | SysML `part` usage tree | satisfies → SR (native `satisfy`) |
| L | Logical interface | `LI-nnn` | SysML `port` on a logical component | none |
| L | Allocation | none | SysML `allocate <function> to <component>` | F allocated_to → LC |
| P | Physical component | `PC-nnn` | SysML `#Mechanical`, `#Electrical` or `#Software part` | LC allocated_to → PC (`allocate`); specializes → platform PC (`:>`) |
| P | Assembly | `PC-nnn` | SysML `#Assembly part`, no domain: the product as built, owning or referencing its PCs | LC allocated_to → assembly (`allocate`, optional); specializes → platform assembly (`:>`) |
| P | Physical interface | `PI-nnn` | SysML `port` on a PC, same domain keywords | LI allocated_to → PI (`allocate`) |
| P | SW component | `PC-nnn` | SysML `#Software part` owned by the firmware PC | LC allocated_to → SW component (`allocate`); owned_by → firmware |
| P | SW unit | `PC-nnn` | SysML `#Software part` owned by its SW component | owned_by → SW component |
| P | Software requirement | `SWR-nnn` | Markdown or RST `swreq`, `docs/software/` | satisfies → SR, allocated_to → the SW component or unit implementing it (no rules) |
| V | Customer test requirement | `CTR-nnn` | Markdown `ctr` directive, `docs/customer/`; `:purpose:` verification or validation, `:method:` test, analysis, inspection or demonstration | `applies_to` → CRS/PRQ (`:applies_to:`) |
| V | System test case | `STC-nnn` | SysML `verification` | verifies → SR (native `verify`) or constraint (`@Verifies`); implements → CTR (`@Implements`) |
| V | Acceptance test case | `ATC-nnn` | Markdown or RST `acctest` | verifies → CRS, UC; implements → CTR (`:implements:`) |
| V | Test result | generated | JUnit XML, `<property name="verifies" value="STC-001"/>` | tests → STC/ATC/SWR |

Keywords `#Feature`, `#Mechanical`, `#Electrical`, `#Software`, `#Assembly` and the metadata `@Matches`, `@Satisfies`, `@Verifies`, `@Implements` are in `model/trace.sysml` (package `Trace`). A part or port without a domain keyword or `#Assembly` is logical. The id prefix must agree with the kind (`PC-` on a domain part or an assembly, `FEAT-` on a `#Feature` action); the bridge errors otherwise. Exactly one domain keyword per element, none on an assembly.

The layers depend downwards only: a logical component is never typed by a physical definition, and rated values and the constraints on them belong to physical parts.

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

## Use case titles

A use case's need title is "The <actor> wants to <goal>", written as the doc of its `objective`; the model name stays the short identifier:

```
use case <'UC-101'> moveWindow {
    objective { doc /* The occupant wants to open or close a window */ }
    ...
}
```

The bridge takes the title from the objective's doc, otherwise from the name.

## Software architecture and design

Software is physical: the firmware is a `#Software part`, it owns its SW components (`#Software part`), and each SW component owns its SW units (`#Software part`). Every one of them carries its own `#Software` keyword and a `PC-` id; a nested part without a keyword is logical and the bridge rejects its `PC-` id. A SW component's interfaces are `#Software port`s (`PI-` ids where they are traced), wired with `connect` between units and `bind` from the component's port to the unit behind it.

- Logical components are allocated to SW components (`allocate <LC> to <firmware>.<component>;`), not to units. Rule `swcomponent-used` requires one on every SW component; a SW unit needs none, since its trace runs through the component that owns it. A firmware not yet broken into SW components takes the LC itself (`software-used`). Keep the firmware top-level: a `#Software` PC owned by another PC counts as a SW component or unit.
- Each software requirement (`swreq`, `SWR-nnn`, in `docs/software/`) is allocated to the SW component or unit that implements it (`:allocated_to:`) and `:satisfies:` the SR it refines.
- SW units are verified by SWR tests: unit test results in `test-results/*.xml` carry `<property name="verifies" value="SWR-nnn"/>` and become test results linked to the SWR (`tests`).

## Requirement classes, constraints, customer test requirements

Classify every CRS and PRQ (`:class:`; rule `crs-class`). The class decides what the supplier owes:

- `functional`: a feature matches it (`@Matches`) and an SR or a constraint satisfies it.
- `non-functional` and `constraint`: a `CON-` constraint in the model satisfies it. A plain value (a mass, a speed, a voltage) is a constraint over a physical part's attribute, never a bare attribute. Write a textual SR only for what the model cannot express.
- `information`: no obligation. It still needs a class (`crs-class`), but nothing needs to satisfy, match, answer or verify it.

A constraint that satisfies a CRS only in part (`@Satisfies { need = "CRS-nnn"; partial = true; }`) states what is met; a CST with `:compliance: partial` answering the CRS states the gap to the customer.

The bridge evaluates every constraint against the attribute values its owner states or inherits (through `:>`, `:`, `:>>`): one that does not hold fails the bridge with the values it used (`CON-112: does not hold: mass <= 40 [g] (mass = 48 [g])`), so a platform rating that no longer meets an RFQ's limit breaks the RFQ build. A constraint over a value nobody states, or over syntax beyond `and`/`or`/`not`, comparisons, numbers with a unit in brackets, strings and feature chains, is reported as `not evaluated` (a warning). Values are compared only in the same unit.

CTRs are the customer's own test requirements, captured as written (`ctr` directive, `:applies_to:` the CRS or PRQ they test). The supplier does not rewrite them: its tests implement them, with `@Implements { need = "CTR-nnn"; }` in a system test or `:implements:` in an acceptance test. A CTR counts toward verifying every CRS it `applies_to`, whatever its scope. A system test verifies an SR or a constraint (`@Verifies`), or implements a CTR; an acceptance test verifies a CRS or UC, or implements a CTR. A CTR with `:scope: commercial` or `not-offered` needs a CST answer instead of an implementing test, and still needs that CST when a test implements it.

## Platform, variants, matching

The platform is the supplier's own project with this same layout (its PRQ play the role of CRS), in `<project>/platform/` as a git submodule (`git submodule add <platform repo> platform`), or a checkout elsewhere that the Makefile's `PLATFORM := <path>` names, as the repo examples do with their sibling platform. Not a symlink: Git for Windows checks one out as a text file. Its ids carry a tag before the type prefix (`WSW-FEAT-001`, `WSW-PC-004`). `make` loads its model next to `model/`; its elements become needs with `platform: true`, which RFQ builds never rule-check (the platform's own build does).

- Reuse is subsetting: `#Electrical part <'PC-101'> driverKeyModule :> WindowSwitchPhysical::keyModule::fourKey;` or `#Feature action <'FEAT-101'> windowKeys :> WindowSwitchFeatures::windowControl;`. The bridge turns it into a `specializes` link; the coverage chain follows it into the platform.
- Variants are native `variation` / `variant` members in the platform; the RFQ part subsets one variant to select it. The platform's own allocations to its variants offer them, they do not select them: in an RFQ build a platform variant counts only when a project part subsets it or a project component is allocated to it. A chain that reaches a variation without such a selection reaches no PC there: the feature is `incomplete`.
- Several configurations of the product (one per door) are physical: an `#Assembly` per configuration that subsets the program's assembly and owns its variant selections (`#Electrical part <'PC-101'> driverKeyModule :>> keyModule :> WindowSwitchPhysical::keyModule::fourKey`, redefining the inherited slot), with what holds between them as constraints on an assembly that owns them all. They are not extra logical components or functions; a component that subsets a composite inherits its children and is not a leaf.
- `@Matches { need = "CRS-001"; }` in a feature states that it covers that CRS. Every SR that satisfies a matched CRS must be satisfied by a component in the chain of one of its matching features, so the function path and the requirement path meet. `partial = true` says only in part: then an SR that satisfies the CRS must be satisfied by a component in the feature's chain (it states what is met), and a `partial` CST answering the CRS states the gap.
- Reuse status per matched feature is derived from the chain feature → leaf functions → LC → PC, never written: `platform` (all PCs from the platform, no variant), `variant` (all from the platform, at least one a selected variant), `modified` (some platform, some new), `new` (no platform PC), `incomplete` (a leaf function reaches no PC). On a CRS: the worst of its features.
- A CRS with `:scope: commercial` (terms, delivery, warranty) or `:scope: not-offered` (a technical CRS the supplier does not meet at all) is exempt from `crs-satisfied` and from the not-verified finding and must be answered by a CST; for `not-offered` the CST is `not-comply`. A technical CRS met in part keeps empty scope: a feature or constraint covers it partially, an SR or the constraint states what is met, and a CST `partial` states the gap. Adding `:scope:` and `:class:` (agreed with the user) are the only permitted edits to a customer's CRS; its text and every CTR stay untouched. `sysml2kit compliance` runs at the V gate, fails the build, and reports (exact texts): `<CRS>: not answered` (no matching feature, no CST, and for non-functional or constraint no constraint and no system requirement); `<CRS>: not offered, but its statement is not not-comply`; `<CRS>: matched, but its chain reaches no physical component`; `<CRS>: variation <V> reached without a selected variant`; `<CRS>: partial match without a system requirement stating what is met`; `<CRS>: partial, but no partial compliance statement answers it`; `<CRS>: system requirement <SR> is satisfied outside the chain of its matching features`; `<CRS>: not verified (no acceptance test, no implemented CTR applying to it)` (class functional, non-functional or constraint, empty scope; applies to PRQ too); `<CTR>: not implemented`; and for a CTR with scope, `<CTR>: not answered` or `not offered, but its statement is not not-comply` even when a test implements it.

## Rules (docs/schemas.json, enforced by `make all` and ubCode)

| Rule id | Layer gate | Rule |
|---|---|---|
| `crs-class` | R | every CRS and PRQ has a class |
| `crs-satisfied` | R | every CRS of class functional, non-functional or constraint with empty scope is satisfied by at least one SR or constraint |
| `constraint-satisfies` | R | every constraint satisfies at least one CRS or PRQ |
| `usecase-realizes` | R | every UC realizes at least one CRS |
| `sysreq-satisfies` | R | every SR satisfies at least one CRS |
| `cst-compliance` | R | every CST has a compliance value (comply, partial or not-comply) |
| `usecase-realized` | F | every UC is realized by at least one feature |
| `feature-realizes` | F | every feature realizes at least one UC |
| `function-allocated` | L | every leaf function is allocated to exactly one component |
| `component-used` | L | every leaf logical component has at least one function allocated |
| `sysreq-satisfied` | L | every SR is satisfied by at least one component |
| `logical-allocated` | P | every leaf logical component is allocated to at least one PC |
| `physical-used` | P | every leaf mechanical or electrical PC has at least one logical component allocated |
| `swcomponent-used` | P | every SW component (a `#Software` PC owned by a PC and owning SW units) has at least one logical component allocated |
| `software-used` | P | every top-level `#Software` PC without SW components has at least one logical component allocated |
| `systest-verifies` | V | every STC that implements nothing verifies at least one SR or constraint |
| `systest-implements` | V | every STC with `implements` links implements at least one CTR |
| `constraint-verified` | V | every constraint is verified by at least one STC |
| `ctr-implemented` | V | every CTR with empty scope is implemented by at least one STC or ATC |
| `acctest-verifies` | V | every ATC that implements nothing verifies a CRS or UC |
| `acctest-implements` | V | every ATC with `implements` links implements at least one CTR |
| `sysreq-verified` | V | every SR is verified by at least one STC |
| `usecase-verified` | V | every UC is verified by at least one ATC |

CRS and PRQ verification is not a schema rule: it is the computed compliance finding `<CRS>: not verified (no acceptance test, no implemented CTR applying to it)`, run by `sysml2kit compliance` at the V gate. `sysml2kit gaps` does not show it.

In an RFQ build the model rules (all except `crs-class`, `crs-satisfied`, `cst-compliance`, `ctr-implemented`, `acctest-verifies` and `acctest-implements`, which select Markdown needs) select only needs with `platform: false`. In the platform project `prq` needs take CRS's place in these rules.

"Leaf" means no child of the same type, owned or inherited by subsetting (a component that owns only ports is a leaf; one that subsets a composite is not). A SW unit is a leaf `#Software` PC owned by another PC; no allocation rule applies to it.

## Writing quality (the reviewer checks these; `sysml2kit` warns on an SR without exactly one `shall` or with TBD, etc., as appropriate, user-friendly, fast)

- **CRS** are the customer's words. Do not rewrite them; ask when one is ambiguous.
- **UC**: name a verb phrase from the actor's view (`commute`, `transportOnTrailer`), with subject and actors; title "The <actor> wants to <goal>" in the `objective` doc.
- **SR**: one `shall` per requirement; verifiable (a number with a unit, or an observable yes/no); solution-free (no component names, no technology); no TBD, "etc.", "as appropriate", "user-friendly", "fast".
- **FEAT**: a noun for what the product offers (`windowControl`, `nightIllumination`), not a verb phrase.
- **F**: verb + noun, solution-neutral (`storeEnergy`, not `chargeBattery` unless the battery is a given constraint); nest sub-functions under the function they refine.
- **LC**: technology-neutral role (`energyStore`, not `liIonPack48V`); each leaf has a purpose (an allocated function).
- **PC/PI**: one domain keyword, or `#Assembly` for the product as built; the `doc` names the BOM item, drawing or code module; a platform part is reused with `:>` before a new one is created. SW components and units say in their `doc` which they are (`SW component: ...`, `SW unit: ...`).
- **STC/ATC**: the `doc` says the procedure and the pass criterion.
