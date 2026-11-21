# Acceptance tests

:::{acctest} Seat adjustment in the vehicle
:id: SSW-ATC-001
:verifies: SSW-PRQ-001, SSW-PRQ-004, SSW-UC-001

In the reference seat with its seat control unit, move the seat in every direction with the knob
and the lumbar pad; pass if the seat moves only while the knob or pad is held, in the requested direction.
:::

:::{acctest} Comfort functions and night design
:id: SSW-ATC-002
:verifies: SSW-PRQ-002, SSW-PRQ-003, SSW-UC-002

With each button set in the reference seat, step every comfort function through its levels and
switch the vehicle to night mode; pass if seat and level LEDs follow each press and the symbols
follow the dimming level.
:::

:::{acctest} Workshop diagnosis and update
:id: SSW-ATC-003
:verifies: SSW-PRQ-005, SSW-PRQ-006, SSW-PRQ-007, SSW-PRQ-020, SSW-UC-003

With a workshop diagnostic tester on the vehicle bus, read and clear a provoked fault, then
update the firmware after certificate-based authentication; pass if the fault is reported and the new firmware
runs within 120 s, and if the update is refused without authentication.
:::

:::{acctest} End-of-line production test
:id: SSW-ATC-004
:verifies: SSW-PRQ-008, SSW-PRQ-017, SSW-PRQ-018, SSW-PRQ-019, SSW-PRQ-021, SSW-UC-004

Run a production batch of each housing and button set through the end-of-line station; pass if
every part is flashed, coded, marked and passes the key and LED test within the cycle time, and if
no housing fits the fixture of the other side.
:::

:::{acctest} Design validation
:id: SSW-ATC-005
:verifies: SSW-PRQ-009, SSW-PRQ-010, SSW-PRQ-011, SSW-PRQ-012, SSW-PRQ-013, SSW-PRQ-014, SSW-PRQ-015, SSW-PRQ-016

Run the qualification plan QP-SSW-01 on parts from series tooling; pass if every test of the plan
passes.
:::
