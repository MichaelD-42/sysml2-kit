# RFQ-owned components, realized by the platform

## Why

The supplier quotes a rough solution, a classic BOM, built from the logical breakdown the RFQ analysis
derives and the reuse degree of each block. Today an RFQ inherits that breakdown from the platform:
`LC-100 OEM_WindowSwitch :> ACME_WindowSwitch`, and every RFQ feature subsets a platform feature and
inherits its functions. The quote then describes the platform, not the RFQ, and a block cannot be new
or partly reused.

## Goal

The RFQ owns its F and L layers. The platform enters at P: each RFQ logical component is realized by
physical parts **fully**, **partly**, or **not at all** (new for this RFQ). The degree is derived from
the model and never written by hand. The one judgment the model cannot show, that a platform part has
to change (a new tool, another material), is written as a `#Modified` keyword on that part.

Non-goals: supplier use cases and requirements from the platform (the next project; it first needs a
decision on how platform PRQs get into an RFQ build, which today loads only the platform's model);
UML activities; any change to what the example RFQ offers the customer (compliance answers stay as
they are).

Anti-goal: a degree someone types in and nobody checks.

## Approaches

- **P-layer allocation (chosen).** RFQ components are allocated to physical parts as today: a platform
  part used as it is, an RFQ part that subsets a platform part or selects a variant, or a new RFQ part.
  The degree follows from those parts. It reuses the allocation and subsetting the method already has.
- **RFQ component subsets a platform component.** Rejected: it inherits the platform's functions and
  their allocations to platform components, which is what this change removes, and it states reuse at
  L although the platform's solution is its physical parts.
- **Degree stated per component by the engineer**, checked against the parts. Rejected by the user in
  favour of derivation plus `#Modified`: a stated degree goes stale.

## Method

### F and L belong to the RFQ

- RFQ features own their functions (`F-1xx`) and do not subset platform features. RFQ logical
  components (`LC-1xx`) and interfaces (`LI-1xx`) are the RFQ's own; they do not subset platform
  components.
- The bridge rejects a project (non-platform) feature, function, logical component or logical interface
  that specializes a platform need, with
  `<id>: specializes the platform's <platform id>; an RFQ derives its own <type>s and the platform realizes them at P`.
- Use cases, requirements, constraints and tests are unaffected. Physical parts still subset platform
  parts and variants exactly as today.

### `#Modified`

- New keyword `metadata def Modified;` in `Trace`, written on a physical part: `#Electrical #Modified part`.
  It combines with one domain keyword or `#Assembly`.
- The bridge sets `modified: true` on the need. It rejects `#Modified` on anything but a physical part,
  and on a physical part that does not specialize a platform part (directly or through its chain), with
  `<id>: #Modified needs a platform part to modify; a part of its own is new`.
- Its `doc` says what changes against the platform part; the `rflp-reviewer` checks that.

### Degree

Values: `full`, `partial`, `new`, `incomplete`. They replace `platform`, `variant`, `modified`, `new`,
`incomplete` everywhere the reuse status appears (needs field `reuse`, compliance table). Worst first:
`incomplete`, `new`, `partial`, `full`.

- **A physical part**: `full` if its specialization chain reaches a platform part and it is not
  `#Modified`; `partial` if it is `#Modified`; `new` if its chain reaches no platform part. An assembly
  without a domain combines its own with its parts' as `part_reuse` does today (all `full` → `full`, all
  `new` → `new`, else `partial`).
- **A leaf logical component**: combines the degrees of the physical parts it is allocated to, the same
  way (all `full` → `full`, all `new` → `new`, else `partial`). An allocation to an assembly reaches its
  parts, and the variant rules stay: a variation reached without a selected variant reaches no part
  there. A component reaching no part is `incomplete`.
- **A composite logical component**: `incomplete` if a leaf descendant is; otherwise its leaves combined
  the same way (a `full` and a `new` leaf make it `partial`).
- **A feature**: the parts its leaf functions reach, combined the same way; `incomplete` if a leaf
  function reaches no part.
- **A CRS** in the compliance table: the worst of its features and of the parts owning its constraints,
  as today.

The bridge writes the degree into `reuse` on feature and logical-component needs.

