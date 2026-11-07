# RFLP structure: customer requirement to acceptance test

Requirements → Functional → Logical, verified on the right side of the V. The physical layer (software, hardware, code) lives in sphinx-needs next to the code, outside the SysML model.

## Artifacts

| Layer | Artifact | Id | Written in | Outgoing links |
|---|---|---|---|---|
| R | Customer requirement | `CRS-nnn` | RST `.. crs::` (or imported from ReqIF/DOORS) | none |
| R | Use case | `UC-nnn` | SysML `use case` | realizes → CRS (`@Realizes`) |
| R | System requirement | `SR-nnn` | SysML `requirement` usage, text in `doc` | satisfies → CRS (`@Satisfies`) |
| F | Function | `F-nnn` | SysML `action` usage tree | realizes → UC (native: `perform` in the use case) |
| L | Logical component | `LC-nnn` | SysML `part` usage tree | satisfies → SR (native `satisfy`) |
| L | Logical interface | `LI-nnn` | SysML `port` on a component | none |
| L | Allocation | none | SysML `allocate <function> to <component>` | F allocated_to → LC |
| V | System test case | `STC-nnn` | SysML `verification` | verifies → SR (native `verify`) |
| V | Acceptance test case | `ATC-nnn` | RST `.. acctest::` | verifies → CRS, UC |
| V | Test result | generated | JUnit XML, `<property name="verifies" value="STC-001"/>` | tests → STC/ATC |
| P | Software requirement | `SWR-nnn` | RST `.. swreq::` | satisfies → SR, realizes → LC (no rules yet) |

Rule of thumb: a link between two model elements is native SysML; a link that leaves the model uses `Trace` metadata, one annotation per target need.

## Model layout

```
model/trace.sysml                         Trace metadata (from the template, do not edit)
model/requirements/use_cases.sysml        package <Sys>UseCases
model/requirements/system_requirements.sysml  package <Sys>Requirements
model/functional/functions.sysml          package <Sys>Functions
model/logical/architecture.sysml          package <Sys>Logical (components, ports, connections, allocations, satisfy)
model/verification/system_tests.sysml     package <Sys>SystemTests
docs/customer/*.rst                       CRS
docs/acceptance/*.rst                     ATC
test-results/*.xml                        JUnit results
```

Prefix package names with the system name; `UseCases`, `Requirements` and similar collide with the standard library.

## Rules (docs/schemas.json, enforced by `make all` and ubCode)

| Rule id | Layer gate | Rule |
|---|---|---|
| `crs-satisfied` | R | every CRS is satisfied by at least one SR |
| `usecase-realizes` | R | every UC realizes at least one CRS |
| `sysreq-satisfies` | R | every SR satisfies at least one CRS |
| `usecase-realized` | F | every UC is realized by at least one function |
| `function-allocated` | L | every leaf function is allocated to exactly one component |
| `component-used` | L | every leaf component has at least one function allocated |
| `sysreq-satisfied` | L | every SR is satisfied by at least one component |
| `systest-verifies` | V | every STC verifies at least one SR |
| `acctest-verifies` | V | every ATC verifies a CRS or UC |
| `sysreq-verified` | V | every SR is verified by at least one STC |
| `usecase-verified` | V | every UC is verified by at least one ATC |
| `crs-verified` | V | every CRS is verified by at least one ATC |

"Leaf" means no child of the same type (a component that owns only ports is a leaf).

## Writing quality (reviewer checks these; the build does not)

- **CRS** are the customer's words. Do not rewrite them; ask when one is ambiguous.
- **UC**: verb phrase from the actor's view (`commute`, `transportOnTrailer`), with subject and actors.
- **SR**: one `shall` per requirement; verifiable (a number with a unit, or an observable yes/no); solution-free (no component names, no technology); no TBD, "etc.", "as appropriate", "user-friendly", "fast".
- **F**: verb + noun, solution-neutral (`storeEnergy`, not `chargeBattery` unless the battery is a given constraint).
- **LC**: technology-neutral role (`energyStore`, not `liIonPack48V`); each leaf has a purpose (an allocated function).
- **STC/ATC**: the `doc` says the procedure and the pass criterion.
