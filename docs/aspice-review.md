# ASPICE traceability review of the kit's meta-model

This review asks one question: can a project built with this kit show the traceability and consistency that Automotive SPICE 4.0 expects in the system (SYS.1 to SYS.5), software (SWE.1 to SWE.6) and hardware (HWE.1 to HWE.4) engineering processes? It is evidence of traceability, not an assessment. A process is rated on far more than links (work product content, reviews, strategies, communication, the people doing it), and none of that is judged here. Process ids and short names are cited; what each process expects is paraphrased, and the VDA text is not reproduced.

The meta-model reviewed is the project template at commit 79c7c3a: need types, links and fields in `plugins/sysml-rflp/templates/project/docs/ubproject.toml`, rules in `docs/schemas.json` (layer gates in `src/sysml2kit/gaps.py`), and the computed findings of `sysml2kit compliance` (`src/sysml2kit/compliance.py`). The method is in `plugins/sysml-rflp/skills/rflp-method/references/structure.md`. Examples are from `examples/seat-switch-platform` (ids tagged `SSW-`) and `examples/seat-switch-rfq`, a customer project that reuses it.

## How the kit shows traceability

Every link is a typed sphinx-needs link with a declared back-link, so each link can be followed both ways in the docs and in the demo explorer. A rule in `schemas.json` checks that a link or a required field exists: at least one, sometimes exactly one, from or into a selected need type. `make all` fails on a violation, and `sysml2kit gaps` lists violations by layer gate. Compliance findings add checks a schema cannot express: whether a customer requirement is answered, verified by an acceptance test or by an implemented customer test requirement (CTR), and whether a partial match or partial satisfaction has a system requirement stating the gap.

What rules cannot show is consistency of content: that a system requirement says what the customer requirement means, or that a test really checks its requirement. The kit leaves that to review, helped by SR text warnings (exactly one `shall`, no vague terms such as TBD). Rules check link existence, not link correctness.

Platform elements reused in a customer project carry `platform: true` and are rule-checked by the platform's own build, not by the customer project.

## System engineering (SYS)

| Process | Kit types and links | Rules and findings | Gap |
| --- | --- | --- | --- |
| SYS.1 Requirements Elicitation | CRS in the customer's own words, with `class` and `scope`; CTR (`applies_to` CRS or PRQ, `purpose`, `method`); CST `answers` CRS or CTR with a compliance value; PRQ in the platform. Example: `CRS-207` is not offered and `CST-001` answers it not-comply. | `crs-class`, `cst-compliance`; findings "not answered" and "not offered, but its statement is not not-comply". | Partial. No agreement status, change history or change request on a requirement beyond git history. |
| SYS.2 System Requirements Analysis | SR and CON `satisfies` CRS or PRQ; UC `realizes` CRS; `partial_satisfies` for a constraint that covers a CRS in part. Example: `SR-104` satisfies `CRS-401` and `CRS-403`; `CON-101` satisfies `CRS-301`. | `crs-satisfied`, `sysreq-satisfies`, `constraint-satisfies`, `usecase-realizes`; partial-satisfaction finding; SR text warnings. | Covered for traceability. No priority, release or verification-criteria attribute on SR; no computed impact of a changed CRS. |
| SYS.3 System Architectural Design | FEAT `realizes` UC and `matches` CRS; F `owned_by` FEAT; F `allocated_to` LC; LC `satisfies` SR; LC `allocated_to` PC; LI `allocated_to` PI; PC `specializes` a platform PC. Example: `SSW-LC-005` satisfies `SSW-SR-004` and is allocated to `SSW-PC-009`, `SSW-PC-020`, `SSW-PC-022` and `SSW-PC-034`. | `usecase-realized`, `feature-realizes`, `function-allocated`, `component-used`, `sysreq-satisfied`, `logical-allocated`, `physical-used`; findings "chain reaches no physical component" and "variation reached without a selected variant". | Partial. No rule that every LI is allocated to a PI or used by a connection. Dynamic behaviour is modelled only as function decomposition; no rule covers it. |
| SYS.4 System Integration and Integration Verification | None specific. STC verifies SR or CON, not an architecture element or interface. | None. | Gap. No integration test type, no link from a test to an LC, PC or interface, no integration sequence. |
| SYS.5 System Verification | STC `verifies` SR or CON and `implements` CTR; ATC `verifies` CRS or UC and `implements` CTR; test results (`tests`) from JUnit. Example: `STC-104` verifies `CON-105`, `CON-106`, `CON-123` and implements `CTR-001`. | `sysreq-verified`, `constraint-verified`, `systest-verifies`, `systest-implements`, `ctr-implemented`, `usecase-verified`, `acctest-verifies`, `acctest-implements`; finding "not verified (no acceptance test, no implemented CTR applying to it)" for every technical CRS and PRQ; finding "not implemented" for a CTR. | Partial. No rule that a test has a result, or that the result passed. Selection of verification measures (regression scope, criteria per release) is not modelled; CTR `method` is the only method attribute. |

