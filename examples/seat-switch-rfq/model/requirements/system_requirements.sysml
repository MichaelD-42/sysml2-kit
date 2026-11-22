package SeatSwitchRfqRequirements {
    doc /* R layer: what the seat switches shall do, derived from the customer requirements. Values the
     * model can state are constraints on OEM_SeatSwitch and on the position parts (SeatSwitchRfqLogical,
     * SeatSwitchRfqPhysical); these are the rest: behaviour, and what only a document or a drawing shows. */

    private import Trace::*;

    requirement <'SR-101'> adjustmentRequests {
        @Satisfies { need = "CRS-201"; }
        @Satisfies { need = "CRS-202"; }
        doc /* The switch shall report seat fore, aft, up, down, recline forward and recline back, and lumbar up, down, in and out, as ten distinct requests while the knob or lumbar pad is held in that direction. */
    }
    requirement <'SR-102'> comfortLevelSteps {
        @Satisfies { need = "CRS-204"; }
        @Satisfies { need = "CRS-205"; }
        doc /* Each press of a comfort key shall step its function from off through levels 1, 2 and 3 back to off, with one level LED lit per active level. */
    }
    requirement <'SR-103'> nightDesignDimming {
        @Satisfies { need = "CRS-206"; }
        doc /* The switch shall light every key symbol at the dimming level received on LIN within 100 ms of receiving it. */
    }
    requirement <'SR-104'> keyStateReporting {
        @Satisfies { need = "CRS-401"; }
        @Satisfies { need = "CRS-403"; }
        doc /* The switch shall send a changed key state in its LIN frame to the seat control unit at most 50 ms after the change. */
    }
    requirement <'SR-105'> messagePlausibility {
        @Satisfies { need = "CRS-605"; }
        doc /* The switch shall discard every received LIN frame with a wrong checksum, a repeated alive counter or a signal out of its range. */
    }
    requirement <'SR-106'> diagnosticIdentification {
        @Satisfies { need = "CRS-404"; }
        doc /* The switch shall report its part number, hardware version, software version and serial number on a diagnostic read request. */
    }
    requirement <'SR-107'> faultCodes {
        @Satisfies { need = "CRS-801"; }
        doc /* The switch shall store a fault code for a key held longer than 30 s, an open LED and a supply outside 9 V to 16 V, and report it on a diagnostic read request. */
    }
    requirement <'SR-108'> authenticatedWrite {
        @Satisfies { need = "CRS-603"; }
        doc /* The switch shall reject every diagnostic write and flash request until the tester has passed certificate-based authentication. */
    }
    requirement <'SR-109'> signedImagesOnly {
        @Satisfies { need = "CRS-601"; }
        @Satisfies { need = "CRS-602"; }
        doc /* The switch shall install and start only a firmware image whose signature verifies against the key stored at production. */
    }
    requirement <'SR-110'> workshopUpdate {
        @Satisfies { need = "CRS-802"; }
        doc /* The switch shall accept a complete firmware update over LIN from the workshop tester while fitted in the vehicle. */
    }
    requirement <'SR-111'> endOfLineTest {
        @Satisfies { need = "CRS-701"; }
        doc /* In end-of-line test mode the switch shall report every key's state and light every LED on command. */
    }
    requirement <'SR-112'> endOfLineCoding {
        @Satisfies { need = "CRS-702"; }
        doc /* The switch shall accept flashing and button-set coding at end of line and report only the keys of the coded button set. */
    }
    requirement <'SR-113'> debugInterfaceClosed {
        @Satisfies { need = "CRS-604"; }
        doc /* The debug interface of every series switch shall be permanently disabled before delivery. */
    }
    requirement <'SR-115'> installationSpace {
        @Satisfies { need = "CRS-507"; }
        doc /* Each switch, knob included, shall fit within the installation space of the customer's seat trim drawing. */
    }
    requirement <'SR-116'> materialDeclaration {
        @Satisfies { need = "CRS-508"; }
        doc /* Every material of the switch shall be declared in the OEM material data system, with no substance from the OEM-MAT-500 restricted list. */
    }
    requirement <'SR-117'> seatInPlaceReplacement {
        @Satisfies { need = "CRS-804"; }
        doc /* Each switch shall be removable from and refittable to the fitted seat trim with a trim tool in at most 5 minutes. */
    }
    requirement <'SR-118'> sparePartNumbers {
        @Satisfies { need = "CRS-805"; }
        doc /* Each combination of housing side and button set shall carry its own spare-part number. */
    }
    requirement <'SR-120'> traceabilityContent {
        @Satisfies { need = "CRS-703"; }
        doc /* The traceability code of every switch shall encode the OEM part number, the serial number and the production date. */
    }
    // states the gap of the partial satisfaction: the platform key is rated for 200 000 actuations, the OEM asks for 300 000
    requirement <'SR-119'> durabilityGap {
        @Satisfies { need = "CRS-304"; }
        doc /* Every key and knob direction shall withstand 200 000 actuations, two thirds of the 300 000 requested; the rest needs a new key mechanism outside the platform. */
    }
}