### Output

`sysml2kit compliance` writes a second table into `compliance.md`, after the CRS table:

| Component | Title | Degree | Physical parts |
|---|---|---|---|
| LC-106 | enclosure | partial | PC-112 keyCaps (modified WSW-PC-002), PC-113 partNumberLabel (new), WSW-PC-001, WSW-PC-003 |

One row per project logical component, composites included, in id order. A part is listed by its id and
name, with `(modified <platform id>)`, `(new)`, or, for a project part used as a platform part or variant,
`(<platform id>)`; a platform part allocated directly is listed by its own id. The `docs/compliance.md`
page introduction mentions the table. This table is the basis of the quote.

The explorer's allocation view tags the focus component with its degree and tags `#Modified` parts
`modified`.

## Example (window-switch RFQ)

- F: FEAT-101 to FEAT-104 keep their ids, docs and `@Matches`, and get their own functions, mirroring the
  platform's (F-101 to F-113), with the same flows and successions.
- L: LC-100 `OEM_WindowSwitch` owns LC-101 keySensing, LC-102 switchController, LC-103 linCommunication,
  LC-104 illumination, LC-105 powerSupply, LC-106 enclosure, with ports LI-101 to LI-109 and the
  connections the platform has. The SRs are satisfied by the same components as today, by their RFQ
  counterparts; SR-106 partNumberLabel moves from LC-100 to LC-106 enclosure.
- P: the RFQ allocates its components to the platform's parts and its own, as the platform does for its
  components. Two changes on top of today's parts:
  - PC-112 `oemKeyCaps :>> keyCaps :> WindowSwitchPhysical::keyCaps`, `#Mechanical #Modified`, in PC-100:
    the platform caps with the OEM's symbol set, a new laser-etching program.
  - PC-113 `partNumberLabel`, `#Mechanical`, new, in PC-100: the printed label with the door's OEM part
    number and its Data Matrix code.
- Degrees: LC-106 enclosure `partial` (modified caps, a new label, platform housing and seal); every
  other leaf `full`; LC-100 `partial`. FEAT-101 windowKeys reaches the enclosure through
  provideTactileFeedback and is `partial`, the others `full`. No component is all `new`; that degree is
  covered by unit tests and an acceptance mutation.
- `docs/conf.py`'s project name, still "Seat switch RFQ", becomes "Window switch RFQ".

The platform example is unchanged.

## Where it lands

- `src/sysml2kit/needs.py`: the specialization error, `#Modified`, the `modified` field.
- `src/sysml2kit/reuse.py`: degrees per part, component and feature.
- `src/sysml2kit/compliance.py`: the new values and the realization table.
- `Trace` in both examples and the project template; `ubproject.toml` (`reuse` description, a
  `modified` field) in both examples and the template.
- `plugins/sysml-rflp`: `rflp-method/references/structure.md` (platform section and reuse status),
  `rfq` skill, `sysml-author` skill and `patterns.sysml`, the functional, logical, physical and reviewer
  agents, `glossary.md`.
- `demo`: the allocation view tags; tests that name RFQ components or functions.
- Tests: `tests/test_reuse.py`, bridge tests, `tests/acceptance.py` (mutations that rely on features
  subsetting platform features are retargeted; new mutations for the two bridge errors and an all-`new`
  component).

## Calls made while writing this up

- `#Mechanical #Modified part` parses: `sysml` 0.2.0-kit.3 checks it and exports two metadata usages on
  the part.
- Constraints sit on PC-100, which now holds a modified and a new part, so the CRS they satisfy
  (CRS-301, CRS-302, CRS-402, CRS-501 to CRS-505, and CRS-404 through PC-109) show `partial` in the compliance table's Reuse column. That is
  the switch as built; no special case.
- In the platform's own build nothing is `platform: true`, so every degree there is `new`, as every
  status is `new` today. Unchanged; the platform build does not report reuse.
- `variant` disappears as a status; which variant a part selects stays visible in the variants view.

## Left to the builder

Function and port names in the RFQ (mirroring the platform's is the default); the wording of docs; how
the explorer renders the tags; where in `needs.py` and `reuse.py` the code goes.
