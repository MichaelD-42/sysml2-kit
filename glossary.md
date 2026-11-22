# Glossary

Terms used in this repository, the plugin and the generated docs. Which layer owns which artifact, and the rules between them, are in [`structure.md`](plugins/sysml-rflp/skills/rflp-method/references/structure.md).

## Method

**RFLP**: Requirements → Functional → Logical → Physical. The layers a system is described in, from what the customer wants down to what gets built. This kit models all four in SysML; software components also link to code and tests in sphinx-needs.

**RFQ** (request for quotation): a customer's call for an offer. The `rfq` skill builds the architecture that answers it, reusing the supplier's platform.

**Platform**: the supplier's own project of reusable features, components and variants, with the same layout as an RFQ project. An RFQ project pulls it in at `platform/` (git submodule). Its ids carry a tag (`WSW-PC-004`); its needs have `platform: true` and are checked by the platform's own build, not the RFQ's.

**V model**: the left side of the V goes down through the RFLP layers; the right side goes up through tests that verify each layer. Here: system tests verify system requirements, acceptance tests verify customer requirements and use cases.

**Layer gate**: the point in the `rflp` workflow where one layer is finished, its rules pass, and the user approves before the next layer starts.

**Traceability**: being able to follow every customer requirement through use cases, system requirements, functions and components to the tests and results that verify it, and back.

**Leaf**: a function or component with no child of the same type. Allocation rules apply to leaves only. A component that owns only ports is still a leaf; one that subsets a composite component inherits its children and is not. SW units are leaves but take no allocation; SW components do (see SW component).

## Definitions

- A use case describes what you can do with the system.
- A feature is a capability/property of the system to fulfil a use case, someone finds valuable (usually a noun).
- A function is how a feature is implemented (needs a verb).
- A logical component is an abstract, solution-free component of the system.
- A physical component is a physical component of the system that is part of the solution.

SW architecture and design are physical components: SW components and SW units.

## Artifacts and ids

**CRS** (customer requirement, `CRS-nnn`): the customer's own words, written in Markdown (MyST). Not part of the SysML model. `:scope: commercial` (terms, delivery, warranty) or `:scope: not-offered` (a technical requirement the supplier does not meet at all) exempts it from `crs-satisfied` and from the not-verified compliance finding and requires a CST, `not-comply` for `not-offered`. Adding `:scope:` and `:class:` (agreed with the user) are the only edits the supplier makes to a CRS; the text and every CTR stay untouched.

**Requirement class**: `:class:` on every CRS and PRQ: `functional`, `non-functional`, `constraint` or `information`. Functional needs a matching feature and an SR or constraint; non-functional and constraint need a `CON-` constraint; information needs a class but nothing to satisfy, match, answer or verify it.

**CON** (constraint, `CON-nnn`): a SysML `constraint` usage over a physical part's attribute that satisfies a CRS with a plain value, owned by the part it limits (an assembly for the whole product). The bridge evaluates it against the values the part states or inherits and fails when it does not hold. Verified by a system test (`@Verifies`).

**CTR** (customer test requirement, `CTR-nnn`): the customer's own test, written in Markdown and captured as written; `applies_to` the CRS it tests. The supplier's STC or ATC implements it (`@Implements` / `:implements:`). It counts toward verifying the CRSs it applies to, whatever its scope.

**PRQ** (platform requirement, `PRQ-nnn`): what the platform offers every program, written in Markdown in the platform project, where it plays the role CRS plays in an RFQ project.

**CST** (compliance statement, `CST-nnn`): the supplier's answer to a CRS that no architecture element can meet, or meets only in part (then it states the gap), in Markdown, with `answers` and `compliance` (comply, partial, not-comply).

**UC** (use case, `UC-nnn`): what an actor does with the system, as a SysML `use case` with a subject and actors. Its title is "The <actor> wants to <goal>" (e.g. "The occupant wants to open or close a window"), written as the doc of its `objective`; the model name (`moveWindow`) stays the identifier.

**SR** (system requirement, `SR-nnn`): one verifiable, solution-free `shall`, as a SysML `requirement`.

**FEAT** (feature, `FEAT-nnn`): what the product offers, as a SysML `#Feature action` with a noun name. Performed by use cases; owns functions.

**F** (function, `F-nnn`): what the system does, as a SysML `action` nested in a feature or another function (sub-function).

**LC** (logical component, `LC-nnn`): a technology-neutral part of the system, as a tree of SysML `part` usages.

**LI** (logical interface, `LI-nnn`): a SysML `port` on a component.

**PC** (physical component, `PC-nnn`): a part that is built or bought, as a SysML `part` with one domain keyword.

**Assembly** (`PC-nnn`): the product as built, across domains, as a SysML `#Assembly part` with no domain keyword. It owns or references its PCs and carries the product's rated values and constraints. A configuration of the product (one per door) is an assembly that subsets the program's assembly and selects its variants.

**SW component** (`PC-nnn`): a `#Software part` owned by the firmware PC; the SW architecture. Its interfaces are `#Software` ports and connections. Logical components are allocated to it.

**SW unit** (`PC-nnn`): a `#Software part` owned by its SW component; the SW design. Software requirements are allocated to it, unit tests verify those.

