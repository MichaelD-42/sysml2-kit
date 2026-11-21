# Acceptance tests

Tests run with the customer on the vehicle or with the customer's witnesses. Each verifies customer
requirements and use cases, implements a customer test requirement, or both.

:::{acctest} Seat adjustment in the vehicle
:id: ATC-101
:verifies: CRS-201, CRS-202, CRS-401, CRS-403, UC-101

At each seat position of a prototype vehicle, move the seat in every direction with the knob and the
lumbar pad; pass if the seat moves only while the control is held, in the requested direction.
:::

:::{acctest} Comfort functions and night design in the vehicle
:id: ATC-102
:verifies: CRS-203, CRS-204, CRS-205, CRS-206, CRS-303, CRS-305, UC-102

At each seat position, step every comfort function through its levels, then switch the vehicle
lighting on and vary the dimming; pass if each position has its keys, the function and indicator
lights follow each press, and the white symbols follow the dimming level within 8 cd/m² to
40 cd/m².
:::

:::{acctest} Workshop diagnosis, update and replacement
:id: ATC-103
:verifies: CRS-404, CRS-801, CRS-802, CRS-803, UC-103
:implements: CTR-010

With an OEM technician, carry out CTR-010: read identification and a provoked fault, update the
software over the vehicle bus after security access, and replace the driver switch with a spare part;
pass if every step succeeds with the workshop manual alone and the update takes at most 3 minutes.
:::

:::{acctest} End-of-line production test
:id: ATC-104
:verifies: CRS-701, CRS-702, CRS-703, CRS-704, UC-104

At the supplier's end-of-line station, witnessed by the customer, flash, code and test switches for
all four positions, read their labels and try every switch in both trim openings; pass if every key
and light is tested, each switch reports its position's keys, every label reads, and each switch
fits its own side only.
:::

:::{acctest} In-vehicle validation drive
:id: ATC-105
:implements: CTR-011

Carry out CTR-011 with the customer's test drivers; pass if the findings are agreed with the customer.
:::

:::{acctest} Initial sample inspection
:id: ATC-106
:implements: CTR-009

Measure, weigh and inspect the first off-tool samples of every variant and submit the initial sample
inspection report of CTR-009; pass when the customer approves the report.
:::
