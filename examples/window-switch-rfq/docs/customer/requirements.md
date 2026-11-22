# Customer requirements

Component specification "Door window switch", as received with the request for quotation. The OEM
numbers its requirements by chapter (CRS-1xx general, 2xx operating functions, 3xx haptics and
illumination, 4xx communication, 5xx environment and mechanics, 9xx commercial). The supplier has
added `:class:` to every requirement and `:scope:` where it applies; the texts are the customer's.

## 1 General

:::{crs} Scope of supply
:id: CRS-101
:class: information

This specification covers the window-lifter switches of the vehicle line's front doors: the driver door
switch for all four windows and the passenger door switch for its own window, each mounted in the
armrest trim. The vehicle line is left-hand drive only; the rear doors keep their own switches.
:::

:::{crs} Start of production and volumes
:id: CRS-102
:class: information

SOP is planned for calendar week 10 of 2029. Planned volume is 220 000 vehicles per year over a
6-year production period.
:::

## 2 Operating functions

:::{crs} Window keys per door
:id: CRS-201
:class: functional

The driver door switch shall have one key for each of the four windows and a child-lock key; the
passenger door switch shall have one key for its own window.
:::

:::{crs} Manual and express travel
:id: CRS-202
:class: functional

Each window key shall move its window while held at a first stage and start express travel to the
end position when pulled or pushed to a second stage.
:::

:::{crs} Child lock with telltale
:id: CRS-203
:class: functional

The child-lock key shall lock and unlock the rear windows. A telltale shall show the lock, and shall
blink when the door control unit reports a child-lock fault.
:::

:::{crs} Night design
:id: CRS-204
:class: functional

Key symbols shall be lit at night at the dimming level the vehicle sends.
:::

:::{crs} Capacitive window keys
:id: CRS-205
:class: functional
:scope: not-offered

The window keys shall be capacitive touch surfaces flush with the trim, with a slider for the window
position.
:::

## 3 Haptics and illumination

:::{crs} Actuation force
:id: CRS-301
:class: non-functional

The first-stage actuation force of every key shall be 3.0 N to 7.5 N.
:::

:::{crs} Durability
:id: CRS-302
:class: non-functional

Every key shall withstand 150 000 actuations of each stage.
:::

:::{crs} Symbol colour
:id: CRS-303
:class: constraint

Key symbols shall be lit white.
:::

## 4 Communication

:::{crs} LIN interface
:id: CRS-401
:class: functional

The switch shall be a LIN responder of the door control unit and send its key states per the LIN
description file supplied by the OEM.
:::

:::{crs} LIN version
:id: CRS-402
:class: constraint

The switch shall implement LIN 2.2A.
:::

:::{crs} LIN message plausibility
:id: CRS-403
:class: functional

The switch shall ignore received frames with a wrong checksum, a repeated alive counter or a signal
out of its range.
:::

:::{crs} Node addresses
:id: CRS-404
:class: constraint

Both door switches share the door LIN; each shall have its own node address, 0x2A for the driver
door and 0x2B for the passenger door.
:::

## 5 Environment and mechanics

:::{crs} Operating voltage
:id: CRS-501
:class: constraint

The switch shall operate from 9 V to 16 V.
:::

:::{crs} Operating temperature
:id: CRS-502
:class: constraint

The switch shall operate from -40 °C to +85 °C.
:::

:::{crs} Ingress protection
:id: CRS-503
:class: constraint

The switch shall be rated IP5K3 as mounted in the armrest.
:::

:::{crs} Quiescent current
:id: CRS-504
:class: non-functional

With the LIN bus asleep, the switch shall draw at most 100 µA.
:::

:::{crs} Mass
:id: CRS-505
:class: constraint

A switch shall weigh at most 50 g.
:::

:::{crs} Part numbers
:id: CRS-506
:class: non-functional

Each switch shall carry the OEM part number of its door on its label, so the driver and passenger
switches cannot be mixed up at the line.
:::

## 9 Commercial

:::{crs} Warranty
:id: CRS-901
:class: non-functional
:scope: commercial

The supplier shall warrant the switches for 5 years or 150 000 km from vehicle registration,
whichever comes first.
:::
