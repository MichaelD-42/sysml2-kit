# Software requirements

Requirements on the switch firmware (SSW-PC-016), each allocated to the SW component or SW unit
that implements it. Unit and integration test results link to them from `test-results/junit.xml`.

:::{swreq} Secure boot
:id: SSW-SWR-001
:satisfies: SSW-SR-006
:allocated_to: SSW-PC-024
:tags: cybersecurity

The boot loader shall check the application image's ECDSA signature against the public key in
write-protected flash at every start and stay in boot mode if the check fails.
:::

:::{swreq} Tester authentication
:id: SSW-SWR-002
:satisfies: SSW-SR-007
:allocated_to: SSW-PC-043
:tags: cybersecurity

The diagnostic stack shall unlock write and flash services only after the tester presents a
certificate that chains to the root key in write-protected flash and proves possession of its
private key, and shall refuse further attempts for 10 s after three failed ones.
:::

:::{swreq} LIN stack
:id: SSW-SWR-003
:satisfies: SSW-SR-004
:allocated_to: SSW-PC-034

The LIN stack shall operate as a LIN 2.2A responder at 19.2 kbit/s with the enhanced checksum,
publishing the status frame and subscribing to the command frame and the diagnostic frames of the
customer's LDF.
:::

:::{swreq} Debouncing
:id: SSW-SWR-004
:satisfies: SSW-SR-001, SSW-SR-002
:allocated_to: SSW-PC-029

The firmware shall accept a key, knob or lumbar pad direction after 10 ms of stable input.
:::

:::{swreq} Fault memory
:id: SSW-SWR-005
:satisfies: SSW-SR-005
:allocated_to: SSW-PC-044
:tags: workshop

The diagnostic stack shall store a stuck-key trouble code with its key number after 30 s of
continuous press and keep it across power cycles.
:::

:::{swreq} Frame checks
:id: SSW-SWR-006
:satisfies: SSW-SR-014
:allocated_to: SSW-PC-036

The LIN protocol shall discard a received frame whose protected identifier parity or enhanced
checksum is wrong.
:::

:::{swreq} Signal plausibility
:id: SSW-SWR-007
:satisfies: SSW-SR-014
:allocated_to: SSW-PC-037

The signal interface shall discard a received command frame whose alive counter repeats the
previous frame's or whose signals are outside their LDF range.
:::

:::{swreq} Node address
:id: SSW-SWR-008
:satisfies: SSW-SR-012
:allocated_to: SSW-PC-038

The node configuration shall answer master requests addressed to the NAD written by end-of-line
coding or to the broadcast NAD 0x7F, and ignore all others.
:::

:::{swreq} Sleep and wake-up
:id: SSW-SWR-009
:satisfies: SSW-SR-013
:allocated_to: SSW-PC-040

The network management shall switch the transceiver to sleep mode on a go-to-sleep command or after
4 s of bus inactivity, and wake on a dominant bus pulse of at least 150 µs.
:::

:::{swreq} Diagnostic transport
:id: SSW-SWR-010
:satisfies: SSW-SR-005
:allocated_to: SSW-PC-039
:tags: workshop

The transport layer shall segment and reassemble UDS messages of up to 4095 bytes into master
request and slave response frames.
:::

:::{swreq} Dimming
:id: SSW-SWR-011
:satisfies: SSW-SR-003
:allocated_to: SSW-PC-032

The LED control shall set the symbol LED duty cycle for a received dimming level within 20 ms.
:::

:::{swreq} Image activation
:id: SSW-SWR-012
:satisfies: SSW-SR-006
:allocated_to: SSW-PC-048
:tags: cybersecurity

The update manager shall mark a downloaded image valid for start only after its signature verifies.
:::

:::{swreq} End-of-line coding
:id: SSW-SWR-013
:satisfies: SSW-SR-009, SSW-SR-012
:allocated_to: SSW-PC-045
:tags: production

The end-of-line services shall write the button-set code and the NAD to write-protected memory only
in an authenticated end-of-line session.
:::
