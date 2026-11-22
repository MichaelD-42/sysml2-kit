# Platform requirements

What the window-switch product line offers every vehicle program. In this project they take the
place of customer requirements: use cases realize them, system requirements and constraints
satisfy them. Environmental values follow the supplier's qualification plan QP-WSW-01.

:::{prq} Two-stage window keys
:id: WSW-PRQ-001
:class: functional

The switch shall let the occupant move each window with its own key: while held at the first stage the window moves, a pull or push to the second stage starts express travel to the end position. The product line offers a one-key and a four-key module.
:::

:::{prq} Child lock for the rear windows
:id: WSW-PRQ-002
:class: functional

The four-key module shall have a child-lock key that asks the door control unit to block the rear window keys, and a telltale that shows the lock.
:::

:::{prq} Night design illumination
:id: WSW-PRQ-003
:class: functional

Key symbols shall be lit at the dimming level the vehicle sends, in white or amber.
:::

:::{prq} LIN communication
:id: WSW-PRQ-004
:class: functional

The switch shall send its key states to, and receive commands from, the door control unit over LIN.
:::

:::{prq} Key haptics
:id: WSW-PRQ-005
:class: non-functional

Each key shall need a perceptible first-stage force that occupants can operate without looking.
:::

:::{prq} Key durability
:id: WSW-PRQ-006
:class: non-functional

Keys shall withstand the actuations of a vehicle life.
:::

:::{prq} Operating voltage
:id: WSW-PRQ-007
:class: constraint

The switch shall operate on the 12 V vehicle supply from 9 V to 16 V.
:::

:::{prq} Operating temperature
:id: WSW-PRQ-008
:class: constraint

The switch shall operate from -40 °C to +85 °C.
:::

:::{prq} Ingress protection
:id: WSW-PRQ-009
:class: constraint

The switch shall be rated IP5K3 as mounted in the door trim.
:::

:::{prq} LIN version
:id: WSW-PRQ-010
:class: constraint

The switch shall implement LIN 2.2A.
:::
