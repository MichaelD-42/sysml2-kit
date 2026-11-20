# Software requirements

Requirements on the drive control firmware (EDU-PC-005).

:::{swreq} Torque request handling
:id: EDU-SWR-001
:satisfies: EDU-SR-003
:realizes: EDU-PC-005

The firmware shall read the torque request CAN message every 1 ms and update the current
setpoint in the same cycle.
:::

:::{swreq} Recovery current limit
:id: EDU-SWR-002
:satisfies: EDU-SR-002
:realizes: EDU-PC-005

The firmware shall cap recovery current at the battery charge limit sent by the vehicle.
:::
