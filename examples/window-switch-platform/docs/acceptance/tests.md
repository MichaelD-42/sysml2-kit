# Acceptance tests

:::{acctest} Window operation in the door
:id: WSW-ATC-001
:verifies: WSW-PRQ-001, WSW-PRQ-004, WSW-UC-001

In the reference door with its door control unit, move every window with each key module at both stages; pass if the window moves while the first stage is held and runs to its end position after the second.
:::

:::{acctest} Child lock in the door
:id: WSW-ATC-002
:verifies: WSW-PRQ-002, WSW-UC-002

With the four-key module in the reference driver door, press the child-lock key; pass if the rear window keys are blocked and the telltale lights, and both are undone on the next press.
:::

:::{acctest} Night design in the door
:id: WSW-ATC-003
:verifies: WSW-PRQ-003, WSW-UC-003

Switch the reference vehicle to night mode with each backlight; pass if the symbols follow the dimming level.
:::

:::{acctest} Design validation
:id: WSW-ATC-004
:verifies: WSW-PRQ-005, WSW-PRQ-006, WSW-PRQ-007, WSW-PRQ-008, WSW-PRQ-009, WSW-PRQ-010

Run the qualification plan QP-WSW-01 on parts from series tooling; pass if every test of the plan passes.
:::
