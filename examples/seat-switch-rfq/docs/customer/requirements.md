# Customer requirements

Component specification "Seat adjustment switch", as received with the request for quotation. The
OEM numbers its requirements by chapter (CRS-1xx general, 2xx operating functions, 3xx haptics and
illumination, 4xx communication and diagnostics, 5xx environment and mechanics, 6xx cybersecurity,
7xx production, 8xx service, 9xx commercial). The supplier has added `:class:` to every requirement
and `:scope:` where it applies; the texts are the customer's.

## 1 General

:::{crs} Scope of supply
:id: CRS-101
:class: information

This specification covers the seat adjustment switches of the vehicle line: one switch at each of the
driver, co-driver, rear left and rear right seats, each mounted in the outer side trim of its seat.
The vehicle line is left-hand drive only.
:::

:::{crs} Start of production and volumes
:id: CRS-102
:class: information

SOP is planned for calendar week 14 of 2029. Planned volume is 180 000 vehicles per year over a
7-year production period; 55 % of vehicles are ordered with powered rear seats and carry the two
rear switches.
:::

:::{crs} Mounting and connection
:id: CRS-103
:class: information

Each switch clips into an opening of the seat side trim and connects to the seat wiring harness with
a 6-pin connector carrying supply, ground and LIN. The seat control unit is the LIN commander.
:::

:::{crs} Applicable OEM standards
:id: CRS-104
:class: information

The following OEM standards apply in the version valid at nomination: OEM-ENV-100 (environmental
testing of electrical components), OEM-EMC-200 (electromagnetic compatibility), OEM-LIN-300 (LIN
communication), OEM-SEC-400 (cybersecurity of control units), OEM-MAT-500 (materials and restricted
substances).
:::

:::{crs} Functional safety classification
:id: CRS-105
:class: information

The seat adjustment switch is classified QM: none of its functions is assigned an ASIL. Unintended
seat movement is prevented by the seat control unit.
:::

## 2 Operating functions

:::{crs} Seat adjustment directions
:id: CRS-201
:class: functional

The switch shall allow the occupant to adjust the seat fore and aft, the seat height, the backrest
recline and the lumbar support (up, down, in, out). The control shall be shaped like the seat so
that its use is understood without instruction.
:::

:::{crs} Adjustment while held
:id: CRS-202
:class: functional

The seat shall move only as long as the control is held in a direction and shall stop when it is
released.
:::

:::{crs} Comfort keys per seat position
:id: CRS-203
:class: functional

The switches shall carry the following comfort keys: driver seat: massage, seat heating, seat
cooling; co-driver seat: seat heating, seat cooling; rear left and rear right seats: seat heating.
:::

:::{crs} Comfort level steps
:id: CRS-204
:class: functional

Each press of a comfort key shall select the next level of its function in the order off, 1, 2, 3,
off.
:::

:::{crs} Comfort level indication
:id: CRS-205
:class: functional

The current level of each comfort function shall be shown at its key by three indicator lights.
:::

:::{crs} Night design
:id: CRS-206
:class: functional

All key symbols shall be backlit when the vehicle lighting is on, at the dimming level sent by the
vehicle.
:::

:::{crs} Capacitive comfort keys
:id: CRS-207
:class: functional
:scope: not-offered

The comfort keys shall be capacitive touch surfaces flush with the trim, with active haptic feedback
on touch.
:::

## 3 Haptics and illumination

:::{crs} Actuation force
:id: CRS-301
:class: non-functional

The actuation force of every key and every control direction shall be between 3.0 N and 6.5 N.
:::

:::{crs} Key travel
:id: CRS-302
:class: non-functional

The travel to the actuation point shall be between 0.2 mm and 1.5 mm, with a clearly perceptible
tactile point.
:::

:::{crs} Symbol luminance
:id: CRS-303
:class: non-functional

The luminance of a lit key symbol shall be between 8 cd/m² and 40 cd/m² at full dimming level.
:::

:::{crs} Durability
:id: CRS-304
:class: non-functional

Every key and every control direction shall withstand 300 000 actuations over the temperature range
without loss of function and with the actuation force still within CRS-301.
:::

:::{crs} Light colours
:id: CRS-305
:class: constraint

Key symbols shall be lit white and level indicators amber, within the OEM interior colour limits.
:::

## 4 Communication and diagnostics

:::{crs} LIN interface
:id: CRS-401
:class: functional

The switch shall be a LIN responder of the seat control unit and shall communicate per the LIN
description file supplied by the OEM.
:::

:::{crs} LIN version
:id: CRS-402
:class: constraint

