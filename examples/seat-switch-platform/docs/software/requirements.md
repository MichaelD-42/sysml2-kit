# Software requirements

Requirements on the switch firmware (SSW-PC-016). Unit and integration test results link to them
from `test-results/junit.xml`.

:::{swreq} Secure boot
:id: SSW-SWR-001
:satisfies: SSW-SR-006
:realizes: SSW-PC-016
:tags: cybersecurity

The boot loader shall check the application image's ECDSA signature against the public key in
write-protected flash at every start and stay in boot mode if the check fails.
:::

:::{swreq} Tester authentication
:id: SSW-SWR-002
:satisfies: SSW-SR-007
:realizes: SSW-PC-016
:tags: cybersecurity

The diagnostic stack shall unlock write and flash services only after the tester presents a
certificate that chains to the root key in write-protected flash and proves possession of its
private key, and shall refuse further attempts for 10 s after three failed ones.
:::

:::{swreq} LIN stack
:id: SSW-SWR-003
:satisfies: SSW-SR-004
:realizes: SSW-PC-016

The LIN stack shall update the key-state frame in the task that detects the change and discard
received frames with a wrong checksum.
:::

:::{swreq} Debouncing
:id: SSW-SWR-004
:satisfies: SSW-SR-001, SSW-SR-002
:realizes: SSW-PC-016

The firmware shall accept a key, knob or lumbar pad direction after 10 ms of stable input.
:::

:::{swreq} Fault memory
:id: SSW-SWR-005
:satisfies: SSW-SR-005
:realizes: SSW-PC-016
:tags: workshop

The diagnostic stack shall store a stuck-key trouble code with its key number after 30 s of
continuous press and keep it across power cycles.
:::