Validation sits outside SYS.5 in ASPICE 4.0 (VAL.1). The kit separates it: a CTR has `purpose: validation`, and an ATC implements it. `CTR-011` (in-vehicle validation) is implemented by `ATC-105`.

## Software engineering (SWE)

Software architecture and design are physical components in the model. The firmware (`SSW-PC-016`) is a `#Software` PC; it owns SW components such as `SSW-PC-026` (input processing), which own SW units such as `SSW-PC-029` (debouncer). SW interfaces are `#Software` ports (`SSW-PI-004`). Software requirements (`swreq`, SWR) are Markdown needs in the platform's `docs/software/`.

| Process | Kit types and links | Rules and findings | Gap |
| --- | --- | --- | --- |
| SWE.1 Software Requirements Analysis | SWR `satisfies` SR and is `allocated_to` the SW component or unit implementing it. Example: `SSW-SWR-004` satisfies `SSW-SR-001` and `SSW-SR-002`. | None. | Partial, accepted open gap. No rule that every SWR satisfies an SR, or that every SR allocated to software is refined by an SWR. The SWR has no class or verification attribute. A customer project does not load the platform's SWRs, so they appear only in the platform build, and no rule checks them there either. |
| SWE.2 Software Architectural Design | SW component (`#Software` PC owned by the firmware); LC `allocated_to` SW component; SW ports; SWR `allocated_to` SW component. Example: `SSW-LC-005` is allocated to `SSW-PC-034` (LIN stack). | `swcomponent-used`, `software-used`. | Partial. No rule that every SWR is allocated. No dynamic behaviour, timing or resource budget on SW components. SW interfaces are not traced to SWRs. |
| SWE.3 Software Detailed Design and Unit Construction | SW unit (`#Software` PC owned by a SW component); SWR `allocated_to` a unit. Example: `SSW-SWR-004` is allocated to `SSW-PC-029`. | None; no allocation rule applies to a SW unit by design. | Gap for detailed design: no unit interface, algorithm or behaviour as a need. Code is not traced; at most the JUnit classname of a unit test (`firmware.inputProcessing.debouncer`) mirrors the unit's path in the model. |
| SWE.4 Software Unit Verification | Test results from unit tests, linked to the SWR (`tests`) through the JUnit property `verifies`. Example: the debouncer test result tests `SSW-SWR-004`; all 14 platform SWRs have a passing result. | None. | Partial. No rule that every SWR or unit has a result. A result reaches the unit only through the SWR's allocation. No static verification evidence and no unit verification criteria. |
| SWE.5 Software Component Verification and Integration Verification | None specific. Units are wired with `connect` and `bind` in the model. | None. | Gap. No test type or link for a SW component or a SW interface, no integration sequence. |
| SWE.6 Software Verification | The same JUnit results against SWR. | None. | Gap in practice. There is no separate software test level; unit test results double as software verification evidence. |

## Hardware engineering (HWE)

Electrical design exists as `#Electrical` PCs: the PCB (`SSW-PC-007`) owns, among others, the microcontroller, voltage regulator, reverse polarity protection, LIN ESD protection and LED drivers (`SSW-PC-017` to `SSW-PC-021`), and the vehicle connector (`SSW-PC-022`) has one physical interface per pin (`SSW-PI-005` to `SSW-PI-007`, supply, ground and LIN). There is no hardware requirement need type.

