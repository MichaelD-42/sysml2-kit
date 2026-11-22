# Window-switch example replacing the seat switch

## Why

The seat-switch examples (`examples/seat-switch-platform`, `examples/seat-switch-rfq`, about 5,300 lines, 45 CRS, 49 platform parts, four seat positions) are too large to take in or present. Michael wants a simpler automotive HMI example that keeps the whole method visible. It replaces the seat switch as the kit's acceptance fixture and the demo's model.

Goal: about a third of the content, every kind of element and every acceptance mutation still present. "Simpler" means fewer instances of each kind, not fewer kinds.

Non-goals: no method change. The planned platform change (RFQ-owned logical components realized fully, partly or not by platform solutions) comes next, on this example. No UML activities (dropped). No new rules or bridge features.

Anti-goal: an example that silently loses acceptance coverage. Every mutation in `tests/acceptance.py` must have a counterpart that still fails the build the same way.

## Approaches

1. **Swap first on today's method, then the method change** (chosen by Michael): the port is checkable against the same 36 mutations and the retargeted view tests; the method change then touches a third of the content.
2. Method change first on the seat switch, then swap: rewrites the large example twice.
3. Both at once: one diff where a porting mistake and a method change look alike.

## The product

A door window-lifter switch pack on LIN. The supplier's platform is a switch family; the OEM's RFQ asks for the driver door pack (four window keys plus a rear child lock) and the passenger door pack (one window key). Two-stage keys: first stage manual, second stage express. Anti-pinch and motor control stay in the door control unit (the context), not in the switch.

Projects: `examples/window-switch-platform` (tag `WSW-`, e.g. `WSW-PC-004`), `examples/window-switch-rfq` (untagged ids, as today). Same layout, Makefiles, docs, schemas and test-result files as the seat-switch projects; the seat-switch directories are deleted.

## Content and sizes

| Kind | Seat switch (platform / RFQ) | Window switch (platform / RFQ) | Window-switch content |
|---|---|---|---|
| Use case | 4 / 4 | 3 / 3 | move a window; lock the rear windows (driver); find the switch at night |
| Feature | 6 / 6 | 4 / 4 | window control; child lock; night illumination; vehicle communication |
| Function | 22 / – | ~10 | sense key stage, debounce, map to window request (with successions); detect child-lock key, show child-lock state; receive dimming, light symbols; send key states, receive commands, check plausibility |
| Logical component | 8 / 1 | 6 / 1 | keySensing, switchController, illumination, linCommunication, powerSupply, enclosure; RFQ `LC-100` subsets the platform switch as today |
| Physical part | 49 / 14 | ~18 / ~6 | ME housing, key caps, seal; EE PCB with microcontroller, LIN transceiver, LED driver, key sensors, voltage regulator; SW firmware with three SW components (inputProcessing: keyScan, debouncer; linStack: linDriver, signalInterface; illuminationControl: ledControl) |
| Variation | 2 | 2 | `keyModule` {fourKey, oneKey} (ME/EE key population), `illumination` {white, amber} |
| Assembly / positions | 1 + 4 | 1 + 2 | `driverDoorSwitch` (fourKey, its own LIN NAD), `passengerDoorSwitch` (oneKey); a constraint on the program assembly keeps their NADs distinct |
| PRQ | 21 | ~10 | platform requirements, classed |
| CRS | – / 45 | – / ~16 | see below |
| CST | – / 4 | – / 3 | warranty terms (commercial), capacitive keys not offered (not-comply), durability met in part (partial) |
| CTR | – / 11 | – / 4 | durability per key (met in part), haptic measurement, ingress test, initial sample inspection (`scope: commercial`, answered by a CST) |
| SR | 14 / 18 | ~6 / ~6 | one `shall` each |
| Constraint | 12 / 24 | ~5 / ~8 | platform ratings (key force, IP, voltage, quiescent current); RFQ limits on them, a partial one, the NAD one |
| SWR | 14 / – | ~5 | on the SW components and units, with unit test results |
| System test / acceptance test | 22+5 / 21+6 | ~8+3 / ~8+3 | one test deviation kept |
| Test results | 41 / 27 | ~15 / ~12 | JUnit XML |

RFQ CRS (about 16), one or more per class and scope the method knows:

- functional: window keys per door; two-stage manual and express; child lock with telltale (matched in part: the OEM's fault blinking is not in the platform, so an SR states what is met and a CST `partial` the gap); night design; key-state signals on LIN; LIN message plausibility
- non-functional / constraint: actuation force; ingress protection; operating voltage; operating temperature; quiescent current; installation space; durability (met in part by a partial constraint)
- information: applicable OEM standards; start of production and volumes
- commercial: warranty
- not offered: capacitive touch keys

## Acceptance mutations

Each of the 36 mutations in `tests/acceptance.py` is retargeted to the matching window-switch text, keeping its description apart from the domain words (for example "two door positions coded to one node address break the vehicle's constraint"). The `information()`, `incremental()` and `hook()` checks are retargeted the same way.

## Everything else that names the seat switch

Retarget, keeping each file's structure: `demo/tests/*` (about 150 ids in `test_views.py`), `demo/tests/support.py`, `demo/Makefile`, `demo/explorer/prompt.md` (its example queries run against the RFQ graph), `demo/README.md` walkthrough, `README.md`, `glossary.md`, `.github/workflows/ci.yml`, `tests/test_template.py`, the method spec `plugins/sysml-rflp/skills/rflp-method/references/structure.md` and `rfq/references/platform-capture.md`, and the functional, physical and requirements agents. Historical docs under `docs/` (reviews, earlier specs and plans) stay as they are.

## Settled calls

- Baseline: the working tree as committed before the swap (the seat-switch edits, the method spec and the explorer work of 2026-11-22 included). The RFQ names its platform as a sibling checkout, `PLATFORM := ../window-switch-platform`, as the seat-switch RFQ does now.
- The child-lock key belongs to the `fourKey` variant (the driver module: four window keys and the child-lock key, each with its key sensor). The child-lock feature and its telltale are in the platform; the RFQ's fault blinking of the telltale is what the platform does not do (the partial match).
- Sizes are soft: size by what the rules and the mutations need, staying near a third of the seat switch.
- The compliance table shows every rating the kit gives except `not answered`: comply, partial, not offered, commercial, information.
- The NAD constraint stays on the program assembly as one `!=` between the two positions; the evaluator handles it (the seat switch uses the same operator).
- The hook's duplicate-id mutation puts the clashing id in `passengerDoorSwitch`; all RFQ use cases share one subject, so the incremental check's subject rename keeps working.
- Demo tests are re-derived, not only renamed, where they assert counts or structure (four positions, shared parts named "also in" three others).
- Test results are hand-written JUnit XML with `verifies` properties naming the STC, ATC and SWR ids, as today.

## Left to the builder

Exact names, ids, doc texts, attribute values and test texts, within the sizes above; which CRS each SR and constraint satisfies; the test deviation's case. Every example must build with `make` (platform and RFQ), the compliance table must show each rating class, and `tests/acceptance.py`, the kit's unit tests and the demo tests must pass.
