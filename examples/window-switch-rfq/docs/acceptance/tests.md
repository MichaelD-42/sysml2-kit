# Acceptance tests

Tests run with the customer on the vehicle or with the customer's witnesses. Each verifies customer
requirements and use cases, implements a customer test requirement, or both.

:::{acctest} Window operation in the vehicle
:id: ATC-101
:verifies: CRS-201, CRS-202, CRS-401, CRS-402, CRS-403, CRS-404, UC-101

In both front doors of a prototype vehicle, move every window with its key at both stages; pass if
the window moves while the first stage is held and runs to its end position after the second, and
both switches work together on the door LIN.
:::

:::{acctest} Child lock in the vehicle
:id: ATC-102
:verifies: CRS-203, UC-102

In the driver door, press the child-lock key; pass if the rear windows are locked and the telltale
lights, and both are undone on the next press.
:::

:::{acctest} Night design in the vehicle
:id: ATC-103
:verifies: CRS-204, CRS-303, UC-103

Switch the vehicle lighting on and vary the dimming; pass if the white symbols of both switches
follow the dimming level.
:::

:::{acctest} Initial sample inspection
:id: ATC-104
:implements: CTR-004

Submit the initial sample inspection report of CTR-004 with the first off-tool samples; pass when
the customer approves the report.
:::