| Process | Kit types and links | Rules and findings | Gap |
| --- | --- | --- | --- |
| HWE.1 Hardware Requirements Analysis | None. A constraint owned by an electrical PC is the closest stand-in: `CON-114` limits the comfort keys of `PC-102` and satisfies `CRS-203`. | None. | Gap, accepted and open. No hardware requirement type, so nothing refines an SR for hardware. |
| HWE.2 Hardware Design | Electrical PC and PI with ownership; LC `allocated_to` PC; each electrical PC's `doc` names its BOM item, and the connector's also its pin assignment. | `physical-used` (every leaf mechanical or electrical PC has an LC allocated). | Partial. No trace from a hardware element to a hardware requirement, because there is none; no rule on electrical interfaces; schematic and layout are outside the model. |
| HWE.3 Verification against Hardware Design | None. | None. | Gap. No hardware test type and no link from a test to a PC or PI. |
| HWE.4 Verification against Hardware Requirements | STC `verifies` a CON owned by an electrical PC. Example: `STC-112` verifies `CON-114`. | `constraint-verified`. | Gap. Without hardware requirements there is nothing to verify against at this level. |

## Gaps

The software and hardware requirement levels are thin. The platform has SWRs but no rules on them, a customer project does not see them, and there is no hardware requirement type at all. The owner has accepted this for now and intends to close it later. It is an open gap, not a design decision. Closing it means a `hwreq` type, rules that every SWR and hardware requirement satisfies an SR and is allocated, and rules that each is verified.

Verification below the system has no test types. System tests verify system requirements and acceptance tests verify customer requirements, but nothing verifies an architecture element or an interface (SYS.4, SWE.5, HWE.3). Unit test results are attached to SWRs, which covers SWE.4 in part and leaves SWE.6 without its own level.

No rule looks at test outcomes. A failed or missing result breaks no rule. ASPICE expects verification results to be recorded and traced, and the kit records and traces them, but it does not check them.

Release and baseline are not modelled. There is no release attribute on any need and no baseline beyond git commits and tags, so release scope and the selection of verification measures per release cannot be shown from the meta-model.

Dynamic behaviour, timing and resource budgets are not traced at any level.

Management, support and supply processes (MAN, SUP, ACQ, SPL) are out of reach of a meta-model of engineering work products. The kit can supply evidence to configuration management (everything is text under git), but nothing more.

## Recommendation: an ASPICE overlay on the meta-model view

The demo's meta-model view (`demo/explorer/views.py`, `metamodel`) already draws every need type by layer, every link between types with instance counts, the rules that act on each type and link, and how many instances come from the platform versus the project. That is most of what an ASPICE overlay needs. The overlay should add three things.

First, process ids on types and links, as a small mapping kept next to the template, for example SR and its `satisfies` link to CRS tagged SYS.2, LC `allocated_to` PC tagged SYS.3, STC `verifies` SR tagged SYS.5. Keeping the mapping out of `ubproject.toml` keeps the standard's ids out of the meta-model itself.

Second, coverage per expectation, computed from what the build already produces: for each process, the rules mapped to it and whether they pass (`schema_violations.json`), plus the compliance findings mapped to it. Both are build outputs of one project: `make` writes `build/needs/schema_violations.json`, and `sysml2kit compliance` prints its findings while writing `docs/_generated/compliance.md` (they are not saved, so the overlay would recompute them from `build/needs/needs.json`). The customer project's view would get the platform's results by running the platform build in its `platform/` checkout and reading that build's outputs, or from outputs the platform publishes with each release. A process row would then read, for example, "SYS.5: 8 rules, 0 violations; 0 not-verified findings". A process with no mapped rule shows as uncovered, which makes the gaps above visible instead of silent.

Third, keep the platform and project split the view already has. A customer project reuses platform elements that the platform's build checked, so the overlay should show which evidence comes from which build, not merge them.

The overlay's limits should be on the screen, not only in this document. It shows that links exist and rules pass; it does not show that content is right, that reviews happened, or that a process is performed. A process with full coverage is not a rated process. Its value is in letting a team see where the trace is missing before an assessor does.