**PI** (physical interface, `PI-nnn`): a SysML `port` on a PC with the same domain keywords; a logical interface is allocated to it.

**Domain**: the engineering discipline of a PC or PI: `#Mechanical` (ME), `#Electrical` (EE) or `#Software` (SW). A part or port without one (and without `#Assembly`) is logical.

**STC** (system test case, `STC-nnn`): a SysML `verification` that verifies system requirements.

**ATC** (acceptance test case, `ATC-nnn`): an RST test that verifies customer requirements or use cases.

**Test result** (`testresult_…`): a need generated from JUnit XML by ub-test-reports, linked to its STC, ATC or SWR.

**SWR** (software requirement, `SWR-nnn`): a requirement on software, written in Markdown or RST (`swreq`). It is allocated to the SW component or unit implementing it (`:allocated_to:`) and satisfies an SR; unit test results verify it. No rules yet.

## Links

**satisfies**: a requirement or component fulfils a requirement one layer up (SR → CRS, LC → SR).

**realizes**: a use case or feature implements the layer above (UC → CRS, FEAT → UC).

**matches**: a feature covers a customer requirement (FEAT → CRS), stated with `@Matches`; `partial = true` means only in part.

**specializes**: an element reuses a platform element by subsetting (`:>`), such as a PC subsetting a platform PC or a selected variant. Coverage chains follow it into the platform.

**answers**: a compliance statement responds to a CRS (CST → CRS).

**verifies**: a test case checks a requirement (STC → SR, ATC → CRS or UC).

**allocated_to**: a function is carried out by a component (F → LC), a logical component by a physical one (LC → PC, for software LC → SW component), a logical interface by a physical one (LI → PI), a software requirement by the SW component or unit implementing it (SWR → PC).

**owned_by**: the nearest owning element that is also a need; generated by the bridge.

**tests**: a test result belongs to a test case or a software requirement.

## SysML v2

**Definition / usage**: a definition (`part def Engine`) is a type; a usage (`part engine : Engine`) is an occurrence of it in a structure. Traced elements are modelled as usages.

**Short name**: the id in angle brackets, `requirement <'SR-001'> range;`. Every element with a declared short name becomes a need with that id. `declaredShortName` is the one written in the model; `shortName` is also set on implicit features that inherit it, so the bridge ignores it.

**Qualified name**: the full path of an element, `VehicleRequirements::range`.

**`satisfy`, `verify`, `allocate`, `perform`**: native SysML relations the bridge turns into `satisfies`, `verifies`, `allocated_to` and `realizes` links.

**Subject / actor**: the system a use case is about, and who takes part in it. One use case diagram is drawn per subject.

**Trace metadata**: `@Realizes`, `@Satisfies`, `@Verifies`, `@Matches` from `model/trace.sysml`. Links from a model element to a need written outside the model, such as a CRS: `@Realizes { need = "CRS-001"; }`.

**Keyword metadata**: `#Feature`, `#Mechanical`, `#Electrical`, `#Software`, `#Assembly`, also from `model/trace.sysml`; they set what kind of need an `action`, `part` or `port` becomes.

**Variation / variant**: SysML v2 way to declare alternatives: a `variation part` with `variant part` members. An RFQ part selects one by subsetting it; the platform's own allocations to its variants only offer them. A chain that reaches the variation without a selection makes the feature `incomplete`.

**Interchange JSON**: the output of `sysml export`, a flat array of elements with `@id`, `@type` and every metamodel property.

**OMG corpus**: the SysML-v2-Release repository from OMG, the standard's own example models. Used here as the conformance test for the toolchain.

## Tools

**`sysml`**: the sysmlv2-cli command line tool, built from the fork at the tag `SYSML_TAG` in the Makefile. Checks, exports and draws the model and runs the MCP server.

**MCP server**: `sysml mcp`, which lets Claude query the model and the SysML standard library (`check`, `find`, `relations`, `outline`, and others) instead of guessing.

**Bridge**: `sysml2kit needs`, which turns interchange JSON into sphinx-needs needs.

**sphinx-needs**: the Sphinx extension that holds needs, their links and the rules. The docs build is the traceability check.

**Need**: one tracked item in sphinx-needs, with an id, a type, fields and links.

**needimport**: the sphinx-needs directive that loads a generated needs JSON file into the docs.

**Schema rules**: the RFLP rules in `docs/schemas.json`, such as `sysreq-verified`. `sphinx-build -W` fails when one is broken.

**Reuse status**: derived per matched feature from its chain feature → functions → LC → PC, never written: `platform`, `variant`, `modified`, `new`, or `incomplete` (a leaf function reaches no PC). A CRS shows the worst of its features.

**Compliance table**: per CRS the matched features, reuse status, partial flag, compliance statements and domains; generated by `sysml2kit compliance`, which also reports unanswered CRS, partial ones without a partial statement, and system requirements satisfied outside their matching features' chains.

**Gap**: one broken schema rule on one need. `sysml2kit gaps build/needs --layer L` lists the gaps of layer L and earlier, with the file and line to fix.

**ubproject.toml**: need types, link types and fields, read by both Sphinx and ubCode.

**ubCode**: the editor extension for sphinx-needs projects that reads the same configuration and rules.
