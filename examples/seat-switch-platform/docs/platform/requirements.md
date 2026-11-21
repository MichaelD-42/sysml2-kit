# Platform requirements

What the seat-switch product line offers every vehicle program. In this project they take the
place of customer requirements: use cases realize them, system requirements and constraints
satisfy them. SSW-PRQ-001 to -017 describe what the product line offers a customer;
SSW-PRQ-018 to -021 are our own production and workshop requirements, set by internal standards
SSW-PRD-04 (production) and SSW-SRV-02 (service). Environmental values follow the supplier's qualification plan QP-SSW-01, which
covers the fictional OEM standards OEM-ENV-100 and OEM-EMC-200.

:::{prq} Seat adjustment input
:id: SSW-PRQ-001
:class: functional

The switch shall let the occupant request seat fore/aft, height and recline adjustment from a
seat-shaped two-part knob (cushion and backrest), and lumbar support adjustment from a 4-way pad,
for as long as the knob or pad is held.
:::

:::{prq} Comfort function input by button set
:id: SSW-PRQ-002
:class: functional

The product line shall offer four button sets: adjustment only; heating; heating and cooling;
massage, heating and cooling. Each comfort key shall step its function through its levels.
:::

:::{prq} Night design illumination
:id: SSW-PRQ-003
:class: functional

Key symbols shall be lit at the dimming level the vehicle sends.
:::

:::{prq} LIN communication
:id: SSW-PRQ-004
:class: functional

The switch shall send its key states to, and receive commands from, the seat control unit over LIN.
:::

:::{prq} Fault memory for the workshop
:id: SSW-PRQ-005
:class: functional
:tags: workshop

The switch shall record faults and make them readable over the vehicle diagnostic channel.
:::

:::{prq} Authenticated firmware update
:id: SSW-PRQ-006
:class: functional
:tags: cybersecurity, workshop

The switch shall accept firmware updates over the vehicle bus and run only firmware signed by
the supplier.
:::

:::{prq} Protected diagnostic access
:id: SSW-PRQ-007
:class: functional
:tags: cybersecurity

Diagnostic services that write data or flash firmware shall be locked until the tester has passed
certificate-based authentication.
:::

:::{prq} End-of-line test and variant coding
:id: SSW-PRQ-008
:class: functional
:tags: production

At end of line the switch shall be flashed, coded to its button set, and every key and LED tested.
:::

:::{prq} Key haptics
:id: SSW-PRQ-009
:class: non-functional

Keys and knob shall have a defined actuation force and travel with a tactile click.
:::

:::{prq} Symbol luminance
:id: SSW-PRQ-010
:class: non-functional

Lit symbols shall be legible at night without glare.
:::

:::{prq} Key durability
:id: SSW-PRQ-011
:class: non-functional

Every key and knob direction shall be rated for at least 200 000 actuations.
:::

:::{prq} Operating voltage
:id: SSW-PRQ-012
:class: constraint

9 V to 16 V.
:::

:::{prq} Operating temperature
:id: SSW-PRQ-013
:class: constraint

-40 °C to +85 °C.
:::

:::{prq} Ingress protection
:id: SSW-PRQ-014
:class: constraint

IP5K4 when mounted in the seat trim.
:::

:::{prq} ESD immunity
:id: SSW-PRQ-015
:class: constraint

±8 kV contact discharge and ±15 kV air discharge on every touchable surface.
:::

:::{prq} LIN version
:id: SSW-PRQ-016
:class: constraint

LIN 2.2A.
:::

:::{prq} Mirrored housings
:id: SSW-PRQ-017
:class: constraint
:tags: production

Housings for the left and right seat side shall be mirror images, and a housing shall not be
fittable on the wrong side.
:::

:::{prq} End-of-line test cycle time
:id: SSW-PRQ-018
:class: non-functional
:tags: production

Our end-of-line station requires the complete key, LED and coding test of one switch to finish
within 12 s, to hold the line's cycle time.
:::

:::{prq} Traceability marking
:id: SSW-PRQ-019
:class: constraint
:tags: production

Production requires every switch to carry a laser-marked Data Matrix code with part number,
variant and serial number, per SSW-PRD-04.
:::

:::{prq} Workshop reflash time
:id: SSW-PRQ-020
:class: non-functional
:tags: workshop

Our service process (SSW-SRV-02) requires a full firmware reflash over LIN, with the fault memory
read before and after, to finish within 120 s.
:::

:::{prq} Side-keyed assembly
:id: SSW-PRQ-021
:class: constraint
:tags: production

Our assembly line requires that left-hand and right-hand inner parts cannot be assembled into a
housing of the other side.
:::
