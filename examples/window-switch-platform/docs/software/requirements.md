# Software requirements

Requirements on the switch firmware (WSW-PC-016), each allocated to the SW component or SW unit
that implements it. Unit test results link to them from `test-results/junit.xml`.

:::{swreq} Two-stage detection
:id: WSW-SWR-001
:satisfies: WSW-SR-001
:allocated_to: WSW-PC-018

The key scan shall read both contacts of every two-stage key every 2 ms and report the stage the key is at.
:::

:::{swreq} Debouncing
:id: WSW-SWR-002
:satisfies: WSW-SR-001, WSW-SR-002
:allocated_to: WSW-PC-019

The debouncer shall accept a key stage only after it is stable for 10 ms.
:::

:::{swreq} Node address
:id: WSW-SWR-003
:satisfies: WSW-SR-005
:allocated_to: WSW-PC-021

The LIN driver shall pass on only requests addressed to the configured node address or to the broadcast address.
:::

:::{swreq} Signal plausibility
:id: WSW-SWR-004
:satisfies: WSW-SR-006
:allocated_to: WSW-PC-022

The signal interface shall discard a command frame with a repeated alive counter or a signal outside its LDF range.
:::

:::{swreq} Dimming
:id: WSW-SWR-005
:satisfies: WSW-SR-003
:allocated_to: WSW-PC-024

The LED control shall set the symbol PWM duty from the received dimming level within one 10 ms cycle.
:::
