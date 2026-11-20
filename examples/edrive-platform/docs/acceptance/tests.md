# Acceptance tests

:::{acctest} Vehicle drive
:id: EDU-ATC-001
:verifies: EDU-PRQ-001, EDU-PRQ-003, EDU-UC-001

In a test vehicle with each motor variant, drive the reference route on pedal torque requests;
pass if the vehicle follows the pedal without fault codes.
:::

:::{acctest} Braking energy recovery
:id: EDU-ATC-002
:verifies: EDU-PRQ-002, EDU-UC-002

In a test vehicle, brake from 100 km/h to standstill on the drive alone; pass if the battery
state of charge rises.
:::

:::{acctest} Vehicle installation
:id: EDU-ATC-003
:verifies: EDU-PRQ-004

Install each motor variant in the reference vehicle body; pass if both use the same mounting
points and parts.
:::