The switch shall implement LIN 2.2A.
:::

:::{crs} Key state signals
:id: CRS-403
:class: functional

The switch shall send the state of every key and control direction in its LIN frame. A change shall
be sent within 50 ms.
:::

:::{crs} Identification data
:id: CRS-404
:class: functional
:tags: workshop

The switch shall report its OEM part number, hardware version, software version and serial number on
diagnostic request.
:::

## 5 Environment and mechanics

:::{crs} Operating voltage
:id: CRS-501
:class: constraint

The switch shall operate with full function from 9 V to 16 V.
:::

:::{crs} Operating temperature
:id: CRS-502
:class: constraint

The switch shall operate with full function from -40 °C to +85 °C.
:::

:::{crs} Ingress protection
:id: CRS-503
:class: constraint

The switch, mounted in the trim, shall meet IP5K4.
:::

:::{crs} Electrostatic discharge
:id: CRS-504
:class: constraint

The switch shall withstand electrostatic discharge of ±8 kV contact and ±15 kV air on every surface
the occupant can touch, without reset or damage.
:::

:::{crs} Electromagnetic compatibility
:id: CRS-505
:class: constraint

The switch shall meet OEM-EMC-200, severity class 3, for emission and immunity.
:::

:::{crs} Mass
:id: CRS-506
:class: constraint

The mass of a switch shall not exceed 60 g.
:::

:::{crs} Installation space
:id: CRS-507
:class: constraint

The switch including its control shall fit the installation space defined in the seat trim drawing.
:::

:::{crs} Materials
:id: CRS-508
:class: constraint

All materials shall comply with OEM-MAT-500. The supplier shall declare every material in the OEM
material data system before the first sample delivery.
:::

:::{crs} Quiescent current
:id: CRS-509
:class: constraint

With the LIN bus asleep, the switch shall draw at most 100 µA.
:::

## 6 Cybersecurity

:::{crs} Authenticated software update
:id: CRS-601
:class: functional
:tags: cybersecurity

The switch shall accept only software images signed with a key authorised by the OEM.
:::

:::{crs} Secure boot
:id: CRS-602
:class: functional
:tags: cybersecurity

At every start the switch shall verify its software and shall not run software that fails the
check.
:::

:::{crs} Protected diagnostic access
:id: CRS-603
:class: functional
:tags: cybersecurity, workshop

Writing diagnostic services and software download shall be possible only after successful security
access per OEM-SEC-400.
:::

:::{crs} No open debug interface
:id: CRS-604
:class: constraint
:tags: cybersecurity

Series parts shall have no open debug or programming interface.
:::

:::{crs} LIN message plausibility
:id: CRS-605
:class: functional
:tags: cybersecurity

The switch shall discard received LIN frames with an invalid checksum, a frozen alive counter or a
signal value out of range.
:::

## 7 Production

:::{crs} End-of-line test
:id: CRS-701
:class: functional
:tags: production

Every key and every light of every switch shall be tested at the supplier's end of line.
:::

:::{crs} Flashing and variant coding at end of line
:id: CRS-702
:class: functional
:tags: production

The software shall be flashed and the switch coded for its seat position at the supplier's end of
line.
:::

:::{crs} Traceability label
:id: CRS-703
:class: constraint
:tags: production

Every switch shall carry a permanent Data Matrix code with OEM part number, serial number and
production date.
:::

:::{crs} Left/right mistake-proofing
:id: CRS-704
:class: constraint
:tags: production

A switch for a left seat shall not fit a right seat opening and vice versa.
:::

## 8 Service

:::{crs} Fault memory
:id: CRS-801
:class: functional
:tags: workshop

The switch shall store faults (stuck key, defective light, supply voltage out of range) and report
them on diagnostic request.
:::

:::{crs} Software update in the workshop
:id: CRS-802
:class: functional
:tags: workshop

The software shall be updatable in the workshop over the vehicle bus without removing the switch.
:::

:::{crs} Workshop update time
:id: CRS-803
:class: non-functional
:tags: workshop

A complete software update in the workshop shall take at most 3 minutes.
:::

:::{crs} Replacement without seat removal
:id: CRS-804
:class: constraint
:tags: workshop

The switch shall be replaceable without removing the seat from the vehicle.
:::

:::{crs} Spare-part numbers
:id: CRS-805
:class: constraint
:tags: workshop

Each switch variant shall have its own spare-part number.
:::

## 9 Commercial

:::{crs} Warranty
:id: CRS-901
:class: non-functional
:scope: commercial

The supplier shall warrant the switches for 5 years or 150 000 km from vehicle registration,
whichever comes first.
:::
