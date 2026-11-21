# Customer test requirements

The tests the OEM prescribes, as received with the request for quotation. The supplier's system and
acceptance tests implement them; the texts are the customer's.

:::{ctr} Environmental test programme
:id: CTR-001
:purpose: verification
:method: test
:applies_to: CRS-501, CRS-502

The switch shall pass the OEM-ENV-100 programme for interior components, mounting location "seat",
on 6 samples: thermal shock, temperature and humidity cycling, low and high temperature operation,
supply voltage variation, vibration and mechanical shock, with function checks before, during and
after each test.
:::

:::{ctr} Durability per key
:id: CTR-002
:purpose: verification
:method: test
:applies_to: CRS-304

Each key and each control direction shall be actuated 300 000 times, one third each at -40 °C,
+23 °C and +85 °C, at 1 Hz, on 6 samples. Actuation force and function shall be checked every 50 000
cycles.
:::

:::{ctr} Haptic measurement
:id: CTR-003
:purpose: verification
:method: test
:applies_to: CRS-301, CRS-302

The force-travel curve of every key and control direction shall be recorded on 10 samples per
variant, before and after durability testing, and reported with peak force, force at the actuation
point and travel.
:::

:::{ctr} EMC test
:id: CTR-004
:purpose: verification
:method: test
:applies_to: CRS-505

The switch shall be tested to OEM-EMC-200, severity class 3, in a laboratory accredited for that
standard. The test plan shall be agreed with the OEM before testing.
:::

:::{ctr} ESD test
:id: CTR-005
:purpose: verification
:method: test
:applies_to: CRS-504

Discharges of ±2, ±4, ±6, ±8 kV contact and ±15 kV air shall be applied to every touchable surface,
10 per point and polarity, powered and unpowered.
:::

:::{ctr} Ingress test
:id: CTR-006
:purpose: verification
:method: test
:applies_to: CRS-503

The switch mounted in an original trim panel shall be tested for IP5K4: dust for 8 h, then splash
water, followed by a function check and inspection of the PCB.
:::

:::{ctr} Cybersecurity penetration test
:id: CTR-007
:purpose: verification
:method: test
:applies_to: CRS-601, CRS-602, CRS-603, CRS-604, CRS-605

Before SOP an independent party shall perform a penetration test per OEM-SEC-400 on series-equivalent
parts, covering the software update path, diagnostic access, hardware interfaces and the LIN
interface. Findings rated high or critical shall be closed before SOP.
:::

:::{ctr} LIN conformance test
:id: CTR-008
:purpose: verification
:method: test
:applies_to: CRS-401, CRS-402, CRS-403, CRS-605

The LIN implementation shall pass the LIN 2.2A conformance test and the OEM-LIN-300 test catalogue.
:::

:::{ctr} Initial sample inspection
:id: CTR-009
:purpose: verification
:method: inspection
:applies_to: CRS-506, CRS-507, CRS-508, CRS-703

With the first off-tool samples the supplier shall submit an initial sample inspection report:
dimensions against the drawing, mass, label content and readability, and the confirmation of the
material declaration.
:::

:::{ctr} Workshop procedure validation
:id: CTR-010
:purpose: validation
:method: demonstration
:applies_to: CRS-801, CRS-802, CRS-804, CRS-805

In a series-equivalent vehicle, an OEM workshop technician shall read the fault memory, update the
software and replace a switch by a spare part ordered by its spare-part number, using only the
workshop manual and the workshop tester.
:::

:::{ctr} In-vehicle validation
:id: CTR-011
:purpose: validation
:method: demonstration
:applies_to: CRS-201, CRS-203, CRS-206

In a prototype vehicle, test drivers shall use all switches during day and night drives for at least
4 weeks and rate operation, feel and readability; findings shall be agreed with the OEM.
:::
