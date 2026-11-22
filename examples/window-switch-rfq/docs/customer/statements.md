# Compliance statements

The supplier's answers that the model does not give: what the platform does not offer, commercial
terms, and deviations from a customer test requirement.

:::{cst} Capacitive window keys not offered
:id: CST-001
:answers: CRS-205
:compliance: not-comply

Not offered. The window-switch platform has mechanical two-stage keys; capacitive keys with a
position slider would need new sensor electronics and an actuator. A quotation can be made
separately on request.
:::

:::{cst} Warranty terms
:id: CST-002
:answers: CRS-901
:compliance: comply

The supplier warrants the switches for 5 years or 150 000 km from vehicle registration, whichever
comes first, under its standard warranty conditions.
:::

:::{cst} Durability test pass criterion
:id: CST-003
:answers: CTR-001
:compliance: partial

Deviation. The test is run as CTR-001 prescribes, to 150 000 cycles per stage, but the pass
criterion is 100 000 cycles: the platform key is rated for 100 000 actuations (CRS-302 is met in
part). The cycle count at which the first key fails is reported.
:::

:::{cst} Durability met in part
:id: CST-004
:answers: CRS-302
:compliance: partial

Partial. The platform key mechanism is rated for 100 000 actuations per stage (CON-102), two thirds
of the 150 000 requested. Reaching 150 000 needs a new key mechanism outside the platform, which
can be quoted separately on request.
:::

:::{cst} Child-lock fault blinking not offered
:id: CST-005
:answers: CRS-203
:compliance: partial

Partial. The child-lock key and the telltale showing the lock are offered as the platform has them
(SR-102); the platform telltale does not blink on a child-lock fault. Fault blinking needs a new
signal in the LIN description file and a firmware change, which can be quoted separately.
:::
